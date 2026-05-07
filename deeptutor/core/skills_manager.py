"""
Skills Manager
==============

技能管理器 — 发现、解析和加载 SKILL.md 文件
Discovers, parses, and loads SKILL.md files from skill directories.

Skills provide specialized instructions and workflows for specific tasks,
loaded from ~/.claude/skills/<name>/SKILL.md.
技能提供特定任务的专门指令和工作流程。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SkillDefinition:
    """Metadata and content of a loaded skill.
    已加载技能的元数据和内容。
    """

    name: str
    description: str = ""
    file_path: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class SkillsManager:
    """
    Discover, load, and provide access to skill files.

    发现、加载和提供对技能文件的访问。

    Skills are stored as SKILL.md files in skill directories.
    The default search path is ~/.claude/skills/.
    技能以 SKILL.md 文件形式存储在技能目录中。
    默认搜索路径为 ~/.claude/skills/。
    """

    DEFAULT_SKILLS_DIR = str(Path.home() / ".claude" / "skills")

    def __init__(self, skills_dirs: list[str] | None = None) -> None:
        self._skills_dirs = skills_dirs or [self.DEFAULT_SKILLS_DIR]
        self._skills: dict[str, SkillDefinition] = {}
        self._loaded = False

    def discover(self) -> list[SkillDefinition]:
        """
        Scan skill directories and discover available skills.

        扫描技能目录并发现可用技能。
        """
        self._skills = {}
        discovered: list[SkillDefinition] = []

        for skills_dir in self._skills_dirs:
            path = Path(skills_dir)
            if not path.exists() or not path.is_dir():
                logger.debug("Skills directory not found: %s", skills_dir)
                continue

            for skill_path in path.iterdir():
                if not skill_path.is_dir():
                    continue
                skill_md = skill_path / "SKILL.md"
                if not skill_md.exists():
                    continue

                try:
                    content = skill_md.read_text(encoding="utf-8")
                    name = skill_path.name
                    description = self._parse_description(content, name)
                    definition = SkillDefinition(
                        name=name,
                        description=description,
                        file_path=str(skill_md),
                        content=content,
                        metadata={
                            "directory": str(skill_path),
                            "discovered_from": skills_dir,
                        },
                    )
                    self._skills[name] = definition
                    discovered.append(definition)
                    logger.info("Discovered skill: %s (%s)", name, skill_md)
                except OSError as exc:
                    logger.warning("Failed to read skill %s: %s", skill_path, exc)

        self._loaded = True
        return discovered

    def get_skill(self, name: str) -> SkillDefinition | None:
        """Get a skill by name. Runs discover() first if not yet loaded."""
        if not self._loaded:
            self.discover()
        return self._skills.get(name)

    def list_skills(self) -> list[SkillDefinition]:
        """List all discovered skills."""
        if not self._loaded:
            self.discover()
        return list(self._skills.values())

    def skill_names(self) -> list[str]:
        """Return names of all discovered skills."""
        return [s.name for s in self.list_skills()]

    def load_skill_content(self, name: str) -> str:
        """
        Load the full SKILL.md content for a named skill.

        加载指定技能的完整 SKILL.md 内容。

        Args:
            name: Skill name (directory name under skills dir).

        Returns:
            The skill file content, or empty string if not found.
        """
        skill = self.get_skill(name)
        if skill is None:
            return ""
        if not skill.content:
            try:
                skill.content = Path(skill.file_path).read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning("Failed to re-read skill %s: %s", name, exc)
                return ""
        return skill.content

    def reload(self) -> list[SkillDefinition]:
        """Force re-discovery of all skills."""
        self._loaded = False
        return self.discover()

    @staticmethod
    def _parse_description(content: str, fallback_name: str) -> str:
        """Extract a short description from the first line of SKILL.md."""
        first_line = content.strip().split("\n")[0] if content else ""
        description = first_line.lstrip("#").strip()
        if not description:
            return f"Skill: {fallback_name}"
        return description


# Global singleton
_global_skills_manager: SkillsManager | None = None


def get_skills_manager() -> SkillsManager:
    global _global_skills_manager
    if _global_skills_manager is None:
        _global_skills_manager = SkillsManager()
    return _global_skills_manager
