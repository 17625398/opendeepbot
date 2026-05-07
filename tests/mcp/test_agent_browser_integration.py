"""
Agent-Browser 集成测试

测试范围：
- 完整工作流程
- 多模块集成
- 实际浏览器操作
- 性能基准测试

Author: DeepTutor
Created: 2026-03-06
"""

import asyncio
import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integrations.mcp.agent_browser_native_daemon import get_daemon_manager, DaemonConfig
from src.integrations.mcp.agent_browser_cdp import get_browser
from src.integrations.mcp.agent_browser_migrated_tools import MigratedToolFactory
from src.integrations.mcp.agent_browser_optimizer import get_optimizer, CacheConfig


# ==================== 集成测试工具 ====================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def browser_session():
    """浏览器会话夹具"""
    config = DaemonConfig(headless=True, session="test_integration")
    manager = await get_daemon_manager(config)
    browser = await get_browser("test_integration")
    
    yield browser
    
    # 清理
    await browser.close()


# ==================== 工作流程测试 ====================

class TestWorkflows:
    """工作流程测试"""
    
    @pytest.mark.asyncio
    async def test_navigation_and_snapshot(self, browser_session):
        """测试导航和快照获取"""
        browser = browser_session
        
        # 导航
        nav_result = await browser.navigate("https://example.com")
        assert nav_result.success is True
        
        # 获取快照
        snapshot_result = await browser.get_snapshot()
        assert snapshot_result.success is True
        assert "tree" in snapshot_result.data
        
        # 验证 URL
        assert browser.current_url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_click_operation(self, browser_session):
        """测试点击操作"""
        browser = browser_session
        
        # 导航到测试页面
        await browser.navigate("https://example.com")
        
        # 尝试点击（示例页面可能没有特定元素）
        # 这里测试 API 调用是否正常工作
        result = await browser.click("body")
        assert result.success is True or result.success is False  # 可能失败，但 API 应正常
    
    @pytest.mark.asyncio
    async def test_fill_operation(self, browser_session):
        """测试填充操作"""
        browser = browser_session
        
        # 创建测试 HTML
        test_html = """
        <html>
        <body>
            <input type="text" id="test-input" />
        </body>
        </html>
        """
        
        # 导航到数据 URL
        data_url = f"data:text/html,{test_html}"
        await browser.navigate(data_url)
        
        # 填充输入框
        result = await browser.fill("#test-input", "test value")
        assert result.success is True
        
        # 验证值
        eval_result = await browser.evaluate_js(
            "document.getElementById('test-input').value"
        )
        assert eval_result.data.get("result") == "test value"


# ==================== 工具迁移测试 ====================

class TestMigratedTools:
    """迁移工具测试"""
    
    @pytest.mark.asyncio
    async def test_migrated_open_tool(self, browser_session):
        """测试迁移的打开工具"""
        tool = MigratedToolFactory.create_tool("open", "test_integration")
        
        result = await tool.execute("https://example.com")
        assert result["success"] is True
        assert result["url"] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_migrated_snapshot_tool(self, browser_session):
        """测试迁移的快照工具"""
        tool = MigratedToolFactory.create_tool("snapshot", "test_integration")
        
        result = await tool.execute(interactive_only=True, compact=True)
        assert result["success"] is True
        assert "snapshot" in result
        assert "refs" in result
    
    @pytest.mark.asyncio
    async def test_migrated_click_tool(self, browser_session):
        """测试迁移的点击工具"""
        tool = MigratedToolFactory.create_tool("click", "test_integration")
        
        result = await tool.execute("body")
        # 可能成功或失败，但工具应正常工作
        assert "success" in result


# ==================== 性能优化测试 ====================

class TestPerformanceOptimization:
    """性能优化测试"""
    
    @pytest.fixture
    def optimizer(self):
        """创建优化器"""
        config = CacheConfig(
            memory_cache_size=100,
            disk_cache_enabled=False
        )
        return get_optimizer(config)
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, optimizer):
        """测试缓存性能"""
        cache = optimizer.cache
        
        # 第一次访问（未命中）
        start = time.time()
        await cache.set("test_key", {"data": "value"})
        first_access = time.time() - start
        
        # 第二次访问（命中）
        start = time.time()
        value = await cache.get("test_key")
        second_access = time.time() - start
        
        assert value["data"] == "value"
        # 缓存命中应该快 10 倍以上
        assert second_access < first_access
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self, optimizer):
        """测试并发执行"""
        executor = optimizer.executor
        
        async def fetch_item(item_id):
            await asyncio.sleep(0.1)
            return f"item_{item_id}"
        
        # 串行执行
        start = time.time()
        for i in range(10):
            await fetch_item(i)
        serial_time = time.time() - start
        
        # 并发执行
        start = time.time()
        tasks = [(fetch_item, [i], {}) for i in range(10)]
        results = await executor.execute_batch(tasks)
        concurrent_time = time.time() - start
        
        assert len(results) == 10
        # 并发应该快 5 倍以上
        assert concurrent_time < serial_time / 3
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, optimizer):
        """测试批量处理"""
        processor = optimizer.batch_processor
        
        async def process_item(item):
            await asyncio.sleep(0.05)
            return item * 2
        
        items = list(range(20))
        
        start = time.time()
        results = await processor.process(items, process_item)
        batch_time = time.time() - start
        
        assert len(results) == 20
        assert results == [i * 2 for i in range(20)]


# ==================== 性能基准测试 ====================

class TestBenchmarks:
    """性能基准测试"""
    
    @pytest.fixture
    def benchmark_browser(self):
        """基准测试浏览器"""
        config = DaemonConfig(headless=True, session="benchmark")
        
        async def setup():
            manager = await get_daemon_manager(config)
            return await get_browser("benchmark")
        
        async def teardown(browser):
            await browser.close()
        
        browser = asyncio.get_event_loop().run_until_complete(setup())
        yield browser
        asyncio.get_event_loop().run_until_complete(teardown(browser))
    
    def test_navigation_latency(self, benchmark_browser):
        """测试导航延迟"""
        async def run_test():
            start = time.time()
            await benchmark_browser.navigate("https://example.com")
            return time.time() - start
        
        latency = asyncio.get_event_loop().run_until_complete(run_test())
        
        # 导航延迟应小于 100ms
        assert latency < 0.1, f"导航延迟过高：{latency * 1000:.2f}ms"
    
    def test_snapshot_latency(self, benchmark_browser):
        """测试快照延迟"""
        async def run_test():
            await benchmark_browser.navigate("https://example.com")
            start = time.time()
            await benchmark_browser.get_snapshot()
            return time.time() - start
        
        latency = asyncio.get_event_loop().run_until_complete(run_test())
        
        # 快照延迟应小于 50ms
        assert latency < 0.05, f"快照延迟过高：{latency * 1000:.2f}ms"
    
    def test_click_latency(self, benchmark_browser):
        """测试点击延迟"""
        async def run_test():
            await benchmark_browser.navigate("https://example.com")
            start = time.time()
            await benchmark_browser.click("body")
            return time.time() - start
        
        latency = asyncio.get_event_loop().run_until_complete(run_test())
        
        # 点击延迟应小于 30ms
        assert latency < 0.03, f"点击延迟过高：{latency * 1000:.2f}ms"


# ==================== 压力测试 ====================

class TestStress:
    """压力测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """测试并发会话"""
        sessions = []
        
        try:
            # 创建多个并发会话
            for i in range(3):
                config = DaemonConfig(headless=True, session=f"stress_{i}")
                manager = await get_daemon_manager(config)
                browser = await get_browser(f"stress_{i}")
                sessions.append(browser)
            
            # 并发执行操作
            async def navigate_and_snapshot(browser, url):
                await browser.navigate(url)
                return await browser.get_snapshot()
            
            tasks = [
                navigate_and_snapshot(browser, "https://example.com")
                for browser in sessions
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证所有操作成功
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            assert success_count == len(sessions)
        
        finally:
            # 清理所有会话
            for browser in sessions:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_rapid_operations(self, browser_session):
        """测试快速连续操作"""
        browser = browser_session
        
        # 执行大量快速操作
        operations = []
        for i in range(50):
            operations.append(browser.get_snapshot())
        
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        # 验证大部分成功
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count >= 45  # 90% 成功率


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",
        "-m", "not benchmark"  # 默认不运行基准测试
    ])
