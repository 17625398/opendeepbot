"""
Knowledge Graph Configuration Utilities
知识图谱配置工具

提供统一的配置加载机制，支持从环境变量读取配置。
所有知识图谱相关模块应使用此工具获取配置。

Configuration Priority:
1. Environment variables (HYPEREXTRACT_*, KG_*, etc.)
2. Global DeepTutor configuration
3. Default values
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class KGConfig:
    """
    Knowledge Graph Configuration
    
    Provides unified configuration access for all knowledge graph modules.
    Supports loading from environment variables.
    """
    
    # Configuration keys
    ENV_PREFIX = "KG_"
    HYPEREXTRACT_PREFIX = "HYPEREXTRACT_"
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # LLM Configuration
        self.llm_provider = self._get_env("LLM_PROVIDER", "ollama")
        self.llm_model = self._get_env("LLM_MODEL", "deepseek-chat")
        self.llm_api_key = self._get_env("LLM_API_KEY", "")
        self.llm_base_url = self._get_env("LLM_BASE_URL", "")
        
        # Ollama-specific configuration
        self.ollama_base_url = self._get_env("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Neo4j Configuration
        self.neo4j_uri = self._get_env("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = self._get_env("NEO4J_USER", "neo4j")
        self.neo4j_password = self._get_env("NEO4J_PASSWORD", "password")
        
        # Graph Storage Configuration
        self.graph_storage_backend = self._get_env("STORAGE_BACKEND", "memory")
        self.graph_data_dir = self._get_env("DATA_DIR", "./data/kg")
        
        # Extraction Configuration
        self.extraction_enabled = self._get_env_bool("EXTRACTION_ENABLED", True)
        self.extraction_timeout = self._get_env_int("EXTRACTION_TIMEOUT", 120)
        self.extraction_batch_size = self._get_env_int("EXTRACTION_BATCH_SIZE", 10)
        
        # Visualization Configuration
        self.visualization_enabled = self._get_env_bool("VISUALIZATION_ENABLED", True)
        self.visualization_engine = self._get_env("VISUALIZATION_ENGINE", "d3")
        
        logger.info(f"Knowledge Graph Config loaded: provider={self.llm_provider}, model={self.llm_model}")
    
    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable value with fallback"""
        # Try HYPEREXTRACT_ prefix first
        hyper_key = f"{self.HYPEREXTRACT_PREFIX}{key}"
        if hyper_key in os.environ:
            return os.environ[hyper_key]
        
        # Try KG_ prefix
        kg_key = f"{self.ENV_PREFIX}{key}"
        if kg_key in os.environ:
            return os.environ[kg_key]
        
        # Try without prefix
        if key in os.environ:
            return os.environ[key]
        
        return default
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = self._get_env(key, str(default))
        return value.lower() in ("true", "1", "yes", "enabled")
    
    def _get_env_int(self, key: str, default: int = 0) -> int:
        """Get integer environment variable"""
        value = self._get_env(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_api_key": "***" if self.llm_api_key else "",
            "llm_base_url": self.llm_base_url,
            "ollama_base_url": self.ollama_base_url,
            "neo4j_uri": self.neo4j_uri,
            "neo4j_user": self.neo4j_user,
            "graph_storage_backend": self.graph_storage_backend,
            "graph_data_dir": self.graph_data_dir,
            "extraction_enabled": self.extraction_enabled,
            "extraction_timeout": self.extraction_timeout,
            "visualization_enabled": self.visualization_enabled,
            "visualization_engine": self.visualization_engine,
        }


# Global configuration instance
_kg_config: Optional[KGConfig] = None


def get_kg_config() -> KGConfig:
    """Get global knowledge graph configuration instance"""
    global _kg_config
    if _kg_config is None:
        _kg_config = KGConfig()
    return _kg_config


def reload_kg_config() -> KGConfig:
    """Reload configuration from environment"""
    global _kg_config
    _kg_config = KGConfig()
    return _kg_config


def get_llm_settings() -> Dict[str, str]:
    """Get LLM-related settings for knowledge graph operations"""
    config = get_kg_config()
    return {
        "provider": config.llm_provider,
        "model": config.llm_model,
        "api_key": config.llm_api_key,
        "base_url": config.llm_base_url or config.ollama_base_url,
    }


def get_neo4j_settings() -> Dict[str, str]:
    """Get Neo4j database settings"""
    config = get_kg_config()
    return {
        "uri": config.neo4j_uri,
        "user": config.neo4j_user,
        "password": config.neo4j_password,
    }


# Backward compatibility - for Hyper-Extract specific config
def get_hyperextract_config() -> Dict[str, Any]:
    """Get Hyper-Extract specific configuration"""
    config = get_kg_config()
    return {
        "llm_provider": config.llm_provider,
        "llm_model": config.llm_model,
        "llm_api_key": config.llm_api_key,
        "llm_base_url": config.llm_base_url,
        "ollama_base_url": config.ollama_base_url,
    }
