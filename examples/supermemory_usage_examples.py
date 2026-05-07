"""
SuperMemory 使用示例

展示如何使用 SuperMemory 的各种功能
"""

import asyncio
import time
from typing import List, Dict, Any

# 导入 SuperMemory 组件
from src.integrations.supermemory import (
    # 基础组件
    SuperMemoryClient,
    MemoryStorageService,
    KnowledgeGraphService,
    AgentMemoryManager,
    
    # 性能优化
    get_cache_manager,
    get_vector_search_optimizer,
    get_batch_processor,
    get_metrics_collector,
    timed,
    
    # 功能增强
    MemoryCompressor,
    CompressionStrategy,
    MemoryForgettingManager,
    EntityLinker,
    MemoryConsolidator,
    
    # 模型
    MemoryType,
    MemoryRecord,
)


# =============================================================================
# 示例 1: 基础记忆存储和检索
# =============================================================================

async def example_basic_memory_operations():
    """基础记忆操作示例"""
    print("\n=== 示例 1: 基础记忆操作 ===\n")
    
    # 初始化存储服务
    storage = MemoryStorageService()
    await storage.initialize()
    
    # 存储记忆
    memory = await storage.store_memory(
        content="Python 是一种高级编程语言，由 Guido van Rossum 创建",
        memory_type=MemoryType.SEMANTIC,
        importance=0.9,
        tags=["编程", "Python", "语言"],
        categories=["技术", "编程语言"],
        metadata={"source": "学习笔记", "author": "user_001"}
    )
    print(f"✓ 存储记忆: {memory.id}")
    
    # 检索记忆
    retrieved = await storage.retrieve_memories(
        memory_type=MemoryType.SEMANTIC,
        tags=["Python"],
        limit=5
    )
    print(f"✓ 检索到 {len(retrieved)} 条记忆")
    
    # 向量搜索
    similar = await storage.search_similar(
        query_text="编程语言",
        top_k=3,
        min_score=0.7
    )
    print(f"✓ 相似搜索找到 {len(similar)} 条记忆")
    
    await storage.close()


# =============================================================================
# 示例 2: 知识图谱构建和查询
# =============================================================================

async def example_knowledge_graph():
    """知识图谱示例"""
    print("\n=== 示例 2: 知识图谱构建和查询 ===\n")
    
    # 初始化知识图谱服务
    kg_service = KnowledgeGraphService()
    
    # 从文本提取实体和关系
    text = """
    张三在北京大学工作，他是计算机科学教授。
    北京大学位于北京，是中国著名的高等学府。
    张三的研究领域是人工智能和机器学习。
    """
    
    entity_result, relation_result = await kg_service.extract_entities_and_relations(text)
    print(f"✓ 提取 {len(entity_result.entities)} 个实体")
    print(f"  实体: {[e['name'] for e in entity_result.entities]}")
    print(f"✓ 提取 {len(relation_result.relations)} 个关系")
    
    # 创建实体
    entity = await kg_service.create_entity(
        name="深度学习",
        entity_type="CONCEPT",
        description="机器学习的一个分支",
        properties={"field": "AI", "complexity": "high"}
    )
    print(f"✓ 创建实体: {entity['name']} ({entity['id']})")
    
    # 查询图谱
    query_result = await kg_service.query_graph(
        entity_name="北京大学",
        depth=2
    )
    print(f"✓ 图谱查询返回 {len(query_result.nodes)} 个节点")
    
    # 导出图谱
    graph_data = await kg_service.export_to_json()
    print(f"✓ 导出图谱: {len(graph_data['nodes'])} 节点, {len(graph_data['edges'])} 边")


# =============================================================================
# 示例 3: Agent 记忆管理
# =============================================================================

async def example_agent_memory():
    """Agent 记忆管理示例"""
    print("\n=== 示例 3: Agent 记忆管理 ===\n")
    
    # 初始化 Agent 记忆管理器
    agent_memory = AgentMemoryManager()
    
    # 为 Solver Agent 创建记忆空间
    await agent_memory.create_agent_memory_space(
        agent_id="solver_001",
        agent_type="smart_solver",
        session_id="session_001",
        user_id="user_001"
    )
    print("✓ 创建 Agent 记忆空间")
    
    # 存储到工作记忆
    await agent_memory.store_to_working_memory(
        agent_id="solver_001",
        content="用户正在询问关于二次方程的问题",
        importance=0.8
    )
    print("✓ 存储到工作记忆")
    
    # 存储到长期记忆
    await agent_memory.store_to_long_term_memory(
        agent_id="solver_001",
        content="用户偏好详细的数学推导过程",
        category="user_preference",
        importance=0.9
    )
    print("✓ 存储到长期记忆")
    
    # 检索 Agent 记忆
    memories = await agent_memory.get_agent_memory(
        agent_id="solver_001",
        include_working=True,
        include_long_term=True
    )
    print(f"✓ 检索到 {len(memories)} 条 Agent 记忆")
    
    # 在 Agent 间共享记忆
    await agent_memory.share_memory_between_agents(
        source_agent_id="solver_001",
        target_agent_ids=["guide_001", "research_001"],
        memory_filter={"category": "user_preference"}
    )
    print("✓ 共享记忆给其他 Agent")
    
    # 获取记忆统计
    stats = await agent_memory.get_agent_memory_stats("solver_001")
    print(f"✓ Agent 记忆统计: {stats}")


# =============================================================================
# 示例 4: 性能优化 - 缓存和批量处理
# =============================================================================

async def example_performance_optimizations():
    """性能优化示例"""
    print("\n=== 示例 4: 性能优化 ===\n")
    
    # 缓存管理器
    cache_manager = await get_cache_manager()
    print("✓ 初始化缓存管理器")
    
    # 存储到缓存
    await cache_manager.set("key_001", {"data": "value"}, ttl=300)
    
    # 从缓存获取
    cached_value = await cache_manager.get("key_001")
    print(f"✓ 缓存获取: {cached_value}")
    
    # 缓存统计
    cache_stats = await cache_manager.get_stats()
    print(f"✓ 缓存统计: {cache_stats}")
    
    # 批量处理器
    from src.integrations.supermemory.optimizations import BatchProcessor, BatchConfig
    
    batch_config = BatchConfig(
        batch_size=10,
        max_concurrency=5,
        retry_attempts=3
    )
    batch_processor = BatchProcessor(batch_config)
    print("✓ 初始化批量处理器")
    
    # 定义处理函数
    async def process_item(item: Dict) -> Dict:
        await asyncio.sleep(0.1)  # 模拟处理
        return {"processed": True, "id": item["id"]}
    
    # 批量处理
    items = [{"id": f"item_{i}"} for i in range(20)]
    results = await batch_processor.process(items, process_item)
    print(f"✓ 批量处理完成: {len(results)} 项")
    
    # 性能指标
    from src.integrations.supermemory.optimizations import get_metrics_collector
    metrics = get_metrics_collector()
    
    @timed("example_operation")
    async def example_operation():
        await asyncio.sleep(0.5)
        return "done"
    
    await example_operation()
    
    metrics_summary = await metrics.get_summary()
    print(f"✓ 性能指标: {metrics_summary}")


# =============================================================================
# 示例 5: 遗忘机制
# =============================================================================

async def example_forgetting_mechanism():
    """遗忘机制示例"""
    print("\n=== 示例 5: 遗忘机制 ===\n")
    
    from src.integrations.supermemory import (
        MemoryForgettingManager,
        ForgettingConfig,
        ForgettingCurveType
    )
    
    # 配置遗忘曲线
    config = ForgettingConfig(
        curve_type=ForgettingCurveType.EBINGHAUS,
        base_strength=1.0,
        decay_rate=0.1,
        importance_weight=0.5,
        access_weight=0.3
    )
    
    # 初始化遗忘管理器
    forgetting_manager = MemoryForgettingManager(config)
    await forgetting_manager.start(cleanup_interval=3600)
    print("✓ 启动遗忘管理器")
    
    # 注册记忆
    current_time = time.time()
    memories = [
        {
            "id": f"mem_{i:03d}",
            "content": f"记忆内容 {i}",
            "importance": 0.9 if i < 3 else 0.3,
            "created_at": current_time - i * 86400,  # 不同时间
            "access_count": 10 if i < 2 else 0
        }
        for i in range(10)
    ]
    
    for memory in memories:
        forgetting_manager.register_memory(memory["id"], memory)
    print(f"✓ 注册 {len(memories)} 条记忆")
    
    # 获取记忆强度
    for i in [0, 5, 9]:
        strength = forgetting_manager.get_memory_strength(f"mem_{i:03d}")
        print(f"  记忆 mem_{i:03d} 强度: {strength:.2f}")
    
    # 获取复习推荐
    recommendations = forgetting_manager.get_review_recommendations(limit=5)
    print(f"✓ 复习推荐: {len(recommendations)} 条")
    for rec in recommendations[:3]:
        print(f"  - {rec['memory_id']}: 强度={rec['current_strength']:.2f}")
    
    # 访问记忆（增强强度）
    forgetting_manager.access_memory("mem_005")
    print("✓ 访问记忆 mem_005")
    
    # 获取统计
    stats = forgetting_manager.get_stats()
    print(f"✓ 遗忘统计: {stats}")
    
    await forgetting_manager.stop()


# =============================================================================
# 示例 6: 实体链接
# =============================================================================

async def example_entity_linking():
    """实体链接示例"""
    print("\n=== 示例 6: 实体链接 ===\n")
    
    # 初始化实体链接器
    linker = EntityLinker()
    
    # 注册实体
    entities = [
        ("ent_001", "北京大学", "ORGANIZATION", ["北大", "PKU", "Peking University"]),
        ("ent_002", "清华大学", "ORGANIZATION", ["清华", "Tsinghua"]),
        ("ent_003", "张三", "PERSON", ["张先生"]),
    ]
    
    for entity_id, name, entity_type, aliases in entities:
        linker.register_entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            aliases=aliases
        )
    print(f"✓ 注册 {len(entities)} 个实体")
    
    # 链接实体提及
    mentions = [
        ("北大", "他毕业于北大"),
        ("清华大学", None),
        ("张先生", "张先生是教授"),
        ("北京大学", None),
    ]
    
    for mention, context in mentions:
        result = await linker.link_entity(
            mention=mention,
            context=context,
            min_confidence=0.6
        )
        if result:
            print(f"✓ '{mention}' -> {result.canonical_name} (置信度: {result.confidence:.2f})")
        else:
            print(f"✗ '{mention}' -> 未链接")
    
    # 查找共指
    text = "北京大学是一所著名学府，北大位于北京。张三在北大工作。"
    coreferences = linker.find_coreferences(text, ["ent_001", "ent_003"])
    print(f"✓ 找到 {len(coreferences)} 个共指")
    for mention, entity_id, conf in coreferences:
        print(f"  - '{mention}' -> {entity_id} (置信度: {conf:.2f})")
    
    # 获取链接统计
    stats = linker.get_linking_stats()
    print(f"✓ 链接统计: {stats}")


# =============================================================================
# 示例 7: 记忆巩固
# =============================================================================

async def example_memory_consolidation():
    """记忆巩固示例"""
    print("\n=== 示例 7: 记忆巩固 ===\n")
    
    # 初始化记忆巩固器
    consolidator = MemoryConsolidator()
    
    # 准备记忆数据
    current_time = time.time()
    memories = [
        {
            "id": "mem_001",
            "content": "Python 列表使用方括号定义",
            "tags": ["python", "list", "数据结构"],
            "created_at": current_time - 3600,
            "strength": 0.6
        },
        {
            "id": "mem_002",
            "content": "Python 字典使用花括号定义",
            "tags": ["python", "dict", "数据结构"],
            "created_at": current_time - 7200,
            "strength": 0.6
        },
        {
            "id": "mem_003",
            "content": "Python 元组使用圆括号定义",
            "tags": ["python", "tuple", "数据结构"],
            "created_at": current_time - 10800,
            "strength": 0.6
        },
        {
            "id": "mem_004",
            "content": "Python 集合使用 set() 函数定义",
            "tags": ["python", "set", "数据结构"],
            "created_at": current_time - 14400,
            "strength": 0.6
        },
        {
            "id": "mem_005",
            "content": "Python 是动态类型语言",
            "tags": ["python", "类型系统"],
            "created_at": current_time - 18000,
            "strength": 0.7
        },
    ]
    
    print(f"✓ 准备 {len(memories)} 条记忆")
    
    # 执行巩固
    result = await consolidator.consolidate(
        memories,
        min_pattern_support=2,
        min_confidence=0.6
    )
    
    print(f"✓ 巩固完成:")
    print(f"  - 提取模式: {result.patterns_extracted}")
    print(f"  - 巩固记忆: {result.memories_consolidated}")
    print(f"  - 泛化知识: {len(result.new_generalizations)}")
    print(f"  - 处理时间: {result.processing_time:.2f}s")
    
    # 查看提取的模式
    patterns = consolidator.get_patterns()
    print(f"✓ 提取的模式 ({len(patterns)}):")
    for pattern in patterns[:3]:
        print(f"  - {pattern.pattern_type}: {pattern.description} (置信度: {pattern.confidence:.2f})")
    
    # 获取巩固统计
    stats = consolidator.get_consolidation_stats()
    print(f"✓ 巩固统计: {stats}")


# =============================================================================
# 示例 8: 记忆压缩
# =============================================================================

async def example_memory_compression():
    """记忆压缩示例"""
    print("\n=== 示例 8: 记忆压缩 ===\n")
    
    # 初始化记忆压缩器
    compressor = MemoryCompressor()
    
    # 准备重复和冗余的记忆
    current_time = time.time()
    memories = [
        # 重复内容
        {"id": "mem_001", "content": "Python 是一种编程语言", "tags": ["python"]},
        {"id": "mem_002", "content": "Python 是一种编程语言", "tags": ["python"]},
        {"id": "mem_003", "content": "Python 是一种编程语言", "tags": ["python"]},
        
        # 相似内容
        {"id": "mem_004", "content": "Python 列表操作", "tags": ["python", "list"]},
        {"id": "mem_005", "content": "Python 列表方法", "tags": ["python", "list"]},
        
        # 独特内容
        {"id": "mem_006", "content": "Java 是一种编程语言", "tags": ["java"]},
        
        # 低重要性旧记忆
        {"id": "mem_007", "content": "旧的不重要记忆", "tags": ["old"], 
         "importance": 0.1, "created_at": current_time - 86400 * 400, "access_count": 0},
        
        # 高重要性旧记忆
        {"id": "mem_008", "content": "重要的旧记忆", "tags": ["important"], 
         "importance": 0.9, "created_at": current_time - 86400 * 400, "access_count": 0},
    ]
    
    print(f"✓ 原始记忆数量: {len(memories)}")
    
    # 去重压缩
    result_dedup = await compressor.compress_by_deduplication(memories)
    print(f"✓ 去重压缩: {result_dedup.original_count} -> {result_dedup.compressed_count} "
          f"(压缩率: {result_dedup.compression_ratio*100:.1f}%)")
    
    # 合并压缩
    result_merge = await compressor.compress_by_merging(memories, similarity_threshold=0.5)
    print(f"✓ 合并压缩: {result_merge.original_count} -> {result_merge.compressed_count} "
          f"(压缩率: {result_merge.compression_ratio*100:.1f}%)")
    
    # 剪枝压缩
    result_prune = await compressor.compress_by_pruning(
        memories,
        importance_threshold=0.3,
        age_threshold_days=365
    )
    print(f"✓ 剪枝压缩: {result_prune.original_count} -> {result_prune.compressed_count} "
          f"(压缩率: {result_prune.compression_ratio*100:.1f}%)")
    
    # 自动压缩
    result_auto = await compressor.auto_compress(memories, target_ratio=0.5)
    print(f"✓ 自动压缩: {result_auto.original_count} -> {result_auto.compressed_count} "
          f"(压缩率: {result_auto.compression_ratio*100:.1f}%)")
    
    # 压缩统计
    stats = compressor.get_stats()
    print(f"✓ 压缩统计: {stats}")


# =============================================================================
# 主函数：运行所有示例
# =============================================================================

async def main():
    """运行所有示例"""
    print("=" * 60)
    print("SuperMemory 使用示例")
    print("=" * 60)
    
    try:
        # 运行所有示例
        await example_basic_memory_operations()
        await example_knowledge_graph()
        await example_agent_memory()
        await example_performance_optimizations()
        await example_forgetting_mechanism()
        await example_entity_linking()
        await example_memory_consolidation()
        await example_memory_compression()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
