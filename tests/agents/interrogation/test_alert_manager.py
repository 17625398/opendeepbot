#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
告警管理器单元测试
"""

from unittest.mock import Mock

import pytest

from src.agents.interrogation.utils.alert_manager import (
    Alert,
    AlertLevel,
    AlertManager,
    AlertThreshold,
    AlertType,
    check_duration,
    check_error,
    get_alert_manager,
    set_threshold,
)


class TestAlertThreshold:
    """测试 AlertThreshold 类"""

    def test_creation(self):
        """测试创建阈值配置"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            max_duration=10.0,
            max_error_rate=0.1,
            min_throughput=100,
            consecutive_errors=5
        )

        assert threshold.agent_name == "TestAgent"
        assert threshold.max_duration == 10.0
        assert threshold.max_error_rate == 0.1
        assert threshold.min_throughput == 100
        assert threshold.consecutive_errors == 5

    def test_default_values(self):
        """测试默认值"""
        threshold = AlertThreshold(agent_name="TestAgent")

        assert threshold.max_duration is None
        assert threshold.max_error_rate is None
        assert threshold.min_throughput is None
        assert threshold.consecutive_errors == 3


class TestAlert:
    """测试 Alert 类"""

    def test_creation(self):
        """测试创建告警"""
        alert = Alert(
            id="alert_1",
            agent_name="TestAgent",
            alert_type=AlertType.DURATION_THRESHOLD,
            level=AlertLevel.WARNING,
            message="Test message",
            timestamp="2024-01-01T00:00:00",
            details={"key": "value"},
            acknowledged=False
        )

        assert alert.id == "alert_1"
        assert alert.agent_name == "TestAgent"
        assert alert.alert_type == AlertType.DURATION_THRESHOLD
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test message"
        assert alert.acknowledged is False


class TestAlertManager:
    """测试 AlertManager 类"""

    @pytest.fixture
    def manager(self):
        """创建告警管理器实例"""
        return AlertManager()

    def test_set_and_get_threshold(self, manager):
        """测试设置和获取阈值"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            max_duration=10.0
        )

        manager.set_threshold(threshold)

        retrieved = manager.get_threshold("TestAgent")
        assert retrieved is not None
        assert retrieved.max_duration == 10.0

    def test_check_duration_below_threshold(self, manager):
        """测试耗时低于阈值"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            max_duration=10.0
        )
        manager.set_threshold(threshold)

        # 低于阈值，不应触发告警
        manager.check_duration("TestAgent", 5.0)

        alerts = manager.get_alerts()
        assert len(alerts) == 0

    def test_check_duration_above_threshold(self, manager):
        """测试耗时超过阈值"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            max_duration=10.0
        )
        manager.set_threshold(threshold)

        # 超过阈值但不超过1.5倍，应触发 WARNING 告警
        manager.check_duration("TestAgent", 14.0)

        alerts = manager.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.DURATION_THRESHOLD
        assert alerts[0].level == AlertLevel.WARNING

    def test_check_duration_critical(self, manager):
        """测试严重超时"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            max_duration=10.0
        )
        manager.set_threshold(threshold)

        # 严重超时（超过1.5倍）
        manager.check_duration("TestAgent", 20.0)

        alerts = manager.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.ERROR

    def test_check_error_success(self, manager):
        """测试成功不触发告警"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            consecutive_errors=3
        )
        manager.set_threshold(threshold)

        # 成功不应触发告警
        manager.check_error("TestAgent", True)

        alerts = manager.get_alerts()
        assert len(alerts) == 0

    def test_check_error_consecutive(self, manager):
        """测试连续错误触发告警"""
        threshold = AlertThreshold(
            agent_name="TestAgent",
            consecutive_errors=3
        )
        manager.set_threshold(threshold)

        # 连续3次错误
        manager.check_error("TestAgent", False)
        manager.check_error("TestAgent", False)
        manager.check_error("TestAgent", False)

        alerts = manager.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.ERROR_RATE
        assert "连续 3 次" in alerts[0].message

    def test_alert_handler(self, manager):
        """测试告警处理器"""
        handler = Mock()
        manager.add_handler(handler)

        threshold = AlertThreshold(
            agent_name="TestAgent",
            max_duration=10.0
        )
        manager.set_threshold(threshold)

        manager.check_duration("TestAgent", 15.0)

        # 验证处理器被调用
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.agent_name == "TestAgent"

    def test_get_alerts_filtering(self, manager):
        """测试告警过滤"""
        # 创建两个 Agent 的告警
        threshold1 = AlertThreshold("Agent1", max_duration=10.0)
        threshold2 = AlertThreshold("Agent2", max_duration=10.0)
        manager.set_threshold(threshold1)
        manager.set_threshold(threshold2)

        # 14秒超过10秒阈值，产生 WARNING 级别告警
        manager.check_duration("Agent1", 14.0)
        manager.check_duration("Agent2", 14.0)

        # 按 Agent 过滤
        agent1_alerts = manager.get_alerts(agent_name="Agent1")
        assert len(agent1_alerts) == 1
        assert agent1_alerts[0].agent_name == "Agent1"

        # 按级别过滤
        warning_alerts = manager.get_alerts(level=AlertLevel.WARNING)
        assert len(warning_alerts) == 2

    def test_acknowledge_alert(self, manager):
        """测试确认告警"""
        threshold = AlertThreshold("TestAgent", max_duration=10.0)
        manager.set_threshold(threshold)

        manager.check_duration("TestAgent", 15.0)

        # 确认前
        alerts = manager.get_alerts(unacknowledged_only=True)
        assert len(alerts) == 1

        # 确认告警
        alert_id = alerts[0].id
        result = manager.acknowledge_alert(alert_id)
        assert result is True

        # 确认后
        alerts = manager.get_alerts(unacknowledged_only=True)
        assert len(alerts) == 0

        # 确认不存在的告警
        result = manager.acknowledge_alert("nonexistent")
        assert result is False

    def test_clear_alerts(self, manager):
        """测试清除告警"""
        threshold1 = AlertThreshold("Agent1", max_duration=10.0)
        threshold2 = AlertThreshold("Agent2", max_duration=10.0)
        manager.set_threshold(threshold1)
        manager.set_threshold(threshold2)

        manager.check_duration("Agent1", 15.0)
        manager.check_duration("Agent2", 15.0)

        assert len(manager.get_alerts()) == 2

        # 清除指定 Agent 的告警
        manager.clear_alerts("Agent1")
        assert len(manager.get_alerts()) == 1
        assert manager.get_alerts()[0].agent_name == "Agent2"

        # 清除所有告警
        manager.clear_alerts()
        assert len(manager.get_alerts()) == 0

    def test_get_alert_stats(self, manager):
        """测试告警统计"""
        threshold = AlertThreshold("TestAgent", max_duration=10.0)
        manager.set_threshold(threshold)

        # 14秒产生 WARNING，20秒产生 ERROR
        manager.check_duration("TestAgent", 14.0)
        manager.check_duration("TestAgent", 20.0)

        stats = manager.get_alert_stats()

        assert stats["total"] == 2
        assert stats["unacknowledged"] == 2
        assert stats["by_level"]["warning"] == 1
        assert stats["by_level"]["error"] == 1
        assert stats["by_agent"]["TestAgent"]["total"] == 2

    def test_no_threshold(self, manager):
        """测试无阈值配置"""
        # 没有设置阈值，不应触发告警
        manager.check_duration("TestAgent", 100.0)

        alerts = manager.get_alerts()
        assert len(alerts) == 0


class TestGlobalFunctions:
    """测试全局便捷函数"""

    def test_get_alert_manager_singleton(self):
        """测试全局管理器是单例"""
        manager1 = get_alert_manager()
        manager2 = get_alert_manager()
        assert manager1 is manager2

    def test_check_duration_global(self):
        """测试全局检查耗时函数"""
        # 设置阈值
        set_threshold(AlertThreshold("TestAgent", max_duration=10.0))

        # 超过阈值
        check_duration("TestAgent", 15.0)

        alerts = get_alert_manager().get_alerts()
        assert len(alerts) == 1

        # 清理
        get_alert_manager().clear_alerts()

    def test_check_error_global(self):
        """测试全局检查错误函数"""
        # 设置阈值
        set_threshold(AlertThreshold("TestAgent", consecutive_errors=1))

        # 错误
        check_error("TestAgent", False)

        alerts = get_alert_manager().get_alerts()
        assert len(alerts) == 1

        # 清理
        get_alert_manager().clear_alerts()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
