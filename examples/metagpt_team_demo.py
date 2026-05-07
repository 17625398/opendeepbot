"""
MetaGPT 风格团队演示
展示如何使用预定义角色进行多智能体协作
"""

import asyncio
from src.agents import (
    create_software_team,
    ProductManager,
    Architect,
    ProjectManager,
    Engineer,
    Team,
    TeamConfig,
)


async def demo_basic_usage():
    """基础使用演示"""
    print("=" * 60)
    print("Demo 1: Basic Usage - Create a Todo App")
    print("=" * 60)
    
    # 创建团队
    idea = "Create a simple todo list application with user authentication"
    team = create_software_team(idea)
    
    # 运行团队
    result = await team.run()
    
    # 输出结果
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    for role_name, output in result.outputs.items():
        print(f"\n[{role_name}]:")
        print(output[:200] + "..." if len(output) > 200 else output)
    
    print(f"\nTotal duration: {result.duration:.2f}s")
    print(f"Total rounds: {result.total_rounds}")


async def demo_custom_team():
    """自定义团队演示"""
    print("\n" + "=" * 60)
    print("Demo 2: Custom Team - Data Analysis Project")
    print("=" * 60)
    
    # 创建自定义团队配置
    config = TeamConfig(
        name="Data Analysis Team",
        idea="Build a data visualization dashboard for sales analytics",
        n_round=3,
    )
    
    # 创建团队
    team = Team(config)
    
    # 招聘特定角色
    team.hire([
        ProductManager(name="PM_Lead"),
        Architect(name="Tech_Lead"),
        Engineer(name="Senior_Engineer"),
    ])
    
    # 运行
    result = await team.run()
    
    print("\n" + "=" * 60)
    print("Custom Team Results:")
    print("=" * 60)
    for role_name, output in result.outputs.items():
        print(f"\n[{role_name}]:")
        print(output[:150] + "..." if len(output) > 150 else output)


async def demo_single_role():
    """单角色演示"""
    print("\n" + "=" * 60)
    print("Demo 3: Single Role - Product Manager")
    print("=" * 60)
    
    # 创建单个角色
    pm = ProductManager()
    
    # 运行角色
    result = await pm.run("Create a mobile app for fitness tracking")
    
    print("\n[ProductManager Output]:")
    print(result[:500] + "..." if len(result) > 500 else result)


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("MetaGPT-Style Multi-Agent Team Demo")
    print("=" * 60 + "\n")
    
    try:
        # 运行所有演示
        await demo_basic_usage()
        await demo_custom_team()
        await demo_single_role()
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
