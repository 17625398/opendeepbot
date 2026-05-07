#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 工厂模式单元测试
"""

from unittest.mock import Mock, patch

import pytest

from src.agents.interrogation.agent_factory import (
    AgentConfig,
    AgentFactory,
    AgentType,
    create_agent,
)
from src.agents.interrogation.agents.extract_agent import ExtractAgent
from src.agents.interrogation.agents.legal_match_agent import LegalMatchAgent


class TestAgentConfig:
    """测试 AgentConfig 类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = AgentConfig()
        assert config.api_key is None
        assert config.base_url is None
        assert config.model is None
        assert config.binding is None
        assert config.language == "zh"
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = AgentConfig(
            api_key="test_key",
            base_url="http://test.com",
            model="gpt-4",
            binding="openai",
            language="en"
        )
        assert config.api_key == "test_key"
        assert config.base_url == "http://test.com"
        assert config.model == "gpt-4"
        assert config.binding == "openai"
        assert config.language == "en"
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = AgentConfig(
            api_key="test_key",
            model="gpt-4",
            custom_field="custom_value"
        )
        config_dict = config.to_dict()
        assert config_dict["api_key"] == "test_key"
        assert config_dict["model"] == "gpt-4"
        assert config_dict["custom_field"] == "custom_value"
        assert "base_url" not in config_dict  # None 值被过滤


class TestAgentFactory:
    """测试 AgentFactory 类"""
    
    def test_list_agent_types(self):
        """测试列出所有 Agent 类型"""
        agent_types = AgentFactory.list_agent_types()
        assert len(agent_types) == 9
        assert AgentType.EXTRACT in agent_types
        assert AgentType.LEGAL_MATCH in agent_types
    
    def test_get_agent_class(self):
        """测试获取 Agent 类"""
        agent_class = AgentFactory.get_agent_class(AgentType.EXTRACT)
        assert agent_class == ExtractAgent
        
        agent_class = AgentFactory.get_agent_class(AgentType.LEGAL_MATCH)
        assert agent_class == LegalMatchAgent
    
    @patch('src.services.llm.get_llm_config')
    def test_create_agent_with_default_config(self, mock_get_llm_config):
        """测试使用默认配置创建 Agent"""
        mock_config = Mock()
        mock_config.api_key = "test_key"
        mock_config.base_url = "http://test.com"
        mock_config.model = "gpt-4"
        mock_config.binding = "openai"
        mock_get_llm_config.return_value = mock_config

        agent = AgentFactory.create_agent(AgentType.EXTRACT)
        assert isinstance(agent, ExtractAgent)
    
    def test_create_agent_with_custom_config(self):
        """测试使用自定义配置创建 Agent"""
        config = AgentConfig(
            api_key="test_key",
            base_url="http://test.com",
            model="gpt-4",
            binding="openai"
        )
        
        agent = AgentFactory.create_agent(AgentType.EXTRACT, config)
        assert isinstance(agent, ExtractAgent)
    
    def test_singleton_mode(self):
        """测试单例模式"""
        config = AgentConfig(api_key="test_key", model="gpt-4")
        
        # 创建两个 Agent，使用单例模式
        agent1 = AgentFactory.create_agent(AgentType.EXTRACT, config, use_singleton=True)
        agent2 = AgentFactory.create_agent(AgentType.EXTRACT, config, use_singleton=True)
        
        # 应该是同一个实例
        assert agent1 is agent2
    
    def test_non_singleton_mode(self):
        """测试非单例模式"""
        config = AgentConfig(api_key="test_key", model="gpt-4")
        
        # 创建两个 Agent，不使用单例模式
        agent1 = AgentFactory.create_agent(AgentType.EXTRACT, config, use_singleton=False)
        agent2 = AgentFactory.create_agent(AgentType.EXTRACT, config, use_singleton=False)
        
        # 应该是不同实例
        assert agent1 is not agent2
    
    def test_create_pipeline_agents(self):
        """测试创建 Pipeline Agents"""
        config = AgentConfig(api_key="test_key", model="gpt-4")
        agents = AgentFactory.create_pipeline_agents(config)
        
        assert "extract" in agents
        assert "legal_match" in agents
        assert "quality" in agents
        assert "relation" in agents
        assert "report" in agents
        assert len(agents) == 5
    
    def test_create_advanced_agents(self):
        """测试创建高级 Agents"""
        config = AgentConfig(api_key="test_key", model="gpt-4")
        agents = AgentFactory.create_advanced_agents(config)
        
        assert "cross_record" in agents
        assert "case_report" in agents
        assert "evidence_chain" in agents
        assert "knowledge_graph" in agents
        assert len(agents) == 4
    
    def test_clear_cache(self):
        """测试清除缓存"""
        config = AgentConfig(api_key="test_key", model="gpt-4")
        
        # 创建单例 Agent
        agent1 = AgentFactory.create_agent(AgentType.EXTRACT, config, use_singleton=True)
        
        # 清除缓存
        AgentFactory.clear_cache()
        
        # 再次创建，应该是新实例
        agent2 = AgentFactory.create_agent(AgentType.EXTRACT, config, use_singleton=True)
        assert agent1 is not agent2


class TestCreateAgentFunction:
    """测试 create_agent 便捷函数"""
    
    def test_create_agent_by_string(self):
        """测试通过字符串创建 Agent"""
        agent = create_agent(
            "extract",
            api_key="test_key",
            base_url="http://test.com",
            model="gpt-4"
        )
        assert isinstance(agent, ExtractAgent)
    
    def test_create_agent_invalid_type(self):
        """测试创建无效的 Agent 类型"""
        with pytest.raises(ValueError) as exc_info:
            create_agent("invalid_type")
        assert "未知的 Agent 类型" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])