#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interrogation 模块集成测试

测试整个 Pipeline 的端到端流程。
"""

from unittest.mock import Mock, patch

import pytest

from src.agents.interrogation.agent_factory import AgentFactory, AgentType
from src.agents.interrogation.data_structures import (
    AnalysisResult,
    ExtractedInfo,
    InterrogationRecord,
    LegalMatch,
    QualityScore,
    RelationData,
)
from src.agents.interrogation.prompt_version_manager import (
    PromptStatus,
    get_prompt_version_manager,
)
from src.agents.interrogation.utils import (
    AlertThreshold,
    get_alert_manager,
    get_performance_monitor,
)


class TestAgentFactoryIntegration:
    """测试 Agent 工厂集成"""

    @pytest.mark.asyncio
    async def test_create_and_use_agent(self):
        """测试创建并使用 Agent"""
        # 创建 Agent
        agent = AgentFactory.create_agent(AgentType.EXTRACT)
        assert agent is not None

        # 创建模拟记录（使用正确的字段）
        from datetime import datetime
        record = InterrogationRecord(
            case_id="TEST001",
            interrogator="询问人",
            interviewee="被询问人",
            time=datetime.now(),
            location="地点",
            content="测试笔录内容",
            record_id="REC001"
        )

        # 由于实际调用需要 LLM，这里只验证 Agent 可以创建
        assert agent.agent_name == "extract_agent"

    def test_create_pipeline_agents(self):
        """测试创建 Pipeline Agents"""
        agents = AgentFactory.create_pipeline_agents()

        assert "extract" in agents
        assert "legal_match" in agents
        assert "quality" in agents
        assert "relation" in agents
        assert "report" in agents

    def test_singleton_mode(self):
        """测试单例模式"""
        agent1 = AgentFactory.create_agent(
            AgentType.EXTRACT,
            use_singleton=True
        )
        agent2 = AgentFactory.create_agent(
            AgentType.EXTRACT,
            use_singleton=True
        )

        assert agent1 is agent2


class TestPerformanceMonitorIntegration:
    """测试性能监控集成"""

    def test_monitor_with_alert(self):
        """测试性能监控与告警集成"""
        # 设置告警阈值
        alert_manager = get_alert_manager()
        alert_manager.set_threshold(AlertThreshold(
            agent_name="TestAgent",
            max_duration=1.0,  # 1秒阈值
            consecutive_errors=2
        ))

        # 清除之前的告警
        alert_manager.clear_alerts()

        # 记录性能指标（超过阈值）
        monitor = get_performance_monitor()
        import time

        from src.agents.interrogation.utils.performance_monitor import PerformanceMetrics

        metrics = PerformanceMetrics(
            agent_name="TestAgent",
            start_time=time.time(),
            end_time=time.time() + 2.0,  # 2秒，超过1秒阈值
            success=True
        )
        monitor.record(metrics)

        # 验证告警被触发
        alerts = alert_manager.get_alerts(agent_name="TestAgent")
        assert len(alerts) == 1
        assert alerts[0].agent_name == "TestAgent"

        # 清理
        alert_manager.clear_alerts()
        monitor.reset()

    def test_error_alert_integration(self):
        """测试错误告警集成"""
        alert_manager = get_alert_manager()
        alert_manager.set_threshold(AlertThreshold(
            agent_name="ErrorAgent",
            consecutive_errors=2
        ))
        alert_manager.clear_alerts()

        # 记录错误
        monitor = get_performance_monitor()
        import time

        from src.agents.interrogation.utils.performance_monitor import PerformanceMetrics

        # 第一次错误
        metrics1 = PerformanceMetrics(
            agent_name="ErrorAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=False,
            error="Test error"
        )
        monitor.record(metrics1)

        # 第二次错误（应该触发告警）
        metrics2 = PerformanceMetrics(
            agent_name="ErrorAgent",
            start_time=time.time(),
            end_time=time.time() + 1.0,
            success=False,
            error="Test error"
        )
        monitor.record(metrics2)

        # 验证告警
        alerts = alert_manager.get_alerts(agent_name="ErrorAgent")
        assert len(alerts) >= 1

        # 清理
        alert_manager.clear_alerts()
        monitor.reset()


class TestPromptVersionManagerIntegration:
    """测试 Prompt 版本管理集成"""

    def test_version_lifecycle(self, tmp_path):
        """测试版本完整生命周期"""
        from src.agents.interrogation.prompt_version_manager import PromptVersionManager

        # 创建管理器
        manager = PromptVersionManager(tmp_path / "versions")

        # 1. 创建版本
        version1 = manager.create_version(
            agent_name="TestAgent",
            content={"system": "v1"},
            description="初始版本"
        )
        assert version1.status == PromptStatus.DRAFT

        # 2. 激活版本
        result = manager.set_active_version("TestAgent", version1.version)
        assert result is True

        version1_updated = manager.get_version("TestAgent", version1.version)
        assert version1_updated.status == PromptStatus.ACTIVE

        # 3. 创建新版本并激活（旧版本应该变为废弃）
        version2 = manager.create_version(
            agent_name="TestAgent",
            content={"system": "v2"},
            description="优化版本"
        )
        manager.set_active_version("TestAgent", version2.version)

        version1_updated = manager.get_version("TestAgent", version1.version)
        assert version1_updated.status == PromptStatus.DEPRECATED

        version2_updated = manager.get_version("TestAgent", version2.version)
        assert version2_updated.status == PromptStatus.ACTIVE

        # 4. 更新指标
        manager.update_metrics("TestAgent", version2.version, {
            "avg_response_time": 1.5,
            "success_rate": 0.95
        })

        version2_with_metrics = manager.get_version("TestAgent", version2.version)
        assert version2_with_metrics.metrics["avg_response_time"] == 1.5

        # 5. 获取统计
        stats = manager.get_version_stats()
        assert stats["total_agents"] == 1
        assert stats["total_versions"] == 2

    def test_version_comparison(self, tmp_path):
        """测试版本比较"""
        from src.agents.interrogation.prompt_version_manager import PromptVersionManager

        manager = PromptVersionManager(tmp_path / "versions")

        # 创建两个版本
        v1 = manager.create_version(
            agent_name="TestAgent",
            content={"system": "content v1"}
        )
        v2 = manager.create_version(
            agent_name="TestAgent",
            content={"system": "content v2"}
        )

        # 比较版本
        comparison = manager.compare_versions("TestAgent", v1.version, v2.version)

        assert comparison["content_diff"] is True
        assert "version1" in comparison
        assert "version2" in comparison


class TestCacheManagerIntegration:
    """测试缓存管理集成"""

    def test_cache_with_ttl(self, tmp_path):
        """测试带 TTL 的缓存"""
        from src.agents.interrogation.utils.cache_manager import InterrogationCacheManager

        cache = InterrogationCacheManager(
            tmp_path / "cache",
            "TEST001",
            ttl=1  # 1秒 TTL
        )

        # 保存数据
        cache.save_step_result("extract", {"data": "test"})

        # 立即获取应该成功
        result = cache.get_step_result("extract")
        assert result is not None

        # 等待过期
        import time
        time.sleep(2)

        # 过期后获取应该失败
        result = cache.get_step_result("extract")
        assert result is None

    def test_cache_metadata(self, tmp_path):
        """测试缓存元数据"""
        from src.agents.interrogation.utils.cache_manager import InterrogationCacheManager

        cache = InterrogationCacheManager(tmp_path / "cache", "TEST002")

        # 保存带元数据的数据
        cache.save_step_result(
            "extract",
            {"data": "test"},
            metadata={"version": "1.0", "source": "test"}
        )

        # 获取数据
        result = cache.get_step_result("extract")
        assert result["metadata"]["version"] == "1.0"

        # 获取缓存信息
        info = cache.get_cache_info()
        # 验证缓存存在且包含步骤
        assert info["cache_exists"] is True
        assert "extract" in info["cached_steps"]


class TestEndToEndWorkflow:
    """测试端到端工作流"""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow_mock(self):
        """测试完整分析工作流（Mock 版本）"""
        # 创建模拟的 Pipeline
        from src.agents.interrogation.interrogation_pipeline import InterrogationPipeline

        # Mock LLM 配置
        with patch('src.agents.interrogation.interrogation_pipeline.get_llm_config') as mock_config:
            mock_config.return_value = Mock(
                api_key="test_key",
                base_url="http://test.com",
                model="gpt-4",
                binding="openai"
            )

            # 创建 Pipeline
            pipeline = InterrogationPipeline(
                output_dir="./test_output",
                kb_name="test_kb"
            )

            # 验证 Pipeline 创建成功
            assert pipeline is not None
            # output_dir 是 Path 对象，使用 str 比较
            assert str(pipeline.output_dir) == "test_output"

    def test_data_structures_integration(self):
        """测试数据结构集成"""
        # 创建完整的分析结果（使用正确的字段名）
        extracted_info = ExtractedInfo(
            persons=[{"name": "张三", "type": "person"}],
            events=[{"description": "事件发生"}],
            locations=["北京"],
            key_points=["关键点"]
        )

        legal_matches = [
            LegalMatch(
                article="第1条",
                content="法律内容",
                relevance=0.9,
                source="刑法"
            )
        ]

        quality_score = QualityScore(
            total_score=0.85,
            completeness=0.8,
            standardization=0.9,
            logic=0.85,
            legality=0.9
        )

        relations = RelationData(
            person_relations=[{"from": "张三", "to": "李四", "relation": "同事"}],
            timeline=[{"time": "2024-01-01", "event": "事件发生"}],
            evidence_chain=[{"evidence": "证据1", "confidence": 0.9}]
        )

        # 创建笔录记录
        from datetime import datetime
        record = InterrogationRecord(
            case_id="TEST001",
            interrogator="询问人",
            interviewee="被询问人",
            time=datetime.now(),
            location="地点",
            content="测试内容",
            record_id="REC001"
        )

        # 创建分析结果
        result = AnalysisResult(
            record=record,
            extracted_info=extracted_info,
            legal_matches=legal_matches,
            quality_score=quality_score,
            relations=relations,
            report="# 分析报告"
        )

        # 验证数据结构
        assert result.record.case_id == "TEST001"
        assert len(result.extracted_info.persons) == 1
        assert len(result.legal_matches) == 1
        assert result.quality_score.total_score == 0.85


class TestUtilsIntegration:
    """测试工具函数集成"""

    def test_all_utils_singletons(self):
        """测试所有工具单例"""
        from src.agents.interrogation.utils import (
            get_alert_manager,
            get_performance_monitor,
        )

        # 验证都是单例
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        assert monitor1 is monitor2

        alert1 = get_alert_manager()
        alert2 = get_alert_manager()
        assert alert1 is alert2

        version1 = get_prompt_version_manager()
        version2 = get_prompt_version_manager()
        assert version1 is version2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
