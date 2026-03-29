# -*- coding: utf-8 -*-
"""
股票表格组件

展示股票列表的表格组件
"""
from typing import List, Dict, Callable, Optional
from PyQt6.QtWidgets import (
    QTableView, QAbstractItemView, QMenu,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QBrush

from utils.logger import get_logger

logger = get_logger(__name__)


class StockTableModel(QAbstractTableModel):
    """股票表格数据模型"""
    
    def __init__(self):
        super().__init__()
        self._data: List[Dict] = []
        self._columns: List[Dict] = []
    
    def set_data(self, data: List[Dict]):
        """设置数据"""
        self.beginResetModel()
        self._data = data
        self.endResetModel()
    
    def set_columns(self, columns: List[Dict]):
        """设置列定义"""
        self._columns = columns
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data) or col >= len(self._columns):
            return None
        
        item = self._data[row]
        column = self._columns[col]
        field = column.get('field', '')
        value = item.get(field)
        
        if role == Qt.ItemDataRole.DisplayRole:
            if value is None:
                return "--"
            # 格式化数值
            if isinstance(value, float):
                decimal = column.get('decimal', 2)
                return f"{value:.{decimal}f}"
            return str(value)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            align = column.get('align', 'left')
            if align == 'center':
                return Qt.AlignmentFlag.AlignCenter
            elif align == 'right':
                return Qt.AlignmentFlag.AlignRight
            return Qt.AlignmentFlag.AlignLeft
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            # 根据涨跌幅设置颜色
            if field == 'change_pct' and value is not None:
                if value > 0:
                    return QBrush(QColor("#cf1322"))  # 红色（A股涨）
                elif value < 0:
                    return QBrush(QColor("#3f8600"))  # 绿色（A股跌）
            elif field in ['pe_ttm', 'pb'] and value is not None:
                # 估值颜色
                if value < 10:
                    return QBrush(QColor("#3f8600"))  # 低估-绿
                elif value > 50:
                    return QBrush(QColor("#cf1322"))  # 高估-红
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < len(self._columns):
                return self._columns[section].get('title', '')
        return None
    
    def get_item(self, row: int) -> Optional[Dict]:
        """获取指定行数据"""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None


class StockTable(QTableView):
    """
    股票表格组件
    
    展示股票列表，支持排序、选择、右键菜单
    """
    
    # 信号
    stock_selected = pyqtSignal(str)  # 股票代码
    stock_double_clicked = pyqtSignal(str)  # 双击股票代码
    
    # 默认列定义
    DEFAULT_COLUMNS = [
        {'field': 'code', 'title': '代码', 'width': 80, 'align': 'center'},
        {'field': 'name', 'title': '名称', 'width': 100, 'align': 'center'},
        {'field': 'price', 'title': '最新价', 'width': 80, 'align': 'right', 'decimal': 2},
        {'field': 'change_pct', 'title': '涨跌幅%', 'width': 80, 'align': 'right', 'decimal': 2},
        {'field': 'volume', 'title': '成交量', 'width': 100, 'align': 'right'},
        {'field': 'turnover', 'title': '换手率%', 'width': 80, 'align': 'right', 'decimal': 2},
        {'field': 'pe_ttm', 'title': 'PE(TTM)', 'width': 80, 'align': 'right', 'decimal': 2},
        {'field': 'pb', 'title': 'PB', 'width': 70, 'align': 'right', 'decimal': 2},
        {'field': 'total_mv', 'title': '总市值', 'width': 100, 'align': 'right'},
    ]
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        
        self._model = StockTableModel()
        self._model.set_columns(self.DEFAULT_COLUMNS)
        self.setModel(self._model)
        
        self._init_ui()
        
        # 右键菜单
        self._context_menu = None
        self._menu_callbacks: Dict[str, Callable] = {}
    
    def _init_ui(self):
        """初始化UI"""
        # 选择模式
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # 表头设置
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.setSortIndicatorShown(True)
        
        # 设置列宽
        for i, col in enumerate(self.DEFAULT_COLUMNS):
            width = col.get('width', 100)
            self.setColumnWidth(i, width)
        
        # 交替行颜色
        self.setAlternatingRowColors(True)
        
        # 双击事件
        self.doubleClicked.connect(self._on_double_click)
        
        # 选择变化事件
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
    
    def set_data(self, data: List[Dict]):
        """
        设置表格数据
        
        Args:
            data: 股票数据列表
        """
        self._model.set_data(data)
        logger.debug(f"表格数据更新: {len(data)} 条")
    
    def set_columns(self, columns: List[Dict]):
        """
        设置列定义
        
        Args:
            columns: 列定义列表
        """
        self._model.set_columns(columns)
    
    def get_selected_code(self) -> Optional[str]:
        """
        获取选中的股票代码
        
        Returns:
            股票代码或None
        """
        indexes = self.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            item = self._model.get_item(row)
            if item:
                return item.get('code')
        return None
    
    def get_selected_codes(self) -> List[str]:
        """
        获取所有选中的股票代码
        
        Returns:
            股票代码列表
        """
        codes = []
        seen = set()
        
        for index in self.selectedIndexes():
            row = index.row()
            if row not in seen:
                seen.add(row)
                item = self._model.get_item(row)
                if item:
                    code = item.get('code')
                    if code:
                        codes.append(code)
        
        return codes
    
    def _on_double_click(self, index: QModelIndex):
        """双击事件"""
        item = self._model.get_item(index.row())
        if item:
            code = item.get('code')
            if code:
                self.stock_double_clicked.emit(code)
    
    def _on_selection_changed(self):
        """选择变化事件"""
        code = self.get_selected_code()
        if code:
            self.stock_selected.emit(code)
    
    # ========== 右键菜单 ==========
    
    def set_context_menu(self, menu_items: List[Dict]):
        """
        设置右键菜单
        
        Args:
            menu_items: 菜单项列表 [{'text': '菜单文本', 'callback': 回调函数, 'id': '标识'}]
        """
        self._context_menu = QMenu(self)
        self._menu_callbacks = {}
        
        for item in menu_items:
            action = self._context_menu.addAction(item['text'])
            action_id = item.get('id', item['text'])
            self._menu_callbacks[action_id] = item['callback']
            action.triggered.connect(lambda checked, aid=action_id: self._on_menu_triggered(aid))
    
    def _on_menu_triggered(self, action_id: str):
        """菜单项触发"""
        callback = self._menu_callbacks.get(action_id)
        if callback:
            code = self.get_selected_code()
            if code:
                callback(code)
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        if self._context_menu:
            # 确保有选中行
            index = self.indexAt(event.pos())
            if index.isValid():
                self.selectRow(index.row())
                self._context_menu.exec(event.globalPos())
    
    # ========== 排序 ==========
    
    def sort_by(self, column: str, desc: bool = False):
        """
        按列排序
        
        Args:
            column: 列字段名
            desc: 是否降序
        """
        for i, col in enumerate(self.DEFAULT_COLUMNS):
            if col.get('field') == column:
                order = Qt.SortOrder.DescendingOrder if desc else Qt.SortOrder.AscendingOrder
                self.sortByColumn(i, order)
                break
    
    # ========== 便捷方法 ==========
    
    def clear(self):
        """清空表格"""
        self._model.set_data([])
    
    def refresh(self):
        """刷新表格"""
        self._model.layoutChanged.emit()
