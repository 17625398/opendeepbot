"""DeepTutor Channels Module

Provides multi-platform chat channel support for DeepTutor.
Supports: Telegram, Discord, WeChat, Feishu, Slack, QQ, Email, WebSocket

Based on HKUDS nanobot channel architecture.
"""

from .manager import ChannelManager
from .base import BaseChannel
from .telegram import TelegramChannel
from .discord import DiscordChannel
from .wechat import WeChatChannel
from .feishu import FeishuChannel
from .websocket import WebSocketChannel

__all__ = [
    "ChannelManager",
    "BaseChannel",
    "TelegramChannel",
    "DiscordChannel",
    "WeChatChannel",
    "FeishuChannel",
    "WebSocketChannel",
    "get_channel_manager",
]

_channel_manager = None


def get_channel_manager(config: dict = None) -> ChannelManager:
    """Get singleton channel manager instance"""
    global _channel_manager
    if _channel_manager is None:
        _channel_manager = ChannelManager(config or {})
    return _channel_manager