# -*- coding: utf-8 -*-
"""
K线图表组件

使用 pyqtgraph 绘制K线图
"""
from typing import List, Dict, Optional
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入 pyqtgraph
try:
    import pyqtgraph as pg
    from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    logger.warning("pyqtgraph 未安装，K线图将使用简化显示")


class KlineChart(QWidget):
    """
    K线图表组件
    
    展示股票K线图，支持技术指标叠加
    """
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        
        self._data: List[Dict] = []
        self._indicators: Dict[str, Dict] = {}
        self._period: str = "daily"
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if PYQTGRAPH_AVAILABLE:
            self._init_pyqtgraph(layout)
        else:
            self._init_placeholder(layout)
    
    def _init_pyqtgraph(self, layout: QVBoxLayout):
        """使用 pyqtgraph 初始化图表"""
        # 创建绘图部件
        self._plot_widget = pg.PlotWidget()
        layout.addWidget(self._plot_widget)
        
        # 配置
        self._plot_widget.setMenuEnabled(False)
        self._plot_widget.setMouseEnabled(x=True, y=True)
        self._plot_widget.enableAutoRange()
        
        # 创建K线图项
        self._candlestick_item = CandlestickItem()
        self._plot_widget.addItem(self._candlestick_item)
        
        # 成交量图
        self._volume_plot = pg.PlotWidget()
        self._volume_plot.setMaximumHeight(100)
        self._volume_plot.setMenuEnabled(False)
        self._volume_plot.setXLink(self._plot_widget)
        layout.addWidget(self._volume_plot)
        
        self._volume_item = pg.BarGraphItem(x=[], height=[], width=0.8)
        self._volume_plot.addItem(self._volume_item)
    
    def _init_placeholder(self, layout: QVBoxLayout):
        """初始化占位显示"""
        from PyQt6.QtWidgets import QLabel
        
        self._placeholder = QLabel("K线图显示区域\n\n请安装 pyqtgraph 以获得完整功能\npip install pyqtgraph")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px dashed #ccc;
                color: #666;
                font-size: 14px;
            }
        """)
        layout.addWidget(self._placeholder)
    
    def set_data(self, kline_data: List[Dict]):
        """
        设置K线数据
        
        Args:
            kline_data: K线数据列表，每项包含:
                - date: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
        """
        self._data = kline_data
        
        if PYQTGRAPH_AVAILABLE and hasattr(self, '_candlestick_item'):
            self._candlestick_item.set_data(kline_data)
            self._update_volume(kline_data)
            self._update_indicators()
        
        logger.debug(f"K线图数据更新: {len(kline_data)} 条")
    
    def _update_volume(self, data: List[Dict]):
        """更新成交量图"""
        if not data or not hasattr(self, '_volume_item'):
            return
        
        x = np.arange(len(data))
        heights = [d.get('volume', 0) for d in data]
        
        # 根据涨跌设置颜色
        brushes = []
        for d in data:
            if d.get('close', 0) >= d.get('open', 0):
                brushes.append(pg.mkColor('#cf1322'))  # 涨-红
            else:
                brushes.append(pg.mkColor('#3f8600'))  # 跌-绿
        
        self._volume_item.setOpts(
            x=x, height=heights, width=0.8, brushes=brushes
        )
    
    def add_indicator(self, indicator_type: str, params: Optional[Dict] = None):
        """
        添加技术指标
        
        Args:
            indicator_type: 指标类型 (ma/boll/macd/kdj)
            params: 指标参数
        """
        self._indicators[indicator_type] = params or {}
        self._update_indicators()
        
        logger.debug(f"添加指标: {indicator_type}")
    
    def remove_indicator(self, indicator_type: str):
        """
        移除技术指标
        
        Args:
            indicator_type: 指标类型
        """
        if indicator_type in self._indicators:
            del self._indicators[indicator_type]
            self._update_indicators()
            logger.debug(f"移除指标: {indicator_type}")
    
    def _update_indicators(self):
        """更新指标显示"""
        if not PYQTGRAPH_AVAILABLE or not self._data:
            return
        
        # TODO: 实现技术指标计算和绘制
        pass
    
    def set_period(self, period: str):
        """
        设置周期
        
        Args:
            period: 周期 (daily/weekly/monthly)
        """
        self._period = period
        logger.debug(f"设置周期: {period}")
    
    def zoom_in(self):
        """放大"""
        if PYQTGRAPH_AVAILABLE and hasattr(self, '_plot_widget'):
            self._plot_widget.getViewBox().scaleBy((0.9, 1))
    
    def zoom_out(self):
        """缩小"""
        if PYQTGRAPH_AVAILABLE and hasattr(self, '_plot_widget'):
            self._plot_widget.getViewBox().scaleBy((1.1, 1))
    
    def clear(self):
        """清空图表"""
        self._data = []
        self._indicators.clear()
        
        if PYQTGRAPH_AVAILABLE:
            if hasattr(self, '_candlestick_item'):
                self._candlestick_item.set_data([])
            if hasattr(self, '_volume_item'):
                self._volume_item.setOpts(x=[], height=[])


class CandlestickItem(pg.GraphicsObject):
    """
    K线图形项
    
    用于绘制K线蜡烛图
    """
    
    def __init__(self):
        super().__init__()
        self._data: List[Dict] = []
        self._picture = None
        self.generatePicture()
    
    def set_data(self, data: List[Dict]):
        """设置数据"""
        self._data = data
        self.generatePicture()
        self.update()
    
    def generatePicture(self):
        """生成图形"""
        self._picture = pg.QtGui.QPicture()
        
        if not self._data:
            return
        
        p = pg.QtGui.QPainter(self._picture)
        
        for i, d in enumerate(self._data):
            open_price = d.get('open', 0)
            high_price = d.get('high', 0)
            low_price = d.get('low', 0)
            close_price = d.get('close', 0)
            
            # 确定颜色
            if close_price >= open_price:
                color = pg.mkColor('#cf1322')  # 涨-红
            else:
                color = pg.mkColor('#3f8600')  # 跌-绿
            
            p.setPen(pg.mkPen(color))
            p.setBrush(pg.mkBrush(color))
            
            # 绘制实体
            x = i
            body_top = max(open_price, close_price)
            body_bottom = min(open_price, close_price)
            body_height = body_top - body_bottom
            
            if body_height == 0:
                body_height = 0.01  # 避免高度为0
            
            p.drawRect(
                pg.QtCore.QRectF(x - 0.3, body_bottom, 0.6, body_height)
            )
            
            # 绘制影线
            p.drawLine(
                pg.QtCore.QPointF(x, low_price),
                pg.QtCore.QPointF(x, high_price)
            )
        
        p.end()
    
    def paint(self, p, *args):
        """绘制"""
        if self._picture:
            p.drawPicture(0, 0, self._picture)
    
    def boundingRect(self):
        """边界矩形"""
        return pg.QtCore.QRectF(self._picture.boundingRect())
