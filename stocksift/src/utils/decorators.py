# -*- coding: utf-8 -*-
"""
通用装饰器模块

提供重试、计时、缓存等装饰器
"""
import time
import functools
from typing import Callable, Any, Optional
from functools import wraps

from utils.logger import get_logger

logger = get_logger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, 
          exceptions: tuple = (Exception,), on_retry: Optional[Callable] = None):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要捕获的异常类型
        on_retry: 重试时的回调函数
        
    使用示例:
        @retry(max_attempts=3, delay=1.0)
        def fetch_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} 第{attempt}次尝试失败: {e}，"
                            f"{delay}秒后重试..."
                        )
                        
                        if on_retry:
                            on_retry(attempt, e)
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} 重试{max_attempts}次后仍然失败"
                        )
            
            raise last_exception
        return wrapper
    return decorator


def retry_with_backoff(max_attempts: int = 3, initial_delay: float = 1.0,
                       backoff_factor: float = 2.0,
                       exceptions: tuple = (Exception,)):
    """
    指数退避重试装饰器
    
    每次重试间隔时间呈指数增长
    
    Args:
        max_attempts: 最大重试次数
        initial_delay: 初始延迟（秒）
        backoff_factor: 退避因子
        exceptions: 需要捕获的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} 第{attempt}次尝试失败: {e}，"
                            f"{delay}秒后重试..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"{func.__name__} 重试{max_attempts}次后仍然失败"
                        )
            
            raise last_exception
        return wrapper
    return decorator


def timer(func: Callable) -> Callable:
    """
    计时装饰器
    
    记录函数执行时间
    
    使用示例:
        @timer
        def slow_function():
            time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        elapsed = end_time - start_time
        logger.info(f"{func.__name__} 执行耗时: {elapsed:.3f}秒")
        
        return result
    return wrapper


def cache_result(ttl: int = 60):
    """
    结果缓存装饰器
    
    缓存函数结果，指定时间内直接返回缓存值
    
    Args:
        ttl: 缓存有效期（秒）
        
    使用示例:
        @cache_result(ttl=300)
        def get_stock_list():
            # 耗时操作
            return stock_list
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = str(args) + str(sorted(kwargs.items()))
            
            now = time.time()
            
            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    return result
            
            # 执行函数
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            
            return result
        
        # 添加清除缓存方法
        wrapper.clear_cache = lambda: cache.clear()
        
        return wrapper
    return decorator


def throttle(interval: float = 1.0):
    """
    节流装饰器
    
    限制函数调用频率
    
    Args:
        interval: 最小调用间隔（秒）
        
    使用示例:
        @throttle(interval=0.5)
        def fetch_quote():
            pass
    """
    def decorator(func: Callable) -> Callable:
        last_call_time = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - last_call_time[0]
            
            if elapsed < interval:
                time.sleep(interval - elapsed)
            
            last_call_time[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def debounce(wait: float = 0.5):
    """
    防抖装饰器
    
    延迟执行，如果在等待时间内再次调用，则重新计时
    
    Args:
        wait: 等待时间（秒）
        
    使用示例:
        @debounce(wait=0.3)
        def on_search(text):
            pass
    """
    def decorator(func: Callable) -> Callable:
        timer = [None]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 取消之前的定时器
            if timer[0] is not None:
                timer[0].cancel()
            
            # 创建新的定时器
            import threading
            timer[0] = threading.Timer(wait, lambda: func(*args, **kwargs))
            timer[0].start()
        
        return wrapper
    return decorator


def singleton(cls):
    """
    单例装饰器
    
    确保类只有一个实例
    
    使用示例:
        @singleton
        class DatabaseManager:
            pass
    """
    instances = {}
    lock = threading.Lock()
    
    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper


def log_execution(level: str = "info"):
    """
    执行日志装饰器
    
    记录函数执行前后的日志
    
    Args:
        level: 日志级别 (debug, info, warning, error)
        
    使用示例:
        @log_execution(level="info")
        def process_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            log_func = getattr(logger, level.lower(), logger.info)
            
            log_func(f"开始执行 {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                log_func(f"{func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} 执行失败: {e}")
                raise
        
        return wrapper
    return decorator


def deprecated(message: str = ""):
    """
    弃用装饰器
    
    标记函数已弃用
    
    Args:
        message: 弃用说明
        
    使用示例:
        @deprecated("请使用 new_function 代替")
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warn_msg = f"{func.__name__} 已弃用"
            if message:
                warn_msg += f": {message}"
            warnings.warn(warn_msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


import threading
