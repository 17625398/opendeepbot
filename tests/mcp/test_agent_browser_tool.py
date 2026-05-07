"""
Agent-Browser MCP Tool 测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.integrations.mcp.agent_browser_tool import (
    AgentBrowserTool,
    AgentBrowserError,
    CommandTimeoutError,
    agent_browser_open,
    agent_browser_snapshot,
    agent_browser_click,
    agent_browser_fill,
)


class TestAgentBrowserTool:
    """AgentBrowserTool 单元测试"""
    
    @pytest.fixture
    def tool(self):
        """创建工具实例"""
        return AgentBrowserTool(timeout=30, session="test_session")
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, tool):
        """测试初始化成功"""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/agent-browser'
            
            with patch.object(tool, '_run_command') as mock_run:
                mock_run.return_value = {
                    'stdout': 'help text',
                    'stderr': '',
                    'returncode': 0
                }
                
                result = await tool.initialize()
                assert result is True
                assert tool._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_not_found(self, tool):
        """测试未找到 agent-browser"""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None
            
            with patch.object(tool, '_run_command') as mock_run:
                mock_run.return_value = {
                    'stdout': '',
                    'stderr': 'not found',
                    'returncode': 1
                }
                
                result = await tool.initialize()
                assert result is False
    
    @pytest.mark.asyncio
    async def test_browser_open_success(self, tool):
        """测试打开网页成功"""
        with patch.object(tool, '_run_command') as mock_run:
            mock_run.return_value = {
                'stdout': 'Opened https://example.com',
                'stderr': '',
                'returncode': 0
            }
            
            result = await tool.browser_open('https://example.com')
            
            assert result['success'] is True
            assert result['url'] == 'https://example.com'
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_browser_open_failure(self, tool):
        """测试打开网页失败"""
        with patch.object(tool, '_run_command') as mock_run:
            mock_run.return_value = {
                'stdout': '',
                'stderr': 'Connection failed',
                'returncode': 1
            }
            
            result = await tool.browser_open('https://invalid-url')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_browser_snapshot_success(self, tool):
        """测试获取快照成功"""
        snapshot_data = {
            'snapshot': '- heading "Example" [ref=e1]\n- button "Click" [ref=e2]',
            'refs': {
                'e1': {'role': 'heading', 'name': 'Example'},
                'e2': {'role': 'button', 'name': 'Click'}
            }
        }
        
        with patch.object(tool, '_run_command') as mock_run:
            mock_run.return_value = {
                'stdout': json.dumps({'success': True, 'data': snapshot_data}),
                'stderr': '',
                'returncode': 0,
                'json': {'success': True, 'data': snapshot_data}
            }
            
            result = await tool.browser_snapshot()
            
            assert result['success'] is True
            assert 'snapshot' in result
            assert 'refs' in result
    
    @pytest.mark.asyncio
    async def test_browser_click_success(self, tool):
        """测试点击元素成功"""
        with patch.object(tool, '_run_command') as mock_run:
            mock_run.return_value = {
                'stdout': 'Clicked @e1',
                'stderr': '',
                'returncode': 0
            }
            
            result = await tool.browser_click('@e1')
            
            assert result['success'] is True
            assert result['selector'] == '@e1'
    
    @pytest.mark.asyncio
    async def test_browser_fill_success(self, tool):
        """测试填充输入框成功"""
        with patch.object(tool, '_run_command') as mock_run:
            mock_run.return_value = {
                'stdout': 'Filled @e2',
                'stderr': '',
                'returncode': 0
            }
            
            result = await tool.browser_fill('@e2', 'test@example.com')
            
            assert result['success'] is True
            assert result['selector'] == '@e2'
    
    @pytest.mark.asyncio
    async def test_command_timeout(self, tool):
        """测试命令超时"""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(
                side_effect=asyncio.TimeoutError()
            )
            mock_process.kill = Mock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process
            
            with pytest.raises(CommandTimeoutError):
                await tool._run_command(['open', 'https://example.com'])


class TestMCPFunctions:
    """MCP 工具函数测试"""
    
    @pytest.mark.asyncio
    async def test_agent_browser_open(self):
        """测试 agent_browser_open MCP 工具"""
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_open = AsyncMock(return_value={
                'success': True,
                'url': 'https://example.com'
            })
            mock_tool_class.return_value = mock_tool
            
            result = await agent_browser_open('https://example.com')
            
            assert result['success'] is True
            mock_tool.browser_open.assert_called_once_with('https://example.com', None)
    
    @pytest.mark.asyncio
    async def test_agent_browser_snapshot(self):
        """测试 agent_browser_snapshot MCP 工具"""
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_snapshot = AsyncMock(return_value={
                'success': True,
                'snapshot': 'test',
                'refs': {}
            })
            mock_tool_class.return_value = mock_tool
            
            result = await agent_browser_snapshot(interactive_only=True)
            
            assert result['success'] is True
            mock_tool.browser_snapshot.assert_called_once_with(True, True, None)
    
    @pytest.mark.asyncio
    async def test_agent_browser_click(self):
        """测试 agent_browser_click MCP 工具"""
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_click = AsyncMock(return_value={
                'success': True,
                'selector': '@e1'
            })
            mock_tool_class.return_value = mock_tool
            
            result = await agent_browser_click('@e1', new_tab=True)
            
            assert result['success'] is True
            mock_tool.browser_click.assert_called_once_with('@e1', True)
    
    @pytest.mark.asyncio
    async def test_agent_browser_fill(self):
        """测试 agent_browser_fill MCP 工具"""
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_fill = AsyncMock(return_value={
                'success': True,
                'selector': '@e2'
            })
            mock_tool_class.return_value = mock_tool
            
            result = await agent_browser_fill('@e2', 'test@example.com')
            
            assert result['success'] is True
            mock_tool.browser_fill.assert_called_once_with('@e2', 'test@example.com')


class TestWorkflow:
    """工作流测试"""
    
    @pytest.mark.asyncio
    async def test_workflow_success(self):
        """测试工作流成功执行"""
        from src.integrations.mcp.agent_browser_tool import agent_browser_workflow
        
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_open = AsyncMock(return_value={'success': True})
            mock_tool.browser_click = AsyncMock(return_value={'success': True})
            mock_tool.browser_fill = AsyncMock(return_value={'success': True})
            mock_tool.browser_wait = AsyncMock(return_value={'success': True})
            mock_tool.browser_screenshot = AsyncMock(return_value={
                'success': True,
                'path': '/tmp/screenshot.png'
            })
            mock_tool_class.return_value = mock_tool
            
            steps = [
                {'action': 'fill', 'selector': '@e1', 'value': 'test'},
                {'action': 'click', 'selector': '@e2'},
                {'action': 'screenshot'}
            ]
            
            result = await agent_browser_workflow(
                url='https://example.com',
                steps=steps
            )
            
            assert result['success'] is True
            assert result['total_steps'] == 3
    
    @pytest.mark.asyncio
    async def test_workflow_failure(self):
        """测试工作流失败"""
        from src.integrations.mcp.agent_browser_tool import agent_browser_workflow
        
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_open = AsyncMock(return_value={'success': True})
            mock_tool.browser_click = AsyncMock(return_value={
                'success': False,
                'error': 'Element not found'
            })
            mock_tool_class.return_value = mock_tool
            
            steps = [
                {'action': 'click', 'selector': '@invalid'}
            ]
            
            result = await agent_browser_workflow(
                url='https://example.com',
                steps=steps
            )
            
            assert result['success'] is False
            assert 'error' in result


class TestDataExtraction:
    """数据提取测试"""
    
    @pytest.mark.asyncio
    async def test_extract_data_success(self):
        """测试数据提取成功"""
        from src.integrations.mcp.agent_browser_tool import agent_browser_extract_data
        
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_open = AsyncMock(return_value={'success': True})
            mock_tool.browser_get_text = AsyncMock(return_value={
                'success': True,
                'text': 'Example Title'
            })
            mock_tool_class.return_value = mock_tool
            
            result = await agent_browser_extract_data(
                url='https://example.com/article',
                selectors={'title': '@e1'}
            )
            
            assert result['success'] is True
            assert result['data']['title'] == 'Example Title'
    
    @pytest.mark.asyncio
    async def test_extract_data_partial_failure(self):
        """测试部分提取失败"""
        from src.integrations.mcp.agent_browser_tool import agent_browser_extract_data
        
        with patch('src.mcp.agent_browser_tool.AgentBrowserTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.browser_open = AsyncMock(return_value={'success': True})
            
            async def mock_get_text(selector):
                if selector == '@e1':
                    return {'success': True, 'text': 'Title'}
                else:
                    return {'success': False, 'error': 'Not found'}
            
            mock_tool.browser_get_text = AsyncMock(side_effect=mock_get_text)
            mock_tool_class.return_value = mock_tool
            
            result = await agent_browser_extract_data(
                url='https://example.com/article',
                selectors={'title': '@e1', 'missing': '@e2'}
            )
            
            assert result['success'] is True
            assert result['data']['title'] == 'Title'
            assert result['data']['missing'] is None
            assert len(result['errors']) == 1


# 导入 json 用于测试
import json


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
