# -*- coding: utf-8 -*-
"""
页面基类

定义页面的通用接口和生命周期
"""
from typing import Dict, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import pyqtSignal

from utils.logger import get_logger

logger = get_logger(__name__)


class BasePage(QWidget):
    """
    页面基类
    
    所有页面的基类，定义页面生命周期和通用方法
    """
    
    # 页面标识（子类必须覆盖）
    page_id: str = ""
    page_name: str = ""
    
    # 信号
    message_requested = pyqtSignal(str, int)  # 消息, 超时时间
    error_occurred = pyqtSignal(str)  # 错误信息
    loading_changed = pyqtSignal(bool)  # 加载状态
    
    def __init__(self, parent=None):
        """
        初始化
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        self._data: Dict = {}
        self._is_loading = False
        
        # 初始化UI
        self._init_ui()
        
        logger.debug(f"页面初始化: {self.page_id}")
    
    def _init_ui(self):
        """初始化UI（子类可覆盖）"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        
        # 页面标题
        if self.page_name:
            self._title_label = QLabel(self.page_name)
            self._title_label.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            """)
            self._layout.addWidget(self._title_label)
        
        # 进度条（默认隐藏）
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setVisible(False)
        self._layout.addWidget(self._progress_bar)
        
        # 内容区域（子类添加内容）
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._content_widget, 1)
    
    # ========== 生命周期方法 ==========
    
    def on_enter(self):
        """
        进入页面时调用
        
        子类可覆盖此方法执行页面进入时的初始化
        """
        logger.debug(f"进入页面: {self.page_id}")
    
    def on_leave(self):
        """
        离开页面时调用
        
        子类可覆盖此方法执行页面离开时的清理
        """
        logger.debug(f"离开页面: {self.page_id}")
    
    def on_refresh(self):
        """
        刷新页面
        
        子类可覆盖此方法执行页面刷新
        """
        logger.debug(f"刷新页面: {self.page_id}")
    
    # ========== 数据更新 ==========
    
    def update_data(self, data: Dict):
        """
        更新数据
        
        Args:
            data: 数据字典
        """
        self._data.update(data)
        self._on_data_updated()
    
    def _on_data_updated(self):
        """
        数据更新后的处理（子类可覆盖）
        """
        pass
    
    def get_data(self) -> Dict:
        """
        获取当前数据
        
        Returns:
            数据字典
        """
        return self._data.copy()
    
    # ========== 消息显示 ==========
    
    def show_message(self, message: str, timeout: int = 3000):
        """
        显示消息
        
        Args:
            message: 消息内容
            timeout: 显示时长（毫秒）
        """
        self.message_requested.emit(message, timeout)
        logger.info(f"[{self.page_id}] {message}")
    
    def show_error(self, error: str):
        """
        显示错误
        
        Args:
            error: 错误信息
        """
        self.error_occurred.emit(error)
        logger.error(f"[{self.page_id}] {error}")
    
    def show_loading(self, show: bool = True):
        """
        显示/隐藏加载状态
        
        Args:
            show: 是否显示
        """
        self._is_loading = show
        self.loading_changed.emit(show)
        
        if show:
            self._progress_bar.setVisible(True)
            self._progress_bar.setRange(0, 0)  # 无限循环
        else:
            self._progress_bar.setVisible(False)
            self._progress_bar.setRange(0, 100)
    
    def set_progress(self, value: int):
        """
        设置进度值
        
        Args:
            value: 进度值（0-100）
        """
        if self._is_loading:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(value)
    
    def is_loading(self) -> bool:
        """
        是否正在加载
        
        Returns:
            是否正在加载
        """
        return self._is_loading
    
    # ========== 内容区域操作 ==========
    
    def get_content_layout(self) -> QVBoxLayout:
        """
        获取内容区域布局
        
        Returns:
            内容布局
        """
        return self._content_layout
    
    def clear_content(self):
        """清空内容区域"""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    # ========== 页面信息 ==========
    
    @classmethod
    def get_page_id(cls) -> str:
        """
        获取页面ID
        
        Returns:
            页面ID
        """
        return cls.page_id
    
    @classmethod
    def get_page_name(cls) -> str:
        """
        获取页面名称
        
        Returns:
            页面名称
        """
        return cls.page_name
