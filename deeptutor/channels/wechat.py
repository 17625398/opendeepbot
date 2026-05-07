"""WeChat Channel for DeepTutor

WeChat bot integration using wechaty.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .base import BaseChannel

logger = logging.getLogger(__name__)

try:
    from wechaty import Wechaty, Contact, Message, Room
    from wechaty_puppet import PuppetOptions
    WECHATY_AVAILABLE = True
except ImportError:
    WECHATY_AVAILABLE = False
    logger.warning("wechaty not installed, WeChat channel disabled")


class WeChatChannel(BaseChannel):
    """WeChat chat channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "wechat"
        self.token = config.get("token")
        self.puppet_service = config.get("puppet_service", "wechaty-puppet-wechat")
        self.bot: Optional[Wechaty] = None
    
    async def initialize(self) -> bool:
        """Initialize WeChat channel"""
        if not WECHATY_AVAILABLE:
            logger.error("wechaty not installed")
            return False
        
        try:
            self.bot = Wechaty()
            
            @self.bot.on_message
            async def on_message(msg: Message):
                """Handle incoming messages"""
                if msg.self():
                    return
                
                user_id = str(msg.from_contact().contact_id if msg.from_contact() else "unknown")
                message_text = msg.text()
                
                if message_text:
                    await self._handle_incoming_message(user_id, message_text)
            
            @self.bot.on_login
            async def on_login(user: Contact):
                logger.info(f"WeChat bot logged in as {user.name}")
                self._connected = True
                self._stats["connected_at"] = __import__("datetime").datetime.now().isoformat()
            
            @self.bot.on_logout
            async def on_logout(user: Contact, reason: str):
                logger.info(f"WeChat bot logged out: {reason}")
                self._connected = False
            
            self._initialized = True
            logger.info("WeChat channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize WeChat channel: {e}")
            return False
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to WeChat user"""
        if not self.bot or not self._connected:
            logger.error("WeChat channel not connected")
            return False
        
        try:
            contact = await self.bot.Contact.find(user_id)
            if contact:
                await contact.say(message)
                return True
            
            # Try room
            room = await self.bot.Room.find(user_id)
            if room:
                await room.say(message)
                return True
            
            logger.error(f"Could not find contact or room: {user_id}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to send WeChat message: {e}")
            return False
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        if not self.bot:
            return
        
        try:
            contact = await self.bot.Contact.find(user_id)
            if contact:
                await contact.say("正在输入...")
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
    
    async def start(self):
        """Start WeChat bot"""
        if not self.bot:
            logger.error("WeChat bot not initialized")
            return
        
        try:
            logger.info("Starting WeChat bot...")
            await self.bot.start()
        except Exception as e:
            logger.error(f"Failed to start WeChat bot: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown WeChat channel"""
        await super().shutdown()
        
        if self.bot:
            await self.bot.stop()
        
        logger.info("WeChat channel shutdown")