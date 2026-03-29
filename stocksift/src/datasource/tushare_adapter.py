# -*- coding: utf-8 -*-
"""
Tushare 数据源适配器

Tushare Pro 接口实现，需要申请 token
官网: https://tushare.pro
"""
import time
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False

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


class TushareAdapter(BaseDataAdapter):
    """
    Tushare 数据源适配器
    
    使用 Tushare Pro 接口获取 A 股数据
    """
    
    # 交易所映射
    EXCHANGE_MAP = {
        'SSE': EXCHANGE_SSE,
        'SZSE': EXCHANGE_SZSE,
        'BSE': EXCHANGE_BSE,
    }
    
    # 市场类型映射
    MARKET_MAP = {
        '主板': MARKET_MAIN,
        '创业板': MARKET_GEM,
        '科创板': MARKET_STAR,
        '北交所': MARKET_BJ,
    }
    
    # K线周期映射
    PERIOD_MAP = {
        PERIOD_DAILY: 'D',
        PERIOD_WEEKLY: 'W',
        PERIOD_MONTHLY: 'M',
    }
    
    def __init__(self, name: str = "tushare", config: Dict[str, Any] = None):
        """
        初始化 Tushare 适配器
        
        Args:
            name: 适配器名称
            config: 配置字典，需要包含 'token'
        """
        super().__init__(name, config or {})
        self._pro = None
        self._token = self.config.get('token', '')
        self._rate_limit_delay = self.config.get('rate_limit_delay', 0.5)  # 请求间隔
        self._last_request_time = 0
    
    def _rate_limit(self):
        """简单的速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def connect(self) -> bool:
        """
        连接 Tushare 数据源
        
        Returns:
            是否连接成功
        """
        if not TUSHARE_AVAILABLE:
            raise ConnectionError("tushare 模块未安装，请执行: pip install tushare")
        
        if not self._token:
            raise AuthenticationError("缺少 Tushare token，请在配置中设置")
        
        try:
            self._pro = ts.pro_api(self._token)
            # 测试连接
            self._rate_limit()
            self._pro.trade_cal(exchange='SSE', limit=1)
            
            self._connected = True
            self._logger.info("Tushare 连接成功")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if 'token' in error_msg.lower() or '认证' in error_msg:
                raise AuthenticationError(f"Tushare 认证失败: {e}")
            raise ConnectionError(f"Tushare 连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开 Tushare 连接"""
        self._pro = None
        self._connected = False
        self._logger.info("Tushare 连接已断开")
    
    def _call_api(self, api_name: str, **kwargs) -> Optional[Any]:
        """
        调用 Tushare API
        
        Args:
            api_name: API 名称
            **kwargs: 参数
            
        Returns:
            API 返回结果
        """
        self._check_connection()
        self._rate_limit()
        
        try:
            api_func = getattr(self._pro, api_name)
            result = api_func(**kwargs)
            
            if result is None or result.empty:
                return None
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'limit' in error_msg or '频率' in error_msg:
                raise RateLimitError(f"Tushare 请求频率限制: {e}")
            elif 'token' in error_msg or '认证' in error_msg:
                raise AuthenticationError(f"Tushare 认证失败: {e}")
            raise DataSourceError(f"Tushare API 调用失败: {e}")
    
    def get_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取所有股票列表
        
        Returns:
            股票列表
        """
        df = self._call_api('stock_basic', exchange='', list_status='L')
        
        if df is None:
            return []
        
        stocks = []
        for _, row in df.iterrows():
            stock = {
                'code': row['ts_code'].split('.')[0],
                'name': row['name'],
                'exchange': self.EXCHANGE_MAP.get(row['exchange'], row['exchange']),
                'market_type': self.MARKET_MAP.get(row['market'], MARKET_MAIN),
                'industry_code': row.get('industry', ''),
                'industry_name': row.get('industry', ''),
                'list_date': row['list_date'],
            }
            stocks.append(stock)
        
        return stocks
    
    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票基本信息字典或 None
        """
        ts_code = self.add_exchange_suffix(code)
        df = self._call_api('stock_basic', ts_code=ts_code)
        
        if df is None or df.empty:
            return None
        
        row = df.iloc[0]
        return {
            'code': code,
            'name': row['name'],
            'exchange': self.EXCHANGE_MAP.get(row['exchange'], row['exchange']),
            'market_type': self.MARKET_MAP.get(row['market'], MARKET_MAIN),
            'industry': row.get('industry', ''),
            'list_date': row['list_date'],
        }
    
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
        
        # 转换为 Tushare 格式
        ts_codes = [self.add_exchange_suffix(c) for c in codes]
        trade_date = datetime.now().strftime('%Y%m%d')
        
        df = self._call_api(
            'daily',
            ts_code=','.join(ts_codes),
            trade_date=trade_date
        )
        
        if df is None:
            return []
        
        quotes = []
        for _, row in df.iterrows():
            quote = {
                'code': row['ts_code'].split('.')[0],
                'date': row['trade_date'],
                'open': Decimal(str(row['open'])),
                'high': Decimal(str(row['high'])),
                'low': Decimal(str(row['low'])),
                'close': Decimal(str(row['close'])),
                'volume': int(row['vol'] * 100),  # 转换为股
                'amount': Decimal(str(row['amount'] * 1000)),  # 转换为元
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
        # Tushare Pro 没有免费实时行情接口，使用日线数据代替
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
        ts_code = self.add_exchange_suffix(code)
        freq = self.PERIOD_MAP.get(period, 'D')
        
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        # 使用 pro_bar 接口
        try:
            self._rate_limit()
            df = ts.pro_bar(
                ts_code=ts_code,
                freq=freq,
                start_date=start_str,
                end_date=end_str,
                api=self._pro
            )
        except Exception as e:
            # 如果 pro_bar 失败，尝试使用 daily 接口
            if period == PERIOD_DAILY:
                df = self._call_api(
                    'daily',
                    ts_code=ts_code,
                    start_date=start_str,
                    end_date=end_str
                )
            else:
                raise DataSourceError(f"获取 K 线数据失败: {e}")
        
        if df is None or df.empty:
            return []
        
        klines = []
        for _, row in df.iterrows():
            kline = {
                'code': code,
                'date': row['trade_date'],
                'open': Decimal(str(row['open'])),
                'high': Decimal(str(row['high'])),
                'low': Decimal(str(row['low'])),
                'close': Decimal(str(row['close'])),
                'volume': int(row['vol'] * 100) if 'vol' in row else 0,
                'amount': Decimal(str(row['amount'] * 1000)) if 'amount' in row else Decimal('0'),
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
        ts_code = self.add_exchange_suffix(code)
        
        # 获取最新财务指标
        df = self._call_api('fina_indicator', ts_code=ts_code, limit=1)
        
        if df is None or df.empty:
            return None
        
        row = df.iloc[0]
        return {
            'code': code,
            'report_date': row.get('ann_date', ''),
            'report_type': report_type,
            'eps': Decimal(str(row['eps'])) if pd_not_null(row.get('eps')) else None,
            'roe': Decimal(str(row['roe'])) if pd_not_null(row.get('roe')) else None,
            'roa': Decimal(str(row['roa'])) if pd_not_null(row.get('roa')) else None,
            'gross_margin': Decimal(str(row['grossprofit_margin'])) if pd_not_null(row.get('grossprofit_margin')) else None,
            'net_margin': Decimal(str(row['netprofit_margin'])) if pd_not_null(row.get('netprofit_margin')) else None,
            'debt_ratio': Decimal(str(row['debt_to_assets'])) if pd_not_null(row.get('debt_to_assets')) else None,
            'revenue_growth': Decimal(str(row['or_yoy'])) if pd_not_null(row.get('or_yoy')) else None,
            'profit_growth': Decimal(str(row['netprofit_yoy'])) if pd_not_null(row.get('netprofit_yoy')) else None,
        }
    
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
        ts_code = self.add_exchange_suffix(code)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        df = self._call_api(
            'income',
            ts_code=ts_code,
            start_date=start_str,
            end_date=end_str
        )
        
        if df is None:
            return []
        
        statements = []
        for _, row in df.iterrows():
            stmt = {
                'code': code,
                'report_date': row['ann_date'],
                'revenue': Decimal(str(row['total_revenue'])) if pd_not_null(row.get('total_revenue')) else None,
                'operating_profit': Decimal(str(row['operate_profit'])) if pd_not_null(row.get('operate_profit')) else None,
                'net_profit': Decimal(str(row['n_income'])) if pd_not_null(row.get('n_income')) else None,
            }
            statements.append(stmt)
        
        return statements
    
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
        ts_code = self.add_exchange_suffix(code)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        df = self._call_api(
            'balancesheet',
            ts_code=ts_code,
            start_date=start_str,
            end_date=end_str
        )
        
        if df is None:
            return []
        
        sheets = []
        for _, row in df.iterrows():
            sheet = {
                'code': code,
                'report_date': row['ann_date'],
                'total_assets': Decimal(str(row['total_assets'])) if pd_not_null(row.get('total_assets')) else None,
                'total_liabilities': Decimal(str(row['total_liab'])) if pd_not_null(row.get('total_liab')) else None,
                'equity': Decimal(str(row['total_hldr_eqy_exc_min_int'])) if pd_not_null(row.get('total_hldr_eqy_exc_min_int')) else None,
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
        ts_code = self.add_exchange_suffix(code)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        df = self._call_api(
            'cashflow',
            ts_code=ts_code,
            start_date=start_str,
            end_date=end_str
        )
        
        if df is None:
            return []
        
        flows = []
        for _, row in df.iterrows():
            flow = {
                'code': code,
                'report_date': row['ann_date'],
                'operating_cash_flow': Decimal(str(row['n_cashflow_act'])) if pd_not_null(row.get('n_cashflow_act')) else None,
                'investing_cash_flow': Decimal(str(row['n_cashflow_inv_act'])) if pd_not_null(row.get('n_cashflow_inv_act')) else None,
                'financing_cash_flow': Decimal(str(row['n_cashflow_fin_act'])) if pd_not_null(row.get('n_cashflow_fin_act')) else None,
            }
            flows.append(flow)
        
        return flows
    
    def get_index_list(self) -> List[Dict[str, Any]]:
        """
        获取指数列表
        
        Returns:
            指数列表
        """
        df = self._call_api('index_basic', market='SW')
        
        if df is None:
            return []
        
        indices = []
        for _, row in df.iterrows():
            index = {
                'code': row['ts_code'],
                'name': row['name'],
                'market': row['market'],
            }
            indices.append(index)
        
        return indices
    
    def get_index_quotes(self, index_code: str) -> List[Dict[str, Any]]:
        """
        获取指数行情
        
        Args:
            index_code: 指数代码
            
        Returns:
            指数行情数据列表
        """
        df = self._call_api('index_daily', ts_code=index_code, limit=30)
        
        if df is None:
            return []
        
        quotes = []
        for _, row in df.iterrows():
            quote = {
                'code': index_code,
                'date': row['trade_date'],
                'open': Decimal(str(row['open'])),
                'high': Decimal(str(row['high'])),
                'low': Decimal(str(row['low'])),
                'close': Decimal(str(row['close'])),
                'volume': int(row['vol']) if pd_not_null(row.get('vol')) else 0,
                'amount': Decimal(str(row['amount'])) if pd_not_null(row.get('amount')) else Decimal('0'),
            }
            quotes.append(quote)
        
        return quotes
    
    def get_industry_list(self) -> List[Dict[str, Any]]:
        """
        获取行业列表
        
        Returns:
            行业列表
        """
        # 使用股票基础信息中的行业数据
        df = self._call_api('stock_basic', exchange='', list_status='L')
        
        if df is None:
            return []
        
        industries = {}
        for _, row in df.iterrows():
            industry = row.get('industry')
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
        df = self._call_api('concept')
        
        if df is None:
            return []
        
        concepts = []
        for _, row in df.iterrows():
            concept = {
                'code': row['code'],
                'name': row['name'],
            }
            concepts.append(concept)
        
        return concepts
    
    def get_capital_flow(self, code: str, trade_date: date) -> Optional[Dict[str, Any]]:
        """
        获取资金流向
        
        Args:
            code: 股票代码
            trade_date: 交易日期
            
        Returns:
            资金流向数据或 None
        """
        ts_code = self.add_exchange_suffix(code)
        date_str = trade_date.strftime('%Y%m%d')
        
        df = self._call_api(
            'moneyflow',
            ts_code=ts_code,
            trade_date=date_str
        )
        
        if df is None or df.empty:
            return None
        
        row = df.iloc[0]
        return {
            'code': code,
            'trade_date': date_str,
            'inflow': Decimal(str(row['net_mf_amount'])) if pd_not_null(row.get('net_mf_amount')) else Decimal('0'),
            'main_inflow': Decimal(str(row['net_mf_amount'])) if pd_not_null(row.get('net_mf_amount')) else Decimal('0'),
        }


def pd_not_null(value):
    """检查 pandas 值是否不为空"""
    if value is None:
        return False
    try:
        import pandas as pd
        return not pd.isna(value)
    except ImportError:
        return True
