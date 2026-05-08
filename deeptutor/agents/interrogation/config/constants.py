#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interrogation 模块配置常量

集中管理所有硬编码值，便于维护和调整。

Configuration:
    Integrates with unified KGConfig from deeptutor.tools.kg_config
    Environment variables with KG_* prefix take precedence
"""

import os
from dataclasses import dataclass
from typing import Any, Dict


def _get_env(key: str, default):
    """Get environment variable with KG_ prefix support"""
    kg_key = f"KG_{key}"
    if kg_key in os.environ:
        return os.environ[kg_key]
    if key in os.environ:
        return os.environ[key]
    return default


def _get_env_int(key: str, default: int) -> int:
    """Get integer environment variable"""
    value = _get_env(key, str(default))
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    """Get float environment variable"""
    value = _get_env(key, str(default))
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AnalysisSteps:
    """分析步骤配置"""
    EXTRACT: Dict[str, Any] = None
    RELATION: Dict[str, Any] = None
    LEGAL_MATCH: Dict[str, Any] = None
    QUALITY: Dict[str, Any] = None
    REPORT: Dict[str, Any] = None
    
    def __post_init__(self):
        object.__setattr__(self, 'EXTRACT', {"progress": 10, "message": "正在提取关键信息...", "name": "extract"})
        object.__setattr__(self, 'RELATION', {"progress": 30, "message": "正在分析人物关系...", "name": "relation"})
        object.__setattr__(self, 'LEGAL_MATCH', {"progress": 50, "message": "正在匹配法律法规...", "name": "legal_match"})
        object.__setattr__(self, 'QUALITY', {"progress": 70, "message": "正在评估笔录质量...", "name": "quality"})
        object.__setattr__(self, 'REPORT', {"progress": 90, "message": "正在生成分析报告...", "name": "report"})


@dataclass(frozen=True)
class Timeouts:
    """超时配置（秒）
    
    Supports environment variables:
    - KG_DEFAULT_TIMEOUT
    - KG_OLLAMA_TIMEOUT
    - KG_CONNECT_TIMEOUT
    - KG_SOCK_READ_TIMEOUT
    - KG_STREAM_SOCK_READ_TIMEOUT
    - KG_CHECK_TIMEOUT
    """
    DEFAULT_TIMEOUT: int = _get_env_int("DEFAULT_TIMEOUT", 300)
    OLLAMA_TIMEOUT: int = _get_env_int("OLLAMA_TIMEOUT", 1800)
    CONNECT_TIMEOUT: int = _get_env_int("CONNECT_TIMEOUT", 30)
    SOCK_READ_TIMEOUT: int = _get_env_int("SOCK_READ_TIMEOUT", 300)
    STREAM_SOCK_READ_TIMEOUT: int = _get_env_int("STREAM_SOCK_READ_TIMEOUT", 60)
    CHECK_TIMEOUT: int = _get_env_int("CHECK_TIMEOUT", 10)


@dataclass(frozen=True)
class CacheConfig:
    """缓存配置
    
    Supports environment variables:
    - KG_MAX_MEMORY_CACHE_SIZE
    - KG_DEFAULT_TTL
    - KG_CLEANUP_INTERVAL
    """
    MAX_MEMORY_CACHE_SIZE: int = _get_env_int("MAX_MEMORY_CACHE_SIZE", 100)
    DEFAULT_TTL: int = _get_env_int("DEFAULT_TTL", 3600)  # 1小时
    CLEANUP_INTERVAL: int = _get_env_int("CLEANUP_INTERVAL", 300)  # 5分钟


@dataclass(frozen=True)
class LLMDefaults:
    """LLM 配置
    
    Supports environment variables:
    - KG_DEFAULT_TEMPERATURE
    - KG_DEFAULT_MAX_TOKENS
    - KG_DEFAULT_NUM_CTX
    - KG_RAG_TOP_K
    """
    DEFAULT_TEMPERATURE: float = _get_env_float("DEFAULT_TEMPERATURE", 0.7)
    DEFAULT_MAX_TOKENS: int = _get_env_int("DEFAULT_MAX_TOKENS", 4000)
    DEFAULT_NUM_CTX: int = _get_env_int("DEFAULT_NUM_CTX", 8192)
    RAG_TOP_K: int = _get_env_int("RAG_TOP_K", 10)


@dataclass(frozen=True)
class QualityWeights:
    """质量评估权重"""
    COMPLETENESS: float = 0.3
    STANDARDIZATION: float = 0.3
    LOGIC: float = 0.2
    LEGALITY: float = 0.2


@dataclass(frozen=True)
class FilterKeywords:
    """过滤关键词"""
    EVENT_FILTER: tuple = (
        "接受询问", "接受讯问", "制作笔录", "到达办案", "到达派出所",
        "到达公安局", "被传唤", "被抓获", "讯问开始", "讯问结束"
    )
    
    LOCATION_FILTER: tuple = (
        "公安局", "派出所", "办案区", "办案中心", "看守所", 
        "刑警大队", "支队", "大队", "询问室", "讯问室"
    )


@dataclass(frozen=True)
class OutputConfig:
    """输出配置
    
    Supports environment variables:
    - KG_DEFAULT_OUTPUT_DIR
    - KG_DEFAULT_KB_NAME
    - KG_MAX_LOG_CONTENT_LENGTH
    - KG_MAX_SUGGESTIONS
    - KG_MIN_SUGGESTIONS
    """
    DEFAULT_OUTPUT_DIR: str = _get_env("DEFAULT_OUTPUT_DIR", "./data/user/interrogation")
    DEFAULT_KB_NAME: str = _get_env("DEFAULT_KB_NAME", "legal_regulations")
    MAX_LOG_CONTENT_LENGTH: int = _get_env_int("MAX_LOG_CONTENT_LENGTH", 200)
    MAX_SUGGESTIONS: int = _get_env_int("MAX_SUGGESTIONS", 10)
    MIN_SUGGESTIONS: int = _get_env_int("MIN_SUGGESTIONS", 3)


@dataclass(frozen=True)
class RetryConfig:
    """重试配置"""
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    BACKOFF_FACTOR: float = 2.0


# 实例化配置（供导入使用）
ANALYSIS_STEPS = AnalysisSteps()
TIMEOUTS = Timeouts()
CACHE_CONFIG = CacheConfig()
LLM_CONFIG = LLMDefaults()
QUALITY_WEIGHTS = QualityWeights()
FILTER_KEYWORDS = FilterKeywords()
OUTPUT_CONFIG = OutputConfig()
RETRY_CONFIG = RetryConfig()

__all__ = [
    "ANALYSIS_STEPS",
    "TIMEOUTS", 
    "CACHE_CONFIG",
    "LLM_CONFIG",
    "QUALITY_WEIGHTS",
    "FILTER_KEYWORDS",
    "OUTPUT_CONFIG",
    "RETRY_CONFIG",
]
