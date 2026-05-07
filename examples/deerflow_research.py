#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeerFlow 研究任务示例

本示例展示如何使用 DeerFlow 执行复杂的研究任务：
1. 深度研究分析
2. 多源信息收集和整合
3. 研究报告生成
4. 数据可视化和分析
5. 自动化研究流程

运行前请确保：
1. 已安装 DeerFlow: pip install deerflow
2. 已配置 .env.deerflow 文件（包含 API 密钥）
3. Docker 服务正在运行
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

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


class ResearchTask:
    """研究任务类"""

    def __init__(self, topic: str, flow):
        self.topic = topic
        self.flow = flow
        self.results = {}
        self.timestamp = datetime.now()

    async def execute(self) -> Dict[str, Any]:
        """执行完整的研究流程"""
        print(f"\n开始研究: {self.topic}")
        print("=" * 60)

        # 1. 初步信息收集
        await self._collect_initial_info()

        # 2. 深度分析
        await self._deep_analysis()

        # 3. 生成报告
        await self._generate_report()

        return self.results

    async def _collect_initial_info(self):
        """收集初步信息"""
        print("\n[阶段 1] 收集初步信息...")

        collector = self.flow.create_subagent(
            name="info_collector",
            instructions="""
            你是信息收集专家。你的任务是：
            1. 收集关于主题的基本信息
            2. 识别关键概念和术语
            3. 列出重要的相关主题
            4. 提供信息来源建议

            输出格式要结构化，便于后续分析。
            """,
        )

        result = await collector.execute_async(
            f"收集关于'{self.topic}'的基本信息和背景知识"
        )

        self.results["initial_info"] = {
            "content": result.response,
            "timestamp": datetime.now().isoformat(),
        }

        print("✓ 初步信息收集完成")

    async def _deep_analysis(self):
        """深度分析"""
        print("\n[阶段 2] 深度分析...")

        # 创建多个分析专家
        analysts = {
            "technical": self.flow.create_subagent(
                name="technical_analyst",
                instructions="""
                你是技术分析专家。专注于：
                1. 技术原理和架构分析
                2. 技术优势和局限性
                3. 技术实现细节
                4. 技术发展趋势
                """,
            ),
            "market": self.flow.create_subagent(
                name="market_analyst",
                instructions="""
                你是市场分析专家。专注于：
                1. 市场规模和增长趋势
                2. 主要参与者和竞争格局
                3. 市场需求和驱动因素
                4. 商业机会和挑战
                """,
            ),
            "application": self.flow.create_subagent(
                name="application_analyst",
                instructions="""
                你是应用分析专家。专注于：
                1. 实际应用场景
                2. 成功案例研究
                3. 实施挑战和解决方案
                4. 最佳实践建议
                """,
            ),
        }

        # 并行执行分析
        tasks = []
        for name, analyst in analysts.items():
            task = analyst.execute_async(
                f"基于以下信息，对'{self.topic}'进行{name}分析:\n{self.results['initial_info']['content']}"
            )
            tasks.append((name, task))

        # 等待所有分析完成
        for name, task in tasks:
            result = await task
            self.results[f"{name}_analysis"] = {
                "content": result.response,
                "timestamp": datetime.now().isoformat(),
            }

        print("✓ 深度分析完成")

    async def _generate_report(self):
        """生成研究报告"""
        print("\n[阶段 3] 生成研究报告...")

        # 整合所有分析结果
        synthesis = self.flow.create_subagent(
            name="report_synthesizer",
            instructions="""
            你是报告撰写专家。你的任务是：
            1. 整合多个分析来源的信息
            2. 生成结构化的研究报告
            3. 提供执行摘要
            4. 给出行动建议

            报告应该专业、全面、易于理解。
            """,
        )

        # 构建综合分析内容
        analysis_content = f"""
主题: {self.topic}

初步信息:
{self.results['initial_info']['content']}

技术分析:
{self.results.get('technical_analysis', {}).get('content', '')}

市场分析:
{self.results.get('market_analysis', {}).get('content', '')}

应用分析:
{self.results.get('application_analysis', {}).get('content', '')}
"""

        result = await synthesis.execute_async(
            f"基于以下分析内容，生成一份完整的研究报告:\n{analysis_content}"
        )

        self.results["final_report"] = {
            "content": result.response,
            "timestamp": datetime.now().isoformat(),
        }

        print("✓ 研究报告生成完成")


def example_1_single_topic_research():
    """示例 1: 单一主题深度研究"""
    print("\n" + "=" * 60)
    print("示例 1: 单一主题深度研究")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        # 初始化
        print("\n[1] 初始化 DeerFlow...")
        flow = DeerFlow()
        print("✓ DeerFlow 初始化成功")

        # 创建研究任务
        topic = "生成式人工智能在企业中的应用"
        print(f"\n[2] 创建研究任务: {topic}")

        research = ResearchTask(topic, flow)

        # 执行研究
        print("\n[3] 执行研究流程...")
        results = asyncio.run(research.execute())

        # 显示结果
        print("\n[4] 研究结果:")
        print("=" * 60)
        print(f"\n主题: {topic}")
        print(f"研究时间: {research.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n报告内容:\n{results['final_report']['content'][:1000]}...")
        print("=" * 60)

        # 保存结果
        output_file = Path("research_output.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 研究结果已保存到: {output_file}")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_2_comparative_research():
    """示例 2: 对比研究"""
    print("\n" + "=" * 60)
    print("示例 2: 对比研究")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # 定义对比主题
        topics = [
            "Python vs JavaScript 在数据科学中的应用",
            "传统机器学习 vs 深度学习",
            "单体架构 vs 微服务架构",
        ]

        print(f"\n[1] 准备对比研究: {len(topics)} 个主题")

        # 为每个主题创建研究任务
        researches = []
        for topic in topics:
            research = ResearchTask(topic, flow)
            researches.append(research)

        # 并行执行所有研究
        print("\n[2] 并行执行研究...")

        async def run_all_researches():
            tasks = [r.execute() for r in researches]
            return await asyncio.gather(*tasks)

        all_results = asyncio.run(run_all_researches())

        # 生成对比报告
        print("\n[3] 生成对比分析报告...")

        comparator = flow.create_subagent(
            name="comparator",
            instructions="""
            你是对比分析专家。你的任务是：
            1. 对比多个研究主题的结果
            2. 识别共同点和差异
            3. 提供综合评估
            4. 给出选择建议
            """,
        )

        comparison_content = "\n\n".join(
            f"主题 {i+1}: {topics[i]}\n{result['final_report']['content'][:500]}"
            for i, result in enumerate(all_results)
        )

        comparison_result = comparator.execute(
            f"基于以下研究内容，生成对比分析报告:\n{comparison_content}"
        )

        print("\n[4] 对比分析结果:")
        print("=" * 60)
        print(comparison_result.response)
        print("=" * 60)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_3_data_driven_research():
    """示例 3: 数据驱动的研究"""
    print("\n" + "=" * 60)
    print("示例 3: 数据驱动的研究")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        print("\n[1] 生成研究数据...")

        # 在沙箱中生成模拟数据
        data_generation_code = """
import json
import random
from datetime import datetime, timedelta

# 生成模拟的科技公司数据
companies = ["TechCorp", "InnovateLtd", "FutureTech", "DataSystems", "CloudNine"]
metrics = ["revenue", "users", "satisfaction", "growth"]

# 生成时间序列数据
data = []
base_date = datetime(2023, 1, 1)

for company in companies:
    for i in range(12):  # 12个月
        date = base_date + timedelta(days=30*i)
        data.append({
            "company": company,
            "date": date.strftime("%Y-%m"),
            "revenue": random.uniform(1, 10),  # 百万美元
            "users": random.randint(10000, 1000000),
            "satisfaction": random.uniform(3.5, 5.0),
            "growth": random.uniform(-0.1, 0.5)
        })

# 统计分析
from collections import defaultdict

company_stats = defaultdict(lambda: {"total_revenue": 0, "avg_users": 0, "avg_satisfaction": 0})
for record in data:
    company = record["company"]
    company_stats[company]["total_revenue"] += record["revenue"]
    company_stats[company]["avg_users"] += record["users"]
    company_stats[company]["avg_satisfaction"] += record["satisfaction"]

# 计算平均值
for company in company_stats:
    company_stats[company]["avg_users"] /= 12
    company_stats[company]["avg_satisfaction"] /= 12

print("=== 生成的研究数据 ===")
print(f"数据点数量: {len(data)}")
print(f"公司数量: {len(companies)}")
print("\n公司统计:")
for company, stats in company_stats.items():
    print(f"  {company}:")
    print(f"    年度总收入: ${stats['total_revenue']:.2f}M")
    print(f"    平均用户数: {stats['avg_users']:,.0f}")
    print(f"    平均满意度: {stats['avg_satisfaction']:.2f}")

# 输出JSON格式
print("\n=== JSON格式数据 ===")
print(json.dumps(data[:5], indent=2))  # 只显示前5条
"""

        result = flow.execute(data_generation_code, language="python")
        print(result.output)

        print("\n[2] 基于数据进行研究分析...")

        # 创建数据分析师
        data_analyst = flow.create_subagent(
            name="data_analyst",
            instructions="""
            你是数据分析专家。你的任务是：
            1. 分析提供的数据
            2. 识别趋势和模式
            3. 提供数据驱动的见解
            4. 生成可视化建议
            """,
        )

        analysis_result = data_analyst.execute(
            f"基于以下数据进行分析:\n{result.output}\n\n请提供详细的分析报告。"
        )

        print("\n[3] 数据分析结果:")
        print("=" * 60)
        print(analysis_result.response)
        print("=" * 60)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_4_iterative_research():
    """示例 4: 迭代式研究"""
    print("\n" + "=" * 60)
    print("示例 4: 迭代式研究")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        topic = "区块链技术"
        print(f"\n[1] 开始迭代研究: {topic}")

        # 初始研究
        researcher = flow.create_subagent(
            name="iterative_researcher",
            instructions="""
            你是迭代研究专家。你的任务是：
            1. 基于当前信息进行研究
            2. 识别需要深入探索的问题
            3. 提出下一步研究方向
            4. 持续改进研究质量
            """,
        )

        context = {}
        iterations = 3

        for i in range(iterations):
            print(f"\n[迭代 {i+1}/{iterations}]")

            # 构建查询
            if i == 0:
                query = f"开始对'{topic}'进行初步研究"
            else:
                query = f"基于之前的发现，深入探索'{topic}'的以下方面: {context.get('next_questions', '更多细节')}"

            result = researcher.execute(query, context=context)

            print(f"  发现: {result.response[:200]}...")

            # 更新上下文
            context[f"iteration_{i+1}"] = {
                "query": query,
                "response": result.response,
                "actions": result.actions_taken,
            }

            # 提取下一步问题
            if hasattr(result, 'next_questions'):
                context['next_questions'] = result.next_questions

        # 生成最终综合报告
        print("\n[2] 生成综合报告...")

        synthesizer = flow.create_subagent(
            name="synthesizer",
            instructions="整合多次迭代的研究结果，生成最终报告。",
        )

        final_report = synthesizer.execute(
            f"基于以下迭代研究结果生成综合报告:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )

        print("\n[3] 最终报告:")
        print("=" * 60)
        print(final_report.response)
        print("=" * 60)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_5_automated_research_pipeline():
    """示例 5: 自动化研究流程"""
    print("\n" + "=" * 60)
    print("示例 5: 自动化研究流程")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        print("\n[1] 定义自动化研究流程...")

        # 定义研究流程
        research_pipeline = {
            "steps": [
                {"name": "topic_analysis", "description": "主题分析"},
                {"name": "literature_review", "description": "文献综述"},
                {"name": "data_collection", "description": "数据收集"},
                {"name": "analysis", "description": "深度分析"},
                {"name": "report_generation", "description": "报告生成"},
            ]
        }

        topic = "边缘计算在物联网中的应用"
        print(f"\n研究主题: {topic}")
        print(f"流程步骤: {len(research_pipeline['steps'])}")

        # 创建流程管理器
        pipeline_manager = flow.create_subagent(
            name="pipeline_manager",
            instructions="""
            你是研究流程管理专家。你的任务是：
            1. 管理多步骤研究流程
            2. 确保每个步骤的质量
            3. 协调各步骤之间的衔接
            4. 监控整体进度
            """,
        )

        results = {}

        # 执行每个步骤
        for i, step in enumerate(research_pipeline["steps"], 1):
            print(f"\n[步骤 {i}/{len(research_pipeline['steps'])}] {step['description']}")

            step_result = pipeline_manager.execute(
                f"""
                执行研究流程的第 {i} 步: {step['name']} - {step['description']}
                研究主题: {topic}
                之前步骤的结果: {json.dumps(results, ensure_ascii=False) if results else '无'}

                请完成此步骤并输出结果。
                """
            )

            results[step["name"]] = {
                "content": step_result.response,
                "status": "completed",
            }

            print(f"  ✓ 步骤完成")

        # 生成最终输出
        print("\n[2] 生成最终研究报告...")

        final_synthesizer = flow.create_subagent(
            name="final_synthesizer",
            instructions="整合所有研究步骤的结果，生成最终的研究报告。",
        )

        final_report = final_synthesizer.execute(
            f"基于以下研究流程结果生成最终报告:\n{json.dumps(results, ensure_ascii=False, indent=2)}"
        )

        print("\n[3] 自动化研究完成!")
        print("=" * 60)
        print(f"\n最终报告摘要:\n{final_report.response[:800]}...")
        print("=" * 60)

        # 保存完整结果
        output = {
            "topic": topic,
            "pipeline": research_pipeline,
            "results": results,
            "final_report": final_report.response,
            "timestamp": datetime.now().isoformat(),
        }

        output_file = Path("automated_research_result.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 完整结果已保存到: {output_file}")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeerFlow 研究任务示例")
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
        ("单一主题深度研究", example_1_single_topic_research),
        ("对比研究", example_2_comparative_research),
        ("数据驱动的研究", example_3_data_driven_research),
        ("迭代式研究", example_4_iterative_research),
        ("自动化研究流程", example_5_automated_research_pipeline),
    ]

    results = []
    for name, func in examples:
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ 示例 '{name}' 失败: {e}")
            results.append((name, False))

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
