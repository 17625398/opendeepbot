"""Base Channel for DeepTutor

Base class for all chat channels.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class BaseChannel(ABC):
    """Base class for all chat channels
    
    Provides common functionality for channel implementations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the channel
        
        Args:
            config: Channel configuration
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.name = config.get("name", "unknown")
        self.allow_from = config.get("allow_from", config.get("allowFrom", []))
        self._message_handler: Optional[Callable] = None
        self._connected = False
        self._initialized = False
        self._stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "connected_at": None
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the channel
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send a message to a user
        
        Args:
            user_id: User identifier
            message: Message text
            **kwargs: Additional arguments
            
        Returns:
            True if message sent successfully
        """
        pass
    
    @abstractmethod
    async def send_typing(self, user_id: str):
        """Send typing indicator to a user
        
        Args:
            user_id: User identifier
        """
        pass
    
    async def shutdown(self):
        """Shutdown the channel"""
        self._connected = False
        logger.info(f"{self.name} channel shutdown")
    
    def set_message_handler(self, handler: Callable):
        """Set message handler callback
        
        Args:
            handler: Function to handle incoming messages
        """
        self._message_handler = handler
    
    def _is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user is allowed
        """
        if not self.allow_from:
            return True
        return user_id in self.allow_from
    
    async def _handle_incoming_message(self, user_id: str, message: str, **kwargs):
        """Handle incoming message
        
        Args:
            user_id: User identifier
            message: Message text
            **kwargs: Additional message data
        """
        if not self._is_allowed(user_id):
            logger.warning(f"Message from unauthorized user: {user_id}")
            return
        
        self._stats["messages_received"] += 1
        
        if self._message_handler:
            try:
                await self._message_handler({
                    "channel": self.name,
                    "user_id": user_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    **kwargs
                })
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                self._stats["errors"] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get channel status
        
        Returns:
            Status dictionary
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "connected": self._connected,
            "initialized": self._initialized,
            "stats": self._stats.copy()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get channel statistics"""
        return self._stats.copy()
    
    def increment_sent(self):
        """Increment sent message count"""
        self._stats["messages_sent"] += 1
    
    def increment_errors(self):
        """Increment error count"""
        self._stats["errors"] += 1