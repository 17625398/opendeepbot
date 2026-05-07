"""
ClawX Integration Tests
=======================

测试 ClawX 集成功能。
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.integrations.clawx import (
    ClawXConfigManager,
    DeepTutorSkillAdapter,
    get_clawx_gateway,
)
from src.integrations.clawx.gateway import ClawXMessage


class TestClawXMessage:
    """测试 ClawXMessage 类"""
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = ClawXMessage(
            msg_type="test",
            content={"data": "value"},
            session_id="session-123"
        )
        
        assert msg.type == "test"
        assert msg.content == {"data": "value"}
        assert msg.session_id == "session-123"
        assert msg.id is not None
        assert msg.timestamp is not None
    
    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = ClawXMessage(
            msg_type="test",
            content={"data": "value"}
        )
        
        data = msg.to_dict()
        assert data["type"] == "test"
        assert data["content"] == {"data": "value"}
        assert "id" in data
        assert "timestamp" in data
    
    def test_message_from_dict(self):
        """测试从字典创建消息"""
        data = {
            "id": "msg-123",
            "type": "test",
            "content": {"data": "value"},
            "session_id": "session-123",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        msg = ClawXMessage.from_dict(data)
        assert msg.id == "msg-123"
        assert msg.type == "test"
        assert msg.content == {"data": "value"}
        assert msg.session_id == "session-123"

    def test_message_from_dict_nested_skill_fields(self):
        data = {
            "type": "skill_invoke",
            "content": {"skill_id": "deeptutor-solver", "parameters": {"prompt": "hi"}},
        }

        msg = ClawXMessage.from_dict(data)
        assert msg.type == "skill_invoke"
        assert msg.skill_id == "deeptutor-solver"
        assert msg.parameters == {"prompt": "hi"}


class TestClawXConfigManager:
    """测试 ClawXConfigManager 类"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = ClawXConfigManager()
        manager2 = ClawXConfigManager()
        
        assert manager1 is manager2
    
    def test_default_config(self):
        """测试默认配置"""
        manager = ClawXConfigManager()
        config = manager.get_config_object()
        
        assert config.gateway_host == "127.0.0.1"
        assert config.gateway_port == 18789
        assert config.default_model == "gpt-4"
        assert config.theme in ["dark", "light", "system"]
        assert config.language == "zh-CN"
    
    def test_get_gateway_url(self):
        """测试获取 Gateway URL"""
        manager = ClawXConfigManager()
        url = manager.get_gateway_url()
        
        assert url == "ws://127.0.0.1:18789"


class TestDeepTutorSkillAdapter:
    """测试 DeepTutorSkillAdapter 类"""
    
    @pytest.fixture
    def adapter(self):
        return DeepTutorSkillAdapter(
            agent_id="test_agent",
            skill_id="test_skill",
            skill_name="Test Skill",
            description="Test description"
        )
    
    def test_adapter_creation(self, adapter):
        """测试适配器创建"""
        assert adapter.agent_id == "test_agent"
        assert adapter.skill_id == "test_skill"
        assert adapter.skill_name == "Test Skill"
        assert adapter.description == "Test description"
        assert adapter.agent is None
    
    def test_to_clawx_skill_definition(self, adapter):
        """测试转换为 ClawX Skill 定义"""
        definition = adapter.to_clawx_skill_definition()
        
        assert definition["id"] == "test_skill"
        assert definition["name"] == "Test Skill"
        assert definition["description"] == "Test description"
        assert definition["version"] == "1.0.0"
        assert definition["author"] == "DeepTutor"
        assert "parameters" in definition
        assert "returns" in definition


class TestClawXGateway:
    """测试 ClawXGateway 类"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        gateway1 = get_clawx_gateway()
        gateway2 = get_clawx_gateway()
        
        assert gateway1 is gateway2
    
    def test_default_config(self):
        """测试默认配置"""
        gateway = get_clawx_gateway()
        
        assert gateway.host == "127.0.0.1"
        assert gateway.port == 18789
        assert gateway.running is False
    
    def test_get_session_stats(self):
        """测试获取会话统计"""
        gateway = get_clawx_gateway()
        stats = gateway.get_session_stats()
        
        assert "total_sessions" in stats
        assert "authenticated_sessions" in stats
        assert "running" in stats
        assert "host" in stats
        assert "port" in stats


@pytest.mark.asyncio
class TestClawXAsync:
    """异步测试"""
    
    async def test_config_manager_update(self):
        """测试配置更新"""
        manager = ClawXConfigManager()
        
        # 测试更新配置
        success = manager.update_config({"theme": "light"})
        
        # 验证更新
        config = manager.get_config_object()
        assert config.theme == "light"
    
    async def test_skill_adapter_execution_mock(self):
        """测试 Skill 适配器执行（Mock）"""
        adapter = DeepTutorSkillAdapter(
            agent_id="test_agent",
            skill_id="test_skill",
            skill_name="Test Skill",
            description="Test"
        )
        
        # 创建 Mock 会话
        mock_session = Mock()
        mock_session.session_id = "session-123"
        mock_session.user_id = "user-123"
        mock_session.send = AsyncMock()
        
        # 由于无法初始化真实 Agent，测试初始化失败情况
        with pytest.raises(Exception):
            await adapter.execute({"prompt": "test"}, mock_session)

    async def test_gateway_auth_api_key(self):
        gateway = get_clawx_gateway()
        manager = ClawXConfigManager()
        manager._config.auth_type = "api_key"
        manager._config.api_key = "secret"

        session = Mock()
        session.session_id = "session-1"
        session.authenticated = False
        session.user_id = None
        session.send = AsyncMock()

        await gateway._handle_auth(
            session,
            ClawXMessage(msg_type="auth", content={"token": "secret", "user_id": "u1"}),
        )

        assert session.authenticated is True
        assert session.user_id == "u1"
        assert session.send.called is True

    async def test_gateway_skill_invoke_disabled(self):
        gateway = get_clawx_gateway()
        manager = ClawXConfigManager()
        manager._config.enabled_skills = ["allowed-skill"]

        async def handler(parameters, session):
            return {"success": True, "result": "ok"}

        gateway.register_skill_handler("allowed-skill", handler)

        session = Mock()
        session.session_id = "session-1"
        session.authenticated = True
        session.user_id = "u1"
        session.send = AsyncMock()

        await gateway._handle_skill_invoke(
            session,
            ClawXMessage(msg_type="skill_invoke", skill_id="blocked-skill", parameters={"prompt": "hi"}),
        )

        assert session.send.called is True
        sent = session.send.call_args.args[0]
        assert isinstance(sent, ClawXMessage)
        assert sent.type == "skill_error"

    async def test_gateway_skill_invoke_memory_injection(self):
        gateway = get_clawx_gateway()
        manager = ClawXConfigManager()
        manager._config.enabled_skills = ["allowed-skill"]

        async def handler(parameters, session):
            assert parameters["context"]["memory_snippets"] == ["m1", "m2"]
            return {"success": True, "result": "ok"}

        gateway.register_skill_handler("allowed-skill", handler)

        session = Mock()
        session.session_id = "session-1"
        session.authenticated = True
        session.user_id = "u1"
        session.send = AsyncMock()

        fake_memory = Mock()
        fake_memory.retrieve_memories = AsyncMock(
            return_value=[Mock(content="m1"), Mock(content="m2")]
        )
        fake_memory.store_memory = AsyncMock(return_value=True)

        with patch(
            "src.integrations.clawx.gateway.get_enhanced_memory",
            new=AsyncMock(return_value=fake_memory),
        ):
            await gateway._handle_skill_invoke(
                session,
                ClawXMessage(
                    msg_type="skill_invoke",
                    skill_id="allowed-skill",
                    parameters={"prompt": "hi", "context": {}},
                ),
            )

        assert fake_memory.retrieve_memories.called is True
        assert fake_memory.store_memory.called is True

    async def test_gateway_feedback_stores_memory(self):
        gateway = get_clawx_gateway()

        session = Mock()
        session.session_id = "session-1"
        session.authenticated = True
        session.user_id = "u1"
        session.send = AsyncMock()

        fake_memory = Mock()
        fake_memory.store_memory = AsyncMock(return_value=True)

        with patch(
            "src.integrations.clawx.gateway.get_enhanced_memory",
            new=AsyncMock(return_value=fake_memory),
        ):
            await gateway._route_message(
                session,
                ClawXMessage(
                    msg_type="feedback",
                    content={
                        "skill_id": "allowed-skill",
                        "prompt": "hi",
                        "response": "ok",
                        "rating": 5,
                        "comment": "good",
                    },
                ),
            )

        assert fake_memory.store_memory.called is True
        assert session.send.called is True
        sent = session.send.call_args.args[0]
        assert isinstance(sent, ClawXMessage)
        assert sent.type == "feedback_saved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
