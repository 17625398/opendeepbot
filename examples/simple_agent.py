#!/usr/bin/env python3
"""
DeepTutor 简单 Agent 使用示例

演示 AgentLoop 的基本功能：
- 普通模式
- YOLO 模式
- 成本跟踪
- 思考可视化
- 快照和回滚
"""

import asyncio
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("example")


class MockLLMClient:
    """模拟 LLM 客户端用于示例"""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
        self.last_usage = {"prompt_tokens": 100, "completion_tokens": 50}
    
    async def chat_completion(self, messages: list) -> str:
        """模拟 LLM 响应"""
        logger.info(f"LLM 调用，模型: {self.model}")
        return "这是模拟的 LLM 响应"
    
    def get_last_usage(self) -> Dict[str, int]:
        """获取使用统计"""
        return self.last_usage


async def example_normal_mode():
    """示例 1: 普通模式"""
    logger.info("=" * 60)
    logger.info("示例 1: 普通模式")
    logger.info("=" * 60)
    
    # 导入 AgentLoop
    from deeptutor.integrations.nanobot.agent import AgentLoop
    
    # 创建客户端
    llm_client = MockLLMClient()
    
    # 创建 Agent
    agent = AgentLoop(
        llm_client=llm_client,
        yolo_mode=False,  # 需要人工批准
        track_cost=True    # 跟踪成本
    )
    
    # 运行任务
    # result = await agent.run("帮我分析这个任务")
    
    # 获取成本摘要
    cost_summary = agent.get_cost_summary()
    logger.info(f"成本摘要: {cost_summary}")


async def example_yolo_mode():
    """示例 2: YOLO 模式"""
    logger.info("=" * 60)
    logger.info("示例 2: YOLO 模式 (自动批准)")
    logger.info("=" * 60)
    
    from deeptutor.integrations.nanobot.agent import AgentLoop
    
    llm_client = MockLLMClient()
    
    agent = AgentLoop(
        llm_client=llm_client,
        yolo_mode=True,  # 自动批准
        track_cost=True
    )
    
    logger.info("YOLO 模式已启用，所有工具调用会自动批准")
    
    # 动态切换模式
    agent.set_yolo_mode(False)
    logger.info("已切换回普通模式")


async def example_thinking_visualization():
    """示例 3: 思考模式可视化"""
    logger.info("=" * 60)
    logger.info("示例 3: 思考模式可视化")
    logger.info("=" * 60)
    
    from deeptutor.integrations.nanobot.agent import AgentLoop
    
    llm_client = MockLLMClient()
    agent = AgentLoop(llm_client=llm_client)
    
    # 设置不同的显示风格
    for style in ["chain", "tree", "mindmap"]:
        agent.set_thinking_style(style)
        logger.info(f"已设置思考风格: {style}")
        
        # 打印思考过程
        # agent.print_thinking()


async def example_snapshots_rollback():
    """示例 4: 快照和回滚"""
    logger.info("=" * 60)
    logger.info("示例 4: 快照和回滚")
    logger.info("=" * 60)
    
    from deeptutor.integrations.nanobot.agent import AgentLoop
    
    llm_client = MockLLMClient()
    agent = AgentLoop(llm_client=llm_client)
    
    # 创建快照
    snapshot_id = agent._create_snapshot("initial_state")
    logger.info(f"已创建快照: {snapshot_id}")
    
    # 列出快照
    snapshots = agent._snapshots
    logger.info(f"可用快照: {[s['snapshot_id'] for s in snapshots]}")
    
    # 回滚到快照
    success = agent._rollback_to_snapshot(snapshot_id)
    logger.info(f"回滚成功: {success}")
    
    # 回滚几步
    agent._rollback_steps(0)


async def example_parallel_models():
    """示例 5: 多模型并行推理"""
    logger.info("=" * 60)
    logger.info("示例 5: 多模型并行推理 (概念演示)")
    logger.info("=" * 60)
    
    from deeptutor.integrations.nanobot.agent import AgentLoop
    
    # 创建多个客户端
    client1 = MockLLMClient("model-1")
    client2 = MockLLMClient("model-2")
    client3 = MockLLMClient("model-3")
    
    agent = AgentLoop(llm_client=client1)
    
    # 并行推理 (概念演示)
    logger.info("多模型并行推理可以:")
    logger.info("1. 投票聚合 (vote)")
    logger.info("2. 集成聚合 (ensemble)")
    logger.info("3. 选择最佳 (best)")


async def main():
    """运行所有示例"""
    logger.info("=" * 60)
    logger.info("DeepTutor Agent 示例")
    logger.info("=" * 60)
    
    try:
        await example_normal_mode()
        print()
        
        await example_yolo_mode()
        print()
        
        await example_thinking_visualization()
        print()
        
        await example_snapshots_rollback()
        print()
        
        await example_parallel_models()
        print()
        
        logger.info("=" * 60)
        logger.info("所有示例完成!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"执行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())