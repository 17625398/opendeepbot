"""Skill tool — load and inject skill instructions into conversation context.
技能工具 — 加载技能指令并注入对话上下文。

Integrates with SkillsManager to discover and load SKILL.md files.
与 SkillsManager 集成以发现和加载 SKILL.md 文件。
"""

from __future__ import annotations

from typing import Any

from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolParameter, ToolResult


class SkillTool(BaseTool):
    """Load and inject skill instructions into the conversation.
    加载技能指令并注入对话。
    """

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for registration.
        获取用于注册的工具定义。
        """
        return ToolDefinition(
            name="load_skill",
            description=(
                "Load a skill SKILL.md file and return its instructions. "
                "Skills provide specialized workflows for specific tasks. "
                "Use 'list_skills' operation first to see available skills. | "
                "加载技能 SKILL.md 文件并返回其指令。技能提供特定任务的专门工作流程。"
            ),
            parameters=[
                ToolParameter(
                    name="operation",
                    type="string",
                    description=(
                        "Operation: 'load' to load a skill, 'list' to see available skills. | "
                        "操作：'load' 加载技能，'list' 列出可用技能。"
                    ),
                    enum=["load", "list"],
                ),
                ToolParameter(
                    name="skill_name",
                    type="string",
                    description=(
                        "Name of the skill to load (required for 'load' operation). | "
                        "要加载的技能名称（'load' 操作需要）。"
                    ),
                    required=False,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute skill load or list operation."""
        from deeptutor.core.skills_manager import get_skills_manager

        manager = get_skills_manager()
        operation = str(kwargs.get("operation", "list")).strip().lower()

        if operation == "list":
            return self._handle_list(manager)
        elif operation == "load":
            return await self._handle_load(manager, kwargs)
        else:
            return ToolResult(
                content=(
                    f"Unknown operation '{operation}'. Supported: load, list. | "
                    f"未知操作 '{operation}'。支持：load、list。"
                ),
                success=False,
            )

    def _handle_list(self, manager: Any) -> ToolResult:
        """List all available skills."""
        skills = manager.list_skills()
        if not skills:
            return ToolResult(
                content=(
                    "No skills found. Skills are loaded from ~/.claude/skills/<name>/SKILL.md. | "
                    "未找到技能。技能从 ~/.claude/skills/<name>/SKILL.md 加载。"
                ),
                metadata={"skills": [], "operation": "list"},
                success=True,
            )

        lines = ["Available skills: | 可用技能："]
        for s in skills:
            lines.append(f"  - {s.name}: {s.description[:80]}")
        lines.append(
            "\nUse 'load_skill' with operation='load' and skill_name='<name>' to load one. | "
            "使用 load_skill 工具，operation='load'，skill_name='<name>' 来加载技能。"
        )

        return ToolResult(
            content="\n".join(lines),
            metadata={
                "skills": [{"name": s.name, "description": s.description} for s in skills],
                "operation": "list",
            },
            success=True,
        )

    async def _handle_load(self, manager: Any, kwargs: dict[str, Any]) -> ToolResult:
        """Load a specific skill by name."""
        skill_name = str(kwargs.get("skill_name", "")).strip()
        if not skill_name:
            return ToolResult(
                content="Error: 'skill_name' is required for load operation. | 错误：加载操作需要 'skill_name' 参数。",
                success=False,
            )

        skill = manager.get_skill(skill_name)
        if skill is None:
            available = ", ".join(manager.skill_names()) or "none"
            return ToolResult(
                content=(
                    f"Skill '{skill_name}' not found. Available: {available}. | "
                    f"未找到技能 '{skill_name}'。可用：{available}。"
                ),
                success=False,
                metadata={"available_skills": manager.skill_names()},
            )

        content = manager.load_skill_content(skill_name)
        if not content:
            return ToolResult(
                content=f"Skill '{skill_name}' found but content is empty. | 技能 '{skill_name}' 存在但内容为空。",
                success=False,
            )

        return ToolResult(
            content=f"Skill '{skill_name}' loaded ({len(content)} chars). | 技能 '{skill_name}' 已加载（{len(content)} 字符）。\n\n{content}",
            metadata={
                "skill_name": skill_name,
                "description": skill.description,
                "file_path": skill.file_path,
                "content_length": len(content),
                "operation": "load",
            },
            success=True,
        )
