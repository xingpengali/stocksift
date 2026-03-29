# -*- coding: utf-8 -*-
"""
配置管理模块
"""
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List
from threading import Lock

from .constants import (
    APP_NAME, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    DEFAULT_THEME, DEFAULT_LANGUAGE, DEFAULT_REFRESH_INTERVAL,
    DATA_DIR, CACHE_DIR, DB_DIR, LOG_DIR,
    DEFAULT_DATA_SOURCE_PRIORITY
)


class Settings:
    """配置管理类 - 单例模式"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: str = None):
        if self._initialized:
            return
            
        self._initialized = True
        self._config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._observers: List[callable] = []
        
        # 加载配置
        self.load()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 获取项目根目录（从 src/config/settings.py 向上两级是项目根目录）
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "data" / "config.json")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": APP_NAME,
                "window_width": DEFAULT_WINDOW_WIDTH,
                "window_height": DEFAULT_WINDOW_HEIGHT,
                "theme": DEFAULT_THEME,
                "language": DEFAULT_LANGUAGE,
                "auto_update": True,
                "update_interval": DEFAULT_REFRESH_INTERVAL
            },
            "data_source": {
                "tushare_token": "",
                "baostock_user": "",
                "baostock_password": "",
                "priority": DEFAULT_DATA_SOURCE_PRIORITY.copy()
            },
            "user_preferences": {
                "default_screener_conditions": {},
                "watchlist_refresh_interval": 5,
                "alert_sound": True,
                "alert_popup": True
            },
            "display": {
                "default_page_size": 50,
                "kline_default_days": 120,
                "show_pre_post_market": False
            }
        }
    
    def load(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置（保留默认值）
                    self._config = self._merge_config(
                        self._get_default_config(),
                        loaded_config
                    )
            else:
                # 配置文件不存在，使用默认配置
                self._config = self._get_default_config()
                self.save()
        except json.JSONDecodeError as e:
            # 配置文件损坏，备份并重建
            self._backup_corrupted_config()
            self._config = self._get_default_config()
            self.save()
        except Exception as e:
            # 其他错误，使用默认配置
            self._config = self._get_default_config()
    
    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        """合并配置，保留默认值中不存在的键"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def _backup_corrupted_config(self) -> None:
        """备份损坏的配置文件"""
        if os.path.exists(self._config_path):
            import time
            backup_path = f"{self._config_path}.backup.{int(time.time())}"
            shutil.copy2(self._config_path, backup_path)
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔的路径，如 "app.theme"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
            auto_save: 是否自动保存
        """
        keys = key.split('.')
        config = self._config
        
        # 遍历到倒数第二层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        old_value = config.get(keys[-1])
        config[keys[-1]] = value
        
        # 自动保存
        if auto_save:
            self.save()
        
        # 通知观察者
        if old_value != value:
            self._notify_observers(key, value, old_value)
    
    def reset(self, key: str = None, auto_save: bool = True) -> None:
        """
        重置配置
        
        Args:
            key: 配置键，None表示重置所有
            auto_save: 是否自动保存
        """
        default_config = self._get_default_config()
        
        if key is None:
            self._config = default_config
        else:
            keys = key.split('.')
            default_value = default_config
            
            for k in keys:
                if isinstance(default_value, dict) and k in default_value:
                    default_value = default_value[k]
                else:
                    default_value = None
                    break
            
            self.set(key, default_value, auto_save=False)
        
        if auto_save:
            self.save()
    
    def ensure_directories(self) -> None:
        """确保必要的目录存在"""
        # 从配置文件路径推断项目根目录
        config_path = Path(self._config_path)
        project_root = config_path.parent
        
        directories = [
            config_path.parent,  # data目录
            project_root / CACHE_DIR,
            project_root / DB_DIR,
            project_root / LOG_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def add_observer(self, callback: callable) -> None:
        """添加配置变更观察者"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: callable) -> None:
        """移除配置变更观察者"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, key: str, new_value: Any, old_value: Any) -> None:
        """通知观察者配置变更"""
        for callback in self._observers:
            try:
                callback(key, new_value, old_value)
            except Exception:
                pass
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    @property
    def config_path(self) -> str:
        """获取配置文件路径"""
        return self._config_path


# 全局配置实例
_settings_instance: Optional[Settings] = None


def get_settings(config_path: str = None) -> Settings:
    """
    获取配置实例
    
    Args:
        config_path: 配置文件路径，None使用默认路径
        
    Returns:
        Settings实例
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_path)
    return _settings_instance


def reset_settings() -> None:
    """重置配置实例（主要用于测试）"""
    global _settings_instance
    _settings_instance = None
    Settings._instance = None
