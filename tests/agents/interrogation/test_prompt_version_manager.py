#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prompt 版本管理器单元测试
"""

from datetime import datetime

import pytest

from src.agents.interrogation.prompt_version_manager import (
    PromptStatus,
    PromptVersion,
    PromptVersionManager,
    get_prompt_version_manager,
)


class TestPromptVersion:
    """测试 PromptVersion 类"""
    
    def test_creation(self):
        """测试创建版本"""
        version = PromptVersion(
            version="v20240101_120000",
            agent_name="test_agent",
            content={"system": "test prompt"},
            status=PromptStatus.DRAFT,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Test version",
            author="test_user"
        )
        
        assert version.version == "v20240101_120000"
        assert version.agent_name == "test_agent"
        assert version.content == {"system": "test prompt"}
        assert version.status == PromptStatus.DRAFT
        assert version.description == "Test version"
        assert version.author == "test_user"
        assert version.tags == []
        assert version.metrics == {}
    
    def test_to_dict(self):
        """测试转换为字典"""
        version = PromptVersion(
            version="v1",
            agent_name="test",
            content={"key": "value"},
            status=PromptStatus.ACTIVE,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        data = version.to_dict()
        assert data["version"] == "v1"
        assert data["status"] == "active"
        assert data["content"] == {"key": "value"}
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "version": "v1",
            "agent_name": "test",
            "content": {"key": "value"},
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        version = PromptVersion.from_dict(data)
        assert version.version == "v1"
        assert version.status == PromptStatus.ACTIVE
    
    def test_compute_hash(self):
        """测试计算哈希"""
        version = PromptVersion(
            version="v1",
            agent_name="test",
            content={"system": "prompt content"},
            status=PromptStatus.DRAFT,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        hash1 = version.compute_hash()
        assert len(hash1) == 8
        
        # 相同内容应该产生相同哈希
        hash2 = version.compute_hash()
        assert hash1 == hash2
        
        # 不同内容应该产生不同哈希
        version.content = {"system": "different content"}
        hash3 = version.compute_hash()
        assert hash1 != hash3


class TestPromptVersionManager:
    """测试 PromptVersionManager 类"""
    
    @pytest.fixture
    def temp_versions_dir(self, tmp_path):
        """创建临时版本目录"""
        return tmp_path / "versions"
    
    @pytest.fixture
    def manager(self, temp_versions_dir):
        """创建版本管理器实例"""
        return PromptVersionManager(temp_versions_dir)
    
    def test_initialization(self, temp_versions_dir):
        """测试初始化"""
        manager = PromptVersionManager(temp_versions_dir)
        assert manager.versions_dir == temp_versions_dir
        assert temp_versions_dir.exists()
    
    def test_create_version(self, manager):
        """测试创建版本"""
        content = {"system": "test prompt", "user": "test template"}
        
        version = manager.create_version(
            agent_name="test_agent",
            content=content,
            description="Initial version",
            author="test_user",
            tags=["v1", "initial"]
        )
        
        assert version.agent_name == "test_agent"
        assert version.content == content
        assert version.description == "Initial version"
        assert version.author == "test_user"
        assert version.tags == ["v1", "initial"]
        assert version.status == PromptStatus.DRAFT
        assert version.version.startswith("v20")
    
    def test_get_version(self, manager):
        """测试获取版本"""
        # 创建版本
        version = manager.create_version(
            agent_name="test_agent",
            content={"system": "test"}
        )
        
        # 获取版本
        retrieved = manager.get_version("test_agent", version.version)
        assert retrieved is not None
        assert retrieved.version == version.version
        
        # 获取不存在的版本
        assert manager.get_version("test_agent", "nonexistent") is None
        assert manager.get_version("nonexistent_agent", version.version) is None
    
    def test_set_and_get_active_version(self, manager):
        """测试设置和获取活跃版本"""
        # 创建两个版本
        v1 = manager.create_version(
            agent_name="test_agent",
            content={"system": "v1"}
        )
        v2 = manager.create_version(
            agent_name="test_agent",
            content={"system": "v2"}
        )

        # 先设置 v1 为活跃
        result = manager.set_active_version("test_agent", v1.version)
        assert result is True

        # 获取活跃版本
        active = manager.get_active_version("test_agent")
        assert active is not None
        assert active.version == v1.version
        assert active.status == PromptStatus.ACTIVE

        # 再设置 v2 为活跃，此时 v1 应该被设为废弃
        result = manager.set_active_version("test_agent", v2.version)
        assert result is True

        # v1 应该被设为废弃
        v1_updated = manager.get_version("test_agent", v1.version)
        assert v1_updated.status == PromptStatus.DEPRECATED

        # v2 应该是活跃状态
        v2_updated = manager.get_version("test_agent", v2.version)
        assert v2_updated.status == PromptStatus.ACTIVE
    
    def test_list_versions(self, manager):
        """测试列出版本"""
        # 创建多个版本
        manager.create_version("agent1", {"system": "a1v1"})
        manager.create_version("agent1", {"system": "a1v2"})
        manager.create_version("agent2", {"system": "a2v1"})
        
        # 列出所有版本
        all_versions = manager.list_versions()
        assert len(all_versions) == 3
        
        # 按 Agent 过滤
        agent1_versions = manager.list_versions(agent_name="agent1")
        assert len(agent1_versions) == 2
        
        # 按状态过滤
        draft_versions = manager.list_versions(status=PromptStatus.DRAFT)
        assert len(draft_versions) == 3
    
    def test_update_metrics(self, manager):
        """测试更新指标"""
        # 创建版本
        version = manager.create_version(
            agent_name="test_agent",
            content={"system": "test"}
        )
        
        # 更新指标
        metrics = {
            "avg_response_time": 2.5,
            "success_rate": 0.95,
            "usage_count": 100
        }
        result = manager.update_metrics("test_agent", version.version, metrics)
        assert result is True
        
        # 验证指标
        updated = manager.get_version("test_agent", version.version)
        assert updated.metrics["avg_response_time"] == 2.5
        assert updated.metrics["success_rate"] == 0.95
        
        # 更新不存在的版本
        result = manager.update_metrics("test_agent", "nonexistent", {})
        assert result is False
    
    def test_compare_versions(self, manager):
        """测试比较版本"""
        # 创建两个版本
        v1 = manager.create_version(
            agent_name="test_agent",
            content={"system": "content v1"}
        )
        v2 = manager.create_version(
            agent_name="test_agent",
            content={"system": "content v2"}
        )
        
        # 比较版本
        comparison = manager.compare_versions("test_agent", v1.version, v2.version)
        
        assert "version1" in comparison
        assert "version2" in comparison
        assert comparison["content_diff"] is True
        assert comparison["metrics_diff"] is False
        
        # 比较不存在的版本
        comparison = manager.compare_versions("test_agent", v1.version, "nonexistent")
        assert "error" in comparison
    
    def test_delete_version(self, manager):
        """测试删除版本"""
        # 创建版本
        version = manager.create_version(
            agent_name="test_agent",
            content={"system": "test"}
        )
        
        # 删除版本
        result = manager.delete_version("test_agent", version.version)
        assert result is True
        assert manager.get_version("test_agent", version.version) is None
        
        # 删除不存在的版本
        result = manager.delete_version("test_agent", "nonexistent")
        assert result is False
    
    def test_cannot_delete_active_version(self, manager):
        """测试不能删除活跃版本"""
        # 创建并激活版本
        version = manager.create_version(
            agent_name="test_agent",
            content={"system": "test"}
        )
        manager.set_active_version("test_agent", version.version)
        
        # 尝试删除活跃版本
        result = manager.delete_version("test_agent", version.version)
        assert result is False
        
        # 版本应该仍然存在
        assert manager.get_version("test_agent", version.version) is not None
    
    def test_get_version_stats(self, manager):
        """测试获取版本统计"""
        # 创建版本
        manager.create_version("agent1", {"system": "a1"})
        manager.create_version("agent1", {"system": "a2"})
        manager.create_version("agent2", {"system": "b1"})
        
        # 获取统计
        stats = manager.get_version_stats()
        
        assert stats["total_agents"] == 2
        assert stats["total_versions"] == 3
        assert stats["active_versions"] == 0
        assert "agent1" in stats["agents"]
        assert "agent2" in stats["agents"]
        
        agent1_stats = stats["agents"]["agent1"]
        assert agent1_stats["total_versions"] == 2
    
    def test_persistence(self, temp_versions_dir):
        """测试持久化"""
        # 创建管理器并添加版本
        manager1 = PromptVersionManager(temp_versions_dir)
        version = manager1.create_version(
            agent_name="test_agent",
            content={"system": "persistent content"}
        )
        
        # 创建新的管理器（应该加载已有版本）
        manager2 = PromptVersionManager(temp_versions_dir)
        retrieved = manager2.get_version("test_agent", version.version)
        
        assert retrieved is not None
        assert retrieved.content == {"system": "persistent content"}


class TestGetPromptVersionManager:
    """测试获取全局管理器"""
    
    def test_singleton(self):
        """测试单例模式"""
        manager1 = get_prompt_version_manager()
        manager2 = get_prompt_version_manager()
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])