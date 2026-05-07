"""Tests for the configuration module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from deeptutor.config import (
    LLMConfig,
    TelegramConfig,
    DiscordConfig,
    SlackConfig,
    EmailConfig,
    WebSocketConfig,
    DeepTutorConfig,
    ConfigLoader,
    load_config,
    validate_config,
)


class TestLLMConfig:
    """Tests for LLMConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == "deepseek"
        assert config.model == "deepseek-chat"
        assert config.api_key == ""
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
    
    def test_validate_valid_config(self):
        """Test validation with valid config."""
        config = LLMConfig(api_key="test-key", model="test-model")
        errors = config.validate()
        assert errors == []
    
    def test_validate_missing_api_key(self):
        """Test validation with missing API key."""
        config = LLMConfig(model="test-model")
        errors = config.validate()
        assert "LLM API key is required" in errors
    
    def test_validate_missing_model(self):
        """Test validation with missing model."""
        config = LLMConfig(api_key="test-key")
        errors = config.validate()
        assert "LLM model is required" in errors
    
    def test_validate_invalid_temperature(self):
        """Test validation with invalid temperature."""
        config = LLMConfig(api_key="test-key", model="test-model", temperature=-0.1)
        errors = config.validate()
        assert "Temperature must be between 0 and 2" in errors
        
        config.temperature = 2.1
        errors = config.validate()
        assert "Temperature must be between 0 and 2" in errors


class TestChannelConfigs:
    """Tests for channel configuration classes."""
    
    def test_telegram_config_valid(self):
        """Test valid Telegram config."""
        config = TelegramConfig(enabled=True, token="test-token")
        errors = config.validate()
        assert errors == []
    
    def test_telegram_config_missing_token(self):
        """Test Telegram config with missing token when enabled."""
        config = TelegramConfig(enabled=True)
        errors = config.validate()
        assert "Telegram token is required when enabled" in errors
    
    def test_telegram_config_disabled_no_token(self):
        """Test Telegram config disabled doesn't need token."""
        config = TelegramConfig(enabled=False)
        errors = config.validate()
        assert errors == []
    
    def test_discord_config_valid(self):
        """Test valid Discord config."""
        config = DiscordConfig(enabled=True, token="test-token")
        errors = config.validate()
        assert errors == []
    
    def test_slack_config_valid(self):
        """Test valid Slack config."""
        config = SlackConfig(
            enabled=True,
            bot_token="test-bot-token",
            app_token="test-app-token"
        )
        errors = config.validate()
        assert errors == []
    
    def test_slack_config_missing_tokens(self):
        """Test Slack config with missing tokens."""
        config = SlackConfig(enabled=True)
        errors = config.validate()
        assert "Slack bot token is required when enabled" in errors
        assert "Slack app token is required when enabled" in errors
    
    def test_email_config_valid(self):
        """Test valid Email config."""
        config = EmailConfig(
            enabled=True,
            username="test@example.com",
            password="test-password"
        )
        errors = config.validate()
        assert errors == []
    
    def test_websocket_config_valid_port(self):
        """Test valid WebSocket port."""
        config = WebSocketConfig(enabled=True, port=8765)
        errors = config.validate()
        assert errors == []
    
    def test_websocket_config_invalid_port(self):
        """Test invalid WebSocket port."""
        config = WebSocketConfig(enabled=True, port=0)
        errors = config.validate()
        assert "WebSocket port must be between 1 and 65535" in errors
        
        config.port = 65536
        errors = config.validate()
        assert "WebSocket port must be between 1 and 65535" in errors


class TestDeepTutorConfig:
    """Tests for DeepTutorConfig class."""
    
    def test_is_valid(self):
        """Test is_valid method."""
        config = DeepTutorConfig()
        config.llm.api_key = "test-key"
        config.llm.model = "test-model"
        assert config.is_valid() is True
    
    def test_is_invalid(self):
        """Test is_valid with invalid config."""
        config = DeepTutorConfig()
        assert config.is_valid() is False
    
    def test_validate_combines_errors(self):
        """Test validate combines all errors."""
        config = DeepTutorConfig()
        # LLM config has errors
        config.llm.api_key = ""
        
        # Add an invalid channel
        telegram_config = TelegramConfig(enabled=True)
        config.channels["telegram"] = telegram_config
        
        errors = config.validate()
        assert len(errors) >= 2


class TestConfigLoader:
    """Tests for ConfigLoader class."""
    
    def test_init_with_env_file(self):
        """Test initializing with env file."""
        with patch("deeptutor.config.load_dotenv") as mock_load:
            loader = ConfigLoader(".env.test")
            mock_load.assert_called_once_with(".env.test")
    
    def test_load_from_env(self, monkeypatch):
        """Test loading from environment variables."""
        monkeypatch.setenv("LLM_PROVIDER", "test-provider")
        monkeypatch.setenv("LLM_MODEL", "test-model")
        monkeypatch.setenv("LLM_API_KEY", "test-api-key")
        monkeypatch.setenv("TELEGRAM_ENABLED", "true")
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-telegram-token")
        
        loader = ConfigLoader()
        config = loader.load_from_env()
        
        assert config.llm.provider == "test-provider"
        assert config.llm.model == "test-model"
        assert config.llm.api_key == "test-api-key"
        assert config.channels["telegram"].enabled is True
        assert config.channels["telegram"].token == "test-telegram-token"
    
    def test_load_from_yaml(self, temp_dir):
        """Test loading from YAML file."""
        yaml_content = """
llm:
  provider: yaml-provider
  model: yaml-model
  api_key: yaml-key
"""
        yaml_path = temp_dir / "config.yaml"
        yaml_path.write_text(yaml_content)
        
        loader = ConfigLoader()
        config = loader.load_from_yaml(str(yaml_path))
        
        assert config.llm.provider == "yaml-provider"
        assert config.llm.model == "yaml-model"
        assert config.llm.api_key == "yaml-key"
    
    def test_load_from_yaml_file_not_found(self):
        """Test loading from non-existent YAML file."""
        loader = ConfigLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_from_yaml("nonexistent.yaml")


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_load_config(self, monkeypatch):
        """Test load_config function."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "test-model")
        
        config = load_config()
        assert config.llm.api_key == "test-key"
        assert config.llm.model == "test-model"
    
    def test_validate_config_valid(self):
        """Test validate_config with valid config."""
        config = DeepTutorConfig()
        config.llm.api_key = "test-key"
        config.llm.model = "test-model"
        
        with patch("deeptutor.config.logger") as mock_logger:
            result = validate_config(config)
            assert result is True
            mock_logger.info.assert_called_with("Configuration is valid")
    
    def test_validate_config_invalid(self):
        """Test validate_config with invalid config."""
        config = DeepTutorConfig()
        
        with patch("deeptutor.config.logger") as mock_logger:
            result = validate_config(config)
            assert result is False
            mock_logger.error.assert_called()
