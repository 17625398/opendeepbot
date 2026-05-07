"""
OpenHarness 快速入门示例

展示如何在 DeepTutor 中使用 OpenHarness 集成功能
"""

import asyncio
from src.integrations.openharness import (
    init_openharness,
    get_engine,
    loop_manager,
    create_task,
    get_task_status,
)


async def basic_agent_execution():
    """基础 Agent 执行示例"""
    print("=" * 50)
    print("示例 1: 基础 Agent 执行")
    print("=" * 50)

    # 初始化 OpenHarness
    success = await init_openharness()
    if not success:
        print("OpenHarness 初始化失败")
        return

    # 获取引擎
    engine = get_engine()

    # 执行简单任务
    prompt = "列出当前目录下的所有 Python 文件"

    try:
        result = await engine.execute(prompt, stream=False)
        print(f"执行结果: {result}")
    except Exception as e:
        print(f"执行失败: {e}")


async def streaming_execution():
    """流式执行示例"""
    print("\n" + "=" * 50)
    print("示例 2: 流式 Agent 执行")
    print("=" * 50)

    # 使用 LoopManager 执行流式任务
    prompt = "分析 src/integrations/openharness/ 目录的代码结构"

    try:
        async for event in loop_manager.execute_stream(prompt):
            if event.type == "text":
                print(event.content, end="", flush=True)
            elif event.type == "tool_call":
                print(f"\n[工具调用: {event.tool_name}]")
            elif event.type == "tool_result":
                print(f"[工具结果: {event.tool_name}]")
            elif event.type == "error":
                print(f"\n[错误: {event.error}]")
    except Exception as e:
        print(f"流式执行失败: {e}")


async def task_management():
    """任务管理示例"""
    print("\n" + "=" * 50)
    print("示例 3: 后台任务管理")
    print("=" * 50)

    # 创建后台任务
    task_config = {
        "name": "代码分析任务",
        "description": "分析项目代码质量",
        "prompt": "分析 src/ 目录下的代码，找出潜在的改进点",
        "timeout": 300,
    }

    try:
        task = await create_task(task_config)
        print(f"任务创建成功: {task.id}")
        print(f"任务状态: {task.status}")

        # 等待任务完成
        while task.status in ["pending", "running"]:
            await asyncio.sleep(1)
            task = await get_task_status(task.id)
            print(f"任务状态更新: {task.status}")

        print(f"任务完成，结果: {task.output}")
    except Exception as e:
        print(f"任务管理失败: {e}")


async def multi_agent_coordination():
    """多 Agent 协调示例"""
    print("\n" + "=" * 50)
    print("示例 4: 多 Agent 协调")
    print("=" * 50)

    from src.integrations.openharness import (
        AgentCoordinator,
        create_worker_agent,
        create_specialist_agent,
    )

    # 创建协调器
    coordinator = AgentCoordinator()

    # 创建专业 Agent
    code_agent = await create_specialist_agent(
        name="代码审查员",
        specialty="code_review",
        description="专门审查代码质量和最佳实践"
    )

    doc_agent = await create_specialist_agent(
        name="文档生成器",
        specialty="documentation",
        description="自动生成代码文档"
    )

    print(f"创建 Agent: {code_agent.name}, {doc_agent.name}")

    # 委派任务
    task1 = await coordinator.delegate_task(
        agent_id=code_agent.id,
        task="审查 src/integrations/openharness/ 目录的代码",
        priority="high"
    )

    task2 = await coordinator.delegate_task(
        agent_id=doc_agent.id,
        task="为 OpenHarness 集成生成 API 文档",
        priority="medium"
    )

    print(f"委派任务: {task1.id}, {task2.id}")

    # 监控任务状态
    await coordinator.monitor_tasks()


async def skill_usage():
    """技能使用示例"""
    print("\n" + "=" * 50)
    print("示例 5: 技能加载和使用")
    print("=" * 50)

    from src.integrations.openharness import openharness_engine

    # 加载技能
    skills_to_load = ["code-review", "data-analysis", "document-generator"]

    for skill_name in skills_to_load:
        success = await openharness_engine.load_skill(skill_name)
        if success:
            print(f"技能加载成功: {skill_name}")
        else:
            print(f"技能加载失败: {skill_name}")

    # 使用技能执行任务
    prompt = "使用 code-review 技能审查以下代码: def hello(): print('world')"

    try:
        result = await openharness_engine.execute(prompt)
        print(f"技能执行结果: {result}")
    except Exception as e:
        print(f"技能执行失败: {e}")


async def memory_persistence():
    """记忆持久化示例"""
    print("\n" + "=" * 50)
    print("示例 6: 记忆持久化")
    print("=" * 50)

    from src.integrations.openharness.memory import create_memory_manager

    # 创建记忆管理器
    memory_manager = create_memory_manager()

    # 写入记忆
    memory_entry = {
        "type": "fact",
        "content": "OpenHarness 是一个轻量级 Agent 基础设施",
        "tags": ["openharness", "agent", "infrastructure"],
        "importance": 0.9,
    }

    memory_id = await memory_manager.add_memory(memory_entry)
    print(f"记忆写入成功: {memory_id}")

    # 搜索记忆
    results = await memory_manager.search_memories("Agent 基础设施")
    print(f"搜索结果: {len(results)} 条记忆")
    for result in results:
        print(f"  - {result.content}")

    # 获取相关记忆
    context = await memory_manager.get_relevant_memories("OpenHarness 功能")
    print(f"相关记忆: {len(context)} 条")


async def main():
    """主函数"""
    print("OpenHarness 快速入门示例")
    print("=" * 50)

    # 运行所有示例
    await basic_agent_execution()
    await streaming_execution()
    await task_management()
    await multi_agent_coordination()
    await skill_usage()
    await memory_persistence()

    print("\n" + "=" * 50)
    print("所有示例执行完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
