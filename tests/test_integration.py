#!/usr/bin/env python3
"""
Phase 1 集成测试套件

测试整个 SDK 的完整功能，包括：
- Agent 创建和管理
- 持久化
- 安全认证
- CLI 工具
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# ==================== SDK 集成测试 ====================

class TestSDKIntegration:
    """SDK 集成测试"""
    
    @pytest_asyncio.fixture
    async def setup_environment(self, tmp_path):
        """设置测试环境"""
        # 创建临时目录
        test_dir = tmp_path / "deeptutor_test"
        test_dir.mkdir()
        
        # 初始化组件
        from src.sdk.persistence.agent_storage import AgentStorageManager
        from src.sdk.security.auth import JWTManager, PasswordManager, User, SecurityConfig
        
        storage_mgr = AgentStorageManager(
            backend="file",
            base_dir=str(test_dir / "agents"),
            auto_backup=True
        )
        
        jwt_mgr = JWTManager(SecurityConfig(
            secret_key="test-secret-key-for-integration-test"
        ))
        
        pwd_mgr = PasswordManager()
        
        try:
            yield {
                "test_dir": test_dir,
                "storage_mgr": storage_mgr,
                "jwt_mgr": jwt_mgr,
                "pwd_mgr": pwd_mgr,
            }
        finally:
            # 清理
            await storage_mgr.close()
            shutil.rmtree(str(test_dir), ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle(self, setup_environment):
        """测试 Agent 完整生命周期"""
        storage_mgr = setup_environment["storage_mgr"]
        
        # 1. 创建 Agent 数据
        agent_data = {
            "agent_id": "test-agent-001",
            "name": "Test Agent",
            "agent_type": "base",
            "status": "idle",
            "config": {
                "name": "Test Agent",
                "agent_type": "base",
                "skills": ["test"],
            },
            "state": {"test": True},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # 2. 保存 Agent
        success = await storage_mgr._storage.save("agent_test-agent-001", agent_data)
        assert success is True
        
        # 3. 加载 Agent
        loaded = await storage_mgr._storage.load("agent_test-agent-001")
        assert loaded is not None
        assert loaded["name"] == "Test Agent"
        
        # 4. 列出 Agent
        agents = await storage_mgr.list_agents()
        assert "test-agent-001" in agents
        
        # 5. 删除 Agent
        success = await storage_mgr._storage.delete("agent_test-agent-001")
        assert success is True
        
        # 6. 验证删除
        loaded = await storage_mgr._storage.load("agent_test-agent-001")
        assert loaded is None
    
    @pytest.mark.asyncio
    async def test_authentication_flow(self, setup_environment):
        """测试认证流程"""
        jwt_mgr = setup_environment["jwt_mgr"]
        pwd_mgr = setup_environment["pwd_mgr"]
        
        # 1. 创建用户
        from src.sdk.security.auth import User
        
        user = User(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_mgr.hash_password("TestPassword123"),
            roles=["developer"]
        )
        
        # 2. 创建 Token
        from src.sdk.security.auth import create_user_token
        
        token_response = create_user_token(user, jwt_mgr)
        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        
        # 3. 验证 Token
        token_data = jwt_mgr.verify_token(token_response.access_token, "access")
        assert token_data is not None
        assert token_data.user_id == "user-123"
        assert token_data.username == "testuser"
        
        # 4. 刷新 Token
        new_access_token = jwt_mgr.refresh_access_token(token_response.refresh_token)
        assert new_access_token is not None
        
        # 5. 验证新 Token
        new_token_data = jwt_mgr.verify_token(new_access_token, "access")
        assert new_token_data is not None
        assert new_token_data.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_permission_system(self, setup_environment):
        """测试权限系统"""
        from src.sdk.security.auth import (
            User, Role, Permission, PermissionChecker
        )
        
        # 创建不同角色的用户
        admin_user = User(
            user_id="admin-123",
            username="admin",
            email="admin@example.com",
            hashed_password="xxx",
            roles=["admin"]
        )
        
        viewer_user = User(
            user_id="viewer-123",
            username="viewer",
            email="viewer@example.com",
            hashed_password="xxx",
            roles=["viewer"]
        )
        
        # 测试管理员权限
        assert PermissionChecker.has_permission(admin_user, Permission.AGENT_CREATE)
        assert PermissionChecker.has_permission(admin_user, Permission.AGENT_DELETE)
        assert PermissionChecker.has_role(admin_user, Role.ADMIN)
        
        # 测试只读用户权限
        assert PermissionChecker.has_permission(viewer_user, Permission.AGENT_READ)
        assert not PermissionChecker.has_permission(viewer_user, Permission.AGENT_CREATE)
        assert PermissionChecker.has_role(viewer_user, Role.VIEWER)
    
    @pytest.mark.asyncio
    async def test_backup_and_restore(self, setup_environment):
        """测试备份和恢复"""
        storage_mgr = setup_environment["storage_mgr"]
        
        # 1. 创建测试数据
        await storage_mgr._storage.save("agent_agent1", {"name": "Agent 1"})
        await storage_mgr._storage.save("agent_agent2", {"name": "Agent 2"})
        
        # 2. 备份
        backup_dir = setup_environment["test_dir"] / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = await storage_mgr.backup(str(backup_dir))
        assert backup_path is not None
        # 给文件系统一点时间完成写入
        await asyncio.sleep(0.1)
        assert Path(backup_path).exists(), f"Backup file not found: {backup_path}"
        
        # 3. 清空
        await storage_mgr.clear_all()
        agents = await storage_mgr.list_agents()
        assert len(agents) == 0
        
        # 4. 恢复
        restored_count = await storage_mgr.restore(backup_path)
        assert restored_count == 2
        
        # 5. 验证恢复
        agents = await storage_mgr.list_agents()
        assert len(agents) == 2


# ==================== CLI 集成测试 ====================

class TestCLIIntegration:
    """CLI 集成测试"""
    
    @pytest.fixture
    def setup_cli_environment(self, tmp_path):
        """设置 CLI 测试环境"""
        test_dir = tmp_path / "cli_test"
        test_dir.mkdir()
        
        # 设置环境变量
        import os
        os.environ["DEEPTUTOR_DATA_DIR"] = str(test_dir)
        
        yield {"test_dir": test_dir}
        
        # 清理
        shutil.rmtree(str(test_dir), ignore_errors=True)
    
    def test_cli_help(self, setup_cli_environment):
        """测试 CLI 帮助命令"""
        import subprocess
        
        result = subprocess.run(
            ["python", "scripts/deeptutor.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "DeepTutor CLI" in result.stdout
        assert "create" in result.stdout
        assert "list" in result.stdout
    
    def test_cli_stats(self, setup_cli_environment):
        """测试 CLI stats 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python", "scripts/deeptutor.py", "stats"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "注册中心统计" in result.stdout


# ==================== 端到端测试 ====================

class TestEndToEnd:
    """端到端测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """测试完整工作流"""
        from src.sdk.persistence.agent_storage import AgentStorageManager
        from src.sdk.security.auth import (
            JWTManager, PasswordManager, User, SecurityConfig,
            create_user_token, PermissionChecker, Permission
        )
        
        # 1. 初始化系统
        test_dir = tmp_path / "e2e_test"
        test_dir.mkdir()
        
        storage_mgr = AgentStorageManager(
            backend="file",
            base_dir=str(test_dir / "agents"),
            auto_backup=True
        )
        
        jwt_mgr = JWTManager()
        pwd_mgr = PasswordManager()
        
        # 2. 创建管理员用户
        admin = User(
            user_id="admin-001",
            username="admin",
            email="admin@example.com",
            hashed_password=pwd_mgr.hash_password("Admin123"),
            roles=["admin"]
        )
        
        # 3. 获取 Token
        token_response = create_user_token(admin, jwt_mgr)
        
        # 4. 验证权限
        assert PermissionChecker.has_permission(admin, Permission.AGENT_CREATE)
        
        # 5. 创建 Agent
        agent_data = {
            "agent_id": "e2e-agent-001",
            "name": "E2E Test Agent",
            "agent_type": "base",
            "status": "idle",
            "config": {
                "name": "E2E Test Agent",
                "agent_type": "base",
            },
        }
        
        await storage_mgr._storage.save("agent_e2e-agent-001", agent_data)
        
        # 6. 验证 Agent 已保存
        agents = await storage_mgr.list_agents()
        assert "e2e-agent-001" in agents
        
        # 7. 备份
        backup_dir = test_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = await storage_mgr.backup(str(backup_dir))
        assert backup_path is not None
        await asyncio.sleep(0.1)  # 给文件系统时间完成写入
        assert Path(backup_path).exists(), f"Backup file not found: {backup_path}"
        
        # 8. 清理
        await storage_mgr.close()
        shutil.rmtree(str(test_dir), ignore_errors=True)


# ==================== 性能测试 ====================

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_storage_performance(self, tmp_path):
        """测试存储性能"""
        from src.sdk.persistence.agent_storage import AgentStorageManager
        import time
        
        storage_mgr = AgentStorageManager(
            backend="file",
            base_dir=str(tmp_path / "perf_test"),
            auto_backup=False
        )
        
        # 批量创建 Agent
        start_time = time.time()
        for i in range(100):
            agent_data = {
                "agent_id": f"perf-agent-{i:03d}",
                "name": f"Performance Agent {i}",
                "agent_type": "base",
            }
            await storage_mgr._storage.save(f"agent_perf-agent-{i:03d}", agent_data)
        
        save_time = time.time() - start_time
        
        # 批量加载 Agent
        start_time = time.time()
        for i in range(100):
            await storage_mgr._storage.load(f"agent_perf-agent-{i:03d}")
        
        load_time = time.time() - start_time
        
        # 验证性能
        assert save_time < 5.0, f"保存 100 个 Agent 耗时过长：{save_time}秒"
        assert load_time < 5.0, f"加载 100 个 Agent 耗时过长：{load_time}秒"
        
        # 输出性能指标
        print(f"\n性能测试结果:")
        print(f"  保存 100 个 Agent: {save_time:.2f}秒 ({100/save_time:.1f} ops/s)")
        print(f"  加载 100 个 Agent: {load_time:.2f}秒 ({100/load_time:.1f} ops/s)")
        
        await storage_mgr.close()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
