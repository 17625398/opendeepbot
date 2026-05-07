"""
知识库完整功能示例

展示知识库模块的所有功能集成使用
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.skills.knowledge_base import (
    # 基础组件
    KnowledgeBaseManager,
    KnowledgeBaseConfig,
    DocumentType,
    
    # 缓存
    get_embedding_cache,
    get_query_cache,
    
    # 索引
    DocumentIndexer,
    get_version_manager,
    VersionAction,
    
    # 批量处理
    get_batch_processor,
    
    # 同步备份
    get_backup_manager,
    get_export_import_manager,
    
    # 知识图谱
    get_graph_builder,
    
    # 搜索过滤
    get_search_engine,
    SearchQuery,
    FilterCondition,
    FilterOperator,
    
    # 相似度分析
    get_similarity_analyzer,
    
    # 标签系统
    get_tag_manager,
    
    # 推荐系统
    get_recommendation_engine,
    
    # 统计分析
    get_analytics_manager,
)


async def demo_complete_workflow():
    """演示完整工作流程"""
    print("\n" + "=" * 70)
    print("知识库完整功能示例")
    print("=" * 70)
    
    # 1. 初始化知识库管理器
    print("\n📚 1. 初始化知识库管理器")
    print("-" * 50)
    
    config = KnowledgeBaseConfig(
        vector_store_path="./kb_data",
        vector_store_type="memory",  # 使用内存存储，无需安装 chromadb
        chunk_size=500,
        chunk_overlap=50
    )
    
    kb_manager = KnowledgeBaseManager(config)
    print(f"✓ 知识库管理器初始化完成")
    print(f"  - 向量存储路径: {config.vector_store_path}")
    print(f"  - 嵌入模型: {config.embedding_model}")
    print(f"  - 向量存储: {config.vector_store_type} (内存模式)")
    
    # 2. 创建知识库
    print("\n📁 2. 创建知识库")
    print("-" * 50)
    
    kb = await kb_manager.create_knowledge_base(
        name="技术文档库",
        description="包含编程、AI、云计算等技术文档",
        owner_id="team",
        is_public=True
    )
    print(f"✓ 知识库创建成功")
    print(f"  - ID: {kb.kb_id}")
    print(f"  - 名称: {kb.name}")
    print(f"  - 描述: {kb.description}")
    
    # 3. 添加文档
    print("\n📝 3. 添加文档到知识库")
    print("-" * 50)
    
    documents = [
        {
            "title": "Python 编程入门",
            "content": """
Python 是一种高级编程语言，由 Guido van Rossum 创建。
它强调代码的可读性和简洁的语法，使用缩进来表示代码块。
Python 支持多种编程范式，包括面向对象、命令式、函数式和结构化编程。

主要特点：
1. 简单易学
2. 丰富的标准库
3. 跨平台
4. 强大的社区支持

Python 广泛应用于 Web 开发、数据分析、人工智能、科学计算等领域。
            """.strip(),
            "doc_type": "text"
        },
        {
            "title": "机器学习基础",
            "content": """
机器学习是人工智能的一个分支，使用统计方法让计算机从数据中学习。
深度学习是机器学习的一个子领域，使用多层神经网络。

常见算法：
- 监督学习：线性回归、决策树、支持向量机
- 无监督学习：聚类、降维
- 强化学习：Q-learning、策略梯度

应用场景：
- 图像识别
- 自然语言处理
- 推荐系统
            """.strip(),
            "doc_type": "text"
        },
        {
            "title": "云计算概述",
            "content": """
云计算是通过互联网提供计算服务的模式，包括服务器、存储、数据库、网络、软件等。

服务模型：
1. IaaS (基础设施即服务) - 如 AWS EC2, Azure VM
2. PaaS (平台即服务) - 如 Google App Engine
3. SaaS (软件即服务) - 如 Office 365, Salesforce

优势：
- 成本效益
- 可扩展性
- 灵活性
- 灾难恢复
            """.strip(),
            "doc_type": "text"
        }
    ]
    
    kb_id = kb.kb_id  # 使用实际创建的知识库ID
    
    import tempfile
    import os
    
    added_docs = []
    for i, doc_data in enumerate(documents):
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(doc_data["content"])
            temp_path = f.name
        
        try:
            doc = await kb_manager.add_document(
                kb_id=kb_id,
                file_path=temp_path,
                filename=f"{doc_data['title']}.txt",
                metadata={
                    "author": "system",
                    "created": datetime.now().isoformat(),
                    "title": doc_data["title"]
                }
            )
            if doc:
                added_docs.append(doc)
                print(f"✓ 添加文档: {doc.filename} (ID: {doc.document_id})")
        finally:
            # 清理临时文件
            os.unlink(temp_path)
    
    # 4. 自动标签
    print("\n🏷️  4. 自动为文档打标签")
    print("-" * 50)
    
    tag_manager = get_tag_manager("./tags")
    
    for doc in added_docs:
        # 从 metadata 获取标题，或使用 filename
        doc_title = doc.metadata.get('title', doc.filename)
        doc_tags = tag_manager.auto_tag_document(
            doc_id=doc.document_id,
            kb_id=kb_id,
            title=doc_title,
            content=doc.content,
            doc_type=doc.file_type.value
        )
        tags = tag_manager.get_document_tags(doc.document_id)
        tag_names = [t.name for t in tags]
        print(f"✓ {doc_title}: {', '.join(tag_names)}")
    
    # 5. 内容分析
    print("\n📊 5. 分析文档内容")
    print("-" * 50)
    
    analytics = get_analytics_manager("./analytics")
    
    for doc in added_docs:
        analysis = analytics.analyze_document(doc.document_id, doc.content)
        doc_title = doc.metadata.get('title', doc.filename)
        print(f"\n  {doc_title}:")
        print(f"    - 字数: {analysis.word_count}")
        print(f"    - 可读性: {analysis.readability_score:.1f}/100")
        print(f"    - 语言: {analysis.language}")
        print(f"    - 关键词: {', '.join([k for k, _ in analysis.top_keywords[:3]])}")
        
        # 记录查看
        analytics.record_view(doc.document_id, kb_id)
    
    # 6. 搜索测试
    print("\n🔍 6. 测试搜索功能")
    print("-" * 50)
    
    search_queries = ["Python 编程", "机器学习算法", "云计算服务"]
    
    for query in search_queries:
        print(f"\n  查询: '{query}'")
        results = await kb_manager.search(kb_id, query, top_k=2)
        for i, result in enumerate(results, 1):
            # result 是 SearchResult 对象，包含 chunk 和 score
            chunk_content = result.chunk.content[:50] + "..." if len(result.chunk.content) > 50 else result.chunk.content
            print(f"    {i}. 分块: {chunk_content} (相似度: {result.score:.3f})")
    
    # 7. 相似度分析
    print("\n🔄 7. 文档相似度分析")
    print("-" * 50)
    
    similarity_analyzer = get_similarity_analyzer()
    
    # 分析第一个文档与其他文档的相似度
    target_doc = added_docs[0]
    candidate_docs = [(d.document_id, d.content) for d in added_docs[1:]]
    
    similar_results = similarity_analyzer.analyze_document_similarity(
        target_doc_id=target_doc.document_id,
        target_content=target_doc.content,
        candidate_docs=candidate_docs,
        top_k=2
    )
    
    target_title = target_doc.metadata.get('title', target_doc.filename)
    print(f"\n  与 '{target_title}' 相似的文档:")
    for result in similar_results:
        doc = next((d for d in added_docs if d.document_id == result.doc_id2), None)
        if doc:
            doc_title = doc.metadata.get('title', doc.filename)
            print(f"    - {doc_title}: {result.similarity_score:.2f}")
            print(f"      方法: {result.method}")
            if result.common_terms:
                print(f"      共同词: {', '.join(result.common_terms[:5])}")
    
    # 8. 知识图谱
    print("\n🕸️  8. 构建知识图谱")
    print("-" * 50)
    
    graph_builder = get_graph_builder()
    
    for doc in added_docs:
        doc_title = doc.metadata.get('title', doc.filename)
        graph = await graph_builder.build_from_document(
            graph_id=f"graph_{doc.document_id}",
            kb_id=kb_id,
            doc_id=doc.document_id,
            title=doc_title,
            content=doc.content
        )
        print(f"✓ {doc_title}: {len(graph.entities)} 实体, {len(graph.relations)} 关系")
    
    # 9. 推荐系统
    print("\n🎯 9. 测试推荐系统")
    print("-" * 50)
    
    recommender = get_recommendation_engine("./recommendations")
    
    # 设置文档特征
    for i, doc in enumerate(added_docs):
        tags = [t.name for t in tag_manager.get_document_tags(doc.document_id)]
        recommender.update_doc_features(
            doc_id=doc.document_id,
            tags=tags,
            category="technology",
            popularity=100 - i * 20,
            recency=0.9,
            quality=0.85
        )
    
    # 记录用户交互
    recommender.record_interaction("user_001", added_docs[0].document_id, "view")
    recommender.record_interaction("user_001", added_docs[0].document_id, "like")
    
    # 获取推荐
    recommendations = recommender.get_recommendations("user_001", top_k=3)
    
    print("\n  为用户 user_001 推荐:")
    for rec in recommendations:
        doc = next((d for d in added_docs if d.document_id == rec.doc_id), None)
        if doc:
            doc_title = doc.metadata.get('title', doc.filename)
            print(f"    - {doc_title}: {rec.score:.2f}")
            print(f"      原因: {rec.reason}")
    
    # 10. 统计分析
    print("\n📈 10. 统计分析")
    print("-" * 50)
    
    # 更新知识库统计
    analytics.update_kb_stats(
        kb_id=kb_id,
        total_documents=len(added_docs),
        document_types={"text": len(added_docs)}
    )
    
    # 获取统计
    kb_summary = analytics.get_kb_summary(kb_id)
    global_stats = analytics.get_global_stats()
    
    print(f"\n  知识库统计:")
    print(f"    - 文档总数: {kb_summary.get('total_documents', 0)}")
    print(f"    - 总浏览量: {kb_summary.get('total_views', 0)}")
    print(f"    - 总下载量: {kb_summary.get('total_downloads', 0)}")
    
    print(f"\n  全局统计:")
    print(f"    - 知识库数量: {global_stats.get('total_knowledge_bases', 0)}")
    print(f"    - 文档总数: {global_stats.get('total_documents', 0)}")
    
    # 11. 备份
    print("\n💾 11. 创建备份")
    print("-" * 50)
    
    backup_manager = get_backup_manager("./backups")
    
    backup_metadata = await backup_manager.create_backup(
        kb_manager=kb_manager,
        name="tech_docs_初始备份",
        kb_ids=[kb_id],
        description="技术文档库初始状态备份"
    )
    
    print(f"✓ 备份创建成功")
    print(f"  - 备份ID: {backup_metadata.backup_id}")
    print(f"  - 文档数: {backup_metadata.document_count}")
    print(f"  - 大小: {backup_metadata.size_bytes / 1024:.1f} KB")
    
    # 12. 导出
    print("\n📤 12. 导出知识库")
    print("-" * 50)
    
    export_manager = get_export_import_manager()
    
    export_path = await export_manager.export_knowledge_base(
        kb_manager=kb_manager,
        kb_id=kb_id,
        format="markdown",
        include_chunks=False
    )
    
    print(f"✓ 导出成功: {export_path}")
    
    # 13. 生成报告
    print("\n📋 13. 生成分析报告")
    print("-" * 50)
    
    report = analytics.generate_report(kb_id=kb_id)
    
    print(f"✓ 报告生成完成")
    print(f"  - 生成时间: {report.get('generated_at', 'N/A')}")
    print(f"  - 热门文档数: {len(report.get('popular_documents', []))}")
    print(f"  - 趋势文档数: {len(report.get('trending_documents', []))}")
    
    print("\n" + "=" * 70)
    print("✅ 所有功能演示完成!")
    print("=" * 70)
    
    # 清理（可选）
    print("\n🧹 清理测试数据...")
    # await kb_manager.delete_knowledge_base(kb_id)
    # print("✓ 测试知识库已删除")


async def main():
    """主函数"""
    try:
        await demo_complete_workflow()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
