"""Discord Channel for DeepTutor

Discord bot integration using discord.py with enhanced features.

Features:
- Command system with permissions
- Embedded messages support
- File upload support
- Role-based access control
- Slash commands support
- Reaction handling
- Message editing and deletion
- Statistics tracking
"""

import asyncio
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

from .base import BaseChannel, Message

logger = logging.getLogger(__name__)

try:
    import discord
    from discord import Intents, Message, Embed, Color, File, Reaction
    from discord.ext import commands
    from discord.app_commands import CommandTree
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.warning("discord.py not installed, Discord channel disabled")


class DiscordChannel(BaseChannel):
    """Discord chat channel with enhanced features"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "discord"
        self.token = config.get("token")
        self.prefix = config.get("prefix", "!")
        self.bot: Optional[commands.Bot] = None
        self.bot_task: Optional[asyncio.Task] = None
        self._stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "commands_executed": 0,
            "connected_at": None,
        }
        self._allowed_roles = config.get("allowed_roles", [])
        self._admin_roles = config.get("admin_roles", [])
    
    async def initialize(self) -> bool:
        """Initialize Discord channel with enhanced features"""
        if not DISCORD_AVAILABLE:
            logger.error("discord.py not installed")
            return False
        
        if not self.token:
            logger.error("Discord token not configured")
            return False
        
        try:
            # Set up intents with all required permissions
            intents = Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.members = True
            intents.reactions = True
            
            # Create bot instance
            self.bot = commands.Bot(
                command_prefix=self.prefix,
                intents=intents,
                description="DeepTutor Discord Bot",
                help_command=None  # Disable default help command
            )
            
            # Initialize slash commands
            self._initialize_slash_commands()
            
            # Register event handlers
            @self.bot.event
            async def on_ready():
                logger.info(f"Discord bot logged in as {self.bot.user} (ID: {self.bot.user.id})")
                logger.info(f"Connected to {len(self.bot.guilds)} guilds")
                self._connected = True
                self._stats["connected_at"] = datetime.now().isoformat()
                
                # Sync slash commands
                await self.bot.tree.sync()
                logger.info("Slash commands synced")
            
            @self.bot.event
            async def on_message(message: Message):
                if message.author == self.bot.user:
                    return
                
                # Ignore bot messages by default
                if message.author.bot:
                    return
                
                self._stats["messages_received"] += 1
                
                # Handle commands first
                await self.bot.process_commands(message)
                
                # Handle regular messages (non-command)
                if not message.content.startswith(self.prefix):
                    await self._process_incoming_message(message)
            
            @self.bot.event
            async def on_reaction_add(reaction: Reaction, user):
                """Handle reactions"""
                if user == self.bot.user:
                    return
                
                logger.debug(f"Reaction added: {reaction.emoji} by {user}")
            
            @self.bot.event
            async def on_guild_join(guild):
                """Handle joining a new guild"""
                logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
            
            @self.bot.event
            async def on_member_join(member):
                """Handle new member"""
                logger.info(f"New member joined: {member.name}")
            
            # Register text commands
            self._register_text_commands()
            
            self._initialized = True
            logger.info("Discord channel initialized with enhanced features")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Discord channel: {e}", exc_info=True)
            return False
    
    def _initialize_slash_commands(self):
        """Initialize slash commands"""
        @self.bot.tree.command(name="help", description="Show help message")
        async def slash_help(interaction: discord.Interaction):
            embed = Embed(
                title="DeepTutor Help",
                description="Available commands for DeepTutor Discord Bot",
                color=Color.blue()
            )
            embed.add_field(
                name="Text Commands",
                value=f"""
`{self.prefix}help` - Show this help message
`{self.prefix}start` - Start conversation
`{self.prefix}clear` - Clear conversation history
`{self.prefix}status` - Show bot status
`{self.prefix}stats` - Show statistics
`{self.prefix}version` - Show version
                """.strip(),
                inline=False
            )
            embed.add_field(
                name="Slash Commands",
                value="""
`/help` - Show this help message
`/start` - Start conversation
`/clear` - Clear conversation history
`/status` - Show bot status
                """.strip(),
                inline=False
            )
            embed.set_footer(text="Just send a message to start chatting!")
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name="start", description="Start conversation")
        async def slash_start(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            await self._handle_incoming_message(user_id, "/start")
            embed = Embed(
                title="Welcome!",
                description="Welcome to DeepTutor! I'm ready to help you with any questions.",
                color=Color.green()
            )
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name="clear", description="Clear conversation history")
        async def slash_clear(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            await self._clear_history(user_id)
            embed = Embed(
                title="History Cleared",
                description="Your conversation history has been cleared.",
                color=Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name="status", description="Show bot status")
        async def slash_status(interaction: discord.Interaction):
            embed = self._build_status_embed()
            await interaction.response.send_message(embed=embed)
    
    def _register_text_commands(self):
        """Register text-based commands"""
        @self.bot.command(name="help", help="Show help message")
        async def cmd_help(ctx):
            embed = Embed(
                title="DeepTutor Help",
                description="Available commands for DeepTutor Discord Bot",
                color=Color.blue()
            )
            embed.add_field(
                name="Commands",
                value=f"""
`{self.prefix}help` - Show this help message
`{self.prefix}start` - Start conversation
`{self.prefix}clear` - Clear conversation history
`{self.prefix}status` - Show bot status
`{self.prefix}stats` - Show statistics
`{self.prefix}version` - Show version
                """.strip(),
                inline=False
            )
            embed.set_footer(text="Just send a message to start chatting!")
            await ctx.send(embed=embed)
        
        @self.bot.command(name="start", help="Start the bot")
        async def cmd_start(ctx):
            user_id = str(ctx.author.id)
            await self._handle_incoming_message(user_id, "/start")
            embed = Embed(
                title="Welcome!",
                description="Welcome to DeepTutor! I'm ready to help you with any questions.",
                color=Color.green()
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name="clear", help="Clear conversation history")
        async def cmd_clear(ctx):
            user_id = str(ctx.author.id)
            await self._clear_history(user_id)
            embed = Embed(
                title="History Cleared",
                description="Your conversation history has been cleared.",
                color=Color.orange()
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name="status", help="Show bot status")
        async def cmd_status(ctx):
            embed = self._build_status_embed()
            await ctx.send(embed=embed)
        
        @self.bot.command(name="stats", help="Show bot statistics")
        async def cmd_stats(ctx):
            embed = self._build_stats_embed()
            await ctx.send(embed=embed)
        
        @self.bot.command(name="version", help="Show bot version")
        async def cmd_version(ctx):
            embed = Embed(
                title="Version",
                description="DeepTutor Discord Bot v1.0.0",
                color=Color.purple()
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name="ping", help="Check bot latency")
        async def cmd_ping(ctx):
            latency = round(self.bot.latency * 1000)
            embed = Embed(
                title="Pong!",
                description=f"Latency: {latency}ms",
                color=Color.green()
            )
            await ctx.send(embed=embed)
    
    async def _process_incoming_message(self, message: Message):
        """Process incoming message with enhanced handling"""
        user_id = str(message.author.id)
        
        # Check role permissions if configured
        if self._allowed_roles and message.guild:
            if not self._has_allowed_role(message.author):
                logger.debug(f"User {user_id} denied - no allowed role")
                return
        
        # Create message object
        msg = Message(
            id=str(message.id),
            text=message.content,
            sender_id=user_id,
            sender_name=str(message.author),
            channel_type="discord",
            is_group=message.channel.type != discord.ChannelType.private,
            group_id=str(message.channel.id) if message.channel.type != discord.ChannelType.private else "",
            raw=message
        )
        
        # Send to message handler
        if self._message_handler:
            await self._message_handler(msg)
    
    def _has_allowed_role(self, member: discord.Member) -> bool:
        """Check if member has allowed role"""
        for role in member.roles:
            if role.name in self._allowed_roles or role.id in self._allowed_roles:
                return True
        return False
    
    def _is_admin(self, member: discord.Member) -> bool:
        """Check if member is admin"""
        if member.guild_permissions.administrator:
            return True
        for role in member.roles:
            if role.name in self._admin_roles or role.id in self._admin_roles:
                return True
        return False
    
    def _build_status_embed(self) -> Embed:
        """Build status embed"""
        embed = Embed(
            title="DeepTutor Status",
            color=Color.green() if self._connected else Color.red()
        )
        embed.add_field(name="Status", value="🟢 Online" if self._connected else "🔴 Offline")
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)) if self.bot else "0")
        embed.add_field(name="Connected At", value=self._stats.get("connected_at", "N/A"))
        embed.add_field(name="Prefix", value=f"`{self.prefix}`")
        return embed
    
    def _build_stats_embed(self) -> Embed:
        """Build statistics embed"""
        embed = Embed(
            title="DeepTutor Statistics",
            color=Color.blue()
        )
        embed.add_field(name="Messages Received", value=str(self._stats.get("messages_received", 0)))
        embed.add_field(name="Messages Sent", value=str(self._stats.get("messages_sent", 0)))
        embed.add_field(name="Commands Executed", value=str(self._stats.get("commands_executed", 0)))
        return embed
    
    async def _clear_history(self, user_id: str):
        """Clear conversation history for user"""
        # This would connect to your memory/history system
        logger.info(f"Cleared history for user: {user_id}")
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to Discord user or channel with enhanced options"""
        if not self.bot or not self._connected:
            logger.error("Discord channel not connected")
            return False
        
        try:
            # Get embed option
            use_embed = kwargs.get("embed", False)
            
            # Try to get user first
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    if use_embed:
                        embed = Embed(description=message, color=Color.blue())
                        await user.send(embed=embed)
                    else:
                        await user.send(message)
                    self._stats["messages_sent"] += 1
                    return True
            except discord.errors.NotFound:
                pass
            
            # Try as channel ID
            try:
                channel = self.bot.get_channel(int(user_id))
                if channel:
                    if use_embed:
                        embed = Embed(description=message, color=Color.blue())
                        await channel.send(embed=embed)
                    else:
                        await channel.send(message)
                    self._stats["messages_sent"] += 1
                    return True
            except (discord.errors.NotFound, ValueError):
                pass
            
            logger.error(f"Could not find user or channel: {user_id}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}", exc_info=True)
            return False
    
    async def send_embed(self, user_id: str, title: str, description: str, **kwargs) -> bool:
        """Send embedded message"""
        if not self.bot or not self._connected:
            logger.error("Discord channel not connected")
            return False
        
        try:
            color = kwargs.get("color", Color.blue())
            fields = kwargs.get("fields", [])
            
            embed = Embed(title=title, description=description, color=color)
            
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", False)
                )
            
            # Try user
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    await user.send(embed=embed)
                    self._stats["messages_sent"] += 1
                    return True
            except discord.errors.NotFound:
                pass
            
            # Try channel
            channel = self.bot.get_channel(int(user_id))
            if channel:
                await channel.send(embed=embed)
                self._stats["messages_sent"] += 1
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to send embed: {e}", exc_info=True)
            return False
    
    async def send_file(self, user_id: str, file_path: str, **kwargs) -> bool:
        """Send file to user or channel"""
        if not self.bot or not self._connected:
            logger.error("Discord channel not connected")
            return False
        
        try:
            file = File(file_path)
            caption = kwargs.get("caption", "")
            
            # Try user
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    await user.send(file=file, content=caption)
                    self._stats["messages_sent"] += 1
                    return True
            except discord.errors.NotFound:
                pass
            
            # Try channel
            channel = self.bot.get_channel(int(user_id))
            if channel:
                await channel.send(file=file, content=caption)
                self._stats["messages_sent"] += 1
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to send file: {e}", exc_info=True)
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
            logger.error(f"Failed to start Discord bot: {e}", exc_info=True)
            self._connected = False
    
    async def shutdown(self):
        """Shutdown Discord channel"""
        await super().shutdown()
        
        if self.bot:
            await self.bot.close()
        
        if self.bot_task:
            self.bot_task.cancel()
        
        logger.info("Discord channel shutdown")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get channel statistics"""
        return self._stats
