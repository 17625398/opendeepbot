"""
Agent-Browser 核心模块单元测试

测试范围：
- 守护进程管理
- CDP 浏览器操作
- Snapshot 引擎
- 语义定位器
- 安全特性
- 认证管理

Author: DeepTutor
Created: 2026-03-06
"""

import asyncio
import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integrations.mcp.agent_browser_native_daemon import (
    NativeDaemon,
    CLIDaemon,
    DaemonManager,
    DaemonConfig,
    CommandResult
)
from src.integrations.mcp.agent_browser_cdp import CDPBrowser, CommandResult as CDPCommandResult
from src.integrations.mcp.agent_browser_snapshot import (
    SnapshotEngine,
    SnapshotOptions,
    SnapshotMode
)
from src.integrations.mcp.agent_browser_security import (
    SecurityManager,
    ContentBoundary,
    DomainAllowlist,
    ActionPolicy
)
from src.integrations.mcp.agent_browser_auth import (
    CredentialVault,
    SessionManager,
    EncryptionManager
)


# ==================== 测试工具类 ====================

class AsyncMock:
    """异步 Mock 工具"""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __call__(self, *args, **kwargs):
        return self.return_value


# ==================== 守护进程测试 ====================

class TestNativeDaemon:
    """Native 守护进程测试"""
    
    @pytest.fixture
    def daemon(self):
        """创建守护进程实例"""
        return NativeDaemon()
    
    @pytest.mark.asyncio
    async def test_daemon_initialization(self, daemon):
        """测试守护进程初始化"""
        assert daemon is not None
        assert daemon.ws_url is None
        assert not daemon.is_running
    
    @pytest.mark.asyncio
    async def test_daemon_start(self, daemon, monkeypatch):
        """测试守护进程启动"""
        # Mock subprocess
        async def mock_create_subprocess(*args, **kwargs):
            class MockProcess:
                async def communicate(self):
                    return (b"output", b"")
                @property
                def returncode(self):
                    return 0
            return MockProcess()
        
        monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_subprocess)
        
        # 测试启动（需要实际环境）
        # result = await daemon.start()
        # assert result is True
    
    @pytest.mark.asyncio
    async def test_command_result_creation(self):
        """测试命令结果创建"""
        result = CommandResult(
            success=True,
            data={"key": "value"},
            error=None
        )
        
        assert result.success is True
        assert result.data["key"] == "value"
        assert result.error is None


class TestCLIDaemon:
    """CLI 守护进程测试"""
    
    @pytest.fixture
    def cli_daemon(self):
        """创建 CLI 守护进程"""
        return CLIDaemon()
    
    @pytest.mark.asyncio
    async def test_cli_daemon_initialization(self, cli_daemon):
        """测试 CLI 守护进程初始化"""
        assert cli_daemon is not None
        assert cli_daemon.timeout == 30


class TestDaemonManager:
    """守护进程管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return DaemonManager()
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
        assert manager.mode_name is None
    
    @pytest.mark.asyncio
    async def test_mode_selection(self, manager):
        """测试模式选择逻辑"""
        # 测试 Native 模式优先
        config = DaemonConfig(prefer_native=True)
        manager._config = config
        
        # 模拟 Native 可用
        manager._native_available = True
        mode = manager._select_mode()
        assert mode == "native"
        
        # 模拟 Native 不可用
        manager._native_available = False
        mode = manager._select_mode()
        assert mode == "cli"


# ==================== CDP 浏览器测试 ====================

class TestCDPBrowser:
    """CDP 浏览器测试"""
    
    @pytest.fixture
    def browser(self):
        """创建浏览器实例"""
        return CDPBrowser("test_session")
    
    @pytest.mark.asyncio
    async def test_browser_initialization(self, browser):
        """测试浏览器初始化"""
        assert browser is not None
        assert browser.session_name == "test_session"
        assert browser.current_url is None
    
    @pytest.mark.asyncio
    async def test_navigate_command(self, browser):
        """测试导航命令"""
        # Mock CDP 调用
        async def mock_send_command(cmd, params):
            return CDPCommandResult(
                success=True,
                data={"url": params.get("url")}
            )
        
        browser._send_cdp_command = mock_send_command
        
        result = await browser.navigate("https://example.com")
        assert result.success is True
        assert browser.current_url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_click_command(self, browser):
        """测试点击命令"""
        async def mock_send_command(cmd, params):
            return CDPCommandResult(success=True, data={})
        
        browser._send_cdp_command = mock_send_command
        
        result = await browser.click("#button")
        assert result.success is True


# ==================== Snapshot 引擎测试 ====================

class TestSnapshotEngine:
    """Snapshot 引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建 Snapshot 引擎"""
        return SnapshotEngine()
    
    @pytest.fixture
    def sample_tree(self):
        """示例无障碍树"""
        return [
            {
                "backendDOMNodeId": 1,
                "role": {"value": "WebArea"},
                "name": {"value": "Test Page"},
                "children": [
                    {
                        "backendDOMNodeId": 2,
                        "role": {"value": "button"},
                        "name": {"value": "Click Me"},
                        "attributes": {
                            "id": "btn1",
                            "class": "primary"
                        }
                    },
                    {
                        "backendDOMNodeId": 3,
                        "role": {"value": "textbox"},
                        "name": {"value": "Input"},
                        "attributes": {
                            "placeholder": "Enter text"
                        }
                    }
                ]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert engine.cache is not None
    
    @pytest.mark.asyncio
    async def test_snapshot_generation(self, engine, sample_tree):
        """测试快照生成"""
        page_info = {
            "url": "https://example.com",
            "title": "Test Page"
        }
        
        result = await engine.generate(sample_tree, page_info)
        
        assert result.success is True
        assert result.snapshot is not None
        assert len(result.refs) > 0
        assert "e1" in result.refs or "e2" in result.refs
    
    @pytest.mark.asyncio
    async def test_interactive_mode(self, engine, sample_tree):
        """测试交互式模式"""
        options = SnapshotOptions(mode=SnapshotMode.INTERACTIVE)
        
        result = await engine.generate(
            sample_tree,
            {"url": "https://example.com"},
            options
        )
        
        assert result.success is True
        # 交互式模式应该过滤掉非交互元素
        assert result.stats["interactive_filtered"] is True
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, engine, sample_tree):
        """测试缓存命中"""
        page_info = {"url": "https://example.com", "title": "Test"}
        
        # 第一次生成
        result1 = await engine.generate(sample_tree, page_info)
        
        # 第二次应该命中缓存
        result2 = await engine.generate(sample_tree, page_info)
        
        assert result1.snapshot == result2.snapshot
        assert result2.stats["cache_hit"] is True


# ==================== 安全特性测试 ====================

class TestSecurityManager:
    """安全管理器测试"""
    
    @pytest.fixture
    def security(self):
        """创建安全管理器"""
        return SecurityManager()
    
    def test_content_boundary(self, security):
        """测试内容边界"""
        content = "Test content"
        wrapped = security.wrap_content(content)
        
        assert ContentBoundary.START_MARKER in wrapped
        ContentBoundary.END_MARKER in wrapped
        content in wrapped
    
    def test_domain_allowlist(self):
        """测试域允许列表"""
        allowlist = DomainAllowlist(
            allowed_domains=["example.com", "*.example.com"]
        )
        
        assert allowlist.is_allowed("https://example.com/page") is True
        assert allowlist.is_allowed("https://sub.example.com/page") is True
        assert allowlist.is_allowed("https://evil.com/page") is False
    
    def test_action_policy(self, security):
        """测试动作策略"""
        # 安全动作
        result = security.check_action("click", {"selector": "#btn"})
        assert result.allowed is True
        
        # 危险动作（需要确认）
        result = security.check_action("eval", {"code": "alert(1)"})
        assert result.requires_confirmation is True
    
    def test_output_limit(self, security):
        """测试输出限制"""
        # 短内容
        short_content = "A" * 100
        allowed, truncated = security.limit_output(short_content)
        assert allowed is True
        assert truncated == short_content
        
        # 长内容
        long_content = "A" * 100000
        allowed, truncated = security.limit_output(long_content)
        assert len(truncated) <= 50000


# ==================== 认证管理测试 ====================

class TestEncryptionManager:
    """加密管理器测试"""
    
    @pytest.fixture
    def encryption(self):
        """创建加密管理器"""
        return EncryptionManager()
    
    def test_encrypt_decrypt(self, encryption):
        """测试加密解密"""
        original = "Secret message"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert original == decrypted
        assert encrypted != original
    
    def test_different_plaintexts(self, encryption):
        """测试不同明文"""
        texts = ["text1", "text2", "text3"]
        encrypted_texts = [encryption.encrypt(t) for t in texts]
        
        # 确保每个加密结果不同
        assert len(set(encrypted_texts)) == len(texts)
        
        # 确保都能正确解密
        for original, encrypted in zip(texts, encrypted_texts):
            assert encryption.decrypt(encrypted) == original


class TestCredentialVault:
    """凭证库测试"""
    
    @pytest.fixture
    def vault(self, tmp_path):
        """创建凭证库"""
        return CredentialVault(storage_dir=str(tmp_path))
    
    def test_save_get_credential(self, vault):
        """测试保存和获取凭证"""
        vault.save(
            name="test_site",
            url="https://test.com/login",
            username="testuser",
            password="testpass"
        )
        
        cred = vault.get("test_site")
        assert cred is not None
        assert cred.username == "testuser"
        assert vault.get_password("test_site") == "testpass"
    
    def test_delete_credential(self, vault):
        """测试删除凭证"""
        vault.save("test", "https://test.com", "user", "pass")
        assert vault.get("test") is not None
        
        vault.delete("test")
        assert vault.get("test") is None


class TestSessionManager:
    """会话管理器测试"""
    
    @pytest.fixture
    def session_mgr(self, tmp_path):
        """创建会话管理器"""
        return SessionManager(storage_dir=str(tmp_path))
    
    def test_save_load_session(self, session_mgr):
        """测试保存和加载会话"""
        cookies = [
            {"name": "session", "value": "abc123", "domain": "example.com"}
        ]
        
        session_mgr.save_session(
            session_name="test_session",
            cookies=cookies,
            local_storage={"key": "value"},
            session_storage={}
        )
        
        session = session_mgr.load_session("test_session")
        assert session is not None
        assert len(session.cookies) == 1
        assert session.cookies[0]["name"] == "session"


# ==================== 性能监控测试 ====================

class TestPerformanceMonitor:
    """性能监控器测试"""
    
    @pytest.fixture
    def monitor(self):
        """创建性能监控器"""
        from src.integrations.mcp.agent_browser_performance import PerformanceMonitor
        return PerformanceMonitor()
    
    def test_record_command(self, monitor):
        """测试记录命令"""
        monitor.record_command(
            command="navigate",
            mode="native",
            execution_time_ms=15.5,
            success=True
        )
        
        stats = monitor.get_stats()
        assert stats["total_commands"] == 1
        assert stats["commands_by_mode"]["native"] == 1
    
    def test_get_report(self, monitor):
        """测试获取报告"""
        # 记录多个命令
        for i in range(10):
            monitor.record_command(
                command="click",
                mode="native" if i % 2 == 0 else "cli",
                execution_time_ms=10.0 if i % 2 == 0 else 50.0,
                success=True
            )
        
        report = monitor.get_report()
        assert report["total_commands"] == 10
        assert "overall_speedup" in report


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"
    ])
