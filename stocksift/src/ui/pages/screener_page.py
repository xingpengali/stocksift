# -*- coding: utf-8 -*-
"""
股票筛选页面

提供多条件股票筛选功能
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QMessageBox, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt

from ui.base_page import BasePage
from ui.widgets.filter_panel import FilterPanel
from ui.widgets.stock_table import StockTable
from core.screener import ScreenerEngine
from utils.exporter import DataExporter
from utils.logger import get_logger

logger = get_logger(__name__)


class ScreenerPage(BasePage):
    """
    股票筛选页面
    
    多条件股票筛选器
    """
    
    page_id = "screener"
    page_name = "股票筛选"
    
    def __init__(self, parent=None):
        self._screener = ScreenerEngine()
        self._exporter = DataExporter()
        super().__init__(parent)
    
    def _init_ui(self):
        """初始化UI"""
        super()._init_ui()
        content_layout = self.get_content_layout()
        content_layout.setSpacing(20)
        
        # 页面标题
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 10)
        
        title = QLabel("🔍 智能选股")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1a1a2e;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("多维度筛选，发现优质股票")
        subtitle.setStyleSheet("font-size: 13px; color: #8c8c8c; margin-left: 10px;")
        title_layout.addWidget(subtitle)
        title_layout.addStretch()
        
        content_layout.addWidget(title_widget)
        
        # 快速筛选标签
        quick_filter_widget = QWidget()
        quick_filter_layout = QHBoxLayout(quick_filter_widget)
        quick_filter_layout.setContentsMargins(0, 0, 0, 10)
        quick_filter_layout.addWidget(QLabel("快速筛选:"))
        
        quick_filters = [
            ("💎 价值投资", "value", "#e94560"),
            ("🚀 成长股", "growth", "#52c41a"),
            ("💰 高分红", "dividend", "#1890ff"),
            ("📈 技术突破", "technical", "#722ed1"),
        ]
        
        for text, filter_type, color in quick_filters:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 16px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, ft=filter_type: self._on_quick_filter(ft))
            quick_filter_layout.addWidget(btn)
        
        quick_filter_layout.addStretch()
        content_layout.addWidget(quick_filter_widget)
        
        # 主布局：左侧筛选 + 右侧结果
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        
        # 左侧筛选面板
        self._filter_panel = FilterPanel()
        self._filter_panel.filter_requested.connect(self._on_filter)
        self._filter_panel.setMaximumWidth(380)
        main_layout.addWidget(self._filter_panel, 1)
        
        # 右侧结果区域
        right_container = QWidget()
        right_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)
        
        # 结果头部
        result_header = QWidget()
        result_header_layout = QHBoxLayout(result_header)
        result_header_layout.setContentsMargins(0, 0, 0, 0)
        
        result_title = QLabel("筛选结果")
        result_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #262626;")
        result_header_layout.addWidget(result_title)
        
        self._stats_label = QLabel("共 0 只股票")
        self._stats_label.setStyleSheet("font-size: 13px; color: #8c8c8c;")
        result_header_layout.addWidget(self._stats_label)
        result_header_layout.addStretch()
        
        # 导出按钮
        self._export_btn = QPushButton("📥 导出")
        self._export_btn.setFixedWidth(80)
        self._export_btn.clicked.connect(self._on_export)
        self._export_btn.setEnabled(False)
        result_header_layout.addWidget(self._export_btn)
        
        right_layout.addWidget(result_header)
        
        # 结果表格
        self._result_table = StockTable()
        self._result_table.stock_double_clicked.connect(self._on_stock_selected)
        
        # 设置右键菜单
        self._result_table.set_context_menu([
            {'text': '查看详情', 'callback': self._on_view_detail, 'id': 'detail'},
            {'text': '⭐ 加入自选', 'callback': self._on_add_watchlist, 'id': 'watchlist'},
        ])
        
        # 让表格占据所有可用空间
        right_layout.addWidget(self._result_table, 1)
        
        main_layout.addWidget(right_container, 2)
        
        # 让主布局占据所有可用垂直空间
        content_layout.addLayout(main_layout, 1)
    
    def _on_filter(self):
        """执行筛选"""
        self.show_loading(True)
        
        try:
            # 获取筛选条件
            conditions = self._filter_panel.get_conditions()
            
            if not conditions:
                self.show_message("请至少设置一个筛选条件")
                self.show_loading(False)
                return
            
            logger.info(f"执行筛选，条件数: {len(conditions)}")
            
            # 执行筛选
            result = self._screener.screen(conditions)
            
            # 更新表格
            self._update_results(result.data)
            
            self.show_message(f"筛选完成，找到 {result.total} 只股票")
            
        except Exception as e:
            logger.error(f"筛选失败: {e}")
            self.show_error(f"筛选失败: {e}")
        finally:
            self.show_loading(False)
    
    def _on_quick_filter(self, filter_type: str):
        """
        快速筛选
        
        Args:
            filter_type: 筛选类型
        """
        self._filter_panel.set_quick_filter(filter_type)
        self._on_filter()
    
    def _update_results(self, results: list):
        """
        更新结果表格
        
        Args:
            results: 筛选结果列表
        """
        self._result_table.set_data(results)
        self._stats_label.setText(f"共 {len(results)} 只股票")
        self._export_btn.setEnabled(len(results) > 0)
    
    def _on_stock_selected(self, code: str):
        """
        股票被选中
        
        Args:
            code: 股票代码
        """
        logger.info(f"选中股票: {code}")
        # TODO: 跳转到股票详情页
    
    def _on_view_detail(self, code: str):
        """
        查看详情
        
        Args:
            code: 股票代码
        """
        logger.info(f"查看详情: {code}")
        # TODO: 跳转到股票详情页
    
    def _on_add_watchlist(self, code: str):
        """
        加入自选
        
        Args:
            code: 股票代码
        """
        logger.info(f"加入自选: {code}")
        # TODO: 添加到自选股
        self.show_message(f"已添加 {code} 到自选股")
    
    def _on_export(self):
        """导出结果"""
        codes = self._result_table.get_selected_codes()
        
        if not codes:
            # 如果没有选中，导出全部
            reply = QMessageBox.question(
                self, "确认导出",
                "未选择股票，是否导出全部结果？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # 获取全部数据
            # TODO: 获取完整数据
            data = []
        else:
            # 导出选中的
            data = []
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "筛选结果.xlsx",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.xlsx'):
                self._exporter.to_excel(data, file_path)
            else:
                self._exporter.to_csv(data, file_path)
            
            self.show_message(f"导出成功: {file_path}")
            
        except Exception as e:
            logger.error(f"导出失败: {e}")
            self.show_error(f"导出失败: {e}")
