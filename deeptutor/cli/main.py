#!/usr/bin/env python3
"""DeepTutor CLI

A command-line interface for DeepTutor with TUI support.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deeptutor.agents.agent_loop import AgentLoop
from deeptutor.channels import ChannelManager
from deeptutor.llm.providers import LLMProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("deeptutor.cli")

app = typer.Typer(
    name="deeptutor",
    help="DeepTutor - Multi-platform AI Assistant",
    no_args_is_help=True
)

console = Console()


def print_banner():
    """Print DeepTutor banner"""
    banner = r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    DeepTutor                                  ║
    ║               Multi-platform AI Assistant                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="Model to use"),
    provider: str = typer.Option(None, "--provider", "-p", help="LLM provider"),
    yolo: bool = typer.Option(False, "--yolo", help="Enable YOLO mode (auto-approve)"),
    cost: bool = typer.Option(True, "--cost/--no-cost", help="Track costs"),
    max_iterations: int = typer.Option(10, "--max-iter", help="Max iterations"),
):
    """Start an interactive chat session with the agent"""
    print_banner()
    
    console.print("\n[bold green]Starting chat session...[/bold green]\n")
    
    # Initialize LLM
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Initializing LLM client...", total=None)
        
        llm_provider = LLMProvider.from_env()
        if provider:
            llm_provider.provider_name = provider
        if model:
            llm_provider.model = model
        
        llm_client = llm_provider.get_client()
    
    console.print(f"✓ LLM Client: [cyan]{llm_provider.provider_name}[/cyan]")
    console.print(f"✓ Model: [cyan]{llm_provider.model}[/cyan]")
    console.print(f"✓ YOLO Mode: [cyan]{'Enabled' if yolo else 'Disabled'}[/cyan]")
    console.print(f"✓ Cost Tracking: [cyan]{'Enabled' if cost else 'Disabled'}[/cyan]")
    
    # Initialize Agent
    agent = AgentLoop(
        llm_client=llm_client,
        max_iterations=max_iterations,
        yolo_mode=yolo,
        track_cost=cost
    )
    
    console.print("\n[bold green]Chat session ready! Type 'exit' or 'quit' to exit.[/bold green]")
    console.print("-" * 60)
    
    # Chat loop
    total_cost = 0.0
    message_count = 0
    
    try:
        while True:
            user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("\n[bold green]Goodbye! 👋[/bold green]")
                break
            
            if not user_input.strip():
                continue
            
            message_count += 1
            
            console.print("\n[bold blue]DeepTutor[/bold blue]: ", end="")
            
            # Run agent
            try:
                response = asyncio.run(agent.run(user_input))
                console.print(response)
                
                if cost:
                    cost_info = agent.get_cost_info()
                    if cost_info:
                        total_cost += cost_info.get('total_cost', 0)
                        console.print(f"\n[dim]Cost: ${total_cost:.4f} | Messages: {message_count}[/dim]")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                continue
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {str(e)}")
                logger.error(f"Error in chat: {e}")
    
    except KeyboardInterrupt:
        console.print("\n\n[bold green]Goodbye! 👋[/bold green]")


@app.command()
def channels():
    """Start all configured chat channels"""
    print_banner()
    
    console.print("\n[bold green]Starting channel gateway...[/bold green]\n")
    
    from deeptutor.channels import ChannelManager
    from deeptutor.channels import (
        TelegramChannel,
        DiscordChannel,
        WeChatChannel,
        FeishuChannel,
        SlackChannel,
        EmailChannel,
        WebSocketChannel
    )
    
    # Load config from env
    channel_config = {
        "telegram": {
            "enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            "token": os.getenv("TELEGRAM_TOKEN"),
            "name": "telegram"
        },
        "discord": {
            "enabled": os.getenv("DISCORD_ENABLED", "false").lower() == "true",
            "token": os.getenv("DISCORD_TOKEN"),
            "prefix": os.getenv("DISCORD_PREFIX", "!"),
            "name": "discord"
        },
        "wechat": {
            "enabled": os.getenv("WECHAT_ENABLED", "false").lower() == "true",
            "token": os.getenv("WECHAT_TOKEN"),
            "puppet_service": os.getenv("WECHAT_PUPPET_SERVICE", "wechaty-puppet-wechat"),
            "name": "wechat"
        },
        "feishu": {
            "enabled": os.getenv("FEISHU_ENABLED", "false").lower() == "true",
            "app_id": os.getenv("FEISHU_APP_ID"),
            "app_secret": os.getenv("FEISHU_APP_SECRET"),
            "encrypt_key": os.getenv("FEISHU_ENCRYPT_KEY"),
            "verification_token": os.getenv("FEISHU_VERIFICATION_TOKEN"),
            "name": "feishu"
        },
        "slack": {
            "enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true",
            "bot_token": os.getenv("SLACK_BOT_TOKEN"),
            "app_token": os.getenv("SLACK_APP_TOKEN"),
            "name": "slack"
        },
        "email": {
            "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            "smtp_host": os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
            "imap_host": os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com"),
            "imap_port": int(os.getenv("EMAIL_IMAP_PORT", "993")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "from_email": os.getenv("EMAIL_FROM"),
            "name": "email"
        },
        "websocket": {
            "enabled": os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true",
            "host": os.getenv("WEBSOCKET_HOST", "localhost"),
            "port": int(os.getenv("WEBSOCKET_PORT", "8765")),
            "name": "websocket"
        }
    }
    
    channel_manager = ChannelManager(channel_config)
    
    # Register channels
    if channel_config["telegram"]["enabled"]:
        channel_manager.register_channel(TelegramChannel(channel_config["telegram"]))
    
    if channel_config["discord"]["enabled"]:
        channel_manager.register_channel(DiscordChannel(channel_config["discord"]))
    
    if channel_config["wechat"]["enabled"]:
        channel_manager.register_channel(WeChatChannel(channel_config["wechat"]))
    
    if channel_config["feishu"]["enabled"]:
        channel_manager.register_channel(FeishuChannel(channel_config["feishu"]))
    
    if channel_config["slack"]["enabled"]:
        channel_manager.register_channel(SlackChannel(channel_config["slack"]))
    
    if channel_config["email"]["enabled"]:
        channel_manager.register_channel(EmailChannel(channel_config["email"]))
    
    if channel_config["websocket"]["enabled"]:
        channel_manager.register_channel(WebSocketChannel(channel_config["websocket"]))
    
    # Initialize LLM
    llm_provider = LLMProvider.from_env()
    llm_client = llm_provider.get_client()
    agent = AgentLoop(llm_client=llm_client)
    
    # Message handler
    async def handle_message(message):
        logger.info(f"📨 {message['channel']}: {message['user_id']}")
        await channel_manager.send_typing(message['channel'], message['user_id'])
        
        try:
            response = await agent.run(message['message'])
            await channel_manager.send_message(
                message['channel'],
                message['user_id'],
                response
            )
            logger.info("✓ Response sent")
        except Exception as e:
            logger.error(f"Error: {e}")
            error_msg = f"Sorry, an error occurred: {str(e)}"
            await channel_manager.send_message(
                message['channel'],
                message['user_id'],
                error_msg
            )
    
    channel_manager.set_message_handler(handle_message)
    
    # Show active channels
    active_channels = [name for name, cfg in channel_config.items() if cfg['enabled']]
    table = Table(title="Active Channels")
    table.add_column("Channel", style="cyan")
    table.add_column("Status", style="green")
    
    for channel in active_channels:
        table.add_row(channel.capitalize(), "Enabled")
    
    console.print(table)
    console.print("\nPress Ctrl+C to stop\n")
    
    # Start channels
    try:
        asyncio.run(channel_manager.start())
    except KeyboardInterrupt:
        console.print("\nShutting down...")
        asyncio.run(channel_manager.stop())


@app.command()
def version():
    """Show version information"""
    console.print("[bold blue]DeepTutor[/bold blue] v0.1.0")


@app.command()
def config():
    """Show current configuration"""
    print_banner()
    
    table = Table(title="DeepTutor Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    # LLM
    table.add_row("LLM Provider", os.getenv("LLM_PROVIDER", "deepseek"))
    table.add_row("LLM Model", os.getenv("LLM_MODEL", "deepseek-chat"))
    
    # Channels
    table.add_row("Telegram", "✓" if os.getenv("TELEGRAM_ENABLED") == "true" else "✗")
    table.add_row("Discord", "✓" if os.getenv("DISCORD_ENABLED") == "true" else "✗")
    table.add_row("WeChat", "✓" if os.getenv("WECHAT_ENABLED") == "true" else "✗")
    table.add_row("Feishu", "✓" if os.getenv("FEISHU_ENABLED") == "true" else "✗")
    table.add_row("Slack", "✓" if os.getenv("SLACK_ENABLED") == "true" else "✗")
    table.add_row("Email", "✓" if os.getenv("EMAIL_ENABLED") == "true" else "✗")
    table.add_row("WebSocket", "✓" if os.getenv("WEBSOCKET_ENABLED", "true") == "true" else "✗")
    
    # MCP
    table.add_row("MCP", "✓" if os.getenv("MCP_ENABLED", "true") == "true" else "✗")
    
    console.print(table)


if __name__ == "__main__":
    app()
