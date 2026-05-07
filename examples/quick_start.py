"""
知识库快速入门示例

展示如何使用 DeepSeekMine 集成的知识库功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.skills.knowledge_base import (
    KnowledgeBaseConfig,
    KnowledgeBaseManager,
    RAGPipeline,
    AdaptiveRAGPipeline,
)


async def quick_start():
    """快速入门：创建知识库、添加文档、进行 RAG 对话"""
    
    print("=" * 60)
    print("🚀 知识库快速入门")
    print("=" * 60)
    
    # 1. 配置知识库
    print("\n📋 步骤 1: 配置知识库")
    config = KnowledgeBaseConfig(
        vector_store_type="memory",  # 使用内存存储，便于测试
        chunk_size=500,
        chunk_overlap=50,
    )
    print("✓ 配置完成")
    
    # 2. 初始化管理器
    print("\n🔧 步骤 2: 初始化知识库管理器")
    manager = KnowledgeBaseManager(config)
    await manager.initialize(embedding_provider="mock")
    print("✓ 初始化完成")
    
    # 3. 创建知识库
    print("\n📚 步骤 3: 创建知识库")
    kb = await manager.create_knowledge_base(
        name="AI 学习资料",
        description="人工智能相关的学习文档",
    )
    print(f"✓ 知识库创建成功: {kb.name} (ID: {kb.kb_id})")
    
    # 4. 添加文档（模拟）
    print("\n📄 步骤 4: 添加文档到知识库")
    # 创建临时文档
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。

机器学习是 AI 的核心技术之一，它使计算机能够从数据中学习，而无需明确编程。

深度学习是机器学习的一个子领域，使用多层神经网络来模拟人类大脑的工作方式。

神经网络由许多相互连接的节点（神经元）组成，可以识别数据中的复杂模式。
""")
        temp_path = f.name
    
    try:
        doc = await manager.add_document(
            kb_id=kb.kb_id,
            file_path=temp_path,
            filename="ai_introduction.txt",
            metadata={"category": "AI基础", "author": "系统"},
        )
        print(f"✓ 文档添加成功: {doc.filename}")
        
        # 处理文档
        await manager.process_document(kb.kb_id, doc.document_id)
        print("✓ 文档处理完成")
    finally:
        os.unlink(temp_path)
    
    # 5. 执行 RAG 检索
    print("\n🔍 步骤 5: 执行 RAG 检索")
    rag = RAGPipeline(
        vector_store=manager.vector_store,
        embedding_manager=manager.embedding_manager,
        config=config,
    )
    
    result = await rag.retrieve(
        query="什么是深度学习？",
        knowledge_base_id=kb.kb_id,
        top_k=3,
    )
    
    print(f"✓ 检索到 {len(result.chunks)} 个相关片段")
    print(f"\n检索结果:")
    for i, chunk in enumerate(result.chunks, 1):
        print(f"  {i}. {chunk.content[:100]}...")
    
    # 6. 使用 Adaptive RAG
    print("\n🤖 步骤 6: 使用 Adaptive RAG 进行智能检索")
    adaptive_rag = AdaptiveRAGPipeline(
        rag_pipeline=rag,
        config=config,
    )
    
    adaptive_result = await adaptive_rag.retrieve(
        query="分析神经网络和深度学习的关系",
        knowledge_base_id=kb.kb_id,
    )
    
    print(f"✓ Adaptive RAG 完成")
    print(f"  - 查询类型: {adaptive_result.classification.query_type}")
    print(f"  - 检索策略: {adaptive_result.strategy}")
    print(f"  - 迭代次数: {adaptive_result.iterations}")
    
    # 7. 获取统计信息
    print("\n📊 步骤 7: 查看知识库统计")
    stats = await manager.get_stats(kb.kb_id)
    print(f"✓ 统计信息:")
    print(f"  - 文档总数: {stats.get('total_documents', 0)}")
    print(f"  - 总块数: {stats.get('total_chunks', 0)}")
    
    print("\n" + "=" * 60)
    print("✅ 快速入门完成！")
    print("=" * 60)
    print("\n下一步建议:")
    print("  1. 尝试添加更多文档")
    print("  2. 使用前端界面进行管理")
    print("  3. 配置 OpenAI API 以获得更好的嵌入效果")
    print("  4. 使用 ChromaDB 进行持久化存储")


async def advanced_usage():
    """高级用法示例"""
    
    print("\n" + "=" * 60)
    print("🎯 高级用法示例")
    print("=" * 60)
    
    from src.skills.knowledge_base import (
        get_embedding_cache,
        get_query_cache,
        get_tag_manager,
        get_analytics_manager,
    )
    
    # 缓存使用
    print("\n💾 缓存管理")
    embedding_cache = get_embedding_cache()
    query_cache = get_query_cache()
    
    # 存储嵌入向量
    embedding_cache.set("query_hash", [0.1, 0.2, 0.3])
    print("✓ 嵌入缓存存储成功")
    
    # 存储查询结果
    query_cache.set("search_query", {"results": [...]})
    print("✓ 查询缓存存储成功")
    
    # 标签系统
    print("\n🏷️ 标签管理")
    tag_manager = get_tag_manager()
    
    tag = tag_manager.create_tag(
        name="重要文档",
        color="#ff4d4f",
        description="标记重要的文档",
    )
    print(f"✓ 标签创建成功: {tag.name}")
    
    # 分析统计
    print("\n📈 分析统计")
    analytics = get_analytics_manager()
    
    # 记录事件
    analytics.record_view("doc_001", "kb_001")
    analytics.record_download("doc_001", "kb_001")
    print("✓ 事件记录成功")
    
    print("\n高级功能演示完成！")


async def main():
    """主函数"""
    try:
        await quick_start()
        await advanced_usage()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
