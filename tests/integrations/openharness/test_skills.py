"""
OpenHarness 技能系统测试

测试技能加载器、转换器等功能
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.integrations.openharness.skills.converter import (
    DeepTutorSkill,
    OpenHarnessSkill,
    SkillConverter,
    SkillFormat,
    convert_to_deeptutor,
    convert_to_openharness,
    get_converter,
)
from src.integrations.openharness.skills.loader import (
    SkillCache,
    SkillContent,
    SkillFrontmatter,
    SkillLoader,
    get_skill_loader,
)


class TestSkillFrontmatter:
    """技能 Frontmatter 测试类"""

    def test_default_values(self):
        """测试默认值"""
        fm = SkillFrontmatter(
            name="test_skill",
            description="A test skill"
        )

        assert fm.name == "test_skill"
        assert fm.description == "A test skill"
        assert fm.version == "1.0.0"
        assert fm.author == ""
        assert fm.tags == []
        assert fm.category == "general"
        assert fm.icon == "🔧"
        assert fm.parameters == []
        assert fm.dependencies == []
        assert fm.entry_point == ""
        assert fm.timeout == 30
        assert fm.enabled is True

    def test_custom_values(self):
        """测试自定义值"""
        fm = SkillFrontmatter(
            name="custom_skill",
            description="Custom skill",
            version="2.0.0",
            author="Test Author",
            tags=["test", "demo"],
            category="analysis",
            icon="📊",
            parameters=[{"name": "param1", "type": "string"}],
            dependencies=["dep1"],
            entry_point="main.py",
            timeout=60,
            enabled=False
        )

        assert fm.version == "2.0.0"
        assert fm.author == "Test Author"
        assert fm.tags == ["test", "demo"]
        assert fm.category == "analysis"


class TestSkillCache:
    """技能缓存测试类"""

    @pytest.fixture
    def cache(self):
        """创建缓存实例"""
        return SkillCache(max_size=3, ttl=60)

    @pytest.fixture
    def sample_content(self):
        """创建示例技能内容"""
        fm = SkillFrontmatter(name="test", description="Test")
        return SkillContent(
            frontmatter=fm,
            content="Test content",
            file_path=Path("/test/skill.md"),
            checksum="abc123"
        )

    def test_cache_set_and_get(self, cache, sample_content):
        """测试缓存设置和获取"""
        cache.set("key1", sample_content)
        retrieved = cache.get("key1")

        assert retrieved is not None
        assert retrieved.frontmatter.name == "test"

    def test_cache_miss(self, cache):
        """测试缓存未命中"""
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expiration(self, cache, sample_content):
        """测试缓存过期"""
        cache = SkillCache(max_size=3, ttl=0)  # 立即过期
        cache.set("key1", sample_content)

        # 应该立即过期
        result = cache.get("key1")
        assert result is None

    def test_cache_lru_eviction(self, cache, sample_content):
        """测试 LRU 淘汰"""
        fm = sample_content.frontmatter

        # 添加超过最大容量的项目
        for i in range(4):
            content = SkillContent(
                frontmatter=SkillFrontmatter(name=f"skill{i}", description=f"Skill {i}"),
                content=f"Content {i}",
                file_path=Path(f"/test/skill{i}.md"),
                checksum=f"hash{i}"
            )
            cache.set(f"key{i}", content)

        # 第一个应该被淘汰
        assert cache.get("key0") is None
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None

    def test_cache_stats(self, cache, sample_content):
        """测试缓存统计"""
        cache.set("key1", sample_content)
        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 3
        assert stats["ttl"] == 60
        assert "key1" in stats["keys"]

    def test_cache_clear(self, cache, sample_content):
        """测试清空缓存"""
        cache.set("key1", sample_content)
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get_stats()["size"] == 0


class TestSkillLoader:
    """技能加载器测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """创建加载器实例"""
        return SkillLoader(skills_dir=temp_dir, cache_enabled=True)

    def create_skill_file(self, directory: Path, name: str, content: str = None) -> Path:
        """创建技能文件"""
        file_path = directory / f"{name}.md"

        if content is None:
            content = """---
name: Test Skill
description: A test skill
version: 1.0.0
---

# Test Skill

This is a test skill.
"""
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_load_from_file(self, loader, temp_dir):
        """测试从文件加载"""
        file_path = self.create_skill_file(temp_dir, "test")

        skill = loader.load_from_file(file_path)

        assert skill is not None
        assert skill.frontmatter.name == "Test Skill"
        assert skill.frontmatter.description == "A test skill"

    def test_load_from_file_not_found(self, loader):
        """测试加载不存在的文件"""
        skill = loader.load_from_file("/nonexistent/skill.md")
        assert skill is None

    def test_load_from_file_invalid_format(self, loader, temp_dir):
        """测试加载无效格式文件"""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Not a markdown file")

        skill = loader.load_from_file(file_path)
        assert skill is None

    def test_load_from_directory(self, loader, temp_dir):
        """测试从目录加载"""
        self.create_skill_file(temp_dir, "skill1")
        self.create_skill_file(temp_dir, "skill2")

        skills = loader.load_from_directory()

        assert len(skills) == 2

    def test_load_by_name(self, loader, temp_dir):
        """测试按名称加载"""
        self.create_skill_file(temp_dir, "my_skill")

        skill = loader.load_by_name("my_skill")

        assert skill is not None
        assert skill.frontmatter.name == "Test Skill"

    def test_load_by_name_not_found(self, loader):
        """测试加载不存在的名称"""
        skill = loader.load_by_name("nonexistent")
        assert skill is None

    def test_load_by_category(self, loader, temp_dir):
        """测试按分类加载"""
        content = """---
name: Analysis Skill
description: An analysis skill
category: analysis
---

# Analysis Skill
"""
        self.create_skill_file(temp_dir, "analysis_skill", content)

        skills = loader.load_by_category("analysis")

        assert len(skills) == 1
        assert skills[0].frontmatter.category == "analysis"

    def test_search_skills(self, loader, temp_dir):
        """测试搜索技能"""
        content1 = """---
name: Python Skill
description: Python programming
tags: [python, coding]
---

# Python Skill
"""
        content2 = """---
name: Java Skill
description: Java programming
tags: [java, coding]
---

# Java Skill
"""
        self.create_skill_file(temp_dir, "python_skill", content1)
        self.create_skill_file(temp_dir, "java_skill", content2)

        results = loader.search_skills("python")

        assert len(results) == 1
        assert results[0].frontmatter.name == "Python Skill"

    def test_search_by_tag(self, loader, temp_dir):
        """测试按标签搜索"""
        content = """---
name: Tagged Skill
description: A tagged skill
tags: [ml, ai]
---

# Tagged Skill
"""
        self.create_skill_file(temp_dir, "tagged", content)

        results = loader.search_skills("ml")

        assert len(results) == 1

    def test_reload_skill(self, loader, temp_dir):
        """测试重新加载技能"""
        file_path = self.create_skill_file(temp_dir, "reload_test")

        # 首次加载
        skill1 = loader.load_from_file(file_path)
        assert skill1 is not None

        # 修改文件
        new_content = """---
name: Updated Skill
description: Updated description
---

# Updated
"""
        file_path.write_text(new_content, encoding="utf-8")

        # 重新加载
        skill2 = loader.reload_skill(file_path)

        assert skill2 is not None
        assert skill2.frontmatter.name == "Updated Skill"

    def test_parse_frontmatter(self, loader):
        """测试解析 frontmatter"""
        frontmatter_text = """
name: Parsed Skill
description: Parsed description
version: 2.0.0
author: Test
tags: [a, b, c]
category: test
icon: 🧪
"""
        fm = loader._parse_frontmatter(frontmatter_text)

        assert fm.name == "Parsed Skill"
        assert fm.version == "2.0.0"
        assert fm.tags == ["a", "b", "c"]


class TestSkillConverter:
    """技能转换器测试类"""

    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        return SkillConverter()

    @pytest.fixture
    def sample_skill_content(self):
        """创建示例技能内容"""
        fm = SkillFrontmatter(
            name="Test Skill",
            description="A test skill for conversion",
            version="1.0.0",
            author="Test Author",
            tags=["test", "demo"],
            category="analysis",
            parameters=[
                {"name": "input", "type": "string", "description": "Input data", "required": True},
                {"name": "count", "type": "integer", "description": "Count", "default": 1}
            ]
        )
        return SkillContent(
            frontmatter=fm,
            content="# Test Skill\n\nThis is the skill content.",
            file_path=Path("/test/skill.md"),
            checksum="abc123"
        )

    def test_deeptutor_to_openharness(self, converter, sample_skill_content):
        """测试 DeepTutor 到 OpenHarness 转换"""
        oh_skill = converter.deeptutor_to_openharness(sample_skill_content)

        assert isinstance(oh_skill, OpenHarnessSkill)
        assert oh_skill.name == "Test Skill"
        assert oh_skill.description == "A test skill for conversion"
        assert oh_skill.version == "1.0.0"
        assert len(oh_skill.tools) == 2
        assert "system_prompt" in oh_skill.system_prompt

    def test_openharness_to_deeptutor(self, converter):
        """测试 OpenHarness 到 DeepTutor 转换"""
        oh_skill = OpenHarnessSkill(
            name="OH Skill",
            description="OpenHarness skill",
            tools=[
                {"name": "tool1", "type": "string", "description": "Tool 1", "required": True}
            ],
            system_prompt="# OH Skill\n\nContent here."
        )

        dt_skill = converter.openharness_to_deeptutor(oh_skill)

        assert isinstance(dt_skill, DeepTutorSkill)
        assert dt_skill.name == "OH Skill"
        assert dt_skill.id == "oh_skill"
        assert len(dt_skill.parameters) == 1

    def test_category_mapping_dt_to_oh(self, converter):
        """测试分类映射 DT -> OH"""
        fm = SkillFrontmatter(
            name="Test",
            description="Test",
            category="knowledge"
        )
        content = SkillContent(
            frontmatter=fm,
            content="",
            file_path=Path("/test.md"),
            checksum=""
        )

        oh_skill = converter.deeptutor_to_openharness(content)
        assert oh_skill.category == "knowledge_base"

    def test_category_mapping_oh_to_dt(self, converter):
        """测试分类映射 OH -> DT"""
        oh_skill = OpenHarnessSkill(
            name="Test",
            description="Test",
            category="data_analysis"
        )

        dt_skill = converter.openharness_to_deeptutor(oh_skill)
        assert dt_skill.category == "analysis"

    def test_detect_format_openharness(self, converter):
        """测试检测 OpenHarness 格式"""
        data = {
            "name": "Test",
            "tools": [],
            "system_prompt": "",
            "memory_config": {}
        }

        format_type = converter.detect_format(data)
        assert format_type == SkillFormat.OPENHARNESS

    def test_detect_format_deeptutor(self, converter):
        """测试检测 DeepTutor 格式"""
        data = {
            "id": "test",
            "name": "Test",
            "parameters": [],
            "type": "custom"
        }

        format_type = converter.detect_format(data)
        assert format_type == SkillFormat.DEEPTUTOR

    def test_detect_format_unknown(self, converter):
        """测试检测未知格式"""
        data = {"name": "Test"}

        format_type = converter.detect_format(data)
        assert format_type == SkillFormat.UNKNOWN

    def test_validate_conversion_openharness(self, converter):
        """测试验证 OpenHarness 转换"""
        source = {"name": "Test", "description": "Test"}
        target = {"name": "Test", "description": "Test", "tools": []}

        is_valid, errors = converter.validate_conversion(target, target, SkillFormat.OPENHARNESS)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_conversion_deeptutor(self, converter):
        """测试验证 DeepTutor 转换"""
        target = {"id": "test", "name": "Test", "description": "Test"}

        is_valid, errors = converter.validate_conversion({}, target, SkillFormat.DEEPTUTOR)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_conversion_missing_fields(self, converter):
        """测试验证缺少字段"""
        target = {"name": "Test"}  # 缺少 description 和 tools

        is_valid, errors = converter.validate_conversion({}, target, SkillFormat.OPENHARNESS)
        assert is_valid is False
        assert len(errors) > 0

    def test_generate_skill_id(self, converter):
        """测试生成技能 ID"""
        skill_id = converter._generate_skill_id("My Test Skill!")
        assert skill_id == "my_test_skill"

        skill_id2 = converter._generate_skill_id("Skill-With-Dashes")
        assert skill_id2 == "skill_with_dashes"

    def test_convert_skill_definition(self, converter):
        """测试通用技能定义转换"""
        definition = {
            "name": "Test",
            "description": "Test skill",
            "category": "general",
            "parameters": []
        }

        result = converter.convert_skill_definition(
            definition,
            SkillFormat.DEEPTUTOR,
            SkillFormat.OPENHARNESS
        )

        assert "tools" in result
        assert "system_prompt" in result


class TestSkillConverterFunctions:
    """技能转换函数测试类"""

    def test_get_converter(self):
        """测试获取转换器"""
        converter1 = get_converter()
        converter2 = get_converter()

        assert isinstance(converter1, SkillConverter)
        assert converter1 is converter2  # 单例

    def test_convert_to_openharness(self, sample_skill_content):
        """测试便捷转换函数"""
        result = convert_to_openharness(sample_skill_content)

        assert isinstance(result, OpenHarnessSkill)
        assert result.name == "Test Skill"

    def test_convert_to_deeptutor():
        """测试便捷转换函数"""
        oh_skill = OpenHarnessSkill(
            name="Test",
            description="Test skill"
        )

        result = convert_to_deeptutor(oh_skill)

        assert isinstance(result, DeepTutorSkill)
        assert result.name == "Test"


class TestSkillEdgeCases:
    """技能边界情况测试类"""

    def test_empty_frontmatter(self):
        """测试空 frontmatter"""
        fm = SkillFrontmatter(name="", description="")
        assert fm.name == ""
        assert fm.version == "1.0.0"

    def test_unicode_skill_content(self, temp_dir):
        """测试 Unicode 技能内容"""
        loader = SkillLoader(skills_dir=temp_dir)

        content = """---
name: Unicode Skill
description: 中文描述
---

# Unicode Skill

中文内容 🎉
"""
        file_path = temp_dir / "unicode.md"
        file_path.write_text(content, encoding="utf-8")

        skill = loader.load_from_file(file_path)

        assert skill is not None
        assert skill.frontmatter.description == "中文描述"
        assert "中文内容" in skill.content

    def test_skill_with_no_frontmatter(self, temp_dir):
        """测试没有 frontmatter 的技能"""
        loader = SkillLoader(skills_dir=temp_dir)

        content = "# Simple Skill\n\nNo frontmatter here."
        file_path = temp_dir / "simple.md"
        file_path.write_text(content, encoding="utf-8")

        skill = loader.load_from_file(file_path)

        assert skill is not None
        assert skill.frontmatter.name == "simple"  # 使用文件名

    def test_nested_skill_directories(self, temp_dir):
        """测试嵌套技能目录"""
        loader = SkillLoader(skills_dir=temp_dir)

        # 创建嵌套目录
        nested_dir = temp_dir / "category" / "subcategory"
        nested_dir.mkdir(parents=True)

        content = """---
name: Nested Skill
description: A nested skill
---

# Nested
"""
        (nested_dir / "nested.md").write_text(content, encoding="utf-8")

        skills = loader.load_from_directory(recursive=True)

        assert len(skills) == 1
        assert skills[0].frontmatter.name == "Nested Skill"


@pytest.fixture
def sample_skill_content():
    """示例技能内容 fixture"""
    fm = SkillFrontmatter(
        name="Test Skill",
        description="A test skill",
        version="1.0.0"
    )
    return SkillContent(
        frontmatter=fm,
        content="# Test\n\nContent",
        file_path=Path("/test/skill.md"),
        checksum="abc"
    )


@pytest.fixture(autouse=True)
def reset_loader():
    """自动重置加载器"""
    import src.integrations.openharness.skills.loader as loader_module
    loader_module._skill_loader = None
    yield
    loader_module._skill_loader = None
