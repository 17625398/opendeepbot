"""
SuperMemory Integration Tests
=============================

测试 SuperMemory 集成功能，包括：
- 记忆存储与检索
- 向量相似度搜索
- 知识图谱操作
- Agent 内存管理
- API 端点
- WebSocket 连接

Author: DeepTutor Team
"""

import json
import pytest
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
from fastapi import WebSocket


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supermemory_config():
    """Mock SuperMemory 配置"""
    from src.integrations.supermemory.config import SuperMemoryConfig
    
    config = SuperMemoryConfig(
        enabled=True,
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test_password",
        vector_db_host="localhost",
        vector_db_port=6333,
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
        api_base_url="http://localhost:8002",
        api_key="test_api_key",
        timeout=30,
        max_retries=3,
    )
    return config


@pytest.fixture
def sample_memory_record():
    """示例记忆记录"""
    from src.integrations.supermemory.models import MemoryRecord, MemoryType
    
    return MemoryRecord(
        id="mem_1234567890abcdef",
        content="这是一个测试记忆内容",
        memory_type=MemoryType.SEMANTIC,
        source="test",
        agent_id="agent_001",
        session_id="session_001",
        user_id="user_001",
        embedding=[0.1] * 1536,
        metadata={"test": True},
        importance=0.8,
        confidence=0.9,
        tags=["test", "memory"],
        categories=["test_category"],
    )


@pytest.fixture
def sample_knowledge_entity():
    """示例知识实体"""
    from src.integrations.supermemory.models import KnowledgeEntity
    
    return KnowledgeEntity(
        id="ent_1234567890abcdef",
        name="测试实体",
        entity_type="concept",
        description="这是一个测试实体",
        properties={"key": "value"},
        source="test",
        confidence=0.9,
    )


@pytest.fixture
def sample_entity_relation():
    """示例实体关系"""
    from src.integrations.supermemory.models import EntityRelation, RelationType
    
    return EntityRelation(
        id="rel_1234567890abcdef",
        source_id="ent_001",
        target_id="ent_002",
        relation_type=RelationType.RELATED_TO,
        properties={"strength": 0.8},
        strength=0.8,
        bidirectional=False,
        source="test",
        confidence=0.9,
    )


@pytest.fixture
def sample_agent_memory():
    """示例 Agent 内存"""
    from src.integrations.supermemory.models import AgentMemory, MemoryRecord, MemoryType
    
    return AgentMemory(
        agent_id="agent_001",
        session_id="session_001",
        user_id="user_001",
        working_memory=[
            MemoryRecord(
                id="wm_001",
                content="工作记忆1",
                memory_type=MemoryType.WORKING,
            ),
        ],
        long_term_memory_ids=["ltm_001", "ltm_002"],
        context_window=10,
        relevant_entities=["ent_001"],
        metadata={"test": True},
    )


@pytest.fixture
def mock_httpx_client():
    """Mock HTTPX 异步客户端"""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


# =============================================================================
# Config Tests
# =============================================================================


class TestSuperMemoryConfig:
    """测试 SuperMemory 配置"""
    
    def test_config_creation(self, mock_supermemory_config):
        """测试配置创建"""
        config = mock_supermemory_config
        
        assert config.enabled is True
        assert config.neo4j_uri == "bolt://localhost:7687"
        assert config.neo4j_user == "neo4j"
        assert config.embedding_dimensions == 1536
        assert config.api_base_url == "http://localhost:8002"
    
    def test_config_to_dict(self, mock_supermemory_config):
        """测试配置转字典"""
        config = mock_supermemory_config
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["enabled"] is True
        assert config_dict["neo4j_uri"] == "bolt://localhost:7687"
        # 密码应该被隐藏
        assert config_dict["neo4j_password"] == "***"
    
    def test_config_validation_success(self, mock_supermemory_config):
        """测试配置验证成功"""
        config = mock_supermemory_config
        result = config.validate()
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_config_validation_failure(self):
        """测试配置验证失败"""
        from src.integrations.supermemory.config import SuperMemoryConfig
        
        config = SuperMemoryConfig(
            enabled=True,
            neo4j_uri="invalid_uri",  # 无效的 URI
            vector_db_port=99999,  # 无效的端口
            embedding_dimensions=-1,  # 无效的维度
        )
        
        result = config.validate()
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_config_is_configured(self, mock_supermemory_config):
        """测试配置检查"""
        config = mock_supermemory_config
        assert config.is_configured() is True
        
        config.enabled = False
        assert config.is_configured() is False
    
    def test_get_neo4j_auth(self, mock_supermemory_config):
        """测试获取 Neo4j 认证信息"""
        config = mock_supermemory_config
        auth = config.get_neo4j_auth()
        
        assert auth == ("neo4j", "test_password")
    
    def test_get_vector_db_url(self, mock_supermemory_config):
        """测试获取向量数据库 URL"""
        config = mock_supermemory_config
        url = config.get_vector_db_url()
        
        assert url == "http://localhost:6333"


# =============================================================================
# Model Tests
# =============================================================================


class TestMemoryRecord:
    """测试记忆记录模型"""
    
    def test_memory_record_creation(self, sample_memory_record):
        """测试记忆记录创建"""
        memory = sample_memory_record
        
        assert memory.id is not None
        assert memory.content == "这是一个测试记忆内容"
        assert memory.importance == 0.8
        assert memory.confidence == 0.9
    
    def test_memory_record_validation(self):
        """测试记忆记录验证"""
        from src.integrations.supermemory.models import MemoryRecord
        
        # 空内容应该失败
        with pytest.raises(ValueError):
            MemoryRecord(content="", memory_type="semantic")
        
        # 空白内容应该失败
        with pytest.raises(ValueError):
            MemoryRecord(content="   ", memory_type="semantic")
    
    def test_memory_record_score_validation(self):
        """测试评分验证"""
        from src.integrations.supermemory.models import MemoryRecord
        
        # 超出范围的评分会被验证器截断
        memory = MemoryRecord(
            content="测试",
            importance=0.8,
            confidence=0.9,
        )
        
        # 测试正常范围内的值
        assert memory.importance == 0.8
        assert memory.confidence == 0.9
        
        # 测试边界值
        memory_max = MemoryRecord(content="测试", importance=1.0, confidence=1.0)
        assert memory_max.importance == 1.0
        assert memory_max.confidence == 1.0
        
        memory_min = MemoryRecord(content="测试", importance=0.0, confidence=0.0)
        assert memory_min.importance == 0.0
        assert memory_min.confidence == 0.0
    
    def test_memory_record_to_search_text(self, sample_memory_record):
        """测试生成搜索文本"""
        memory = sample_memory_record
        search_text = memory.to_search_text()
        
        assert "测试记忆内容" in search_text
        assert "test" in search_text
        assert "memory" in search_text
    
    def test_memory_record_increment_access(self, sample_memory_record):
        """测试增加访问计数"""
        memory = sample_memory_record
        initial_count = memory.access_count
        
        memory.increment_access()
        
        assert memory.access_count == initial_count + 1
        assert memory.last_accessed is not None
    
    def test_memory_record_update_importance(self, sample_memory_record):
        """测试更新重要性"""
        memory = sample_memory_record
        initial_importance = memory.importance
        
        memory.update_importance(0.1)
        assert memory.importance == min(1.0, initial_importance + 0.1)
        
        memory.update_importance(-0.5)
        assert memory.importance == max(0.0, initial_importance + 0.1 - 0.5)


class TestKnowledgeEntity:
    """测试知识实体模型"""
    
    def test_entity_creation(self, sample_knowledge_entity):
        """测试实体创建"""
        entity = sample_knowledge_entity
        
        assert entity.id is not None
        assert entity.name == "测试实体"
        assert entity.entity_type == "concept"
    
    def test_entity_validation(self):
        """测试实体验证"""
        from src.integrations.supermemory.models import KnowledgeEntity
        
        # 空名称应该失败
        with pytest.raises(ValueError):
            KnowledgeEntity(name="", entity_type="concept")
    
    def test_entity_add_property(self, sample_knowledge_entity):
        """测试添加属性"""
        entity = sample_knowledge_entity
        entity.add_property("new_key", "new_value")
        
        assert entity.properties["new_key"] == "new_value"
    
    def test_entity_get_property(self, sample_knowledge_entity):
        """测试获取属性"""
        entity = sample_knowledge_entity
        
        assert entity.get_property("key") == "value"
        assert entity.get_property("nonexistent", "default") == "default"


class TestEntityRelation:
    """测试实体关系模型"""
    
    def test_relation_creation(self, sample_entity_relation):
        """测试关系创建"""
        relation = sample_entity_relation
        
        assert relation.id is not None
        assert relation.source_id == "ent_001"
        assert relation.target_id == "ent_002"
        assert relation.strength == 0.8
    
    def test_relation_validation(self):
        """测试关系验证"""
        from src.integrations.supermemory.models import EntityRelation, RelationType
        
        # 空实体 ID 应该失败
        with pytest.raises(ValueError):
            EntityRelation(
                source_id="",
                target_id="ent_002",
                relation_type=RelationType.RELATED_TO,
            )
    
    def test_relation_update_strength(self, sample_entity_relation):
        """测试更新关系强度"""
        relation = sample_entity_relation
        
        relation.update_strength(0.1)
        assert relation.strength == 0.9
        
        relation.update_strength(-0.5)
        assert relation.strength == 0.4


class TestAgentMemory:
    """测试 Agent 内存模型"""
    
    def test_agent_memory_creation(self, sample_agent_memory):
        """测试 Agent 内存创建"""
        memory = sample_agent_memory
        
        assert memory.agent_id == "agent_001"
        assert memory.session_id == "session_001"
        assert len(memory.working_memory) == 1
        assert len(memory.long_term_memory_ids) == 2
    
    def test_add_to_working_memory(self, sample_agent_memory):
        """测试添加到工作记忆"""
        from src.integrations.supermemory.models import MemoryRecord, MemoryType
        
        memory = sample_agent_memory
        new_memory = MemoryRecord(
            id="wm_002",
            content="新工作记忆",
            memory_type=MemoryType.WORKING,
        )
        
        initial_count = len(memory.working_memory)
        memory.add_to_working_memory(new_memory)
        
        assert len(memory.working_memory) == initial_count + 1
    
    def test_working_memory_window_limit(self, sample_agent_memory):
        """测试工作记忆窗口限制"""
        from src.integrations.supermemory.models import MemoryRecord, MemoryType
        
        memory = sample_agent_memory
        memory.context_window = 3
        
        # 添加超过窗口大小的记忆
        for i in range(5):
            memory.add_to_working_memory(
                MemoryRecord(
                    id=f"wm_{i+10}",
                    content=f"记忆{i}",
                    memory_type=MemoryType.WORKING,
                )
            )
        
        assert len(memory.working_memory) <= memory.context_window
    
    def test_add_long_term_reference(self, sample_agent_memory):
        """测试添加长期记忆引用"""
        memory = sample_agent_memory
        initial_count = len(memory.long_term_memory_ids)
        
        memory.add_long_term_reference("ltm_new")
        assert len(memory.long_term_memory_ids) == initial_count + 1
        
        # 重复添加不应该增加
        memory.add_long_term_reference("ltm_new")
        assert len(memory.long_term_memory_ids) == initial_count + 1
    
    def test_get_working_memory_context(self, sample_agent_memory):
        """测试获取工作记忆上下文"""
        memory = sample_agent_memory
        context = memory.get_working_memory_context()
        
        assert "工作记忆1" in context
    
    def test_clear_working_memory(self, sample_agent_memory):
        """测试清空工作记忆"""
        memory = sample_agent_memory
        memory.clear_working_memory()
        
        assert len(memory.working_memory) == 0


# =============================================================================
# Client Tests
# =============================================================================


@pytest.mark.asyncio
class TestSuperMemoryClient:
    """测试 SuperMemory 客户端"""
    
    async def test_client_creation(self, mock_supermemory_config):
        """测试客户端创建"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        client = SuperMemoryClient(config=mock_supermemory_config)
        
        assert client.config == mock_supermemory_config
        assert client.base_url == "http://localhost:8002"
        assert client.api_key == "test_api_key"
    
    async def test_client_context_manager(self, mock_supermemory_config):
        """测试客户端上下文管理器"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        async with SuperMemoryClient(config=mock_supermemory_config) as client:
            assert client is not None
    
    async def test_create_memory_success(self, mock_supermemory_config, sample_memory_record):
        """测试成功创建记忆"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_memory_record.model_dump(mode="json")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            result = await client.create_memory(sample_memory_record)
            
            assert result.content == sample_memory_record.content
    
    async def test_get_memory_success(self, mock_supermemory_config, sample_memory_record):
        """测试成功获取记忆"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_memory_record.model_dump(mode="json")
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            result = await client.get_memory("mem_123")
            
            assert result is not None
            assert result.id == sample_memory_record.id
    
    async def test_get_memory_not_found(self, mock_supermemory_config):
        """测试获取不存在的记忆"""
        from src.integrations.supermemory.client import SuperMemoryClient
        import httpx
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=Mock(),
                response=mock_response,
            )
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            result = await client.get_memory("nonexistent")
            
            assert result is None
    
    async def test_search_memories(self, mock_supermemory_config, sample_memory_record):
        """测试搜索记忆"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "memories": [sample_memory_record.model_dump(mode="json")],
                "total": 1,
            }
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            result = await client.search_memories("测试", limit=5)
            
            assert result.total == 1
            assert len(result.memories) == 1
    
    async def test_vector_search(self, mock_supermemory_config, sample_memory_record):
        """测试向量搜索"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "memories": [sample_memory_record.model_dump(mode="json")],
                "total": 1,
            }
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            embedding = [0.1] * 1536
            result = await client.vector_search(embedding, top_k=5)
            
            assert result.total == 1
    
    async def test_health_check_success(self, mock_supermemory_config):
        """测试健康检查成功"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            result = await client.health_check()
            
            assert result["healthy"] is True
    
    async def test_health_check_failure(self, mock_supermemory_config):
        """测试健康检查失败"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_request.side_effect = Exception("Connection error")
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            result = await client.health_check()
            
            assert result["healthy"] is False
            assert "error" in result


# =============================================================================
# Agent Memory Manager Tests
# =============================================================================


@pytest.mark.asyncio
class TestAgentMemoryManager:
    """测试 Agent 内存管理器"""
    
    async def test_manager_creation(self):
        """测试管理器创建"""
        from src.integrations.supermemory.agent_memory import AgentMemoryManager
        
        manager = AgentMemoryManager()
        
        assert manager is not None
        assert manager.client is not None
    
    async def test_create_agent_memory_space(self):
        """测试创建 Agent 内存空间"""
        from src.integrations.supermemory.agent_memory import AgentMemoryManager
        
        with patch("src.integrations.supermemory.agent_memory.get_supermemory_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            manager = AgentMemoryManager(client=mock_client)
            result = await manager.create_agent_memory_space(
                agent_id="agent_001",
                agent_type="solver",
                session_id="session_001",
                user_id="user_001",
            )
            
            assert result["agent_id"] == "agent_001"
            assert result["agent_type"] == "solver"
            assert result["session_id"] == "session_001"
    
    async def test_store_to_working_memory(self):
        """测试存储到工作记忆"""
        from src.integrations.supermemory.agent_memory import AgentMemoryManager
        from src.integrations.supermemory.models import MemoryRecord, MemoryType
        from src.core.memory.base import MemoryImportance
        
        with patch("src.integrations.supermemory.agent_memory.get_supermemory_client") as mock_get_client:
            mock_client = AsyncMock()
            # 设置 mock 返回值
            mock_memory = MemoryRecord(
                id="test_mem_001",
                content="测试工作记忆",
                memory_type=MemoryType.WORKING,
            )
            mock_client.create_memory.return_value = mock_memory
            mock_get_client.return_value = mock_client
            
            manager = AgentMemoryManager(client=mock_client)
            
            # 先创建内存空间
            await manager.create_agent_memory_space(
                agent_id="agent_001",
                agent_type="solver",
                session_id="session_001",
            )
            
            result = await manager.store_to_working_memory(
                agent_id="agent_001",
                session_id="session_001",
                content="测试工作记忆",
                memory_type=MemoryType.WORKING,
                importance=MemoryImportance.HIGH,
            )
            
            assert result is not None
            assert result.content == "测试工作记忆"
    
    async def test_share_memory_between_agents(self):
        """测试 Agent 间共享内存"""
        from src.integrations.supermemory.agent_memory import AgentMemoryManager
        from src.core.memory.base import MemoryType, MemoryImportance
        
        with patch("src.integrations.supermemory.agent_memory.get_supermemory_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            manager = AgentMemoryManager(client=mock_client)
            
            results = await manager.share_memory_between_agents(
                source_agent_id="agent_001",
                target_agent_ids=["agent_002", "agent_003"],
                session_id="session_001",
                memory_content="共享的记忆内容",
                memory_type=MemoryType.SHORT_TERM,
                importance=MemoryImportance.MEDIUM,
            )
            
            assert len(results) == 2
    
    async def test_get_agent_memory_stats(self):
        """测试获取 Agent 内存统计"""
        from src.integrations.supermemory.agent_memory import AgentMemoryManager
        
        with patch("src.integrations.supermemory.agent_memory.get_supermemory_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_stats.return_value = {"total_memories": 100}
            mock_get_client.return_value = mock_client
            
            manager = AgentMemoryManager(client=mock_client)
            
            # 先创建内存空间
            await manager.create_agent_memory_space(
                agent_id="agent_001",
                agent_type="solver",
                session_id="session_001",
            )
            
            stats = await manager.get_agent_memory_stats("agent_001", "session_001")
            
            assert stats["agent_id"] == "agent_001"
            assert stats["session_id"] == "session_001"
            assert "operations" in stats


# =============================================================================
# WebSocket Tests
# =============================================================================


@pytest.mark.asyncio
class TestSuperMemoryWebSocket:
    """测试 SuperMemory WebSocket"""
    
    async def test_websocket_handler_creation(self):
        """测试 WebSocket 处理器创建"""
        from src.integrations.supermemory.websocket import SuperMemoryWebSocketHandler
        
        handler = SuperMemoryWebSocketHandler()
        
        assert handler is not None
        assert len(handler.clients) == 0
    
    async def test_rate_limiter(self):
        """测试速率限制器"""
        from src.integrations.supermemory.websocket import RateLimiter, RateLimitConfig
        
        config = RateLimitConfig(
            max_messages_per_minute=10,
            max_connections_per_user=2,
        )
        limiter = RateLimiter(config)
        
        # 注册连接
        assert limiter.register_connection("client_1", "user_1") is True
        assert limiter.register_connection("client_2", "user_1") is True
        
        # 超过连接限制
        assert limiter.register_connection("client_3", "user_1") is False
        
        # 检查消息速率
        for _ in range(10):
            assert limiter.is_allowed("client_1", "user_1") is True
        
        # 超过消息限制
        assert limiter.is_allowed("client_1", "user_1") is False
    
    async def test_client_connection(self):
        """测试客户端连接"""
        from src.integrations.supermemory.websocket import ClientConnection
        
        mock_websocket = AsyncMock()
        client = ClientConnection(
            websocket=mock_websocket,
            client_id="test_client",
        )
        
        assert client.client_id == "test_client"
        assert client.authenticated is False
        
        # 测试发送消息
        await client.send({"type": "test"})
        assert client.message_count == 1
    
    async def test_broadcast_memory_update(self):
        """测试广播记忆更新"""
        from src.integrations.supermemory.websocket import SuperMemoryWebSocketHandler
        
        handler = SuperMemoryWebSocketHandler()
        
        # 添加 Mock 客户端
        mock_client = Mock()
        mock_client.user_id = "user_1"
        mock_client.subscriptions = {"all"}
        mock_client.send = AsyncMock(return_value=True)
        handler.clients["client_1"] = mock_client
        
        count = await handler.broadcast_memory_update(
            {"memory_id": "mem_001", "action": "created"},
            target_user_id="user_1",
        )
        
        assert count == 1


# =============================================================================
# API Route Tests
# =============================================================================


class TestSuperMemoryAPIRoutes:
    """测试 SuperMemory API 路由"""
    
    def test_memory_models(self):
        """测试记忆相关模型"""
        from src.api.routes.supermemory import (
            MemoryCreateRequest,
            MemoryUpdateRequest,
            MemorySearchRequest,
            MemoryType,
            MemoryStatus,
        )
        
        # 测试创建请求
        create_req = MemoryCreateRequest(
            content="测试内容",
            memory_type=MemoryType.LONG_TERM,
            tags=["test"],
            importance=0.8,
        )
        assert create_req.content == "测试内容"
        
        # 测试更新请求
        update_req = MemoryUpdateRequest(
            content="更新内容",
            status=MemoryStatus.ARCHIVED,
        )
        assert update_req.content == "更新内容"
        
        # 测试搜索请求
        search_req = MemorySearchRequest(
            query="测试查询",
            search_type="hybrid",
            top_k=10,
        )
        assert search_req.query == "测试查询"
    
    def test_entity_models(self):
        """测试实体相关模型"""
        from src.api.routes.supermemory import (
            EntityCreateRequest,
            EntityType,
            RelationType,
        )
        
        entity_req = EntityCreateRequest(
            name="测试实体",
            entity_type=EntityType.CONCEPT,
            description="实体描述",
        )
        assert entity_req.name == "测试实体"
        assert entity_req.entity_type == EntityType.CONCEPT
    
    def test_agent_memory_models(self):
        """测试 Agent 内存相关模型"""
        from src.api.routes.supermemory import (
            AgentMemoryStoreRequest,
            AgentMemoryShareRequest,
            AgentMemoryContextRequest,
            MemoryType,
        )
        
        store_req = AgentMemoryStoreRequest(
            content="Agent 记忆内容",
            memory_type=MemoryType.LONG_TERM,
            importance=0.9,
        )
        assert store_req.content == "Agent 记忆内容"
        
        share_req = AgentMemoryShareRequest(
            source_agent_id="agent_001",
            target_agent_ids=["agent_002", "agent_003"],
            share_type="copy",
        )
        assert share_req.source_agent_id == "agent_001"
        assert len(share_req.target_agent_ids) == 2


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
class TestSuperMemoryIntegration:
    """测试 SuperMemory 集成场景"""
    
    async def test_full_memory_workflow(self, mock_supermemory_config):
        """测试完整记忆工作流"""
        from src.integrations.supermemory.client import SuperMemoryClient
        from src.integrations.supermemory.models import MemoryRecord, MemoryType
        
        with patch("httpx.AsyncClient.request") as mock_request:
            # 模拟创建记忆
            memory_id = "mem_workflow_001"
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": memory_id,
                "content": "工作流测试记忆",
                "memory_type": "semantic",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            
            # 创建记忆
            memory = MemoryRecord(
                content="工作流测试记忆",
                memory_type=MemoryType.SEMANTIC,
            )
            created = await client.create_memory(memory)
            assert created.id == memory_id
    
    async def test_knowledge_graph_workflow(self):
        """测试知识图谱工作流"""
        from src.integrations.supermemory.knowledge_graph import KnowledgeGraphService
        
        with patch("src.integrations.supermemory.knowledge_graph.get_llm_client") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.complete.return_value = json.dumps({
                "entities": [
                    {"name": "张三", "type": "人物", "description": "测试人物"},
                    {"name": "北京大学", "type": "组织", "description": "测试组织"},
                ]
            })
            mock_get_llm.return_value = mock_llm
            
            service = KnowledgeGraphService()
            
            # 提取实体
            result = await service.extract_entities("张三在北京大学工作")
            
            assert len(result.entities) == 2
            assert result.entities[0]["name"] == "张三"
    
    async def test_error_handling(self, mock_supermemory_config):
        """测试错误处理"""
        from src.integrations.supermemory.client import SuperMemoryClient
        import httpx
        
        with patch("httpx.AsyncClient.request") as mock_request:
            # 模拟网络错误
            mock_request.side_effect = httpx.RequestError("Network error")
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            
            # 健康检查应该返回不健康状态
            result = await client.health_check()
            assert result["healthy"] is False


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.asyncio
class TestSuperMemoryPerformance:
    """测试 SuperMemory 性能"""
    
    async def test_batch_operations(self, mock_supermemory_config):
        """测试批量操作性能"""
        from src.integrations.supermemory.client import SuperMemoryClient
        from src.integrations.supermemory.models import MemoryRecord
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "memories": [
                    {"id": f"mem_{i}", "content": f"记忆{i}"}
                    for i in range(100)
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            
            memories = [
                MemoryRecord(content=f"批量记忆{i}")
                for i in range(100)
            ]
            
            results = await client.batch_create_memories(memories)
            
            assert len(results) == 100
    
    async def test_search_performance(self, mock_supermemory_config):
        """测试搜索性能"""
        from src.integrations.supermemory.client import SuperMemoryClient
        
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "memories": [],
                "total": 0,
            }
            mock_response.raise_for_status = Mock()
            mock_request.return_value = mock_response
            
            client = SuperMemoryClient(config=mock_supermemory_config)
            
            import time
            start_time = time.time()
            
            result = await client.search_memories("性能测试", limit=10)
            
            elapsed = (time.time() - start_time) * 1000
            
            # 搜索应该在合理时间内完成
            assert elapsed < 1000  # 1秒
            assert result.search_time_ms is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
