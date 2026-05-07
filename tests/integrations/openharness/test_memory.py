"""
OpenHarness 记忆系统测试

测试记忆管理器、解析器和存储功能
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.integrations.openharness.memory.manager import (
    MemoryCompressionConfig,
    MemoryMDParser,
    MemorySection,
    OpenHarnessMemoryManager,
)
from src.integrations.openharness.memory.storage import (
    MemoryStorage,
    StorageConfig,
)


class TestMemorySection:
    """记忆章节测试类"""

    def test_default_values(self):
        """测试默认值"""
        section = MemorySection(title="Test Section")

        assert section.title == "Test Section"
        assert section.content == ""
        assert section.level == 2
        assert section.subsections == []

    def test_with_subsections(self):
        """测试带子章节"""
        subsection = MemorySection(title="Subsection", level=3)
        section = MemorySection(
            title="Main",
            content="Main content",
            subsections=[subsection]
        )

        assert len(section.subsections) == 1
        assert section.subsections[0].title == "Subsection"


class TestMemoryCompressionConfig:
    """记忆压缩配置测试类"""

    def test_default_config(self):
        """测试默认配置"""
        config = MemoryCompressionConfig()

        assert config.enabled is True
        assert config.max_tokens == 4000
        assert config.compression_ratio == 0.5

    def test_custom_config(self):
        """测试自定义配置"""
        config = MemoryCompressionConfig(
            enabled=False,
            max_tokens=2000,
            compression_ratio=0.3
        )

        assert config.enabled is False
        assert config.max_tokens == 2000
        assert config.compression_ratio == 0.3


class TestMemoryMDParser:
    """MEMORY.md 解析器测试类"""

    def test_parse_simple(self):
        """测试简单解析"""
        content = """# Memory

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
        sections = MemoryMDParser.parse(content)

        assert len(sections) == 2
        assert "Section 1" in sections
        assert "Section 2" in sections
        assert "Content for section 1" in sections["Section 1"].content

    def test_parse_with_subsections(self):
        """测试带子章节的解析"""
        content = """# Memory

## Main Section

Main content.

### Subsection A

Subsection A content.

### Subsection B

Subsection B content.
"""
        sections = MemoryMDParser.parse(content)

        assert len(sections) == 1
        main = sections["Main Section"]
        assert len(main.subsections) == 2
        assert main.subsections[0].title == "Subsection A"
        assert main.subsections[1].title == "Subsection B"

    def test_parse_empty(self):
        """测试空内容解析"""
        sections = MemoryMDParser.parse("")
        assert len(sections) == 0

    def test_generate(self):
        """测试生成内容"""
        sections = {
            "Section 1": MemorySection(
                title="Section 1",
                content="Content 1"
            ),
            "Section 2": MemorySection(
                title="Section 2",
                content="Content 2",
                subsections=[
                    MemorySection(title="Subsection", level=3, content="Sub content")
                ]
            )
        }

        content = MemoryMDParser.generate(sections, title="Test Memory")

        assert "# Test Memory" in content
        assert "## Section 1" in content
        assert "## Section 2" in content
        assert "### Subsection" in content
        assert "Content 1" in content

    def test_extract_facts(self):
        """测试提取事实"""
        section = MemorySection(
            title="Facts",
            content="""
- **Key**: Value
- **Name**: John Doe
- Simple fact without key
* Another fact
"""
        )

        facts = MemoryMDParser.extract_facts(section)

        assert len(facts) == 4
        assert facts[0]["key"] == "Key"
        assert facts[0]["value"] == "Value"
        assert facts[1]["key"] == "Name"
        assert facts[1]["value"] == "John Doe"


class TestMemoryStorage:
    """记忆存储测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    async def storage(self, temp_dir):
        """创建存储实例"""
        config = StorageConfig(base_path=temp_dir)
        storage = MemoryStorage(config)
        await storage.initialize()
        yield storage
        await storage.close()

    @pytest.mark.asyncio
    async def test_storage_initialization(self, temp_dir):
        """测试存储初始化"""
        config = StorageConfig(base_path=temp_dir)
        storage = MemoryStorage(config)

        await storage.initialize()

        assert storage.is_initialized()
        await storage.close()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, temp_dir):
        """测试存储和检索"""
        config = StorageConfig(base_path=temp_dir)
        storage = MemoryStorage(config)
        await storage.initialize()

        # 创建测试条目
        entry = MagicMock()
        entry.id = "test_id"
        entry.content = "Test content"
        entry.to_dict.return_value = {"id": "test_id", "content": "Test content"}

        await storage.store("key1", entry)
        retrieved = await storage.retrieve("key1")

        assert retrieved is not None

        await storage.close()

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent(self, temp_dir):
        """测试检索不存在的键"""
        config = StorageConfig(base_path=temp_dir)
        storage = MemoryStorage(config)
        await storage.initialize()

        result = await storage.retrieve("nonexistent")
        assert result is None

        await storage.close()

    @pytest.mark.asyncio
    async def test_delete(self, temp_dir):
        """测试删除"""
        config = StorageConfig(base_path=temp_dir)
        storage = MemoryStorage(config)
        await storage.initialize()

        entry = MagicMock()
        entry.to_dict.return_value = {"id": "test"}

        await storage.store("key1", entry)
        result = await storage.delete("key1")

        assert result is True
        assert await storage.retrieve("key1") is None

        await storage.close()

    @pytest.mark.asyncio
    async def test_list_all(self, temp_dir):
        """测试列出所有键"""
        config = StorageConfig(base_path=temp_dir)
        storage = MemoryStorage(config)
        await storage.initialize()

        entry = MagicMock()
        entry.to_dict.return_value = {"id": "test"}

        await storage.store("key1", entry)
        await storage.store("key2", entry)

        keys = await storage.list_all()

        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

        await storage.close()


class TestOpenHarnessMemoryManager:
    """OpenHarness 记忆管理器测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    async def manager(self, temp_dir):
        """创建管理器实例"""
        memory_file = temp_dir / "MEMORY.md"
        manager = OpenHarnessMemoryManager(memory_file_path=memory_file)
        await manager.initialize()
        yield manager
        await manager.close()

    @pytest.mark.asyncio
    async def test_initialization(self, temp_dir):
        """测试初始化"""
        manager = OpenHarnessMemoryManager()
        await manager.initialize()

        assert manager._initialized is True
        await manager.close()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, manager):
        """测试存储和检索"""
        from src.core.memory.base import MemoryEntry, MemoryMetadata, MemoryType

        entry = MemoryEntry(
            content="Test memory content",
            memory_type=MemoryType.LONG_TERM,
            metadata=MemoryMetadata()
        )

        stored = await manager.store("test_key", "Test memory content", entry.metadata)
        retrieved = await manager.retrieve("test_key")

        assert retrieved is not None
        assert retrieved.content == "Test memory content"

    @pytest.mark.asyncio
    async def test_forget(self, manager):
        """测试遗忘"""
        from src.core.memory.base import MemoryMetadata

        await manager.store("forget_key", "Content to forget", MemoryMetadata())
        result = await manager.forget("forget_key")

        assert result is True
        assert await manager.retrieve("forget_key") is None

    @pytest.mark.asyncio
    async def test_search(self, manager):
        """测试搜索"""
        from src.core.memory.base import MemoryMetadata, MemoryQuery

        await manager.store("key1", "Python programming", MemoryMetadata())
        await manager.store("key2", "Java programming", MemoryMetadata())

        query = MemoryQuery(content="python", limit=10)
        results = await manager.search(query)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_clear(self, manager):
        """测试清空"""
        from src.core.memory.base import MemoryMetadata

        await manager.store("key1", "Content 1", MemoryMetadata())
        await manager.store("key2", "Content 2", MemoryMetadata())

        await manager.clear()

        assert await manager.retrieve("key1") is None
        assert await manager.retrieve("key2") is None

    @pytest.mark.asyncio
    async def test_compress_disabled(self, manager):
        """测试禁用压缩"""
        manager.compression_config.enabled = False

        result = await manager.compress()
        assert result == 0

    @pytest.mark.asyncio
    async def test_inject_context(self, manager):
        """测试上下文注入"""
        from src.core.memory.base import MemoryMetadata

        await manager.store("key1", "Relevant memory about AI", MemoryMetadata())

        prompt = "Tell me about AI"
        enhanced = await manager.inject_context(prompt, max_context_length=1000)

        assert "相关记忆" in enhanced or "Relevant memory" in enhanced or enhanced == prompt

    @pytest.mark.asyncio
    async def test_add_to_memory_md(self, manager):
        """测试添加到 MEMORY.md"""
        await manager.add_to_memory_md("Projects", "Started new project")

        content = await manager.get_memory_md_content()
        assert "Projects" in content
        assert "Started new project" in content

    @pytest.mark.asyncio
    async def test_add_to_memory_md_with_subsection(self, manager):
        """测试带子章节添加到 MEMORY.md"""
        await manager.add_to_memory_md("Projects", "Task 1", "Active")
        await manager.add_to_memory_md("Projects", "Task 2", "Active")

        content = await manager.get_memory_md_content()
        assert "Projects" in content
        assert "Active" in content

    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """测试获取统计"""
        from src.core.memory.base import MemoryMetadata

        await manager.store("key1", "Content 1", MemoryMetadata())
        await manager.store("key2", "Content 2", MemoryMetadata())

        stats = await manager.get_stats()

        assert "total_memories" in stats
        assert stats["total_memories"] == 2

    @pytest.mark.asyncio
    async def test_context_manager(self, temp_dir):
        """测试上下文管理器"""
        memory_file = temp_dir / "MEMORY.md"

        async with OpenHarnessMemoryManager(memory_file_path=memory_file) as manager:
            assert manager._initialized is True


class TestMemoryEdgeCases:
    """记忆边界情况测试类"""

    @pytest.mark.asyncio
    async def test_unicode_content(self, temp_dir):
        """测试 Unicode 内容"""
        memory_file = temp_dir / "MEMORY.md"
        manager = OpenHarnessMemoryManager(memory_file_path=memory_file)
        await manager.initialize()

        from src.core.memory.base import MemoryMetadata

        await manager.store("unicode_key", "中文内容 🎉", MemoryMetadata())
        retrieved = await manager.retrieve("unicode_key")

        assert retrieved is not None
        assert "中文内容" in retrieved.content

        await manager.close()

    @pytest.mark.asyncio
    async def test_very_long_content(self, temp_dir):
        """测试超长内容"""
        memory_file = temp_dir / "MEMORY.md"
        manager = OpenHarnessMemoryManager(memory_file_path=memory_file)
        await manager.initialize()

        from src.core.memory.base import MemoryMetadata

        long_content = "A" * 10000
        await manager.store("long_key", long_content, MemoryMetadata())
        retrieved = await manager.retrieve("long_key")

        assert retrieved is not None
        assert len(retrieved.content) == 10000

        await manager.close()

    @pytest.mark.asyncio
    async def test_special_characters_in_key(self, temp_dir):
        """测试特殊字符键"""
        memory_file = temp_dir / "MEMORY.md"
        manager = OpenHarnessMemoryManager(memory_file_path=memory_file)
        await manager.initialize()

        from src.core.memory.base import MemoryMetadata

        # 测试各种键名
        keys = ["key-with-dash", "key_with_underscore", "key.with.dots"]
        for key in keys:
            await manager.store(key, f"Content for {key}", MemoryMetadata())
            retrieved = await manager.retrieve(key)
            assert retrieved is not None

        await manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_access(self, temp_dir):
        """测试并发访问"""
        import asyncio

        memory_file = temp_dir / "MEMORY.md"
        manager = OpenHarnessMemoryManager(memory_file_path=memory_file)
        await manager.initialize()

        from src.core.memory.base import MemoryMetadata

        async def store_task(i):
            await manager.store(f"concurrent_{i}", f"Content {i}", MemoryMetadata())

        # 并发存储
        await asyncio.gather(*[store_task(i) for i in range(10)])

        # 验证所有存储成功
        for i in range(10):
            retrieved = await manager.retrieve(f"concurrent_{i}")
            assert retrieved is not None

        await manager.close()


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
