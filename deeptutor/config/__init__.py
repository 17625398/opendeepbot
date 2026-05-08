"""
DeepTutor Configuration Module
"""
# 导入所有内容
from deeptutor.config.config import load_config, validate_config
from deeptutor.config.config import DeepTutorConfig, LLMConfig, ChannelConfig
from deeptutor.config.config import TelegramConfig, DiscordConfig, SlackConfig
from deeptutor.config.config import EmailConfig, WebSocketConfig, MCPConfig
from deeptutor.config.config import ConfigLoader

# 提供 get_config 作为 load_config 的别名，用于向后兼容
get_config = load_config

# 导出所有内容
__all__ = [
    "load_config",
    "get_config",
    "validate_config",
    "DeepTutorConfig",
    "LLMConfig",
    "ChannelConfig",
    "TelegramConfig",
    "DiscordConfig",
    "SlackConfig",
    "EmailConfig",
    "WebSocketConfig",
    "MCPConfig",
    "ConfigLoader",
]
