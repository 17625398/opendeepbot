"""Telegram Channel for DeepTutor

Telegram bot integration using python-telegram-bot.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .base import BaseChannel

logger = logging.getLogger(__name__)

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed, Telegram channel disabled")


class TelegramChannel(BaseChannel):
    """Telegram chat channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "telegram"
        self.token = config.get("token")
        self.application: Optional[Application] = None
        self.updater_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize Telegram channel"""
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot not installed")
            return False
        
        if not self.token:
            logger.error("Telegram token not configured")
            return False
        
        try:
            self.application = ApplicationBuilder().token(self.token).build()
            
            # Register handlers
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("help", self._handle_help))
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )
            
            self._initialized = True
            logger.info("Telegram channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Telegram channel: {e}")
            return False
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        await self._handle_incoming_message(user_id, "/start")
        await update.message.reply_text("Welcome to DeepTutor!")
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
DeepTutor Telegram Bot

Commands:
/start - Start the bot
/help - Show this help message
/clear - Clear conversation history

Just send a message to start chatting!
        """.strip()
        await update.message.reply_text(help_text)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = str(update.effective_user.id)
        message_text = update.message.text
        
        if message_text:
            await self._handle_incoming_message(user_id, message_text)
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to Telegram user"""
        if not self.application or not self._connected:
            logger.error("Telegram channel not connected")
            return False
        
        try:
            await self.application.bot.send_message(
                chat_id=int(user_id),
                text=message,
                parse_mode=kwargs.get("parse_mode", "Markdown"),
                disable_web_page_preview=kwargs.get("disable_web_page_preview", True)
            )
            return True
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        if not self.application:
            return
        
        try:
            await self.application.bot.send_chat_action(
                chat_id=int(user_id),
                action="typing"
            )
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
    
    async def start(self):
        """Start Telegram bot"""
        if not self.application:
            logger.error("Telegram application not initialized")
            return
        
        try:
            self._connected = True
            self._stats["connected_at"] = (
                __import__("datetime").datetime.now().isoformat()
            )
            logger.info("Starting Telegram bot polling...")
            
            # Start polling in background
            self.updater_task = asyncio.create_task(
                self.application.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    poll_interval=1
                )
            )
            
            logger.info("Telegram bot started")
        
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown Telegram channel"""
        await super().shutdown()
        
        if self.updater_task:
            self.updater_task.cancel()
        
        if self.application:
            await self.application.shutdown()
        
        logger.info("Telegram channel shutdown")