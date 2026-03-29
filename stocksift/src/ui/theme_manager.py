# -*- coding: utf-8 -*-
"""
主题管理器

管理应用主题样式
"""
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ThemeManager(QObject):
    """
    主题管理器
    
    管理应用的主题切换和样式加载
    """
    
    # 主题切换信号
    theme_changed = pyqtSignal(str)
    
    # 内置主题
    THEMES = {
        "light": "themes/light.qss",
        "dark": "themes/dark.qss"
    }
    
    def __init__(self):
        """初始化主题管理器"""
        super().__init__()
        self._current_theme = "light"
        self._styles_cache: Dict[str, str] = {}
        
        # 获取项目根目录
        self._project_root = Path(__file__).parent.parent.parent
        
        # 加载保存的主题设置
        self._load_saved_theme()
    
    def _load_saved_theme(self):
        """加载保存的主题设置"""
        settings = get_settings()
        saved_theme = settings.get("ui.theme", "light")
        if saved_theme in self.THEMES:
            self._current_theme = saved_theme
    
    def apply_theme(self, theme_name: str) -> bool:
        """
        应用主题
        
        Args:
            theme_name: 主题名称 (light/dark)
            
        Returns:
            是否成功
        """
        if theme_name not in self.THEMES:
            logger.error(f"未知主题: {theme_name}")
            return False
        
        try:
            # 加载样式文件
            style_content = self._load_style_file(theme_name)
            if style_content:
                # 应用到应用
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(style_content)
                
                self._current_theme = theme_name
                
                # 保存设置
                settings = get_settings()
                settings.set("ui.theme", theme_name)
                
                # 发送信号
                self.theme_changed.emit(theme_name)
                
                logger.info(f"主题已切换: {theme_name}")
                return True
            else:
                # 使用默认样式
                self._apply_default_style()
                return True
                
        except Exception as e:
            logger.error(f"应用主题失败: {e}")
            return False
    
    def _load_style_file(self, theme_name: str) -> Optional[str]:
        """
        加载样式文件
        
        Args:
            theme_name: 主题名称
            
        Returns:
            样式内容或None
        """
        # 检查缓存
        if theme_name in self._styles_cache:
            return self._styles_cache[theme_name]
        
        # 加载文件
        style_path = self.THEMES.get(theme_name)
        if not style_path:
            return None
        
        full_path = self._project_root / "resources" / style_path
        
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._styles_cache[theme_name] = content
                    return content
            except Exception as e:
                logger.error(f"读取样式文件失败: {e}")
        
        return None
    
    def _apply_default_style(self):
        """应用默认样式"""
        if self._current_theme == "light":
            style = self._get_default_light_style()
        else:
            style = self._get_default_dark_style()
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style)
    
    def _get_default_light_style(self) -> str:
        """获取默认浅色样式"""
        return """
        QMainWindow {
            background-color: #f0f2f5;
        }
        
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 13px;
            color: #262626;
        }
        
        /* 按钮样式 */
        QPushButton {
            background-color: #e94560;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            min-width: 80px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #ff6b6b;
        }
        
        QPushButton:pressed {
            background-color: #c73e54;
        }
        
        QPushButton:disabled {
            background-color: #d9d9d9;
            color: #999;
        }
        
        QPushButton#secondary {
            background-color: #f0f0f0;
            color: #595959;
            border: 1px solid #d9d9d9;
        }
        
        QPushButton#secondary:hover {
            background-color: #e6e6e6;
            border-color: #1890ff;
            color: #1890ff;
        }
        
        /* 输入框样式 */
        QLineEdit {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            padding: 8px 12px;
            background-color: white;
            selection-background-color: #e94560;
        }
        
        QLineEdit:focus {
            border-color: #e94560;
        }
        
        QLineEdit:hover {
            border-color: #b3b3b3;
        }
        
        /* 表格样式 */
        QTableView {
            border: none;
            background-color: white;
            alternate-background-color: #fafafa;
            gridline-color: #f0f0f0;
            selection-background-color: #fff1f0;
            selection-color: #e94560;
        }
        
        QTableView::item {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        QTableView::item:selected {
            background-color: #fff1f0;
            color: #e94560;
        }
        
        QHeaderView::section {
            background-color: #fafafa;
            border: none;
            border-bottom: 2px solid #e8e8e8;
            padding: 10px;
            font-weight: 600;
            color: #595959;
        }
        
        QHeaderView::section:hover {
            background-color: #f0f0f0;
        }
        
        /* 标签页样式 */
        QTabWidget::pane {
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            background-color: white;
            top: -1px;
        }
        
        QTabBar::tab {
            background-color: transparent;
            border: none;
            padding: 10px 20px;
            margin-right: 4px;
            color: #8c8c8c;
            font-weight: 500;
        }
        
        QTabBar::tab:selected {
            color: #e94560;
            border-bottom: 2px solid #e94560;
        }
        
        QTabBar::tab:hover {
            color: #e94560;
        }
        
        /* 下拉框样式 */
        QComboBox {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            padding: 8px 12px;
            background-color: white;
            min-width: 100px;
        }
        
        QComboBox:hover {
            border-color: #e94560;
        }
        
        QComboBox:focus {
            border-color: #e94560;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #8c8c8c;
        }
        
        QComboBox QAbstractItemView {
            border: 1px solid #e8e8e8;
            border-radius: 6px;
            background-color: white;
            selection-background-color: #fff1f0;
        }
        
        /* 分组框样式 */
        QGroupBox {
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            margin-top: 16px;
            padding-top: 16px;
            font-weight: 600;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: #262626;
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background-color: white;
            border-top: 1px solid #e8e8e8;
            color: #8c8c8c;
        }
        
        /* 菜单栏样式 */
        QMenuBar {
            background-color: white;
            border-bottom: 1px solid #e8e8e8;
            padding: 4px;
        }
        
        QMenuBar::item {
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: #fff1f0;
            color: #e94560;
        }
        
        /* 工具栏样式 */
        QToolBar {
            background-color: white;
            border-bottom: 1px solid #e8e8e8;
            spacing: 8px;
            padding: 8px;
        }
        
        QToolButton {
            border: none;
            border-radius: 6px;
            padding: 6px;
            color: #595959;
        }
        
        QToolButton:hover {
            background-color: #f5f5f5;
            color: #e94560;
        }
        
        /* 列表样式 */
        QListWidget {
            border: 1px solid #e8e8e8;
            border-radius: 6px;
            background-color: white;
            outline: none;
        }
        
        QListWidget::item {
            padding: 10px;
            border-radius: 4px;
            margin: 2px 4px;
        }
        
        QListWidget::item:selected {
            background-color: #fff1f0;
            color: #e94560;
        }
        
        QListWidget::item:hover {
            background-color: #f5f5f5;
        }
        
        /* 滚动条样式 */
        QScrollBar:vertical {
            background-color: transparent;
            width: 8px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 4px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: transparent;
            height: 8px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #c0c0c0;
            border-radius: 4px;
            min-width: 30px;
        }
        
        /* 进度条样式 */
        QProgressBar {
            border: none;
            border-radius: 4px;
            background-color: #f0f0f0;
            text-align: center;
            height: 8px;
        }
        
        QProgressBar::chunk {
            background-color: #e94560;
            border-radius: 4px;
        }
        
        /* 文本编辑框样式 */
        QTextEdit {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            padding: 8px;
            background-color: white;
        }
        
        QTextEdit:focus {
            border-color: #e94560;
        }
        
        /* 标签样式 */
        QLabel {
            color: #262626;
        }
        
        QLabel#title {
            font-size: 18px;
            font-weight: 600;
            color: #1a1a2e;
        }
        
        QLabel#subtitle {
            font-size: 12px;
            color: #8c8c8c;
        }
        """
    
    def _get_default_dark_style(self) -> str:
        """获取默认深色样式"""
        return """
        QMainWindow {
            background-color: #1e1e1e;
        }
        
        QWidget {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            font-size: 13px;
            color: #e0e0e0;
            background-color: #1e1e1e;
        }
        
        QPushButton {
            background-color: #0d47a1;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            min-width: 60px;
        }
        
        QPushButton:hover {
            background-color: #1565c0;
        }
        
        QPushButton:pressed {
            background-color: #0a3d8f;
        }
        
        QPushButton:disabled {
            background-color: #424242;
            color: #757575;
        }
        
        QLineEdit {
            border: 1px solid #424242;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        QLineEdit:focus {
            border-color: #0d47a1;
        }
        
        QTableView {
            border: 1px solid #424242;
            background-color: #2d2d2d;
            alternate-background-color: #353535;
            gridline-color: #424242;
            color: #e0e0e0;
        }
        
        QTableView::item:selected {
            background-color: #0d47a1;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #2d2d2d;
            border: 1px solid #424242;
            padding: 6px;
            font-weight: bold;
            color: #e0e0e0;
        }
        
        QTabWidget::pane {
            border: 1px solid #424242;
            background-color: #2d2d2d;
        }
        
        QTabBar::tab {
            background-color: #2d2d2d;
            border: 1px solid #424242;
            padding: 8px 16px;
            margin-right: 2px;
            color: #e0e0e0;
        }
        
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom-color: #1e1e1e;
        }
        
        QTabBar::tab:hover {
            background-color: #0d47a1;
        }
        
        QComboBox {
            border: 1px solid #424242;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        QComboBox:hover {
            border-color: #0d47a1;
        }
        
        QGroupBox {
            border: 1px solid #424242;
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
            color: #e0e0e0;
        }
        
        QStatusBar {
            background-color: #2d2d2d;
            border-top: 1px solid #424242;
            color: #e0e0e0;
        }
        
        QMenuBar {
            background-color: #2d2d2d;
            border-bottom: 1px solid #424242;
            color: #e0e0e0;
        }
        
        QToolBar {
            background-color: #2d2d2d;
            border-bottom: 1px solid #424242;
            spacing: 4px;
            padding: 4px;
        }
        
        QListWidget {
            border: 1px solid #424242;
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        QListWidget::item:selected {
            background-color: #0d47a1;
            color: white;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QProgressBar {
            border: 1px solid #424242;
            border-radius: 4px;
            text-align: center;
            color: #e0e0e0;
        }
        
        QProgressBar::chunk {
            background-color: #0d47a1;
            border-radius: 4px;
        }
        """
    
    def get_current_theme(self) -> str:
        """
        获取当前主题
        
        Returns:
            当前主题名称
        """
        return self._current_theme
    
    def toggle_theme(self) -> str:
        """
        切换主题
        
        Returns:
            切换后的主题名称
        """
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme
    
    def get_available_themes(self) -> list:
        """
        获取可用主题列表
        
        Returns:
            主题名称列表
        """
        return list(self.THEMES.keys())


# 全局主题管理器实例
theme_manager = ThemeManager()
