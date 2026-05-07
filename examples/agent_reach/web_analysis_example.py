"""
网页分析示例 - Agent Reach WebReaderSkill 使用示例

演示如何使用 WebReaderSkill 进行网页内容读取、批量处理和链接提取。
适用于内容聚合、竞品分析、新闻监控等场景。

依赖:
    - requests (已包含在项目中)

运行:
    python examples/agent_reach/web_analysis_example.py
"""

import asyncio
import json
from typing import List, Dict, Any

from src.agents.skills import (
    load_skill,
    list_skills,
    get_registry,
    WebReaderSkill,
    SkillCategory
)


async def example_single_page_read():
    """示例1: 读取单个网页"""
    print("=" * 60)
    print("示例1: 读取单个网页")
    print("=" * 60)
    
    # 获取 WebReaderSkill 实例
    skill = load_skill("web_reader")
    if not skill:
        print("错误: WebReaderSkill 未注册")
        return
    
    # 示例 URL - 使用一个技术博客
    url = "https://blog.jina.ai/"
    
    print(f"正在读取: {url}")
    
    # 执行读取
    result = skill.read_webpage(url, use_cache=True, timeout=30)
    
    if result.success:
        print(f"✅ 读取成功!")
        print(f"   内容长度: {result.metadata.get('content_length', 0)} 字符")
        print(f"   响应时间: {result.metadata.get('response_time', 0):.2f} 秒")
        print(f"   是否缓存: {result.metadata.get('cached', False)}")
        print(f"\n内容预览 (前500字符):")
        print("-" * 60)
        print(result.data[:500] if len(result.data) > 500 else result.data)
        print("-" * 60)
    else:
        print(f"❌ 读取失败: {result.error}")
    
    print()


async def example_batch_read():
    """示例2: 批量读取多个网页"""
    print("=" * 60)
    print("示例2: 批量读取多个网页")
    print("=" * 60)
    
    skill = load_skill("web_reader")
    if not skill:
        print("错误: WebReaderSkill 未注册")
        return
    
    # 多个示例 URL
    urls = [
        "https://blog.jina.ai/",
        "https://jina.ai/",
    ]
    
    print(f"批量读取 {len(urls)} 个网页...")
    
    result = skill.read_multiple_pages(urls, use_cache=True, timeout=30)
    
    if result.success:
        data = result.data
        print(f"✅ 批量读取完成!")
        print(f"   总数: {data['total']}")
        print(f"   成功: {data['success_count']}")
        print(f"   失败: {data['error_count']}")
        print(f"   成功率: {data['success_count'] / data['total'] * 100:.1f}%")
        
        print(f"\n成功读取的页面:")
        for page in data['pages']:
            content_preview = page['content'][:200] if len(page['content']) > 200 else page['content']
            print(f"\n📄 {page['url']}")
            print(f"   内容长度: {page['metadata'].get('content_length', 0)} 字符")
            print(f"   预览: {content_preview}...")
        
        if data['errors']:
            print(f"\n失败的页面:")
            for error in data['errors']:
                print(f"   ❌ {error['url']}: {error['error']}")
    else:
        print(f"❌ 批量读取失败: {result.error}")
    
    print()


async def example_extract_links():
    """示例3: 提取网页链接"""
    print("=" * 60)
    print("示例3: 提取网页链接")
    print("=" * 60)
    
    skill = load_skill("web_reader")
    if not skill:
        print("错误: WebReaderSkill 未注册")
        return
    
    url = "https://jina.ai/"
    
    print(f"正在提取链接: {url}")
    
    result = skill.extract_links(url, timeout=30)
    
    if result.success:
        data = result.data
        print(f"✅ 链接提取成功!")
        print(f"   找到 {data['link_count']} 个链接")
        print(f"\n前10个链接:")
        for i, link in enumerate(data['links'][:10], 1):
            print(f"   {i}. {link}")
        
        if len(data['links']) > 10:
            print(f"   ... 还有 {len(data['links']) - 10} 个链接")
    else:
        print(f"❌ 链接提取失败: {result.error}")
    
    print()


async def example_generic_execute():
    """示例4: 使用通用 execute 接口"""
    print("=" * 60)
    print("示例4: 使用通用 execute 接口")
    print("=" * 60)
    
    skill = load_skill("web_reader")
    if not skill:
        print("错误: WebReaderSkill 未注册")
        return
    
    # 使用 execute 方法，通过 action 参数指定操作
    url = "https://blog.jina.ai/"
    
    print(f"使用 execute 接口读取: {url}")
    
    result = skill.execute(url=url, action='read', use_cache=True)
    
    if result.success:
        print(f"✅ 执行成功!")
        print(f"   内容长度: {result.metadata.get('content_length', 0)} 字符")
        print(f"\n内容预览 (前300字符):")
        print("-" * 60)
        print(result.data[:300] if len(result.data) > 300 else result.data)
        print("-" * 60)
    else:
        print(f"❌ 执行失败: {result.error}")
    
    print()


async def example_content_analysis_workflow():
    """示例5: 内容分析工作流 - 结合多个技能"""
    print("=" * 60)
    print("示例5: 内容分析工作流")
    print("=" * 60)
    
    skill = load_skill("web_reader")
    if not skill:
        print("错误: WebReaderSkill 未注册")
        return
    
    # 模拟一个内容分析工作流
    tech_news_urls = [
        "https://blog.jina.ai/",
    ]
    
    print("开始内容分析工作流...")
    print(f"目标: 分析 {len(tech_news_urls)} 个技术新闻源")
    
    # 1. 批量获取内容
    result = skill.read_multiple_pages(tech_news_urls, use_cache=True)
    
    if not result.success:
        print(f"❌ 内容获取失败: {result.error}")
        return
    
    # 2. 分析内容
    print("\n📊 分析结果:")
    for page in result.data['pages']:
        content = page['content']
        
        # 简单的内容分析
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        print(f"\n📄 {page['url']}")
        print(f"   字数: {word_count}")
        print(f"   行数: {line_count}")
        print(f"   字符数: {len(content)}")
        
        # 提取标题（第一行）
        first_line = content.split('\n')[0] if content else "无标题"
        print(f"   标题: {first_line[:100]}")
    
    print("\n✅ 内容分析工作流完成!")
    print()


async def example_list_registered_skills():
    """示例6: 列出所有已注册的技能"""
    print("=" * 60)
    print("示例6: 查看已注册的 Agent Reach 技能")
    print("=" * 60)
    
    registry = get_registry()
    
    # 列出所有 TOOL 类别的技能
    skills = list_skills(category=SkillCategory.TOOL)
    
    print(f"已注册的 TOOL 类别技能 ({len(skills)} 个):")
    print("-" * 60)
    
    for skill_meta in skills:
        print(f"\n{skill_meta.icon} {skill_meta.name}")
        print(f"   描述: {skill_meta.description}")
        print(f"   版本: {skill_meta.version}")
        print(f"   标签: {', '.join(skill_meta.tags)}")
        print(f"   已加载: {registry.is_loaded(skill_meta.name)}")
    
    print()


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 60)
    print("Agent Reach - WebReaderSkill 使用示例")
    print("=" * 60 + "\n")
    
    # 检查技能是否已注册
    registry = get_registry()
    print(f"技能注册表统计: {registry.get_stats()}\n")
    
    # 运行示例
    await example_list_registered_skills()
    await example_single_page_read()
    await example_batch_read()
    await example_extract_links()
    await example_generic_execute()
    await example_content_analysis_workflow()
    
    print("=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
