"""Tests for chat channels functionality."""

import pytest
from unittest.mock import Mock, patch

from deeptutor.channels import ChannelManager
from deeptutor.channels.base import BaseChannel


class TestBaseChannel:
    """Tests for the BaseChannel class."""
    
    def test_init(self):
        """Test channel initialization."""
        config = {"name": "test-channel"}
        channel = BaseChannel(config)
        assert channel.config == config
        assert channel.name == "base"
        assert channel._initialized is False
        assert channel._connected is False
    
    def test_is_available(self):
        """Test is_available property."""
        config = {}
        channel = BaseChannel(config)
        assert channel.is_available is True  # Default is always available
    
    def test_status(self):
        """Test status property."""
        config = {}
        channel = BaseChannel(config)
        status = channel.status
        assert "name" in status
        assert "initialized" in status
        assert "connected" in status


class TestChannelManager:
    """Tests for the ChannelManager class."""
    
    def test_init(self):
        """Test channel manager initialization."""
        config = {}
        manager = ChannelManager(config)
        assert manager.config == config
        assert manager.channels == {}
        assert manager._message_handler is None
    
    def test_register_channel(self):
        """Test registering a channel."""
        config = {}
        manager = ChannelManager(config)
        
        # Create a mock channel
        mock_channel = Mock()
        mock_channel.name = "test-channel"
        
        manager.register_channel(mock_channel)
        assert "test-channel" in manager.channels
        assert manager.channels["test-channel"] == mock_channel
    
    def test_register_duplicate_channel(self):
        """Test registering a channel with duplicate name."""
        config = {}
        manager = ChannelManager(config)
        
        # Create mock channels with same name
        mock_channel1 = Mock()
        mock_channel1.name = "test-channel"
        
        mock_channel2 = Mock()
        mock_channel2.name = "test-channel"
        
        manager.register_channel(mock_channel1)
        manager.register_channel(mock_channel2)  # Should replace the old one
        
        assert manager.channels["test-channel"] == mock_channel2
    
    def test_get_channel(self):
        """Test getting a registered channel."""
        config = {}
        manager = ChannelManager(config)
        
        mock_channel = Mock()
        mock_channel.name = "test-channel"
        manager.register_channel(mock_channel)
        
        channel = manager.get_channel("test-channel")
        assert channel == mock_channel
    
    def test_get_nonexistent_channel(self):
        """Test getting a channel that doesn't exist."""
        config = {}
        manager = ChannelManager(config)
        
        channel = manager.get_channel("nonexistent")
        assert channel is None
    
    def test_set_message_handler(self):
        """Test setting a message handler."""
        config = {}
        manager = ChannelManager(config)
        
        async def mock_handler(message):
            pass
        
        manager.set_message_handler(mock_handler)
        assert manager._message_handler == mock_handler
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending a message through a channel."""
        config = {}
        manager = ChannelManager(config)
        
        # Create mock channel
        mock_channel = Mock()
        mock_channel.name = "test-channel"
        mock_channel.send_message.return_value = True
        
        manager.register_channel(mock_channel)
        
        result = await manager.send_message(
            "test-channel", 
            "user123", 
            "Hello, world!"
        )
        
        mock_channel.send_message.assert_called_once_with("user123", "Hello, world!")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_message_nonexistent_channel(self):
        """Test sending a message to a channel that doesn't exist."""
        config = {}
        manager = ChannelManager(config)
        
        result = await manager.send_message(
            "nonexistent", 
            "user123", 
            "Hello!"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting a message to all channels."""
        config = {}
        manager = ChannelManager(config)
        
        # Create mock channels
        mock_channel1 = Mock()
        mock_channel1.name = "channel1"
        mock_channel1.send_message.return_value = True
        
        mock_channel2 = Mock()
        mock_channel2.name = "channel2"
        mock_channel2.send_message.return_value = True
        
        manager.register_channel(mock_channel1)
        manager.register_channel(mock_channel2)
        
        results = await manager.broadcast("user123", "Broadcast message")
        
        assert len(results) == 2
        assert all(results.values())
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping all channels."""
        config = {}
        manager = ChannelManager(config)
        
        # Create mock channel
        mock_channel = Mock()
        mock_channel.name = "test-channel"
        mock_channel.initialize.return_value = True
        manager.register_channel(mock_channel)
        
        await manager.start()
        mock_channel.initialize.assert_called_once()
        mock_channel.start.assert_called_once()
        
        await manager.stop()
        mock_channel.shutdown.assert_called_once()


class TestChannelList:
    """Tests for channel listing functionality."""
    
    def test_list_channels(self):
        """Test listing registered channels."""
        config = {}
        manager = ChannelManager(config)
        
        mock_channel1 = Mock()
        mock_channel1.name = "channel1"
        
        mock_channel2 = Mock()
        mock_channel2.name = "channel2"
        
        manager.register_channel(mock_channel1)
        manager.register_channel(mock_channel2)
        
        channels = manager.list_channels()
        assert len(channels) == 2
        assert "channel1" in channels
        assert "channel2" in channels
