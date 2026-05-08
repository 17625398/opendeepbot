"""
LLM Provider Failover Wrapper
===============================

Provides automatic failover between LLM providers.
When the primary provider fails, automatically switches to backup provider.

Features:
- Automatic failover on 503/504 errors
- Configurable retry logic
- Health check for providers
- Metrics tracking for provider reliability
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMFailoverConfig:
    """Configuration for LLM failover behavior"""
    
    def __init__(self):
        self.enabled = self._get_bool("LLM_BACKUP_ENABLED", True)
        self.max_retries = self._get_int("LLM_FAILOVER_MAX_RETRIES", 3)
        self.retry_delay = self._get_float("LLM_FAILOVER_RETRY_DELAY", 1.0)
        self.health_check_interval = self._get_int("LLM_FAILOVER_HEALTH_CHECK", 60)
        
        # Backup provider config
        self.backup_binding = os.getenv("LLM_BACKUP_BINDING", "ollama")
        self.backup_model = os.getenv("LLM_BACKUP_MODEL", "qwen2.5:7b")
        self.backup_api_key = os.getenv("LLM_BACKUP_API_KEY", "")
        self.backup_host = os.getenv("LLM_BACKUP_HOST", "http://localhost:11434/v1")
        
    def _get_bool(self, key: str, default: bool) -> bool:
        value = os.getenv(key, str(default))
        return value.lower() in ("true", "1", "yes")
    
    def _get_int(self, key: str, default: int) -> int:
        value = os.getenv(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default
    
    def _get_float(self, key: str, default: float) -> float:
        value = os.getenv(key, str(default))
        try:
            return float(value)
        except ValueError:
            return default


class ProviderHealthTracker:
    """Tracks health metrics for LLM providers"""
    
    def __init__(self):
        self.providers: Dict[str, Dict[str, Any]] = {
            "primary": {"failures": 0, "successes": 0, "last_failure": None},
            "backup": {"failures": 0, "successes": 0, "last_failure": None},
        }
        self._current_provider = "primary"
    
    def record_success(self, provider: str):
        """Record successful call"""
        if provider in self.providers:
            self.providers[provider]["successes"] += 1
            self.providers[provider]["last_failure"] = None
    
    def record_failure(self, provider: str, error: str):
        """Record failed call"""
        if provider in self.providers:
            self.providers[provider]["failures"] += 1
            self.providers[provider]["last_failure"] = error
            
            # Switch provider if primary is unhealthy
            if provider == "primary":
                failure_rate = self.providers["primary"]["failures"] / max(
                    self.providers["primary"]["successes"] + self.providers["primary"]["failures"], 1
                )
                if failure_rate > 0.5:  # 50% failure rate threshold
                    logger.warning(f"Primary provider failure rate: {failure_rate:.1%}, switching to backup")
                    self._current_provider = "backup"
    
    def get_current_provider(self) -> str:
        """Get the currently active provider"""
        return self._current_provider
    
    def switch_to_primary(self):
        """Manually switch back to primary provider"""
        self._current_provider = "primary"
        logger.info("Switched back to primary LLM provider")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics"""
        return {
            "current_provider": self._current_provider,
            "providers": {
                name: {
                    "failures": stats["failures"],
                    "successes": stats["successes"],
                    "success_rate": stats["successes"] / max(stats["successes"] + stats["failures"], 1),
                    "last_failure": stats["last_failure"],
                }
                for name, stats in self.providers.items()
            }
        }


class LLMFailoverWrapper:
    """
    Wrapper that adds automatic failover to any LLM client.
    
    Usage:
        from deeptutor.services.llm.failover import LLMFailoverWrapper
        
        # Wrap your existing LLM client
        wrapped_client = LLMFailoverWrapper(base_client)
        
        # Use normally, failover happens automatically
        response = await wrapped_client.chat(messages)
    """
    
    _instance: Optional["LLMFailoverWrapper"] = None
    
    def __init__(self, base_client: Any = None):
        """
        Initialize failover wrapper
        
        Args:
            base_client: The base LLM client to wrap
        """
        self.config = LLMFailoverConfig()
        self.health_tracker = ProviderHealthTracker()
        self._base_client = base_client
        self._backup_client = None
        self._initialized = False
        
        # Singleton pattern
        LLMFailoverWrapper._instance = self
    
    async def _ensure_initialized(self):
        """Lazily initialize backup client"""
        if self._initialized:
            return
        
        if self._base_client is None:
            from deeptutor.services.llm.client import get_llm_client
            self._base_client = get_llm_client()
        
        self._initialized = True
        logger.info(f"LLM Failover initialized: backup_enabled={self.config.enabled}")
    
    def _get_backup_client(self) -> Any:
        """Get or create backup LLM client"""
        if self._backup_client is None:
            try:
                from deeptutor.services.llm.client import create_llm_client
                
                self._backup_client = create_llm_client(
                    binding=self.config.backup_binding,
                    model=self.config.backup_model,
                    api_key=self.config.backup_api_key,
                    base_url=self.config.backup_host,
                )
                logger.info(f"Backup LLM client created: {self.config.backup_binding}")
            except Exception as e:
                logger.error(f"Failed to create backup LLM client: {e}")
                return None
        return self._backup_client
    
    async def chat(self, messages: list, **kwargs) -> Any:
        """
        Send chat request with automatic failover
        
        Args:
            messages: Chat messages
            **kwargs: Additional arguments passed to LLM client
        
        Returns:
            LLM response
        """
        await self._ensure_initialized()
        
        current_provider = self.health_tracker.get_current_provider()
        
        for attempt in range(self.config.max_retries):
            try:
                if current_provider == "primary":
                    response = await self._base_client.chat(messages, **kwargs)
                    self.health_tracker.record_success("primary")
                    return response
                else:
                    backup = self._get_backup_client()
                    if backup is None:
                        # Fallback to primary if backup unavailable
                        response = await self._base_client.chat(messages, **kwargs)
                        self.health_tracker.record_success("primary")
                        return response
                    
                    response = await backup.chat(messages, **kwargs)
                    self.health_tracker.record_success("backup")
                    return response
                    
            except Exception as e:
                error_str = str(e).lower()
                is_transient = any(code in error_str for code in ["503", "504", "timeout", "unavailable"])
                
                if is_transient and attempt < self.config.max_retries - 1:
                    provider = "primary" if current_provider == "primary" else "backup"
                    logger.warning(f"LLM call failed on {provider} (attempt {attempt + 1}): {e}")
                    self.health_tracker.record_failure(provider, str(e))
                    
                    # Try switching provider
                    if provider == "primary" and self.health_tracker.get_current_provider() == "primary":
                        self.health_tracker._current_provider = "backup"
                        current_provider = "backup"
                    
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise
        
        raise Exception(f"LLM call failed after {self.config.max_retries} attempts")
    
    async def chat_stream(self, messages: list, **kwargs) -> Any:
        """Stream chat with failover support"""
        await self._ensure_initialized()
        
        # For streaming, we don't do automatic failover as it's harder to handle
        # Just use primary and let it fail naturally
        return self._base_client.chat_stream(messages, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get failover statistics"""
        return self.health_tracker.get_stats()
    
    def switch_provider(self, provider: str):
        """Manually switch provider"""
        if provider in ("primary", "backup"):
            self.health_tracker._current_provider = provider
            logger.info(f"Manually switched to {provider} provider")


# Global singleton
_fallback_wrapper: Optional[LLMFailoverWrapper] = None


def get_failover_wrapper() -> LLMFailoverWrapper:
    """Get global failover wrapper instance"""
    global _fallback_wrapper
    if _fallback_wrapper is None:
        _fallback_wrapper = LLMFailoverWrapper()
    return _fallback_wrapper


async def chat_with_failover(messages: list, **kwargs) -> Any:
    """
    Convenience function for making LLM calls with failover support
    
    Usage:
        response = await chat_with_failover([
            {"role": "user", "content": "Hello!"}
        ])
    """
    wrapper = get_failover_wrapper()
    return await wrapper.chat(messages, **kwargs)
