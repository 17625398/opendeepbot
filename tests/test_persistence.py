#!/usr/bin/env python3
"""
持久化层单元测试

测试 FileStorage、RedisStorage 和 AgentStorageManager
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.sdk.persistence.file_storage import FileStorage
from src.sdk.persistence.redis_storage import RedisStorage
from src.sdk.persistence.agent_storage import AgentStorageManager
from src.sdk.agent.base import AgentConfig, AgentStatus


# ============================================================================
# FileStorage 测试
# ============================================================================

class TestFileStorage:
    """FileStorage 测试类"""
    
    @pytest.fixture
    async def storage(self, tmp_path):
        """创建临时存储目录"""
        storage = FileStorage(base_dir=str(tmp_path))
        yield storage
        # 清理
        await storage.clear()
    
    @pytest.mark.asyncio
    async def test_save_and_load(self, storage):
        """测试保存和加载"""
        test_data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        
        # 保存
        success = await storage.save("test_key", test_data)
        assert success is True
        
        # 加载
        loaded = await storage.load("test_key")
        assert loaded == test_data
    
    @pytest.mark.asyncio
    async def test_load_nonexistent(self, storage):
        """测试加载不存在的键"""
        result = await storage.load("nonexistent")
        assert result is None
        
        # 测试默认值
        result = await storage.load("nonexistent", default={"default": True})
        assert result == {"default": True}
    
    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """测试删除"""
        # 先保存
        await storage.save("to_delete", {"data": "value"})
        
        # 删除
        success = await storage.delete("to_delete")
        assert success is True
        
        # 验证已删除
        exists = await storage.exists("to_delete")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """测试存在性检查"""
        # 不存在的键
        assert await storage.exists("nonexistent") is False
        
        # 保存后存在
        await storage.save("existent", {})
        assert await storage.exists("existent") is True
    
    @pytest.mark.asyncio
    async def test_list_keys(self, storage):
        """测试列出键"""
        # 保存多个键
        await storage.save("key1", {})
        await storage.save("key2", {})
        await storage.save("key3", {})
        
        # 列出所有
        keys = await storage.list_keys("*")
        assert len(keys) == 3
        assert set(keys) == {"key1", "key2", "key3"}
        
        # 模式匹配
        keys = await storage.list_keys("key*")
        assert len(keys) == 3
        
        keys = await storage.list_keys("key1")
        assert keys == ["key1"]
    
    @pytest.mark.asyncio
    async def test_metadata(self, storage):
        """测试元数据"""
        await storage.save("test", {"data": "value"})
        
        metadata = await storage.get_metadata("test")
        assert metadata is not None
        assert "key" in metadata
        assert "saved_at" in metadata
        assert "version" in metadata
    
    @pytest.mark.asyncio
    async def test_stats(self, storage):
        """测试统计信息"""
        await storage.save("test1", {})
        await storage.save("test2", {})
        await storage.load("test1")
        
        stats = await storage.get_stats()
        assert stats["total_saves"] == 2
        assert stats["total_loads"] == 1
        assert "file_count" in stats
        assert "total_size_bytes" in stats
    
    @pytest.mark.asyncio
    async def test_backup(self, storage, tmp_path):
        """测试备份"""
        await storage.save("test", {"data": "value"})
        
        backup_dir = str(tmp_path / "backups")
        backup_path = await storage.backup(backup_dir)
        
        assert backup_path is not None
        assert Path(backup_path).exists()
    
    @pytest.mark.asyncio
    async def test_clear(self, storage):
        """测试清空"""
        # 保存多个键
        await storage.save("key1", {})
        await storage.save("key2", {})
        await storage.save("key3", {})
        
        # 清空
        count = await storage.clear()
        assert count == 3
        
        # 验证已清空
        keys = await storage.list_keys("*")
        assert len(keys) == 0


# ============================================================================
# RedisStorage 测试（需要 Redis 服务）
# ============================================================================

class TestRedisStorage:
    """RedisStorage 测试类"""
    
    @pytest.fixture
    async def storage(self):
        """创建 Redis 存储实例"""
        storage = RedisStorage(
            redis_url="redis://localhost:6379",
            db=15  # 使用测试数据库
        )
        
        try:
            await storage.connect()
            yield storage
        finally:
            # 清理测试数据库
            await storage.clear()
            await storage.disconnect()
    
    @pytest.mark.asyncio
    async def test_save_and_load(self, storage):
        """测试保存和加载"""
        test_data = {"name": "test", "value": 123}
        
        # 保存
        success = await storage.save("test_key", test_data)
        assert success is True
        
        # 加载
        loaded = await storage.load("test_key")
        assert loaded == test_data
    
    @pytest.mark.asyncio
    async def test_expire(self, storage):
        """测试过期时间"""
        await storage.save("expiring_key", {"data": "value"}, expire_seconds=2)
        
        # 立即检查存在
        assert await storage.exists("expiring_key") is True
        
        # 等待过期
        await asyncio.sleep(3)
        
        # 应该已过期
        assert await storage.exists("expiring_key") is False
    
    @pytest.mark.asyncio
    async def test_ttl(self, storage):
        """测试 TTL"""
        await storage.save("ttl_key", {}, expire_seconds=10)
        
        ttl = await storage.ttl("ttl_key")
        assert 0 < ttl <= 10
    
    @pytest.mark.asyncio
    async def test_list_keys(self, storage):
        """测试列出键"""
        await storage.save("key1", {})
        await storage.save("key2", {})
        await storage.save("key3", {})
        
        keys = await storage.list_keys("key*")
        assert len(keys) == 3
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self, storage):
        """测试发布订阅"""
        import asyncio
        
        messages_received = []
        
        async def subscriber():
            async for message in storage.subscribe("test_channel"):
                messages_received.append(message)
                break  # 只接收一条消息
        
        # 启动订阅者
        subscriber_task = asyncio.create_task(subscriber())
        
        # 等待订阅
        await asyncio.sleep(0.1)
        
        # 发布消息
        await storage.publish("test_channel", {"test": "data"})
        
        # 等待消息处理
        await asyncio.sleep(0.1)
        
        # 取消订阅任务
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass
        
        assert len(messages_received) > 0
        assert messages_received[0]["data"] == {"test": "data"}


# ============================================================================
# AgentStorageManager 测试
# ============================================================================

class TestAgentStorageManager:
    """AgentStorageManager 测试类"""
    
    @pytest.fixture
    async def storage_manager(self, tmp_path):
        """创建 Agent 存储管理器"""
        manager = AgentStorageManager(
            backend="file",
            base_dir=str(tmp_path / "agents"),
            auto_backup=False
        )
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_save_and_load_agent(self, storage_manager):
        """测试保存和加载 Agent"""
        from src.sdk.agent.base import BaseAgent
        
        # 创建一个简单的 Agent
        config = AgentConfig(
            name="test_agent",
            agent_type="base",
            skills=["test"],
        )
        
        # 使用 BaseAgent（需要实际创建一个可实例化的 Agent）
        # 这里我们直接测试序列化/反序列化
        test_data = {
            "agent_id": "test-123",
            "name": "test_agent",
            "status": "idle",
        }
        
        # 保存
        success = await storage_manager._storage.save("agent:test-123", test_data)
        assert success is True
        
        # 加载
        loaded = await storage_manager._storage.load("agent:test-123")
        assert loaded is not None
        assert loaded["name"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_list_agents(self, storage_manager):
        """测试列出 Agent"""
        # 保存多个 Agent
        await storage_manager._storage.save("agent:agent1", {"name": "agent1"})
        await storage_manager._storage.save("agent:agent2", {"name": "agent2"})
        await storage_manager._storage.save("agent:agent3", {"name": "agent3"})
        
        agents = await storage_manager.list_agents()
        assert len(agents) == 3
        assert set(agents) == {"agent1", "agent2", "agent3"}
    
    @pytest.mark.asyncio
    async def test_agent_count(self, storage_manager):
        """测试 Agent 数量"""
        await storage_manager._storage.save("agent:agent1", {})
        await storage_manager._storage.save("agent:agent2", {})
        
        count = await storage_manager.get_agent_count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_backup_and_restore(self, storage_manager, tmp_path):
        """测试备份和恢复"""
        # 保存一些 Agent
        await storage_manager._storage.save("agent:agent1", {"name": "agent1"})
        await storage_manager._storage.save("agent:agent2", {"name": "agent2"})
        
        # 备份
        backup_dir = str(tmp_path / "backups")
        backup_path = await storage_manager.backup(backup_dir)
        
        assert backup_path is not None
        assert Path(backup_path).exists()
        
        # 清空
        await storage_manager.clear_all()
        
        # 恢复
        restored_count = await storage_manager.restore(backup_path)
        assert restored_count == 2
        
        # 验证恢复
        agents = await storage_manager.list_agents()
        assert len(agents) == 2
    
    @pytest.mark.asyncio
    async def test_stats(self, storage_manager):
        """测试统计信息"""
        await storage_manager._storage.save("agent:agent1", {})
        await storage_manager._storage.load("agent:agent1")
        
        stats = await storage_manager.get_stats()
        assert stats["total_saves"] >= 1
        assert stats["total_loads"] >= 1
        assert stats["backend"] == "file"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
