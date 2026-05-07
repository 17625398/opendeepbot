#!/usr/bin/env python3
"""Full Example: DeepTutor with All Features

This example demonstrates:
- Multi-platform chat channels (Telegram, Discord, WeChat, Feishu, Slack, Email, WebSocket)
- Agent with YOLO mode, cost tracking, and snapshots
- MCP (Model Context Protocol) integration
- Enhanced memory system
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from deeptutor.agents.agent_loop import AgentLoop
from deeptutor.channels import ChannelManager, get_channel_manager
from deeptutor.llm.providers import LLMProvider
from deeptutor.mcp import MCPManager
from deeptutor.memory import MemoryManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("full_example")


async def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("DeepTutor Full Example")
    logger.info("=" * 60)

    # -------------------------------------------------------------------------
    # Step 1: Initialize LLM Client
    # -------------------------------------------------------------------------
    logger.info("\n[1/5] Initializing LLM Client...")
    llm_provider = LLMProvider.from_env()
    llm_client = llm_provider.get_client()
    logger.info(f"✓ LLM Client initialized: {llm_provider.provider_name}")

    # -------------------------------------------------------------------------
    # Step 2: Initialize Memory System
    # -------------------------------------------------------------------------
    logger.info("\n[2/5] Initializing Memory System...")
    memory_manager = MemoryManager(
        persist_path="./data/memory",
        enable_vector_store=True
    )
    logger.info("✓ Memory System initialized")

    # -------------------------------------------------------------------------
    # Step 3: Initialize Agent
    # -------------------------------------------------------------------------
    logger.info("\n[3/5] Initializing Agent Loop...")
    
    agent = AgentLoop(
        llm_client=llm_client,
        max_iterations=10,
        yolo_mode=False,  # Set to True for auto-approve
        track_cost=True,
        cost_callback=lambda cost: logger.info(f"Cost updated: ${cost:.4f}")
    )
    
    logger.info("✓ Agent initialized")

    # -------------------------------------------------------------------------
    # Step 4: Initialize MCP Manager (optional)
    # -------------------------------------------------------------------------
    logger.info("\n[4/5] Initializing MCP Manager...")
    mcp_config = {
        "enabled": os.getenv("MCP_ENABLED", "true").lower() == "true",
        "servers": {}
    }
    
    mcp_manager = MCPManager(mcp_config)
    logger.info("✓ MCP Manager initialized")

    # -------------------------------------------------------------------------
    # Step 5: Initialize Channel Manager
    # -------------------------------------------------------------------------
    logger.info("\n[5/5] Initializing Channel Manager...")
    
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
    logger.info("✓ Channel Manager initialized")

    # -------------------------------------------------------------------------
    # Message Handler: Connect Channels -> Agent
    # -------------------------------------------------------------------------
    async def handle_incoming_message(message):
        """Handle messages from any channel"""
        logger.info(f"📨 Received from {message['channel']}: {message['user_id']}")
        logger.info(f"   Message: {message['message'][:100]}...")
        
        # Send typing indicator
        await channel_manager.send_typing(message['channel'], message['user_id'])
        
        # Get agent response
        try:
            response = await agent.run(message['message'])
            
            # Send response back
            await channel_manager.send_message(
                message['channel'],
                message['user_id'],
                response
            )
            
            # Store in memory
            await memory_manager.add_interaction(
                user_id=message['user_id'],
                channel=message['channel'],
                user_message=message['message'],
                assistant_response=response
            )
            
            logger.info(f"✓ Response sent to {message['channel']}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            await channel_manager.send_message(
                message['channel'],
                message['user_id'],
                error_msg
            )

    # Set message handler
    channel_manager.set_message_handler(handle_incoming_message)

    # -------------------------------------------------------------------------
    # Start all channels
    # -------------------------------------------------------------------------
    logger.info("\nStarting all channels...")
    await channel_manager.start()
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 DeepTutor is running!")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        await channel_manager.stop()
        await mcp_manager.shutdown()
        logger.info("✓ DeepTutor stopped")


if __name__ == "__main__":
    asyncio.run(main())
