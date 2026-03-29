# -*- coding: utf-8 -*-
"""
数据模型模块
"""
from .database import DatabaseManager, get_db_manager, Base, session_scope
from .stock import Stock, StockRepository
from .quote import Quote, QuoteRepository
from .kline import Kline, KlineRepository
from .financial import Financial, FinancialRepository
from .valuation import Valuation, ValuationRepository
from .alert import AlertRule, AlertRecord, AlertRuleRepository, AlertRecordRepository
from .strategy import Strategy, BacktestRecord, StrategyRepository, BacktestRecordRepository
from .watchlist import WatchlistGroup, WatchlistStock, WatchlistGroupRepository, WatchlistStockRepository

__all__ = [
    'DatabaseManager', 'get_db_manager', 'Base', 'session_scope',
    'Stock', 'StockRepository',
    'Quote', 'QuoteRepository',
    'Kline', 'KlineRepository',
    'Financial', 'FinancialRepository',
    'Valuation', 'ValuationRepository',
    'AlertRule', 'AlertRecord', 'AlertRuleRepository', 'AlertRecordRepository',
    'Strategy', 'BacktestRecord', 'StrategyRepository', 'BacktestRecordRepository',
    'WatchlistGroup', 'WatchlistStock', 'WatchlistGroupRepository', 'WatchlistStockRepository',
]
