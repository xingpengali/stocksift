# -*- coding: utf-8 -*-
"""
Baostock 数据源适配器

Baostock 是一个免费的股票数据接口
官网: http://baostock.com
"""
import time
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal

try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    BAOSTOCK_AVAILABLE = False

from .base_adapter import (
    BaseDataAdapter, DataSourceError, ConnectionError,
    DataNotFoundError, RateLimitError, AuthenticationError
)
from config.constants import (
    EXCHANGE_SSE, EXCHANGE_SZSE, EXCHANGE_BSE,
    MARKET_MAIN, MARKET_GEM, MARKET_STAR, MARKET_BJ,
    PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
)
from utils.logger import get_logger

logger = get_logger(__name__)


class BaostockAdapter(BaseDataAdapter):
    """
    Baostock 数据源适配器
    
    Baostock 是一个免费的量化投资数据平台
    """
    
    # 交易所映射
    EXCHANGE_MAP = {
        'sh': EXCHANGE_SSE,
        'sz': EXCHANGE_SZSE,
    }
    
    # K线周期映射
    PERIOD_MAP = {
        PERIOD_DAILY: 'd',
        PERIOD_WEEKLY: 'w',
        PERIOD_MONTHLY: 'm',
    }
    
    # 频率映射（用于历史数据查询）
    FREQUENCY_MAP = {
        PERIOD_DAILY: 'd',
        PERIOD_WEEKLY: 'w',
        PERIOD_MONTHLY: 'm',
    }
    
    def __init__(self, name: str = "baostock", config: Dict[str, Any] = None):
        """
        初始化 Baostock 适配器
        
        Args:
            name: 适配器名称
            config: 配置字典
        """
        super().__init__(name, config or {})
        self._user_id = self.config.get('user_id', '')
        self._password = self.config.get('password', '')
        self._rate_limit_delay = self.config.get('rate_limit_delay', 0.3)
        self._last_request_time = 0
    
    def _rate_limit(self):
        """简单的速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def connect(self) -> bool:
        """
        连接 Baostock 数据源
        
        Returns:
            是否连接成功
        """
        if not BAOSTOCK_AVAILABLE:
            raise ConnectionError("baostock 模块未安装，请执行: pip install baostock")
        
        try:
            self._rate_limit()
            
            # Baostock 登录（可选，匿名也可以访问部分数据）
            if self._user_id and self._password:
                result = bs.login(self._user_id, self._password)
            else:
                result = bs.login()
            
            if result.error_code != '0':
                raise ConnectionError(f"Baostock 登录失败: {result.error_msg}")
            
            self._connected = True
            self._logger.info("Baostock 连接成功")
            return True
            
        except Exception as e:
            raise ConnectionError(f"Baostock 连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开 Baostock 连接"""
        if self._connected:
            try:
                bs.logout()
            except Exception:
                pass
        self._connected = False
        self._logger.info("Baostock 连接已断开")
    
    def _check_result(self, result, context: str = ""):
        """
        检查 Baostock 返回结果
        
        Args:
            result: Baostock 返回结果
            context: 上下文信息
        """
        if result.error_code != '0':
            error_msg = f"{context} 失败: {result.error_msg}" if context else f"请求失败: {result.error_msg}"
            
            if '频率' in result.error_msg or 'limit' in result.error_msg.lower():
                raise RateLimitError(error_msg)
            elif '登录' in result.error_msg or '认证' in result.error_msg:
                raise AuthenticationError(error_msg)
            else:
                raise DataSourceError(error_msg)
    
    def get_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取所有股票列表
        
        Returns:
            股票列表
        """
        self._check_connection()
        
        stocks = []
        
        # 获取上证股票
        self._rate_limit()
        rs = bs.query_all_stock(day=datetime.now().strftime('%Y-%m-%d'))
        self._check_result(rs, "获取股票列表")
        
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            code = row[0]
            
            # 解析代码
            if code.startswith('sh.'):
                exchange = EXCHANGE_SSE
                pure_code = code[3:]
            elif code.startswith('sz.'):
                exchange = EXCHANGE_SZSE
                pure_code = code[3:]
            else:
                continue
            
            # 判断市场类型
            market_type = self._get_market_type(pure_code)
            
            stock = {
                'code': pure_code,
                'name': '',  # Baostock 股票列表接口不返回名称
                'exchange': exchange,
                'market_type': market_type,
                'industry_code': '',
                'industry_name': '',
                'list_date': '',
            }
            stocks.append(stock)
        
        return stocks
    
    def _get_market_type(self, code: str) -> str:
        """
        根据代码判断市场类型
        
        Args:
            code: 股票代码
            
        Returns:
            市场类型
        """
        if code.startswith('60'):
            return MARKET_MAIN
        elif code.startswith('68'):
            return MARKET_STAR
        elif code.startswith('00'):
            return MARKET_MAIN
        elif code.startswith('30'):
            return MARKET_GEM
        elif code.startswith('8') or code.startswith('4'):
            return MARKET_BJ
        else:
            return MARKET_MAIN
    
    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票基本信息字典或 None
        """
        self._check_connection()
        
        bs_code = self._to_bs_code(code)
        
        self._rate_limit()
        rs = bs.query_stock_basic(code=bs_code)
        self._check_result(rs, "获取股票基本信息")
        
        if rs.next():
            row = rs.get_row_data()
            return {
                'code': code,
                'name': row[1] if len(row) > 1 else '',
                'exchange': self.EXCHANGE_MAP.get(row[0][:2], EXCHANGE_SSE) if len(row) > 0 else EXCHANGE_SSE,
                'market_type': self._get_market_type(code),
                'industry': '',
                'list_date': row[5] if len(row) > 5 else '',
            }
        
        return None
    
    def get_daily_quotes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取日线行情
        
        Args:
            codes: 股票代码列表
            
        Returns:
            行情数据列表
        """
        if not codes:
            return []
        
        quotes = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for code in codes:
            bs_code = self._to_bs_code(code)
            
            self._rate_limit()
            rs = bs.query_latest_price(code=bs_code)
            
            if rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                quote = {
                    'code': code,
                    'date': today,
                    'open': Decimal(str(row[2])) if len(row) > 2 and row[2] else Decimal('0'),
                    'high': Decimal(str(row[3])) if len(row) > 3 and row[3] else Decimal('0'),
                    'low': Decimal(str(row[4])) if len(row) > 4 and row[4] else Decimal('0'),
                    'close': Decimal(str(row[5])) if len(row) > 5 and row[5] else Decimal('0'),
                    'volume': int(float(row[6])) if len(row) > 6 and row[6] else 0,
                    'amount': Decimal(str(row[7])) if len(row) > 7 and row[7] else Decimal('0'),
                }
                quotes.append(quote)
        
        return quotes
    
    def get_realtime_quotes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            codes: 股票代码列表
            
        Returns:
            实时行情数据列表
        """
        # Baostock 没有专门的实时行情接口，使用最新价格接口
        return self.get_daily_quotes(codes)
    
    def get_kline_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = PERIOD_DAILY
    ) -> List[Dict[str, Any]]:
        """
        获取 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期
            
        Returns:
            K 线数据列表
        """
        self._check_connection()
        
        bs_code = self._to_bs_code(code)
        frequency = self.FREQUENCY_MAP.get(period, 'd')
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        self._rate_limit()
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,volume,amount",
            start_date=start_str,
            end_date=end_str,
            frequency=frequency,
            adjustflag="3"  # 复权类型：3表示不复权
        )
        
        self._check_result(rs, "获取 K 线数据")
        
        klines = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            
            # 解析代码
            pure_code = row[1][3:] if len(row) > 1 and '.' in row[1] else code
            
            kline = {
                'code': pure_code,
                'date': row[0] if len(row) > 0 else '',
                'open': Decimal(str(row[2])) if len(row) > 2 and row[2] else Decimal('0'),
                'high': Decimal(str(row[3])) if len(row) > 3 and row[3] else Decimal('0'),
                'low': Decimal(str(row[4])) if len(row) > 4 and row[4] else Decimal('0'),
                'close': Decimal(str(row[5])) if len(row) > 5 and row[5] else Decimal('0'),
                'volume': int(float(row[6])) if len(row) > 6 and row[6] else 0,
                'amount': Decimal(str(row[7])) if len(row) > 7 and row[7] else Decimal('0'),
            }
            klines.append(kline)
        
        return klines
    
    def get_financial_data(
        self,
        code: str,
        report_type: str = "annual"
    ) -> Optional[Dict[str, Any]]:
        """
        获取财务数据
        
        Args:
            code: 股票代码
            report_type: 报告类型
            
        Returns:
            财务数据字典或 None
        """
        self._check_connection()
        
        bs_code = self._to_bs_code(code)
        year = datetime.now().year - 1
        
        # 查询季频盈利能力
        self._rate_limit()
        rs = bs.query_profit_data(code=bs_code, year=year, quarter=4)
        self._check_result(rs, "获取财务数据")
        
        if rs.next():
            row = rs.get_row_data()
            return {
                'code': code,
                'report_date': f"{year}-12-31",
                'report_type': report_type,
                'eps': Decimal(str(row[3])) if len(row) > 3 and row[3] else None,
                'roe': Decimal(str(row[4])) if len(row) > 4 and row[4] else None,
            }
        
        return None
    
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
        # Baostock 的利润表接口需要指定年份和季度
        # 这里简化处理，返回最近的数据
        financial = self.get_financial_data(code)
        if financial:
            return [{
                'code': code,
                'report_date': financial.get('report_date', ''),
                'revenue': None,
                'operating_profit': None,
                'net_profit': None,
            }]
        return []
    
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
        self._check_connection()
        
        bs_code = self._to_bs_code(code)
        year = datetime.now().year - 1
        
        self._rate_limit()
        rs = bs.query_balance_data(code=bs_code, year=year, quarter=4)
        self._check_result(rs, "获取资产负债表")
        
        sheets = []
        if rs.next():
            row = rs.get_row_data()
            sheet = {
                'code': code,
                'report_date': f"{year}-12-31",
                'total_assets': Decimal(str(row[3])) if len(row) > 3 and row[3] else None,
                'total_liabilities': Decimal(str(row[4])) if len(row) > 4 and row[4] else None,
                'equity': None,
            }
            sheets.append(sheet)
        
        return sheets
    
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
        self._check_connection()
        
        bs_code = self._to_bs_code(code)
        year = datetime.now().year - 1
        
        self._rate_limit()
        rs = bs.query_cash_flow_data(code=bs_code, year=year, quarter=4)
        self._check_result(rs, "获取现金流量表")
        
        flows = []
        if rs.next():
            row = rs.get_row_data()
            flow = {
                'code': code,
                'report_date': f"{year}-12-31",
                'operating_cash_flow': Decimal(str(row[3])) if len(row) > 3 and row[3] else None,
                'investing_cash_flow': None,
                'financing_cash_flow': None,
            }
            flows.append(flow)
        
        return flows
    
    def get_index_list(self) -> List[Dict[str, Any]]:
        """
        获取指数列表
        
        Returns:
            指数列表
        """
        # Baostock 没有专门的指数列表接口，返回常见指数
        return [
            {'code': 'sh.000001', 'name': '上证指数'},
            {'code': 'sz.399001', 'name': '深证成指'},
            {'code': 'sz.399006', 'name': '创业板指'},
            {'code': 'sh.000016', 'name': '上证50'},
            {'code': 'sh.000300', 'name': '沪深300'},
            {'code': 'sh.000905', 'name': '中证500'},
        ]
    
    def get_index_quotes(self, index_code: str) -> List[Dict[str, Any]]:
        """
        获取指数行情
        
        Args:
            index_code: 指数代码
            
        Returns:
            指数行情数据列表
        """
        self._check_connection()
        
        end_date = datetime.now()
        start_date = end_date.replace(day=1)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        self._rate_limit()
        rs = bs.query_history_k_data_plus(
            index_code,
            "date,open,high,low,close,volume,amount",
            start_date=start_str,
            end_date=end_str,
            frequency='d'
        )
        
        self._check_result(rs, "获取指数行情")
        
        quotes = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            quote = {
                'code': index_code,
                'date': row[0] if len(row) > 0 else '',
                'open': Decimal(str(row[1])) if len(row) > 1 and row[1] else Decimal('0'),
                'high': Decimal(str(row[2])) if len(row) > 2 and row[2] else Decimal('0'),
                'low': Decimal(str(row[3])) if len(row) > 3 and row[3] else Decimal('0'),
                'close': Decimal(str(row[4])) if len(row) > 4 and row[4] else Decimal('0'),
                'volume': int(float(row[5])) if len(row) > 5 and row[5] else 0,
                'amount': Decimal(str(row[6])) if len(row) > 6 and row[6] else Decimal('0'),
            }
            quotes.append(quote)
        
        return quotes
    
    def get_industry_list(self) -> List[Dict[str, Any]]:
        """
        获取行业列表
        
        Returns:
            行业列表
        """
        self._check_connection()
        
        self._rate_limit()
        rs = bs.query_stock_industry()
        self._check_result(rs, "获取行业列表")
        
        industries = {}
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            industry = row[2] if len(row) > 2 else ''
            if industry and industry not in industries:
                industries[industry] = {
                    'code': industry,
                    'name': industry,
                }
        
        return list(industries.values())
    
    def get_concept_list(self) -> List[Dict[str, Any]]:
        """
        获取概念板块列表
        
        Returns:
            概念板块列表
        """
        # Baostock 没有概念板块接口，返回空列表
        return []
    
    def get_capital_flow(self, code: str, trade_date: date) -> Optional[Dict[str, Any]]:
        """
        获取资金流向
        
        Args:
            code: 股票代码
            trade_date: 交易日期
            
        Returns:
            资金流向数据或 None
        """
        # Baostock 没有资金流向接口
        return None
    
    def _to_bs_code(self, code: str) -> str:
        """
        转换为 Baostock 代码格式
        
        Args:
            code: 股票代码
            
        Returns:
            Baostock 格式代码
        """
        code = self.normalize_code(code)
        
        if code.startswith('6'):
            return f"sh.{code}"
        else:
            return f"sz.{code}"
