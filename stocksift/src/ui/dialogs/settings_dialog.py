# -*- coding: utf-8 -*-
"""
设置对话框

应用设置配置
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QSpinBox, QCheckBox, QGroupBox, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt

from config.settings import get_settings
from ui.theme_manager import theme_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """
    设置对话框
    
    配置应用各项设置
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)
        
        self._settings = get_settings()
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标签页
        self._tab_widget = QTabWidget()
        
        # 通用设置
        self._general_tab = self._create_general_tab()
        self._tab_widget.addTab(self._general_tab, "⚙️ 通用")
        
        # 数据源设置
        self._data_tab = self._create_data_tab()
        self._tab_widget.addTab(self._data_tab, "📡 数据源")
        
        # 显示设置
        self._display_tab = self._create_display_tab()
        self._tab_widget.addTab(self._display_tab, "🖥️ 显示")
        
        # 通知设置
        self._notify_tab = self._create_notify_tab()
        self._tab_widget.addTab(self._notify_tab, "🔔 通知")
        
        layout.addWidget(self._tab_widget)
        
        # 按钮区域
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
    
    def _create_general_tab(self) -> QWidget:
        """创建通用设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 数据存储
        data_group = QGroupBox("数据存储")
        data_layout = QHBoxLayout(data_group)
        
        data_layout.addWidget(QLabel("数据目录:"))
        self._data_dir_edit = QLineEdit()
        self._data_dir_edit.setReadOnly(True)
        data_layout.addWidget(self._data_dir_edit, 1)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._on_browse_data_dir)
        data_layout.addWidget(browse_btn)
        
        layout.addWidget(data_group)
        
        # 自动更新
        update_group = QGroupBox("自动更新")
        update_layout = QVBoxLayout(update_group)
        
        self._auto_update_check = QCheckBox("启动时检查更新")
        update_layout.addWidget(self._auto_update_check)
        
        layout.addWidget(update_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_data_tab(self) -> QWidget:
        """创建数据源设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Tushare设置
        tushare_group = QGroupBox("Tushare")
        tushare_layout = QGridLayout(tushare_group)
        
        tushare_layout.addWidget(QLabel("Token:"), 0, 0)
        self._tushare_token_edit = QLineEdit()
        self._tushare_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        tushare_layout.addWidget(self._tushare_token_edit, 0, 1)
        
        tushare_layout.addWidget(QLabel("数据频率:"), 1, 0)
        self._tushare_freq_combo = QComboBox()
        self._tushare_freq_combo.addItems(["日线", "周线", "月线"])
        tushare_layout.addWidget(self._tushare_freq_combo, 1, 1)
        
        layout.addWidget(tushare_group)
        
        # Baostock设置
        baostock_group = QGroupBox("Baostock")
        baostock_layout = QGridLayout(baostock_group)
        
        baostock_layout.addWidget(QLabel("用户名:"), 0, 0)
        self._baostock_user_edit = QLineEdit()
        baostock_layout.addWidget(self._baostock_user_edit, 0, 1)
        
        baostock_layout.addWidget(QLabel("密码:"), 1, 0)
        self._baostock_pass_edit = QLineEdit()
        self._baostock_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        baostock_layout.addWidget(self._baostock_pass_edit, 1, 1)
        
        layout.addWidget(baostock_group)
        
        # 默认数据源
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("默认数据源:"))
        self._default_source_combo = QComboBox()
        self._default_source_combo.addItems(["Tushare", "Baostock"])
        default_layout.addWidget(self._default_source_combo)
        default_layout.addStretch()
        
        layout.addLayout(default_layout)
        layout.addStretch()
        
        return widget
    
    def _create_display_tab(self) -> QWidget:
        """创建显示设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QHBoxLayout(theme_group)
        
        theme_layout.addWidget(QLabel("界面主题:"))
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(theme_manager.get_available_themes())
        theme_layout.addWidget(self._theme_combo)
        theme_layout.addStretch()
        
        layout.addWidget(theme_group)
        
        # 刷新设置
        refresh_group = QGroupBox("数据刷新")
        refresh_layout = QGridLayout(refresh_group)
        
        refresh_layout.addWidget(QLabel("自动刷新间隔(秒):"), 0, 0)
        self._refresh_spin = QSpinBox()
        self._refresh_spin.setRange(0, 3600)
        self._refresh_spin.setSingleStep(30)
        self._refresh_spin.setSuffix(" 秒")
        refresh_layout.addWidget(self._refresh_spin, 0, 1)
        
        refresh_layout.addWidget(QLabel("0表示不自动刷新"), 0, 2)
        
        layout.addWidget(refresh_group)
        
        # 表格设置
        table_group = QGroupBox("表格显示")
        table_layout = QVBoxLayout(table_group)
        
        self._alternate_row_check = QCheckBox("交替行颜色")
        table_layout.addWidget(self._alternate_row_check)
        
        self._grid_lines_check = QCheckBox("显示网格线")
        table_layout.addWidget(self._grid_lines_check)
        
        layout.addWidget(table_group)
        layout.addStretch()
        
        return widget
    
    def _create_notify_tab(self) -> QWidget:
        """创建通知设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 预警通知
        alert_group = QGroupBox("预警通知")
        alert_layout = QVBoxLayout(alert_group)
        
        self._alert_popup_check = QCheckBox("弹出窗口提醒")
        alert_layout.addWidget(self._alert_popup_check)
        
        self._alert_sound_check = QCheckBox("播放提示音")
        alert_layout.addWidget(self._alert_sound_check)
        
        layout.addWidget(alert_group)
        
        # 系统通知
        notify_group = QGroupBox("系统通知")
        notify_layout = QVBoxLayout(notify_group)
        
        self._notify_update_check = QCheckBox("数据更新通知")
        notify_layout.addWidget(self._notify_update_check)
        
        self._notify_error_check = QCheckBox("错误通知")
        notify_layout.addWidget(self._notify_error_check)
        
        layout.addWidget(notify_group)
        layout.addStretch()
        
        return widget
    
    def _load_settings(self):
        """加载设置"""
        # 通用
        self._data_dir_edit.setText(
            self._settings.get("data.data_dir", "")
        )
        self._auto_update_check.setChecked(
            self._settings.get("general.auto_update", True)
        )
        
        # 数据源
        self._tushare_token_edit.setText(
            self._settings.get("tushare.token", "")
        )
        self._baostock_user_edit.setText(
            self._settings.get("baostock.username", "")
        )
        default_source = self._settings.get("datasource.default", "tushare")
        index = self._default_source_combo.findText(default_source.capitalize())
        if index >= 0:
            self._default_source_combo.setCurrentIndex(index)
        
        # 显示
        theme = self._settings.get("ui.theme", "light")
        index = self._theme_combo.findText(theme)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)
        
        self._refresh_spin.setValue(
            self._settings.get("ui.refresh_interval", 60)
        )
        self._alternate_row_check.setChecked(
            self._settings.get("ui.alternate_rows", True)
        )
        self._grid_lines_check.setChecked(
            self._settings.get("ui.grid_lines", True)
        )
        
        # 通知
        self._alert_popup_check.setChecked(
            self._settings.get("notification.alert_popup", True)
        )
        self._alert_sound_check.setChecked(
            self._settings.get("notification.alert_sound", False)
        )
    
    def _on_browse_data_dir(self):
        """浏览数据目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择数据目录", self._data_dir_edit.text()
        )
        if dir_path:
            self._data_dir_edit.setText(dir_path)
    
    def _on_save(self):
        """保存设置"""
        try:
            # 通用
            self._settings.set("data.data_dir", self._data_dir_edit.text())
            self._settings.set("general.auto_update", self._auto_update_check.isChecked())
            
            # 数据源
            self._settings.set("tushare.token", self._tushare_token_edit.text())
            self._settings.set("baostock.username", self._baostock_user_edit.text())
            self._settings.set(
                "datasource.default",
                self._default_source_combo.currentText().lower()
            )
            
            # 显示
            new_theme = self._theme_combo.currentText()
            if new_theme != theme_manager.get_current_theme():
                theme_manager.apply_theme(new_theme)
            self._settings.set("ui.theme", new_theme)
            
            self._settings.set("ui.refresh_interval", self._refresh_spin.value())
            self._settings.set("ui.alternate_rows", self._alternate_row_check.isChecked())
            self._settings.set("ui.grid_lines", self._grid_lines_check.isChecked())
            
            # 通知
            self._settings.set("notification.alert_popup", self._alert_popup_check.isChecked())
            self._settings.set("notification.alert_sound", self._alert_sound_check.isChecked())
            
            # 保存到文件
            self._settings.save()
            
            logger.info("设置已保存")
            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()
            
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
