# -*- coding: utf-8 -*-
"""
内存缓存模块
"""
import time
import threading
from collections import OrderedDict
from typing import Any, Optional, Dict, Tuple
from functools import wraps

from config.constants import DEFAULT_CACHE_TTL, MAX_CACHE_SIZE


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, expire_at: float):
        self.value = value
        self.expire_at = expire_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expire_at


class Cache:
    """
    LRU缓存类
    
    特性：
    - 支持TTL过期
    - LRU淘汰策略
    - 线程安全
    """
    
    def __init__(self, max_size: int = MAX_CACHE_SIZE, default_ttl: int = DEFAULT_CACHE_TTL):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认过期时间（秒）
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()
    
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
            item = self._cache.get(key)
            
            if item is None:
                return default
            
            # 检查是否过期
            if item.is_expired():
                del self._cache[key]
                return default
            
            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认值
        """
        if ttl is None:
            ttl = self._default_ttl
        
        with self._lock:
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 检查容量，淘汰最久未使用的
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            
            # 添加新项
            expire_at = time.time() + ttl
            self._cache[key] = CacheItem(value, expire_at)
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
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
    
    def has(self, key: str) -> bool:
        """
        检查键是否存在且未过期
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                return False
            
            if item.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    def get_or_set(self, key: str, default_factory: callable, ttl: Optional[int] = None) -> Any:
        """
        获取或设置缓存值
        
        Args:
            key: 缓存键
            default_factory: 默认值工厂函数
            ttl: 过期时间
            
        Returns:
            缓存值
        """
        value = self.get(key)
        if value is None:
            value = default_factory()
            self.set(key, value, ttl)
        return value
    
    def keys(self) -> list:
        """获取所有未过期的键"""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())
    
    def values(self) -> list:
        """获取所有未过期的值"""
        with self._lock:
            self._cleanup_expired()
            return [item.value for item in self._cache.values()]
    
    def items(self) -> Dict[str, Any]:
        """获取所有未过期的键值对"""
        with self._lock:
            self._cleanup_expired()
            return {k: v.value for k, v in self._cache.items()}
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)
    
    def _cleanup_expired(self) -> None:
        """清理过期项"""
        expired_keys = [
            key for key, item in self._cache.items()
            if item.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for item in self._cache.values() if item.is_expired())
            return {
                "total": total,
                "expired": expired,
                "valid": total - expired,
                "max_size": self._max_size
            }


# 全局缓存实例
global_cache = Cache()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            result = global_cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            global_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def clear_cache():
    """清空全局缓存"""
    global_cache.clear()
