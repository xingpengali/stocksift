# -*- coding: utf-8 -*-
"""
筛选面板组件

用于设置股票筛选条件
"""
from typing import List, Dict, Any, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QGroupBox,
    QScrollArea, QFrame
)
from PyQt6.QtCore import pyqtSignal

from core.screener import FilterCondition
from utils.logger import get_logger

logger = get_logger(__name__)


class FilterItem(QWidget):
    """单个筛选条件项"""
    
    removed = pyqtSignal(object)  # 发送自身引用
    
    # 字段选项
    FIELDS = [
        {'value': 'pe_ttm', 'label': 'PE(TTM)', 'type': 'number'},
        {'value': 'pb', 'label': 'PB', 'type': 'number'},
        {'value': 'ps', 'label': 'PS', 'type': 'number'},
        {'value': 'roe', 'label': 'ROE%', 'type': 'number'},
        {'value': 'revenue_growth', 'label': '营收增长率%', 'type': 'number'},
        {'value': 'profit_growth', 'label': '净利润增长率%', 'type': 'number'},
        {'value': 'gross_margin', 'label': '毛利率%', 'type': 'number'},
        {'value': 'net_margin', 'label': '净利率%', 'type': 'number'},
        {'value': 'debt_ratio', 'label': '资产负债率%', 'type': 'number'},
        {'value': 'current_ratio', 'label': '流动比率', 'type': 'number'},
        {'value': 'price', 'label': '最新价', 'type': 'number'},
        {'value': 'change_pct', 'label': '涨跌幅%', 'type': 'number'},
        {'value': 'turnover', 'label': '换手率%', 'type': 'number'},
        {'value': 'industry_name', 'label': '所属行业', 'type': 'string'},
        {'value': 'market_type', 'label': '市场类型', 'type': 'string'},
    ]
    
    # 操作符选项
    OPERATORS = [
        {'value': '>', 'label': '大于'},
        {'value': '<', 'label': '小于'},
        {'value': '=', 'label': '等于'},
        {'value': '>=', 'label': '大于等于'},
        {'value': '<=', 'label': '小于等于'},
        {'value': 'between', 'label': '介于'},
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 字段选择
        self.field_combo = QComboBox()
        for field in self.FIELDS:
            self.field_combo.addItem(field['label'], field['value'])
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)
        layout.addWidget(self.field_combo)
        
        # 操作符选择
        self.operator_combo = QComboBox()
        for op in self.OPERATORS:
            self.operator_combo.addItem(op['label'], op['value'])
        layout.addWidget(self.operator_combo)
        
        # 值输入
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("数值")
        self.value_edit.setFixedWidth(100)
        layout.addWidget(self.value_edit)
        
        # 第二个值（用于between）
        self.value2_edit = QLineEdit()
        self.value2_edit.setPlaceholderText("结束值")
        self.value2_edit.setFixedWidth(100)
        self.value2_edit.setVisible(False)
        layout.addWidget(self.value2_edit)
        
        # 删除按钮
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
        """)
        self.remove_btn.clicked.connect(self._on_remove)
        layout.addWidget(self.remove_btn)
        
        layout.addStretch()
    
    def _on_field_changed(self, index: int):
        """字段改变事件"""
        field_value = self.field_combo.currentData()
        # 根据字段类型调整操作符
        for i, field in enumerate(self.FIELDS):
            if field['value'] == field_value:
                if field['type'] == 'string':
                    # 字符串类型只保留等于操作符
                    self.operator_combo.clear()
                    self.operator_combo.addItem('等于', '=')
                    self.operator_combo.addItem('包含', 'like')
                else:
                    # 数值类型恢复所有操作符
                    self.operator_combo.clear()
                    for op in self.OPERATORS:
                        self.operator_combo.addItem(op['label'], op['value'])
                break
    
    def _on_remove(self):
        """删除按钮点击"""
        self.removed.emit(self)
    
    def get_condition(self) -> FilterCondition:
        """
        获取筛选条件
        
        Returns:
            筛选条件对象
        """
        field = self.field_combo.currentData()
        operator = self.operator_combo.currentData()
        value_str = self.value_edit.text().strip()
        
        # 转换数值
        try:
            value = float(value_str)
        except ValueError:
            value = value_str
        
        # 处理between操作符
        value2 = None
        if operator == 'between':
            value2_str = self.value2_edit.text().strip()
            try:
                value2 = float(value2_str)
            except ValueError:
                value2 = None
        
        return FilterCondition(
            field=field,
            operator=operator,
            value=value,
            value2=value2
        )
    
    def set_condition(self, condition: FilterCondition):
        """
        设置筛选条件
        
        Args:
            condition: 筛选条件
        """
        # 设置字段
        index = self.field_combo.findData(condition.field)
        if index >= 0:
            self.field_combo.setCurrentIndex(index)
        
        # 设置操作符
        index = self.operator_combo.findData(condition.operator)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)
        
        # 设置值
        self.value_edit.setText(str(condition.value))
        if condition.value2 is not None:
            self.value2_edit.setText(str(condition.value2))


class FilterPanel(QGroupBox):
    """
    筛选面板组件
    
    用于设置多个筛选条件
    """
    
    # 信号
    filter_changed = pyqtSignal()  # 筛选条件变化
    filter_requested = pyqtSignal()  # 请求筛选
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__("🎯 筛选条件", parent)
        
        self._filter_items: List[FilterItem] = []
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #e8e8e8;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #262626;
                font-size: 14px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        # 滚动区域（用于条件列表）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll)
        
        # 条件容器
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(8)
        self._container_layout.addStretch()
        
        scroll.setWidget(self._container)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 添加条件按钮
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #595959;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-color: #1890ff;
                color: #1890ff;
            }
        """)
        self.add_btn.clicked.connect(self._add_filter_item)
        btn_layout.addWidget(self.add_btn)
        
        # 清空按钮
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #fff2f0;
                color: #ff4d4f;
                border: 1px solid #ffccc7;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff4d4f;
                color: white;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        
        # 筛选按钮
        self.filter_btn = QPushButton("🔍 开始筛选")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                font-weight: 600;
                padding: 8px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #c73e54;
            }
        """)
        self.filter_btn.clicked.connect(self.filter_requested.emit)
        btn_layout.addWidget(self.filter_btn)
        
        layout.addLayout(btn_layout)
        
        # 添加默认条件
        self._add_filter_item()
    
    def _add_filter_item(self):
        """添加筛选条件项"""
        item = FilterItem()
        item.removed.connect(self._remove_filter_item)
        
        # 插入到 stretch 之前
        self._container_layout.insertWidget(
            self._container_layout.count() - 1, item
        )
        self._filter_items.append(item)
        
        self.filter_changed.emit()
        logger.debug("添加筛选条件")
    
    def _remove_filter_item(self, item: FilterItem):
        """移除筛选条件项"""
        if item in self._filter_items:
            self._filter_items.remove(item)
            item.deleteLater()
            self.filter_changed.emit()
            logger.debug("移除筛选条件")
    
    def get_conditions(self) -> List[FilterCondition]:
        """
        获取所有筛选条件
        
        Returns:
            筛选条件列表
        """
        conditions = []
        for item in self._filter_items:
            try:
                condition = item.get_condition()
                if condition.value is not None and condition.value != '':
                    conditions.append(condition)
            except Exception as e:
                logger.warning(f"获取筛选条件失败: {e}")
        return conditions
    
    def load_conditions(self, conditions: List[FilterCondition]):
        """
        加载筛选条件
        
        Args:
            conditions: 筛选条件列表
        """
        self.clear_all()
        
        for condition in conditions:
            self._add_filter_item()
            if self._filter_items:
                self._filter_items[-1].set_condition(condition)
    
    def clear_all(self):
        """清空所有条件"""
        for item in self._filter_items:
            item.deleteLater()
        self._filter_items.clear()
        
        # 添加一个默认条件
        self._add_filter_item()
        
        self.filter_changed.emit()
        logger.debug("清空所有筛选条件")
    
    def set_quick_filter(self, filter_type: str):
        """
        设置快速筛选
        
        Args:
            filter_type: 筛选类型 (value/growth/technical)
        """
        self.clear_all()
        
        if filter_type == 'value':
            # 价值投资筛选
            conditions = [
                FilterCondition('pe_ttm', 'between', 5, 25),
                FilterCondition('pb', '<=', 3),
                FilterCondition('roe', '>=', 10),
            ]
        elif filter_type == 'growth':
            # 成长股筛选
            conditions = [
                FilterCondition('revenue_growth', '>=', 20),
                FilterCondition('profit_growth', '>=', 20),
            ]
        elif filter_type == 'dividend':
            # 高分红筛选
            conditions = [
                FilterCondition('pe_ttm', 'between', 5, 20),
                FilterCondition('pb', '<=', 2),
                FilterCondition('roe', '>=', 8),
            ]
        else:
            return
        
        self.load_conditions(conditions)
