"""DeepTutor Configuration Module

Handles loading and validating configuration from environment variables and config files.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if not self.api_key:
            errors.append("LLM API key is required")
        if not self.model:
            errors.append("LLM model is required")
        if self.temperature < 0 or self.temperature > 2:
            errors.append("Temperature must be between 0 and 2")
        return errors


@dataclass
class ChannelConfig:
    """通用通道配置"""
    enabled: bool = False
    name: str = ""


@dataclass
class TelegramConfig(ChannelConfig):
    """Telegram 通道配置"""
    token: str = ""
    name: str = "telegram"
    
    def validate(self) -> List[str]:
        errors = []
        if self.enabled and not self.token:
            errors.append("Telegram token is required when enabled")
        return errors


@dataclass
class DiscordConfig(ChannelConfig):
    """Discord 通道配置"""
    token: str = ""
    prefix: str = "!"
    name: str = "discord"
    
    def validate(self) -> List[str]:
        errors = []
        if self.enabled and not self.token:
            errors.append("Discord token is required when enabled")
        return errors


@dataclass
class SlackConfig(ChannelConfig):
    """Slack 通道配置"""
    bot_token: str = ""
    app_token: str = ""
    name: str = "slack"
    
    def validate(self) -> List[str]:
        errors = []
        if self.enabled:
            if not self.bot_token:
                errors.append("Slack bot token is required when enabled")
            if not self.app_token:
                errors.append("Slack app token is required when enabled")
        return errors


@dataclass
class EmailConfig(ChannelConfig):
    """Email 通道配置"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    username: str = ""
    password: str = ""
    from_email: str = ""
    name: str = "email"
    
    def validate(self) -> List[str]:
        errors = []
        if self.enabled:
            if not self.username:
                errors.append("Email username is required when enabled")
            if not self.password:
                errors.append("Email password is required when enabled")
        return errors


@dataclass
class WebSocketConfig(ChannelConfig):
    """WebSocket 通道配置"""
    host: str = "localhost"
    port: int = 8765
    name: str = "websocket"
    
    def validate(self) -> List[str]:
        errors = []
        if self.enabled:
            if self.port < 1 or self.port > 65535:
                errors.append("WebSocket port must be between 1 and 65535")
        return errors


@dataclass
class MCPConfig:
    """MCP 配置"""
    enabled: bool = True
    servers: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        errors = []
        return errors


@dataclass
class DeepTutorConfig:
    """完整的 DeepTutor 配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    channels: Dict[str, ChannelConfig] = field(default_factory=dict)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    
    def validate(self) -> List[str]:
        """验证所有配置"""
        errors = []
        
        errors.extend(self.llm.validate())
        
        for name, channel in self.channels.items():
            if hasattr(channel, "validate"):
                errors.extend(channel.validate())
        
        errors.extend(self.mcp.validate())
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate()) == 0


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, env_file: Optional[str] = None):
        if env_file:
            load_dotenv(env_file)
        else:
            # 尝试从默认位置加载
            for path in [".env", ".env.local"]:
                if Path(path).exists():
                    load_dotenv(path)
                    logger.info(f"Loaded config from {path}")
                    break
    
    def load_from_env(self) -> DeepTutorConfig:
        """从环境变量加载配置"""
        config = DeepTutorConfig()
        
        # LLM 配置
        config.llm.provider = os.getenv("LLM_PROVIDER", "deepseek")
        config.llm.model = os.getenv("LLM_MODEL", "deepseek-chat")
        config.llm.api_key = os.getenv("LLM_API_KEY", "")
        config.llm.base_url = os.getenv("LLM_BASE_URL", "")
        
        # 通道配置
        config.channels["telegram"] = TelegramConfig(
            enabled=os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            token=os.getenv("TELEGRAM_TOKEN", ""),
        )
        
        config.channels["discord"] = DiscordConfig(
            enabled=os.getenv("DISCORD_ENABLED", "false").lower() == "true",
            token=os.getenv("DISCORD_TOKEN", ""),
            prefix=os.getenv("DISCORD_PREFIX", "!"),
        )
        
        config.channels["slack"] = SlackConfig(
            enabled=os.getenv("SLACK_ENABLED", "false").lower() == "true",
            bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
            app_token=os.getenv("SLACK_APP_TOKEN", ""),
        )
        
        config.channels["email"] = EmailConfig(
            enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            smtp_host=os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            imap_host=os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com"),
            imap_port=int(os.getenv("EMAIL_IMAP_PORT", "993")),
            username=os.getenv("EMAIL_USERNAME", ""),
            password=os.getenv("EMAIL_PASSWORD", ""),
            from_email=os.getenv("EMAIL_FROM", ""),
        )
        
        config.channels["websocket"] = WebSocketConfig(
            enabled=os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true",
            host=os.getenv("WEBSOCKET_HOST", "localhost"),
            port=int(os.getenv("WEBSOCKET_PORT", "8765")),
        )
        
        # MCP 配置
        config.mcp.enabled = os.getenv("MCP_ENABLED", "true").lower() == "true"
        
        return config
    
    def load_from_yaml(self, filepath: str) -> DeepTutorConfig:
        """从 YAML 文件加载配置"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        config = DeepTutorConfig()
        
        # 解析 LLM 配置
        if "llm" in data:
            llm_data = data["llm"]
            config.llm.provider = llm_data.get("provider", "deepseek")
            config.llm.model = llm_data.get("model", "deepseek-chat")
            config.llm.api_key = llm_data.get("api_key", "")
            config.llm.base_url = llm_data.get("base_url", "")
        
        # 解析通道配置
        if "channels" in data:
            # 这里可以根据需要解析各个通道的配置
            pass
        
        return config
    
    def load(self, env_file: Optional[str] = None, yaml_file: Optional[str] = None) -> DeepTutorConfig:
        """加载配置（YAML 优先，然后环境变量）"""
        config = DeepTutorConfig()
        
        if yaml_file:
            config = self.load_from_yaml(yaml_file)
        
        # 环境变量会覆盖 YAML 配置
        env_config = self.load_from_env()
        
        # 合并配置
        config.llm = env_config.llm
        config.channels.update(env_config.channels)
        config.mcp = env_config.mcp
        
        return config


def load_config(env_file: Optional[str] = None) -> DeepTutorConfig:
    """加载配置的便捷函数"""
    loader = ConfigLoader(env_file)
    return loader.load_from_env()


def validate_config(config: DeepTutorConfig) -> bool:
    """验证配置并输出错误信息"""
    errors = config.validate()
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("Configuration is valid")
    return True
