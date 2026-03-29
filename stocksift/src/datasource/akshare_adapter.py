# -*- coding: utf-8 -*-
"""
AKShare 数据源适配器

AKShare 是一个免费的股票数据接口，数据来源于东方财富、新浪财经等
官网: https://www.akshare.xyz
"""
import time
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

from .base_adapter import (
    BaseDataAdapter, DataSourceError, ConnectionError,
    DataNotFoundError, RateLimitError
)
from config.constants import (
    EXCHANGE_SSE, EXCHANGE_SZSE, EXCHANGE_BSE,
    MARKET_MAIN, MARKET_GEM, MARKET_STAR, MARKET_BJ,
    PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY
)
from utils.logger import get_logger

logger = get_logger(__name__)


class AkshareAdapter(BaseDataAdapter):
    """
    AKShare 数据源适配器
    
    使用 AKShare 获取 A 股数据，数据免费且无需 Token
    """
    
    # 交易所映射
    EXCHANGE_MAP = {
        'SH': EXCHANGE_SSE,
        'SZ': EXCHANGE_SZSE,
        'BJ': EXCHANGE_BSE,
    }
    
    # 市场类型映射
    MARKET_MAP = {
        '主板': MARKET_MAIN,
        '创业板': MARKET_GEM,
        '科创板': MARKET_STAR,
        '北交所': MARKET_BJ,
    }
    
    def __init__(self, name: str = "akshare", config: Dict[str, Any] = None):
        """
        初始化 AKShare 适配器
        
        Args:
            name: 适配器名称
            config: 配置字典
        """
        super().__init__(name, config or {})
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
        连接 AKShare 数据源
        
        Returns:
            是否连接成功
        """
        if not AKSHARE_AVAILABLE:
            raise ConnectionError("akshare 模块未安装，请执行: pip install akshare")
        
        try:
            # AKShare 无需认证，测试获取股票列表
            self._rate_limit()
            ak.stock_zh_a_spot_em()
            
            self._connected = True
            self._logger.info("AKShare 连接成功")
            return True
            
        except Exception as e:
            raise ConnectionError(f"AKShare 连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开 AKShare 连接"""
        self._connected = False
        self._logger.info("AKShare 连接已断开")
    
    def get_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取所有股票列表
        
        Returns:
            股票列表
        """
        self._check_connection()
        self._rate_limit()
        
        try:
            # 使用东方财富接口获取A股列表
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                code = str(row.get('代码', ''))
                if not code:
                    continue
                
                # 判断交易所
                exchange = self._get_exchange(code)
                market_type = self._get_market_type(code)
                
                stock = {
                    'code': code,
                    'name': row.get('名称', ''),
                    'exchange': exchange,
                    'market_type': market_type,
                    'industry_code': '',
                    'industry_name': '',
                    'list_date': '',
                }
                stocks.append(stock)
            
            return stocks
            
        except Exception as e:
            self.handle_error(e, "获取股票列表")
    
    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票基本信息字典或 None
        """
        self._check_connection()
        self._rate_limit()
        
        try:
            # 获取实时行情作为基本信息
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return None
            
            # 查找指定股票
            stock_row = df[df['代码'] == code]
            if stock_row.empty:
                return None
            
            row = stock_row.iloc[0]
            return {
                'code': code,
                'name': row.get('名称', ''),
                'exchange': self._get_exchange(code),
                'market_type': self._get_market_type(code),
                'industry': '',
                'list_date': '',
            }
            
        except Exception as e:
            self.handle_error(e, f"获取股票 {code} 基本信息")
    
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
        
        self._check_connection()
        self._rate_limit()
        
        try:
            # 获取全部A股实时行情
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return []
            
            # 过滤指定股票
            df = df[df['代码'].isin(codes)]
            
            quotes = []
            today = datetime.now().strftime('%Y%m%d')
            
            for _, row in df.iterrows():
                quote = {
                    'code': str(row.get('代码', '')),
                    'date': today,
                    'open': self._to_decimal(row.get('今开')),
                    'high': self._to_decimal(row.get('最高')),
                    'low': self._to_decimal(row.get('最低')),
                    'close': self._to_decimal(row.get('最新价')),
                    'volume': int(row.get('成交量', 0)) if pd_not_null(row.get('成交量')) else 0,
                    'amount': self._to_decimal(row.get('成交额')),
                }
                quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            self.handle_error(e, "获取日线行情")
    
    def get_realtime_quotes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            codes: 股票代码列表
            
        Returns:
            实时行情数据列表
        """
        # AKShare 的 spot 接口就是实时行情
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
        self._rate_limit()
        
        try:
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')
            
            # 根据周期选择接口
            if period == PERIOD_DAILY:
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_str,
                    end_date=end_str,
                    adjust=""
                )
            elif period == PERIOD_WEEKLY:
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="weekly",
                    start_date=start_str,
                    end_date=end_str,
                    adjust=""
                )
            elif period == PERIOD_MONTHLY:
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="monthly",
                    start_date=start_str,
                    end_date=end_str,
                    adjust=""
                )
            else:
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_str,
                    end_date=end_str,
                    adjust=""
                )
            
            if df is None or df.empty:
                return []
            
            klines = []
            for _, row in df.iterrows():
                kline = {
                    'code': code,
                    'date': str(row.get('日期', '')),
                    'open': self._to_decimal(row.get('开盘')),
                    'high': self._to_decimal(row.get('最高')),
                    'low': self._to_decimal(row.get('最低')),
                    'close': self._to_decimal(row.get('收盘')),
                    'volume': int(row.get('成交量', 0)) if pd_not_null(row.get('成交量')) else 0,
                    'amount': self._to_decimal(row.get('成交额')),
                }
                klines.append(kline)
            
            return klines
            
        except Exception as e:
            self.handle_error(e, f"获取 {code} K线数据")
    
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
        self._rate_limit()
        
        try:
            # 获取主要财务指标
            df = ak.stock_financial_analysis_indicator(symbol=code)
            
            if df is None or df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'code': code,
                'report_date': str(row.get('报告期', '')),
                'report_type': report_type,
                'eps': self._to_decimal(row.get('每股收益')),
                'roe': self._to_decimal(row.get('净资产收益率')),
                'roa': self._to_decimal(row.get('总资产收益率')),
                'gross_margin': self._to_decimal(row.get('销售毛利率')),
                'net_margin': self._to_decimal(row.get('销售净利率')),
                'debt_ratio': self._to_decimal(row.get('资产负债率')),
                'revenue_growth': self._to_decimal(row.get('营业收入增长率')),
                'profit_growth': self._to_decimal(row.get('净利润增长率')),
            }
            
        except Exception as e:
            self._logger.warning(f"获取 {code} 财务数据失败: {e}")
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
        # AKShare 暂不提供完整的利润表历史数据
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
        
        Returns:
            资产负债表数据列表
        """
        # AKShare 暂不提供完整的资产负债表历史数据
        return []
    
    def get_cash_flow(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取现金流量表
        
        Returns:
            现金流量表数据列表
        """
        # AKShare 暂不提供完整的现金流量表历史数据
        return []
    
    def get_index_list(self) -> List[Dict[str, Any]]:
        """
        获取指数列表
        
        Returns:
            指数列表
        """
        # 返回常见指数
        return [
            {'code': '000001', 'name': '上证指数'},
            {'code': '399001', 'name': '深证成指'},
            {'code': '399006', 'name': '创业板指'},
            {'code': '000016', 'name': '上证50'},
            {'code': '000300', 'name': '沪深300'},
            {'code': '000905', 'name': '中证500'},
            {'code': '000688', 'name': '科创50'},
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
        self._rate_limit()
        
        try:
            # 使用东方财富指数行情接口
            df = ak.index_zh_a_hist(symbol=index_code, period="daily")
            
            if df is None or df.empty:
                return []
            
            quotes = []
            for _, row in df.iterrows():
                quote = {
                    'code': index_code,
                    'date': str(row.get('日期', '')),
                    'open': self._to_decimal(row.get('开盘')),
                    'high': self._to_decimal(row.get('最高')),
                    'low': self._to_decimal(row.get('最低')),
                    'close': self._to_decimal(row.get('收盘')),
                    'volume': int(row.get('成交量', 0)) if pd_not_null(row.get('成交量')) else 0,
                    'amount': self._to_decimal(row.get('成交额')),
                }
                quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            self._logger.warning(f"获取指数 {index_code} 行情失败: {e}")
            return []
    
    def get_industry_list(self) -> List[Dict[str, Any]]:
        """
        获取行业列表
        
        Returns:
            行业列表
        """
        self._check_connection()
        self._rate_limit()
        
        try:
            # 获取行业板块
            df = ak.stock_board_industry_name_em()
            
            if df is None or df.empty:
                return []
            
            industries = []
            for _, row in df.iterrows():
                industry = {
                    'code': str(row.get('板块代码', '')),
                    'name': row.get('板块名称', ''),
                }
                industries.append(industry)
            
            return industries
            
        except Exception as e:
            self._logger.warning(f"获取行业列表失败: {e}")
            return []
    
    def get_concept_list(self) -> List[Dict[str, Any]]:
        """
        获取概念板块列表
        
        Returns:
            概念板块列表
        """
        self._check_connection()
        self._rate_limit()
        
        try:
            # 获取概念板块
            df = ak.stock_board_concept_name_em()
            
            if df is None or df.empty:
                return []
            
            concepts = []
            for _, row in df.iterrows():
                concept = {
                    'code': str(row.get('板块代码', '')),
                    'name': row.get('板块名称', ''),
                }
                concepts.append(concept)
            
            return concepts
            
        except Exception as e:
            self._logger.warning(f"获取概念列表失败: {e}")
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
        self._check_connection()
        self._rate_limit()
        
        try:
            # 获取个股资金流向
            df = ak.stock_individual_fund_flow(symbol=code)
            
            if df is None or df.empty:
                return None
            
            row = df.iloc[0]
            return {
                'code': code,
                'trade_date': str(row.get('日期', '')),
                'inflow': self._to_decimal(row.get('净流入')),
                'main_inflow': self._to_decimal(row.get('主力净流入')),
            }
            
        except Exception as e:
            self._logger.warning(f"获取 {code} 资金流向失败: {e}")
            return None
    
    def get_sector_spot(self) -> List[Dict[str, Any]]:
        """
        获取板块实时行情（AKShare特有）
        
        Returns:
            板块行情列表
        """
        self._check_connection()
        self._rate_limit()
        
        try:
            df = ak.stock_board_industry_name_em()
            
            if df is None or df.empty:
                return []
            
            sectors = []
            for _, row in df.iterrows():
                sector = {
                    'code': str(row.get('板块代码', '')),
                    'name': row.get('板块名称', ''),
                    'change_pct': self._to_decimal(row.get('涨跌幅')),
                    'volume': self._to_decimal(row.get('总成交量')),
                    'amount': self._to_decimal(row.get('总成交额')),
                }
                sectors.append(sector)
            
            return sectors
            
        except Exception as e:
            self._logger.warning(f"获取板块行情失败: {e}")
            return []
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览数据（AKShare特有）
        
        Returns:
            市场概览数据
        """
        self._check_connection()
        
        try:
            # 获取大盘指数
            indices = {}
            index_codes = {
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指',
                'sh000688': '科创50',
            }
            
            for code, name in index_codes.items():
                try:
                    self._rate_limit()
                    df = ak.index_zh_a_hist(symbol=code[-6:], period="daily", limit=1)
                    if df is not None and not df.empty:
                        row = df.iloc[-1]
                        indices[name] = {
                            'value': self._to_decimal(row.get('收盘')),
                            'change': self._to_decimal(row.get('涨跌幅')),
                        }
                except:
                    pass
            
            # 获取涨跌统计
            self._rate_limit()
            spot_df = ak.stock_zh_a_spot_em()
            
            up_count = len(spot_df[spot_df['涨跌幅'] > 0]) if '涨跌幅' in spot_df.columns else 0
            down_count = len(spot_df[spot_df['涨跌幅'] < 0]) if '涨跌幅' in spot_df.columns else 0
            flat_count = len(spot_df[spot_df['涨跌幅'] == 0]) if '涨跌幅' in spot_df.columns else 0
            
            return {
                'indices': indices,
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
            }
            
        except Exception as e:
            self._logger.warning(f"获取市场概览失败: {e}")
            return {}
    
    def _get_exchange(self, code: str) -> str:
        """根据代码判断交易所"""
        if code.startswith('6') or code.startswith('5'):
            return EXCHANGE_SSE
        elif code.startswith('0') or code.startswith('3') or code.startswith('1'):
            return EXCHANGE_SZSE
        elif code.startswith('8') or code.startswith('4'):
            return EXCHANGE_BSE
        else:
            return EXCHANGE_SSE
    
    def _get_market_type(self, code: str) -> str:
        """根据代码判断市场类型"""
        if code.startswith('60') or code.startswith('00'):
            return MARKET_MAIN
        elif code.startswith('68'):
            return MARKET_STAR
        elif code.startswith('30'):
            return MARKET_GEM
        elif code.startswith('8') or code.startswith('4'):
            return MARKET_BJ
        else:
            return MARKET_MAIN
    
    def _to_decimal(self, value) -> Optional[Decimal]:
        """转换为 Decimal"""
        if value is None or pd_isna(value):
            return None
        try:
            return Decimal(str(value))
        except:
            return None


def pd_not_null(value):
    """检查 pandas 值是否不为空"""
    if value is None:
        return False
    try:
        import pandas as pd
        return not pd.isna(value)
    except ImportError:
        return True


def pd_isna(value):
    """检查 pandas 值是否为空"""
    if value is None:
        return True
    try:
        import pandas as pd
        return pd.isna(value)
    except ImportError:
        return False
