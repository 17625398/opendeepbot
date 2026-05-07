"""
完整 Agent 技能集成示例

这个示例展示了如何在 DeepTutor 中创建一个使用多种技能的完整 Agent：
- 上下文压缩技能 - 自动管理长上下文
- 评估框架 - 自动评估响应质量
- 记忆系统 - 短期和长期记忆
- 多 Agent 协调 - 任务分解和协作
- 工具设计 - 工具验证和文档生成

运行说明:
    1. 确保已安装 DeepTutor 依赖
    2. 从项目根目录运行: python examples/skills/complete_agent_example.py
    3. 或直接运行: python complete_agent_example.py

功能演示:
    - 创建集成多种技能的 Agent
    - 自动上下文压缩
    - 响应质量评估
    - 记忆管理
    - 多技能协作
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入技能相关模块
from src.agents.skills.context_compression import ContextCompressionSkill, CompressionStrategy, CompressionLevel
from src.agents.skills.context_fundamentals import ContextFundamentalsSkill
from src.agents.skills.tool_design import ToolDesignSkill
from src.agents.memory import ShortTermMemory, LongTermMemory, GraphMemory
from src.agents.memory.base import MemoryMetadata
from src.agents.memory.long_term import StorageConfig
from src.agents.evaluation import BasicEvaluator, LLMJudgeEvaluator, EvaluationMetric, MetricType


class CompleteSkillDemoAgent:
    """
    完整技能演示 Agent
    
    展示如何集成和使用多种技能：
    - 上下文管理（分析、压缩）
    - 评估框架（自动评估）
    - 记忆系统（短期、长期、图记忆）
    - 工具设计（验证、文档生成）
    """
    
    def __init__(
        self,
        name: str = "CompleteDemoAgent",
        enable_compression: bool = True,
        enable_evaluation: bool = True,
        enable_memory: bool = True,
    ):
        """
        初始化完整演示 Agent
        
        Args:
            name: Agent 名称
            enable_compression: 是否启用上下文压缩
            enable_evaluation: 是否启用评估框架
            enable_memory: 是否启用记忆系统
        """
        self.name = name
        self.enable_compression = enable_compression
        self.enable_evaluation = enable_evaluation
        self.enable_memory = enable_memory
        
        # 初始化技能
        self._init_skills()
        
        # 初始化记忆系统
        if enable_memory:
            self._init_memory()
        
        # 评估历史
        self.evaluation_history: List[Dict[str, Any]] = []
        
        # 会话统计
        self.session_stats = {
            "total_requests": 0,
            "total_responses": 0,
            "compression_count": 0,
            "evaluation_count": 0,
        }
    
    def _init_skills(self) -> None:
        """初始化技能"""
        # 上下文相关技能
        self.context_fundamentals_skill = ContextFundamentalsSkill()
        self.context_compression_skill = ContextCompressionSkill()
        
        # 工具设计技能
        self.tool_design_skill = ToolDesignSkill()
        
        # 评估器
        self.basic_evaluator = BasicEvaluator()
        self.llm_judge = LLMJudgeEvaluator()
        
        print(f"✅ [{self.name}] 技能初始化完成")
    
    def _init_memory(self) -> None:
        """初始化记忆系统"""
        # 短期记忆（5分钟TTL）
        self.short_term_memory = ShortTermMemory(
            ttl=300,  # 5分钟
            max_size=1000,
        )
        
        # 长期记忆（内存存储，用于演示）
        self.long_term_memory = LongTermMemory(
            config=StorageConfig(
                backend="json",
                path="./demo_memory",
                auto_save=True,
            )
        )
        
        # 图记忆
        self.graph_memory = GraphMemory()
        
        print(f"✅ [{self.name}] 记忆系统初始化完成")
    
    async def process_with_skills(
        self,
        user_input: str,
        context: str = "",
        expected_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用多种技能处理用户输入
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            expected_output: 期望输出（用于评估）
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        print(f"\n{'='*60}")
        print(f"🤖 [{self.name}] 处理请求")
        print(f"{'='*60}")
        
        self.session_stats["total_requests"] += 1
        
        # 1. 上下文分析
        print("\n📊 步骤 1: 上下文分析")
        context_analysis = await self._analyze_context(context)
        
        # 2. 上下文压缩（如果需要）
        print("\n🗜️ 步骤 2: 上下文压缩")
        processed_context = await self._compress_context_if_needed(context)
        
        # 3. 检索相关记忆
        if self.enable_memory:
            print("\n🧠 步骤 3: 检索记忆")
            memories = await self._retrieve_memories(user_input)
        else:
            memories = []
        
        # 4. 生成响应（模拟）
        print("\n💬 步骤 4: 生成响应")
        response = await self._generate_response(user_input, processed_context, memories)
        
        # 5. 评估响应质量
        if self.enable_evaluation:
            print("\n📈 步骤 5: 评估响应")
            evaluation = await self._evaluate_response(user_input, response, expected_output)
        else:
            evaluation = None
        
        # 6. 存储记忆
        if self.enable_memory:
            print("\n💾 步骤 6: 存储记忆")
            await self._store_memories(user_input, response)
        
        self.session_stats["total_responses"] += 1
        
        return {
            "response": response,
            "context_analysis": context_analysis,
            "compression_applied": processed_context != context,
            "memories_retrieved": len(memories),
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _analyze_context(self, context: str) -> Dict[str, Any]:
        """分析上下文"""
        if not context:
            return {"status": "no_context"}
        
        try:
            result = await self.context_fundamentals_skill.execute(context)
            
            print(f"  - 总长度: {result.structure.total_length} 字符")
            print(f"  - 预估 Token: {result.structure.token_estimate}")
            print(f"  - 组件数量: {result.structure.component_count}")
            print(f"  - 健康评分: {result.overall_health_score:.2f}")
            
            if result.issues:
                print(f"  - 检测到 {len(result.issues)} 个问题")
            
            return {
                "status": "success",
                "total_length": result.structure.total_length,
                "token_estimate": result.structure.token_estimate,
                "health_score": result.overall_health_score,
                "issues_count": len(result.issues),
            }
        except Exception as e:
            print(f"  - 分析失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _compress_context_if_needed(
        self,
        context: str,
        threshold: int = 2000,
    ) -> str:
        """根据需要压缩上下文"""
        if not self.enable_compression or not context:
            return context
        
        # 估算 token 数
        token_estimate = len(context) // 4  # 简化估算
        
        if token_estimate < threshold:
            print(f"  - 上下文长度 {token_estimate} tokens，无需压缩")
            return context
        
        print(f"  - 上下文长度 {token_estimate} tokens，超过阈值 {threshold}")
        print(f"  - 执行压缩...")
        
        try:
            result = await self.context_compression_skill.execute(
                context,
                strategy=CompressionStrategy.HYBRID,
                level=CompressionLevel.MEDIUM,
            )
            
            self.session_stats["compression_count"] += 1
            
            print(f"  - 压缩完成:")
            print(f"    原始长度: {len(context)} 字符")
            print(f"    压缩后: {len(result.compressed)} 字符")
            print(f"    压缩率: {result.metrics.compression_ratio:.2%}")
            print(f"    质量评分: {result.metrics.quality_score:.2f}")
            
            return result.compressed
        except Exception as e:
            print(f"  - 压缩失败: {e}")
            return context
    
    async def _retrieve_memories(self, query: str) -> List[str]:
        """检索相关记忆"""
        memories = []
        
        try:
            # 从短期记忆检索
            stm_keys = await self.short_term_memory.get_keys()
            for key in stm_keys[:3]:  # 限制数量
                entry = await self.short_term_memory.retrieve(key)
                if entry:
                    memories.append(f"[短期记忆] {key}: {entry.content}")
            
            # 从长期记忆搜索
            from src.agents.memory.base import MemoryQuery
            ltm_results = await self.long_term_memory.search(
                MemoryQuery(content=query, limit=3)
            )
            for result in ltm_results:
                memories.append(f"[长期记忆] {result.entry.content[:100]}...")
            
            print(f"  - 检索到 {len(memories)} 条相关记忆")
            for mem in memories[:2]:  # 只显示前2条
                print(f"    - {mem[:80]}...")
            
        except Exception as e:
            print(f"  - 记忆检索失败: {e}")
        
        return memories
    
    async def _generate_response(
        self,
        user_input: str,
        context: str,
        memories: List[str],
    ) -> str:
        """生成响应（模拟）"""
        # 模拟响应生成
        response_parts = []
        
        if memories:
            response_parts.append("根据我的记忆，")
        
        response_parts.append(f"我收到了您的问题：'{user_input}'")
        
        if context:
            response_parts.append("我会结合上下文为您提供回答。")
        
        response = " ".join(response_parts)
        
        print(f"  - 生成响应: {response[:80]}...")
        
        return response
    
    async def _evaluate_response(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """评估响应质量"""
        try:
            # 使用基础评估器
            basic_result = await self.basic_evaluator.evaluate(
                input_text,
                output_text,
                expected_output,
            )
            
            self.session_stats["evaluation_count"] += 1
            
            print(f"  - 基础评估:")
            print(f"    综合评分: {basic_result.overall_score:.2f}")
            print(f"    指标数量: {len(basic_result.metrics)}")
            
            # 记录评估历史
            eval_record = {
                "timestamp": datetime.now().isoformat(),
                "input": input_text[:50],
                "output": output_text[:50],
                "score": basic_result.overall_score,
            }
            self.evaluation_history.append(eval_record)
            
            return {
                "overall_score": basic_result.overall_score,
                "metrics_count": len(basic_result.metrics),
                "duration_ms": basic_result.duration_ms,
            }
        except Exception as e:
            print(f"  - 评估失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _store_memories(self, user_input: str, response: str) -> None:
        """存储记忆"""
        try:
            # 存储到短期记忆
            await self.short_term_memory.store(
                f"session_{datetime.now().timestamp()}",
                f"Q: {user_input} | A: {response}",
            )
            
            # 存储关键信息到长期记忆
            if len(user_input) > 10:  # 只存储有意义的输入
                await self.long_term_memory.store(
                    f"knowledge_{datetime.now().timestamp()}",
                    user_input,
                    metadata=MemoryMetadata(
                        tags=["user_input", "demo"],
                        importance=0.7,
                    )
                )
            
            print(f"  - 记忆存储完成")
            
        except Exception as e:
            print(f"  - 记忆存储失败: {e}")
    
    async def demonstrate_tool_validation(self, tool_def: Dict[str, Any]) -> Dict[str, Any]:
        """演示工具验证"""
        print(f"\n{'='*60}")
        print(f"🔧 [{self.name}] 工具验证演示")
        print(f"{'='*60}")
        
        report = self.tool_design_skill.validate_tool_definition(tool_def)
        
        print(f"\n  工具: {tool_def.get('name', 'unknown')}")
        print(f"  验证结果:")
        print(f"    - 是否有效: {'✅ 是' if report.is_valid else '❌ 否'}")
        print(f"    - 错误数: {len(report.get_errors())}")
        print(f"    - 警告数: {len(report.get_warnings())}")
        
        if report.get_errors():
            print("\n  错误详情:")
            for error in report.get_errors():
                print(f"    - [{error.field}] {error.message}")
        
        return report.to_dict()
    
    async def demonstrate_memory_systems(self) -> Dict[str, Any]:
        """演示记忆系统"""
        print(f"\n{'='*60}")
        print(f"🧠 [{self.name}] 记忆系统演示")
        print(f"{'='*60}")
        
        results = {}
        
        # 短期记忆演示
        print("\n📌 短期记忆:")
        await self.short_term_memory.store("demo_key", "演示值")
        entry = await self.short_term_memory.retrieve("demo_key")
        print(f"  - 存储和检索: {'✅ 成功' if entry else '❌ 失败'}")
        results["short_term"] = {"stored": entry is not None}
        
        # 图记忆演示
        print("\n📌 图记忆:")
        node1 = await self.graph_memory.add_node("概念A", "这是一个概念", "concept")
        node2 = await self.graph_memory.add_node("概念B", "这是另一个概念", "concept")
        await self.graph_memory.add_edge(node1.id, node2.id)
        print(f"  - 节点数: {self.graph_memory.node_count}")
        print(f"  - 边数: {self.graph_memory.edge_count}")
        results["graph_memory"] = {
            "nodes": self.graph_memory.node_count,
            "edges": self.graph_memory.edge_count,
        }
        
        return results
    
    async def demonstrate_evaluation(self) -> Dict[str, Any]:
        """演示评估框架"""
        print(f"\n{'='*60}")
        print(f"📊 [{self.name}] 评估框架演示")
        print(f"{'='*60}")
        
        # 示例问答
        question = "什么是Python？"
        answer = "Python是一种高级编程语言，以简洁易读著称。"
        expected = "Python是编程语言"
        
        print(f"\n  问题: {question}")
        print(f"  回答: {answer}")
        
        # 执行评估
        result = await self.basic_evaluator.evaluate(question, answer, expected)
        
        print(f"\n  评估结果:")
        print(f"    - 综合评分: {result.overall_score:.2f}")
        print(f"    - 评估耗时: {result.duration_ms:.2f}ms")
        print(f"    - 指标数量: {len(result.metrics)}")
        
        return {
            "score": result.overall_score,
            "duration_ms": result.duration_ms,
            "metrics": [m.name for m in result.metrics],
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取 Agent 统计信息"""
        return {
            "name": self.name,
            "session_stats": self.session_stats.copy(),
            "evaluation_count": len(self.evaluation_history),
            "features": {
                "compression": self.enable_compression,
                "evaluation": self.enable_evaluation,
                "memory": self.enable_memory,
            },
        }


async def demonstrate_complete_agent():
    """演示完整 Agent"""
    print("\n" + "="*60)
    print("🚀 完整 Agent 技能集成演示")
    print("="*60)
    
    # 创建 Agent
    agent = CompleteSkillDemoAgent(
        name="SmartAssistant",
        enable_compression=True,
        enable_evaluation=True,
        enable_memory=True,
    )
    
    # 演示 1: 处理请求（短上下文）
    print("\n" + "-"*60)
    print("\n📍 演示 1: 处理简单请求")
    result1 = await agent.process_with_skills(
        user_input="你好，请介绍一下自己",
        context="",
    )
    print(f"\n  响应: {result1['response'][:80]}...")
    print(f"  记忆检索: {result1['memories_retrieved']} 条")
    
    # 演示 2: 处理请求（长上下文，触发压缩）
    print("\n" + "-"*60)
    print("\n📍 演示 2: 处理长上下文请求（触发压缩）")
    long_context = "人工智能" * 500  # 生成长文本
    result2 = await agent.process_with_skills(
        user_input="总结一下上述内容",
        context=long_context,
    )
    print(f"\n  压缩应用: {'是' if result2['compression_applied'] else '否'}")
    
    # 演示 3: 工具验证
    print("\n" + "-"*60)
    sample_tool = {
        "id": "demo_tool",
        "name": "demo_tool",
        "description": "这是一个演示工具",
        "parameters": [
            {"name": "input", "type": "string", "description": "输入", "required": True},
        ],
    }
    await agent.demonstrate_tool_validation(sample_tool)
    
    # 演示 4: 记忆系统
    print("\n" + "-"*60)
    await agent.demonstrate_memory_systems()
    
    # 演示 5: 评估框架
    print("\n" + "-"*60)
    await agent.demonstrate_evaluation()
    
    # 显示统计
    print("\n" + "="*60)
    print("📈 Agent 会话统计")
    print("="*60)
    stats = agent.get_stats()
    print(f"\n  Agent 名称: {stats['name']}")
    print(f"  总请求数: {stats['session_stats']['total_requests']}")
    print(f"  总响应数: {stats['session_stats']['total_responses']}")
    print(f"  压缩次数: {stats['session_stats']['compression_count']}")
    print(f"  评估次数: {stats['session_stats']['evaluation_count']}")
    print(f"\n  功能状态:")
    for feature, enabled in stats['features'].items():
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"    - {feature}: {status}")


async def demonstrate_skill_comparison():
    """演示不同技能配置的比较"""
    print("\n" + "="*60)
    print("⚖️ 不同技能配置比较")
    print("="*60)
    
    # 创建不同配置的 Agent
    configs = [
        ("FullFeatured", True, True, True),
        ("NoCompression", False, True, True),
        ("NoEvaluation", True, False, True),
        ("Minimal", False, False, False),
    ]
    
    test_input = "解释机器学习"
    test_context = "AI " * 1000  # 长上下文
    
    for name, comp, eval_, mem in configs:
        print(f"\n{'-'*40}")
        print(f"\n🔧 配置: {name}")
        print(f"  压缩: {comp}, 评估: {eval_}, 记忆: {mem}")
        
        agent = CompleteSkillDemoAgent(name, comp, eval_, mem)
        
        start_time = datetime.now()
        result = await agent.process_with_skills(test_input, test_context)
        duration = (datetime.now() - start_time).total_seconds()
        
        stats = agent.get_stats()
        print(f"\n  处理时间: {duration:.3f}s")
        print(f"  压缩应用: {result['compression_applied']}")
        print(f"  评估结果: {'有' if result['evaluation'] else '无'}")


async def demonstrate_context_compression_feature():
    """演示上下文压缩功能"""
    print("\n" + "="*60)
    print("🗜️ 上下文压缩功能详细演示")
    print("="*60)
    
    agent = CompleteSkillDemoAgent("CompressionDemo")
    
    # 不同长度的上下文
    test_cases = [
        ("短文本", "Hello World" * 10),
        ("中等文本", "Python是一种语言。" * 100),
        ("长文本", "人工智能" * 1000),
    ]
    
    for name, context in test_cases:
        print(f"\n{'-'*40}")
        print(f"\n📝 测试: {name}")
        print(f"  原始长度: {len(context)} 字符")
        
        result = await agent.process_with_skills(
            user_input="总结",
            context=context,
        )
        
        print(f"  压缩应用: {'是' if result['compression_applied'] else '否'}")
        if result['compression_applied']:
            print(f"  上下文分析: 已压缩")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("DeepTutor 完整 Agent 技能集成示例")
    print("="*60)
    print("\n本示例演示以下内容:")
    print("  1. 完整 Agent 创建和配置")
    print("  2. 上下文分析和压缩")
    print("  3. 记忆系统使用")
    print("  4. 响应质量评估")
    print("  5. 工具验证")
    print("  6. 不同配置比较")
    print()
    
    try:
        # 运行演示
        await demonstrate_complete_agent()
        await demonstrate_skill_comparison()
        await demonstrate_context_compression_feature()
        
        print("\n" + "="*60)
        print("✅ 所有演示完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
