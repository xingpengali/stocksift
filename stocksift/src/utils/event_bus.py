# -*- coding: utf-8 -*-
"""
事件总线模块

提供组件间事件通信机制
"""
import threading
from typing import Callable, Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """事件对象"""
    name: str
    data: Any
    timestamp: datetime
    source: Optional[str] = None


class EventBus:
    """
    事件总线
    
    实现发布-订阅模式，支持同步和异步事件处理
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
        # 订阅者字典: {事件名: [(处理器, 优先级)]}
        self._subscribers: Dict[str, List[tuple]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_name: str, handler: Callable, 
                  priority: int = 0) -> None:
        """
        订阅事件
        
        Args:
            event_name: 事件名称
            handler: 事件处理器
            priority: 优先级，数字越大优先级越高
            
        使用示例:
            def on_quote_updated(data):
                print(f"行情更新: {data}")
            
            event_bus.subscribe("quote_updated", on_quote_updated)
        """
        with self._lock:
            # 检查是否已订阅
            for h, p in self._subscribers[event_name]:
                if h is handler:
                    logger.warning(f"处理器已订阅事件 {event_name}")
                    return
            
            self._subscribers[event_name].append((handler, priority))
            # 按优先级排序
            self._subscribers[event_name].sort(key=lambda x: -x[1])
            
            logger.debug(f"处理器订阅事件 {event_name}")
    
    def unsubscribe(self, event_name: str, handler: Callable) -> bool:
        """
        取消订阅
        
        Args:
            event_name: 事件名称
            handler: 事件处理器
            
        Returns:
            是否成功取消
        """
        with self._lock:
            handlers = self._subscribers.get(event_name, [])
            for i, (h, p) in enumerate(handlers):
                if h is handler:
                    handlers.pop(i)
                    logger.debug(f"处理器取消订阅事件 {event_name}")
                    return True
            return False
    
    def publish(self, event_name: str, data: Any = None, 
                source: Optional[str] = None) -> None:
        """
        发布事件（同步）
        
        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件来源
            
        使用示例:
            event_bus.publish("quote_updated", {"code": "000001", "price": 10.5})
        """
        event = Event(
            name=event_name,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # 记录历史
        self._add_to_history(event)
        
        # 获取订阅者
        with self._lock:
            handlers = list(self._subscribers.get(event_name, []))
        
        # 调用处理器
        for handler, priority in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"事件处理器执行失败 {event_name}: {e}")
    
    def publish_async(self, event_name: str, data: Any = None,
                      source: Optional[str] = None) -> None:
        """
        发布事件（异步）
        
        在新线程中处理事件
        
        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件来源
        """
        import threading
        thread = threading.Thread(
            target=self.publish,
            args=(event_name, data, source),
            daemon=True
        )
        thread.start()
    
    def once(self, event_name: str, handler: Callable, 
             priority: int = 0) -> None:
        """
        只订阅一次事件
        
        事件触发后自动取消订阅
        
        Args:
            event_name: 事件名称
            handler: 事件处理器
            priority: 优先级
        """
        def wrapper(data):
            self.unsubscribe(event_name, wrapper)
            handler(data)
        
        self.subscribe(event_name, wrapper, priority)
    
    def clear(self, event_name: Optional[str] = None) -> None:
        """
        清除订阅
        
        Args:
            event_name: 事件名称，None表示清除所有
        """
        with self._lock:
            if event_name:
                self._subscribers[event_name].clear()
                logger.debug(f"清除事件 {event_name} 的所有订阅")
            else:
                self._subscribers.clear()
                logger.debug("清除所有事件订阅")
    
    def get_subscribers(self, event_name: str) -> List[Callable]:
        """
        获取事件的订阅者
        
        Args:
            event_name: 事件名称
            
        Returns:
            处理器列表
        """
        with self._lock:
            return [h for h, p in self._subscribers.get(event_name, [])]
    
    def get_event_names(self) -> List[str]:
        """
        获取所有事件名称
        
        Returns:
            事件名称列表
        """
        with self._lock:
            return list(self._subscribers.keys())
    
    def get_history(self, event_name: Optional[str] = None, 
                    limit: int = 100) -> List[Event]:
        """
        获取事件历史
        
        Args:
            event_name: 事件名称，None表示所有事件
            limit: 返回数量限制
            
        Returns:
            事件列表
        """
        with self._lock:
            if event_name:
                events = [e for e in self._history if e.name == event_name]
            else:
                events = list(self._history)
            
            return events[-limit:]
    
    def clear_history(self) -> None:
        """清除事件历史"""
        with self._lock:
            self._history.clear()
    
    def _add_to_history(self, event: Event) -> None:
        """添加事件到历史"""
        with self._lock:
            self._history.append(event)
            # 限制历史记录数量
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]


# 全局事件总线实例
event_bus = EventBus()


# 常用事件名称常量
class EventType:
    """事件类型常量"""
    
    # 行情相关
    QUOTE_UPDATED = "quote_updated"
    QUOTE_BATCH_UPDATED = "quote_batch_updated"
    KLINE_UPDATED = "kline_updated"
    
    # 股票相关
    STOCK_LIST_UPDATED = "stock_list_updated"
    STOCK_SELECTED = "stock_selected"
    
    # 预警相关
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_CREATED = "alert_created"
    ALERT_DELETED = "alert_deleted"
    
    # 策略相关
    STRATEGY_EXECUTED = "strategy_executed"
    SIGNAL_GENERATED = "signal_generated"
    
    # 界面相关
    VIEW_CHANGED = "view_changed"
    SETTINGS_CHANGED = "settings_changed"
    
    # 数据相关
    DATA_SYNC_STARTED = "data_sync_started"
    DATA_SYNC_COMPLETED = "data_sync_completed"
    DATA_SYNC_FAILED = "data_sync_failed"
    
    # 系统相关
    APP_STARTED = "app_started"
    APP_SHUTDOWN = "app_shutdown"
    ERROR_OCCURRED = "error_occurred"
