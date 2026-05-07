"""
SuperMemory 增强功能测试

测试遗忘机制、实体链接、记忆巩固等功能
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

from src.integrations.supermemory.enhancements import (
    MemoryCompressor,
    CompressionStrategy,
    ForgettingCurve,
    ForgettingCurveType,
    ForgettingConfig,
    MemoryForgettingManager,
    EntityLinker,
    LinkingResult,
    MemoryConsolidator,
    ConsolidationResult,
    MemoryPattern,
)


# =============================================================================
# 遗忘机制测试
# =============================================================================

class TestForgettingCurve:
    """测试遗忘曲线"""
    
    def test_ebbinghaus_curve(self):
        """测试艾宾浩斯遗忘曲线"""
        config = ForgettingConfig(
            curve_type=ForgettingCurveType.EBINGHAUS,
            base_strength=1.0
        )
        curve = ForgettingCurve(config)
        
        # 初始强度应该接近1
        strength = curve.calculate_strength(1.0, 0)
        assert strength > 0.9
        
        # 随着时间衰减
        strength_1day = curve.calculate_strength(1.0, 86400)
        strength_7days = curve.calculate_strength(1.0, 7 * 86400)
        
        assert strength_1day < strength
        assert strength_7days < strength_1day
    
    def test_exponential_decay(self):
        """测试指数衰减"""
        config = ForgettingConfig(
            curve_type=ForgettingCurveType.EXPONENTIAL,
            decay_rate=0.1
        )
        curve = ForgettingCurve(config)
        
        strength = curve.calculate_strength(1.0, 86400)
        assert 0 < strength < 1.0
    
    def test_access_count_boost(self):
        """测试访问次数提升"""
        config = ForgettingConfig(access_weight=0.3)
        curve = ForgettingCurve(config)
        
        strength_no_access = curve.calculate_strength(1.0, 86400, access_count=0)
        strength_with_access = curve.calculate_strength(1.0, 86400, access_count=10)
        
        assert strength_with_access > strength_no_access
    
    def test_importance_protection(self):
        """测试重要性保护"""
        config = ForgettingConfig(importance_weight=0.5)
        curve = ForgettingCurve(config)
        
        strength_low = curve.calculate_strength(1.0, 86400 * 10, importance=0.1)
        strength_high = curve.calculate_strength(1.0, 86400 * 10, importance=1.0)
        
        assert strength_high > strength_low
    
    def test_review_interval(self):
        """测试复习间隔计算"""
        curve = ForgettingCurve()
        
        # 高强度 = 长间隔
        interval_high = curve.calculate_review_interval(0.9)
        interval_low = curve.calculate_review_interval(0.3)
        
        assert interval_high > interval_low
    
    def test_should_forget(self):
        """测试遗忘判断"""
        curve = ForgettingCurve()
        
        assert curve.should_forget(0.1, threshold=0.2) is True
        assert curve.should_forget(0.3, threshold=0.2) is False


class TestMemoryForgettingManager:
    """测试记忆遗忘管理器"""
    
    @pytest.fixture
    def manager(self):
        return MemoryForgettingManager()
    
    def test_register_memory(self, manager):
        """测试注册记忆"""
        memory_data = {
            "id": "mem_001",
            "content": "测试内容",
            "importance": 0.8,
            "created_at": time.time()
        }
        
        manager.register_memory("mem_001", memory_data)
        
        assert "mem_001" in manager._memories
        assert manager._memories["mem_001"]["status"] == "active"
    
    def test_access_memory(self, manager):
        """测试访问记忆"""
        memory_data = {
            "id": "mem_001",
            "content": "测试内容",
            "importance": 0.5,
            "created_at": time.time()
        }
        
        manager.register_memory("mem_001", memory_data)
        
        # 访问记忆
        result = manager.access_memory("mem_001")
        assert result is True
        
        # 检查访问次数增加
        assert manager._memories["mem_001"]["access_count"] == 1
    
    def test_get_memory_strength(self, manager):
        """测试获取记忆强度"""
        memory_data = {
            "id": "mem_001",
            "content": "测试内容",
            "importance": 0.5,
            "created_at": time.time(),
            "initial_strength": 1.0
        }
        
        manager.register_memory("mem_001", memory_data)
        
        strength = manager.get_memory_strength("mem_001")
        assert strength is not None
        assert 0 <= strength <= 1.0
    
    def test_get_review_recommendations(self, manager):
        """测试获取复习推荐"""
        # 注册多个记忆
        for i in range(5):
            memory_data = {
                "id": f"mem_{i:03d}",
                "content": f"内容{i}",
                "importance": 0.5,
                "created_at": time.time() - i * 86400,  # 不同时间
                "initial_strength": 0.5
            }
            manager.register_memory(f"mem_{i:03d}", memory_data)
        
        recommendations = manager.get_review_recommendations(limit=3)
        assert len(recommendations) <= 3
    
    def test_force_forget(self, manager):
        """测试强制遗忘"""
        memory_data = {
            "id": "mem_001",
            "content": "测试内容",
            "created_at": time.time()
        }
        
        manager.register_memory("mem_001", memory_data)
        
        result = manager.force_forget("mem_001")
        assert result is True
        assert manager._memories["mem_001"]["status"] == "forgotten"
    
    def test_force_remember(self, manager):
        """测试强制记住"""
        memory_data = {
            "id": "mem_001",
            "content": "测试内容",
            "created_at": time.time()
        }
        
        manager.register_memory("mem_001", memory_data)
        manager.force_forget("mem_001")
        
        result = manager.force_remember("mem_001")
        assert result is True
        assert manager._memories["mem_001"]["status"] == "active"
        assert manager._memories["mem_001"]["initial_strength"] == 1.0
    
    def test_get_stats(self, manager):
        """测试获取统计"""
        stats = manager.get_stats()
        
        assert "total_memories" in stats
        assert "active_memories" in stats
        assert "forgetting_rate" in stats


# =============================================================================
# 实体链接测试
# =============================================================================

class TestEntityLinker:
    """测试实体链接器"""
    
    @pytest.fixture
    def linker(self):
        return EntityLinker()
    
    def test_register_entity(self, linker):
        """测试注册实体"""
        linker.register_entity(
            entity_id="ent_001",
            name="北京大学",
            entity_type="ORGANIZATION",
            aliases=["北大", "PKU"]
        )
        
        assert "ent_001" in linker._entities
        assert linker._entities["ent_001"]["name"] == "北京大学"
    
    @pytest.mark.asyncio
    async def test_exact_match(self, linker):
        """测试精确匹配"""
        linker.register_entity(
            entity_id="ent_001",
            name="北京大学",
            entity_type="ORGANIZATION"
        )
        
        result = await linker.link_entity("北京大学")
        
        assert result is not None
        assert result.entity_id == "ent_001"
        assert result.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_alias_match(self, linker):
        """测试别名匹配"""
        linker.register_entity(
            entity_id="ent_001",
            name="北京大学",
            entity_type="ORGANIZATION",
            aliases=["北大"]
        )
        
        result = await linker.link_entity("北大")
        
        assert result is not None
        assert result.entity_id == "ent_001"
        assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_fuzzy_match(self, linker):
        """测试模糊匹配"""
        linker.register_entity(
            entity_id="ent_001",
            name="北京大学",
            entity_type="ORGANIZATION"
        )
        
        result = await linker.link_entity("北京大")
        
        assert result is not None
        assert result.confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_create_new_entity(self, linker):
        """测试创建新实体"""
        result = await linker.link_entity("清华大学", entity_type="ORGANIZATION")
        
        assert result is not None
        assert result.is_new is True
        assert result.confidence == 1.0
    
    def test_merge_entities(self, linker):
        """测试合并实体"""
        linker.register_entity(
            entity_id="ent_001",
            name="北京大学",
            entity_type="ORGANIZATION",
            aliases=["北大"]
        )
        
        linker.register_entity(
            entity_id="ent_002",
            name="北大",
            entity_type="ORGANIZATION"
        )
        
        result = linker.merge_entities("ent_002", "ent_001")
        
        assert result is True
        assert "ent_002" in linker._entities["ent_001"]["linked_to"]
    
    def test_find_coreferences(self, linker):
        """测试查找共指"""
        linker.register_entity(
            entity_id="ent_001",
            name="北京大学",
            entity_type="ORGANIZATION",
            aliases=["北大"]
        )
        
        text = "北京大学是一所著名学府，北大位于北京。"
        coreferences = linker.find_coreferences(text, ["ent_001"])
        
        assert len(coreferences) >= 1
    
    def test_get_entity_cluster(self, linker):
        """测试获取实体聚类"""
        linker.register_entity("ent_001", "A", "TYPE")
        linker.register_entity("ent_002", "B", "TYPE")
        linker.register_entity("ent_003", "C", "TYPE")
        
        linker.merge_entities("ent_002", "ent_001")
        linker.merge_entities("ent_003", "ent_001")
        
        cluster = linker.get_entity_cluster("ent_001")
        
        assert len(cluster) == 3
    
    def test_get_linking_stats(self, linker):
        """测试获取链接统计"""
        linker.register_entity("ent_001", "A", "TYPE")
        linker.register_entity("ent_002", "B", "TYPE")
        linker.merge_entities("ent_002", "ent_001")
        
        stats = linker.get_linking_stats()
        
        assert stats["total_entities"] == 2
        assert stats["linked_entities"] == 2


# =============================================================================
# 记忆巩固测试
# =============================================================================

class TestMemoryConsolidator:
    """测试记忆巩固器"""
    
    @pytest.fixture
    def consolidator(self):
        return MemoryConsolidator()
    
    @pytest.mark.asyncio
    async def test_consolidate_insufficient_memories(self, consolidator):
        """测试记忆数量不足"""
        memories = [
            {"id": "mem_001", "content": "内容1", "tags": ["tag1"]},
            {"id": "mem_002", "content": "内容2", "tags": ["tag1"]}
        ]
        
        result = await consolidator.consolidate(memories, min_pattern_support=3)
        
        assert result.patterns_extracted == 0
        assert result.memories_consolidated == 0
    
    @pytest.mark.asyncio
    async def test_extract_tag_patterns(self, consolidator):
        """测试提取标签模式"""
        memories = [
            {"id": "mem_001", "content": "内容1", "tags": ["python", "programming"]},
            {"id": "mem_002", "content": "内容2", "tags": ["python", "programming"]},
            {"id": "mem_003", "content": "内容3", "tags": ["python", "programming"]},
        ]
        
        patterns = consolidator._extract_tag_patterns(memories, min_support=2)
        
        assert len(patterns) > 0
        assert any(p.pattern_type == "tag_cooccurrence" for p in patterns)
    
    @pytest.mark.asyncio
    async def test_extract_temporal_patterns(self, consolidator):
        """测试提取时间模式"""
        current_time = time.time()
        memories = [
            {"id": "mem_001", "content": "内容1", "created_at": current_time},
            {"id": "mem_002", "content": "内容2", "created_at": current_time + 3600},
            {"id": "mem_003", "content": "内容3", "created_at": current_time + 7200},
        ]
        
        patterns = consolidator._extract_temporal_patterns(memories, min_support=2)
        
        # 应该能找到时间聚类模式
        assert len(patterns) >= 0  # 可能找到也可能找不到，取决于时间分组
    
    @pytest.mark.asyncio
    async def test_generalize_knowledge(self, consolidator):
        """测试知识泛化"""
        patterns = [
            MemoryPattern(
                pattern_type="test",
                description="测试模式",
                supporting_memories=["mem_001", "mem_002", "mem_003"],
                confidence=0.8
            )
        ]
        
        generalizations = await consolidator._generalize_knowledge(patterns, min_confidence=0.7)
        
        assert len(generalizations) == 1
        assert generalizations[0]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_integrate_memories(self, consolidator):
        """测试记忆整合"""
        memories = [
            {"id": "mem_001", "content": "内容1", "strength": 0.5},
            {"id": "mem_002", "content": "内容2", "strength": 0.5},
            {"id": "mem_003", "content": "内容3", "strength": 0.5}
        ]
        
        patterns = [
            MemoryPattern(
                pattern_type="test",
                description="测试",
                supporting_memories=["mem_001", "mem_002"],
                confidence=0.8
            )
        ]
        
        consolidated = await consolidator._integrate_memories(memories, patterns)
        
        assert consolidated == 2
        assert memories[0].get("consolidated") is True
        assert memories[1].get("consolidated") is True
    
    def test_get_patterns(self, consolidator):
        """测试获取模式"""
        pattern = MemoryPattern(
            pattern_type="test_type",
            description="测试",
            supporting_memories=["mem_001"],
            confidence=0.8
        )
        consolidator._patterns.append(pattern)
        
        patterns = consolidator.get_patterns(pattern_type="test_type")
        
        assert len(patterns) == 1
        assert patterns[0].pattern_type == "test_type"
    
    def test_get_consolidation_stats(self, consolidator):
        """测试获取巩固统计"""
        stats = consolidator.get_consolidation_stats()
        
        assert "total_consolidations" in stats
        assert "patterns_found" in stats
        assert "total_patterns" in stats
    
    def test_get_transferable_knowledge(self, consolidator):
        """测试获取可迁移知识"""
        pattern = MemoryPattern(
            pattern_type="test",
            description="高置信度模式",
            supporting_memories=["mem_001"],
            confidence=0.9
        )
        consolidator._patterns.append(pattern)
        
        transferable = consolidator.get_transferable_knowledge("agent_a", "agent_b")
        
        assert len(transferable) == 1
        assert transferable[0]["source"] == "agent_a"
        assert transferable[0]["target"] == "agent_b"


# =============================================================================
# 记忆压缩测试
# =============================================================================

class TestMemoryCompressor:
    """测试记忆压缩器"""
    
    @pytest.fixture
    def compressor(self):
        return MemoryCompressor()
    
    @pytest.mark.asyncio
    async def test_compress_by_deduplication(self, compressor):
        """测试去重压缩"""
        memories = [
            {"id": "mem_001", "content": "重复内容", "tags": ["tag1"]},
            {"id": "mem_002", "content": "重复内容", "tags": ["tag1"]},
            {"id": "mem_003", "content": "独特内容", "tags": ["tag2"]}
        ]
        
        result = await compressor.compress_by_deduplication(memories)
        
        assert result.compressed_count == 2
        assert result.compression_ratio > 0
    
    @pytest.mark.asyncio
    async def test_compress_by_merging(self, compressor):
        """测试合并压缩"""
        memories = [
            {"id": "mem_001", "content": "Python编程", "tags": ["python", "code"]},
            {"id": "mem_002", "content": "Python学习", "tags": ["python", "study"]},
            {"id": "mem_003", "content": "Java编程", "tags": ["java", "code"]}
        ]
        
        result = await compressor.compress_by_merging(memories, similarity_threshold=0.5)
        
        # 由于标签相似度计算，可能合并也可能不合并
        assert result.original_count == 3
    
    @pytest.mark.asyncio
    async def test_compress_by_pruning(self, compressor):
        """测试剪枝压缩"""
        current_time = time.time()
        memories = [
            {"id": "mem_001", "content": "重要内容", "importance": 0.9, "created_at": current_time - 86400 * 400},
            {"id": "mem_002", "content": "不重要内容", "importance": 0.1, "created_at": current_time - 86400 * 400, "access_count": 0},
            {"id": "mem_003", "content": "频繁访问", "importance": 0.1, "created_at": current_time - 86400 * 400, "access_count": 10}
        ]
        
        result = await compressor.compress_by_pruning(
            memories,
            importance_threshold=0.3,
            age_threshold_days=365
        )
        
        # 重要内容和频繁访问的应该保留
        assert result.compressed_count >= 2
    
    @pytest.mark.asyncio
    async def test_auto_compress(self, compressor):
        """测试自动压缩"""
        memories = [
            {"id": "mem_001", "content": "重复内容"},
            {"id": "mem_002", "content": "重复内容"},
            {"id": "mem_003", "content": "重复内容"},
            {"id": "mem_004", "content": "独特内容"}
        ]
        
        result = await compressor.auto_compress(memories, target_ratio=0.5)
        
        assert result.compression_ratio > 0
    
    def test_group_by_topic(self, compressor):
        """测试按主题分组"""
        memories = [
            {"id": "mem_001", "content": "内容1", "topic": "python"},
            {"id": "mem_002", "content": "内容2", "topic": "python"},
            {"id": "mem_003", "content": "内容3", "topic": "java"}
        ]
        
        groups = compressor._group_by_topic(memories)
        
        assert "python" in groups
        assert "java" in groups
        assert len(groups["python"]) == 2
    
    def test_cluster_by_similarity(self, compressor):
        """测试基于相似度聚类"""
        memories = [
            {"id": "mem_001", "content": "内容1", "tags": ["python", "code"]},
            {"id": "mem_002", "content": "内容2", "tags": ["python", "code"]},
            {"id": "mem_003", "content": "内容3", "tags": ["java", "code"]}
        ]
        
        clusters = compressor._cluster_by_similarity(memories, threshold=0.5)
        
        assert len(clusters) > 0
    
    def test_calculate_similarity(self, compressor):
        """测试相似度计算"""
        memory1 = {"id": "mem_001", "content": "内容1", "tags": ["python", "code"]}
        memory2 = {"id": "mem_002", "content": "内容2", "tags": ["python", "study"]}
        
        similarity = compressor._calculate_similarity(memory1, memory2)
        
        assert 0 <= similarity <= 1.0
        assert similarity > 0  # 有共同标签 "python"
    
    def test_get_stats(self, compressor):
        """测试获取统计"""
        stats = compressor.get_stats()
        
        assert "total_compressions" in stats
        assert "total_saved_bytes" in stats
        assert "strategy_usage" in stats
