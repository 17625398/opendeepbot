"""
知识库高级功能使用示例

展示如何使用缓存、索引、批量处理等高级功能
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.skills.knowledge_base import (
    # 基础组件
    KnowledgeBaseManager,
    KnowledgeBaseConfig,
    DocumentType,

    # 缓存
    CacheManager,
    EmbeddingCache,
    QueryCache,
    cached,
    get_embedding_cache,
    get_query_cache,

    # 索引
    DocumentIndexer,
    TextAnalyzer,
    QuerySuggester,

    # 批量处理
    BatchProcessor,
    DocumentBatchProcessor,
    TaskStatus,
    get_batch_processor,
)


async def demo_cache():
    """演示缓存功能"""
    print("\n=== 缓存功能演示 ===\n")

    # 1. 基础缓存管理器
    print("1. 基础缓存管理器")
    cache = CacheManager[str](max_size=100, default_ttl=60)

    # 设置缓存
    cache.set("key1", "value1", ttl=30)
    cache.set("key2", "value2")

    # 获取缓存
    value1 = cache.get("key1")
    print(f"   key1: {value1}")

    value2 = cache.get("key2")
    print(f"   key2: {value2}")

    # 获取统计信息
    stats = cache.get_stats()
    print(f"   缓存统计: {stats}")

    # 2. 嵌入向量缓存
    print("\n2. 嵌入向量缓存")
    embedding_cache = EmbeddingCache(max_size=1000, default_ttl=3600)

    # 模拟嵌入向量
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    embedding_cache.set_embedding("测试文本", "text-embedding-ada-002", embedding)

    # 获取嵌入
    cached_embedding = embedding_cache.get_embedding("测试文本", "text-embedding-ada-002")
    print(f"   缓存命中: {cached_embedding is not None}")

    # 3. 使用装饰器缓存函数结果
    print("\n3. 缓存装饰器")

    compute_cache = CacheManager[int](max_size=100)

    @cached(compute_cache, ttl=60)
    async def expensive_computation(n: int) -> int:
        """模拟耗时计算"""
        await asyncio.sleep(0.1)
        return n * n

    # 第一次调用（计算）
    start = time.time()
    result1 = await expensive_computation(5)
    duration1 = time.time() - start
    print(f"   第一次调用: result={result1}, time={duration1:.3f}s")

    # 第二次调用（缓存）
    start = time.time()
    result2 = await expensive_computation(5)
    duration2 = time.time() - start
    print(f"   第二次调用: result={result2}, time={duration2:.3f}s (缓存)")

    print(f"   缓存统计: {compute_cache.get_stats()}")


async def demo_indexer():
    """演示文档索引功能"""
    print("\n=== 文档索引演示 ===\n")

    # 创建索引器
    indexer = DocumentIndexer()

    # 添加文档到索引
    print("1. 添加文档到索引")
    documents = [
        ("doc1", "Python编程指南", "Python是一种高级编程语言，支持多种编程范式。"),
        ("doc2", "机器学习入门", "机器学习是人工智能的一个分支，使用统计方法让计算机从数据中学习。"),
        ("doc3", "深度学习基础", "深度学习是机器学习的一个子领域，使用多层神经网络。"),
        ("doc4", "自然语言处理", "NLP是人工智能和语言学的交叉领域，研究计算机与人类语言的交互。"),
    ]

    for doc_id, title, content in documents:
        await indexer.index_document(doc_id, title, content)
        print(f"   已索引: {title}")

    # 搜索文档
    print("\n2. 搜索文档")
    queries = ["Python编程", "机器学习", "神经网络"]

    for query in queries:
        result = await indexer.search(query, top_k=3)
        print(f"\n   查询: '{query}'")
        print(f"   优化后的查询: '{result['query']}'")
        print(f"   结果数量: {len(result['results'])}")

        for r in result['results']:
            print(f"   - {r.document_id}: score={r.score:.3f}")

    # 获取搜索建议
    print("\n3. 搜索建议")
    partial_queries = ["Py", "机器", "深度"]

    for partial in partial_queries:
        suggestions = indexer.get_suggestions(partial, top_k=3)
        print(f"\n   输入: '{partial}'")
        for s in suggestions:
            print(f"   - {s.text} (score={s.score:.2f}, type={s.type})")

    # 获取统计信息
    print("\n4. 索引统计")
    stats = indexer.get_stats()
    print(f"   {stats}")


async def demo_batch_processor():
    """演示批量处理功能"""
    print("\n=== 批量处理演示 ===\n")

    # 创建批量处理器
    processor = BatchProcessor(max_workers=4, max_concurrent=5)

    # 注册任务处理器
    async def process_item(data: dict) -> dict:
        """模拟处理任务"""
        await asyncio.sleep(0.1)  # 模拟耗时操作
        return {
            "id": data["id"],
            "processed": True,
            "result": data["value"] * 2
        }

    processor.register_handler("process", process_item)

    # 创建批量任务
    print("1. 创建批量任务")
    tasks_data = [
        {"id": i, "value": i * 10}
        for i in range(10)
    ]

    job = await processor.create_job(
        job_id="batch_job_001",
        name="处理10个任务",
        tasks_data=tasks_data,
        task_type="process"
    )
    print(f"   作业ID: {job.id}")
    print(f"   任务数量: {job.total_count}")

    # 运行作业并跟踪进度
    print("\n2. 运行批量作业")

    def progress_callback(job):
        print(f"   进度: {job.progress*100:.1f}% ({job.completed_count}/{job.total_count})")

    completed_job = await processor.run_job(job.id, progress_callback)

    print(f"\n   作业完成!")
    print(f"   成功: {completed_job.completed_count}")
    print(f"   失败: {completed_job.failed_count}")

    # 查看任务结果
    print("\n3. 任务结果")
    for task in completed_job.tasks[:3]:  # 显示前3个
        print(f"   任务 {task.id}: {task.status.value}")
        if task.result:
            print(f"   - 结果: {task.result}")

    # 获取作业状态
    print("\n4. 作业状态")
    status = processor.get_job_status(job.id)
    print(f"   {status}")


async def demo_text_analyzer():
    """演示文本分析功能"""
    print("\n=== 文本分析演示 ===\n")

    # 创建文本分析器
    analyzer = TextAnalyzer(language="zh", remove_stopwords=True)

    # 测试文本
    text = """
    Python是一种广泛使用的高级编程语言，由Guido van Rossum创建。
    它强调代码的可读性和简洁的语法，使用缩进来表示代码块。
    Python支持多种编程范式，包括面向对象、命令式、函数式和结构化编程。
    """

    # 1. 分词
    print("1. 分词")
    tokens = analyzer.tokenize(text)
    print(f"   词项数量: {len(tokens)}")
    print(f"   前10个词项: {tokens[:10]}")

    # 2. 分析（去除停用词）
    print("\n2. 分析（去除停用词）")
    analyzed = analyzer.analyze(text)
    print(f"   处理后词项数量: {len(analyzed)}")
    print(f"   前10个词项: {analyzed[:10]}")

    # 3. 提取关键词
    print("\n3. 提取关键词")
    keywords = analyzer.extract_keywords(text, top_k=10)
    print("   关键词:")
    for word, freq in keywords:
        print(f"   - {word}: {freq}次")


async def demo_query_suggester():
    """演示查询建议功能"""
    print("\n=== 查询建议演示 ===\n")

    # 创建查询建议器
    suggester = QuerySuggester()

    # 添加一些查询历史
    print("1. 添加查询历史")
    queries = [
        "Python教程",
        "Python入门",
        "Python高级编程",
        "机器学习基础",
        "机器学习算法",
        "深度学习框架",
        "自然语言处理",
    ]

    for query in queries:
        suggester.add_query(query)
        print(f"   添加: {query}")

    # 获取建议
    print("\n2. 获取查询建议")
    partial_queries = ["Py", "机器", "深度", "自然"]

    for partial in partial_queries:
        suggestions = suggester.suggest(partial, top_k=3)
        print(f"\n   输入 '{partial}':")
        for s in suggestions:
            print(f"   - {s.text} (score={s.score:.2f}, type={s.type})")


async def main():
    """主函数"""
    print("=" * 60)
    print("知识库高级功能示例")
    print("=" * 60)

    try:
        # 运行所有演示
        await demo_cache()
        await demo_text_analyzer()
        await demo_indexer()
        await demo_query_suggester()
        await demo_batch_processor()

        print("\n" + "=" * 60)
        print("所有演示完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
