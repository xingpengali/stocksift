# -*- coding: utf-8 -*-
"""
数据源适配器基类

定义统一的数据源接口，所有具体数据源适配器必须继承此类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from utils.logger import get_logger

logger = get_logger(__name__)


class DataSourceError(Exception):
    """数据源异常基类"""
    pass


class ConnectionError(DataSourceError):
    """连接异常"""
    pass


class DataNotFoundError(DataSourceError):
    """数据不存在异常"""
    pass


class RateLimitError(DataSourceError):
    """请求频率限制异常"""
    pass


class AuthenticationError(DataSourceError):
    """认证异常"""
    pass


class BaseDataAdapter(ABC):
    """
    数据源适配器抽象基类
    
    所有数据源适配器必须继承此类并实现抽象方法
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化适配器
        
        Args:
            name: 适配器名称
            config: 配置字典
        """
        self.name = name
        self.config = config
        self._connected = False
        self._logger = get_logger(f"{__name__}.{name}")
    
    # ==================== 连接管理 ====================
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接数据源
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开数据源连接"""
        pass
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            是否已连接
        """
        return self._connected
    
    def _check_connection(self):
        """检查连接状态，未连接时抛出异常"""
        if not self._connected:
            raise ConnectionError(f"数据源 {self.name} 未连接")
    
    # ==================== 股票基础数据 ====================
    
    @abstractmethod
    def get_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取所有股票列表
        
        Returns:
            股票列表，每项包含：
            - code: 股票代码
            - name: 股票名称
            - exchange: 交易所
            - market_type: 市场类型
            - industry_code: 行业代码
            - industry_name: 行业名称
            - list_date: 上市日期
        """
        pass
    
    @abstractmethod
    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票基本信息字典或None
        """
        pass
    
    # ==================== 行情数据 ====================
    
    @abstractmethod
    def get_daily_quotes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取日线行情
        
        Args:
            codes: 股票代码列表
            
        Returns:
            行情数据列表，每项包含：
            - code: 股票代码
            - date: 日期
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
        """
        pass
    
    @abstractmethod
    def get_realtime_quotes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            codes: 股票代码列表
            
        Returns:
            实时行情数据列表
        """
        pass
    
    @abstractmethod
    def get_kline_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期（daily/weekly/monthly）
            
        Returns:
            K线数据列表
        """
        pass
    
    # ==================== 财务数据 ====================
    
    @abstractmethod
    def get_financial_data(
        self,
        code: str,
        report_type: str = "annual"
    ) -> Optional[Dict[str, Any]]:
        """
        获取财务数据
        
        Args:
            code: 股票代码
            report_type: 报告类型（Q1/Q2/Q3/annual）
            
        Returns:
            财务数据字典或None
        """
        pass
    
    @abstractmethod
    def get_income_statement(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取利润表
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            利润表数据列表
        """
        pass
    
    @abstractmethod
    def get_balance_sheet(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取资产负债表
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            资产负债表数据列表
        """
        pass
    
    @abstractmethod
    def get_cash_flow(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取现金流量表
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            现金流量表数据列表
        """
        pass
    
    # ==================== 市场数据 ====================
    
    @abstractmethod
    def get_index_list(self) -> List[Dict[str, Any]]:
        """
        获取指数列表
        
        Returns:
            指数列表
        """
        pass
    
    @abstractmethod
    def get_index_quotes(self, index_code: str) -> List[Dict[str, Any]]:
        """
        获取指数行情
        
        Args:
            index_code: 指数代码
            
        Returns:
            指数行情数据列表
        """
        pass
    
    @abstractmethod
    def get_industry_list(self) -> List[Dict[str, Any]]:
        """
        获取行业列表
        
        Returns:
            行业列表
        """
        pass
    
    @abstractmethod
    def get_concept_list(self) -> List[Dict[str, Any]]:
        """
        获取概念板块列表
        
        Returns:
            概念板块列表
        """
        pass
    
    # ==================== 资金流向 ====================
    
    @abstractmethod
    def get_capital_flow(self, code: str, trade_date: date) -> Optional[Dict[str, Any]]:
        """
        获取资金流向
        
        Args:
            code: 股票代码
            trade_date: 交易日期
            
        Returns:
            资金流向数据或None
        """
        pass
    
    # ==================== 辅助方法 ====================
    
    def normalize_code(self, code: str) -> str:
        """
        标准化股票代码
        
        Args:
            code: 原始代码
            
        Returns:
            标准化后的代码（6位数字）
        """
        if not code:
            return ""
        
        # 去除空格和后缀
        code = code.strip().upper()
        if '.' in code:
            code = code.split('.')[0]
        
        return code
    
    def add_exchange_suffix(self, code: str) -> str:
        """
        添加交易所后缀
        
        Args:
            code: 股票代码
            
        Returns:
            带后缀的代码
        """
        code = self.normalize_code(code)
        
        if not code:
            return ""
        
        # 根据代码规则判断交易所
        if code.startswith('6'):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"
    
    def handle_error(self, error: Exception, context: str = ""):
        """
        统一错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        self._logger.error(f"{context} 错误: {error}")
        
        if isinstance(error, (ConnectionError, DataNotFoundError, RateLimitError)):
            raise error
        else:
            raise DataSourceError(f"{context} 失败: {error}")


class AdapterFactory:
    """
    适配器工厂
    
    用于注册和创建数据源适配器
    """
    
    _adapters: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: type):
        """
        注册适配器
        
        Args:
            name: 适配器名称
            adapter_class: 适配器类
        """
        if not issubclass(adapter_class, BaseDataAdapter):
            raise ValueError(f"适配器类必须继承 BaseDataAdapter")
        
        cls._adapters[name] = adapter_class
        logger.info(f"注册数据源适配器: {name}")
    
    @classmethod
    def create(cls, name: str, config: Dict[str, Any]) -> BaseDataAdapter:
        """
        创建适配器实例
        
        Args:
            name: 适配器名称
            config: 配置字典
            
        Returns:
            适配器实例
        """
        if name not in cls._adapters:
            raise ValueError(f"未找到适配器: {name}，可用适配器: {list(cls._adapters.keys())}")
        
        adapter_class = cls._adapters[name]
        return adapter_class(name, config)
    
    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        获取所有已注册的适配器名称
        
        Returns:
            适配器名称列表
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查适配器是否已注册
        
        Args:
            name: 适配器名称
            
        Returns:
            是否已注册
        """
        return name in cls._adapters
