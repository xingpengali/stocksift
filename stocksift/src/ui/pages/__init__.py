# -*- coding: utf-8 -*-
"""
页面模块

各个功能页面的实现
"""
from .market_overview import MarketOverviewPage
from .screener_page import ScreenerPage
from .stock_detail import StockDetailPage
from .watchlist_page import WatchlistPage
from .backtest_page import BacktestPage
from .value_investing_page import ValueInvestingPage

__all__ = [
    'MarketOverviewPage',
    'ScreenerPage',
    'StockDetailPage',
    'WatchlistPage',
    'BacktestPage',
    'ValueInvestingPage',
]
