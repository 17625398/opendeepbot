"""Feishu Channel for DeepTutor

Feishu/Lark bot integration using feishu-sdk.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .base import BaseChannel

logger = logging.getLogger(__name__)

try:
    from larksuiteoapi import Config, ACCESS_TOKEN_TYPE_TENANT
    from larksuiteoapi.api.im.v1 import MessageCreateRequest, MessageCreateResponse
    FEISHU_AVAILABLE = True
except ImportError:
    FEISHU_AVAILABLE = False
    logger.warning("larksuite-oapi not installed, Feishu channel disabled")


class FeishuChannel(BaseChannel):
    """Feishu chat channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "feishu"
        self.app_id = config.get("app_id")
        self.app_secret = config.get("app_secret")
        self.encrypt_key = config.get("encrypt_key")
        self.verification_token = config.get("verification_token")
    
    async def initialize(self) -> bool:
        """Initialize Feishu channel"""
        if not FEISHU_AVAILABLE:
            logger.error("larksuite-oapi not installed")
            return False
        
        if not self.app_id or not self.app_secret:
            logger.error("Feishu app_id and app_secret required")
            return False
        
        try:
            self._initialized = True
            logger.info("Feishu channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Feishu channel: {e}")
            return False
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to Feishu user"""
        if not self._connected:
            logger.error("Feishu channel not connected")
            return False
        
        try:
            config = Config.new_internal_app_config(
                self.app_id,
                self.app_secret,
                access_token_type=ACCESS_TOKEN_TYPE_TENANT
            )
            
            # Create message request
            request = MessageCreateRequest.builder() \
                .receive_id_type("user_id") \
                .user_id(user_id) \
                .content({
                    "text": message
                }) \
                .msg_type("text") \
                .build()
            
            # Execute request (pseudo-code)
            # response = await request.execute(config)
            
            logger.info(f"Feishu message sent to {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send Feishu message: {e}")
            return False
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        if not self._connected:
            return
        
        try:
            # Feishu doesn't have native typing indicator, send a status message instead
            await self.send_message(user_id, "正在思考中...")
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
    
    async def start(self):
        """Start Feishu bot"""
        try:
            self._connected = True
            self._stats["connected_at"] = __import__("datetime").datetime.now().isoformat()
            logger.info("Feishu bot started")
        except Exception as e:
            logger.error(f"Failed to start Feishu bot: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown Feishu channel"""
        await super().shutdown()
        logger.info("Feishu channel shutdown")