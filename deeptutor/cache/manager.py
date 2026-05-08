"""Cache Manager for DeepTutor

Provides caching capabilities with multiple backends.

Features:
- Multi-backend support (in-memory, Redis, SQLite)
- Automatic cache invalidation
- TTL-based expiration
- Namespace support for different cache types
- Async operations support
- Cache statistics
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration"""
    backend: str = "memory"  # memory, redis, sqlite
    ttl: int = 3600  # Default TTL in seconds
    max_size: int = 10000  # Max items for memory cache
    redis_url: str = "redis://localhost:6379/0"
    sqlite_path: str = "cache.db"
    enabled: bool = True


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    namespace: str
    ttl: int
    created_at: datetime
    accessed_at: datetime
    hit_count: int = 0


class BaseCacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str, namespace: str = "default") -> bool:
        pass
    
    @abstractmethod
    async def exists(self, key: str, namespace: str = "default") -> bool:
        pass
    
    @abstractmethod
    async def clear(self, namespace: str = "default") -> int:
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        pass


class MemoryCacheBackend(BaseCacheBackend):
    """In-memory cache backend"""
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Dict[str, CacheEntry]] = {}  # namespace -> {key -> entry}
        self._max_size = max_size
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        if namespace not in self._cache:
            self._stats["misses"] += 1
            return None
        
        if key not in self._cache[namespace]:
            self._stats["misses"] += 1
            return None
        
        entry = self._cache[namespace][key]
        
        # Check TTL
        if datetime.now() > entry.accessed_at + timedelta(seconds=entry.ttl):
            await self.delete(key, namespace)
            self._stats["misses"] += 1
            return None
        
        # Update access time and hit count
        entry.accessed_at = datetime.now()
        entry.hit_count += 1
        self._stats["hits"] += 1
        
        return entry.value
    
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> bool:
        if namespace not in self._cache:
            self._cache[namespace] = {}
        
        # Enforce max size
        if len(self._cache[namespace]) >= self._max_size:
            await self._evict_oldest(namespace)
        
        self._cache[namespace][key] = CacheEntry(
            key=key,
            value=value,
            namespace=namespace,
            ttl=ttl or 3600,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            hit_count=0,
        )
        
        self._stats["sets"] += 1
        return True
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        if namespace in self._cache and key in self._cache[namespace]:
            del self._cache[namespace][key]
            self._stats["deletes"] += 1
            return True
        return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        if namespace not in self._cache:
            return False
        
        if key not in self._cache[namespace]:
            return False
        
        # Check TTL
        entry = self._cache[namespace][key]
        if datetime.now() > entry.accessed_at + timedelta(seconds=entry.ttl):
            await self.delete(key, namespace)
            return False
        
        return True
    
    async def clear(self, namespace: str = "default") -> int:
        if namespace not in self._cache:
            return 0
        
        count = len(self._cache[namespace])
        self._cache[namespace].clear()
        return count
    
    async def _evict_oldest(self, namespace: str):
        """Evict the oldest entry in namespace"""
        if namespace not in self._cache or not self._cache[namespace]:
            return
        
        oldest_key = min(
            self._cache[namespace].keys(),
            key=lambda k: self._cache[namespace][k].accessed_at
        )
        
        del self._cache[namespace][oldest_key]
        self._stats["evictions"] += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        total_entries = sum(len(entries) for entries in self._cache.values())
        return {
            **self._stats,
            "total_entries": total_entries,
            "namespaces": list(self._cache.keys()),
            "hit_rate": self._stats["hits"] / (self._stats["hits"] + self._stats["misses"]) if (self._stats["hits"] + self._stats["misses"]) > 0 else 0,
        }


class RedisCacheBackend(BaseCacheBackend):
    """Redis cache backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._redis_url = redis_url
        self._client = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
    
    async def _get_client(self):
        """Lazy initialize Redis client"""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(self._redis_url)
                await self._client.ping()
                logger.info("Connected to Redis")
            except ImportError:
                logger.error("redis-py not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        
        return self._client
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        try:
            client = await self._get_client()
            full_key = f"{namespace}:{key}"
            
            value = await client.get(full_key)
            if value is None:
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return json.loads(value)
        
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> bool:
        try:
            client = await self._get_client()
            full_key = f"{namespace}:{key}"
            serialized = json.dumps(value)
            
            if ttl:
                await client.set(full_key, serialized, ex=ttl)
            else:
                await client.set(full_key, serialized)
            
            self._stats["sets"] += 1
            return True
        
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        try:
            client = await self._get_client()
            full_key = f"{namespace}:{key}"
            
            result = await client.delete(full_key)
            self._stats["deletes"] += 1
            return result > 0
        
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        try:
            client = await self._get_client()
            full_key = f"{namespace}:{key}"
            return await client.exists(full_key) > 0
        
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def clear(self, namespace: str = "default") -> int:
        try:
            client = await self._get_client()
            keys = await client.keys(f"{namespace}:*")
            
            if keys:
                count = len(keys)
                await client.delete(*keys)
                return count
            return 0
        
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "backend": "redis",
            "hit_rate": self._stats["hits"] / (self._stats["hits"] + self._stats["misses"]) if (self._stats["hits"] + self._stats["misses"]) > 0 else 0,
        }


class SQLiteCacheBackend(BaseCacheBackend):
    """SQLite cache backend"""
    
    def __init__(self, db_path: str = "cache.db"):
        self._db_path = db_path
        self._conn = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
    
    async def _get_connection(self):
        """Lazy initialize SQLite connection"""
        if self._conn is None:
            try:
                import sqlite3
                self._conn = sqlite3.connect(self._db_path)
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL,
                        namespace TEXT NOT NULL,
                        value TEXT NOT NULL,
                        ttl INTEGER NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        accessed_at TIMESTAMP NOT NULL,
                        hit_count INTEGER DEFAULT 0,
                        UNIQUE(key, namespace)
                    )
                """)
                self._conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_key_namespace ON cache(key, namespace)
                """)
                self._conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_expiration ON cache(accessed_at)
                """)
                self._conn.commit()
                logger.info("SQLite cache initialized")
            except ImportError:
                logger.error("sqlite3 not available")
                raise
        
        return self._conn
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        try:
            conn = await self._get_connection()
            
            # Cleanup expired entries
            conn.execute("""
                DELETE FROM cache WHERE accessed_at + ttl < strftime('%s', 'now')
            """)
            conn.commit()
            
            cursor = conn.execute("""
                SELECT value, ttl, accessed_at, hit_count FROM cache 
                WHERE key = ? AND namespace = ?
            """, (key, namespace))
            
            row = cursor.fetchone()
            if row is None:
                self._stats["misses"] += 1
                return None
            
            value, ttl, accessed_at, hit_count = row
            
            # Update access time and hit count
            conn.execute("""
                UPDATE cache SET accessed_at = strftime('%s', 'now'), hit_count = ? 
                WHERE key = ? AND namespace = ?
            """, (hit_count + 1, key, namespace))
            conn.commit()
            
            self._stats["hits"] += 1
            return json.loads(value)
        
        except Exception as e:
            logger.error(f"SQLite get error: {e}")
            self._stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> bool:
        try:
            conn = await self._get_connection()
            serialized = json.dumps(value)
            now = datetime.now().timestamp()
            
            conn.execute("""
                INSERT OR REPLACE INTO cache 
                (key, namespace, value, ttl, created_at, accessed_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (key, namespace, serialized, ttl or 3600, now, now))
            conn.commit()
            
            self._stats["sets"] += 1
            return True
        
        except Exception as e:
            logger.error(f"SQLite set error: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        try:
            conn = await self._get_connection()
            
            cursor = conn.execute("""
                DELETE FROM cache WHERE key = ? AND namespace = ?
            """, (key, namespace))
            conn.commit()
            
            self._stats["deletes"] += 1
            return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"SQLite delete error: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        try:
            conn = await self._get_connection()
            
            # Cleanup expired entries
            conn.execute("""
                DELETE FROM cache WHERE accessed_at + ttl < strftime('%s', 'now')
            """)
            conn.commit()
            
            cursor = conn.execute("""
                SELECT 1 FROM cache WHERE key = ? AND namespace = ?
            """, (key, namespace))
            
            return cursor.fetchone() is not None
        
        except Exception as e:
            logger.error(f"SQLite exists error: {e}")
            return False
    
    async def clear(self, namespace: str = "default") -> int:
        try:
            conn = await self._get_connection()
            
            cursor = conn.execute("""
                DELETE FROM cache WHERE namespace = ?
            """, (namespace,))
            conn.commit()
            
            return cursor.rowcount
        
        except Exception as e:
            logger.error(f"SQLite clear error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        try:
            conn = await self._get_connection()
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM cache
            """)
            total_entries = cursor.fetchone()[0]
            
            return {
                **self._stats,
                "backend": "sqlite",
                "total_entries": total_entries,
                "hit_rate": self._stats["hits"] / (self._stats["hits"] + self._stats["misses"]) if (self._stats["hits"] + self._stats["misses"]) > 0 else 0,
            }
        
        except Exception as e:
            logger.error(f"SQLite stats error: {e}")
            return self._stats


class CacheManager:
    """Central cache manager"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._backend: BaseCacheBackend = self._create_backend()
        self._enabled = self.config.enabled
        logger.info(f"Cache manager initialized with {self.config.backend} backend")
    
    def _create_backend(self) -> BaseCacheBackend:
        """Create appropriate backend based on config"""
        backend_type = self.config.backend.lower()
        
        if backend_type == "redis":
            return RedisCacheBackend(self.config.redis_url)
        elif backend_type == "sqlite":
            return SQLiteCacheBackend(self.config.sqlite_path)
        else:
            return MemoryCacheBackend(self.config.max_size)
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache"""
        if not self._enabled:
            return None
        
        return await self._backend.get(key, namespace)
    
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self._enabled:
            return False
        
        return await self._backend.set(key, value, namespace, ttl or self.config.ttl)
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete value from cache"""
        if not self._enabled:
            return False
        
        return await self._backend.delete(key, namespace)
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache"""
        if not self._enabled:
            return False
        
        return await self._backend.exists(key, namespace)
    
    async def clear(self, namespace: str = "default") -> int:
        """Clear all entries in namespace"""
        if not self._enabled:
            return 0
        
        return await self._backend.clear(namespace)
    
    async def clear_all(self) -> int:
        """Clear all entries across all namespaces"""
        if not self._enabled:
            return 0
        
        # For memory backend
        if hasattr(self._backend, '_cache'):
            total = sum(len(entries) for entries in self._backend._cache.values())
            self._backend._cache.clear()
            return total
        
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = await self._backend.get_stats()
        stats["enabled"] = self._enabled
        stats["backend"] = self.config.backend
        return stats
    
    def generate_key(self, *args: Any) -> str:
        """Generate a cache key from arguments"""
        key_str = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def memoize(self, namespace: str = "default", ttl: Optional[int] = None):
        """Decorator to cache function results"""
        def decorator(func: Callable) -> Callable:
            async def async_wrapper(*args, **kwargs):
                cache_key = self.generate_key(func.__name__, *args, frozenset(kwargs.items()))
                
                # Try to get from cache
                cached = await self.get(cache_key, namespace)
                if cached is not None:
                    return cached
                
                # Call the function
                result = await func(*args, **kwargs)
                
                # Cache the result
                await self.set(cache_key, result, namespace, ttl)
                
                return result
            
            def sync_wrapper(*args, **kwargs):
                cache_key = self.generate_key(func.__name__, *args, frozenset(kwargs.items()))
                
                # Try to get from cache
                cached = asyncio.run(self.get(cache_key, namespace))
                if cached is not None:
                    return cached
                
                # Call the function
                result = func(*args, **kwargs)
                
                # Cache the result
                asyncio.run(self.set(cache_key, result, namespace, ttl))
                
                return result
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def enable(self):
        """Enable caching"""
        self._enabled = True
        logger.info("Cache enabled")
    
    def disable(self):
        """Disable caching"""
        self._enabled = False
        logger.info("Cache disabled")


# Global cache manager instance
_cache_manager_instance = None

def get_cache_manager(config: Optional[CacheConfig] = None) -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager_instance
    
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(config)
    
    return _cache_manager_instance
