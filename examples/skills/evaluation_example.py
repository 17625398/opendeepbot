"""
评估框架使用示例

这个示例展示了如何在 DeepTutor 中使用评估框架：
- 基础评估器 (BasicEvaluator) - 准确率、响应时间、Token使用等指标
- LLM-as-a-Judge (LLMJudgeEvaluator) - 使用LLM进行智能评估
- 成对比较 - 比较两个输出的质量
- 评分标准生成 - 自动生成评估标准
- 偏见检测和减少 - 识别并减少评估偏见
- 组合评估器 - 综合多个评估器的结果

运行说明:
    1. 确保已安装 DeepTutor 依赖
    2. 从项目根目录运行: python examples/skills/evaluation_example.py
    3. 或直接运行: python evaluation_example.py

功能演示:
    - 基础指标评估（准确率、响应时间、Token使用）
    - LLM直接评分
    - 成对比较（pairwise comparison）
    - 评分标准生成
    - 偏见检测和减少
    - 组合多个评估器
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.evaluation import (
    BasicEvaluator,
    LLMJudgeEvaluator,
    CompositeEvaluator,
    EvaluationMetric,
    EvaluationResult,
    MetricType,
)
from src.agents.evaluation.base import Evaluator


# 示例数据
SAMPLE_QA_PAIRS = [
    {
        "question": "什么是Python？",
        "answer": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。它以简洁、易读的语法著称，广泛应用于Web开发、数据科学、人工智能等领域。",
        "expected": "Python是一种高级编程语言，由Guido van Rossum创建，以简洁语法著称。",
    },
    {
        "question": "解释机器学习",
        "answer": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习而无需明确编程。",
        "expected": "机器学习是AI的子领域，让计算机从数据中学习模式。",
    },
    {
        "question": "什么是深度学习？",
        "answer": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。",
        "expected": "深度学习使用神经网络进行学习。",
    },
]

SAMPLE_RESPONSES_FOR_COMPARISON = {
    "prompt": "解释什么是API",
    "response_a": "API是应用程序接口，允许不同的软件系统相互通信。",
    "response_b": """API（Application Programming Interface，应用程序编程接口）是一组定义、协议和工具，用于构建软件应用程序。

API规定了软件组件之间如何交互，使得开发者可以使用预定义的功能而无需了解其内部实现细节。

主要特点：
1. 封装性：隐藏实现细节
2. 标准化：提供统一的接口
3. 可重用性：避免重复开发

常见类型包括REST API、GraphQL API等。""",
}


class MockBasicEvaluator(BasicEvaluator):
    """模拟基础评估器（用于演示）"""

    async def evaluate(
        self,
        input_data: str,
        output_data: str,
        expected_output: str = None,
        **kwargs
    ) -> EvaluationResult:
        """执行基础评估"""
        import uuid
        import time

        start_time = time.time()
        eval_id = str(uuid.uuid4())

        # 模拟计算指标
        metrics: List[EvaluationMetric] = []

        # 文本相似度（简化版）
        if expected_output:
            similarity = self._calculate_similarity(output_data, expected_output)
            metrics.append(EvaluationMetric(
                name="text_similarity",
                value=similarity,
                metric_type=MetricType.ACCURACY,
                weight=1.5,
                description="文本相似度",
            ))

        # 响应长度
        metrics.append(EvaluationMetric(
            name="response_length",
            value=len(output_data),
            metric_type=MetricType.CUSTOM,
            weight=0.5,
            description="响应长度（字符数）",
        ))

        # 词汇多样性
        diversity = self._calculate_diversity(output_data)
        metrics.append(EvaluationMetric(
            name="lexical_diversity",
            value=diversity,
            metric_type=MetricType.CUSTOM,
            weight=1.0,
            description="词汇多样性",
        ))

        # 包含关键信息检查
        if expected_output:
            key_info_score = self._check_key_information(output_data, expected_output)
            metrics.append(EvaluationMetric(
                name="key_information_coverage",
                value=key_info_score,
                metric_type=MetricType.RECALL,
                weight=2.0,
                description="关键信息覆盖率",
            ))

        duration_ms = (time.time() - start_time) * 1000

        # 计算综合评分
        total_weight = sum(m.weight for m in metrics)
        overall_score = (
            sum(m.value * m.weight for m in metrics) / total_weight
            if total_weight > 0 else 0.0
        )

        result = EvaluationResult(
            eval_id=eval_id,
            input_text=input_data,
            output_text=output_data,
            expected_output=expected_output,
            metrics=metrics,
            overall_score=overall_score,
            metadata={
                "evaluator_type": "basic",
                "input_length": len(input_data),
                "output_length": len(output_data),
            },
            duration_ms=duration_ms,
        )

        self._record_metrics(result)
        return result

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版Jaccard）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _calculate_diversity(self, text: str) -> float:
        """计算词汇多样性"""
        words = text.lower().split()
        if not words:
            return 0.0

        unique_words = set(words)
        return len(unique_words) / len(words)

    def _check_key_information(self, output: str, expected: str) -> float:
        """检查关键信息覆盖率"""
        expected_words = set(expected.lower().split())
        output_words = set(output.lower().split())

        if not expected_words:
            return 1.0

        covered = expected_words & output_words
        return len(covered) / len(expected_words)


async def demonstrate_basic_evaluation():
    """演示基础评估"""
    print("=" * 60)
    print("演示 1: 基础评估器 (BasicEvaluator)")
    print("=" * 60)
    print("\n特性说明:")
    print("  - 文本相似度评估")
    print("  - 词汇多样性分析")
    print("  - 关键信息覆盖率")
    print("  - 响应长度统计")

    evaluator = MockBasicEvaluator()

    print("\n📊 评估问答对:")
    for i, qa in enumerate(SAMPLE_QA_PAIRS, 1):
        print(f"\n  问题 {i}: {qa['question']}")

        result = await evaluator.evaluate(
            input_data=qa['question'],
            output_data=qa['answer'],
            expected_output=qa['expected'],
        )

        print(f"  综合评分: {result.overall_score:.2f}")
        print(f"  评估耗时: {result.duration_ms:.2f}ms")
        print("  指标详情:")
        for metric in result.metrics:
            print(f"    - {metric.name}: {metric.value:.4f} (权重: {metric.weight})")

    print("\n📈 评估统计:")
    stats = evaluator.get_statistics()
    print(f"  - 评估次数: {stats['eval_count']}")
    print(f"  - 平均评分: {stats['avg_score']:.2f}")
    print(f"  - 最高评分: {stats['max_score']:.2f}")
    print(f"  - 最低评分: {stats['min_score']:.2f}")


async def demonstrate_llm_judge_evaluation():
    """演示LLM-as-a-Judge评估"""
    print("\n" + "=" * 60)
    print("演示 2: LLM-as-a-Judge 评估")
    print("=" * 60)
    print("\n特性说明:")
    print("  - 使用LLM进行智能评估")
    print("  - 多维度评分")
    print("  - 详细评估理由")
    print("  - 偏见检测")

    evaluator = LLMJudgeEvaluator(
        name="LLM-Judge-Demo",
        detect_bias=True,
        num_judges=1,  # 演示使用单次评判
    )

    print("\n🤖 LLM评估问答质量:")
    qa = SAMPLE_QA_PAIRS[0]
    print(f"\n  问题: {qa['question']}")
    print(f"  回答: {qa['answer'][:80]}...")

    result = await evaluator.evaluate(
        input_data=qa['question'],
        output_data=qa['answer'],
        criteria="准确性、完整性、清晰度、有用性",
    )

    print(f"\n  综合评分: {result.overall_score:.2f}")
    print(f"  评估耗时: {result.duration_ms:.2f}ms")
    print("  指标详情:")
    for metric in result.metrics:
        print(f"    - {metric.name}: {metric.value:.4f} (权重: {metric.weight})")

    # 显示详细评分信息
    if 'score_details' in result.metadata:
        details = result.metadata['score_details']
        print("\n  LLM评分详情:")
        print(f"    - 原始分数: {details.get('score', 'N/A')}")
        if 'dimensions' in details:
            print("    - 维度评分:")
            for dim, score in details['dimensions'].items():
                print(f"      - {dim}: {score}")

    # 偏见检测
    if result.metadata.get('bias_detected'):
        print(f"\n  ⚠️ 检测到的偏见: {result.metadata['bias_detected']}")
    else:
        print("\n  ✓ 未检测到明显偏见")


async def demonstrate_direct_scoring():
    """演示直接评分"""
    print("\n" + "=" * 60)
    print("演示 3: 直接评分")
    print("=" * 60)

    evaluator = LLMJudgeEvaluator()

    print("\n🎯 对单个回答进行评分:")

    test_cases = [
        {
            "prompt": "解释什么是REST API",
            "response": "REST API是一种基于HTTP协议的API设计风格，使用URL定位资源，使用HTTP方法（GET、POST、PUT、DELETE）操作资源。",
            "criteria": "准确性、简洁性、实用性",
        },
        {
            "prompt": "解释什么是REST API",
            "response": "REST API就是网络接口。",
            "criteria": "准确性、简洁性、实用性",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n  测试用例 {i}:")
        print(f"    回答: {case['response'][:60]}...")

        score_result = await evaluator.score_direct(
            prompt=case['prompt'],
            response=case['response'],
            criteria=case['criteria'],
            return_details=True,
        )

        print(f"    总分: {score_result['score']:.1f}/10")
        if 'dimensions' in score_result:
            print("    维度评分:")
            for dim, value in score_result['dimensions'].items():
                print(f"      - {dim}: {value:.1f}")
        if 'reasoning' in score_result:
            print(f"    评估理由: {score_result['reasoning'][:100]}...")


async def demonstrate_pairwise_comparison():
    """演示成对比较"""
    print("\n" + "=" * 60)
    print("演示 4: 成对比较 (Pairwise Comparison)")
    print("=" * 60)
    print("\n特性说明:")
    print("  - 比较两个回答的质量")
    print("  - 自动检测位置偏见")
    print("  - 提供置信度评估")

    evaluator = LLMJudgeEvaluator(
        mitigate_bias=True,  # 启用偏见减少
    )

    print("\n⚖️ 比较两个回答:")
    print(f"\n  问题: {SAMPLE_RESPONSES_FOR_COMPARISON['prompt']}")

    print("\n  回答 A:")
    print(f"    {SAMPLE_RESPONSES_FOR_COMPARISON['response_a']}")

    print("\n  回答 B:")
    print(f"    {SAMPLE_RESPONSES_FOR_COMPARISON['response_b'][:100]}...")

    # 成对比较
    comparison = await evaluator.compare_pairwise(
        prompt=SAMPLE_RESPONSES_FOR_COMPARISON['prompt'],
        response_a=SAMPLE_RESPONSES_FOR_COMPARISON['response_a'],
        response_b=SAMPLE_RESPONSES_FOR_COMPARISON['response_b'],
        criteria="信息完整性、准确性、清晰度、有用性",
        return_confidence=True,
    )

    winner_map = {
        "A": "回答 A",
        "B": "回答 B",
        "tie": "平局",
    }

    print(f"\n  🏆 胜出: {winner_map.get(comparison['winner'], comparison['winner'])}")
    print(f"  置信度: {comparison.get('confidence', 'N/A')}")
    print(f"  比较理由: {comparison['reasoning'][:150]}...")

    if comparison.get('position_bias_detected'):
        print("  ⚠️ 检测到位置偏见，已进行校正")


async def demonstrate_rubric_generation():
    """演示评分标准生成"""
    print("\n" + "=" * 60)
    print("演示 5: 评分标准生成")
    print("=" * 60)

    evaluator = LLMJudgeEvaluator()

    print("\n📋 自动生成评分标准:")

    tasks = [
        "技术文档写作",
        "代码审查",
        "客户支持回复",
    ]

    for task in tasks:
        print(f"\n  任务: {task}")

        rubric = await evaluator.generate_rubric(
            task_description=task,
            num_criteria=4,
            scale=(1, 10),
        )

        print("  评分维度:")
        total_weight = sum(item.weight for item in rubric)
        for item in rubric:
            print(f"    - {item.criterion} (权重: {item.weight:.2f})")
            print(f"      描述: {item.description}")


async def demonstrate_bias_detection():
    """演示偏见检测"""
    print("\n" + "=" * 60)
    print("演示 6: 偏见检测和减少")
    print("=" * 60)

    evaluator = LLMJudgeEvaluator(detect_bias=True)

    print("\n🔍 检测评估文本中的偏见:")

    # 模拟评估理由
    sample_reasonings = [
        "第一个回答更加详细和完整，因此我选择A。",
        "第二个回答虽然简短，但内容更加准确。",
        "回答B的语言表达更加流畅优美，所以更好。",
        "回答A使用了更多专业术语，显得更加权威。",
    ]

    for i, reasoning in enumerate(sample_reasonings, 1):
        print(f"\n  评估理由 {i}: {reasoning}")

        biases = evaluator.detect_bias(reasoning)
        if biases:
            print("  检测到的偏见:")
            for bias in biases:
                print(f"    - {bias.name}: {bias.description}")
                print(f"      严重程度: {bias.severity:.1f}")
        else:
            print("  ✓ 未检测到明显偏见")

    print("\n📊 偏见统计:")
    bias_stats = evaluator.get_bias_statistics()
    print(f"  - 总检测次数: {bias_stats['total_detections']}")
    if bias_stats['bias_breakdown']:
        print("  - 偏见分布:")
        for bias_name, count in bias_stats['bias_breakdown'].items():
            print(f"    - {bias_name}: {count}次")


async def demonstrate_bias_mitigation():
    """演示偏见减少"""
    print("\n" + "=" * 60)
    print("演示 7: 偏见减少技术")
    print("=" * 60)

    evaluator = LLMJudgeEvaluator()

    print("\n🛡️ 使用多次评估减少偏见:")

    qa = SAMPLE_QA_PAIRS[0]
    print(f"\n  问题: {qa['question']}")
    print(f"  回答: {qa['answer'][:60]}...")

    # 使用偏见减少技术进行评估
    result = await evaluator.mitigate_bias(
        prompt=qa['question'],
        response=qa['answer'],
        criteria="准确性、完整性、清晰度",
        num_iterations=3,
    )

    print(f"\n  去偏后评分: {result['score']:.2f}")
    print(f"  修剪均值: {result['trimmed_mean']:.2f}")
    print(f"  标准差: {result['std']:.2f}")
    print(f"  所有评分: {result['all_scores']}")

    if result['bias_detected']:
        print(f"  检测到的偏见类型: {result['bias_detected']}")
    print(f"  置信度: {result['confidence']:.2f}")


async def demonstrate_composite_evaluation():
    """演示组合评估器"""
    print("\n" + "=" * 60)
    print("演示 8: 组合评估器 (CompositeEvaluator)")
    print("=" * 60)
    print("\n特性说明:")
    print("  - 组合多个评估器")
    print("  - 综合评估结果")
    print("  - 可配置权重")

    # 创建子评估器
    basic_evaluator = MockBasicEvaluator(name="BasicMetrics")
    llm_evaluator = LLMJudgeEvaluator(name="LLMJudge")

    # 创建组合评估器
    composite = CompositeEvaluator(
        evaluators=[basic_evaluator, llm_evaluator],
        name="CompositeDemo",
        weights={
            "BasicMetrics": 1.0,
            "LLMJudge": 2.0,  # LLM评估权重更高
        },
    )

    print("\n🔀 组合多个评估器:")
    print("  - 基础评估器: 文本相似度、词汇多样性")
    print("  - LLM评估器: 准确性、完整性、清晰度")
    print("  - 权重: 基础=1.0, LLM=2.0")

    qa = SAMPLE_QA_PAIRS[0]
    print(f"\n  评估问题: {qa['question']}")

    result = await composite.evaluate(
        input_data=qa['question'],
        output_data=qa['answer'],
        expected_output=qa['expected'],
    )

    print(f"\n  综合评分: {result.overall_score:.2f}")
    print(f"  评估耗时: {result.duration_ms:.2f}ms")
    print(f"  使用评估器数量: {result.metadata.get('evaluator_count', 'N/A')}")

    print("\n  所有指标:")
    for metric in result.metrics:
        print(f"    - {metric.name}: {metric.value:.4f} (权重: {metric.weight})")

    # 显示子结果
    if 'sub_results' in result.metadata:
        print("\n  子评估器结果:")
        for sub_result in result.metadata['sub_results']:
            print(f"    - {sub_result['eval_id'][:8]}...: {sub_result['overall_score']:.2f}")


async def demonstrate_evaluation_metrics():
    """演示评估指标类型"""
    print("\n" + "=" * 60)
    print("演示 9: 评估指标类型")
    print("=" * 60)

    print("\n📊 支持的指标类型:")

    metric_types = [
        (MetricType.ACCURACY, "准确率", "评估输出的正确性"),
        (MetricType.PRECISION, "精确率", "评估精确程度"),
        (MetricType.RECALL, "召回率", "评估覆盖程度"),
        (MetricType.F1_SCORE, "F1分数", "精确率和召回率的调和平均"),
        (MetricType.BLEU, "BLEU分数", "评估文本生成质量"),
        (MetricType.ROUGE, "ROUGE分数", "评估摘要质量"),
        (MetricType.RESPONSE_TIME, "响应时间", "评估系统响应速度"),
        (MetricType.TOKEN_COUNT, "Token数量", "评估资源使用"),
        (MetricType.RELEVANCE, "相关性", "评估内容相关性"),
        (MetricType.COHERENCE, "连贯性", "评估逻辑连贯性"),
        (MetricType.FLUENCY, "流畅性", "评估语言流畅度"),
        (MetricType.HELPFULNESS, "有用性", "评估实际帮助程度"),
        (MetricType.SAFETY, "安全性", "评估内容安全性"),
    ]

    for metric_type, name, description in metric_types:
        print(f"  - {metric_type.value}: {name}")
        print(f"    {description}")

    print("\n🎯 创建自定义指标:")
    custom_metric = EvaluationMetric(
        name="custom_quality_score",
        value=8.5,
        metric_type=MetricType.CUSTOM,
        weight=1.5,
        description="自定义质量评分",
    )

    print(f"  指标名称: {custom_metric.name}")
    print(f"  指标值: {custom_metric.value}")
    print(f"  指标类型: {custom_metric.metric_type.value}")
    print(f"  权重: {custom_metric.weight}")
    print(f"  描述: {custom_metric.description}")
    print(f"  时间戳: {custom_metric.timestamp}")


async def demonstrate_evaluation_result():
    """演示评估结果"""
    print("\n" + "=" * 60)
    print("演示 10: 评估结果处理")
    print("=" * 60)

    print("\n📄 创建评估结果:")

    # 创建评估结果
    result = EvaluationResult(
        eval_id="eval_001",
        input_text="什么是机器学习？",
        output_text="机器学习是人工智能的一个分支，使计算机能够从数据中学习。",
        expected_output="机器学习是AI的子领域。",
        overall_score=0.85,
        duration_ms=150.5,
    )

    # 添加指标
    result.add_metric(EvaluationMetric(
        name="accuracy",
        value=0.9,
        metric_type=MetricType.ACCURACY,
        weight=2.0,
    ))
    result.add_metric(EvaluationMetric(
        name="completeness",
        value=0.8,
        metric_type=MetricType.CUSTOM,
        weight=1.0,
    ))
    result.add_metric(EvaluationMetric(
        name="response_time_ms",
        value=150.5,
        metric_type=MetricType.RESPONSE_TIME,
        weight=0.5,
    ))

    print(f"  评估ID: {result.eval_id}")
    print(f"  输入: {result.input_text}")
    print(f"  输出: {result.output_text[:50]}...")
    print(f"  综合评分: {result.overall_score}")
    print(f"  耗时: {result.duration_ms}ms")

    print("\n🔍 查询指标:")
    accuracy_metric = result.get_metric("accuracy")
    if accuracy_metric:
        print(f"  准确率指标: {accuracy_metric.value} (权重: {accuracy_metric.weight})")

    completeness_value = result.get_metric_value("completeness", default=0.0)
    print(f"  完整性值: {completeness_value}")

    print("\n📝 评估摘要:")
    print(result.get_summary())

    print("\n💾 转换为字典:")
    result_dict = result.to_dict()
    print(f"  字典键: {list(result_dict.keys())}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepTutor 评估框架使用示例")
    print("=" * 60)
    print("\n本示例演示以下内容:")
    print("  1. 基础评估器")
    print("  2. LLM-as-a-Judge 评估")
    print("  3. 直接评分")
    print("  4. 成对比较")
    print("  5. 评分标准生成")
    print("  6. 偏见检测")
    print("  7. 偏见减少技术")
    print("  8. 组合评估器")
    print("  9. 评估指标类型")
    print("  10. 评估结果处理")
    print()

    try:
        # 运行所有演示
        await demonstrate_basic_evaluation()
        await demonstrate_llm_judge_evaluation()
        await demonstrate_direct_scoring()
        await demonstrate_pairwise_comparison()
        await demonstrate_rubric_generation()
        await demonstrate_bias_detection()
        await demonstrate_bias_mitigation()
        await demonstrate_composite_evaluation()
        await demonstrate_evaluation_metrics()
        await demonstrate_evaluation_result()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
