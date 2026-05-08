"""
Hermes Agent Integration Module
Provides Hermes-style Skills, MCP, Memory, Gateway, Agent Loop, and User Modeling
"""

# Agent Loop
from .agent_loop import AgentConfig, AgentLoop, AgentMessage, ToolResult

# Gateway
from .gateway.config import GatewayConfig, Platform, PlatformConfig, SessionResetPolicy
from .gateway.session import SessionContext, SessionSource, SessionStore

# MCP
from .mcp.manager import MCPServer, MCPServerManager

# Memory
from .memory import (
    BuiltinMemoryProvider,
    MemoryProvider,
    MemoryStore,
    StreamingContextScrubber,
    build_memory_context_block,
    get_memory_dir,
    sanitize_context,
)

# Scheduler
from .cron import CronParser, CronParserError, parse_cron, validate_cron, get_next_run
from .scheduler import ScheduledTask, Scheduler

# Skills
from .skills.manager import Skill, SkillsManager

# User Modeling
from .user_modeling import HonchoUserModeling, UserModelingEngine, UserProfile

# New modules (from hermes-agent-latest)
from . import prompt_builder
from . import curator
from . import prompt_caching
from . import context_compressor
from . import auxiliary_client
from .think_scrubber import StreamingThinkScrubber
from .tool_guardrails import (
    ToolCallGuardrailConfig,
    ToolCallGuardrailController,
    ToolGuardrailDecision,
    classify_tool_failure,
    canonical_tool_args,
)

__all__ = [
    # Agent Loop
    "AgentLoop",
    "AgentMessage",
    "AgentConfig",
    "ToolResult",
    # Gateway
    "GatewayConfig",
    "PlatformConfig",
    "SessionResetPolicy",
    "Platform",
    "SessionStore",
    "SessionSource",
    "SessionContext",
    # MCP
    "MCPServerManager",
    "MCPServer",
    # Memory
    "MemoryStore",
    "MemoryProvider",
    "BuiltinMemoryProvider",
    "get_memory_dir",
    "sanitize_context",
    "build_memory_context_block",
    "StreamingContextScrubber",
    # Scheduler
    "CronParser",
    "CronParserError",
    "parse_cron",
    "validate_cron",
    "get_next_run",
    "ScheduledTask",
    "Scheduler",
    # Skills
    "SkillsManager",
    "Skill",
    # User Modeling
    "UserModelingEngine",
    "UserProfile",
    "HonchoUserModeling",
    # New modules
    "prompt_builder",
    "curator",
    "prompt_caching",
    "context_compressor",
    "auxiliary_client",
    "StreamingThinkScrubber",
    "ToolCallGuardrailConfig",
    "ToolCallGuardrailController",
    "ToolGuardrailDecision",
    "classify_tool_failure",
    "canonical_tool_args",
]
