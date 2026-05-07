"""
社交媒体监控示例 - Agent Reach SocialSearchSkill & RSSReaderSkill 使用示例

演示如何使用 SocialSearchSkill 监控 Twitter/X 和 Reddit，
以及使用 RSSReaderSkill 订阅新闻源。适用于舆情监控、竞品追踪、热点发现等场景。

依赖:
    - requests (已包含在项目中)
    - feedparser: pip install feedparser

运行:
    python examples/agent_reach/social_monitor_example.py
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

from src.agents.skills import (
    load_skill,
    get_registry,
    SocialSearchSkill,
    RSSReaderSkill,
)


async def example_twitter_search():
    """示例1: 搜索 Twitter/X 推文"""
    print("=" * 60)
    print("示例1: 搜索 Twitter/X 推文")
    print("=" * 60)
    
    skill = load_skill("social_search")
    if not skill:
        print("错误: SocialSearchSkill 未注册")
        return
    
    # 搜索关键词
    query = "AI artificial intelligence"
    
    print(f"搜索关键词: '{query}'")
    print("注意: Twitter 搜索需要配置 Cookie\n")
    
    result = skill.search_twitter(
        query=query,
        limit=10,
        use_cache=True
    )
    
    if result.success:
        data = result.data
        print(f"✅ 搜索成功!")
        print(f"   找到 {data['count']} 条推文")
        print(f"   查询: {data['query']}")
        
        print(f"\n推文列表:")
        print("-" * 60)
        for i, tweet in enumerate(data['tweets'][:5], 1):
            print(f"\n{i}. @{tweet['author']}")
            print(f"   内容: {tweet['text'][:100]}...")
            print(f"   ❤️ {tweet['likes']} | 🔄 {tweet['retweets']} | 💬 {tweet['replies']}")
            print(f"   链接: {tweet['url']}")
    else:
        print(f"❌ 搜索失败: {result.error}")
        if result.metadata:
            print(f"   建议: {result.metadata.get('fix_suggestion', '')}")
    
    print()


async def example_reddit_search():
    """示例2: 搜索 Reddit 帖子"""
    print("=" * 60)
    print("示例2: 搜索 Reddit 帖子")
    print("=" * 60)
    
    skill = load_skill("social_search")
    if not skill:
        print("错误: SocialSearchSkill 未注册")
        return
    
    query = "machine learning"
    
    print(f"搜索关键词: '{query}'")
    print("注意: Reddit 搜索需要配置 Exa API Key\n")
    
    result = skill.search_reddit(
        query=query,
        limit=10,
        use_cache=True
    )
    
    if result.success:
        data = result.data
        print(f"✅ 搜索成功!")
        print(f"   找到 {data['count']} 个帖子")
        print(f"   查询: {data['query']}")
        
        print(f"\n帖子列表:")
        print("-" * 60)
        for i, post in enumerate(data['posts'][:5], 1):
            print(f"\n{i}. {post['title'][:80]}")
            print(f"   内容: {post['text'][:150]}...")
            print(f"   链接: {post['url']}")
    else:
        print(f"❌ 搜索失败: {result.error}")
        if result.metadata:
            print(f"   建议: {result.metadata.get('fix_suggestion', '')}")
    
    print()


async def example_rss_feed_parsing():
    """示例3: 解析 RSS 订阅源"""
    print("=" * 60)
    print("示例3: 解析 RSS 订阅源")
    print("=" * 60)
    
    skill = load_skill("rss_reader")
    if not skill:
        print("错误: RSSReaderSkill 未注册")
        return
    
    # 示例 RSS 源 - Hacker News
    rss_url = "https://news.ycombinator.com/rss"
    
    print(f"解析 RSS 源: {rss_url}\n")
    
    result = skill.parse_rss(
        url=rss_url,
        limit=10,
        use_cache=True
    )
    
    if result.success:
        data = result.data
        feed = data['feed']
        items = data['items']
        
        print(f"✅ 解析成功!")
        print(f"   源名称: {feed['title']}")
        print(f"   描述: {feed['description']}")
        print(f"   总条目: {data['total']}")
        print(f"   返回条目: {data['returned']}")
        
        print(f"\n最新文章:")
        print("-" * 60)
        for i, item in enumerate(items[:5], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   链接: {item['link']}")
            if item.get('author'):
                print(f"   作者: {item['author']}")
            if item.get('published'):
                print(f"   发布: {item['published']}")
    else:
        print(f"❌ 解析失败: {result.error}")
    
    print()


async def example_multi_rss_aggregation():
    """示例4: 多 RSS 源聚合"""
    print("=" * 60)
    print("示例4: 多 RSS 源聚合")
    print("=" * 60)
    
    skill = load_skill("rss_reader")
    if not skill:
        print("错误: RSSReaderSkill 未注册")
        return
    
    # 多个 RSS 源
    rss_urls = [
        "https://news.ycombinator.com/rss",
        "https://www.reddit.com/r/technology/.rss",
    ]
    
    print(f"聚合 {len(rss_urls)} 个 RSS 源:\n")
    for url in rss_urls:
        print(f"   - {url}")
    print()
    
    result = skill.parse_multiple_feeds(
        urls=rss_urls,
        limit_per_feed=5,
        use_cache=True
    )
    
    if result.success:
        data = result.data
        items = data['items']
        errors = data['errors']
        
        print(f"✅ 聚合完成!")
        print(f"   总条目: {data['total']}")
        print(f"   源数量: {data['feed_count']}")
        print(f"   错误数: {data['error_count']}")
        
        if errors:
            print(f"\n错误详情:")
            for error in errors:
                print(f"   ❌ {error['url']}: {error['error']}")
        
        print(f"\n聚合内容 (按时间排序):")
        print("-" * 60)
        for i, item in enumerate(items[:8], 1):
            source = item.get('source_feed', 'Unknown')
            print(f"\n{i}. [{source}] {item['title']}")
            print(f"   链接: {item['link']}")
    else:
        print(f"❌ 聚合失败: {result.error}")
    
    print()


async def example_social_monitoring_workflow():
    """示例5: 社交媒体监控工作流"""
    print("=" * 60)
    print("示例5: 社交媒体监控工作流")
    print("=" * 60)
    
    social_skill = load_skill("social_search")
    rss_skill = load_skill("rss_reader")
    
    if not social_skill or not rss_skill:
        print("错误: 所需技能未注册")
        return
    
    # 监控配置
    monitor_config = {
        "keywords": ["AI", "machine learning", "deep learning"],
        "rss_sources": [
            "https://news.ycombinator.com/rss",
        ],
        "time_window": "24h"
    }
    
    print("启动社交媒体监控工作流...")
    print(f"监控关键词: {', '.join(monitor_config['keywords'])}")
    print(f"RSS 源: {len(monitor_config['rss_sources'])} 个")
    print(f"时间窗口: {monitor_config['time_window']}\n")
    
    all_content = []
    
    # 1. 从 RSS 源收集内容
    print("📡 从 RSS 源收集内容...")
    rss_result = rss_skill.parse_multiple_feeds(
        urls=monitor_config['rss_sources'],
        limit_per_feed=10
    )
    
    if rss_result.success:
        for item in rss_result.data['items']:
            # 检查是否包含关键词
            content_text = f"{item['title']} {item.get('description', '')}".lower()
            for keyword in monitor_config['keywords']:
                if keyword.lower() in content_text:
                    all_content.append({
                        'source': f"RSS:{item.get('source_feed', 'Unknown')}",
                        'title': item['title'],
                        'url': item['link'],
                        'matched_keyword': keyword,
                        'type': 'rss'
                    })
                    break
        print(f"   从 RSS 收集到 {len(all_content)} 条相关内容")
    
    # 2. 输出监控报告
    print("\n📊 监控报告:")
    print("-" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"相关内容总数: {len(all_content)}")
    
    if all_content:
        print(f"\n相关内容列表:")
        for i, content in enumerate(all_content[:10], 1):
            print(f"\n{i}. [{content['source']}] {content['title'][:70]}")
            print(f"   匹配关键词: {content['matched_keyword']}")
            print(f"   链接: {content['url']}")
    else:
        print("\n暂无相关内容")
    
    print("\n✅ 监控工作流完成!")
    print()


async def example_trend_analysis():
    """示例6: 热点趋势分析"""
    print("=" * 60)
    print("示例6: 热点趋势分析")
    print("=" * 60)
    
    skill = load_skill("rss_reader")
    if not skill:
        print("错误: RSSReaderSkill 未注册")
        return
    
    # 科技新闻源
    tech_sources = [
        "https://news.ycombinator.com/rss",
    ]
    
    print("分析科技热点趋势...\n")
    
    result = skill.parse_multiple_feeds(
        urls=tech_sources,
        limit_per_feed=20
    )
    
    if result.success:
        items = result.data['items']
        
        # 简单的词频分析
        word_freq = {}
        tech_keywords = [
            'AI', 'artificial intelligence', 'machine learning', 'deep learning',
            'Python', 'JavaScript', 'cloud', 'blockchain', 'crypto',
            'startup', 'funding', 'acquisition', 'IPO'
        ]
        
        for item in items:
            title = item['title'].lower()
            for keyword in tech_keywords:
                if keyword.lower() in title:
                    word_freq[keyword] = word_freq.get(keyword, 0) + 1
        
        # 排序
        sorted_trends = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        print("📈 热点趋势 (基于标题词频):")
        print("-" * 60)
        for keyword, count in sorted_trends[:10]:
            bar = "█" * count
            print(f"{keyword:20s} {bar} ({count})")
        
        print(f"\n📰 最新文章:")
        print("-" * 60)
        for i, item in enumerate(items[:5], 1):
            print(f"{i}. {item['title'][:70]}")
    else:
        print(f"❌ 分析失败: {result.error}")
    
    print()


async def example_generic_execute():
    """示例7: 使用通用 execute 接口"""
    print("=" * 60)
    print("示例7: 使用通用 execute 接口")
    print("=" * 60)
    
    skill = load_skill("social_search")
    if not skill:
        print("错误: SocialSearchSkill 未注册")
        return
    
    print("使用 execute 接口搜索 Twitter...")
    print("注意: 需要配置 Twitter Cookie\n")
    
    # 使用通用接口
    result = skill.execute(
        platform='twitter',
        action='search',
        query='OpenAI',
        limit=5
    )
    
    if result.success:
        data = result.data
        print(f"✅ 执行成功!")
        print(f"   找到 {data['count']} 条推文")
        
        for tweet in data['tweets'][:3]:
            print(f"\n@{tweet['author']}: {tweet['text'][:80]}...")
    else:
        print(f"❌ 执行失败: {result.error}")
        if result.metadata:
            print(f"   建议: {result.metadata.get('fix_suggestion', '')}")
    
    print()


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 60)
    print("Agent Reach - 社交媒体监控示例")
    print("=" * 60 + "\n")
    
    # 检查技能是否已注册
    registry = get_registry()
    print(f"技能注册表统计: {registry.get_stats()}\n")
    
    # 运行示例
    await example_twitter_search()
    await example_reddit_search()
    await example_rss_feed_parsing()
    await example_multi_rss_aggregation()
    await example_social_monitoring_workflow()
    await example_trend_analysis()
    await example_generic_execute()
    
    print("=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
