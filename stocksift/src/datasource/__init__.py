# -*- coding: utf-8 -*-
"""
数据源适配器模块
"""
from .base_adapter import (
    BaseDataAdapter, AdapterFactory,
    DataSourceError, ConnectionError, DataNotFoundError,
    RateLimitError, AuthenticationError
)

# 注册适配器
try:
    from .tushare_adapter import TushareAdapter
    AdapterFactory.register('tushare', TushareAdapter)
except ImportError:
    pass

try:
    from .baostock_adapter import BaostockAdapter
    AdapterFactory.register('baostock', BaostockAdapter)
except ImportError:
    pass

__all__ = [
    'BaseDataAdapter',
    'AdapterFactory',
    'DataSourceError',
    'ConnectionError',
    'DataNotFoundError',
    'RateLimitError',
    'AuthenticationError',
]
