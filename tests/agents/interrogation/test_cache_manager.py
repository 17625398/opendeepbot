#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
缓存管理器单元测试
"""

from datetime import datetime
import time

import pytest

from src.agents.interrogation.utils.cache_manager import InterrogationCacheManager


class TestInterrogationCacheManager:
    """测试 InterrogationCacheManager 类"""
    
    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """创建临时缓存目录"""
        return tmp_path / "cache"
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """创建缓存管理器实例"""
        return InterrogationCacheManager(temp_cache_dir, "test_case_001", ttl=3600)
    
    def test_initialization(self, temp_cache_dir):
        """测试初始化"""
        manager = InterrogationCacheManager(temp_cache_dir, "test_case_001", ttl=7200)
        
        assert manager.case_id == "test_case_001"
        assert manager._ttl == 7200
        assert manager.cache_dir.exists()
        assert "test_case_001" in str(manager.cache_file)
    
    def test_save_and_get_step_result(self, cache_manager):
        """测试保存和获取步骤结果"""
        # 保存结果
        result = {"key": "value", "number": 123}
        cache_manager.save_step_result("extract", result)
        
        # 获取结果
        step_data = cache_manager.get_step_result("extract")
        assert step_data is not None
        assert step_data["result"] == result
        assert "saved_at" in step_data
        assert "expires_at" in step_data
    
    def test_get_nonexistent_step(self, cache_manager):
        """测试获取不存在的步骤"""
        result = cache_manager.get_step_result("nonexistent")
        assert result is None
    
    def test_step_expiration(self, temp_cache_dir):
        """测试步骤过期"""
        # 创建短 TTL 的缓存管理器
        manager = InterrogationCacheManager(temp_cache_dir, "test_case_002", ttl=1)
        
        # 保存结果
        manager.save_step_result("extract", {"data": "test"})
        
        # 立即获取应该成功
        result = manager.get_step_result("extract")
        assert result is not None
        
        # 等待过期
        time.sleep(2)
        
        # 再次获取应该返回 None
        result = manager.get_step_result("extract")
        assert result is None
    
    def test_custom_ttl_per_step(self, cache_manager):
        """测试每个步骤的自定义 TTL"""
        # 保存带自定义 TTL 的结果
        cache_manager.save_step_result("step1", {"data": "1"}, ttl=3600)
        cache_manager.save_step_result("step2", {"data": "2"}, ttl=7200)
        
        # 获取结果
        step1 = cache_manager.get_step_result("step1")
        step2 = cache_manager.get_step_result("step2")
        
        assert step1 is not None
        assert step2 is not None
        
        # 检查过期时间
        expires1 = datetime.fromisoformat(step1["expires_at"])
        expires2 = datetime.fromisoformat(step2["expires_at"])
        
        # step2 的过期时间应该比 step1 晚
        assert expires2 > expires1
    
    def test_cleanup_expired_on_init(self, temp_cache_dir):
        """测试初始化时清理过期缓存"""
        # 创建缓存管理器并保存数据
        manager1 = InterrogationCacheManager(temp_cache_dir, "test_case_003", ttl=1)
        manager1.save_step_result("old_step", {"data": "old"})
        
        # 等待过期
        time.sleep(2)
        
        # 创建新的缓存管理器（应该清理过期数据）
        manager2 = InterrogationCacheManager(temp_cache_dir, "test_case_003", ttl=3600)
        
        # 过期数据应该被清理
        result = manager2.get_step_result("old_step")
        assert result is None
    
    def test_clear_cache(self, cache_manager):
        """测试清空缓存"""
        # 保存数据
        cache_manager.save_step_result("step1", {"data": "1"})
        cache_manager.save_step_result("step2", {"data": "2"})
        
        # 清空缓存
        cache_manager.clear()
        
        # 所有数据应该被删除
        assert cache_manager.get_step_result("step1") is None
        assert cache_manager.get_step_result("step2") is None
        assert cache_manager._cache["steps"] == {}
    
    def test_delete_step(self, cache_manager):
        """测试删除指定步骤"""
        # 保存数据
        cache_manager.save_step_result("step1", {"data": "1"})
        cache_manager.save_step_result("step2", {"data": "2"})
        
        # 删除 step1
        result = cache_manager.delete_step("step1")
        assert result is True
        
        # step1 应该被删除，step2 应该保留
        assert cache_manager.get_step_result("step1") is None
        assert cache_manager.get_step_result("step2") is not None
        
        # 删除不存在的步骤
        result = cache_manager.delete_step("nonexistent")
        assert result is False
    
    def test_is_step_expired(self, temp_cache_dir):
        """测试检查步骤是否过期"""
        manager = InterrogationCacheManager(temp_cache_dir, "test_case_004", ttl=1)
        
        # 保存结果
        manager.save_step_result("expiring_step", {"data": "test"})
        
        # 未过期
        assert manager.is_step_expired("expiring_step") is False
        
        # 等待过期
        time.sleep(2)
        
        # 已过期
        assert manager.is_step_expired("expiring_step") is True
        
        # 不存在的步骤视为过期
        assert manager.is_step_expired("nonexistent") is True
    
    def test_get_cache_info(self, cache_manager):
        """测试获取缓存信息"""
        # 保存数据
        cache_manager.save_step_result("extract", {"data": "test"})
        
        # 获取信息
        info = cache_manager.get_cache_info()
        
        assert "cache_file" in info
        assert "cache_exists" in info
        assert "cached_steps" in info
        assert "steps_info" in info
        assert "ttl" in info
        assert info["ttl"] == 3600
        assert "extract" in info["cached_steps"]
        assert len(info["steps_info"]) == 1
        
        step_info = info["steps_info"][0]
        assert step_info["step_name"] == "extract"
        assert "saved_at" in step_info
        assert "expires_at" in step_info
        assert "is_expired" in step_info
        assert step_info["is_expired"] is False
    
    def test_serialize_dataclass(self, cache_manager):
        """测试序列化 dataclass"""
        from dataclasses import dataclass
        
        @dataclass
        class TestData:
            name: str
            value: int
        
        data = TestData(name="test", value=42)
        cache_manager.save_step_result("dataclass_step", data)
        
        result = cache_manager.get_step_result("dataclass_step")
        assert result is not None
        assert result["result"]["name"] == "test"
        assert result["result"]["value"] == 42
    
    def test_serialize_complex_object(self, cache_manager):
        """测试序列化复杂对象"""
        class TestObject:
            def __init__(self):
                self.name = "test"
                self.nested = {"key": "value"}
        
        obj = TestObject()
        cache_manager.save_step_result("object_step", obj)
        
        result = cache_manager.get_step_result("object_step")
        assert result is not None
        assert result["result"]["name"] == "test"
        assert result["result"]["nested"]["key"] == "value"
    
    def test_metadata(self, cache_manager):
        """测试元数据"""
        metadata = {"version": "1.0", "source": "test"}
        cache_manager.save_step_result("step", {"data": "test"}, metadata=metadata)
        
        result = cache_manager.get_step_result("step")
        assert result is not None
        assert result["metadata"] == metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])