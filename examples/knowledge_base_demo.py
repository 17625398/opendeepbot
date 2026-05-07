"""
知识库功能完整演示

展示 DeepSeekMine 集成到 DeepTutor 的所有知识库功能
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import tempfile
from datetime import datetime

# 导入知识库模块
from src.skills.knowledge_base import (
    # 基础组件
    KnowledgeBaseConfig,
    KnowledgeBaseManager,
    
    # RAG 检索
    RAGPipeline,
    AdaptiveRAGPipeline,
    
    # 分片上传
    ChunkedUploadManager,
    get_chunked_upload_manager,
    
    # Ollama 集成
    get_ollama_manager,
    
    # 系统监控
    get_system_monitor,
    
    # 缓存管理
    get_embedding_cache,
    get_query_cache,
    
    # 文档索引
    DocumentIndexer,
    
    # 批量处理
    get_batch_processor,
    
    # 同步备份
    get_backup_manager,
    get_export_import_manager,
    get_sync_manager,
    
    # 版本控制
    get_version_manager,
    
    # 知识图谱
    get_graph_builder,
    
    # 高级搜索
    get_search_engine,
    FilterOperator,
    
    # 相似度分析
    get_similarity_analyzer,
    
    # 智能标签
    get_tag_manager,
    
    # 推荐系统
    get_recommendation_engine,
    
    # 统计分析
    get_analytics_manager,
    
    # 实用工具
    generate_id,
    format_file_size,
    format_duration,
    ProgressTracker,
    Timer,
)


async def demo_basic_knowledge_base():
    """演示基础知识库功能"""
    print("\n" + "="*60)
    print("演示 1: 基础知识库管理")
    print("="*60)
    
    # 创建配置
    config = KnowledgeBaseConfig(
        vector_store_type="memory",  # 使用内存存储便于演示
        chunk_size=500,
        chunk_overlap=50,
    )
    
    # 初始化管理器
    manager = KnowledgeBaseManager(config)
    await manager.initialize(embedding_provider="mock")
    
    # 创建知识库
    kb = await manager.create_knowledge_base(
        name="演示知识库",
        description="用于演示功能的知识库"
    )
    print(f"✓ 创建知识库: {kb.name} (ID: {kb.kb_id})")
    
    # 列出知识库
    kbs = await manager.list_knowledge_bases()
    print(f"✓ 共有 {len(kbs)} 个知识库")
    
    # 获取统计信息
    stats = await manager.get_stats(kb.kb_id)
    print(f"✓ 知识库统计: {stats}")
    
    return manager, kb


async def demo_document_processing(manager: KnowledgeBaseManager, kb_id: str):
    """演示文档处理"""
    print("\n" + "="*60)
    print("演示 2: 文档处理")
    print("="*60)
    
    # 创建示例文档
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

人工智能的研究领域包括：
1. 机器学习 - 让计算机从数据中学习
2. 自然语言处理 - 让计算机理解和生成人类语言
3. 计算机视觉 - 让计算机"看见"和理解图像
4. 机器人技术 - 让机器人执行复杂任务

深度学习是机器学习的一个子领域，它使用多层神经网络来学习数据的复杂模式。
深度学习的突破使得人工智能在图像识别、语音识别、自然语言处理等领域取得了巨大进展。
""")
        temp_path = f.name
    
    try:
        # 添加文档
        doc = await manager.add_document(
            kb_id=kb_id,
            file_path=temp_path,
            filename="ai_introduction.txt",
            metadata={"category": "technology", "author": "demo"}
        )
        print(f"✓ 添加文档: {doc.filename} (ID: {doc.document_id})")
        
        # 处理文档
        success = await manager.process_document(kb_id, doc.document_id)
        print(f"✓ 文档处理{'成功' if success else '失败'}")
        
        # 获取文档
        retrieved_doc = await manager.get_document(kb_id, doc.document_id)
        print(f"✓ 文档块数: {len(retrieved_doc.chunks)}")
        
        return doc
    finally:
        os.unlink(temp_path)


async def demo_rag_retrieval(manager: KnowledgeBaseManager, kb_id: str):
    """演示 RAG 检索"""
    print("\n" + "="*60)
    print("演示 3: RAG 检索")
    print("="*60)
    
    # 创建 RAG 管道
    rag = RAGPipeline(
        vector_store=manager.vector_store,
        embedding_manager=manager.embedding_manager,
        config=manager.config,
        retriever_type="similarity"
    )
    
    # 执行检索
    result = await rag.retrieve(
        query="什么是深度学习？",
        knowledge_base_id=kb_id,
        top_k=3
    )
    
    print(f"✓ 检索到 {len(result.chunks)} 个文档块")
    print(f"✓ 上下文长度: {len(result.context)} 字符")
    print(f"✓ 检索耗时: {format_duration(result.metadata.get('retrieval_time', 0))}")
    
    return result


async def demo_adaptive_rag(manager: KnowledgeBaseManager, kb_id: str):
    """演示 Adaptive RAG"""
    print("\n" + "="*60)
    print("演示 4: Adaptive RAG 自适应检索")
    print("="*60)
    
    # 创建基础 RAG 管道
    rag = RAGPipeline(
        vector_store=manager.vector_store,
        embedding_manager=manager.embedding_manager,
        config=manager.config,
        retriever_type="similarity"
    )
    
    # 创建 Adaptive RAG 管道
    adaptive_rag = AdaptiveRAGPipeline(
        rag_pipeline=rag,
        config=manager.config
    )
    
    # 执行自适应检索
    result = await adaptive_rag.retrieve(
        query="分析人工智能的优缺点",
        knowledge_base_id=kb_id
    )
    
    print(f"✓ 查询类型: {result.classification.query_type}")
    print(f"✓ 检索策略: {result.strategy}")
    print(f"✓ 迭代次数: {result.iterations}")
    print(f"✓ 执行时间: {format_duration(result.execution_time)}")
    
    return result


async def demo_cache_management():
    """演示缓存管理"""
    print("\n" + "="*60)
    print("演示 5: 缓存管理")
    print("="*60)
    
    # 获取缓存管理器
    embedding_cache = get_embedding_cache()
    query_cache = get_query_cache()
    
    # 模拟缓存操作
    test_key = "test_embedding_key"
    test_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # 存储到缓存
    embedding_cache.set(test_key, test_value)
    print(f"✓ 存储嵌入缓存")
    
    # 从缓存获取
    cached_value = embedding_cache.get(test_key)
    print(f"✓ 获取嵌入缓存: {'成功' if cached_value else '未找到'}")
    
    # 获取缓存统计
    stats = embedding_cache.get_stats()
    print(f"✓ 缓存统计: {stats}")
    
    # 清空缓存
    embedding_cache.clear()
    print(f"✓ 缓存已清空")


async def demo_document_indexing():
    """演示文档索引"""
    print("\n" + "="*60)
    print("演示 6: 文档索引")
    print("="*60)
    
    # 创建索引器
    indexer = DocumentIndexer()
    
    # 添加文档到索引
    doc_id = generate_id("doc")
    content = "人工智能是计算机科学的一个重要分支，它研究如何让计算机模拟人类智能。"
    
    await indexer.index_document(doc_id, "示例文档", content)
    print(f"✓ 添加文档到索引: {doc_id}")
    
    # 搜索文档
    search_response = await indexer.search("人工智能")
    results = search_response.get('results', [])
    print(f"✓ 搜索结果: 找到 {len(results)} 个文档")
    
    for result in results[:3]:  # 只显示前3个
        if hasattr(result, 'document_id'):
            print(f"  - 文档 {result.document_id}: 得分 {result.score:.4f}")
        else:
            print(f"  - 结果: {result}")
    
    # 获取搜索建议
    suggestions = indexer.get_suggestions("人工")
    print(f"✓ 搜索建议: {suggestions}")


async def demo_similarity_analysis():
    """演示相似度分析"""
    print("\n" + "="*60)
    print("演示 7: 文档相似度分析")
    print("="*60)
    
    # 获取相似度分析器
    analyzer = get_similarity_analyzer()
    
    # 准备文档
    docs = [
        ("doc1", "人工智能是计算机科学的一个分支"),
        ("doc2", "机器学习是人工智能的子领域"),
        ("doc3", "深度学习使用神经网络进行学习"),
        ("doc4", "今天的天气真好，适合去公园散步"),
    ]
    
    # 分析文档相似度
    target_doc_id, target_content = docs[0]
    candidate_docs = docs[1:]  # 其他文档作为候选
    
    results = analyzer.analyze_document_similarity(
        target_doc_id=target_doc_id,
        target_content=target_content,
        candidate_docs=candidate_docs,
        top_k=2
    )
    
    print(f"✓ 分析了 {len(docs)} 个文档")
    print(f"✓ 与 doc1 最相似的文档:")
    for result in results:
        print(f"  - {result.doc_id2}: 相似度 {result.similarity_score:.4f} ({result.method})")
    
    # 使用 MinHashLSH 检测重复（需要较长文本）
    print(f"✓ 相似度分析完成")


async def demo_smart_tagging():
    """演示智能标签"""
    print("\n" + "="*60)
    print("演示 8: 智能标签系统")
    print("="*60)
    
    # 获取标签管理器
    tag_manager = get_tag_manager()
    
    # 创建标签
    tag1 = tag_manager.create_tag(
        name="人工智能",
        color="#1890ff",
        description="AI 相关文档"
    )
    tag2 = tag_manager.create_tag(
        name="机器学习",
        color="#52c41a",
        description="ML 相关文档"
    )
    print(f"✓ 创建标签: {tag1.name}, {tag2.name}")
    
    # 为文档添加标签
    doc_id = generate_id("doc")
    tag_manager.add_tag_to_document(doc_id, tag1.tag_id)
    tag_manager.add_tag_to_document(doc_id, tag2.tag_id)
    print(f"✓ 为文档添加标签")
    
    # 获取文档标签
    doc_tags = tag_manager.get_document_tags(doc_id)
    tag_names = [t.name for t in doc_tags]
    print(f"✓ 文档标签: {tag_names}")
    
    # 按标签搜索文档
    results = tag_manager.get_tagged_documents(tag1.tag_id)
    print(f"✓ 标签搜索: 找到 {len(results)} 个文档")


async def demo_recommendation():
    """演示推荐系统"""
    print("\n" + "="*60)
    print("演示 9: 文档推荐系统")
    print("="*60)
    
    # 获取推荐引擎
    engine = get_recommendation_engine()
    
    # 添加用户行为
    user_id = "user_001"
    doc_id = generate_id("doc")
    
    engine.record_interaction(user_id, doc_id, "view")
    engine.record_interaction(user_id, doc_id, "like")
    print(f"✓ 添加用户行为: view, like")
    
    # 获取推荐
    recommendations = engine.get_recommendations(
        user_id=user_id,
        top_k=5
    )
    print(f"✓ 为用户推荐 {len(recommendations)} 个文档")
    
    # 获取相似文档
    similar = engine.get_similar_documents(doc_id, top_k=3)
    print(f"✓ 相似文档推荐: {len(similar)} 个")


async def demo_analytics():
    """演示统计分析"""
    print("\n" + "="*60)
    print("演示 10: 文档统计分析")
    print("="*60)
    
    # 获取分析管理器
    analytics = get_analytics_manager()
    
    # 记录事件
    kb_id = generate_id("kb")
    doc_id = generate_id("doc")
    analytics.record_view(doc_id, kb_id)
    analytics.record_download(doc_id, kb_id)
    print(f"✓ 记录分析事件")
    
    # 获取知识库统计
    stats = analytics.get_kb_stats(kb_id)
    if stats:
        print(f"✓ 知识库统计:")
        print(f"  - 文档总数: {stats.total_documents}")
        print(f"  - 总大小: {format_file_size(stats.total_storage_bytes)}")
        print(f"  - 总块数: {stats.total_chunks}")
    else:
        print(f"✓ 暂无知识库统计")


async def demo_system_monitor():
    """演示系统监控"""
    print("\n" + "="*60)
    print("演示 11: 系统监控")
    print("="*60)
    
    # 获取监控器
    monitor = get_system_monitor(interval=5)
    
    # 获取当前统计
    stats = monitor.get_last_stats()
    if stats:
        print(f"✓ CPU 使用率: {stats.cpu.usage_percent}%")
        print(f"✓ 内存使用率: {stats.memory.usage_percent}%")
        print(f"✓ 内存使用: {format_file_size(stats.memory.used_bytes)}")
        print(f"✓ 磁盘使用: {format_file_size(stats.disk.used_bytes)}")
    else:
        print("✓ 暂无监控数据")


async def demo_utils():
    """演示实用工具"""
    print("\n" + "="*60)
    print("演示 12: 实用工具函数")
    print("="*60)
    
    # ID 生成
    id1 = generate_id("kb")
    id2 = generate_id()
    print(f"✓ 生成 ID: {id1[:20]}..., {id2[:20]}...")
    
    # 文件大小格式化
    sizes = [512, 1024, 1024*1024, 1024*1024*1024]
    for size in sizes:
        print(f"✓ {size} bytes = {format_file_size(size)}")
    
    # 持续时间格式化
    durations = [30, 120, 3600, 7200]
    for seconds in durations:
        print(f"✓ {seconds} 秒 = {format_duration(seconds)}")
    
    # 进度跟踪器
    tracker = ProgressTracker(total=100, description="处理文档")
    for i in range(0, 101, 25):
        tracker.current = i
        tracker._print_progress()
    tracker.finish()
    
    # 计时器
    with Timer("示例操作"):
        await asyncio.sleep(0.1)


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("DeepSeekMine 知识库功能演示")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 基础知识库
        manager, kb = await demo_basic_knowledge_base()
        
        # 2. 文档处理
        doc = await demo_document_processing(manager, kb.kb_id)
        
        # 3. RAG 检索
        await demo_rag_retrieval(manager, kb.kb_id)
        
        # 4. Adaptive RAG
        await demo_adaptive_rag(manager, kb.kb_id)
        
        # 5. 缓存管理
        await demo_cache_management()
        
        # 6. 文档索引
        await demo_document_indexing()
        
        # 7. 相似度分析
        await demo_similarity_analysis()
        
        # 8. 智能标签
        await demo_smart_tagging()
        
        # 9. 推荐系统
        await demo_recommendation()
        
        # 10. 统计分析
        await demo_analytics()
        
        # 11. 系统监控
        await demo_system_monitor()
        
        # 12. 实用工具
        await demo_utils()
        
        print("\n" + "="*60)
        print("所有演示完成！")
        print("="*60)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n✗ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
