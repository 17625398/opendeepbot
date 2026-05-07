"""SubAgent tool — spawn, wait, list, and cancel sub-agents.
子代理工具 — 生成、等待、列出和取消子代理。

Integrates with SubAgentManager for lifecycle management.
与 SubAgentManager 集成以进行生命周期管理。
"""

from __future__ import annotations

from typing import Any

from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolParameter, ToolResult


class SubAgentTool(BaseTool):
    """Spawn, wait, list, and cancel sub-agents during a conversation.
    在对话中生成、等待、列出和取消子代理。
    """

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for registration.
        获取用于注册的工具定义。
        """
        return ToolDefinition(
            name="subagent",
            description=(
                "Manage sub-agents: spawn a new agent, wait for completion, list active agents, "
                "or cancel a running agent. | 管理子代理：生成新代理、等待完成、列出活动代理或取消运行中的代理。"
            ),
            parameters=[
                ToolParameter(
                    name="operation",
                    type="string",
                    description=(
                        "Operation to perform: 'spawn', 'wait', 'list', or 'cancel'. | "
                        "要执行的操作：'spawn'、'wait'、'list' 或 'cancel'。"
                    ),
                    enum=["spawn", "wait", "list", "cancel"],
                ),
                ToolParameter(
                    name="role",
                    type="string",
                    description=(
                        "Agent role for 'spawn': general, explore, plan, review, implementer, "
                        "verifier, custom. | 生成时的代理角色。"
                    ),
                    required=False,
                    default="general",
                ),
                ToolParameter(
                    name="task",
                    type="string",
                    description="Task description for 'spawn'. | 用于 'spawn' 的任务描述。",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="agent_id",
                    type="string",
                    description=(
                        "Agent ID for 'wait' or 'cancel'. | 用于 'wait' 或 'cancel' 的代理 ID。"
                    ),
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="Timeout in seconds for 'wait' (default: 120). | 等待超时秒数。",
                    required=False,
                    default=120,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the requested sub-agent operation."""
        from deeptutor.core.sub_agent_manager import get_sub_agent_manager

        manager = get_sub_agent_manager()
        operation = str(kwargs.get("operation", "")).strip().lower()

        if operation == "spawn":
            return await self._handle_spawn(manager, kwargs)
        elif operation == "wait":
            return await self._handle_wait(manager, kwargs)
        elif operation == "list":
            return self._handle_list(manager, kwargs)
        elif operation == "cancel":
            return await self._handle_cancel(manager, kwargs)
        else:
            return ToolResult(
                content=(
                    f"Unknown operation '{operation}'. Supported: spawn, wait, list, cancel. | "
                    f"未知操作 '{operation}'。支持：spawn、wait、list、cancel。"
                ),
                success=False,
            )

    async def _handle_spawn(self, manager: Any, kwargs: dict[str, Any]) -> ToolResult:
        """Handle sub-agent spawn operation."""
        role = str(kwargs.get("role", "general")).strip()
        task = str(kwargs.get("task", "")).strip()
        if not task:
            return ToolResult(
                content="Error: 'task' is required for spawn operation. | 错误：生成操作需要 'task' 参数。",
                success=False,
            )

        try:
            allowed_tools = kwargs.get("allowed_tools")
            if allowed_tools and isinstance(allowed_tools, list):
                allowed_tools = [str(t) for t in allowed_tools]
            else:
                allowed_tools = None

            parent_session = str(kwargs.get("session_id", ""))
            agent_id = await manager.spawn(
                role=role,
                task=task,
                parent_session_id=parent_session,
                allowed_tools=allowed_tools,
            )
            return ToolResult(
                content=f"Spawned sub-agent {agent_id} (role={role}). | 已生成子代理 {agent_id}（角色={role}）。",
                metadata={"agent_id": agent_id, "role": role, "operation": "spawn"},
                success=True,
            )
        except (ValueError, RuntimeError) as e:
            return ToolResult(content=f"Error spawning agent: {e}", success=False)

    async def _handle_wait(self, manager: Any, kwargs: dict[str, Any]) -> ToolResult:
        """Handle sub-agent wait operation."""
        agent_id = str(kwargs.get("agent_id", "")).strip()
        if not agent_id:
            return ToolResult(
                content="Error: 'agent_id' is required for wait operation. | 错误：等待操作需要 'agent_id' 参数。",
                success=False,
            )

        timeout = float(kwargs.get("timeout", 120))

        try:
            record = await manager.wait(agent_id, timeout=timeout)
            return ToolResult(
                content=(
                    f"Agent {agent_id} completed (state={record.state.value}). | "
                    f"代理 {agent_id} 已完成（状态={record.state.value}）。\n\n"
                    f"Result: {record.result[:2000]}"
                ),
                metadata={
                    "agent_id": agent_id,
                    "state": record.state.value,
                    "role": record.role,
                    "result": record.result,
                    "error": record.error,
                    "completed_at": record.completed_at,
                    "operation": "wait",
                },
                success=record.state.value == "completed",
            )
        except TimeoutError as e:
            return ToolResult(content=f"Wait timeout: {e}", success=False)
        except KeyError as e:
            return ToolResult(content=f"Error: {e}", success=False)

    def _handle_list(self, manager: Any, kwargs: dict[str, Any]) -> ToolResult:
        """Handle sub-agent list operation."""
        include_archived = bool(kwargs.get("include_archived", False))
        session_id = str(kwargs.get("session_id", "")) or None

        agents = manager.list_agents(
            include_archived=include_archived, session_id=session_id
        )

        if not agents:
            return ToolResult(
                content="No sub-agents found. | 未找到子代理。",
                metadata={"agents": [], "operation": "list"},
                success=True,
            )

        lines = ["Sub-agents: | 子代理："]
        for a in agents:
            lines.append(
                f"  - {a.agent_id[:8]} role={a.role} state={a.state.value} "
                f"task={a.task[:60]}"
            )
        return ToolResult(
            content="\n".join(lines),
            metadata={
                "agents": [
                    {
                        "agent_id": a.agent_id,
                        "role": a.role,
                        "state": a.state.value,
                        "task": a.task,
                    }
                    for a in agents
                ],
                "operation": "list",
            },
            success=True,
        )

    async def _handle_cancel(self, manager: Any, kwargs: dict[str, Any]) -> ToolResult:
        """Handle sub-agent cancel operation."""
        agent_id = str(kwargs.get("agent_id", "")).strip()
        if not agent_id:
            return ToolResult(
                content="Error: 'agent_id' is required for cancel operation. | 错误：取消操作需要 'agent_id' 参数。",
                success=False,
            )

        try:
            await manager.cancel(agent_id)
            return ToolResult(
                content=f"Cancelled agent {agent_id}. | 已取消代理 {agent_id}。",
                metadata={"agent_id": agent_id, "operation": "cancel"},
                success=True,
            )
        except KeyError as e:
            return ToolResult(content=f"Error: {e}", success=False)
