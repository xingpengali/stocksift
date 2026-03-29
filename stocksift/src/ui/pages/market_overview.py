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
from PyQt6.QtCore import Qt, QTimer

from ui.base_page import BasePage
from utils.logger import get_logger
from models.market_overview import (
    get_latest_market_indices, 
    get_latest_sectors, 
    get_latest_market_stats,
    get_latest_capital_flow,
    get_last_update_time
)

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
        
        # 最后更新时间
        self._update_time_label = QLabel("更新于: --")
        self._update_time_label.setStyleSheet("""
            font-size: 12px;
            color: #8c8c8c;
            margin-left: 10px;
        """)
        title_layout.addWidget(self._update_time_label)
        
        title_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self.on_refresh)
        title_layout.addWidget(refresh_btn)
        
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
        """加载市场数据（从数据库）"""
        self.show_loading(True)
        
        try:
            # 从数据库获取数据
            self._update_index_data_from_db()
            self._update_sector_data_from_db()
            self._update_stats_data_from_db()
            self._update_flow_data_from_db()
            
            # 更新最后更新时间
            self._update_last_update_time()
            
        except Exception as e:
            logger.error(f"加载市场数据失败: {e}")
            self.show_error(f"数据加载失败: {e}")
        finally:
            self.show_loading(False)
    
    def _update_last_update_time(self):
        """更新最后更新时间显示"""
        try:
            last_update = get_last_update_time()
            if last_update:
                # 格式化为本地时间字符串 (年月日 时分秒)
                time_str = last_update.strftime("%Y-%m-%d %H:%M:%S")
                self._update_time_label.setText(f"更新于: {time_str}")
            else:
                self._update_time_label.setText("更新于: --")
        except Exception as e:
            logger.error(f"更新最后更新时间失败: {e}")
            self._update_time_label.setText("更新于: --")
    
    def _update_index_data_from_db(self):
        """从数据库更新指数数据"""
        try:
            indices = get_latest_market_indices()
            
            if not indices:
                logger.warning("数据库中没有指数数据")
                return
            
            # 指数名称映射
            name_mapping = {
                "上证指数": "上证指数",
                "深证成指": "深证成指",
                "创业板指": "创业板指",
                "科创50": "科创50",
            }
            
            for index_data in indices:
                name = name_mapping.get(index_data.get('name'), index_data.get('name'))
                if name in self._index_cards:
                    self._index_cards[name].set_data(
                        value=index_data.get('value', 0),
                        change=index_data.get('change', 0),
                        change_pct=index_data.get('change_pct', 0)
                    )
                    
        except Exception as e:
            logger.error(f"从数据库更新指数数据失败: {e}")
    
    def _update_sector_data_from_db(self):
        """从数据库更新板块数据"""
        try:
            sectors = get_latest_sectors(limit=10)
            
            if not sectors:
                logger.warning("数据库中没有板块数据")
                return
            
            self._sector_table.setRowCount(len(sectors))
            
            for i, sector in enumerate(sectors):
                name = sector.get('name', '')
                change = sector.get('change_pct', 0)
                leader = sector.get('leader_name', '-')
                
                self._sector_table.setItem(i, 0, QTableWidgetItem(name))
                
                change_item = QTableWidgetItem(f"{change:+.2f}")
                if change > 0:
                    change_item.setForeground(Qt.GlobalColor.red)
                else:
                    change_item.setForeground(Qt.GlobalColor.darkGreen)
                self._sector_table.setItem(i, 1, change_item)
                
                self._sector_table.setItem(i, 2, QTableWidgetItem(leader))
                
        except Exception as e:
            logger.error(f"从数据库更新板块数据失败: {e}")
    
    def _update_stats_data_from_db(self):
        """从数据库更新涨跌统计"""
        try:
            stats = get_latest_market_stats()
            
            if not stats:
                logger.warning("数据库中没有统计数据")
                return
            
            stats_text = {
                "涨停": stats.get('limit_up', 0),
                "涨5%以上": stats.get('up_over_5', 0),
                "涨0-5%": stats.get('up_0_to_5', 0),
                "平盘": stats.get('flat', 0),
                "跌0-5%": stats.get('down_0_to_5', 0),
                "跌5%以上": stats.get('down_over_5', 0),
                "跌停": stats.get('limit_down', 0),
            }
            
            text = "  |  ".join([f"{k}: {v}" for k, v in stats_text.items()])
            self._stats_label.setText(text)
            
        except Exception as e:
            logger.error(f"从数据库更新统计数据失败: {e}")
    
    def _update_flow_data_from_db(self):
        """从数据库更新资金流向"""
        try:
            flow = get_latest_capital_flow()
            
            if not flow:
                logger.warning("数据库中没有资金流向数据")
                return
            
            flows = {
                "主力净流入": self._format_amount(flow.get('main_inflow', 0)),
                "散户净流入": self._format_amount(flow.get('retail_inflow', 0)),
                "北向资金": self._format_amount(flow.get('north_inflow', 0)),
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
                    else:
                        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #595959;")
                        
        except Exception as e:
            logger.error(f"从数据库更新资金流向失败: {e}")
    
    def _format_amount(self, amount):
        """格式化金额显示"""
        if amount is None:
            return "--"
        
        amount = float(amount)
        
        if amount >= 100000000:
            return f"+{amount/100000000:.1f}亿" if amount > 0 else f"{amount/100000000:.1f}亿"
        elif amount >= 10000:
            return f"+{amount/10000:.1f}万" if amount > 0 else f"{amount/10000:.1f}万"
        else:
            return f"+{amount:.0f}" if amount > 0 else f"{amount:.0f}"
