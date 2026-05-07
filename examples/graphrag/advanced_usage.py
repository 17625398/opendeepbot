"""
GraphRAG 高级使用示例
展示 PDF 处理、向量检索、可视化等高级功能
"""

import asyncio
from src.agents.skills.graphrag import GraphRAG, QueryMode


async def pdf_processing_example():
    """PDF 处理示例"""
    print("\n" + "=" * 60)
    print("PDF 处理示例")
    print("=" * 60)
    
    graphrag = GraphRAG()
    
    # 处理 PDF 文件
    pdf_path = "sample.pdf"  # 替换为实际 PDF 路径
    
    print(f"\n处理 PDF: {pdf_path}")
    try:
        result = await graphrag.process_pdf(
            file_path=pdf_path,
            filename="示例文档"
        )
        
        print(f"  ✓ 页数: {result['pdf_info']['total_pages']}")
        print(f"  ✓ 文本长度: {result['pdf_info']['extracted_text_length']}")
        print(f"  ✓ 提取实体: {result['entities_count']}")
        print(f"  ✓ 视觉实体: {result['visual_entities_count']}")
    except Exception as e:
        print(f"  ✗ PDF 处理失败: {e}")
        print("  提示: 请确保 PDF 文件存在")


async def vector_search_example():
    """向量检索示例"""
    print("\n" + "=" * 60)
    print("向量检索示例")
    print("=" * 60)
    
    graphrag = GraphRAG()
    
    # 添加文档到向量存储
    texts = [
        "Python 是一种高级编程语言",
        "JavaScript 用于网页开发",
        "机器学习是人工智能的一个分支",
        "深度学习使用神经网络",
        "Python 在数据科学中很流行"
    ]
    
    print("\n添加文本到向量存储...")
    embeddings = await graphrag.add_to_vector_store(texts)
    print(f"  ✓ 添加了 {len(embeddings)} 个文本")
    
    # 向量搜索
    queries = [
        "编程语言",
        "人工智能",
        "网页开发"
    ]
    
    print("\n执行向量搜索:")
    for query in queries:
        results = await graphrag.vector_search(query, top_k=2)
        print(f"\n  查询: '{query}'")
        for emb, score in results:
            print(f"    - {emb.text[:30]}... (相似度: {score:.3f})")


async def query_modes_example():
    """不同查询模式示例"""
    print("\n" + "=" * 60)
    print("查询模式对比示例")
    print("=" * 60)
    
    graphrag = GraphRAG()
    
    # 准备数据
    content = """
    Tesla Inc. 由 Elon Musk 于2003年创立。
    公司总部位于美国德克萨斯州奥斯汀。
    Tesla 主要生产电动汽车，包括 Model S、Model 3、Model X 和 Model Y。
    公司还在开发自动驾驶技术和能源存储解决方案。
    """
    
    print("\n准备知识图谱...")
    await graphrag.process_document(content, "Tesla 介绍")
    
    query = "Tesla 生产什么产品?"
    
    print(f"\n查询: {query}")
    print("\n不同模式的回答:")
    
    modes = [
        ("naive", "朴素模式"),
        ("local", "本地模式"),
        ("global", "全局模式"),
        ("hybrid", "混合模式")
    ]
    
    for mode, name in modes:
        result = await graphrag.query(query, mode=mode)
        print(f"\n  {name}:")
        print(f"    实体: {len(result.entities)}")
        print(f"    关系: {len(result.relationships)}")
        print(f"    时间: {result.processing_time:.3f}s")


async def visualization_example():
    """可视化示例"""
    print("\n" + "=" * 60)
    print("可视化导出示例")
    print("=" * 60)
    
    graphrag = GraphRAG()
    
    # 构建示例图谱
    content = """
    Google 由 Larry Page 和 Sergey Brin 创立。
    Google 开发了 Android 操作系统。
    Android 运行在智能手机上。
    Google 的总部在 Mountain View。
    """
    
    print("\n构建知识图谱...")
    await graphrag.process_document(content)
    
    # 导出不同格式
    formats = [
        ("d3", "D3.js"),
        ("visjs", "Vis.js"),
        ("cytoscape", "Cytoscape.js"),
        ("graphviz", "Graphviz DOT")
    ]
    
    print("\n导出可视化格式:")
    for fmt, name in formats:
        try:
            data = graphrag.visualize(format=fmt, max_nodes=20)
            if fmt == "graphviz":
                print(f"  ✓ {name}: {len(data)} 字符")
            else:
                print(f"  ✓ {name}: {len(data.get('nodes', []))} 节点")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    
    # 生成 HTML
    print("\n生成 HTML 可视化页面...")
    html = graphrag.visualize(format="html", library="visjs")
    
    output_file = "knowledge_graph.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ HTML 页面已保存到: {output_file}")


async def incremental_update_example():
    """增量更新示例"""
    print("\n" + "=" * 60)
    print("增量更新示例")
    print("=" * 60)
    
    from src.agents.skills.graphrag import Entity, EntityType, Relationship, RelationType
    
    graphrag = GraphRAG()
    
    # 初始数据
    print("\n1. 添加初始数据...")
    content1 = "OpenAI 由 Sam Altman 领导。"
    result1 = await graphrag.process_document(content1, "Doc 1")
    print(f"  ✓ 实体: {result1['entities_count']}, 关系: {result1['relationships_count']}")
    
    # 增量更新
    print("\n2. 增量更新...")
    new_entities = [
        Entity(name="OpenAI", type=EntityType.ORGANIZATION, description="AI research company"),
        Entity(name="ChatGPT", type=EntityType.PRODUCT, description="AI chatbot")
    ]
    
    new_relationships = [
        Relationship(
            source="OpenAI",
            target="ChatGPT",
            relation_type=RelationType.DEVELOPS,
            description="OpenAI develops ChatGPT"
        )
    ]
    
    stats = graphrag.knowledge_graph.incremental_update(
        new_entities, new_relationships, "doc2"
    )
    
    print(f"  ✓ 新增节点: {stats['added_nodes']}")
    print(f"  ✓ 更新节点: {stats['updated_nodes']}")
    print(f"  ✓ 新增边: {stats['added_edges']}")
    print(f"  ✓ 总节点: {stats['total_nodes']}")


async def persistence_example():
    """持久化示例"""
    print("\n" + "=" * 60)
    print("持久化存储示例")
    print("=" * 60)
    
    from src.agents.skills.graphrag import GraphPersistence
    
    graphrag = GraphRAG()
    
    # 构建图谱
    print("\n1. 构建知识图谱...")
    content = "Amazon 由 Jeff Bezos 创立，总部位于 Seattle。"
    await graphrag.process_document(content)
    
    # 保存
    print("\n2. 保存到文件...")
    persistence = GraphPersistence(storage_dir="./example_storage")
    
    saved = persistence.save_all(
        graphrag.knowledge_graph,
        graphrag.document_store,
        graphrag.vector_store,
        name="amazon_graph"
    )
    
    for key, path in saved.items():
        print(f"  ✓ {key}: {path}")
    
    # 查看存储信息
    print("\n3. 存储信息:")
    info = persistence.get_storage_info("amazon_graph")
    print(f"  - 备份数量: {info['backups']}")
    for file_type, file_info in info['files'].items():
        print(f"  - {file_type}: {file_info['size']} bytes")
    
    # 加载
    print("\n4. 从文件加载...")
    new_graphrag = GraphRAG()
    loaded = persistence.load_all(
        new_graphrag.knowledge_graph,
        new_graphrag.document_store,
        new_graphrag.vector_store,
        name="amazon_graph"
    )
    
    for key, success in loaded.items():
        status = "✓" if success else "✗"
        print(f"  {status} {key}")
    
    # 验证
    stats = new_graphrag.get_statistics()
    print(f"\n  加载后实体数: {stats['knowledge_graph']['total_nodes']}")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("GraphRAG 高级功能示例")
    print("=" * 60)
    
    # 运行示例
    await pdf_processing_example()
    await vector_search_example()
    await query_modes_example()
    await visualization_example()
    await incremental_update_example()
    await persistence_example()
    
    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
