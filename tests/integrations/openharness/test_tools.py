"""
OpenHarness 工具桥接测试

测试工具适配器和注册表功能
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from src.integrations.openharness.tools.adapter import (
    BaseToolAdapter,
    PermissionLevel,
    ToolExecutionError,
    ToolPermissionError,
    ToolRegistry,
    ToolResult,
    ToolValidationError,
    register_tool,
    tool_registry,
)


# 测试用的输入模型
class TestInput(BaseModel):
    """测试输入模型"""
    message: str = Field(description="测试消息")
    count: int = Field(default=1, description="计数")


class ValidTool(BaseToolAdapter):
    """有效的测试工具"""
    name = "test_tool"
    description = "A test tool"
    version = "1.0.0"
    input_model = TestInput
    required_permission = PermissionLevel.READONLY
    timeout = 10

    async def execute(self, **kwargs) -> ToolResult:
        message = kwargs.get("message", "")
        count = kwargs.get("count", 1)
        return ToolResult.success(data={"echo": message, "count": count})


class ErrorTool(BaseToolAdapter):
    """会抛出异常的工具"""
    name = "error_tool"
    description = "A tool that always errors"
    input_model = TestInput

    async def execute(self, **kwargs) -> ToolResult:
        raise Exception("Test error")


class PermissionTool(BaseToolAdapter):
    """需要权限的工具"""
    name = "permission_tool"
    description = "A tool requiring permissions"
    input_model = TestInput
    required_permission = PermissionLevel.ADMIN

    async def _check_permission(self) -> bool:
        raise ToolPermissionError("Admin permission required")

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult.success(data={"authorized": True})


class TestToolResult:
    """工具结果测试类"""

    def test_success_result(self):
        """测试成功结果"""
        data = {"key": "value"}
        result = ToolResult.success(data, execution_time=0.5)

        assert result.success is True
        assert result.data == data
        assert result.error is None
        assert result.execution_time == 0.5
        assert result.timestamp is not None

    def test_error_result(self):
        """测试错误结果"""
        error_msg = "Something went wrong"
        result = ToolResult.error(error_msg, execution_time=0.3)

        assert result.success is False
        assert result.data is None
        assert result.error == error_msg
        assert result.execution_time == 0.3

    def test_to_dict(self):
        """测试转换为字典"""
        result = ToolResult.success({"test": "data"})
        data = result.to_dict()

        assert data["success"] is True
        assert data["data"] == {"test": "data"}
        assert "timestamp" in data


class TestBaseToolAdapter:
    """工具适配器基类测试"""

    def test_valid_tool_creation(self):
        """测试有效工具创建"""
        tool = ValidTool()

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.version == "1.0.0"
        assert tool.required_permission == PermissionLevel.READONLY

    def test_missing_name(self):
        """测试缺少名称"""
        class NoNameTool(BaseToolAdapter):
            description = "Test"
            input_model = TestInput

        with pytest.raises(ValueError, match="must define a name"):
            NoNameTool()

    def test_missing_description(self):
        """测试缺少描述"""
        class NoDescTool(BaseToolAdapter):
            name = "test"
            input_model = TestInput

        with pytest.raises(ValueError, match="must define a description"):
            NoDescTool()

    def test_missing_input_model(self):
        """测试缺少输入模型"""
        class NoModelTool(BaseToolAdapter):
            name = "test"
            description = "Test"

        with pytest.raises(ValueError, match="must define an input_model"):
            NoModelTool()

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """测试成功执行"""
        tool = ValidTool()
        result = await tool.run(message="Hello", count=3)

        assert result.success is True
        assert result.data["echo"] == "Hello"
        assert result.data["count"] == 3

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """测试参数验证"""
        tool = ValidTool()

        # 缺少必填参数
        with pytest.raises(Exception):
            await tool.run()

    @pytest.mark.asyncio
    async def test_execution_error_handling(self):
        """测试执行错误处理"""
        tool = ErrorTool()
        result = await tool.run(message="test")

        assert result.success is False
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_permission_check(self):
        """测试权限检查"""
        tool = PermissionTool()
        result = await tool.run(message="test")

        assert result.success is False
        assert "Permission denied" in result.error

    def test_get_schema(self):
        """测试获取 Schema"""
        tool = ValidTool()
        schema = tool.get_schema()

        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert "parameters" in schema

    def test_get_openharness_schema(self):
        """测试获取 OpenHarness Schema"""
        tool = ValidTool()
        schema = tool.get_openharness_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert "parameters" in schema["function"]

    def test_get_stats(self):
        """测试获取统计信息"""
        tool = ValidTool()

        stats = tool.get_stats()
        assert stats["name"] == "test_tool"
        assert stats["execution_count"] == 0
        assert stats["error_count"] == 0
        assert stats["success_rate"] == 0


class TestToolRegistry:
    """工具注册表测试类"""

    @pytest.fixture
    def registry(self):
        """创建新的注册表 fixture"""
        return ToolRegistry()

    def test_register_tool(self, registry):
        """测试注册工具"""
        tool = ValidTool()
        result = registry.register(tool)

        assert result is True
        assert "test_tool" in registry.list_tools()

    def test_register_duplicate(self, registry):
        """测试重复注册"""
        tool = ValidTool()
        registry.register(tool)

        # 重复注册应该覆盖
        result = registry.register(tool)
        assert result is True

    def test_unregister_tool(self, registry):
        """测试注销工具"""
        tool = ValidTool()
        registry.register(tool)

        result = registry.unregister("test_tool")
        assert result is True
        assert "test_tool" not in registry.list_tools()

    def test_unregister_nonexistent(self, registry):
        """测试注销不存在的工具"""
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_tool(self, registry):
        """测试获取工具"""
        tool = ValidTool()
        registry.register(tool)

        retrieved = registry.get("test_tool")
        assert retrieved is not None
        assert retrieved.name == "test_tool"

    def test_get_nonexistent(self, registry):
        """测试获取不存在的工具"""
        retrieved = registry.get("nonexistent")
        assert retrieved is None

    def test_list_tools(self, registry):
        """测试列出工具"""
        tool1 = ValidTool()
        tool2 = ErrorTool()

        registry.register(tool1)
        registry.register(tool2)

        tools = registry.list_tools()
        assert len(tools) == 2
        assert "test_tool" in tools
        assert "error_tool" in tools

    def test_get_schemas(self, registry):
        """测试获取所有 Schema"""
        tool = ValidTool()
        registry.register(tool)

        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "test_tool"

    def test_get_openharness_schemas(self, registry):
        """测试获取 OpenHarness Schema"""
        tool = ValidTool()
        registry.register(tool)

        schemas = registry.get_openharness_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"

    @pytest.mark.asyncio
    async def test_execute_tool(self, registry):
        """测试执行工具"""
        tool = ValidTool()
        registry.register(tool)

        result = await registry.execute("test_tool", message="Hello")

        assert result.success is True
        assert result.data["echo"] == "Hello"

    @pytest.mark.asyncio
    async def test_execute_nonexistent(self, registry):
        """测试执行不存在的工具"""
        result = await registry.execute("nonexistent")

        assert result.success is False
        assert "not found" in result.error

    def test_get_history(self, registry):
        """测试获取执行历史"""
        # 初始为空
        history = registry.get_history()
        assert len(history) == 0

    def test_clear_history(self, registry):
        """测试清除历史"""
        registry.clear_history()
        history = registry.get_history()
        assert len(history) == 0

    def test_get_all_stats(self, registry):
        """测试获取所有统计"""
        tool = ValidTool()
        registry.register(tool)

        stats = registry.get_all_stats()
        assert "tools" in stats
        assert "total_executions" in stats
        assert "total_errors" in stats


class TestRegisterToolDecorator:
    """工具注册装饰器测试类"""

    def test_register_decorator(self):
        """测试装饰器注册"""
        # 重置全局注册表
        tool_registry._tools.clear()

        @register_tool
        class DecoratedTool(BaseToolAdapter):
            name = "decorated_tool"
            description = "A decorated tool"
            input_model = TestInput

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult.success(data={"decorated": True})

        # 验证工具已注册
        assert "decorated_tool" in tool_registry.list_tools()


class TestPermissionLevels:
    """权限级别测试类"""

    def test_permission_constants(self):
        """测试权限常量"""
        assert PermissionLevel.READONLY == "readonly"
        assert PermissionLevel.WRITE == "write"
        assert PermissionLevel.DELETE == "delete"
        assert PermissionLevel.EXECUTE == "execute"
        assert PermissionLevel.ADMIN == "admin"


class TestToolExceptions:
    """工具异常测试类"""

    def test_tool_permission_error(self):
        """测试权限错误"""
        error = ToolPermissionError("Access denied")
        assert str(error) == "Access denied"

    def test_tool_validation_error(self):
        """测试验证错误"""
        error = ToolValidationError("Invalid params")
        assert str(error) == "Invalid params"

    def test_tool_execution_error(self):
        """测试执行错误"""
        error = ToolExecutionError("Execution failed")
        assert str(error) == "Execution failed"


class TestToolEdgeCases:
    """工具边界情况测试类"""

    @pytest.mark.asyncio
    async def test_empty_params(self):
        """测试空参数"""
        class EmptyParamsTool(BaseToolAdapter):
            name = "empty_params_tool"
            description = "Tool with no params"
            input_model = TestInput

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult.success(data={})

        tool = EmptyParamsTool()
        result = await tool.run(message="test", count=1)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_unicode_params(self):
        """测试 Unicode 参数"""
        tool = ValidTool()
        result = await tool.run(message="中文测试 🎉", count=1)

        assert result.success is True
        assert result.data["echo"] == "中文测试 🎉"

    def test_tool_repr(self):
        """测试工具表示"""
        tool = ValidTool()
        repr_str = repr(tool)

        assert "ValidTool" in repr_str
        assert "test_tool" in repr_str


@pytest.fixture(autouse=True)
def reset_registry():
    """自动重置注册表"""
    tool_registry._tools.clear()
    tool_registry._history.clear()
    yield
    tool_registry._tools.clear()
    tool_registry._history.clear()
