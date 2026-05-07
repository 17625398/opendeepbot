"""
OpenHarness 配置测试

测试配置模块的初始化和功能
"""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.integrations.openharness.config import (
    DeepTutorOpenHarnessConfig,
    OpenHarnessConfig,
    get_deeptutor_config,
    get_openharness_config,
    openharness_config,
    deeptutor_config,
)


class TestOpenHarnessConfig:
    """OpenHarness 配置测试类"""

    def test_default_config(self):
        """测试默认配置"""
        config = OpenHarnessConfig()

        assert config.OPENHARNESS_ENABLED is True
        assert config.OPENHARNESS_DEBUG is False
        assert config.OPENHARNESS_API_FORMAT == "anthropic"
        assert config.OPENHARNESS_MODEL == "claude-3-5-sonnet-20241022"
        assert config.OPENHARNESS_MAX_TURNS == 100
        assert config.OPENHARNESS_EFFORT == "normal"
        assert config.OPENHARNESS_PERMISSION_MODE == "default"
        assert config.OPENHARNESS_DANGEROUSLY_SKIP_PERMISSIONS is False
        assert config.OPENHARNESS_MEMORY_ENABLED is True
        assert config.OPENHARNESS_MEMORY_AUTO_COMPACT is True
        assert config.OPENHARNESS_MEMORY_MAX_TOKENS == 4000
        assert config.OPENHARNESS_SWARM_ENABLED is True
        assert config.OPENHARNESS_MAX_SUBAGENTS == 5
        assert config.OPENHARNESS_TASK_TIMEOUT == 300

    def test_path_configuration(self):
        """测试路径配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = OpenHarnessConfig(
                OPENHARNESS_HOME=Path(tmpdir),
                OPENHARNESS_SKILLS_DIR=Path(tmpdir) / "custom_skills",
                OPENHARNESS_MEMORY_DIR=Path(tmpdir) / "custom_memory",
                OPENHARNESS_PLUGINS_DIR=Path(tmpdir) / "custom_plugins",
            )

            assert config.OPENHARNESS_HOME == Path(tmpdir)
            assert config.OPENHARNESS_SKILLS_DIR == Path(tmpdir) / "custom_skills"
            assert config.OPENHARNESS_MEMORY_DIR == Path(tmpdir) / "custom_memory"
            assert config.OPENHARNESS_PLUGINS_DIR == Path(tmpdir) / "custom_plugins"

            # 验证目录已创建
            assert config.OPENHARNESS_SKILLS_DIR.exists()
            assert config.OPENHARNESS_MEMORY_DIR.exists()
            assert config.OPENHARNESS_PLUGINS_DIR.exists()

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("OPENHARNESS_ENABLED", "false")
        monkeypatch.setenv("OPENHARNESS_DEBUG", "true")
        monkeypatch.setenv("OPENHARNESS_MODEL", "claude-3-opus")
        monkeypatch.setenv("OPENHARNESS_MAX_TURNS", "50")

        config = OpenHarnessConfig()

        assert config.OPENHARNESS_ENABLED is False
        assert config.OPENHARNESS_DEBUG is True
        assert config.OPENHARNESS_MODEL == "claude-3-opus"
        assert config.OPENHARNESS_MAX_TURNS == 50

    def test_boolean_parsing(self, monkeypatch):
        """测试布尔值解析"""
        # 测试各种 true 值
        for val in ["true", "True", "TRUE", "1", "yes", "Yes"]:
            monkeypatch.setenv("OPENHARNESS_ENABLED", val)
            config = OpenHarnessConfig()
            assert config.OPENHARNESS_ENABLED is True, f"Failed for value: {val}"

        # 测试各种 false 值
        for val in ["false", "False", "FALSE", "0", "no", "No"]:
            monkeypatch.setenv("OPENHARNESS_ENABLED", val)
            config = OpenHarnessConfig()
            assert config.OPENHARNESS_ENABLED is False, f"Failed for value: {val}"


class TestDeepTutorOpenHarnessConfig:
    """DeepTutor OpenHarness 配置测试类"""

    def test_default_deeptutor_config(self):
        """测试默认 DeepTutor 配置"""
        config = DeepTutorOpenHarnessConfig()

        assert config.tool_bridge_enabled is True
        assert config.tool_prefix == "dt_"
        assert config.skill_sync_enabled is True
        assert config.skill_sync_interval == 300
        assert config.memory_integration_enabled is True
        assert config.memory_file_name == "MEMORY.md"
        assert config.claude_md_file_name == "CLAUDE.md"
        assert config.frontend_commands_enabled is True
        assert config.frontend_tool_display_enabled is True
        assert config.api_prefix == "/api/v1/openharness"
        assert config.websocket_enabled is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = DeepTutorOpenHarnessConfig(
            tool_bridge_enabled=False,
            tool_prefix="custom_",
            skill_sync_interval=600,
            api_prefix="/api/v2/openharness",
        )

        assert config.tool_bridge_enabled is False
        assert config.tool_prefix == "custom_"
        assert config.skill_sync_interval == 600
        assert config.api_prefix == "/api/v2/openharness"


class TestConfigFunctions:
    """配置函数测试类"""

    def test_get_openharness_config(self):
        """测试获取 OpenHarness 配置"""
        config = get_openharness_config()
        assert isinstance(config, OpenHarnessConfig)

    def test_get_deeptutor_config(self):
        """测试获取 DeepTutor 配置"""
        config = get_deeptutor_config()
        assert isinstance(config, DeepTutorOpenHarnessConfig)

    def test_global_instances(self):
        """测试全局配置实例"""
        assert isinstance(openharness_config, OpenHarnessConfig)
        assert isinstance(deeptutor_config, DeepTutorOpenHarnessConfig)


class TestConfigValidation:
    """配置验证测试类"""

    def test_invalid_max_turns(self):
        """测试无效的最大轮数"""
        # 负数应该被接受，但实际使用时可能需要验证
        config = OpenHarnessConfig(OPENHARNESS_MAX_TURNS=-1)
        assert config.OPENHARNESS_MAX_TURNS == -1

    def test_invalid_timeout(self):
        """测试无效的超时时间"""
        config = OpenHarnessConfig(OPENHARNESS_TASK_TIMEOUT=0)
        assert config.OPENHARNESS_TASK_TIMEOUT == 0

    def test_empty_model(self):
        """测试空模型名称"""
        config = OpenHarnessConfig(OPENHARNESS_MODEL="")
        assert config.OPENHARNESS_MODEL == ""


class TestConfigEdgeCases:
    """配置边界情况测试类"""

    def test_path_with_spaces(self):
        """测试带空格的路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path_with_spaces = Path(tmpdir) / "path with spaces"
            config = OpenHarnessConfig(OPENHARNESS_HOME=path_with_spaces)
            assert config.OPENHARNESS_HOME == path_with_spaces
            assert config.OPENHARNESS_HOME.exists()

    def test_unicode_path(self):
        """测试 Unicode 路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_path = Path(tmpdir) / "中文路径"
            config = OpenHarnessConfig(OPENHARNESS_HOME=unicode_path)
            assert config.OPENHARNESS_HOME == unicode_path
            assert config.OPENHARNESS_HOME.exists()

    def test_nested_directories(self):
        """测试嵌套目录创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "a" / "b" / "c" / "openharness"
            config = OpenHarnessConfig(OPENHARNESS_HOME=nested_path)
            assert config.OPENHARNESS_HOME.exists()
            assert config.OPENHARNESS_SKILLS_DIR.exists()


@pytest.fixture
def temp_config_dir():
    """临时配置目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """模拟环境变量 fixture"""
    env_vars = {
        "OPENHARNESS_ENABLED": "true",
        "OPENHARNESS_DEBUG": "false",
        "OPENHARNESS_MODEL": "claude-3-5-sonnet",
        "OPENHARNESS_MAX_TURNS": "100",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
