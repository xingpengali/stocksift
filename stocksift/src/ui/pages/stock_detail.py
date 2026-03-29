# -*- coding: utf-8 -*-
"""
股票详情页面

展示单只股票的详细信息
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QGridLayout, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt

from ui.base_page import BasePage
from ui.widgets.kline_chart import KlineChart
from utils.logger import get_logger

logger = get_logger(__name__)


class StockDetailPage(BasePage):
    """
    股票详情页面
    
    展示股票的K线图、技术指标、财务数据等
    """
    
    page_id = "stock_detail"
    page_name = "股票详情"
    
    def __init__(self, parent=None):
        self._current_code: str = None
        super().__init__(parent)
    
    def _init_ui(self):
        """初始化UI"""
        super()._init_ui()
        content_layout = self.get_content_layout()
        content_layout.setSpacing(15)
        
        # 顶部信息栏
        info_layout = QHBoxLayout()
        
        # 股票代码和名称
        self._code_label = QLabel("--")
        self._code_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        info_layout.addWidget(self._code_label)
        
        self._name_label = QLabel("--")
        self._name_label.setStyleSheet("font-size: 16px; color: #666;")
        info_layout.addWidget(self._name_label)
        
        info_layout.addStretch()
        
        # 最新价和涨跌幅
        self._price_label = QLabel("--")
        self._price_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        info_layout.addWidget(self._price_label)
        
        self._change_label = QLabel("--")
        self._change_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(self._change_label)
        
        content_layout.addLayout(info_layout)
        
        # 标签页
        self._tab_widget = QTabWidget()
        
        # K线图页
        self._kline_tab = self._create_kline_tab()
        self._tab_widget.addTab(self._kline_tab, "📈 K线图")
        
        # 技术指标页
        self._tech_tab = self._create_tech_tab()
        self._tab_widget.addTab(self._tech_tab, "📊 技术指标")
        
        # 资金流向页
        self._flow_tab = self._create_flow_tab()
        self._tab_widget.addTab(self._flow_tab, "💰 资金流向")
        
        # 财务数据页
        self._financial_tab = self._create_financial_tab()
        self._tab_widget.addTab(self._financial_tab, "📋 财务数据")
        
        # 价值投资页
        self._value_tab = self._create_value_tab()
        self._tab_widget.addTab(self._value_tab, "💎 价值投资")
        
        content_layout.addWidget(self._tab_widget, 1)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self._add_watchlist_btn = QPushButton("⭐ 加入自选")
        self._add_watchlist_btn.clicked.connect(self._on_add_watchlist)
        btn_layout.addWidget(self._add_watchlist_btn)
        
        self._set_alert_btn = QPushButton("🔔 设置预警")
        self._set_alert_btn.clicked.connect(self._on_set_alert)
        btn_layout.addWidget(self._set_alert_btn)
        
        btn_layout.addStretch()
        
        content_layout.addLayout(btn_layout)
    
    def _create_kline_tab(self) -> QWidget:
        """创建K线图标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 周期选择
        period_layout = QHBoxLayout()
        periods = [("日线", "daily"), ("周线", "weekly"), ("月线", "monthly")]
        for text, period in periods:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(period == "daily")
            btn.clicked.connect(lambda checked, p=period: self._on_period_changed(p))
            period_layout.addWidget(btn)
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # K线图
        self._kline_chart = KlineChart()
        layout.addWidget(self._kline_chart, 1)
        
        return widget
    
    def _create_tech_tab(self) -> QWidget:
        """创建技术指标标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 指标选择
        group = QGroupBox("技术指标")
        grid = QGridLayout(group)
        
        indicators = [
            ("MA", "移动平均线"),
            ("MACD", "指数平滑异同平均"),
            ("KDJ", "随机指标"),
            ("RSI", "相对强弱指标"),
            ("BOLL", "布林带"),
            ("VOL", "成交量"),
        ]
        
        for i, (code, name) in enumerate(indicators):
            btn = QPushButton(f"{code} - {name}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=code: self._on_indicator_toggled(c, checked))
            grid.addWidget(btn, i // 3, i % 3)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_flow_tab(self) -> QWidget:
        """创建资金流向标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 资金流向统计
        group = QGroupBox("今日资金流向")
        grid = QGridLayout(group)
        
        labels = [
            ("主力净流入", "main_flow"),
            ("散户净流入", "retail_flow"),
            ("大单流入", "big_in"),
            ("大单流出", "big_out"),
            ("中单流入", "mid_in"),
            ("中单流出", "mid_out"),
        ]
        
        self._flow_labels = {}
        for i, (text, key) in enumerate(labels):
            grid.addWidget(QLabel(text + ":"), i, 0)
            label = QLabel("--")
            self._flow_labels[key] = label
            grid.addWidget(label, i, 1)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_financial_tab(self) -> QWidget:
        """创建财务数据标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 主要财务指标
        group = QGroupBox("主要财务指标")
        grid = QGridLayout(group)
        
        metrics = [
            ("每股收益(EPS)", "eps"),
            ("每股净资产(BPS)", "bps"),
            ("净资产收益率(ROE)", "roe"),
            ("毛利率", "gross_margin"),
            ("净利率", "net_margin"),
            ("营收增长率", "revenue_growth"),
            ("净利润增长率", "profit_growth"),
            ("资产负债率", "debt_ratio"),
        ]
        
        self._financial_labels = {}
        for i, (text, key) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            grid.addWidget(QLabel(text + ":"), row, col)
            label = QLabel("--")
            self._financial_labels[key] = label
            grid.addWidget(label, row, col + 1)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_value_tab(self) -> QWidget:
        """创建价值投资标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 估值指标
        group = QGroupBox("估值指标")
        grid = QGridLayout(group)
        
        metrics = [
            ("PE(TTM)", "pe_ttm"),
            ("PB", "pb"),
            ("PS", "ps"),
            ("PCF", "pcf"),
            ("股息率", "dividend_yield"),
            ("PEG", "peg"),
        ]
        
        self._value_labels = {}
        for i, (text, key) in enumerate(metrics):
            grid.addWidget(QLabel(text + ":"), i // 3, (i % 3) * 2)
            label = QLabel("--")
            self._value_labels[key] = label
            grid.addWidget(label, i // 3, (i % 3) * 2 + 1)
        
        layout.addWidget(group)
        
        # 估值分析
        analysis_group = QGroupBox("估值分析")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self._value_analysis = QLabel("暂无分析数据")
        self._value_analysis.setWordWrap(True)
        analysis_layout.addWidget(self._value_analysis)
        
        layout.addWidget(analysis_group)
        layout.addStretch()
        
        return widget
    
    def set_stock(self, code: str, name: str = None):
        """
        设置当前股票
        
        Args:
            code: 股票代码
            name: 股票名称
        """
        self._current_code = code
        self._code_label.setText(code)
        if name:
            self._name_label.setText(name)
        
        # 加载数据
        self._load_stock_data()
    
    def on_enter(self):
        """进入页面"""
        super().on_enter()
        if self._current_code:
            self._load_stock_data()
    
    def _load_stock_data(self):
        """加载股票数据"""
        if not self._current_code:
            return
        
        self.show_loading(True)
        
        try:
            # TODO: 从数据源获取真实数据
            # 模拟K线数据
            import random
            from datetime import datetime, timedelta
            
            kline_data = []
            base_price = 50.0
            for i in range(60):
                date = datetime.now() - timedelta(days=60-i)
                change = random.uniform(-0.05, 0.05)
                open_price = base_price * (1 + change)
                close_price = open_price * (1 + random.uniform(-0.03, 0.03))
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
                volume = random.randint(1000000, 10000000)
                
                kline_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume,
                })
                
                base_price = close_price
            
            self._kline_chart.set_data(kline_data)
            
            # 更新价格显示
            if kline_data:
                latest = kline_data[-1]
                prev = kline_data[-2] if len(kline_data) > 1 else latest
                
                self._price_label.setText(f"{latest['close']:.2f}")
                
                change = latest['close'] - prev['close']
                change_pct = (change / prev['close']) * 100 if prev['close'] else 0
                
                if change >= 0:
                    color = "#cf1322"
                    sign = "+"
                else:
                    color = "#3f8600"
                    sign = ""
                
                self._change_label.setText(
                    f"<span style='color:{color}'>{sign}{change:.2f} ({sign}{change_pct:.2f}%)</span>"
                )
                self._price_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            
            self.show_message(f"已加载 {self._current_code} 数据")
            
        except Exception as e:
            logger.error(f"加载股票数据失败: {e}")
            self.show_error(f"数据加载失败: {e}")
        finally:
            self.show_loading(False)
    
    def _on_period_changed(self, period: str):
        """
        周期改变
        
        Args:
            period: 周期类型
        """
        self._kline_chart.set_period(period)
        self._load_stock_data()
    
    def _on_indicator_toggled(self, indicator: str, checked: bool):
        """
        指标切换
        
        Args:
            indicator: 指标名称
            checked: 是否选中
        """
        if checked:
            self._kline_chart.add_indicator(indicator)
        else:
            self._kline_chart.remove_indicator(indicator)
    
    def _on_add_watchlist(self):
        """加入自选"""
        if self._current_code:
            logger.info(f"加入自选: {self._current_code}")
            self.show_message(f"已添加 {self._current_code} 到自选股")
    
    def _on_set_alert(self):
        """设置预警"""
        if self._current_code:
            logger.info(f"设置预警: {self._current_code}")
            # TODO: 打开预警设置对话框
            self.show_message(f"请设置 {self._current_code} 的预警条件")
