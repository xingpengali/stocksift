# -*- coding: utf-8 -*-
"""
主窗口

应用的主窗口，包含侧边栏导航和页面切换
"""
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QStatusBar, QToolBar, QMenuBar, QMenu,
    QLabel, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from ui.base_page import BasePage
from ui.theme_manager import theme_manager
from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    主窗口
    
    应用的主界面，包含导航、页面切换、状态栏等
    """
    
    # 导航项定义
    NAV_ITEMS = [
        {"id": "market", "name": "市场概览", "icon": "📊"},
        {"id": "screener", "name": "股票筛选", "icon": "🔍"},
        {"id": "watchlist", "name": "自选股", "icon": "⭐"},
        {"id": "backtest", "name": "策略回测", "icon": "📈"},
        {"id": "value", "name": "价值投资", "icon": "💎"},
        {"id": "settings", "name": "设置", "icon": "⚙️"},
    ]
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        self._pages: Dict[str, BasePage] = {}
        self._current_page_id: Optional[str] = None
        
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        
        # 应用主题
        theme_manager.apply_theme(theme_manager.get_current_theme())
        
        logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("StockSift - A股选股助手")
        self.setMinimumSize(1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        self._sidebar = self._create_sidebar()
        main_layout.addWidget(self._sidebar)
        
        # 页面容器
        self._stacked_widget = QStackedWidget()
        main_layout.addWidget(self._stacked_widget, 1)
    
    def _create_sidebar(self) -> QWidget:
        """
        创建侧边栏
        
        Returns:
            侧边栏部件
        """
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #eaeaea;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/标题区域
        header = QWidget()
        header.setStyleSheet("background-color: #16213e;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 25, 20, 25)
        header_layout.setSpacing(5)
        
        # Logo图标
        logo_label = QLabel("📈")
        logo_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 应用名称
        title_label = QLabel("StockSift")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #e94560;
        """)
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 副标题
        subtitle = QLabel("A股选股助手")
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: #8b8b9a;
        """)
        header_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(header)
        
        # 分隔线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #2d2d44;")
        layout.addWidget(line)
        
        # 导航列表
        self._nav_list = QListWidget()
        self._nav_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #1a1a2e;
                outline: none;
                padding: 10px 0;
            }
            QListWidget::item {
                color: #a0a0b0;
                padding: 14px 20px;
                margin: 2px 10px;
                border-radius: 8px;
                font-size: 14px;
            }
            QListWidget::item:hover {
                color: #ffffff;
                background-color: #2d2d44;
            }
            QListWidget::item:selected {
                color: #ffffff;
                background-color: #e94560;
            }
        """)
        self._nav_list.setFrameShape(QListWidget.Shape.NoFrame)
        self._nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 添加导航项
        for item in self.NAV_ITEMS:
            list_item = QListWidgetItem(f"{item['icon']}  {item['name']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item['id'])
            self._nav_list.addItem(list_item)
        
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self._nav_list)
        
        layout.addStretch()
        
        # 底部信息
        footer = QWidget()
        footer.setStyleSheet("background-color: #16213e;")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #6b6b7b; font-size: 11px;")
        footer_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        copyright_label = QLabel("© 2026 StockSift")
        copyright_label.setStyleSheet("color: #5b5b6b; font-size: 10px;")
        footer_layout.addWidget(copyright_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(footer)
        
        return sidebar
    
    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        theme_action = QAction("切换主题(&T)", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 刷新按钮
        refresh_action = QAction("🔄 刷新", self)
        refresh_action.triggered.connect(self._refresh_current_page)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 主题切换按钮
        theme_action = QAction("🌓 主题", self)
        theme_action.triggered.connect(self._toggle_theme)
        toolbar.addAction(theme_action)
    
    def _init_statusbar(self):
        """初始化状态栏"""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        
        # 状态标签
        self._status_label = QLabel("就绪")
        self._statusbar.addWidget(self._status_label)
        
        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximumWidth(200)
        self._progress_bar.setVisible(False)
        self._statusbar.addPermanentWidget(self._progress_bar)
    
    # ========== 页面管理 ==========
    
    def add_page(self, page: BasePage):
        """
        添加页面
        
        Args:
            page: 页面实例
        """
        page_id = page.get_page_id()
        if not page_id:
            logger.warning("页面ID为空，无法添加")
            return
        
        # 添加到堆叠部件
        self._stacked_widget.addWidget(page)
        self._pages[page_id] = page
        
        # 连接页面信号
        page.message_requested.connect(self.show_message)
        page.error_occurred.connect(self.show_error)
        page.loading_changed.connect(self._on_page_loading_changed)
        
        logger.debug(f"添加页面: {page_id}")
    
    def switch_page(self, page_id: str):
        """
        切换页面
        
        Args:
            page_id: 页面ID
        """
        if page_id not in self._pages:
            logger.warning(f"页面不存在: {page_id}")
            return
        
        # 离开当前页面
        if self._current_page_id:
            current_page = self._pages.get(self._current_page_id)
            if current_page:
                current_page.on_leave()
        
        # 切换到新页面
        page = self._pages[page_id]
        index = self._stacked_widget.indexOf(page)
        self._stacked_widget.setCurrentIndex(index)
        
        # 更新导航选中
        for i in range(self._nav_list.count()):
            item = self._nav_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == page_id:
                self._nav_list.setCurrentRow(i)
                break
        
        # 进入新页面
        self._current_page_id = page_id
        page.on_enter()
        
        logger.debug(f"切换到页面: {page_id}")
    
    def get_current_page(self) -> Optional[BasePage]:
        """
        获取当前页面
        
        Returns:
            当前页面实例或None
        """
        if self._current_page_id:
            return self._pages.get(self._current_page_id)
        return None
    
    def get_page(self, page_id: str) -> Optional[BasePage]:
        """
        获取指定页面
        
        Args:
            page_id: 页面ID
            
        Returns:
            页面实例或None
        """
        return self._pages.get(page_id)
    
    # ========== 事件处理 ==========
    
    def _on_nav_changed(self, index: int):
        """
        导航改变事件
        
        Args:
            index: 选中项索引
        """
        item = self._nav_list.item(index)
        if item:
            page_id = item.data(Qt.ItemDataRole.UserRole)
            self.switch_page(page_id)
    
    def _on_page_loading_changed(self, loading: bool):
        """
        页面加载状态改变
        
        Args:
            loading: 是否加载中
        """
        self._progress_bar.setVisible(loading)
        if loading:
            self._progress_bar.setRange(0, 0)
        else:
            self._progress_bar.setRange(0, 100)
    
    def _refresh_current_page(self):
        """刷新当前页面"""
        page = self.get_current_page()
        if page:
            page.on_refresh()
            self.show_message("页面已刷新")
    
    # ========== 主题 ==========
    
    def set_theme(self, theme: str):
        """
        设置主题
        
        Args:
            theme: 主题名称
        """
        theme_manager.apply_theme(theme)
    
    def _toggle_theme(self):
        """切换主题"""
        new_theme = theme_manager.toggle_theme()
        self.show_message(f"已切换到{ '深色' if new_theme == 'dark' else '浅色' }主题")
    
    # ========== 状态栏 ==========
    
    def show_message(self, message: str, timeout: int = 3000):
        """
        显示状态栏消息
        
        Args:
            message: 消息内容
            timeout: 显示时长（毫秒）
        """
        self._statusbar.showMessage(message, timeout)
        logger.info(message)
    
    def show_error(self, error: str):
        """
        显示错误对话框
        
        Args:
            error: 错误信息
        """
        QMessageBox.critical(self, "错误", error)
        logger.error(error)
    
    def show_progress(self, value: int):
        """
        显示进度
        
        Args:
            value: 进度值（0-100）
        """
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(value)
    
    def hide_progress(self):
        """隐藏进度条"""
        self._progress_bar.setVisible(False)
    
    # ========== 其他 ==========
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 StockSift",
            """<h2>StockSift v1.0.0</h2>
            <p>A股选股助手</p>
            <p>基于 PyQt6 开发的桌面应用</p>
            <p>支持技术分析、基本面分析、策略回测等功能</p>
            """
        )
    
    def closeEvent(self, event):
        """
        关闭事件
        
        Args:
            event: 关闭事件
        """
        # 保存设置
        settings = get_settings()
        settings.save()
        
        logger.info("应用关闭")
        event.accept()
