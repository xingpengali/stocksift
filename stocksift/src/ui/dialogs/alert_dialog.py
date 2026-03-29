# -*- coding: utf-8 -*-
"""
预警设置对话框

设置股票预警规则
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QDoubleSpinBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt

from models.alert import AlertRule
from utils.logger import get_logger

logger = get_logger(__name__)


class AlertDialog(QDialog):
    """
    预警设置对话框
    
    设置股票预警规则
    """
    
    def __init__(self, code: str = None, parent=None):
        super().__init__(parent)
        
        self._code = code
        self._rule = None
        
        self.setWindowTitle("预警设置")
        self.setMinimumSize(400, 350)
        
        self._init_ui()
        
        if code:
            self._code_edit.setText(code)
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 股票代码
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("股票代码:"))
        self._code_edit = QLineEdit()
        self._code_edit.setPlaceholderText("如: 600519")
        code_layout.addWidget(self._code_edit)
        layout.addLayout(code_layout)
        
        # 预警条件
        condition_group = QGroupBox("预警条件")
        condition_layout = QVBoxLayout(condition_group)
        
        # 价格预警
        self._price_check = QCheckBox("价格预警")
        condition_layout.addWidget(self._price_check)
        
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("高于:"))
        self._price_above = QDoubleSpinBox()
        self._price_above.setRange(0, 10000)
        self._price_above.setDecimals(2)
        price_layout.addWidget(self._price_above)
        
        price_layout.addWidget(QLabel("低于:"))
        self._price_below = QDoubleSpinBox()
        self._price_below.setRange(0, 10000)
        self._price_below.setDecimals(2)
        price_layout.addWidget(self._price_below)
        
        condition_layout.addLayout(price_layout)
        
        # 涨跌幅预警
        self._change_check = QCheckBox("涨跌幅预警")
        condition_layout.addWidget(self._change_check)
        
        change_layout = QHBoxLayout()
        change_layout.addWidget(QLabel("涨幅超过(%):"))
        self._change_up = QDoubleSpinBox()
        self._change_up.setRange(0, 100)
        self._change_up.setDecimals(2)
        change_layout.addWidget(self._change_up)
        
        change_layout.addWidget(QLabel("跌幅超过(%):"))
        self._change_down = QDoubleSpinBox()
        self._change_down.setRange(0, 100)
        self._change_down.setDecimals(2)
        change_layout.addWidget(self._change_down)
        
        condition_layout.addLayout(change_layout)
        
        # 成交量预警
        self._volume_check = QCheckBox("成交量预警")
        condition_layout.addWidget(self._volume_check)
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("大于(手):"))
        self._volume_above = QDoubleSpinBox()
        self._volume_above.setRange(0, 100000000)
        self._volume_above.setDecimals(0)
        volume_layout.addWidget(self._volume_above)
        
        condition_layout.addLayout(volume_layout)
        
        layout.addWidget(condition_group)
        
        # 通知方式
        notify_group = QGroupBox("通知方式")
        notify_layout = QVBoxLayout(notify_group)
        
        self._popup_check = QCheckBox("弹出窗口")
        self._popup_check.setChecked(True)
        notify_layout.addWidget(self._popup_check)
        
        self._sound_check = QCheckBox("提示音")
        notify_layout.addWidget(self._sound_check)
        
        layout.addWidget(notify_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._save_btn = QPushButton("💾 保存")
        self._save_btn.clicked.connect(self._on_save)
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
            }
        """)
        btn_layout.addWidget(self._save_btn)
        
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def set_rule(self, rule: AlertRule):
        """
        设置预警规则（编辑模式）
        
        Args:
            rule: 预警规则
        """
        self._rule = rule
        self._code_edit.setText(rule.code)
        
        # 解析条件
        for condition in rule.conditions:
            field = condition.get('field', '')
            operator = condition.get('operator', '')
            value = condition.get('value', 0)
            
            if field == 'price':
                self._price_check.setChecked(True)
                if operator == '>':
                    self._price_above.setValue(float(value))
                elif operator == '<':
                    self._price_below.setValue(float(value))
            
            elif field == 'change_pct':
                self._change_check.setChecked(True)
                if operator == '>':
                    self._change_up.setValue(float(value))
                elif operator == '<':
                    self._change_down.setValue(abs(float(value)))
            
            elif field == 'volume':
                self._volume_check.setChecked(True)
                if operator == '>':
                    self._volume_above.setValue(float(value))
    
    def get_rule(self) -> AlertRule:
        """
        获取预警规则
        
        Returns:
            预警规则对象
        """
        code = self._code_edit.text().strip()
        
        conditions = []
        
        # 价格条件
        if self._price_check.isChecked():
            if self._price_above.value() > 0:
                conditions.append({
                    'field': 'price',
                    'operator': '>',
                    'value': self._price_above.value()
                })
            if self._price_below.value() > 0:
                conditions.append({
                    'field': 'price',
                    'operator': '<',
                    'value': self._price_below.value()
                })
        
        # 涨跌幅条件
        if self._change_check.isChecked():
            if self._change_up.value() > 0:
                conditions.append({
                    'field': 'change_pct',
                    'operator': '>',
                    'value': self._change_up.value()
                })
            if self._change_down.value() > 0:
                conditions.append({
                    'field': 'change_pct',
                    'operator': '<',
                    'value': -self._change_down.value()
                })
        
        # 成交量条件
        if self._volume_check.isChecked() and self._volume_above.value() > 0:
            conditions.append({
                'field': 'volume',
                'operator': '>',
                'value': self._volume_above.value()
            })
        
        # 通知方式
        notify_methods = []
        if self._popup_check.isChecked():
            notify_methods.append('popup')
        if self._sound_check.isChecked():
            notify_methods.append('sound')
        
        return AlertRule(
            code=code,
            conditions=conditions,
            notify_methods=notify_methods,
            enabled=True
        )
    
    def _on_save(self):
        """保存预警规则"""
        code = self._code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return
        
        # 检查是否至少选择了一个条件
        if not any([
            self._price_check.isChecked(),
            self._change_check.isChecked(),
            self._volume_check.isChecked()
        ]):
            QMessageBox.warning(self, "提示", "请至少选择一个预警条件")
            return
        
        self.accept()
