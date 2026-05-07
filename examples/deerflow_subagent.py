#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeerFlow 子代理使用示例

本示例展示如何使用 DeerFlow 的子代理功能：
1. 创建子代理
2. 分配任务给子代理
3. 子代理间的协作
4. 使用工具扩展子代理能力
5. 并行执行多个子代理任务

运行前请确保：
1. 已安装 DeerFlow: pip install deerflow
2. 已配置 .env.deerflow 文件（包含 API 密钥）
3. Docker 服务正在运行
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv

env_path = project_root / ".env.deerflow"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ 已加载环境变量: {env_path}")
else:
    print(f"⚠ 未找到环境变量文件: {env_path}")
    print("  将使用默认配置")


def example_1_create_subagent():
    """示例 1: 创建和使用子代理"""
    print("\n" + "=" * 60)
    print("示例 1: 创建和使用子代理")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        # 初始化 DeerFlow
        print("\n[1] 初始化 DeerFlow...")
        flow = DeerFlow()
        print("✓ DeerFlow 初始化成功")

        # 创建子代理
        print("\n[2] 创建研究子代理...")
        researcher = flow.create_subagent(
            name="researcher",
            instructions="""
            你是一个专业的研究分析师。你的任务是：
            1. 分析给定的主题
            2. 提供结构化的分析报告
            3. 列出关键要点和见解
            4. 给出实用的建议

            请用中文回答，保持客观和专业。
            """,
        )
        print("✓ 子代理创建成功")

        # 分配任务
        print("\n[3] 分配研究任务...")
        task = "分析远程工作对软件开发团队生产力的影响"

        result = researcher.execute(task)

        # 显示结果
        print("\n[4] 任务执行结果:")
        print("  " + "-" * 50)
        print(f"  响应:\n{result.response}")
        print(f"\n  执行的操作: {result.actions_taken}")
        print(f"  迭代次数: {result.iterations}")
        print(f"  执行时间: {result.execution_time:.2f} 秒")
        print(f"  使用令牌数: {result.tokens_used}")
        print("  " + "-" * 50)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_2_multi_agent_collaboration():
    """示例 2: 多代理协作"""
    print("\n" + "=" * 60)
    print("示例 2: 多代理协作")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # 创建多个专业子代理
        print("\n[1] 创建专业子代理团队...")

        # 数据分析师
        data_analyst = flow.create_subagent(
            name="data_analyst",
            instructions="""
            你是数据分析师。专注于：
            1. 数据收集和整理
            2. 统计分析和可视化
            3. 发现数据模式和趋势
            4. 提供数据驱动的见解

            输出格式要清晰，包含具体数字和图表描述。
            """,
        )

        # 内容撰写员
        content_writer = flow.create_subagent(
            name="content_writer",
            instructions="""
            你是专业的内容撰写员。专注于：
            1. 将技术内容转化为易懂的文章
            2. 创建引人入胜的标题和结构
            3. 确保内容准确且易于理解
            4. 优化内容的可读性和吸引力

            使用中文撰写，风格专业但易懂。
            """,
        )

        # 审核员
        reviewer = flow.create_subagent(
            name="reviewer",
            instructions="""
            你是内容审核员。专注于：
            1. 检查内容的准确性和完整性
            2. 评估内容的质量和一致性
            3. 提出改进建议
            4. 确保内容符合标准

            提供建设性的反馈和评分。
            """,
        )

        print("✓ 创建了 3 个专业子代理")

        # 模拟协作流程
        topic = "人工智能在医疗诊断中的应用"

        print(f"\n[2] 主题: {topic}")
        print("\n[3] 开始协作流程...")

        # 步骤 1: 数据分析
        print("\n  → 数据分析师收集信息...")
        analysis_result = data_analyst.execute(
            f"收集和分析关于'{topic}'的关键数据、统计数据和市场信息"
        )
        print(f"  ✓ 数据分析完成 (用时: {analysis_result.execution_time:.2f}s)")

        # 步骤 2: 内容撰写
        print("\n  → 内容撰写员创作文章...")
        writing_result = content_writer.execute(
            f"基于以下分析数据撰写一篇关于'{topic}'的文章:\n{analysis_result.response}"
        )
        print(f"  ✓ 内容撰写完成 (用时: {writing_result.execution_time:.2f}s)")

        # 步骤 3: 内容审核
        print("\n  → 审核员评估内容...")
        review_result = reviewer.execute(
            f"审核以下文章并提供反馈:\n{writing_result.response}"
        )
        print(f"  ✓ 内容审核完成 (用时: {review_result.execution_time:.2f}s)")

        # 显示最终结果
        print("\n[4] 协作结果:")
        print("  " + "=" * 50)
        print("  【数据分析结果】")
        print(f"  {analysis_result.response[:300]}...")
        print("\n  【文章内容】")
        print(f"  {writing_result.response[:300]}...")
        print("\n  【审核反馈】")
        print(f"  {review_result.response[:300]}...")
        print("  " + "=" * 50)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_3_subagent_with_tools():
    """示例 3: 使用工具扩展子代理"""
    print("\n" + "=" * 60)
    print("示例 3: 使用工具扩展子代理")
    print("=" * 60)

    try:
        from deerflow import DeerFlow
        from deerflow.tools import Tool, ToolRegistry

        flow = DeerFlow()

        # 定义自定义工具
        print("\n[1] 创建自定义工具...")

        class CalculatorTool(Tool):
            name = "calculator"
            description = "执行数学计算"

            def execute(self, expression: str) -> Dict[str, Any]:
                """执行数学表达式"""
                try:
                    # 安全计算
                    allowed_names = {
                        "abs": abs,
                        "max": max,
                        "min": min,
                        "sum": sum,
                        "pow": pow,
                        "round": round,
                    }
                    result = eval(expression, {"__builtins__": {}}, allowed_names)
                    return {"success": True, "result": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}

        class DataFormatTool(Tool):
            name = "data_formatter"
            description = "格式化数据"

            def execute(self, data: str, format_type: str = "json") -> Dict[str, Any]:
                """格式化数据"""
                try:
                    import json

                    if format_type == "json":
                        parsed = json.loads(data)
                        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                        return {"success": True, "formatted": formatted}
                    elif format_type == "table":
                        lines = data.strip().split("\n")
                        formatted = "\n".join(f"| {line} |" for line in lines)
                        return {"success": True, "formatted": formatted}
                    else:
                        return {"success": False, "error": "不支持的格式类型"}
                except Exception as e:
                    return {"success": False, "error": str(e)}

        # 注册工具
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(DataFormatTool())

        print("✓ 创建了 2 个自定义工具")

        # 创建带工具的子代理
        print("\n[2] 创建带工具的子代理...")
        assistant = flow.create_subagent(
            name="math_assistant",
            instructions="""
            你是数学助手，可以使用计算工具帮助用户。
            当需要进行复杂计算时，使用 calculator 工具。
            当需要格式化数据时，使用 data_formatter 工具。

            始终保持友好和专业的态度。
            """,
            tools=registry.get_tools(),
        )
        print("✓ 子代理创建成功，已绑定工具")

        # 执行任务
        print("\n[3] 执行需要工具的任务...")
        task = """
        请帮我完成以下任务：
        1. 计算: (100 * 23.5 + 450) / 12.5
        2. 将以下数据格式化为 JSON:
           {"name": "产品A", "price": 99.99, "quantity": 100}
        """

        result = assistant.execute(task)

        print("\n[4] 执行结果:")
        print("  " + "-" * 50)
        print(f"  {result.response}")
        print("  " + "-" * 50)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def example_4_parallel_subagents():
    """示例 4: 并行执行多个子代理"""
    print("\n" + "=" * 60)
    print("示例 4: 并行执行多个子代理")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # 创建多个子代理
        print("\n[1] 创建并行子代理...")

        agents = []
        topics = [
            "机器学习的最新发展趋势",
            "区块链技术在金融领域的应用",
            "物联网在智慧城市中的作用",
        ]

        for i, topic in enumerate(topics, 1):
            agent = flow.create_subagent(
                name=f"researcher_{i}",
                instructions=f"""
                你是专业的研究分析师 #{i}。
                专注于快速、准确地分析技术主题。
                提供简洁但全面的分析结果。
                """,
            )
            agents.append((agent, topic))

        print(f"✓ 创建了 {len(agents)} 个子代理")

        # 并行执行任务
        print("\n[2] 并行执行任务...")
        print(f"  任务列表: {topics}")

        async def execute_agent(agent, topic):
            """执行单个代理任务"""
            start_time = asyncio.get_event_loop().time()
            result = await agent.execute_async(f"分析主题: {topic}")
            end_time = asyncio.get_event_loop().time()
            return {
                "topic": topic,
                "result": result,
                "elapsed": end_time - start_time,
            }

        # 同时执行所有任务
        tasks = [execute_agent(agent, topic) for agent, topic in agents]
        results = await asyncio.gather(*tasks)

        print("\n[3] 并行执行结果:")
        print("  " + "=" * 50)

        for i, res in enumerate(results, 1):
            print(f"\n  【任务 {i}】{res['topic']}")
            print(f"  执行时间: {res['elapsed']:.2f} 秒")
            print(f"  结果摘要: {res['result'].response[:200]}...")

        print("  " + "=" * 50)

        # 计算总时间
        total_time = sum(r["elapsed"] for r in results)
        print(f"\n  总执行时间: {total_time:.2f} 秒")
        print(f"  平均每个任务: {total_time / len(results):.2f} 秒")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_5_memory_and_context():
    """示例 5: 内存和上下文管理"""
    print("\n" + "=" * 60)
    print("示例 5: 内存和上下文管理")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # 创建带内存的子代理
        print("\n[1] 创建带内存的子代理...")
        assistant = flow.create_subagent(
            name="contextual_assistant",
            instructions="""
            你是智能助手，能够记住之前的对话内容。
            利用上下文信息提供连贯、个性化的回答。
            """,
        )
        print("✓ 子代理创建成功")

        # 多轮对话
        print("\n[2] 开始多轮对话...")

        conversation = [
            "你好，我叫张三，是一名软件工程师。",
            "请介绍一下适合我的技术发展方向。",
            "基于我的背景，推荐一些学习资源。",
            "总结一下我们刚才讨论的内容。",
        ]

        context = {}
        for i, message in enumerate(conversation, 1):
            print(f"\n  [回合 {i}]")
            print(f"  用户: {message}")

            result = assistant.execute(
                task=message,
                context=context,
            )

            print(f"  助手: {result.response[:200]}...")

            # 更新上下文
            context[f"turn_{i}"] = {
                "user": message,
                "assistant": result.response,
            }

        print("\n[3] 对话完成")
        print(f"  总回合数: {len(conversation)}")
        print(f"  上下文键: {list(context.keys())}")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeerFlow 子代理使用示例")
    print("=" * 60)

    # 检查 DeerFlow 是否可用
    try:
        from deerflow import DeerFlow

        print("\n✓ DeerFlow 包已安装")
    except ImportError:
        print("\n✗ DeerFlow 包未安装")
        print("  请运行: pip install deerflow")
        return 1

    # 运行所有示例
    examples = [
        ("创建和使用子代理", example_1_create_subagent),
        ("多代理协作", example_2_multi_agent_collaboration),
        ("使用工具扩展", example_3_subagent_with_tools),
        ("内存和上下文", example_5_memory_and_context),
    ]

    results = []
    for name, func in examples:
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ 示例 '{name}' 失败: {e}")
            results.append((name, False))

    # 运行异步示例
    print("\n" + "=" * 60)
    print("运行异步示例...")
    print("=" * 60)

    try:
        success = asyncio.run(example_4_parallel_subagents())
        results.append(("并行子代理", success))
    except Exception as e:
        print(f"\n✗ 异步示例失败: {e}")
        results.append(("并行子代理", False))

    # 显示总结
    print("\n" + "=" * 60)
    print("示例运行总结")
    print("=" * 60)

    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {name:<20} {status}")

    success_count = sum(1 for _, s in results if s)
    total_count = len(results)

    print(f"\n总计: {success_count}/{total_count} 个示例成功")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
