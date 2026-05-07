"""
Sub-Agent Manager
=================

子代理管理器 — 管理子代理生命周期、并发限制、角色分类和持久化
Manages sub-agent lifecycle, concurrency caps, role taxonomy, and persistence.

Inspired by DeepSeek-TUI's sub-agent system:
https://github.com/Hmbown/DeepSeek-TUI
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 角色分类 / Role taxonomy
# ──────────────────────────────────────────────


class AgentRole(str, Enum):
    """Sub-agent role taxonomy matching DeepSeek-TUI semantics."""

    GENERAL = "general"
    EXPLORE = "explore"
    PLAN = "plan"
    REVIEW = "review"
    IMPLEMENTER = "implementer"
    VERIFIER = "verifier"
    CUSTOM = "custom"

    @classmethod
    def aliases(cls) -> dict[str, "AgentRole"]:
        return {
            "worker": cls.GENERAL,
            "default": cls.GENERAL,
            "general-purpose": cls.GENERAL,
            "explorer": cls.EXPLORE,
            "exploration": cls.EXPLORE,
            "planning": cls.PLAN,
            "awaiter": cls.PLAN,
            "reviewer": cls.REVIEW,
            "code-review": cls.REVIEW,
            "implement": cls.IMPLEMENTER,
            "implementation": cls.IMPLEMENTER,
            "builder": cls.IMPLEMENTER,
            "verify": cls.VERIFIER,
            "verification": cls.VERIFIER,
            "validator": cls.VERIFIER,
            "tester": cls.VERIFIER,
        }

    @classmethod
    def resolve(cls, name: str) -> "AgentRole":
        """Resolve a role name or alias, case-insensitive."""
        lower = name.lower().replace("-", "_")
        try:
            return cls(lower)
        except ValueError:
            pass
        aliases = cls.aliases()
        if lower in aliases:
            return aliases[lower]
        msg = f"Unknown agent role '{name}'. Valid: {', '.join(r.value for r in cls)}"
        raise ValueError(msg)


# ──────────────────────────────────────────────
# 子代理状态 / Sub-agent states
# ──────────────────────────────────────────────


class AgentState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


# ──────────────────────────────────────────────
# 数据模型 / Data models
# ──────────────────────────────────────────────


@dataclass
class SubAgentRecord:
    """Persistent record for a single sub-agent."""

    agent_id: str
    role: str
    task: str
    state: AgentState = AgentState.PENDING
    created_at: float = 0.0
    completed_at: float | None = None
    result: str = ""
    error: str = ""
    parent_session_id: str = ""
    from_prior_session: bool = False


# ──────────────────────────────────────────────
# 子代理管理器 / SubAgentManager
# ──────────────────────────────────────────────


class SubAgentManager:
    """
    Manages sub-agent lifecycle with concurrency cap and crash recovery.

    管理子代理生命周期，支持并发上限和崩溃恢复。

    Usage::
        manager = SubAgentManager()
        agent_id = await manager.spawn("explore", "Find all API endpoints")
        result = await manager.wait(agent_id)
    """

    # 默认并发上限 / Default concurrency cap
    DEFAULT_MAX_CONCURRENT = 10
    HARD_CEILING = 20

    # 持久化文件 / Persistence file
    PERSIST_PATH = str(Path.home() / ".deepseek" / "subagents.v1.json")

    def __init__(
        self,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        persist_path: str | None = None,
    ) -> None:
        self.max_concurrent = min(max_concurrent, self.HARD_CEILING)
        self._persist_path = persist_path or self.PERSIST_PATH
        # agent_id -> SubAgentRecord
        self._records: dict[str, SubAgentRecord] = {}
        # agent_id -> asyncio.Task
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._lock = asyncio.Lock()
        self._session_boot_id = str(uuid.uuid4())

        # 从持久化文件恢复 / Load persisted state
        self._load_persisted()

    # ── 属性 / Properties ──

    @property
    def running_count(self) -> int:
        return sum(1 for r in self._records.values() if r.state == AgentState.RUNNING)

    @property
    def can_spawn(self) -> bool:
        return self.running_count < self.max_concurrent

    # ── 核心操作 / Core operations ──

    async def spawn(
        self,
        role: str,
        task: str,
        parent_session_id: str = "",
        allowed_tools: list[str] | None = None,
    ) -> str:
        """
        Spawn a new sub-agent.

        生成一个新的子代理。

        Args:
            role: Role name or alias (see AgentRole).
            task: Task description for the sub-agent.
            parent_session_id: Optional parent session for tracing.
            allowed_tools: Tool allowlist (only for CUSTOM role).

        Returns:
            agent_id string.
        """
        resolved_role = AgentRole.resolve(role)

        if resolved_role == AgentRole.CUSTOM and not allowed_tools:
            raise ValueError("CUSTOM role requires explicit allowed_tools list")

        if not self.can_spawn:
            raise RuntimeError(
                f"Max concurrent agents reached ({self.max_concurrent}). "
                f"Wait or cancel an agent before retrying."
            )

        agent_id = str(uuid.uuid4())
        record = SubAgentRecord(
            agent_id=agent_id,
            role=resolved_role.value,
            task=task,
            state=AgentState.PENDING,
            created_at=time.time(),
            parent_session_id=parent_session_id,
        )

        async with self._lock:
            self._records[agent_id] = record
            task_obj = asyncio.create_task(
                self._run_agent(agent_id, resolved_role, task, allowed_tools or [])
            )
            self._tasks[agent_id] = task_obj

        self._persist()
        logger.info("Sub-agent %s spawned (role=%s): %.60s", agent_id, role, task)
        return agent_id

    async def wait(self, agent_id: str, timeout: float | None = None) -> SubAgentRecord:
        """
        Wait for a sub-agent to complete.

        等待子代理完成。

        Args:
            agent_id: The agent to wait for.
            timeout: Optional timeout in seconds.

        Returns:
            The final SubAgentRecord.
        """
        task = self._tasks.get(agent_id)
        if task is None:
            record = self._records.get(agent_id)
            if record is None:
                raise KeyError(f"Unknown agent: {agent_id}")
            return record  # Already completed

        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Agent {agent_id} did not complete within {timeout}s")
        except Exception:
            pass  # Error already recorded in the task

        return self._records.get(agent_id, task.result() if task.done() else None)

    async def cancel(self, agent_id: str) -> None:
        """Cancel a running sub-agent."""
        task = self._tasks.get(agent_id)
        if task and not task.done():
            task.cancel()
            async with self._lock:
                if agent_id in self._records:
                    self._records[agent_id].state = AgentState.CANCELLED
            self._persist()

    def list_agents(
        self,
        include_archived: bool = False,
        session_id: str | None = None,
    ) -> list[SubAgentRecord]:
        """
        List sub-agents.

        列出子代理。

        Args:
            include_archived: Include prior-session agents.
            session_id: Filter by parent session.
        """
        records = list(self._records.values())
        if not include_archived:
            # Only current session
            records = [
                r
                for r in records
                if not r.from_prior_session
                or r.state in (AgentState.RUNNING, AgentState.PENDING)
            ]
        if session_id:
            records = [r for r in records if r.parent_session_id == session_id]
        return sorted(records, key=lambda r: r.created_at, reverse=True)

    def get_record(self, agent_id: str) -> SubAgentRecord | None:
        return self._records.get(agent_id)

    # ── 内部方法 / Internal ──

    async def _run_agent(
        self,
        agent_id: str,
        role: AgentRole,
        task: str,
        allowed_tools: list[str],
    ) -> SubAgentRecord:
        """
        Execute the sub-agent's task.

        执行子代理任务 — 调用 LLM 并将结果写入记录。
        """
        from deeptutor.services.llm import complete
        from deeptutor.services.llm.config import get_llm_config

        async with self._lock:
            if agent_id in self._records:
                self._records[agent_id].state = AgentState.RUNNING
        self._persist()

        try:
            llm_config = get_llm_config()
            system_prompt = self._build_role_prompt(role, allowed_tools)

            response = await complete(
                prompt=task,
                system_prompt=system_prompt,
                model=llm_config.model,
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                temperature=0.3,
            )

            result_parts = self._format_output(response, role)

            async with self._lock:
                if agent_id in self._records:
                    self._records[agent_id].state = AgentState.COMPLETED
                    self._records[agent_id].completed_at = time.time()
                    self._records[agent_id].result = result_parts

        except asyncio.CancelledError:
            async with self._lock:
                if agent_id in self._records:
                    self._records[agent_id].state = AgentState.CANCELLED
                    self._records[agent_id].completed_at = time.time()

        except Exception as exc:
            logger.exception("Sub-agent %s failed", agent_id)
            async with self._lock:
                if agent_id in self._records:
                    self._records[agent_id].state = AgentState.FAILED
                    self._records[agent_id].completed_at = time.time()
                    self._records[agent_id].error = str(exc)

        finally:
            self._persist()
            async with self._lock:
                self._tasks.pop(agent_id, None)

        return self._records.get(agent_id)

    @staticmethod
    def _build_role_prompt(role: AgentRole, allowed_tools: list[str]) -> str:
        """Build system prompt for the given role."""
        base = "You are a focused sub-agent. Complete your task precisely and concisely.\n\n"

        role_prompts = {
            AgentRole.GENERAL: "You are a general-purpose agent. Do whatever the parent requests.",
            AgentRole.EXPLORE: "You are an exploration agent. Read-only: investigate codebases, files, or systems. Do NOT make changes or run destructive commands. Produce EVIDENCE with file paths and line ranges.",
            AgentRole.PLAN: "You are a planning agent. Analyse and produce a strategy. Do NOT execute. Output a structured plan with steps, dependencies, and risks.",
            AgentRole.REVIEW: "You are a code review agent. Read code and grade it with severity scores (critical/major/minor/warning/info). Do NOT make changes. Include path:line citations.",
            AgentRole.IMPLEMENTER: "You are an implementation agent. Land the specified change with minimum edits. No drive-by refactoring. Run a quick verification after each change.",
            AgentRole.VERIFIER: "You are a verification agent. Run tests and validation, report pass/fail outcomes. Do NOT fix failures. Capture failing assertions and stacks.",
            AgentRole.CUSTOM: f"You are a custom agent. You may only use these tools: {', '.join(allowed_tools)}" if allowed_tools else "You are a custom agent with restricted tools.",
        }

        prompt = base + role_prompts.get(role, "")
        prompt += (
            "\n\n"
            "## Output Contract\n"
            "Your final answer MUST include these five sections:\n"
            "SUMMARY: one paragraph; what you did and what happened\n"
            "CHANGES: files modified, with one-line descriptions; 'None.' if read-only\n"
            "EVIDENCE: path:line-range citations and key findings; one bullet each\n"
            "RISKS: what could go wrong / what the parent should double-check\n"
            "BLOCKERS: what stopped you; 'None.' if you finished cleanly\n"
        )
        return prompt

    @staticmethod
    def _format_output(response: str, role: AgentRole) -> str:
        """Ensure the output has the required contract sections."""
        required_sections = ["SUMMARY:", "CHANGES:", "EVIDENCE:", "RISKS:", "BLOCKERS:"]
        missing = [s for s in required_sections if s not in response]
        if missing:
            response += "\n\n" + "\n".join(f"{s} None." for s in missing)
        return response

    # ── 持久化 / Persistence ──

    def _persist(self) -> None:
        """Save sub-agent state to disk for crash recovery."""
        try:
            os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
            data = {
                "session_boot_id": self._session_boot_id,
                "schema_version": 1,
                "agents": [
                    {
                        **asdict(r),
                        "state": r.state.value,
                    }
                    for r in self._records.values()
                ],
            }
            Path(self._persist_path).write_text(json.dumps(data, indent=2))
        except OSError as exc:
            logger.warning("Failed to persist sub-agents: %s", exc)

    def _load_persisted(self) -> None:
        """Load sub-agent state from disk."""
        try:
            path = Path(self._persist_path)
            if not path.exists():
                return
            data = json.loads(path.read_text())
            for agent_data in data.get("agents", []):
                agent_data["state"] = AgentState(agent_data["state"])
                if agent_data.get("session_boot_id") != data.get("session_boot_id"):
                    agent_data["from_prior_session"] = True
                    if agent_data["state"] == AgentState.RUNNING:
                        agent_data["state"] = AgentState.INTERRUPTED
                record = SubAgentRecord(**agent_data)
                self._records[record.agent_id] = record
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load persisted sub-agents: %s", exc)

    # ── 清理 / Cleanup ──

    async def shutdown(self) -> None:
        """Cancel all running sub-agents."""
        for agent_id in list(self._tasks.keys()):
            await self.cancel(agent_id)
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._persist()


# 全局单例 / Global singleton
_global_manager: SubAgentManager | None = None


def get_sub_agent_manager() -> SubAgentManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = SubAgentManager()
    return _global_manager
