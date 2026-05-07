"""Channel Manager for DeepTutor

Manages all chat channels and message routing.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Type

from .base import BaseChannel

logger = logging.getLogger(__name__)


class ChannelManager:
    """Manages all chat channels
    
    Provides unified interface for managing multiple chat channels.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize channel manager
        
        Args:
            config: Channel configuration dictionary
        """
        self.config = config
        self.channels: Dict[str, BaseChannel] = {}
        self._message_handler: Optional[Callable] = None
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    def register_channel(self, channel: BaseChannel):
        """Register a channel
        
        Args:
            channel: Channel instance to register
        """
        if channel.name in self.channels:
            logger.warning(f"Channel {channel.name} already registered, replacing")
        
        self.channels[channel.name] = channel
        channel.set_message_handler(self._handle_message)
        logger.info(f"Registered channel: {channel.name}")
    
    def unregister_channel(self, name: str) -> bool:
        """Unregister a channel
        
        Args:
            name: Channel name
            
        Returns:
            True if channel was unregistered
        """
        if name in self.channels:
            asyncio.create_task(self.channels[name].shutdown())
            del self.channels[name]
            logger.info(f"Unregistered channel: {name}")
            return True
        return False
    
    def get_channel(self, name: str) -> Optional[BaseChannel]:
        """Get a channel by name
        
        Args:
            name: Channel name
            
        Returns:
            Channel instance or None
        """
        return self.channels.get(name)
    
    def list_channels(self) -> List[str]:
        """List all registered channels"""
        return list(self.channels.keys())
    
    def get_channel_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific channel
        
        Args:
            name: Channel name
            
        Returns:
            Status dictionary or None
        """
        channel = self.get_channel(name)
        if channel:
            return channel.get_status()
        return None
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all channels"""
        status = {}
        for name, channel in self.channels.items():
            status[name] = channel.get_status()
        return status
    
    def set_message_handler(self, handler: Callable):
        """Set global message handler
        
        Args:
            handler: Function to handle incoming messages from all channels
        """
        self._message_handler = handler
        # Also set handler for all registered channels
        for channel in self.channels.values():
            channel.set_message_handler(self._handle_message)
    
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming message from any channel
        
        Args:
            message: Message dictionary with channel, user_id, message, timestamp
        """
        if self._message_handler:
            try:
                await self._message_handler(message)
            except Exception as e:
                logger.error(f"Global message handler error: {e}")
    
    async def initialize_all(self) -> bool:
        """Initialize all enabled channels
        
        Returns:
            True if all channels initialized successfully
        """
        logger.info("Initializing all channels...")
        
        success_count = 0
        total_count = 0
        
        for name, channel in self.channels.items():
            if channel.enabled:
                total_count += 1
                try:
                    success = await channel.initialize()
                    if success:
                        success_count += 1
                        logger.info(f"Successfully initialized channel: {name}")
                    else:
                        logger.warning(f"Failed to initialize channel: {name}")
                except Exception as e:
                    logger.error(f"Error initializing channel {name}: {e}")
        
        if total_count > 0:
            logger.info(f"Initialized {success_count}/{total_count} channels")
        
        return success_count == total_count
    
    async def send_message(self, channel_name: str, user_id: str, message: str, **kwargs) -> bool:
        """Send message through specific channel
        
        Args:
            channel_name: Channel name to use
            user_id: User identifier
            message: Message text
            **kwargs: Additional arguments
            
        Returns:
            True if message sent successfully
        """
        channel = self.get_channel(channel_name)
        if not channel:
            logger.error(f"Channel {channel_name} not found")
            return False
        
        if not channel._connected:
            logger.error(f"Channel {channel_name} is not connected")
            return False
        
        try:
            result = await channel.send_message(user_id, message, **kwargs)
            if result:
                channel.increment_sent()
            return result
        except Exception as e:
            logger.error(f"Error sending message via {channel_name}: {e}")
            channel.increment_errors()
            return False
    
    async def broadcast_message(self, user_id: str, message: str, **kwargs) -> Dict[str, bool]:
        """Broadcast message to all connected channels
        
        Args:
            user_id: User identifier
            message: Message text
            **kwargs: Additional arguments
            
        Returns:
            Dictionary of channel name -> success status
        """
        results = {}
        tasks = []
        
        for name, channel in self.channels.items():
            if channel.enabled and channel._connected:
                tasks.append(self._broadcast_to_channel(channel, user_id, message, results, **kwargs))
        
        await asyncio.gather(*tasks)
        return results
    
    async def _broadcast_to_channel(self, channel: BaseChannel, user_id: str, message: str, 
                                   results: Dict[str, bool], **kwargs):
        """Helper method for broadcasting"""
        try:
            result = await channel.send_message(user_id, message, **kwargs)
            results[channel.name] = result
            if result:
                channel.increment_sent()
        except Exception as e:
            logger.error(f"Broadcast error on {channel.name}: {e}")
            results[channel.name] = False
            channel.increment_errors()
    
    async def start(self):
        """Start all enabled channels"""
        if self._running:
            logger.warning("Channel manager is already running")
            return
        
        logger.info("Starting channel manager...")
        
        # Initialize all channels
        await self.initialize_all()
        
        # Start background tasks for channels that need them
        for name, channel in self.channels.items():
            if channel.enabled and channel._connected:
                task = asyncio.create_task(self._channel_loop(channel))
                self._tasks.append(task)
        
        self._running = True
        logger.info("Channel manager started")
    
    async def _channel_loop(self, channel: BaseChannel):
        """Background loop for a channel"""
        while self._running and channel._connected:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in {channel.name} loop: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop all channels"""
        if not self._running:
            logger.warning("Channel manager is not running")
            return
        
        logger.info("Stopping channel manager...")
        
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Shutdown all channels
        for channel in self.channels.values():
            await channel.shutdown()
        
        self._tasks.clear()
        logger.info("Channel manager stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all channels
        
        Returns:
            Health status dictionary
        """
        health = {
            "status": "healthy",
            "channels": {},
            "timestamp": None
        }
        
        from datetime import datetime
        health["timestamp"] = datetime.now().isoformat()
        
        all_healthy = True
        for name, channel in self.channels.items():
            status = channel.get_status()
            channel_healthy = status.get("connected", False)
            
            if not channel_healthy and channel.enabled:
                all_healthy = False
            
            health["channels"][name] = {
                "connected": status.get("connected", False),
                "enabled": status.get("enabled", False),
                "messages_received": status.get("stats", {}).get("messages_received", 0),
                "messages_sent": status.get("stats", {}).get("messages_sent", 0),
                "errors": status.get("stats", {}).get("errors", 0)
            }
        
        health["status"] = "healthy" if all_healthy else "degraded"
        return health