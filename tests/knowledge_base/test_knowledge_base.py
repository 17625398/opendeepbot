"""
知识库模块单元测试

测试范围：
- 知识库管理
- 文档处理
- RAG 检索
- 工具函数
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.skills.knowledge_base import (
    KnowledgeBaseConfig,
    KnowledgeBaseManager,
    generate_id,
    format_file_size,
    format_duration,
)
from src.skills.knowledge_base.models import (
    KnowledgeBase,
    Document,
    DocumentStatus,
    DocumentChunk,
)


# ============== 工具函数测试 ==============

class TestUtils:
    """测试工具函数"""
    
    def test_generate_id(self):
        """测试 ID 生成"""
        id1 = generate_id("kb")
        id2 = generate_id("doc")
        
        assert id1.startswith("kb_")
        assert id2.startswith("doc_")
        assert len(id1) > 3
        assert len(id2) > 4
        assert id1 != id2
    
    def test_format_file_size(self):
        """测试文件大小格式化"""
        assert format_file_size(512) == "512 B"
        assert "KB" in format_file_size(1024)
        assert "MB" in format_file_size(1024 * 1024)
        assert "GB" in format_file_size(1024 * 1024 * 1024)
    
    def test_format_duration(self):
        """测试持续时间格式化"""
        assert "秒" in format_duration(30)
        assert "分" in format_duration(120)
        assert "时" in format_duration(3600)


# ============== 模型测试 ==============

class TestModels:
    """测试数据模型"""
    
    def test_knowledge_base_creation(self):
        """测试知识库创建"""
        kb = KnowledgeBase(
            kb_id="kb_test",
            name="测试知识库",
            description="用于测试",
        )
        
        assert kb.kb_id == "kb_test"
        assert kb.name == "测试知识库"
        assert kb.description == "用于测试"
        assert len(kb.documents) == 0
        assert kb.total_chunks == 0
    
    def test_document_creation(self):
        """测试文档创建"""
        doc = Document(
            document_id="doc_test",
            knowledge_base_id="kb_test",
            filename="test.txt",
            file_size=1024,
            file_path="/tmp/test.txt",
        )
        
        assert doc.document_id == "doc_test"
        assert doc.filename == "test.txt"
        assert doc.status == DocumentStatus.PENDING
        assert len(doc.chunks) == 0
    
    def test_chunk_creation(self):
        """测试文档块创建"""
        chunk = DocumentChunk(
            chunk_id="chunk_test",
            document_id="doc_test",
            content="测试内容",
            start_pos=0,
            end_pos=10,
        )
        
        assert chunk.chunk_id == "chunk_test"
        assert chunk.content == "测试内容"
        assert chunk.start_pos == 0


# ============== 配置测试 ==============

class TestConfig:
    """测试配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = KnowledgeBaseConfig()
        
        assert config.vector_store_type == "chroma"
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = KnowledgeBaseConfig(
            vector_store_type="memory",
            chunk_size=500,
            chunk_overlap=50,
        )
        
        assert config.vector_store_type == "memory"
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50


# ============== 知识库管理器测试 ==============

@pytest.mark.asyncio
class TestKnowledgeBaseManager:
    """测试知识库管理器"""
    
    async def test_initialization(self):
        """测试初始化"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        
        await manager.initialize(embedding_provider="mock")
        
        assert manager.config == config
        assert manager.embedding_manager is not None
        assert manager.vector_store is not None
    
    async def test_create_knowledge_base(self):
        """测试创建知识库"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        await manager.initialize(embedding_provider="mock")
        
        kb = await manager.create_knowledge_base(
            name="测试知识库",
            description="用于测试",
        )
        
        assert kb.name == "测试知识库"
        assert kb.description == "用于测试"
        # UUID 格式验证
        assert len(kb.kb_id) > 0
    
    async def test_get_knowledge_base(self):
        """测试获取知识库"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        await manager.initialize(embedding_provider="mock")
        
        kb = await manager.create_knowledge_base(name="测试")
        retrieved = await manager.get_knowledge_base(kb.kb_id)
        
        assert retrieved is not None
        assert retrieved.kb_id == kb.kb_id
        assert retrieved.name == kb.name
    
    async def test_list_knowledge_bases(self):
        """测试列出知识库"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        await manager.initialize(embedding_provider="mock")
        
        # 创建多个知识库
        kb1 = await manager.create_knowledge_base(name="知识库1")
        kb2 = await manager.create_knowledge_base(name="知识库2")
        
        kbs = await manager.list_knowledge_bases()
        
        assert len(kbs) >= 2
        kb_ids = [kb.kb_id for kb in kbs]
        assert kb1.kb_id in kb_ids
        assert kb2.kb_id in kb_ids
    
    async def test_delete_knowledge_base(self):
        """测试删除知识库"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        await manager.initialize(embedding_provider="mock")
        
        kb = await manager.create_knowledge_base(name="待删除")
        kb_id = kb.kb_id
        
        success = await manager.delete_knowledge_base(kb_id)
        assert success is True
        
        retrieved = await manager.get_knowledge_base(kb_id)
        assert retrieved is None


# ============== 文档处理测试 ==============

@pytest.mark.asyncio
class TestDocumentProcessing:
    """测试文档处理"""
    
    async def test_add_document(self):
        """测试添加文档"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        await manager.initialize(embedding_provider="mock")
        
        kb = await manager.create_knowledge_base(name="测试")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("测试文档内容")
            temp_path = f.name
        
        try:
            doc = await manager.add_document(
                kb_id=kb.kb_id,
                file_path=temp_path,
                filename="test.txt",
            )
            
            assert doc.filename == "test.txt"
            assert doc.knowledge_base_id == kb.kb_id
            assert doc.status == DocumentStatus.PENDING
        finally:
            os.unlink(temp_path)
    
    async def test_get_document(self):
        """测试获取文档"""
        config = KnowledgeBaseConfig(vector_store_type="memory")
        manager = KnowledgeBaseManager(config)
        await manager.initialize(embedding_provider="mock")
        
        kb = await manager.create_knowledge_base(name="测试")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("测试内容")
            temp_path = f.name
        
        try:
            doc = await manager.add_document(
                kb_id=kb.kb_id,
                file_path=temp_path,
                filename="test.txt",
            )
            
            retrieved = await manager.get_document(kb.kb_id, doc.document_id)
            assert retrieved is not None
            assert retrieved.document_id == doc.document_id
        finally:
            os.unlink(temp_path)


# ============== 缓存测试 ==============

class TestCache:
    """测试缓存功能"""
    
    def test_embedding_cache(self):
        """测试嵌入缓存"""
        from src.skills.knowledge_base.cache import get_embedding_cache
        
        cache = get_embedding_cache()
        
        # 测试设置和获取
        cache.set("key1", [0.1, 0.2, 0.3])
        value = cache.get("key1")
        
        assert value == [0.1, 0.2, 0.3]
        
        # 测试不存在的键
        assert cache.get("nonexistent") is None
        
        # 测试删除
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_query_cache(self):
        """测试查询缓存"""
        from src.skills.knowledge_base.cache import get_query_cache
        
        cache = get_query_cache()
        
        # 测试设置和获取
        cache.set("query1", {"result": "test"})
        value = cache.get("query1")
        
        assert value == {"result": "test"}


# ============== 标签系统测试 ==============

class TestTagging:
    """测试标签系统"""
    
    def test_create_tag(self):
        """测试创建标签"""
        from src.skills.knowledge_base.tagging import get_tag_manager
        
        manager = get_tag_manager()
        
        tag = manager.create_tag(
            name="测试标签",
            color="#1890ff",
            description="用于测试",
        )
        
        assert tag.name == "测试标签"
        assert tag.color == "#1890ff"
        assert tag.description == "用于测试"


# ============== 主测试入口 ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
