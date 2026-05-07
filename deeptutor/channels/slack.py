"""Slack Channel for DeepTutor

Slack bot integration using slack_bolt.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .base import BaseChannel

logger = logging.getLogger(__name__)

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("slack_bolt not installed, Slack channel disabled")


class SlackChannel(BaseChannel):
    """Slack chat channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "slack"
        self.bot_token = config.get("bot_token")
        self.app_token = config.get("app_token")
        self.app: Optional[App] = None
        self.handler: Optional[SocketModeHandler] = None
    
    async def initialize(self) -> bool:
        """Initialize Slack channel"""
        if not SLACK_AVAILABLE:
            logger.error("slack_bolt not installed")
            return False
        
        if not self.bot_token or not self.app_token:
            logger.error("Slack bot_token and app_token required")
            return False
        
        try:
            self.app = App(token=self.bot_token)
            
            @self.app.event("app_mention")
            async def handle_app_mention(event, say):
                """Handle mentions"""
                user_id = event.get("user", "unknown")
                message_text = event.get("text", "")
                await self._handle_incoming_message(user_id, message_text)
            
            @self.app.event("message")
            async def handle_message_events(event):
                """Handle messages"""
                if event.get("bot_id"):
                    return
                
                user_id = event.get("user", "unknown")
                message_text = event.get("text", "")
                
                if message_text:
                    await self._handle_incoming_message(user_id, message_text)
            
            self._initialized = True
            logger.info("Slack channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Slack channel: {e}")
            return False
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to Slack user/channel"""
        if not self.app or not self._connected:
            logger.error("Slack channel not connected")
            return False
        
        try:
            channel = kwargs.get("channel", user_id)
            result = await self.app.client.chat_postMessage(
                channel=channel,
                text=message
            )
            return result.get("ok", False)
        
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        if not self.app or not self._connected:
            return
        
        try:
            await self.app.client.chat_postMessage(
                channel=user_id,
                text="正在思考中...",
                type="typing"
            )
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
    
    async def start(self):
        """Start Slack bot"""
        if not self.app:
            logger.error("Slack app not initialized")
            return
        
        try:
            logger.info("Starting Slack bot...")
            self.handler = SocketModeHandler(self.app, self.app_token)
            await self.handler.start()
            
            self._connected = True
            self._stats["connected_at"] = __import__("datetime").datetime.now().isoformat()
            logger.info("Slack bot started")
        
        except Exception as e:
            logger.error(f"Failed to start Slack bot: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown Slack channel"""
        await super().shutdown()
        
        if self.handler:
            try:
                self.handler.close()
            except Exception as e:
                logger.error(f"Error closing Slack handler: {e}")
        
        logger.info("Slack channel shutdown")
