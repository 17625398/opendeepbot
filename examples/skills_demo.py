"""
DeepTutor Skills Demo
=====================

DeepTutor 技能模块完整演示。

展示如何使用：
- 浏览器自动化 (bb_browser, browser_agent, lightpanda)
- 知识库 (knowledge_base)
- 笔录分析 (record_analyzer)
- 统一接口 (browser_skills)

Usage:
    python examples/skills_demo.py

Author: DeepTutor Team
"""

import asyncio
from typing import Any, Dict


async def demo_browser_skills():
    """演示浏览器技能"""
    print("\n" + "=" * 60)
    print("浏览器技能演示")
    print("=" * 60)
    
    from src.skills.browser_skills import (
        get_unified_browser,
        BrowserType,
        browser_platform_action,
    )
    
    browser = get_unified_browser()
    
    # 1. 浏览器能力对比
    print("\n1. 浏览器能力对比")
    comparison = browser.compare_browsers()
    for browser_type, info in comparison.items():
        print(f"\n  {browser_type}:")
        print(f"    - 支持平台: {info['capabilities']['supports_platforms']}")
        print(f"    - 支持截图: {info['capabilities']['supports_screenshot']}")
        print(f"    - 需要 Docker: {info['requirements']['requires_docker']}")
    
    # 2. 健康检查
    print("\n2. 健康检查")
    health = await browser.health_check()
    for name, status in health.items():
        healthy = status.get("healthy", False)
        print(f"  {name}: {'✓' if healthy else '✗'}")
    
    # 3. 平台操作示例
    print("\n3. 平台操作示例")
    print("  可用平台操作:")
    try:
        from src.skills.bb_browser import list_all_platforms
        platforms = list_all_platforms()
        for p in platforms[:5]:  # 只显示前5个
            print(f"    - {p['icon']} {p['name']} ({p['id']})")
        print(f"    ... 共 {len(platforms)} 个平台")
    except Exception as e:
        print(f"    获取平台列表失败: {e}")


async def demo_knowledge_base():
    """演示知识库功能"""
    print("\n" + "=" * 60)
    print("知识库演示")
    print("=" * 60)
    
    from src.skills.knowledge_base import (
        get_knowledge_base_manager,
        DocumentType,
        QueryRequest,
    )
    
    try:
        manager = await get_knowledge_base_manager()
        
        # 1. 列出文档
        print("\n1. 列出文档")
        docs = await manager.list_documents()
        print(f"  共有 {len(docs)} 个文档")
        
        # 2. 获取统计
        print("\n2. 知识库统计")
        stats = manager.get_stats()
        print(f"  文档总数: {stats['total_documents']}")
        print(f"  分块总数: {stats['total_chunks']}")
        print(f"  存储路径: {stats['storage_path']}")
        
        # 3. 查询示例
        print("\n3. 查询示例")
        print("  查询: '什么是人工智能？'")
        # 注意：实际查询需要文档已添加到知识库
        
    except Exception as e:
        print(f"  知识库演示失败: {e}")


async def demo_record_analyzer():
    """演示笔录分析"""
    print("\n" + "=" * 60)
    print("笔录分析演示")
    print("=" * 60)
    
    from src.skills.record_analyzer import RecordAnalyzer
    
    # 示例笔录文本
    sample_record = """
    张三，男，35岁，是某科技公司的技术总监。他于2024年1月15日向李四汇报工作。
    李四，女，42岁，是该公司的总经理。王五是公司的财务经理，向李四汇报。
    该公司位于北京市海淀区中关村软件园。
    """
    
    analyzer = RecordAnalyzer()
    
    # 1. 实体提取
    print("\n1. 实体提取")
    entities = analyzer.extract_entities(sample_record)
    print(f"  发现 {len(entities)} 个实体:")
    for entity in entities:
        print(f"    - [{entity.type}] {entity.name}")
    
    # 2. 关系分析
    print("\n2. 关系分析")
    relationships = analyzer.extract_relationships(sample_record, entities)
    print(f"  发现 {len(relationships)} 个关系:")
    for rel in relationships:
        print(f"    - {rel.source} --{rel.type}--> {rel.target}")
    
    # 3. 组织架构
    print("\n3. 组织架构")
    org = analyzer.extract_org_structure(sample_record, entities, relationships)
    print(f"  组织层级: {org.max_depth}")
    print(f"  根节点: {org.root.name if org.root else 'None'}")


async def demo_bb_browser():
    """演示 bb_browser 功能"""
    print("\n" + "=" * 60)
    print("bb-browser 功能演示")
    print("=" * 60)
    
    try:
        from src.skills.bb_browser import (
            BBBrowserClient,
            list_all_platforms,
            get_platform_info,
            SessionManager,
            get_cache,
        )
        
        # 1. 平台列表
        print("\n1. 平台列表")
        platforms = list_all_platforms()
        categories = {}
        for p in platforms:
            cat = p['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(p)
        
        for cat, ps in categories.items():
            print(f"  {cat}: {len(ps)} 个平台")
        
        # 2. 会话管理
        print("\n2. 会话管理")
        session_manager = SessionManager()
        sessions = await session_manager.list_sessions()
        print(f"  当前有 {len(sessions)} 个会话")
        
        # 3. 缓存系统
        print("\n3. 缓存系统")
        cache = get_cache("demo", ttl=60)
        await cache.set("test_key", {"data": "test_value"})
        cached_data = await cache.get("test_key")
        print(f"  缓存数据: {cached_data}")
        stats = cache.get_stats()
        print(f"  缓存统计: {stats}")
        
    except Exception as e:
        print(f"  bb-browser 演示失败: {e}")


async def demo_deerflow():
    """演示 DeerFlow 工作流"""
    print("\n" + "=" * 60)
    print("DeerFlow 工作流演示")
    print("=" * 60)
    
    try:
        from src.skills.deerflow import DeerFlow, get_deerflow
        
        # 1. 工作流信息
        print("\n1. 工作流信息")
        flow = get_deerflow()
        info = flow.get_workflow_info()
        print(f"  工作流 ID: {info['id']}")
        print(f"  状态: {info['status']}")
        print(f"  步骤数: {info['total_steps']}")
        
        # 2. 子代理
        print("\n2. 子代理")
        subagents = flow.list_subagents()
        print(f"  可用子代理: {len(subagents)}")
        for sa in subagents[:3]:
            print(f"    - {sa['name']}: {sa['description']}")
        
        # 3. 记忆系统
        print("\n3. 记忆系统")
        memory = flow.get_memory_stats()
        print(f"  记忆条目: {memory.get('total_memories', 0)}")
        
    except Exception as e:
        print(f"  DeerFlow 演示失败: {e}")


async def demo_all_skills():
    """演示所有技能"""
    print("\n" + "=" * 60)
    print("所有技能概览")
    print("=" * 60)
    
    from src.skills import get_all_skills_info, list_available_skills
    
    info = get_all_skills_info()
    print(f"\n共有 {len(info)} 个技能类别:")
    
    for category, data in info.items():
        print(f"\n  {data['name']} ({category}):")
        for skill in data['skills']:
            print(f"    - {skill['name']}: {skill['description']}")
            print(f"      能力: {', '.join(skill['capabilities'])}")
    
    # 列出所有可用技能
    print("\n" + "-" * 60)
    all_skills = list_available_skills()
    print(f"\n总计 {len(all_skills)} 个技能")


async def main():
    """主函数"""
    print("=" * 60)
    print("DeepTutor 技能模块演示")
    print("=" * 60)
    print("\n本演示展示 DeepTutor 的各种技能模块功能")
    print("注意：部分功能需要相应的环境配置才能正常运行")
    
    try:
        # 运行所有演示
        await demo_all_skills()
        await demo_browser_skills()
        await demo_knowledge_base()
        await demo_record_analyzer()
        await demo_bb_browser()
        await demo_deerflow()
        
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("演示结束")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
