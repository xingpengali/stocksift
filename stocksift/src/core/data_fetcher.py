# -*- coding: utf-8 -*-
"""
数据获取协调器

统一数据获取接口，协调数据源和数据存储
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from datasource.data_source_manager import data_source_manager
from models.database import get_db_manager
from models.stock import Stock, StockRepository
from models.quote import Quote, QuoteRepository
from models.kline import Kline, KlineRepository
from models.financial import Financial, FinancialRepository
from models.valuation import Valuation, ValuationRepository
from utils.logger import get_logger
from utils.cache import cache_manager

logger = get_logger(__name__)


class DataFetcher:
    """
    数据获取协调器
    
    统一的数据获取接口，负责：
    - 优先从本地数据库获取
    - 本地数据缺失时从外部数据源获取并缓存
    - 数据更新和同步
    """
    
    def __init__(self):
        """初始化"""
        self.source_manager = data_source_manager
        
        # 初始化数据访问对象
        self.stock_repo = StockRepository()
        self.quote_repo = QuoteRepository()
        self.kline_repo = KlineRepository()
        self.financial_repo = FinancialRepository()
        self.valuation_repo = ValuationRepository()
        
        # 缓存
        self._cache = cache_manager.get_cache('data_fetcher')
    
    def get_stock_list(self, force_update: bool = False) -> List[Dict]:
        """
        获取股票列表
        
        Args:
            force_update: 强制从外部更新
            
        Returns:
            股票列表
        """
        cache_key = 'stock_list'
        
        # 检查缓存
        if not force_update:
            cached = self._cache.get(cache_key)
            if cached:
                return cached
            
            # 检查数据库
            stocks = self.stock_repo.get_all()
            if stocks:
                result = [s.to_dict() for s in stocks]
                self._cache.set(cache_key, result, 3600)  # 缓存1小时
                return result
        
        # 从外部数据源获取
        try:
            self.source_manager.connect()
            external_data = self.source_manager.get_stock_list()
            
            # 保存到数据库
            for item in external_data:
                stock = Stock(
                    code=item.get('code'),
                    name=item.get('name'),
                    industry_name=item.get('industry'),
                    market_type=item.get('market_type'),
                    exchange=item.get('exchange'),
                    list_date=item.get('list_date')
                )
                self.stock_repo.save(stock)
            
            self._cache.set(cache_key, external_data, 3600)
            logger.info(f"从外部数据源获取股票列表: {len(external_data)} 只")
            return external_data
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_stock_basic(self, code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息字典
        """
        # 优先从数据库获取
        stock = self.stock_repo.get_by_code(code)
        if stock:
            return stock.to_dict()
        
        # 从外部获取
        try:
            self.source_manager.connect()
            adapter = self.source_manager.get_primary_adapter()
            if adapter:
                data = adapter.get_stock_basic(code)
                if data:
                    # 保存到数据库
                    stock = Stock(
                        code=data.get('code'),
                        name=data.get('name'),
                        industry=data.get('industry'),
                        market_type=data.get('market_type'),
                        exchange=data.get('exchange')
                    )
                    self.stock_repo.save(stock)
                    return data
        except Exception as e:
            logger.error(f"获取股票基本信息失败 [{code}]: {e}")
        
        return None
    
    def get_quotes(self, codes: List[str], 
                   force_update: bool = False) -> List[Dict]:
        """
        获取行情数据
        
        Args:
            codes: 股票代码列表
            force_update: 强制更新
            
        Returns:
            行情数据列表
        """
        results = []
        need_update = []
        
        for code in codes:
            if not force_update:
                # 从数据库获取最新行情
                quote = self.quote_repo.get_latest(code)
                if quote:
                    results.append(quote.to_dict())
                    continue
            
            need_update.append(code)
        
        # 从外部获取缺失的数据
        if need_update:
            try:
                self.source_manager.connect()
                external_data = self.source_manager.get_daily_quotes(need_update)
                
                for item in external_data:
                    quote = Quote(
                        code=item.get('code'),
                        trade_date=item.get('trade_date', date.today()),
                        open=item.get('open'),
                        high=item.get('high'),
                        low=item.get('low'),
                        close=item.get('close'),
                        volume=item.get('volume'),
                        amount=item.get('amount'),
                        change=item.get('change'),
                        change_pct=item.get('change_pct'),
                        turnover=item.get('turnover')
                    )
                    self.quote_repo.save(quote)
                    results.append(item)
                    
            except Exception as e:
                logger.error(f"获取行情数据失败: {e}")
        
        return results
    
    def get_kline(self, code: str, period: str = 'daily',
                  count: int = 100, start_date: date = None,
                  end_date: date = None) -> List[Dict]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            period: 周期 (daily/weekly/monthly)
            count: 数量
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            K线数据列表
        """
        # 默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=count * 2)
        
        # 从数据库获取
        klines = self.kline_repo.get_by_code_and_date_range(
            code, start_date, end_date, period
        )
        
        if len(klines) >= count * 0.8:  # 数据足够
            return [k.to_dict() for k in klines[-count:]]
        
        # 从外部获取
        try:
            self.source_manager.connect()
            external_data = self.source_manager.get_kline_data(
                code, start_date, end_date, period
            )
            
            # 保存到数据库
            for item in external_data:
                kline = Kline(
                    code=item.get('code'),
                    trade_date=item.get('trade_date'),
                    period=period,
                    open=item.get('open'),
                    high=item.get('high'),
                    low=item.get('low'),
                    close=item.get('close'),
                    volume=item.get('volume'),
                    amount=item.get('amount')
                )
                self.kline_repo.save(kline)
            
            return external_data[-count:]
            
        except Exception as e:
            logger.error(f"获取K线数据失败 [{code}]: {e}")
            return [k.to_dict() for k in klines]
    
    def get_financial(self, code: str, report_type: str = 'annual') -> Optional[Dict]:
        """
        获取财务数据
        
        Args:
            code: 股票代码
            report_type: 报告类型
            
        Returns:
            财务数据字典
        """
        # 从数据库获取最新
        financial = self.financial_repo.get_latest(code, report_type)
        if financial:
            return financial.to_dict()
        
        # 从外部获取
        try:
            self.source_manager.connect()
            adapter = self.source_manager.get_primary_adapter()
            if adapter:
                data = adapter.get_financial_data(code, report_type)
                if data:
                    # 保存到数据库
                    financial = Financial(
                        code=data.get('code'),
                        report_date=data.get('report_date'),
                        report_type=report_type,
                        total_revenue=data.get('total_revenue'),
                        net_profit=data.get('net_profit'),
                        gross_profit=data.get('gross_profit'),
                        total_assets=data.get('total_assets'),
                        total_equity=data.get('total_equity'),
                        total_liabilities=data.get('total_liabilities'),
                        roe=data.get('roe'),
                        eps=data.get('eps')
                    )
                    self.financial_repo.save(financial)
                    return data
        except Exception as e:
            logger.error(f"获取财务数据失败 [{code}]: {e}")
        
        return None
    
    def get_financial_history(self, code: str, years: int = 5) -> List[Dict]:
        """
        获取历史财务数据
        
        Args:
            code: 股票代码
            years: 年数
            
        Returns:
            财务数据列表
        """
        financials = self.financial_repo.get_by_code(code, limit=years * 4)
        return [f.to_dict() for f in financials]
    
    def update_stock_list(self):
        """更新股票列表"""
        logger.info("开始更新股票列表...")
        stocks = self.get_stock_list(force_update=True)
        logger.info(f"股票列表更新完成: {len(stocks)} 只")
    
    def update_quotes(self, codes: List[str] = None):
        """
        更新行情数据
        
        Args:
            codes: 股票代码列表，None则更新全部
        """
        if codes is None:
            # 获取所有股票代码
            stocks = self.stock_repo.get_all()
            codes = [s.code for s in stocks]
        
        logger.info(f"开始更新 {len(codes)} 只股票的行情数据...")
        
        # 分批获取
        batch_size = 100
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i+batch_size]
            self.get_quotes(batch, force_update=True)
            logger.info(f"已更新 {min(i+batch_size, len(codes))}/{len(codes)}")
        
        logger.info("行情数据更新完成")
    
    def update_kline(self, code: str, period: str = 'daily'):
        """
        更新K线数据
        
        Args:
            code: 股票代码
            period: 周期
        """
        logger.info(f"开始更新 [{code}] {period} K线数据...")
        
        # 获取最新日期
        latest = self.kline_repo.get_latest(code, period)
        if latest:
            start_date = latest.trade_date + timedelta(days=1)
        else:
            start_date = date.today() - timedelta(days=365 * 3)  # 3年
        
        end_date = date.today()
        
        if start_date >= end_date:
            logger.info("K线数据已是最新")
            return
        
        try:
            self.source_manager.connect()
            external_data = self.source_manager.get_kline_data(
                code, start_date, end_date, period
            )
            
            for item in external_data:
                kline = Kline(
                    code=item.get('code'),
                    trade_date=item.get('trade_date'),
                    period=period,
                    open=item.get('open'),
                    high=item.get('high'),
                    low=item.get('low'),
                    close=item.get('close'),
                    volume=item.get('volume'),
                    amount=item.get('amount')
                )
                self.kline_repo.save(kline)
            
            logger.info(f"K线数据更新完成: {len(external_data)} 条")
            
        except Exception as e:
            logger.error(f"更新K线数据失败: {e}")
    
    def update_all_data(self):
        """更新所有数据"""
        logger.info("开始全量数据更新...")
        
        # 更新股票列表
        self.update_stock_list()
        
        # 更新行情
        self.update_quotes()
        
        logger.info("全量数据更新完成")
    
    def get_valuation(self, code: str) -> Optional[Dict]:
        """
        获取估值数据
        
        Args:
            code: 股票代码
            
        Returns:
            估值数据
        """
        valuation = self.valuation_repo.get_latest(code)
        if valuation:
            return valuation.to_dict()
        return None
    
    def get_batch_quotes(self, codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取行情（返回字典格式）
        
        Args:
            codes: 股票代码列表
            
        Returns:
            {code: quote_data}
        """
        quotes = self.get_quotes(codes)
        return {q['code']: q for q in quotes}
