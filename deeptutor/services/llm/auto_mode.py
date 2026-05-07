"""Auto mode for DeepSeek V4 integration.

Automatically selects model and reasoning effort level per turn,
using a lightweight router call to deepseek-v4-flash.
"""

from __future__ import annotations

from typing import Any, Tuple

import json_repair

from .config import LLMConfig, get_llm_config

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
    """Parse router response, return (model, reasoning_effort)."""
    try:
        data = json_repair.loads(response.strip())
        if isinstance(data, dict):
            model_choice = str(data.get("model", "flash")).strip().lower()
            reasoning = str(data.get("reasoning", "off")).strip().lower()
            
            # Normalize model
            if model_choice == "pro":
                model = "deepseek-v4-pro"
            else:
                model = "deepseek-v4-flash"
            
            # Normalize reasoning
            if reasoning not in ("off", "high", "max"):
                reasoning = "off"
            
            return model, reasoning
    except Exception:
        pass
    
    # Fallback: local heuristic
    return _local_heuristic(response)


def _local_heuristic(user_message: str) -> Tuple[str, str]:
    """Local heuristic fallback when router fails."""
    msg_lower = user_message.lower()
    
    # Keywords suggesting pro model
    pro_keywords = [
        "debug", "architecture", "design", "review", "security", "optimize",
        "refactor", "complex", "multi-step", "release", "deploy", "scale"
    ]
    # Keywords suggesting high/max reasoning
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
    Returns:
        Tuple of (model_name, reasoning_effort)
    """
    if config is None:
        config = get_llm_config()
    
    # Build router prompt with context
    context_str = ""
    if context_messages:
        # Summarize context (last 3 messages)
        recent = context_messages[-3:]
        context_str = "\n".join(
            f"{m.get('role', 'user')}: {str(m.get('content', ''))[:200]}"
            for m in recent
        )
    
    router_prompt = f"""Context:
{context_str}

User request: {user_message}

Respond with JSON: {{"model": "flash|pro", "reasoning": "off|high|max"}}"""
    
    try:
        # Lazy import to avoid circular import
        from .factory import complete
        
        response = await complete(
            prompt=router_prompt,
            system_prompt=ROUTER_SYSTEM,
            model=ROUTER_MODEL,
            reasoning_effort="off",  # Router itself uses no reasoning
        )
        model, reasoning = _parse_router_response(response)
        return model, reasoning
    except Exception:
        # Fallback to local heuristic
        return _local_heuristic(user_message)


class AutoModeConfig:
    """Configuration for auto mode behavior."""
    
    def __init__(
        self,
        enabled: bool = False,
        router_model: str = ROUTER_MODEL,
        cache_routing: bool = True,
    ):
        self.enabled = enabled
        self.router_model = router_model
        self.cache_routing = cache_routing
        self._cache: dict[str, Tuple[str, str]] = {}
    
    def clear_cache(self) -> None:
        self._cache.clear()
    
    async def get_routing(
        self,
        user_message: str,
        context_messages: list[dict[str, Any]] | None = None,
        config: LLMConfig | None = None,
    ) -> Tuple[str, str]:
        """Get routing decision, with optional caching."""
        cache_key = user_message[:200]  # Simple cache key
        if self.cache_routing and cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await route_turn(user_message, context_messages, config)
        
        if self.cache_routing:
            self._cache[cache_key] = result
        
        return result
