"""Discord Channel for DeepTutor

Discord bot integration using discord.py.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .base import BaseChannel

logger = logging.getLogger(__name__)

try:
    import discord
    from discord import Intents, Message
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.warning("discord.py not installed, Discord channel disabled")


class DiscordChannel(BaseChannel):
    """Discord chat channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "discord"
        self.token = config.get("token")
        self.prefix = config.get("prefix", "!")
        self.bot: Optional[commands.Bot] = None
        self.bot_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize Discord channel"""
        if not DISCORD_AVAILABLE:
            logger.error("discord.py not installed")
            return False
        
        if not self.token:
            logger.error("Discord token not configured")
            return False
        
        try:
            # Set up intents
            intents = Intents.default()
            intents.message_content = True
            intents.guilds = True
            
            # Create bot instance
            self.bot = commands.Bot(
                command_prefix=self.prefix,
                intents=intents,
                description="DeepTutor Discord Bot"
            )
            
            # Register event handlers
            @self.bot.event
            async def on_ready():
                logger.info(f"Discord bot logged in as {self.bot.user}")
                self._connected = True
                self._stats["connected_at"] = (
                    __import__("datetime").datetime.now().isoformat()
                )
            
            @self.bot.event
            async def on_message(message: Message):
                if message.author == self.bot.user:
                    return
                
                # Handle commands
                await self.bot.process_commands(message)
                
                # Handle regular messages
                if not message.content.startswith(self.prefix):
                    user_id = str(message.author.id)
                    await self._handle_incoming_message(user_id, message.content)
            
            # Register commands
            @self.bot.command(name="start", help="Start the bot")
            async def cmd_start(ctx):
                user_id = str(ctx.author.id)
                await self._handle_incoming_message(user_id, "/start")
                await ctx.send("Welcome to DeepTutor!")
            
            @self.bot.command(name="help", help="Show help message")
            async def cmd_help(ctx):
                help_text = f"""
DeepTutor Discord Bot

Commands:
{self.prefix}start - Start the bot
{self.prefix}help - Show this help message
{self.prefix}clear - Clear conversation history

Just send a message to start chatting!
                """.strip()
                await ctx.send(help_text)
            
            self._initialized = True
            logger.info("Discord channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Discord channel: {e}")
            return False
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to Discord user or channel"""
        if not self.bot or not self._connected:
            logger.error("Discord channel not connected")
            return False
        
        try:
            # Try to get user first
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    await user.send(message)
                    return True
            except discord.errors.NotFound:
                pass
            
            # Try as channel ID
            try:
                channel = self.bot.get_channel(int(user_id))
                if channel:
                    await channel.send(message)
                    return True
            except (discord.errors.NotFound, ValueError):
                pass
            
            logger.error(f"Could not find user or channel: {user_id}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        if not self.bot:
            return
        
        try:
            # Try as user
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    async with user.typing():
                        await asyncio.sleep(1)
                    return
            except discord.errors.NotFound:
                pass
            
            # Try as channel
            channel = self.bot.get_channel(int(user_id))
            if channel:
                async with channel.typing():
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
    
    async def start(self):
        """Start Discord bot"""
        if not self.bot:
            logger.error("Discord bot not initialized")
            return
        
        try:
            logger.info("Starting Discord bot...")
            
            # Start bot in background
            self.bot_task = asyncio.create_task(self.bot.start(self.token))
            
            logger.info("Discord bot started")
        
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown Discord channel"""
        await super().shutdown()
        
        if self.bot:
            await self.bot.close()
        
        if self.bot_task:
            self.bot_task.cancel()
        
        logger.info("Discord channel shutdown")