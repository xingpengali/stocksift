# -*- coding: utf-8 -*-
"""
市场概览页面

展示大盘指数、板块热点、涨跌统计等
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton
)
from PyQt6.QtCore import Qt

from ui.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class IndexCard(QWidget):
    """指数卡片组件"""
    
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        
        self._name = name
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
        """)
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # 名称
        name_label = QLabel(self._name)
        name_label.setStyleSheet("""
            font-size: 13px; 
            color: #8c8c8c; 
            border: none;
            font-weight: 500;
        """)
        layout.addWidget(name_label)
        
        # 指数值
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: 700; 
            border: none;
            color: #262626;
        """)
        layout.addWidget(self.value_label)
        
        # 涨跌幅
        self.change_label = QLabel("--")
        self.change_label.setStyleSheet("""
            font-size: 13px; 
            border: none;
            font-weight: 500;
        """)
        layout.addWidget(self.change_label)
        
        layout.addStretch()
    
    def set_data(self, value: float, change: float, change_pct: float):
        """
        设置数据
        
        Args:
            value: 指数值
            change: 涨跌额
            change_pct: 涨跌幅
        """
        self.value_label.setText(f"{value:,.2f}")
        
        # 设置颜色
        if change >= 0:
            color = "#cf1322"  # 红色
            sign = "+"
        else:
            color = "#3f8600"  # 绿色
            sign = ""
        
        self.change_label.setText(
            f"<span style='color:{color}'>{sign}{change:.2f} ({sign}{change_pct:.2f}%)</span>"
        )
        self.value_label.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {color}; border: none;"
        )


class MarketOverviewPage(BasePage):
    """
    市场概览页面
    
    展示市场整体情况
    """
    
    page_id = "market"
    page_name = "市场概览"
    
    def __init__(self, parent=None):
        self._index_cards: dict = {}
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
        
        title = QLabel("市场概览")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1a1a2e;
        """)
        title_layout.addWidget(title)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self.on_refresh)
        title_layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(title_widget)
        
        # 大盘指数区域 - 使用卡片式布局
        indices = ["上证指数", "深证成指", "创业板指", "科创50"]
        index_layout = QHBoxLayout()
        index_layout.setSpacing(16)
        
        for name in indices:
            card = IndexCard(name)
            self._index_cards[name] = card
            index_layout.addWidget(card)
        
        content_layout.addLayout(index_layout)
        
        # 中间区域：板块排行 + 涨跌分布
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)
        
        # 板块涨幅排行
        sector_group = QGroupBox("🏆 板块涨幅排行")
        sector_layout = QVBoxLayout(sector_group)
        sector_layout.setContentsMargins(16, 20, 16, 16)
        sector_layout.setSpacing(12)
        
        self._sector_table = QTableWidget()
        self._sector_table.setColumnCount(3)
        self._sector_table.setHorizontalHeaderLabels(["板块名称", "涨跌幅%", "领涨股"])
        self._sector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._sector_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._sector_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._sector_table.verticalHeader().setVisible(False)
        self._sector_table.setAlternatingRowColors(True)
        sector_layout.addWidget(self._sector_table)
        
        middle_layout.addWidget(sector_group, 1)
        
        # 涨跌分布
        stats_group = QGroupBox("📊 涨跌分布")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(16, 20, 16, 16)
        
        self._stats_label = QLabel("加载中...")
        self._stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_label.setStyleSheet("font-size: 14px; color: #595959; line-height: 2;")
        stats_layout.addWidget(self._stats_label)
        
        middle_layout.addWidget(stats_group, 1)
        
        content_layout.addLayout(middle_layout)
        
        # 资金流向
        flow_group = QGroupBox("💰 资金流向")
        flow_layout = QHBoxLayout(flow_group)
        flow_layout.setContentsMargins(20, 20, 20, 20)
        flow_layout.setSpacing(30)
        
        self._flow_labels = {}
        flow_colors = ["#e94560", "#52c41a", "#1890ff"]
        
        for i, label in enumerate(["主力净流入", "散户净流入", "北向资金"]):
            widget = QWidget()
            wl = QVBoxLayout(widget)
            wl.setSpacing(8)
            
            name_lbl = QLabel(label)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet("font-size: 13px; color: #8c8c8c;")
            wl.addWidget(name_lbl)
            
            value_lbl = QLabel("--")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_lbl.setStyleSheet(f"""
                font-size: 22px; 
                font-weight: 700;
                color: {flow_colors[i]};
            """)
            wl.addWidget(value_lbl)
            
            self._flow_labels[label] = value_lbl
            flow_layout.addWidget(widget)
        
        content_layout.addWidget(flow_group)
    
    def on_enter(self):
        """进入页面时加载数据"""
        super().on_enter()
        self._load_data()
    
    def on_refresh(self):
        """刷新页面"""
        super().on_refresh()
        self._load_data()
    
    def _load_data(self):
        """加载市场数据"""
        self.show_loading(True)
        
        try:
            # TODO: 从数据源获取真实数据
            # 模拟数据
            self._update_index_data()
            self._update_sector_data()
            self._update_stats_data()
            self._update_flow_data()
            
        except Exception as e:
            logger.error(f"加载市场数据失败: {e}")
            self.show_error(f"数据加载失败: {e}")
        finally:
            self.show_loading(False)
    
    def _update_index_data(self):
        """更新指数数据（模拟）"""
        import random
        
        mock_data = {
            "上证指数": (3250.50, 15.30, 0.47),
            "深证成指": (10580.20, -25.60, -0.24),
            "创业板指": (2150.80, 8.90, 0.41),
            "科创50": (980.30, -5.20, -0.53),
        }
        
        for name, (value, change, change_pct) in mock_data.items():
            if name in self._index_cards:
                self._index_cards[name].set_data(value, change, change_pct)
    
    def _update_sector_data(self):
        """更新板块数据（模拟）"""
        sectors = [
            ("半导体", 3.52, "中芯国际"),
            ("新能源", 2.18, "宁德时代"),
            ("医药", 1.85, "恒瑞医药"),
            ("白酒", -1.25, "贵州茅台"),
            ("银行", -0.86, "招商银行"),
        ]
        
        self._sector_table.setRowCount(len(sectors))
        for i, (name, change, leader) in enumerate(sectors):
            self._sector_table.setItem(i, 0, QTableWidgetItem(name))
            
            change_item = QTableWidgetItem(f"{change:+.2f}")
            if change > 0:
                change_item.setForeground(Qt.GlobalColor.red)
            else:
                change_item.setForeground(Qt.GlobalColor.darkGreen)
            self._sector_table.setItem(i, 1, change_item)
            
            self._sector_table.setItem(i, 2, QTableWidgetItem(leader))
    
    def _update_stats_data(self):
        """更新涨跌统计（模拟）"""
        stats = {
            "涨停": 45,
            "涨5%以上": 120,
            "涨0-5%": 1800,
            "平盘": 150,
            "跌0-5%": 2100,
            "跌5%以上": 85,
            "跌停": 12,
        }
        
        text = "  |  ".join([f"{k}: {v}" for k, v in stats.items()])
        self._stats_label.setText(text)
    
    def _update_flow_data(self):
        """更新资金流向（模拟）"""
        flows = {
            "主力净流入": "+58.3亿",
            "散户净流入": "-32.1亿",
            "北向资金": "+25.6亿",
        }
        
        for name, value in flows.items():
            if name in self._flow_labels:
                label = self._flow_labels[name]
                label.setText(value)
                
                # 设置颜色
                if value.startswith("+"):
                    label.setStyleSheet("font-size: 18px; font-weight: bold; color: #cf1322;")
                elif value.startswith("-"):
                    label.setStyleSheet("font-size: 18px; font-weight: bold; color: #3f8600;")
