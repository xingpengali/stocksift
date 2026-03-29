# -*- coding: utf-8 -*-
"""
配置模块测试
"""
import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings, get_settings, reset_settings
from config.constants import (
    APP_NAME, DEFAULT_THEME, DEFAULT_WINDOW_WIDTH,
    EXCHANGE_SSE, EXCHANGE_SZSE, MARKET_MAIN, MARKET_GEM
)


class TestConstants(unittest.TestCase):
    """测试常量定义"""
    
    def test_app_constants(self):
        """测试应用常量"""
        self.assertEqual(APP_NAME, "StockSift")
        self.assertIsNotNone(DEFAULT_THEME)
        self.assertIsInstance(DEFAULT_WINDOW_WIDTH, int)
    
    def test_exchange_constants(self):
        """测试交易所常量"""
        self.assertEqual(EXCHANGE_SSE, "SSE")
        self.assertEqual(EXCHANGE_SZSE, "SZSE")
    
    def test_market_constants(self):
        """测试市场板块常量"""
        self.assertEqual(MARKET_MAIN, "main")
        self.assertEqual(MARKET_GEM, "gem")
    
    def test_market_names(self):
        """测试市场名称映射"""
        from config.constants import MARKET_NAMES
        self.assertIn(MARKET_MAIN, MARKET_NAMES)
        self.assertIn(MARKET_GEM, MARKET_NAMES)


class TestSettings(unittest.TestCase):
    """测试配置管理"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        reset_settings()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")
        
        # 创建配置实例
        self.settings = Settings(self.config_path)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # 重置单例
        reset_settings()
    
    def test_singleton(self):
        """测试单例模式"""
        settings1 = get_settings(self.config_path)
        settings2 = get_settings(self.config_path)
        self.assertIs(settings1, settings2)
    
    def test_default_config(self):
        """测试默认配置"""
        # 验证默认配置项存在
        self.assertEqual(self.settings.get("app.name"), APP_NAME)
        self.assertEqual(self.settings.get("app.theme"), DEFAULT_THEME)
        self.assertIsNotNone(self.settings.get("data_source.priority"))
    
    def test_get_set(self):
        """测试获取和设置配置"""
        # 设置配置
        self.settings.set("app.theme", "dark", auto_save=False)
        
        # 获取配置
        self.assertEqual(self.settings.get("app.theme"), "dark")
        
        # 获取不存在的配置
        self.assertIsNone(self.settings.get("nonexistent.key"))
        self.assertEqual(self.settings.get("nonexistent.key", "default"), "default")
    
    def test_nested_config(self):
        """测试嵌套配置"""
        # 设置嵌套配置
        self.settings.set("user_preferences.test_key", "test_value", auto_save=False)
        
        # 获取嵌套配置
        self.assertEqual(self.settings.get("user_preferences.test_key"), "test_value")
    
    def test_save_load(self):
        """测试保存和加载配置"""
        # 修改配置
        self.settings.set("app.theme", "dark")
        
        # 重新加载
        new_settings = Settings(self.config_path)
        
        # 验证配置已保存
        self.assertEqual(new_settings.get("app.theme"), "dark")
    
    def test_reset(self):
        """测试重置配置"""
        # 修改配置
        self.settings.set("app.theme", "dark", auto_save=False)
        self.assertEqual(self.settings.get("app.theme"), "dark")
        
        # 重置单个配置
        self.settings.reset("app.theme", auto_save=False)
        self.assertEqual(self.settings.get("app.theme"), DEFAULT_THEME)
    
    def test_ensure_directories(self):
        """测试确保目录存在"""
        # 创建临时项目目录
        temp_project = tempfile.mkdtemp()
        config_path = os.path.join(temp_project, "data", "config.json")
        
        try:
            settings = Settings(config_path)
            settings.ensure_directories()
            
            # 验证目录已创建
            self.assertTrue(os.path.exists(os.path.join(temp_project, "data")))
            self.assertTrue(os.path.exists(os.path.join(temp_project, "data", "cache")))
            self.assertTrue(os.path.exists(os.path.join(temp_project, "data", "db")))
            self.assertTrue(os.path.exists(os.path.join(temp_project, "data", "logs")))
        finally:
            shutil.rmtree(temp_project, ignore_errors=True)
    
    def test_observers(self):
        """测试配置变更观察者"""
        changes = []
        
        def on_change(key, new_value, old_value):
            changes.append((key, new_value, old_value))
        
        # 添加观察者
        self.settings.add_observer(on_change)
        
        # 修改配置
        self.settings.set("app.theme", "dark", auto_save=False)
        
        # 验证观察者被调用
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ("app.theme", "dark", DEFAULT_THEME))
        
        # 移除观察者
        self.settings.remove_observer(on_change)
    
    def test_corrupted_config(self):
        """测试损坏的配置文件处理"""
        # 写入损坏的JSON
        with open(self.config_path, 'w') as f:
            f.write("{invalid json")
        
        # 重新加载应该使用默认配置
        settings = Settings(self.config_path)
        self.assertEqual(settings.get("app.name"), APP_NAME)
        
        # 验证备份文件已创建
        backup_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.backup.')]
        self.assertEqual(len(backup_files), 1)


class TestSettingsEdgeCases(unittest.TestCase):
    """测试配置管理边界情况"""
    
    def setUp(self):
        reset_settings()
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_settings()
    
    def test_empty_config_file(self):
        """测试空配置文件"""
        # 创建空文件
        with open(self.config_path, 'w') as f:
            f.write("{}")
        
        settings = Settings(self.config_path)
        # 应该使用默认配置填充
        self.assertIsNotNone(settings.get("app.name"))
    
    def test_merge_config(self):
        """测试配置合并"""
        # 创建包含部分配置的文件
        partial_config = {
            "app": {
                "theme": "dark"
                # 缺少其他字段
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(partial_config, f)
        
        settings = Settings(self.config_path)
        
        # 自定义配置应保留
        self.assertEqual(settings.get("app.theme"), "dark")
        # 默认配置应补充
        self.assertIsNotNone(settings.get("app.window_width"))


if __name__ == '__main__':
    unittest.main()
