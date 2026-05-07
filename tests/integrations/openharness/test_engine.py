"""
OpenHarness 引擎测试

测试引擎模块的初始化和功能
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.integrations.openharness.config import OpenHarnessConfig
from src.integrations.openharness.engine import (
    OpenHarnessEngine,
    get_engine,
    init_openharness,
    openharness_engine,
    register_tools,
)


class TestOpenHarnessEngine:
    """OpenHarness 引擎测试类"""

    @pytest.fixture
    def engine(self):
        """创建引擎实例 fixture"""
        # 重置单例状态
        OpenHarnessEngine._instance = None
        OpenHarnessEngine._initialized = False
        return OpenHarnessEngine()

    @pytest.fixture
    def mock_harness(self):
        """模拟 Harness 类 fixture"""
        with patch("src.integrations.openharness.engine.Harness") as mock:
            harness_instance = MagicMock()
            harness_instance.register_tool = AsyncMock()
            harness_instance.execute = AsyncMock(return_value={"result": "success"})
            harness_instance.execute_stream = AsyncMock(return_value=iter(["chunk1", "chunk2"]))
            harness_instance.load_skill = AsyncMock()
            harness_instance.create_subagent = AsyncMock(return_value=MagicMock())
            mock.return_value = harness_instance
            yield mock, harness_instance

    @pytest.fixture
    def mock_harness_config(self):
        """模拟 HarnessConfig 类 fixture"""
        with patch("src.integrations.openharness.engine.HarnessConfig") as mock:
            config_instance = MagicMock()
            mock.return_value = config_instance
            yield mock

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """测试单例模式"""
        # 重置单例
        OpenHarnessEngine._instance = None
        OpenHarnessEngine._initialized = False

        engine1 = OpenHarnessEngine()
        engine2 = OpenHarnessEngine()

        assert engine1 is engine2

    @pytest.mark.asyncio
    async def test_initialization_disabled(self, engine):
        """测试禁用时初始化"""
        with patch.object(engine.config, "OPENHARNESS_ENABLED", False):
            result = await engine.initialize()
            assert result is False

    @pytest.mark.asyncio
    async def test_initialization_import_error(self, engine):
        """测试导入错误处理"""
        with patch("src.integrations.openharness.engine.Harness", side_effect=ImportError):
            result = await engine.initialize()
            assert result is False

    @pytest.mark.asyncio
    async def test_successful_initialization(self, engine, mock_harness, mock_harness_config):
        """测试成功初始化"""
        mock_harness_class, mock_harness_instance = mock_harness

        result = await engine.initialize()

        assert result is True
        assert engine.is_initialized() is True
        mock_harness_config.assert_called_once()
        mock_harness_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_exception(self, engine):
        """测试初始化异常处理"""
        with patch("src.integrations.openharness.engine.Harness", side_effect=Exception("Test error")):
            result = await engine.initialize()
            assert result is False

    @pytest.mark.asyncio
    async def test_register_tools_success(self, engine, mock_harness):
        """测试成功注册工具"""
        mock_harness_class, mock_harness_instance = mock_harness

        # 先初始化引擎
        await engine.initialize()

        # 注册工具
        tools = [MagicMock(), MagicMock()]
        result = await engine.register_tools(tools)

        assert result is True
        assert engine.are_tools_registered() is True
        assert mock_harness_instance.register_tool.call_count == 2

    @pytest.mark.asyncio
    async def test_register_tools_not_initialized(self, engine):
        """测试未初始化时注册工具"""
        tools = [MagicMock()]
        result = await engine.register_tools(tools)

        assert result is False

    @pytest.mark.asyncio
    async def test_register_tools_exception(self, engine, mock_harness):
        """测试注册工具异常"""
        mock_harness_class, mock_harness_instance = mock_harness
        mock_harness_instance.register_tool = AsyncMock(side_effect=Exception("Test error"))

        await engine.initialize()

        tools = [MagicMock()]
        result = await engine.register_tools(tools)

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_success(self, engine, mock_harness):
        """测试成功执行"""
        mock_harness_class, mock_harness_instance = mock_harness

        await engine.initialize()

        result = await engine.execute("Test prompt", stream=False)

        mock_harness_instance.execute.assert_called_once_with("Test prompt", context=None)

    @pytest.mark.asyncio
    async def test_execute_stream(self, engine, mock_harness):
        """测试流式执行"""
        mock_harness_class, mock_harness_instance = mock_harness

        await engine.initialize()

        result = await engine.execute("Test prompt", stream=True)

        mock_harness_instance.execute_stream.assert_called_once_with("Test prompt", context=None)

    @pytest.mark.asyncio
    async def test_execute_not_initialized(self, engine):
        """测试未初始化时执行"""
        with pytest.raises(RuntimeError, match="OpenHarness 引擎未初始化"):
            await engine.execute("Test prompt")

    @pytest.mark.asyncio
    async def test_execute_exception(self, engine, mock_harness):
        """测试执行异常"""
        mock_harness_class, mock_harness_instance = mock_harness
        mock_harness_instance.execute = AsyncMock(side_effect=Exception("Test error"))

        await engine.initialize()

        with pytest.raises(RuntimeError):
            await engine.execute("Test prompt", stream=False)

    @pytest.mark.asyncio
    async def test_load_skill_success(self, engine, mock_harness):
        """测试成功加载技能"""
        mock_harness_class, mock_harness_instance = mock_harness

        await engine.initialize()

        result = await engine.load_skill("test_skill")

        assert result is True
        mock_harness_instance.load_skill.assert_called_once_with("test_skill")

    @pytest.mark.asyncio
    async def test_load_skill_not_initialized(self, engine):
        """测试未初始化时加载技能"""
        result = await engine.load_skill("test_skill")
        assert result is False

    @pytest.mark.asyncio
    async def test_create_subagent_success(self, engine, mock_harness):
        """测试成功创建子 Agent"""
        mock_harness_class, mock_harness_instance = mock_harness

        await engine.initialize()

        result = await engine.create_subagent("test_agent", "test task")

        assert result is not None
        mock_harness_instance.create_subagent.assert_called_once_with("test_agent", "test task", context=None)

    @pytest.mark.asyncio
    async def test_create_subagent_not_initialized(self, engine):
        """测试未初始化时创建子 Agent"""
        with pytest.raises(RuntimeError, match="OpenHarness 引擎未初始化"):
            await engine.create_subagent("test_agent", "test task")

    def test_get_engine(self, engine):
        """测试获取引擎实例"""
        # 重置单例
        OpenHarnessEngine._instance = None
        OpenHarnessEngine._initialized = False

        result = engine.get_engine()
        assert result is engine

    def test_is_initialized(self, engine, mock_harness):
        """测试初始化状态检查"""
        # 重置单例
        OpenHarnessEngine._instance = None
        OpenHarnessEngine._initialized = False

        engine = OpenHarnessEngine()
        assert engine.is_initialized() is False


class TestEngineConvenienceFunctions:
    """引擎便捷函数测试类"""

    @pytest.mark.asyncio
    async def test_init_openharness(self):
        """测试 init_openharness 便捷函数"""
        with patch.object(OpenHarnessEngine, "initialize", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True

            # 重置单例
            OpenHarnessEngine._instance = None
            OpenHarnessEngine._initialized = False

            result = await init_openharness()
            assert result is True

    @pytest.mark.asyncio
    async def test_register_tools_convenience(self):
        """测试 register_tools 便捷函数"""
        with patch.object(OpenHarnessEngine, "register_tools", new_callable=AsyncMock) as mock_register:
            mock_register.return_value = True

            # 重置单例
            OpenHarnessEngine._instance = None
            OpenHarnessEngine._initialized = False

            tools = [MagicMock()]
            result = await register_tools(tools)
            assert result is True

    def test_get_engine_convenience(self):
        """测试 get_engine 便捷函数"""
        # 重置单例
        OpenHarnessEngine._instance = None
        OpenHarnessEngine._initialized = False

        engine = get_engine()
        assert isinstance(engine, OpenHarnessEngine)


class TestEngineConfiguration:
    """引擎配置测试类"""

    @pytest.mark.asyncio
    async def test_config_passed_to_harness(self, mock_harness_config):
        """测试配置传递给 Harness"""
        # 重置单例
        OpenHarnessEngine._instance = None
        OpenHarnessEngine._initialized = False

        with patch("src.integrations.openharness.engine.Harness"):
            engine = OpenHarnessEngine()
            await engine.initialize()

            # 验证 HarnessConfig 被正确调用
            mock_harness_config.assert_called_once()
            call_kwargs = mock_harness_config.call_args.kwargs

            assert call_kwargs["api_format"] == engine.config.OPENHARNESS_API_FORMAT
            assert call_kwargs["model"] == engine.config.OPENHARNESS_MODEL
            assert call_kwargs["max_turns"] == engine.config.OPENHARNESS_MAX_TURNS


class TestEngineEdgeCases:
    """引擎边界情况测试类"""

    @pytest.mark.asyncio
    async def test_multiple_initialization(self, engine, mock_harness):
        """测试多次初始化"""
        mock_harness_class, mock_harness_instance = mock_harness

        # 第一次初始化
        result1 = await engine.initialize()
        assert result1 is True

        # 第二次初始化应该返回相同结果
        result2 = await engine.initialize()
        assert result2 is True

        # Harness 应该只被创建一次
        assert mock_harness_class.call_count == 1

    @pytest.mark.asyncio
    async def test_empty_tools_list(self, engine, mock_harness):
        """测试空工具列表"""
        mock_harness_class, mock_harness_instance = mock_harness

        await engine.initialize()

        result = await engine.register_tools([])
        assert result is True
        assert engine.are_tools_registered() is True

    @pytest.mark.asyncio
    async def test_context_passing(self, engine, mock_harness):
        """测试上下文传递"""
        mock_harness_class, mock_harness_instance = mock_harness

        await engine.initialize()

        context = {"user_id": "123", "session_id": "abc"}
        await engine.execute("Test", context=context)

        mock_harness_instance.execute.assert_called_once_with("Test", context=context)


@pytest.fixture(autouse=True)
def reset_singleton():
    """自动重置单例状态"""
    OpenHarnessEngine._instance = None
    OpenHarnessEngine._initialized = False
    yield
    OpenHarnessEngine._instance = None
    OpenHarnessEngine._initialized = False
