"""
SmartTutorAgent 使用示例

演示如何在 DeepTutor 中使用集成 Context Engineering Skills 的智能辅导 Agent。
"""

import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

from src.agents.smart_tutor import SmartTutorAgent
from src.agents.smart_tutor.learning_session import QuestionType, DifficultyLevel


async def demo_smart_tutor():
    """演示智能辅导 Agent"""
    
    print("=" * 60)
    print("SmartTutorAgent 演示")
    print("=" * 60)
    
    # 创建 Agent
    agent = SmartTutorAgent(
        student_id="student_001",
        student_name="小明",
        enable_context_compression=True,
        enable_evaluation=True,
        context_compression_threshold=3000  # 较低的阈值以便演示压缩
    )
    
    # 初始化
    print("\n1. 初始化 Agent...")
    await agent.initialize()
    print("✓ Agent 初始化完成")
    
    # 开始数学学习会话
    print("\n2. 开始数学学习会话...")
    await agent.start_new_session(topic="数学-代数")
    print("✓ 会话已启动")
    
    # 提问1：基础概念
    print("\n3. 提问 1 - 基础概念...")
    question1 = await agent.ask_question(
        content="什么是二次方程的一般形式？",
        question_type=QuestionType.CONCEPT,
        difficulty=DifficultyLevel.EASY,
        topic="代数-二次方程"
    )
    print(f"问题: {question1.content}")
    
    # 学生回答
    answer1 = "ax² + bx + c = 0，其中a、b、c是常数，且a≠0"
    print(f"学生回答: {answer1}")
    
    # 处理回答
    result1 = await agent.process_answer(question1, answer1)
    print(f"✓ 回答{'正确' if result1['is_correct'] else '错误'}")
    print(f"  反馈: {result1['feedback']}")
    print(f"  当前难度: {result1['current_difficulty']}")
    if result1.get('evaluation'):
        print(f"  质量评分: {result1['evaluation']['basic_score']:.2f}")
    
    # 提问2：应用题
    print("\n4. 提问 2 - 应用题...")
    question2 = await agent.ask_question(
        content="解方程：x² - 5x + 6 = 0",
        question_type=QuestionType.APPLICATION,
        difficulty=DifficultyLevel.MEDIUM,
        topic="代数-二次方程"
    )
    print(f"问题: {question2.content}")
    
    # 学生回答
    answer2 = "x = 2 或 x = 3"
    print(f"学生回答: {answer2}")
    
    result2 = await agent.process_answer(question2, answer2)
    print(f"✓ 回答{'正确' if result2['is_correct'] else '错误'}")
    print(f"  反馈: {result2['feedback']}")
    
    # 提问3：分析题
    print("\n5. 提问 3 - 分析题...")
    question3 = await agent.ask_question(
        content="分析方程 x² + 4x + 4 = 0 的解的特点",
        question_type=QuestionType.ANALYSIS,
        difficulty=DifficultyLevel.HARD,
        topic="代数-二次方程"
    )
    print(f"问题: {question3.content}")
    
    # 学生回答（故意回答错误以演示反馈）
    answer3 = "有两个不同的实数解"
    print(f"学生回答: {answer3}")
    
    result3 = await agent.process_answer(question3, answer3)
    print(f"✓ 回答{'正确' if result3['is_correct'] else '错误'}")
    print(f"  反馈: {result3['feedback']}")
    
    # 提供解释
    print("\n6. 提供详细解释...")
    explanation = await agent.provide_explanation(
        question3, answer3, result3['is_correct']
    )
    print(f"解释: {explanation}")
    
    # 获取个性化建议
    print("\n7. 获取个性化学习建议...")
    recommendations = await agent.get_personalized_recommendations()
    print("学习建议:")
    for rec in recommendations:
        print(f"  - {rec}")
    
    # 结束会话
    print("\n8. 结束会话...")
    summary = await agent.end_session()
    print("会话摘要:")
    print(f"  - 会话ID: {summary['session_id']}")
    print(f"  - 主题: {summary['current_topic']}")
    print(f"  - 提问数: {summary['questions_asked']}")
    print(f"  - 回答数: {summary['questions_answered']}")
    print(f"  - 正确率: {summary['accuracy']*100:.1f}%")
    print(f"  - 总Token数: {summary['total_context_tokens']}")
    print(f"  - 压缩次数: {summary['compression_count']}")
    
    # 获取学习报告
    print("\n9. 获取学习报告...")
    report = await agent.get_learning_report()
    print(report)
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


async def demo_context_compression():
    """演示上下文压缩功能"""
    
    print("\n" + "=" * 60)
    print("上下文压缩演示")
    print("=" * 60)
    
    agent = SmartTutorAgent(
        student_id="student_002",
        student_name="小红",
        enable_context_compression=True,
        context_compression_threshold=500  # 很低的阈值以便快速触发压缩
    )
    
    await agent.initialize()
    await agent.start_new_session(topic="物理-力学")
    
    print("\n模拟长对话以触发上下文压缩...")
    
    # 模拟多个问答来积累上下文
    for i in range(5):
        question = await agent.ask_question(
            content=f"问题 {i+1}: 请解释牛顿第{i+1}定律的内容和应用场景，并给出具体的计算示例。",
            topic="物理-力学"
        )
        
        answer = f"这是关于牛顿第{i+1}定律的详细回答。" * 20  # 长回答
        result = await agent.process_answer(question, answer)
        
        print(f"  Q{i+1}: {result['context_tokens']} tokens")
        if result['context_tokens'] > 500:
            print(f"    → 触发压缩!")
    
    summary = await agent.end_session()
    print(f"\n总会话压缩次数: {summary['compression_count']}")
    print(f"总Token使用量: {summary['total_context_tokens']}")


async def demo_evaluation():
    """演示评估框架"""
    
    print("\n" + "=" * 60)
    print("评估框架演示")
    print("=" * 60)
    
    agent = SmartTutorAgent(
        student_id="student_003",
        student_name="小李",
        enable_evaluation=True
    )
    
    await agent.initialize()
    await agent.start_new_session(topic="化学-元素周期表")
    
    # 测试不同质量的回答
    test_cases = [
        ("什么是元素周期表？", "元素周期表是化学元素的排列方式。"),
        ("什么是元素周期表？", "元素周期表是按照原子序数排列的化学元素表格，由门捷列夫创立，展示了元素的周期性规律。"),
        ("解释化学键", "化学键是原子之间的相互作用力，包括离子键、共价键和金属键三种主要类型。离子键是电子转移形成的..."),
    ]
    
    print("\n评估不同质量的回答:")
    for question, answer in test_cases:
        print(f"\n问题: {question}")
        print(f"回答: {answer[:50]}...")
        
        q = await agent.ask_question(content=question, topic="化学")
        result = await agent.process_answer(q, answer)
        
        if result.get('evaluation'):
            eval_data = result['evaluation']
            print(f"  基础评分: {eval_data['basic_score']:.2f}")
            print(f"  LLM评分: {eval_data['llm_score']:.2f}")
    
    await agent.end_session()


async def main():
    """主函数"""
    try:
        # 运行主要演示
        await demo_smart_tutor()
        
        # 运行上下文压缩演示
        await demo_context_compression()
        
        # 运行评估框架演示
        await demo_evaluation()
        
    except Exception as e:
        print(f"演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
