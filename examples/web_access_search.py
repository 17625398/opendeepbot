"""
Web Access Skill - 搜索功能示例

本示例展示如何使用 Web Access Skill 的各种搜索功能：
- 基础搜索
- 多提供商搜索
- 搜索结果处理
- 搜索并浏览

运行前请确保：
1. 已配置搜索提供商 API Keys（.env 文件）
2. 已安装依赖: pip install requests aiohttp
"""

import asyncio
import json
from typing import List, Dict, Any

# 尝试导入 WebAccessSkill
try:
    from src.skills.web_access import WebAccessSkill
except ImportError:
    print("警告: 无法导入 WebAccessSkill，请确保在正确的目录运行")
    print("尝试使用模拟实现...")
    
    # 模拟实现用于演示
    class MockWebAccessSkill:
        def __init__(self):
            self.name = "WebAccessSkill (Mock)"
        
        async def execute(self, **kwargs):
            action = kwargs.get("action")
            if action == "search":
                return MockResult({
                    "success": True,
                    "data": {
                        "query": kwargs.get("query"),
                        "results": [
                            {"title": "示例结果 1", "url": "https://example.com/1", "snippet": "这是示例摘要..."},
                            {"title": "示例结果 2", "url": "https://example.com/2", "snippet": "这是示例摘要..."}
                        ],
                        "total": 2,
                        "source": kwargs.get("provider", "mock")
                    }
                })
            return MockResult({"success": False, "error": "Unknown action"})
        
        async def smart_access(self, query: str, **kwargs):
            return await self.execute(action="search", query=query, **kwargs)
        
        async def search_and_browse(self, query: str, browse_top_n: int = 3, **kwargs):
            search_result = await self.execute(action="search", query=query, **kwargs)
            return MockResult({
                "success": True,
                "data": {
                    "search_results": search_result.data,
                    "page_contents": {"message": "模拟页面内容"}
                }
            })
        
        def get_stats(self):
            return {
                "available_search_providers": ["jina", "tavily", "serper", "mock"]
            }
    
    class MockResult:
        def __init__(self, data):
            self.success = data.get("success", False)
            self.data = data.get("data")
            self.error = data.get("error")
            self.execution_time = 0.5
    
    WebAccessSkill = MockWebAccessSkill


class SearchExamples:
    """搜索功能示例类"""
    
    def __init__(self):
        self.skill = WebAccessSkill()
        self.results_history: List[Dict[str, Any]] = []
    
    async def example_1_basic_search(self):
        """
        示例 1: 基础搜索
        
        展示最基本的搜索功能
        """
        print("\n" + "="*60)
        print("示例 1: 基础搜索")
        print("="*60)
        
        queries = [
            "Python 异步编程",
            "FastAPI 教程",
            "机器学习入门"
        ]
        
        for query in queries:
            print(f"\n🔍 搜索: {query}")
            
            result = await self.skill.execute(
                action="search",
                query=query,
                max_results=3
            )
            
            if result.success:
                data = result.data
                print(f"✅ 找到 {data['total']} 个结果 (来源: {data['source']})")
                print(f"⏱️  执行时间: {result.execution_time:.2f}秒")
                
                for i, item in enumerate(data['results'][:3], 1):
                    print(f"\n  {i}. {item['title']}")
                    print(f"     URL: {item['url']}")
                    print(f"     摘要: {item['snippet'][:100]}...")
                
                # 保存到历史
                self.results_history.append({
                    "query": query,
                    "total": data['total'],
                    "source": data['source']
                })
            else:
                print(f"❌ 搜索失败: {result.error}")
    
    async def example_2_multi_provider_search(self):
        """
        示例 2: 多提供商搜索对比
        
        展示如何使用不同的搜索提供商
        """
        print("\n" + "="*60)
        print("示例 2: 多提供商搜索对比")
        print("="*60)
        
        query = "人工智能最新进展"
        providers = ["jina", "tavily", "serper"]
        
        print(f"\n🔍 查询: {query}")
        print("-" * 40)
        
        for provider in providers:
            print(f"\n📡 使用提供商: {provider}")
            
            try:
                result = await self.skill.execute(
                    action="search",
                    query=query,
                    max_results=2,
                    provider=provider
                )
                
                if result.success:
                    data = result.data
                    print(f"   ✅ 成功 - 找到 {data['total']} 个结果")
                    print(f"   ⏱️  耗时: {result.execution_time:.2f}秒")
                    
                    # 显示第一个结果
                    if data['results']:
                        first = data['results'][0]
                        print(f"   📝 首个结果: {first['title'][:50]}...")
                else:
                    print(f"   ❌ 失败: {result.error}")
                    
            except Exception as e:
                print(f"   ⚠️  异常: {e}")
    
    async def example_3_search_with_filtering(self):
        """
        示例 3: 搜索结果过滤和处理
        
        展示如何对搜索结果进行后处理
        """
        print("\n" + "="*60)
        print("示例 3: 搜索结果过滤和处理")
        print("="*60)
        
        query = "Python 最佳实践"
        
        print(f"\n🔍 搜索: {query}")
        
        result = await self.skill.execute(
            action="search",
            query=query,
            max_results=10
        )
        
        if not result.success:
            print(f"❌ 搜索失败: {result.error}")
            return
        
        results = result.data['results']
        print(f"✅ 获取到 {len(results)} 个原始结果")
        
        # 过滤 1: 按域名过滤
        print("\n📋 按域名分组:")
        domain_groups: Dict[str, List[str]] = {}
        for item in results:
            url = item.get('url', '')
            domain = url.split('/')[2] if '//' in url else 'unknown'
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(item['title'])
        
        for domain, titles in domain_groups.items():
            print(f"\n  📁 {domain} ({len(titles)} 个结果)")
            for title in titles[:2]:
                print(f"     - {title[:60]}...")
        
        # 过滤 2: 按关键词过滤
        keywords = ["tutorial", "guide", "best", "practice"]
        print(f"\n🔖 包含关键词 {keywords} 的结果:")
        filtered = [
            r for r in results 
            if any(kw in r.get('title', '').lower() or 
                   kw in r.get('snippet', '').lower() 
                   for kw in keywords)
        ]
        
        for item in filtered[:3]:
            print(f"  ✓ {item['title'][:60]}...")
        
        # 统计信息
        print(f"\n📊 统计信息:")
        print(f"  - 总结果数: {len(results)}")
        print(f"  - 不同域名: {len(domain_groups)}")
        print(f"  - 匹配关键词: {len(filtered)}")
    
    async def example_4_search_and_browse(self):
        """
        示例 4: 搜索并浏览结果
        
        展示如何搜索并获取前 N 个结果的详细内容
        """
        print("\n" + "="*60)
        print("示例 4: 搜索并浏览结果")
        print("="*60)
        
        query = "深度学习框架对比"
        
        print(f"\n🔍 搜索并浏览: {query}")
        print("-" * 40)
        
        result = await self.skill.search_and_browse(
            query=query,
            browse_top_n=3,
            extract_content=True
        )
        
        if result.success:
            data = result.data
            
            # 显示搜索结果摘要
            search_data = data.get('search_results', {})
            print(f"\n📋 搜索结果摘要:")
            print(f"  - 总结果数: {search_data.get('total', 0)}")
            print(f"  - 搜索来源: {search_data.get('source', 'unknown')}")
            
            # 显示浏览的页面
            page_contents = data.get('page_contents', {})
            print(f"\n📄 浏览的页面内容:")
            
            if isinstance(page_contents, dict) and 'results' in page_contents:
                for i, page in enumerate(page_contents['results'], 1):
                    print(f"\n  页面 {i}:")
                    print(f"    URL: {page.get('url', 'N/A')}")
                    content = page.get('content', '')
                    if content:
                        print(f"    内容预览: {content[:150]}...")
                    else:
                        print(f"    状态: {'✅ 成功' if page.get('success') else '❌ 失败'}")
            else:
                print(f"  页面内容: {str(page_contents)[:200]}...")
            
            print(f"\n⏱️  总执行时间: {result.execution_time:.2f}秒")
        else:
            print(f"❌ 操作失败: {result.error}")
    
    async def example_5_smart_access(self):
        """
        示例 5: 智能访问
        
        展示 smart_access 方法如何自动判断是搜索还是直接访问
        """
        print("\n" + "="*60)
        print("示例 5: 智能访问")
        print("="*60)
        
        test_cases = [
            ("https://github.com/HKUDS/DeepTutor", "URL"),
            ("Python 教程", "搜索词"),
            ("https://fastapi.tiangolo.com", "URL"),
            ("机器学习最新论文", "搜索词")
        ]
        
        for query, expected_type in test_cases:
            print(f"\n📝 输入: {query}")
            print(f"   预期类型: {expected_type}")
            
            result = await self.skill.smart_access(query)
            
            if result.success:
                channel = getattr(result, 'channel_used', 'unknown')
                print(f"   ✅ 成功 - 使用通道: {channel}")
                
                if result.data:
                    if 'title' in result.data:
                        print(f"   📄 标题: {result.data['title'][:50]}...")
                    elif 'results' in result.data:
                        print(f"   🔍 结果数: {len(result.data['results'])}")
            else:
                print(f"   ❌ 失败: {result.error}")
    
    async def example_6_advanced_search_options(self):
        """
        示例 6: 高级搜索选项
        
        展示各种高级搜索参数的使用
        """
        print("\n" + "="*60)
        print("示例 6: 高级搜索选项")
        print("="*60)
        
        # 不同参数组合的搜索
        search_configs = [
            {
                "name": "基础搜索",
                "params": {"query": "Python", "max_results": 5}
            },
            {
                "name": "指定提供商",
                "params": {"query": "Python", "max_results": 3, "provider": "jina"}
            },
            {
                "name": "大量结果",
                "params": {"query": "Python", "max_results": 20}
            }
        ]
        
        for config in search_configs:
            print(f"\n🔧 {config['name']}")
            print(f"   参数: {json.dumps(config['params'], ensure_ascii=False)}")
            
            result = await self.skill.execute(
                action="search",
                **config['params']
            )
            
            if result.success:
                data = result.data
                print(f"   ✅ 成功")
                print(f"   📊 结果: {data.get('total', 0)} 个")
                print(f"   📡 来源: {data.get('source', 'unknown')}")
                print(f"   ⏱️  耗时: {result.execution_time:.2f}秒")
            else:
                print(f"   ❌ 失败: {result.error}")
    
    def print_summary(self):
        """打印搜索历史摘要"""
        print("\n" + "="*60)
        print("搜索历史摘要")
        print("="*60)
        
        if not self.results_history:
            print("\n暂无搜索记录")
            return
        
        print(f"\n📊 共执行 {len(self.results_history)} 次搜索:")
        
        for i, record in enumerate(self.results_history, 1):
            print(f"\n  {i}. {record['query']}")
            print(f"     结果数: {record['total']}")
            print(f"     来源: {record['source']}")
        
        # 统计不同来源
        sources = {}
        for record in self.results_history:
            source = record['source']
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n📡 来源统计:")
        for source, count in sources.items():
            print(f"  - {source}: {count} 次")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Web Access Skill - 搜索功能示例")
    print("="*60)
    
    # 显示可用搜索提供商
    examples = SearchExamples()
    stats = examples.skill.get_stats()
    
    print("\n📡 可用搜索提供商:")
    providers = stats.get('available_search_providers', [])
    for provider in providers:
        print(f"  - {provider}")
    
    # 运行示例
    try:
        await examples.example_1_basic_search()
        await examples.example_2_multi_provider_search()
        await examples.example_3_search_with_filtering()
        await examples.example_4_search_and_browse()
        await examples.example_5_smart_access()
        await examples.example_6_advanced_search_options()
        
        # 打印摘要
        examples.print_summary()
        
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("示例运行完成!")
    print("="*60)


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
