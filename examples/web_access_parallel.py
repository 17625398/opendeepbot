"""
Web Access Skill - 并行任务示例

本示例展示如何使用 Web Access Skill 的并行处理能力：
- 批量 URL 获取
- 批量搜索
- 并行任务管理
- 结果合并

运行前请确保：
1. 已配置搜索提供商 API Keys
2. 已安装依赖: pip install requests aiohttp
"""

import asyncio
import time
from typing import List, Dict, Any
from dataclasses import dataclass

# 尝试导入 WebAccessSkill
try:
    from src.skills.web_access import WebAccessSkill
except ImportError:
    print("警告: 无法导入 WebAccessSkill，使用模拟实现")
    
    class MockWebAccessSkill:
        def __init__(self):
            self.name = "WebAccessSkill (Mock)"
        
        async def execute(self, **kwargs):
            action = kwargs.get("action")
            
            if action == "multi_fetch":
                urls = kwargs.get("urls", [])
                await asyncio.sleep(0.1)  # 模拟延迟
                return MockResult({
                    "success": True,
                    "data": {
                        "total": len(urls),
                        "completed": len(urls),
                        "failed": 0,
                        "results": [
                            {
                                "url": url,
                                "success": True,
                                "data": {"title": f"Page {i+1}", "content": f"Content of {url}"}
                            }
                            for i, url in enumerate(urls)
                        ]
                    }
                })
            
            elif action == "multi_search":
                queries = kwargs.get("queries", [])
                await asyncio.sleep(0.1)
                return MockResult({
                    "success": True,
                    "data": {
                        "total": len(queries),
                        "completed": len(queries),
                        "failed": 0,
                        "results": [
                            {
                                "query": query,
                                "success": True,
                                "data": {"results": [{"title": f"Result for {query}"}]}
                            }
                            for query in queries
                        ]
                    }
                })
            
            return MockResult({"success": False, "error": "Unknown action"})
        
        def get_stats(self):
            return {"config": {"parallel": {"max_workers": 5}}}
    
    class MockResult:
        def __init__(self, data):
            self.success = data.get("success", False)
            self.data = data.get("data")
            self.error = data.get("error")
            self.execution_time = 0.5
    
    WebAccessSkill = MockWebAccessSkill


@dataclass
class TaskResult:
    """任务结果数据类"""
    task_id: str
    success: bool
    data: Any = None
    error: str = None
    execution_time: float = 0.0


class ParallelExamples:
    """并行任务示例类"""
    
    def __init__(self):
        self.skill = WebAccessSkill()
        self.task_history: List[Dict[str, Any]] = []
    
    async def example_1_basic_multi_fetch(self):
        """
        示例 1: 基础批量 URL 获取
        
        展示如何并行获取多个 URL
        """
        print("\n" + "="*60)
        print("示例 1: 基础批量 URL 获取")
        print("="*60)
        
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
        ]
        
        print(f"\n🌐 批量获取 {len(urls)} 个 URL:")
        for url in urls:
            print(f"   - {url}")
        
        start_time = time.time()
        
        result = await self.skill.execute(
            action="multi_fetch",
            urls=urls,
            extract_content=True
        )
        
        elapsed = time.time() - start_time
        
        if result.success:
            data = result.data
            print(f"\n✅ 批量获取完成")
            print(f"📊 统计:")
            print(f"   - 总任务: {data.get('total', 0)}")
            print(f"   - 成功: {data.get('completed', 0)}")
            print(f"   - 失败: {data.get('failed', 0)}")
            print(f"   - 总耗时: {elapsed:.2f}秒")
            print(f"   - 平均每个 URL: {elapsed/len(urls):.2f}秒")
            
            # 显示每个结果
            results = data.get('results', [])
            print(f"\n📋 详细结果:")
            for i, item in enumerate(results, 1):
                status = "✅" if item.get('success') else "❌"
                url = item.get('url', 'N/A')
                print(f"   {i}. {status} {url}")
                if item.get('success') and item.get('data'):
                    title = item['data'].get('title', 'N/A')
                    print(f"      标题: {title}")
            
            # 保存到历史
            self.task_history.append({
                "type": "multi_fetch",
                "total": data.get('total', 0),
                "completed": data.get('completed', 0),
                "failed": data.get('failed', 0),
                "time": elapsed
            })
        else:
            print(f"❌ 批量获取失败: {result.error}")
    
    async def example_2_basic_multi_search(self):
        """
        示例 2: 基础批量搜索
        
        展示如何并行执行多个搜索查询
        """
        print("\n" + "="*60)
        print("示例 2: 基础批量搜索")
        print("="*60)
        
        queries = [
            "Python 教程",
            "JavaScript 基础",
            "Go 语言入门",
            "Rust 编程",
            "TypeScript 指南"
        ]
        
        print(f"\n🔍 批量搜索 {len(queries)} 个查询:")
        for query in queries:
            print(f"   - {query}")
        
        start_time = time.time()
        
        result = await self.skill.execute(
            action="multi_search",
            queries=queries,
            max_results=3
        )
        
        elapsed = time.time() - start_time
        
        if result.success:
            data = result.data
            print(f"\n✅ 批量搜索完成")
            print(f"📊 统计:")
            print(f"   - 总查询: {data.get('total', 0)}")
            print(f"   - 成功: {data.get('completed', 0)}")
            print(f"   - 失败: {data.get('failed', 0)}")
            print(f"   - 总耗时: {elapsed:.2f}秒")
            print(f"   - 平均每个查询: {elapsed/len(queries):.2f}秒")
            
            # 显示每个搜索结果
            results = data.get('results', [])
            print(f"\n📋 搜索结果摘要:")
            for i, item in enumerate(results, 1):
                status = "✅" if item.get('success') else "❌"
                query = item.get('query', 'N/A')
                print(f"   {i}. {status} {query}")
                
                if item.get('success') and item.get('data'):
                    search_data = item['data']
                    total_results = search_data.get('total', 0)
                    print(f"      找到 {total_results} 个结果")
            
            self.task_history.append({
                "type": "multi_search",
                "total": data.get('total', 0),
                "completed": data.get('completed', 0),
                "failed": data.get('failed', 0),
                "time": elapsed
            })
        else:
            print(f"❌ 批量搜索失败: {result.error}")
    
    async def example_3_large_batch_processing(self):
        """
        示例 3: 大批量处理
        
        展示如何处理大量 URL 或查询
        """
        print("\n" + "="*60)
        print("示例 3: 大批量处理")
        print("="*60)
        
        # 生成大量 URL
        urls = [f"https://httpbin.org/delay/{i%3}" for i in range(20)]
        
        print(f"\n🌐 大批量获取 {len(urls)} 个 URL")
        print("-" * 40)
        
        start_time = time.time()
        
        result = await self.skill.execute(
            action="multi_fetch",
            urls=urls,
            extract_content=False  # 只检查可访问性，不提取内容
        )
        
        elapsed = time.time() - start_time
        
        if result.success:
            data = result.data
            results = data.get('results', [])
            
            # 统计成功/失败
            success_count = sum(1 for r in results if r.get('success'))
            fail_count = len(results) - success_count
            
            print(f"✅ 大批量处理完成")
            print(f"\n📊 统计:")
            print(f"   - 总任务: {len(urls)}")
            print(f"   - 成功: {success_count}")
            print(f"   - 失败: {fail_count}")
            print(f"   - 成功率: {success_count/len(urls)*100:.1f}%")
            print(f"   - 总耗时: {elapsed:.2f}秒")
            print(f"   - 吞吐量: {len(urls)/elapsed:.1f} URL/秒")
            
            # 显示失败的任务
            if fail_count > 0:
                print(f"\n❌ 失败的任务:")
                for item in results:
                    if not item.get('success'):
                        print(f"   - {item.get('url')}: {item.get('error', 'Unknown error')}")
        else:
            print(f"❌ 大批量处理失败: {result.error}")
    
    async def example_4_performance_comparison(self):
        """
        示例 4: 串行 vs 并行性能对比
        
        展示并行处理相比串行处理的性能优势
        """
        print("\n" + "="*60)
        print("示例 4: 串行 vs 并行性能对比")
        print("="*60)
        
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
        ]
        
        print(f"\n🔄 测试 {len(urls)} 个 URL (每个延迟 1 秒)")
        print("-" * 40)
        
        # 模拟串行处理
        print("\n📊 串行处理 (模拟):")
        serial_time = len(urls) * 1.5  # 假设每个 1.5 秒
        print(f"   预计耗时: {serial_time:.1f}秒")
        
        # 实际并行处理
        print("\n⚡ 并行处理:")
        start_time = time.time()
        
        result = await self.skill.execute(
            action="multi_fetch",
            urls=urls,
            extract_content=False
        )
        
        parallel_time = time.time() - start_time
        
        if result.success:
            print(f"   实际耗时: {parallel_time:.2f}秒")
            print(f"   加速比: {serial_time/parallel_time:.1f}x")
            print(f"   节省时间: {serial_time - parallel_time:.1f}秒")
            print(f"   效率提升: {(1 - parallel_time/serial_time)*100:.1f}%")
        else:
            print(f"   并行处理失败: {result.error}")
    
    async def example_5_result_aggregation(self):
        """
        示例 5: 结果聚合和分析
        
        展示如何聚合和分析批量操作的结果
        """
        print("\n" + "="*60)
        print("示例 5: 结果聚合和分析")
        print("="*60)
        
        queries = [
            "Python web framework",
            "JavaScript frontend framework",
            "Go microservices",
            "Rust web assembly",
            "TypeScript vs JavaScript"
        ]
        
        print(f"\n🔍 执行 {len(queries)} 个搜索查询")
        print("-" * 40)
        
        result = await self.skill.execute(
            action="multi_search",
            queries=queries,
            max_results=5
        )
        
        if result.success:
            data = result.data
            results = data.get('results', [])
            
            print(f"✅ 搜索完成，开始聚合分析...")
            
            # 聚合 1: 按来源统计
            source_stats = {}
            for item in results:
                if item.get('success') and item.get('data'):
                    source = item['data'].get('source', 'unknown')
                    source_stats[source] = source_stats.get(source, 0) + 1
            
            print(f"\n📡 数据来源统计:")
            for source, count in source_stats.items():
                print(f"   - {source}: {count} 个查询")
            
            # 聚合 2: 提取所有标题
            all_titles = []
            for item in results:
                if item.get('success') and item.get('data'):
                    search_results = item['data'].get('results', [])
                    for r in search_results:
                        title = r.get('title', '')
                        if title:
                            all_titles.append(title)
            
            print(f"\n📋 共收集 {len(all_titles)} 个标题")
            print(f"   示例标题:")
            for title in all_titles[:5]:
                print(f"   - {title[:60]}...")
            
            # 聚合 3: 关键词频率分析
            keywords = ["python", "javascript", "go", "rust", "typescript"]
            keyword_count = {kw: 0 for kw in keywords}
            
            for title in all_titles:
                title_lower = title.lower()
                for kw in keywords:
                    if kw in title_lower:
                        keyword_count[kw] += 1
            
            print(f"\n🔑 关键词频率:")
            for kw, count in sorted(keyword_count.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * count
                print(f"   {kw:12} {bar} ({count})")
        else:
            print(f"❌ 搜索失败: {result.error}")
    
    async def example_6_error_handling_in_batch(self):
        """
        示例 6: 批量操作中的错误处理
        
        展示如何处理批量操作中的部分失败
        """
        print("\n" + "="*60)
        print("示例 6: 批量操作中的错误处理")
        print("="*60)
        
        # 混合有效和无效 URL
        urls = [
            "https://example.com",  # 有效
            "https://invalid-domain-12345.com",  # 无效域名
            "https://httpbin.org/status/404",  # 404 错误
            "https://httpbin.org/status/500",  # 500 错误
            "https://httpbin.org/delay/1",  # 有效
        ]
        
        print(f"\n🌐 测试批量错误处理 ({len(urls)} 个 URL):")
        for url in urls:
            print(f"   - {url}")
        
        result = await self.skill.execute(
            action="multi_fetch",
            urls=urls,
            extract_content=True
        )
        
        if result.success:
            data = result.data
            results = data.get('results', [])
            
            print(f"\n📊 结果分析:")
            
            # 分类结果
            successful = []
            failed = []
            
            for item in results:
                if item.get('success'):
                    successful.append(item)
                else:
                    failed.append(item)
            
            print(f"\n✅ 成功的任务 ({len(successful)}):")
            for item in successful:
                print(f"   ✓ {item.get('url')}")
            
            print(f"\n❌ 失败的任务 ({len(failed)}):")
            for item in failed:
                url = item.get('url')
                error = item.get('error', 'Unknown error')
                print(f"   ✗ {url}")
                print(f"     错误: {error}")
            
            print(f"\n💡 建议:")
            print(f"   - 对于失败的任务，可以单独重试")
            print(f"   - 检查 URL 是否正确")
            print(f"   - 考虑增加超时时间")
            print(f"   - 使用 use_browser=True 处理复杂页面")
        else:
            print(f"❌ 批量操作失败: {result.error}")
    
    def print_parallel_config(self):
        """打印并行配置信息"""
        print("\n" + "="*60)
        print("并行处理配置")
        print("="*60)
        
        stats = self.skill.get_stats()
        config = stats.get('config', {})
        parallel_config = config.get('parallel', {})
        
        print(f"\n⚙️  并行配置:")
        print(f"   - 最大工作线程: {parallel_config.get('max_workers', 5)}")
        print(f"   - 最大并发标签页: {parallel_config.get('max_concurrent_tabs', 10)}")
        print(f"   - 启用子代理: {parallel_config.get('enable_sub_agent', True)}")
        print(f"   - 子代理超时: {parallel_config.get('sub_agent_timeout', 120)} 秒")
        print(f"   - 合并策略: {parallel_config.get('merge_strategy', 'smart')}")
        
        print(f"\n💡 性能建议:")
        print(f"   - 对于 I/O 密集型任务，适当增加 max_workers")
        print(f"   - 对于 CPU 密集型任务，保持 max_workers <= CPU 核心数")
        print(f"   - 大量小任务适合并行，少量大任务适合串行")
    
    def print_summary(self):
        """打印任务历史摘要"""
        print("\n" + "="*60)
        print("并行任务历史摘要")
        print("="*60)
        
        if not self.task_history:
            print("\n暂无任务记录")
            return
        
        print(f"\n📊 共执行 {len(self.task_history)} 个批量任务:")
        
        total_tasks = 0
        total_completed = 0
        total_time = 0
        
        for i, record in enumerate(self.task_history, 1):
            print(f"\n  {i}. {record['type']}")
            print(f"     总任务: {record['total']}")
            print(f"     成功: {record['completed']}")
            print(f"     失败: {record['failed']}")
            print(f"     耗时: {record['time']:.2f}秒")
            
            total_tasks += record['total']
            total_completed += record['completed']
            total_time += record['time']
        
        print(f"\n📈 总体统计:")
        print(f"   - 总任务数: {total_tasks}")
        print(f"   - 总成功: {total_completed}")
        print(f"   - 总失败: {total_tasks - total_completed}")
        print(f"   - 总耗时: {total_time:.2f}秒")
        print(f"   - 平均成功率: {total_completed/total_tasks*100:.1f}%")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Web Access Skill - 并行任务示例")
    print("="*60)
    
    examples = ParallelExamples()
    
    # 打印配置信息
    examples.print_parallel_config()
    
    # 运行示例
    try:
        await examples.example_1_basic_multi_fetch()
        await examples.example_2_basic_multi_search()
        await examples.example_3_large_batch_processing()
        await examples.example_4_performance_comparison()
        await examples.example_5_result_aggregation()
        await examples.example_6_error_handling_in_batch()
        
        # 打印摘要
        examples.print_summary()
        
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("示例运行完成!")
    print("="*60)
    print("\n💡 提示:")
    print("   - 并行处理可以显著提高批量操作效率")
    print("   - 注意控制并发数，避免对目标服务器造成压力")
    print("   - 对于重要任务，建议实现重试机制")


if __name__ == "__main__":
    asyncio.run(main())
