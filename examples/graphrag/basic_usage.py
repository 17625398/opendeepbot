"""
GraphRAG 基础使用示例
展示如何构建知识图谱并进行查询
"""

import asyncio
from src.agents.skills.graphrag import GraphRAG


async def basic_example():
    """基础示例：处理文档并查询"""
    
    # 初始化 GraphRAG
    graphrag = GraphRAG()
    
    print("=" * 60)
    print("GraphRAG 基础使用示例")
    print("=" * 60)
    
    # 示例文档
    documents = [
        {
            "title": "苹果公司介绍",
            "content": """
            Apple Inc. 是一家美国跨国科技公司，总部位于加利福尼亚州库比蒂诺。
            公司由史蒂夫·乔布斯、史蒂夫·沃兹尼亚克和罗纳德·韦恩于1976年创立。
            Apple 设计、开发和销售消费电子产品、计算机软件和在线服务。
            其主要产品包括 iPhone、iPad、Mac、Apple Watch 和 Apple TV。
            蒂姆·库克自2011年起担任公司CEO。
            """
        },
        {
            "title": "微软公司介绍",
            "content": """
            Microsoft Corporation 是一家美国跨国科技公司，总部位于华盛顿州雷德蒙德。
            公司由比尔·盖茨和保罗·艾伦于1975年创立。
            Microsoft 以开发、制造、许可和支持计算机软件、消费电子产品和个人电脑而闻名。
            其主要产品包括 Windows 操作系统、Office 办公套件和 Azure 云服务。
            萨提亚·纳德拉自2014年起担任公司CEO。
            """
        }
    ]
    
    # 处理文档
    print("\n1. 处理文档并构建知识图谱...")
    for doc in documents:
        result = await graphrag.process_document(
            content=doc["content"],
            title=doc["title"]
        )
        print(f"  ✓ {doc['title']}: {result['entities_count']} 实体, {result['relationships_count']} 关系")
    
    # 获取统计信息
    print("\n2. 知识图谱统计:")
    stats = graphrag.get_statistics()
    print(f"  - 文档数: {stats['documents']['total_chunks']}")
    print(f"  - 实体数: {stats['knowledge_graph']['total_nodes']}")
    print(f"  - 关系数: {stats['knowledge_graph']['total_edges']}")
    
    # 执行查询
    print("\n3. 执行查询:")
    queries = [
        "谁创立了 Apple?",
        "Microsoft 的总部在哪里?",
        "谁是 Apple 的 CEO?"
    ]
    
    for query_text in queries:
        print(f"\n  查询: {query_text}")
        result = await graphrag.query(query_text, mode="hybrid")
        print(f"  回答: {result.answer[:100]}..." if len(result.answer) > 100 else f"  回答: {result.answer}")
        print(f"  找到 {len(result.entities)} 个实体, {len(result.relationships)} 个关系")
    
    # 可视化
    print("\n4. 导出可视化数据:")
    viz_data = graphrag.visualize(format="d3", max_nodes=50)
    print(f"  ✓ 导出 {len(viz_data['nodes'])} 个节点, {len(viz_data['links'])} 条边")
    
    # 保存到文件
    print("\n5. 保存知识图谱:")
    from src.agents.skills.graphrag import GraphPersistence
    
    persistence = GraphPersistence(storage_dir="./example_storage")
    saved_files = persistence.save_all(
        knowledge_graph=graphrag.knowledge_graph,
        document_store=graphrag.document_store,
        vector_store=graphrag.vector_store,
        name="example_graph"
    )
    print(f"  ✓ 图谱保存到: {saved_files['graph']}")
    print(f"  ✓ 文档保存到: {saved_files['documents']}")
    
    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(basic_example())
