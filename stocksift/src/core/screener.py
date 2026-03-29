# -*- coding: utf-8 -*-
"""
筛选引擎模块

实现多维度股票筛选功能
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
import time

from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session

from models.database import get_db_manager
from models.stock import Stock, StockRepository
from models.quote import Quote, QuoteRepository
from models.valuation import Valuation, ValuationRepository
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FilterCondition:
    """筛选条件"""
    field: str
    operator: str  # >, <, =, >=, <=, between, in, like
    value: Any
    value2: Any = None  # 用于between操作
    logic: str = "AND"  # AND/OR


@dataclass
class FilterGroup:
    """筛选条件组"""
    name: str
    conditions: List[FilterCondition]
    logic: str = "AND"


@dataclass
class ScreenResult:
    """筛选结果"""
    total: int
    page: int
    page_size: int
    data: List[Dict]
    execution_time: float
    sql: str = ""


class ScreenerEngine:
    """
    筛选引擎
    
    支持多维度条件组合筛选
    """
    
    # 支持的筛选字段定义
    AVAILABLE_FIELDS = {
        # 基础字段
        'code': {'type': 'string', 'table': 'stock', 'label': '股票代码'},
        'name': {'type': 'string', 'table': 'stock', 'label': '股票名称'},
        'industry_name': {'type': 'string', 'table': 'stock', 'label': '所属行业'},
        'market_type': {'type': 'string', 'table': 'stock', 'label': '市场类型'},
        
        # 行情字段
        'price': {'type': 'number', 'table': 'quote', 'label': '最新价'},
        'change_pct': {'type': 'number', 'table': 'quote', 'label': '涨跌幅%'},
        'volume': {'type': 'number', 'table': 'quote', 'label': '成交量'},
        'amount': {'type': 'number', 'table': 'quote', 'label': '成交额'},
        'turnover': {'type': 'number', 'table': 'quote', 'label': '换手率%'},
        
        # 估值字段
        'pe_ttm': {'type': 'number', 'table': 'valuation', 'label': 'PE(TTM)'},
        'pb': {'type': 'number', 'table': 'valuation', 'label': 'PB'},
        'ps': {'type': 'number', 'table': 'valuation', 'label': 'PS'},
        'total_mv': {'type': 'number', 'table': 'valuation', 'label': '总市值'},
        'float_mv': {'type': 'number', 'table': 'valuation', 'label': '流通市值'},
        
        # 技术指标字段（需要实时计算或从缓存获取）
        'rsi6': {'type': 'number', 'table': 'indicator', 'label': 'RSI6'},
        'rsi12': {'type': 'number', 'table': 'indicator', 'label': 'RSI12'},
        'rsi24': {'type': 'number', 'table': 'indicator', 'label': 'RSI24'},
        
        # 财务字段
        'roe': {'type': 'number', 'table': 'financial', 'label': 'ROE%'},
        'roa': {'type': 'number', 'table': 'financial', 'label': 'ROA%'},
        'gross_margin': {'type': 'number', 'table': 'financial', 'label': '毛利率%'},
        'net_margin': {'type': 'number', 'table': 'financial', 'label': '净利率%'},
        'revenue_growth': {'type': 'number', 'table': 'financial', 'label': '营收增长率%'},
        'profit_growth': {'type': 'number', 'table': 'financial', 'label': '净利润增长率%'},
        'debt_ratio': {'type': 'number', 'table': 'financial', 'label': '资产负债率%'},
        'current_ratio': {'type': 'number', 'table': 'financial', 'label': '流动比率'},
    }
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化
        
        Args:
            session: 数据库会话，None则自动创建
        """
        self.session = session
        self._use_external_session = session is not None
        self.stock_repo = StockRepository(session)
        self.quote_repo = QuoteRepository(session)
        self.valuation_repo = ValuationRepository(session)
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def screen(self, 
               conditions: List[FilterCondition],
               order_by: Optional[str] = None,
               order_desc: bool = True,
               page: int = 1,
               page_size: int = 50) -> ScreenResult:
        """
        执行筛选
        
        Args:
            conditions: 筛选条件列表
            order_by: 排序字段
            order_desc: 是否降序
            page: 页码
            page_size: 每页数量
            
        Returns:
            筛选结果
        """
        start_time = time.time()
        session = self._get_session()
        
        try:
            # 构建基础查询
            query = self._build_base_query(session)
            
            # 应用筛选条件
            if conditions:
                filter_clause = self._build_filter_clause(conditions)
                if filter_clause is not None:
                    query = query.filter(filter_clause)
            
            # 获取总数
            total = query.count()
            
            # 应用排序
            if order_by and order_by in self.AVAILABLE_FIELDS:
                field_info = self.AVAILABLE_FIELDS[order_by]
                order_column = self._get_order_column(order_by, field_info)
                if order_column is not None:
                    if order_desc:
                        query = query.order_by(desc(order_column))
                    else:
                        query = query.order_by(asc(order_column))
            
            # 应用分页
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 执行查询
            results = query.all()
            
            # 格式化结果
            data = self._format_results(results)
            
            execution_time = time.time() - start_time
            
            return ScreenResult(
                total=total,
                page=page,
                page_size=page_size,
                data=data,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"筛选执行失败: {e}")
            raise
        finally:
            if not self._use_external_session:
                session.close()
    
    def _build_base_query(self, session: Session):
        """构建基础查询"""
        from sqlalchemy import text
        
        # 多表联合查询
        query = session.query(
            Stock.code,
            Stock.name,
            Stock.industry_name.label('industry'),
            Quote.price,
            Quote.change_pct,
            Quote.volume,
            Quote.amount,
            Quote.turnover,
            Valuation.pe_ttm,
            Valuation.pb,
            Valuation.ps_ttm.label('ps'),
            Valuation.total_mv,
            Valuation.float_mv
        ).outerjoin(
            Quote, Stock.code == Quote.code
        ).outerjoin(
            Valuation, Stock.code == Valuation.code
        )
        
        return query
    
    def _build_filter_clause(self, conditions: List[FilterCondition]):
        """构建筛选条件"""
        clauses = []
        
        for condition in conditions:
            clause = self._build_single_condition(condition)
            if clause is not None:
                clauses.append(clause)
        
        if not clauses:
            return None
        
        # 组合条件
        if len(clauses) == 1:
            return clauses[0]
        
        # 默认使用AND连接
        return and_(*clauses)
    
    def _build_single_condition(self, condition: FilterCondition):
        """构建单个条件"""
        field = condition.field
        operator = condition.operator
        value = condition.value
        
        # 获取字段映射
        column = self._get_column(field)
        if column is None:
            logger.warning(f"未知字段: {field}")
            return None
        
        # 根据操作符构建条件
        if operator == '>':
            return column > value
        elif operator == '<':
            return column < value
        elif operator == '=':
            return column == value
        elif operator == '>=':
            return column >= value
        elif operator == '<=':
            return column <= value
        elif operator == 'between':
            return column.between(value, condition.value2)
        elif operator == 'in':
            return column.in_(value if isinstance(value, list) else [value])
        elif operator == 'like':
            return column.like(f'%{value}%')
        else:
            logger.warning(f"未知操作符: {operator}")
            return None
    
    def _get_column(self, field: str):
        """获取字段对应的列"""
        if field not in self.AVAILABLE_FIELDS:
            return None
        
        field_info = self.AVAILABLE_FIELDS[field]
        table = field_info['table']
        
        if table == 'stock':
            return getattr(Stock, field, None)
        elif table == 'quote':
            return getattr(Quote, field, None)
        elif table == 'valuation':
            return getattr(Valuation, field, None)
        
        return None
    
    def _get_order_column(self, field: str, field_info: Dict):
        """获取排序列"""
        return self._get_column(field)
    
    def _format_results(self, results) -> List[Dict]:
        """格式化查询结果"""
        data = []
        for row in results:
            item = {
                'code': row.code,
                'name': row.name,
                'industry': row.industry,
                'price': float(row.price) if row.price else None,
                'change_pct': float(row.change_pct) if row.change_pct else None,
                'volume': int(row.volume) if row.volume else None,
                'amount': float(row.amount) if row.amount else None,
                'turnover': float(row.turnover) if row.turnover else None,
                'pe_ttm': float(row.pe_ttm) if row.pe_ttm else None,
                'pb': float(row.pb) if row.pb else None,
                'ps': float(row.ps) if row.ps else None,
                'total_mv': float(row.total_mv) if row.total_mv else None,
                'float_mv': float(row.float_mv) if row.float_mv else None,
            }
            data.append(item)
        return data
    
    def get_available_fields(self) -> List[Dict]:
        """
        获取可用筛选字段
        
        Returns:
            字段列表
        """
        fields = []
        for name, info in self.AVAILABLE_FIELDS.items():
            fields.append({
                'name': name,
                'label': info['label'],
                'type': info['type'],
                'table': info['table']
            })
        return fields
    
    def quick_screen(self, 
                     min_pe: Optional[float] = None,
                     max_pe: Optional[float] = None,
                     min_pb: Optional[float] = None,
                     max_pb: Optional[float] = None,
                     min_roe: Optional[float] = None,
                     industries: Optional[List[str]] = None,
                     limit: int = 100) -> ScreenResult:
        """
        快速筛选
        
        常用筛选条件的快捷方式
        
        Args:
            min_pe: 最小PE
            max_pe: 最大PE
            min_pb: 最小PB
            max_pb: 最大PB
            min_roe: 最小ROE
            industries: 行业列表
            limit: 结果限制
            
        Returns:
            筛选结果
        """
        conditions = []
        
        if min_pe is not None:
            conditions.append(FilterCondition('pe_ttm', '>=', min_pe))
        if max_pe is not None:
            conditions.append(FilterCondition('pe_ttm', '<=', max_pe))
        if min_pb is not None:
            conditions.append(FilterCondition('pb', '>=', min_pb))
        if max_pb is not None:
            conditions.append(FilterCondition('pb', '<=', max_pb))
        if industries:
            conditions.append(FilterCondition('industry', 'in', industries))
        
        return self.screen(conditions, page=1, page_size=limit)
    
    def value_screen(self, limit: int = 50) -> ScreenResult:
        """
        价值投资筛选
        
        经典价值投资条件：低PE、低PB、高ROE
        
        Args:
            limit: 结果限制
            
        Returns:
            筛选结果
        """
        conditions = [
            FilterCondition('pe_ttm', 'between', 5, 25),
            FilterCondition('pb', '<=', 3),
            FilterCondition('roe', '>=', 10),
            FilterCondition('debt_ratio', '<=', 60),
        ]
        
        return self.screen(conditions, order_by='roe', order_desc=True, 
                          page=1, page_size=limit)
    
    def growth_screen(self, limit: int = 50) -> ScreenResult:
        """
        成长股筛选
        
        成长股条件：高营收增长、高利润增长
        
        Args:
            limit: 结果限制
            
        Returns:
            筛选结果
        """
        conditions = [
            FilterCondition('revenue_growth', '>=', 20),
            FilterCondition('profit_growth', '>=', 20),
            FilterCondition('pe_ttm', '<=', 50),
        ]
        
        return self.screen(conditions, order_by='profit_growth', order_desc=True,
                          page=1, page_size=limit)
    
    def dividend_screen(self, limit: int = 50) -> ScreenResult:
        """
        高分红筛选
        
        分红股条件：低PE、稳定盈利
        
        Args:
            limit: 结果限制
            
        Returns:
            筛选结果
        """
        conditions = [
            FilterCondition('pe_ttm', 'between', 5, 20),
            FilterCondition('pb', '<=', 2),
            FilterCondition('roe', '>=', 8),
        ]
        
        return self.screen(conditions, order_by='pe_ttm', order_desc=False,
                          page=1, page_size=limit)
