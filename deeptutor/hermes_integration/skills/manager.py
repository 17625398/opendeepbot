
"""
Hermes Agent Skills Manager Integration
Initial implementation for DeepTutor
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Skill:
    """
    Represents a Hermes-style skill
    """
    def __init__(
        self,
        name: str,
        description: str = "",
        enabled: bool = False,
        metadata: Optional[Dict] = None
    ):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.metadata = metadata or {}


class SkillsManager:
    """
    Simple skills manager for DeepTutor Hermes integration
    """
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to DeepTutor data dir
            data_dir = Path("./data/user/hermes/skills")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._skills: Dict[str, Skill] = {}
        self._load_skills()
        
    def _load_skills(self):
        """
        Load skills from data directory
        """
        if not self.data_dir.exists():
            return
        
        # Load existing skills from data dir
        for skill_dir in self.data_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "skill.json"
            if skill_file.exists():
                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        skill = Skill(
                            name=data.get("name", skill_dir.name),
                            description=data.get("description", ""),
                            enabled=data.get("enabled", False),
                            metadata=data.get("metadata", {})
                        )
                        self._skills[skill.name] = skill
                except Exception as e:
                    logger.warning(f"Failed to load skill {skill_dir}: {e}")

    def list_skills(self) -> List[Skill]:
        """
        List all available skills
        """
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name
        """
        return self._skills.get(name)

    def create_skill(self, name: str, description: str = "") -> Skill:
        """
        Create a new skill
        """
        if name in self._skills:
            raise ValueError(f"Skill {name} already exists")
        
        skill = Skill(name=name, description=description, enabled=False)
        
        # Save skill to disk
        skill_dir = self.data_dir / name
        skill_dir.mkdir(exist_ok=True)
        skill_file = skill_dir / "skill.json"
        
        with open(skill_file, "w", encoding="utf-8") as f:
            json.dump({
                "name": skill.name,
                "description": skill.description,
                "enabled": skill.enabled,
                "metadata": skill.metadata
            }, f, ensure_ascii=False, indent=2)
        
        self._skills[skill.name] = skill
        return skill

    def update_skill(self, name: str, **kwargs) -> Optional[Skill]:
        """
        Update an existing skill
        """
        if name not in self._skills:
            return None
        
        skill = self._skills[name]
        if "description" in kwargs:
            skill.description = kwargs["description"]
        if "enabled" in kwargs:
            skill.enabled = kwargs["enabled"]
        if "metadata" in kwargs:
            skill.metadata = kwargs["metadata"]
        
        # Save to disk
        skill_dir = self.data_dir / name
        skill_file = skill_dir / "skill.json"
        
        with open(skill_file, "w", encoding="utf-8") as f:
            json.dump({
                "name": skill.name,
                "description": skill.description,
                "enabled": skill.enabled,
                "metadata": skill.metadata
            }, f, ensure_ascii=False, indent=2)
        
        return skill

    def delete_skill(self, name: str) -> bool:
        """
        Delete a skill
        """
        if name not in self._skills:
            return False
        
        # Remove from in-memory
        del self._skills[name]
        
        # Delete from disk
        skill_dir = self.data_dir / name
        if skill_dir.exists():
            import shutil
            shutil.rmtree(skill_dir)
        
        return True
