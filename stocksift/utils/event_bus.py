# -*- coding: utf-8 -*-
"""
事件总线模块

提供组件间的发布-订阅通信机制
"""
import threading
from typing import Dict, List, Callable, Any
from collections import defaultdict


class EventBus:
    """
    事件总线类 - 单例模式
    
    使用示例：
        # 订阅事件
        event_bus.subscribe("quote_updated", on_quote_update)
        
        # 发布事件
        event_bus.publish("quote_updated", {"code": "000001", "price": 10.5})
        
        # 取消订阅
        event_bus.unsubscribe("quote_updated", on_quote_update)
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
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数，接收事件数据作为参数
        """
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> bool:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            是否取消成功
        """
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    return True
            return False
    
    def publish(self, event_type: str, data: Any = None) -> int:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            通知的订阅者数量
        """
        with self._lock:
            callbacks = self._subscribers[event_type].copy()
        
        # 在锁外调用回调，避免死锁
        notified = 0
        for callback in callbacks:
            try:
                callback(data)
                notified += 1
            except Exception as e:
                # 记录错误但不影响其他订阅者
                print(f"事件处理错误 [{event_type}]: {e}")
        
        return notified
    
    def once(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        订阅一次性事件（只触发一次后自动取消订阅）
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        def wrapper(data):
            self.unsubscribe(event_type, wrapper)
            callback(data)
        
        self.subscribe(event_type, wrapper)
    
    def clear(self, event_type: str = None) -> None:
        """
        清除订阅
        
        Args:
            event_type: 事件类型，None表示清除所有
        """
        with self._lock:
            if event_type is None:
                self._subscribers.clear()
            else:
                self._subscribers[event_type].clear()
    
    def get_subscribers(self, event_type: str = None) -> List[str]:
        """
        获取订阅者信息
        
        Args:
            event_type: 事件类型，None返回所有
            
        Returns:
            事件类型列表或订阅者数量
        """
        with self._lock:
            if event_type:
                return len(self._subscribers.get(event_type, []))
            return list(self._subscribers.keys())
    
    def has_subscribers(self, event_type: str) -> bool:
        """
        检查是否有订阅者
        
        Args:
            event_type: 事件类型
            
        Returns:
            是否有订阅者
        """
        with self._lock:
            return len(self._subscribers.get(event_type, [])) > 0


# 全局事件总线实例
event_bus = EventBus()


# 便捷函数
def subscribe(event_type: str, callback: Callable[[Any], None]) -> None:
    """订阅事件"""
    event_bus.subscribe(event_type, callback)


def unsubscribe(event_type: str, callback: Callable[[Any], None]) -> bool:
    """取消订阅事件"""
    return event_bus.unsubscribe(event_type, callback)


def publish(event_type: str, data: Any = None) -> int:
    """发布事件"""
    return event_bus.publish(event_type, data)


def once(event_type: str, callback: Callable[[Any], None]) -> None:
    """订阅一次性事件"""
    event_bus.once(event_type, callback)


# 常用事件类型定义
class EventType:
    """系统事件类型常量"""
    
    # 行情相关
    QUOTE_UPDATED = "quote_updated"           # 行情更新
    QUOTE_BATCH_UPDATED = "quote_batch_updated"  # 批量行情更新
    
    # 股票相关
    STOCK_SELECTED = "stock_selected"         # 股票被选中
    STOCK_ADDED_TO_WATCHLIST = "stock_added_to_watchlist"  # 添加到自选股
    STOCK_REMOVED_FROM_WATCHLIST = "stock_removed_from_watchlist"  # 从自选股移除
    
    # 预警相关
    ALERT_TRIGGERED = "alert_triggered"       # 预警触发
    ALERT_RULE_CHANGED = "alert_rule_changed" # 预警规则变更
    
    # 配置相关
    SETTINGS_CHANGED = "settings_changed"     # 配置变更
    THEME_CHANGED = "theme_changed"           # 主题变更
    
    # 数据相关
    DATA_UPDATED = "data_updated"             # 数据更新
    CACHE_CLEARED = "cache_cleared"           # 缓存清除
    
    # 页面相关
    PAGE_CHANGED = "page_changed"             # 页面切换
    WINDOW_RESIZED = "window_resized"         # 窗口大小变更
