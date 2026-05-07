#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能监控单元测试
"""

import asyncio
import time

import pytest

from src.agents.interrogation.utils.performance_monitor import (
    AgentPerformanceMonitor,
    PerformanceMetrics,
    get_performance_monitor,
    monitor_context,
    monitor_performance,
)


class TestPerformanceMetrics:
    """测试 PerformanceMetrics 类"""
    
    def test_metrics_creation(self):
        """测试创建性能指标"""
        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=True
        )
        assert metrics.agent_name == "TestAgent"
        assert metrics.duration == pytest.approx(1.0, abs=0.01)
        assert metrics.success is True
    
    def test_metrics_with_error(self):
        """测试带错误的性能指标"""
        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=False,
            error="Test error"
        )
        assert metrics.success is False
        assert metrics.error == "Test error"


class TestAgentPerformanceMonitor:
    """测试 AgentPerformanceMonitor 类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.monitor = AgentPerformanceMonitor()
    
    def test_record_metrics(self):
        """测试记录性能指标"""
        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=True
        )
        self.monitor.record(metrics)
        
        stats = self.monitor.get_stats("TestAgent")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 0
    
    def test_record_multiple_metrics(self):
        """测试记录多个性能指标"""
        # 记录成功指标
        for i in range(3):
            metrics = PerformanceMetrics(
                agent_name="TestAgent",
                start_time=time.time(),
                end_time=time.time() + 1.0 + i,
                success=True
            )
            self.monitor.record(metrics)
        
        # 记录失败指标
        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 2.0,
            success=False,
            error="Test error"
        )
        self.monitor.record(metrics)
        
        stats = self.monitor.get_stats("TestAgent")
        assert stats["count"] == 4
        assert stats["success_count"] == 3
        assert stats["failure_count"] == 1
    
    def test_get_all_stats(self):
        """测试获取所有统计"""
        # 记录不同 Agent 的指标
        for agent_name in ["Agent1", "Agent2"]:
            metrics = PerformanceMetrics(
                agent_name=agent_name,
                start_time=time.time(),
                end_time=time.time() + 1.0,
                success=True
            )
            self.monitor.record(metrics)
        
        all_stats = self.monitor.get_stats()
        assert "Agent1" in all_stats
        assert "Agent2" in all_stats
    
    def test_get_summary(self):
        """测试获取摘要"""
        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=True
        )
        self.monitor.record(metrics)
        
        summary = self.monitor.get_summary()
        assert "TestAgent" in summary
        assert "Total calls: 1" in summary
    
    def test_reset(self):
        """测试重置统计"""
        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=True
        )
        self.monitor.record(metrics)
        
        self.monitor.reset()
        
        stats = self.monitor.get_stats()
        assert stats == {}


class TestMonitorPerformanceDecorator:
    """测试性能监控装饰器"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        # 重置全局监控器
        from src.agents.interrogation.utils import performance_monitor
        performance_monitor._global_monitor.reset()
    
    def test_sync_function_monitoring(self):
        """测试同步函数监控"""
        @monitor_performance("TestSyncAgent")
        def test_function():
            time.sleep(0.1)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("TestSyncAgent")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
    
    def test_sync_function_error(self):
        """测试同步函数错误监控"""
        @monitor_performance("TestSyncAgent")
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("TestSyncAgent")
        assert stats["count"] == 1
        assert stats["failure_count"] == 1
    
    @pytest.mark.asyncio
    async def test_async_function_monitoring(self):
        """测试异步函数监控"""
        @monitor_performance("TestAsyncAgent")
        async def test_async_function():
            await asyncio.sleep(0.1)
            return "async_result"
        
        result = await test_async_function()
        assert result == "async_result"
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("TestAsyncAgent")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
    
    @pytest.mark.asyncio
    async def test_async_function_error(self):
        """测试异步函数错误监控"""
        @monitor_performance("TestAsyncAgent")
        async def test_async_function():
            raise ValueError("Test async error")
        
        with pytest.raises(ValueError):
            await test_async_function()
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("TestAsyncAgent")
        assert stats["count"] == 1
        assert stats["failure_count"] == 1


class TestMonitorContext:
    """测试性能监控上下文管理器"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        from src.agents.interrogation.utils import performance_monitor
        performance_monitor._global_monitor.reset()
    
    def test_context_manager_success(self):
        """测试上下文管理器成功"""
        with monitor_context("TestContext"):
            time.sleep(0.1)
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("TestContext")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
    
    def test_context_manager_error(self):
        """测试上下文管理器错误"""
        with pytest.raises(ValueError):
            with monitor_context("TestContext"):
                raise ValueError("Test error")
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("TestContext")
        assert stats["count"] == 1
        assert stats["failure_count"] == 1


class TestGetPerformanceMonitor:
    """测试获取性能监控器"""
    
    def test_singleton_monitor(self):
        """测试全局监控器是单例"""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        assert monitor1 is monitor2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])