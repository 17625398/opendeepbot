"""Auto mode for DeepSeek V4 integration.
DeepSeek V4 自动模式集成 - 自动选择模型和推理等级。

Automatically selects model and reasoning effort level per turn,
using a lightweight router call to deepseek-v4-flash.
使用轻量级路由器调用 deepseek-v4-flash 为每轮对话自动选择模型和推理等级。
"""

from __future__ import annotations

from typing import Any, Tuple

import json_repair

from .config import LLMConfig, get_llm_config

# Router model for making routing decisions
# 用于做出路由决策的路由器模型
ROUTER_MODEL = "deepseek-v4-flash"
ROUTER_SYSTEM = """You are a routing assistant for DeepSeek models.
Analyze the user request and decide:
1. Which model to use: "flash" (deepseek-v4-flash) or "pro" (deepseek-v4-pro)
2. Which reasoning effort: "off", "high", or "max"

Rules:
- Use "flash" for: simple questions, quick explanations, basic code tasks, summarization
- Use "pro" for: complex coding, debugging, architecture design, security review, 
  multi-step problems, release planning, ambiguous requests
- Use reasoning "off" for: simple factual queries, straightforward tasks
- Use reasoning "high" for: code analysis, debugging, moderate complexity
- Use reasoning "max" for: complex architecture, security review, difficult problems

Respond with JSON only: {"model": "flash|pro", "reasoning": "off|high|max"}
"""


def _parse_router_response(response: str) -> Tuple[str, str]:
    """Parse router response, return (model, reasoning_effort).
    解析路由器响应，返回（模型，推理等级）。
    """
    try:
        data = json_repair.loads(response.strip())
        if isinstance(data, dict):
            model_choice = str(data.get("model", "flash")).strip().lower()
            reasoning = str(data.get("reasoning", "off")).strip().lower()
            
            # Normalize model / 标准化模型名称
            if model_choice == "pro":
                model = "deepseek-v4-pro"
            else:
                model = "deepseek-v4-flash"
            
            # Normalize reasoning / 标准化推理等级
            if reasoning not in ("off", "high", "max"):
                reasoning = "off"
            
            return model, reasoning
    except Exception:
        pass
    
    # Fallback: local heuristic / 回退：使用本地启发式
    return _local_heuristic(response)


def _local_heuristic(user_message: str) -> Tuple[str, str]:
    """Local heuristic fallback when router fails.
    当路由器失败时使用的本地启发式回退方法。
    """
    msg_lower = user_message.lower()
    
    # Keywords suggesting pro model / 暗示使用 pro 模型的关键词
    pro_keywords = [
        "debug", "architecture", "design", "review", "security", "optimize",
        "refactor", "complex", "multi-step", "release", "deploy", "scale"
    ]
    # Keywords suggesting high/max reasoning / 暗示使用 high/max 推理的关键词
    reasoning_keywords_high = ["why", "how", "explain", "analyze", "compare"]
    reasoning_keywords_max = ["complex", "difficult", "architecture", "security", "prove"]
    
    model = "deepseek-v4-flash"
    if any(kw in msg_lower for kw in pro_keywords):
        model = "deepseek-v4-pro"
    
    reasoning = "off"
    if any(kw in msg_lower for kw in reasoning_keywords_max):
        reasoning = "max"
    elif any(kw in msg_lower for kw in reasoning_keywords_high):
        reasoning = "high"
    
    return model, reasoning


async def route_turn(
    user_message: str,
    context_messages: list[dict[str, Any]] | None = None,
    config: LLMConfig | None = None,
) -> Tuple[str, str]:
    """
    Route a turn to select model and reasoning effort.
    为当前轮次路由选择模型和推理等级。
    
    Returns / 返回:
        Tuple of (model_name, reasoning_effort)
        （模型名称，推理等级）元组
    """
    if config is None:
        config = get_llm_config()
    
    # Build router prompt with context / 构建带上下文的路由器提示
    context_str = ""
    if context_messages:
        recent = context_messages[-3:]  # Last 3 messages / 最近3条消息
        for msg in recent:
            role = msg.get("role", "unknown")
            content = str(msg.get("content", ""))[:100]  # Truncate / 截断
            context_str += f"{role}: {content}\n"
    
    router_prompt = f"""User message: {user_message}

Context (last 3 messages):
{context_str if context_str else "(no context)"}

Based on the user message and context above, which model and reasoning level should be used?
Respond with JSON only: {{"model": "flash|pro", "reasoning": "off|high|max"}}
"""
    
    try:
        # Use router model for routing decision
        # 使用路由器模型做出路由决策
        from .factory import complete
        
        response = await complete(
            prompt=router_prompt,
            system_prompt=ROUTER_SYSTEM,
            model=ROUTER_MODEL,
            # No reasoning for router itself / 路由器本身不使用推理
            **{"extra_headers": {"X-Routing-Call": "true"}},
        )
        
        return _parse_router_response(response)
    except Exception:
        # Fallback to heuristic / 回退到启发式
        return _local_heuristic(user_message)
