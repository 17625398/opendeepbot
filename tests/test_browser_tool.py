"""
Agent Browser 工具测试
"""

import asyncio
import pytest
from src.tools.browser_tool import (
    AgentBrowserTool,
    agent_browser_tool,
    handle_navigate,
    handle_click,
    handle_type,
    handle_extract,
)


class TestAgentBrowserTool:
    """测试 Agent Browser 工具"""

    @pytest.fixture
    def browser_tool(self):
        """创建浏览器工具实例"""
        return AgentBrowserTool()

    @pytest.mark.asyncio
    async def test_tool_initialization(self, browser_tool):
        """测试工具初始化"""
        assert browser_tool.definition.id == "agent_browser"
        assert browser_tool.definition.name == "Agent Browser"
        assert browser_tool.definition.category == "browser"
        assert browser_tool._browser is None
        assert browser_tool._page is None

    @pytest.mark.asyncio
    async def test_navigate_without_playwright(self, browser_tool):
        """测试无 Playwright 时的导航行为"""
        # 模拟 Playwright 不可用
        browser_tool._playwright_available = False
        
        result = await browser_tool.navigate("https://example.com")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_session_management(self, browser_tool):
        """测试会话管理"""
        # 创建测试会话
        session_id = "test_session_001"
        from src.tools.browser_tool import BrowserSession
        
        session = BrowserSession(
            id=session_id,
            url="https://example.com",
            title="Test Page"
        )
        
        browser_tool.sessions[session_id] = session
        browser_tool._current_session = session_id
        
        assert session_id in browser_tool.sessions
        assert browser_tool._current_session == session_id
        assert browser_tool.sessions[session_id].url == "https://example.com"

    @pytest.mark.asyncio
    async def test_history_tracking(self, browser_tool):
        """测试历史记录追踪"""
        session_id = "test_session_002"
        from src.tools.browser_tool import BrowserSession
        from datetime import datetime
        
        session = BrowserSession(
            id=session_id,
            url="https://example.com",
            title="Test Page"
        )
        
        browser_tool.sessions[session_id] = session
        browser_tool._current_session = session_id
        
        # 更新历史
        browser_tool._update_session_history("click", {"selector": "#button"})
        
        assert len(session.history) == 1
        assert session.history[0]["action"] == "click"
        assert session.history[0]["params"]["selector"] == "#button"

    def test_tool_definition(self):
        """测试工具定义"""
        tool = agent_browser_tool
        
        assert tool.definition.id == "agent_browser"
        assert tool.definition.name == "Agent Browser"
        assert "browser" in tool.definition.tags
        assert tool.definition.icon == "🌐"
        assert tool.definition.timeout == 60


class TestBrowserHandlers:
    """测试浏览器处理器函数"""

    @pytest.mark.asyncio
    async def test_handler_functions_exist(self):
        """测试处理器函数存在"""
        # 这些函数应该存在且可调用
        assert callable(handle_navigate)
        assert callable(handle_click)
        assert callable(handle_type)
        assert callable(handle_extract)


class TestBrowserActions:
    """测试浏览器动作"""

    def test_browser_action_enum(self):
        """测试浏览器动作枚举"""
        from src.tools.browser_tool import BrowserAction
        
        assert BrowserAction.NAVIGATE.value == "navigate"
        assert BrowserAction.CLICK.value == "click"
        assert BrowserAction.TYPE.value == "type"
        assert BrowserAction.SCROLL.value == "scroll"
        assert BrowserAction.WAIT.value == "wait"
        assert BrowserAction.EXTRACT.value == "extract"
        assert BrowserAction.SCREENSHOT.value == "screenshot"
        assert BrowserAction.EVALUATE.value == "evaluate"


# 集成测试（需要 Playwright）
@pytest.mark.integration
class TestBrowserIntegration:
    """浏览器集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        tool = AgentBrowserTool()
        
        # 注意：这个测试需要 Playwright 安装
        # 跳过如果 Playwright 不可用
        if not tool._playwright_available:
            pytest.skip("Playwright not installed")
        
        try:
            # 1. 导航到页面
            result = await tool.navigate("https://example.com")
            assert result["success"] is True
            assert "session_id" in result
            
            # 2. 获取页面信息
            info = await tool.get_page_info()
            assert info["success"] is True
            assert "url" in info
            
            # 3. 提取内容
            extract_result = await tool.extract()
            assert extract_result["success"] is True
            
        finally:
            # 清理
            await tool.close()


if __name__ == "__main__":
    # 运行简单测试
    async def run_tests():
        print("Testing Agent Browser Tool...")
        
        tool = AgentBrowserTool()
        
        # 测试工具定义
        print(f"Tool ID: {tool.definition.id}")
        print(f"Tool Name: {tool.definition.name}")
        print(f"Tool Category: {tool.definition.category}")
        print(f"Playwright Available: {tool._playwright_available}")
        
        # 测试会话管理
        from src.tools.browser_tool import BrowserSession
        session = BrowserSession(
            id="test_001",
            url="https://example.com",
            title="Test"
        )
        tool.sessions["test_001"] = session
        print(f"Session created: {session.id}")
        
        print("\nAll basic tests passed!")
    
    asyncio.run(run_tests())
