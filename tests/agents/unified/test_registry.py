"""
Agent Registry 单元测试
测试 AgentRegistry 的核心功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.unified.registry import AgentRegistry


# 测试Agent定义
class MockAgent:
    """模拟Agent类"""
    
    def __init__(self, name="mock_agent", **kwargs):
        self.name = name
        self.config = kwargs
    
    def process(self, input_data):
        return {"result": f"Processed: {input_data}"}


class TestAgentRegistry:
    """测试 AgentRegistry 类"""
    
    @pytest.fixture
    def registry(self):
        """创建registry实例"""
        # 重置单例
        AgentRegistry._instance = None
        return AgentRegistry()
    
    @pytest.fixture
    def mock_agent_class(self):
        """返回测试用的Agent类"""
        return MockAgent
    
    def test_singleton_pattern(self, registry):
        """测试单例模式"""
        # 获取另一个实例
        registry2 = AgentRegistry()
        
        # 应该是同一个实例
        assert registry is registry2
    
    def test_register_agent_class(self, registry, mock_agent_class):
        """测试注册Agent类"""
        # 注册Agent
        registry.register("test_agent", mock_agent_class)
        
        # 验证注册成功
        assert "test_agent" in registry.list_agents()
        assert registry.is_registered("test_agent")
    
    def test_register_and_get_agent(self, registry, mock_agent_class):
        """测试注册和获取Agent"""
        # 注册Agent
        registry.register("agent1", mock_agent_class)
        
        # 获取Agent实例
        agent = registry.get("agent1", name="instance1")
        
        # 验证
        assert isinstance(agent, MockAgent)
        assert agent.name == "instance1"
    
    def test_get_nonexistent_agent(self, registry):
        """测试获取不存在的Agent"""
        with pytest.raises(ValueError, match="Agent 'nonexistent' not registered"):
            registry.get("nonexistent")
    
    def test_list_agents(self, registry, mock_agent_class):
        """测试列出所有Agent"""
        # 注册多个Agent
        registry.register("agent1", mock_agent_class)
        registry.register("agent2", MockAgent)
        
        # 列出Agents
        agents = registry.list_agents()
        
        # 验证
        assert "agent1" in agents
        assert "agent2" in agents
        assert len(agents) == 2
    
    def test_unregister_agent(self, registry, mock_agent_class):
        """测试取消注册Agent"""
        # 注册Agent
        registry.register("agent1", mock_agent_class)
        assert "agent1" in registry.list_agents()
        
        # 取消注册
        registry.unregister("agent1")
        
        # 验证
        assert "agent1" not in registry.list_agents()
        assert not registry.is_registered("agent1")
    
    def test_unregister_nonexistent_agent(self, registry):
        """测试取消注册不存在的Agent"""
        # 不应该抛出错误,应该静默处理
        registry.unregister("nonexistent")
    
    def test_register_duplicate_agent(self, registry, mock_agent_class):
        """测试注册重复Agent"""
        # 注册Agent
        registry.register("agent1", mock_agent_class)
        
        # 尝试再次注册同名Agent,应该抛出错误
        with pytest.raises(ValueError, match="Agent 'agent1' already registered"):
            registry.register("agent1", MockAgent)
    
    def test_create_agent_with_config(self, registry, mock_agent_class):
        """测试创建带配置的Agent"""
        registry.register("agent1", mock_agent_class)
        
        # 创建Agent时传入配置
        config = {"name": "configured_agent", "value": 123}
        agent = registry.get("agent1", **config)
        
        # 验证
        assert agent.name == "configured_agent"
        assert agent.config == config
    
    def test_get_stats(self, registry, mock_agent_class):
        """测试获取统计信息"""
        registry.register("agent1", mock_agent_class)
        registry.register("agent2", MockAgent)
        
        # 创建一些实例
        registry.get("agent1")
        registry.get("agent1")
        registry.get("agent2")
        
        # 获取统计信息
        stats = registry.get_stats()
        
        # 验证
        assert stats["total_registered"] == 2
        assert stats["total_created"] == 3
        assert stats["agents"]["agent1"]["created_count"] == 2
        assert stats["agents"]["agent2"]["created_count"] == 1
    
    def test_clear(self, registry, mock_agent_class):
        """测试清空注册表"""
        # 注册Agents
        registry.register("agent1", mock_agent_class)
        registry.register("agent2", MockAgent)
        
        # 清空
        registry.clear()
        
        # 验证
        assert len(registry.list_agents()) == 0
    
    @patch('src.agents.unified.registry.AgentRegistry._create_from_spec')
    def test_auto_discover(self, mock_create, registry):
        """测试自动发现Agents"""
        # 模拟Agent规范
        mock_create.return_value = MockAgent
        
        # 自动发现
        discovered = registry.auto_discover()
        
        # 验证mock被调用
        mock_create.assert_called()
    
    def test_decorator_registration(self, registry):
        """测试装饰器注册"""
        # 使用装饰器注册
        @AgentRegistry.register()
        class DecoratedAgent:
            pass
        
        # 验证自动注册
        assert "DecoratedAgent" in registry.list_agents()
        assert registry.is_registered("DecoratedAgent")


# 测试注册函数
class TestRegistryFunctions:
    """测试注册表辅助函数"""
    
    def test_register_agent_function(self):
        """测试register_agent函数"""
        from src.agents.unified.registry import register_agent
        
        # 重置单例
        AgentRegistry._instance = None
        
        # 使用函数注册
        @register_agent("custom_agent")
        class CustomAgent:
            pass
        
        # 验证
        registry = AgentRegistry()
        assert "custom_agent" in registry.list_agents()
    
    def test_get_agent_function(self):
        """测试get_agent函数"""
        from src.agents.unified.registry import get_agent
        
        AgentRegistry._instance = None
        registry = AgentRegistry()
        registry.register("test", MockAgent)
        
        # 使用函数获取
        agent = get_agent("test", name="test_instance")
        
        # 验证
        assert isinstance(agent, MockAgent)
        assert agent.name == "test_instance"
    
    def test_create_agent_function(self):
        """测试create_agent函数"""
        from src.agents.unified.registry import create_agent, AgentInput
        
        AgentRegistry._instance = None
        registry = AgentRegistry()
        
        # 创建一个完整的Agent
        @registry.register("test_agent")
        class SimpleAgent:
            def __init__(self):
                self.processed = False
            
            def process(self, input_data):
                self.processed = True
                return {"result": "ok"}
        
        # 使用create_agent函数
        agent = create_agent("test_agent")
        
        # 验证
        assert agent is not None
        result = agent.process("test")
        assert result["result"] == "ok"
    
    def test_initialize_agent_function(self):
        """测试initialize_agent函数"""
        from src.agents.unified.registry import initialize_agent
        
        AgentRegistry._instance = None
        registry = AgentRegistry()
        registry.register("test", MockAgent)
        
        # 初始化Agent
        agent = initialize_agent("test", name="initialized_agent")
        
        # 验证
        assert isinstance(agent, MockAgent)
        assert agent.name == "initialized_agent"


# 并发测试
class TestConcurrentAccess:
    """测试并发访问"""
    
    @pytest.mark.asyncio
    async def test_concurrent_registration(self):
        """测试并发注册"""
        import asyncio
        AgentRegistry._instance = None
        registry = AgentRegistry()
        
        async def register_agent(name):
            class TempAgent:
                pass
            registry.register(name, TempAgent)
        
        # 并发注册100个Agent
        tasks = [register_agent(f"agent_{i}") for i in range(100)]
        await asyncio.gather(*tasks)
        
        # 验证
        assert len(registry.list_agents()) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """测试并发访问"""
        import asyncio
        AgentRegistry._instance = None
        registry = AgentRegistry()
        registry.register("test", MockAgent)
        
        async def create_agent():
            return registry.get("test")
        
        # 并发创建50个Agent实例
        agents = await asyncio.gather(*[create_agent() for _ in range(50)])
        
        # 验证
        assert len(agents) == 50
        assert all(isinstance(agent, MockAgent) for agent in agents)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/agents/unified/registry", "--cov-report=html"])
