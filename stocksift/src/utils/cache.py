# -*- coding: utf-8 -*-
"""
内存缓存模块

提供 LRU 缓存管理功能
"""
import time
import threading
from typing import Any, Optional, Dict, List, Callable
from collections import OrderedDict
from dataclasses import dataclass, field

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    expire_time: Optional[float] = None
    access_count: int = field(default=0)
    last_access: float = field(default_factory=time.time)


class Cache:
    """
    LRU 缓存管理器
    
    支持 TTL 过期和 LRU 淘汰策略
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒），None表示永不过期
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return default
            
            # 检查是否过期
            if entry.expire_time is not None and time.time() > entry.expire_time:
                del self._cache[key]
                self._misses += 1
                return default
            
            # 更新访问信息
            entry.access_count += 1
            entry.last_access = time.time()
            
            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值
        """
        with self._lock:
            # 计算过期时间
            if ttl is None:
                ttl = self._default_ttl
            
            expire_time = None
            if ttl is not None:
                expire_time = time.time() + ttl
            
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 检查是否需要淘汰
            self._evict_if_needed()
            
            # 添加新条目
            entry = CacheEntry(
                value=value,
                expire_time=expire_time,
                access_count=1,
                last_access=time.time()
            )
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def has(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            # 检查是否过期
            if entry.expire_time is not None and time.time() > entry.expire_time:
                del self._cache[key]
                return False
            
            return True
    
    def keys(self) -> List[str]:
        """
        获取所有键
        
        Returns:
            键列表
        """
        with self._lock:
            # 清理过期条目
            self._cleanup_expired()
            return list(self._cache.keys())
    
    def size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            条目数
        """
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
            }
    
    def _evict_if_needed(self) -> None:
        """如果需要，淘汰最久未使用的条目"""
        while len(self._cache) >= self._max_size:
            # 淘汰第一个条目（最久未使用）
            self._cache.popitem(last=False)
    
    def _cleanup_expired(self) -> None:
        """清理过期条目"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expire_time is not None and now > entry.expire_time
        ]
        for key in expired_keys:
            del self._cache[key]


class CacheManager:
    """
    缓存管理器
    
    管理多个命名缓存实例
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._caches: Dict[str, Cache] = {}
        self._lock = threading.Lock()
    
    def get_cache(self, name: str, max_size: int = 1000, 
                  default_ttl: Optional[int] = None) -> Cache:
        """
        获取或创建缓存
        
        Args:
            name: 缓存名称
            max_size: 最大条目数
            default_ttl: 默认过期时间
            
        Returns:
            缓存实例
        """
        with self._lock:
            if name not in self._caches:
                self._caches[name] = Cache(max_size, default_ttl)
            return self._caches[name]
    
    def clear_cache(self, name: str) -> bool:
        """
        清空指定缓存
        
        Args:
            name: 缓存名称
            
        Returns:
            是否成功
        """
        with self._lock:
            cache = self._caches.get(name)
            if cache:
                cache.clear()
                return True
            return False
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
    
    def remove_cache(self, name: str) -> bool:
        """
        删除缓存
        
        Args:
            name: 缓存名称
            
        Returns:
            是否成功
        """
        with self._lock:
            if name in self._caches:
                del self._caches[name]
                return True
            return False
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            return {name: cache.stats() for name, cache in self._caches.items()}


# 全局缓存管理器实例
cache_manager = CacheManager()


def cached(cache_name: str = "default", ttl: Optional[int] = None, 
           key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    使用指定缓存自动缓存函数结果
    
    Args:
        cache_name: 缓存名称
        ttl: 过期时间（秒）
        key_func: 自定义缓存键生成函数
        
    使用示例:
        @cached(cache_name="stock_list", ttl=3600)
        def get_stock_list():
            return fetch_from_db()
    """
    def decorator(func: Callable) -> Callable:
        cache = cache_manager.get_cache(cache_name)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


from functools import wraps
