# -*- coding: utf-8 -*-
"""
工具模块测试
"""
import os
import sys
import time
import tempfile
import shutil
import unittest
import threading
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import (
    format_number, format_percent, format_volume, format_amount,
    format_date, parse_date, get_trade_date, get_date_range,
    normalize_stock_code, add_exchange_suffix, retry, chunk_list,
    safe_divide, truncate_string
)
from utils.cache import Cache, cached, global_cache, clear_cache
from utils.event_bus import EventBus, event_bus, EventType


class TestFormatHelpers(unittest.TestCase):
    """测试格式化工具函数"""
    
    def test_format_number(self):
        """测试数字格式化"""
        self.assertEqual(format_number(1234.5678, 2), "1,234.57")
        self.assertEqual(format_number(1234.5678, 2, False), "1234.57")
        self.assertEqual(format_number(None), "--")
    
    def test_format_percent(self):
        """测试百分比格式化"""
        self.assertEqual(format_percent(0.0523, 2), "5.23%")
        self.assertEqual(format_percent(0.1), "10.00%")
        self.assertEqual(format_percent(None), "--")
    
    def test_format_volume(self):
        """测试成交量格式化"""
        self.assertEqual(format_volume(1500), "1,500")
        self.assertEqual(format_volume(15000), "1.50万")
        self.assertEqual(format_volume(150000000), "1.50亿")
        self.assertEqual(format_volume(None), "--")
    
    def test_format_amount(self):
        """测试金额格式化"""
        self.assertEqual(format_amount(1500), "1,500.00")
        self.assertEqual(format_amount(15000), "1.50万")
        self.assertEqual(format_amount(150000000), "1.50亿")
    
    def test_format_date(self):
        """测试日期格式化"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        self.assertEqual(format_date(dt), "2024-01-15")
        self.assertEqual(format_date(dt, "%Y/%m/%d"), "2024/01/15")
        self.assertEqual(format_date("2024-01-15"), "2024-01-15")
        self.assertEqual(format_date(None), "--")
    
    def test_parse_date(self):
        """测试日期解析"""
        result = parse_date("2024-01-15")
        self.assertEqual(result, date(2024, 1, 15))
        
        result = parse_date("invalid")
        self.assertIsNone(result)
        
        result = parse_date("")
        self.assertIsNone(result)


class TestDateHelpers(unittest.TestCase):
    """测试日期工具函数"""
    
    def test_get_trade_date_weekday(self):
        """测试获取交易日（工作日）"""
        # 周三
        wednesday = date(2024, 1, 10)
        result = get_trade_date(wednesday)
        self.assertEqual(result, wednesday)
    
    def test_get_trade_date_saturday(self):
        """测试获取交易日（周六）"""
        # 周六 -> 周五
        saturday = date(2024, 1, 13)
        result = get_trade_date(saturday)
        self.assertEqual(result, date(2024, 1, 12))
    
    def test_get_trade_date_sunday(self):
        """测试获取交易日（周日）"""
        # 周日 -> 周五
        sunday = date(2024, 1, 14)
        result = get_trade_date(sunday)
        self.assertEqual(result, date(2024, 1, 12))
    
    def test_get_date_range(self):
        """测试获取日期范围"""
        end = date(2024, 1, 15)
        start, end_result = get_date_range(10, end)
        
        self.assertEqual(end_result, end)
        self.assertEqual(start, date(2024, 1, 5))


class TestStockCodeHelpers(unittest.TestCase):
    """测试股票代码工具函数"""
    
    def test_normalize_stock_code(self):
        """测试标准化股票代码"""
        self.assertEqual(normalize_stock_code("000001.SZ"), "000001")
        self.assertEqual(normalize_stock_code("000001"), "000001")
        self.assertEqual(normalize_stock_code(" 000001 "), "000001")
        self.assertEqual(normalize_stock_code(""), "")
    
    def test_add_exchange_suffix(self):
        """测试添加交易所后缀"""
        self.assertEqual(add_exchange_suffix("000001"), "000001.SZ")
        self.assertEqual(add_exchange_suffix("600000"), "600000.SH")
        self.assertEqual(add_exchange_suffix(""), "")


class TestUtilityHelpers(unittest.TestCase):
    """测试通用工具函数"""
    
    def test_chunk_list(self):
        """测试列表分块"""
        lst = [1, 2, 3, 4, 5, 6, 7]
        result = chunk_list(lst, 3)
        self.assertEqual(result, [[1, 2, 3], [4, 5, 6], [7]])
    
    def test_safe_divide(self):
        """测试安全除法"""
        self.assertEqual(safe_divide(10, 2), 5.0)
        self.assertEqual(safe_divide(10, 0), 0.0)
        self.assertEqual(safe_divide(10, 0, 100), 100)
    
    def test_truncate_string(self):
        """测试字符串截断"""
        self.assertEqual(truncate_string("hello world", 8), "hello...")
        self.assertEqual(truncate_string("hi", 8), "hi")
        self.assertEqual(truncate_string("", 8), "")


class TestRetryDecorator(unittest.TestCase):
    """测试重试装饰器"""
    
    def test_retry_success(self):
        """测试重试成功"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.1)
        def success_func():
            call_count[0] += 1
            return "success"
        
        result = success_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 1)
    
    def test_retry_failure(self):
        """测试重试失败"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.1)
        def fail_func():
            call_count[0] += 1
            raise ValueError("error")
        
        with self.assertRaises(ValueError):
            fail_func()
        
        self.assertEqual(call_count[0], 3)


class TestCache(unittest.TestCase):
    """测试缓存模块"""
    
    def setUp(self):
        """测试前准备"""
        clear_cache()
        self.cache = Cache(max_size=100, default_ttl=1)
    
    def tearDown(self):
        """测试后清理"""
        clear_cache()
    
    def test_basic_operations(self):
        """测试基本操作"""
        # 设置
        self.cache.set("key1", "value1")
        
        # 获取
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # 获取不存在的键
        self.assertIsNone(self.cache.get("key2"))
        self.assertEqual(self.cache.get("key2", "default"), "default")
        
        # 删除
        self.assertTrue(self.cache.delete("key1"))
        self.assertFalse(self.cache.delete("key1"))
    
    def test_ttl_expiration(self):
        """测试TTL过期"""
        # 设置短TTL
        self.cache.set("key1", "value1", ttl=0.1)
        
        # 立即获取应该存在
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # 等待过期
        time.sleep(0.2)
        
        # 过期后应该返回None
        self.assertIsNone(self.cache.get("key1"))
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = Cache(max_size=3)
        
        # 添加3个项
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # 访问key1，使其成为最近使用
        cache.get("key1")
        
        # 添加第4个项，应该淘汰key2
        cache.set("key4", "value4")
        
        self.assertIsNotNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))  # 被淘汰
        self.assertIsNotNone(cache.get("key3"))
        self.assertIsNotNone(cache.get("key4"))
    
    def test_has_and_clear(self):
        """测试存在检查和清空"""
        self.cache.set("key1", "value1")
        
        self.assertTrue(self.cache.has("key1"))
        self.assertFalse(self.cache.has("key2"))
        
        self.cache.clear()
        
        self.assertFalse(self.cache.has("key1"))
        self.assertEqual(self.cache.size(), 0)
    
    def test_get_or_set(self):
        """测试获取或设置"""
        # 第一次调用，应该执行工厂函数
        value1 = self.cache.get_or_set("key1", lambda: "computed_value")
        self.assertEqual(value1, "computed_value")
        
        # 第二次调用，应该返回缓存值
        value2 = self.cache.get_or_set("key1", lambda: "new_value")
        self.assertEqual(value2, "computed_value")
    
    def test_stats(self):
        """测试统计信息"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2", ttl=0.1)
        
        # 等待一个过期
        time.sleep(0.2)
        
        stats = self.cache.stats()
        self.assertIn("total", stats)
        self.assertIn("expired", stats)
        self.assertIn("valid", stats)
        self.assertIn("max_size", stats)
    
    def test_thread_safety(self):
        """测试线程安全"""
        results = []
        
        def worker():
            for i in range(100):
                self.cache.set(f"key_{i}", f"value_{i}")
                value = self.cache.get(f"key_{i}")
                results.append(value)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 验证没有异常发生
        self.assertEqual(len(results), 500)


class TestCachedDecorator(unittest.TestCase):
    """测试缓存装饰器"""
    
    def setUp(self):
        clear_cache()
    
    def tearDown(self):
        clear_cache()
    
    def test_cached_decorator(self):
        """测试缓存装饰器"""
        call_count = [0]
        
        @cached(ttl=60, key_prefix="test_")
        def expensive_function(x, y):
            call_count[0] += 1
            return x + y
        
        # 第一次调用
        result1 = expensive_function(1, 2)
        self.assertEqual(result1, 3)
        self.assertEqual(call_count[0], 1)
        
        # 第二次调用相同参数，应该使用缓存
        result2 = expensive_function(1, 2)
        self.assertEqual(result2, 3)
        self.assertEqual(call_count[0], 1)  # 没有增加
        
        # 不同参数，应该重新计算
        result3 = expensive_function(2, 3)
        self.assertEqual(result3, 5)
        self.assertEqual(call_count[0], 2)


class TestEventBus(unittest.TestCase):
    """测试事件总线"""
    
    def setUp(self):
        """测试前准备"""
        event_bus.clear()
    
    def tearDown(self):
        """测试后清理"""
        event_bus.clear()
    
    def test_subscribe_publish(self):
        """测试订阅和发布"""
        received_events = []
        
        def handler(data):
            received_events.append(data)
        
        # 订阅
        event_bus.subscribe("test_event", handler)
        
        # 发布
        event_bus.publish("test_event", {"message": "hello"})
        
        # 验证
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0], {"message": "hello"})
    
    def test_multiple_subscribers(self):
        """测试多个订阅者"""
        results = []
        
        def handler1(data):
            results.append("handler1")
        
        def handler2(data):
            results.append("handler2")
        
        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)
        
        count = event_bus.publish("test_event", None)
        
        self.assertEqual(count, 2)
        self.assertIn("handler1", results)
        self.assertIn("handler2", results)
    
    def test_unsubscribe(self):
        """测试取消订阅"""
        received = []
        
        def handler(data):
            received.append(data)
        
        event_bus.subscribe("test_event", handler)
        event_bus.publish("test_event", "first")
        
        # 取消订阅
        result = event_bus.unsubscribe("test_event", handler)
        self.assertTrue(result)
        
        event_bus.publish("test_event", "second")
        
        # 只收到第一次
        self.assertEqual(received, ["first"])
    
    def test_once_subscription(self):
        """测试一次性订阅"""
        received = []
        
        def handler(data):
            received.append(data)
        
        event_bus.once("test_event", handler)
        
        # 第一次发布
        event_bus.publish("test_event", "first")
        self.assertEqual(received, ["first"])
        
        # 第二次发布，不应再触发
        event_bus.publish("test_event", "second")
        self.assertEqual(received, ["first"])
    
    def test_has_subscribers(self):
        """测试检查订阅者"""
        self.assertFalse(event_bus.has_subscribers("test_event"))
        
        def handler(data):
            pass
        
        event_bus.subscribe("test_event", handler)
        self.assertTrue(event_bus.has_subscribers("test_event"))
    
    def test_event_types(self):
        """测试事件类型常量"""
        self.assertEqual(EventType.QUOTE_UPDATED, "quote_updated")
        self.assertEqual(EventType.STOCK_SELECTED, "stock_selected")
        self.assertEqual(EventType.SETTINGS_CHANGED, "settings_changed")


if __name__ == '__main__':
    unittest.main()
