# -*- coding: utf-8 -*-
"""
自选股页面

管理自选股分组和股票列表
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QMenu,
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt

from ui.base_page import BasePage
from ui.widgets.stock_table import StockTable
from utils.logger import get_logger

logger = get_logger(__name__)


class WatchlistPage(BasePage):
    """
    自选股页面
    
    管理自选股分组和预警
    """
    
    page_id = "watchlist"
    page_name = "自选股"
    
    def __init__(self, parent=None):
        self._current_group_id = None
        super().__init__(parent)
    
    def _init_ui(self):
        """初始化UI"""
        super()._init_ui()
        content_layout = self.get_content_layout()
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧分组树
        self._group_tree = QTreeWidget()
        self._group_tree.setHeaderLabel("自选股分组")
        self._group_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._group_tree.customContextMenuRequested.connect(self._on_group_context_menu)
        self._group_tree.currentItemChanged.connect(self._on_group_selected)
        self._group_tree.setMaximumWidth(200)
        
        # 添加默认分组
        self._add_default_groups()
        
        splitter.addWidget(self._group_tree)
        
        # 右侧内容
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        self._add_stock_btn = QPushButton("➕ 添加股票")
        self._add_stock_btn.clicked.connect(self._on_add_stock)
        toolbar_layout.addWidget(self._add_stock_btn)
        
        self._remove_stock_btn = QPushButton("➖ 移除股票")
        self._remove_stock_btn.clicked.connect(self._on_remove_stock)
        toolbar_layout.addWidget(self._remove_stock_btn)
        
        toolbar_layout.addStretch()
        
        self._alert_btn = QPushButton("🔔 预警设置")
        self._alert_btn.clicked.connect(self._on_alert_settings)
        toolbar_layout.addWidget(self._alert_btn)
        
        right_layout.addWidget(toolbar)
        
        # 股票表格
        self._stock_table = StockTable()
        self._stock_table.stock_double_clicked.connect(self._on_stock_double_click)
        right_layout.addWidget(self._stock_table, 1)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 800])
        
        content_layout.addWidget(splitter)
    
    def _add_default_groups(self):
        """添加默认分组"""
        default_groups = [
            ("我的自选", "default"),
            ("价值投资", "value"),
            ("成长股", "growth"),
            ("关注", "watch"),
        ]
        
        for name, group_id in default_groups:
            item = QTreeWidgetItem(self._group_tree)
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, group_id)
    
    def on_enter(self):
        """进入页面时加载数据"""
        super().on_enter()
        self._load_watchlist_data()
    
    def _load_watchlist_data(self):
        """加载自选股数据"""
        self.show_loading(True)
        
        try:
            # TODO: 从数据库加载自选股数据
            # 模拟数据
            mock_data = [
                {'code': '000001', 'name': '平安银行', 'price': 12.50, 'change_pct': 1.25},
                {'code': '000002', 'name': '万科A', 'price': 18.30, 'change_pct': -0.85},
                {'code': '600519', 'name': '贵州茅台', 'price': 1680.00, 'change_pct': 0.52},
            ]
            
            self._stock_table.set_data(mock_data)
            self.show_message(f"已加载 {len(mock_data)} 只自选股")
            
        except Exception as e:
            logger.error(f"加载自选股失败: {e}")
            self.show_error(f"数据加载失败: {e}")
        finally:
            self.show_loading(False)
    
    def _on_group_selected(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """
        分组选择事件
        
        Args:
            current: 当前选中项
            previous: 之前选中项
        """
        if current:
            group_id = current.data(0, Qt.ItemDataRole.UserRole)
            self._current_group_id = group_id
            logger.debug(f"选中分组: {group_id}")
            self._load_group_stocks(group_id)
    
    def _load_group_stocks(self, group_id: str):
        """
        加载分组股票
        
        Args:
            group_id: 分组ID
        """
        # TODO: 加载指定分组的股票
        logger.debug(f"加载分组 {group_id} 的股票")
    
    def _on_group_context_menu(self, position):
        """
        分组右键菜单
        
        Args:
            position: 鼠标位置
        """
        menu = QMenu()
        
        add_action = menu.addAction("➕ 新建分组")
        rename_action = menu.addAction("✏️ 重命名")
        delete_action = menu.addAction("🗑️ 删除分组")
        
        action = menu.exec(self._group_tree.mapToGlobal(position))
        
        if action == add_action:
            self._on_add_group()
        elif action == rename_action:
            self._on_rename_group()
        elif action == delete_action:
            self._on_delete_group()
    
    def _on_add_group(self):
        """添加分组"""
        name, ok = QInputDialog.getText(self, "新建分组", "分组名称:")
        if ok and name:
            item = QTreeWidgetItem(self._group_tree)
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, f"custom_{name}")
            logger.info(f"创建分组: {name}")
    
    def _on_rename_group(self):
        """重命名分组"""
        item = self._group_tree.currentItem()
        if not item:
            return
        
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(
            self, "重命名分组", "新名称:", text=old_name
        )
        
        if ok and new_name:
            item.setText(0, new_name)
            logger.info(f"重命名分组: {old_name} -> {new_name}")
    
    def _on_delete_group(self):
        """删除分组"""
        item = self._group_tree.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分组 \"{item.text(0)}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            index = self._group_tree.indexOfTopLevelItem(item)
            self._group_tree.takeTopLevelItem(index)
            logger.info(f"删除分组: {item.text(0)}")
    
    def _on_add_stock(self):
        """添加股票到分组"""
        code, ok = QInputDialog.getText(self, "添加股票", "股票代码:")
        if ok and code:
            # TODO: 验证股票代码并添加
            logger.info(f"添加股票 {code} 到分组 {self._current_group_id}")
            self.show_message(f"已添加 {code}")
    
    def _on_remove_stock(self):
        """从分组移除股票"""
        codes = self._stock_table.get_selected_codes()
        if not codes:
            self.show_message("请先选择要移除的股票")
            return
        
        reply = QMessageBox.question(
            self, "确认移除",
            f"确定要从分组中移除选中的 {len(codes)} 只股票吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 从分组移除股票
            logger.info(f"从分组移除股票: {codes}")
            self.show_message(f"已移除 {len(codes)} 只股票")
    
    def _on_alert_settings(self):
        """预警设置"""
        codes = self._stock_table.get_selected_codes()
        if not codes:
            self.show_message("请先选择要设置预警的股票")
            return
        
        # TODO: 打开预警设置对话框
        logger.info(f"设置预警: {codes}")
        self.show_message(f"请设置预警条件")
    
    def _on_stock_double_click(self, code: str):
        """
        股票双击事件
        
        Args:
            code: 股票代码
        """
        logger.info(f"查看股票详情: {code}")
        # TODO: 跳转到股票详情页
