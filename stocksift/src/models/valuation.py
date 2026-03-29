# -*- coding: utf-8 -*-
"""
估值数据模型

存储股票的历史估值数据（PE、PB等）
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Index

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class Valuation(Base):
    """
    估值数据表
    
    存储股票的历史估值指标
    """
    __tablename__ = 'valuations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, comment='股票代码')
    trade_date = Column(Date, nullable=False, comment='交易日期')
    
    # 市盈率
    pe_ttm = Column(Numeric(10, 2), comment='市盈率TTM')
    pe_lyr = Column(Numeric(10, 2), comment='市盈率LYR')
    pe_forward = Column(Numeric(10, 2), comment='预测市盈率')
    
    # 市净率
    pb = Column(Numeric(10, 2), comment='市净率')
    pb_mrq = Column(Numeric(10, 2), comment='市净率MRQ')
    
    # 市销率
    ps_ttm = Column(Numeric(10, 2), comment='市销率TTM')
    
    # 市现率
    pcf_ttm = Column(Numeric(10, 2), comment='市现率TTM')
    
    # 股息率
    dividend_yield = Column(Numeric(6, 2), comment='股息率%')
    
    # 市值
    total_mv = Column(Numeric(16, 2), comment='总市值')
    float_mv = Column(Numeric(16, 2), comment='流通市值')
    
    # 估值分位（历史百分位）
    pe_ttm_percentile = Column(Numeric(5, 2), comment='PE分位%')
    pb_percentile = Column(Numeric(5, 2), comment='PB分位%')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_valuation_code', 'code'),
        Index('idx_valuation_date', 'trade_date'),
        Index('idx_valuation_unique', 'code', 'trade_date', unique=True),
    )
    
    def __repr__(self):
        return f"<Valuation(code='{self.code}', date={self.trade_date}, pe={self.pe_ttm})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'trade_date': self.trade_date.strftime('%Y-%m-%d') if self.trade_date else None,
            'pe_ttm': float(self.pe_ttm) if self.pe_ttm else None,
            'pe_lyr': float(self.pe_lyr) if self.pe_lyr else None,
            'pe_forward': float(self.pe_forward) if self.pe_forward else None,
            'pb': float(self.pb) if self.pb else None,
            'pb_mrq': float(self.pb_mrq) if self.pb_mrq else None,
            'ps_ttm': float(self.ps_ttm) if self.ps_ttm else None,
            'pcf_ttm': float(self.pcf_ttm) if self.pcf_ttm else None,
            'dividend_yield': float(self.dividend_yield) if self.dividend_yield else None,
            'total_mv': float(self.total_mv) if self.total_mv else None,
            'float_mv': float(self.float_mv) if self.float_mv else None,
            'pe_ttm_percentile': float(self.pe_ttm_percentile) if self.pe_ttm_percentile else None,
            'pb_percentile': float(self.pb_percentile) if self.pb_percentile else None,
        }


class ValuationRepository:
    """估值数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_code(self, code: str, trade_date: Optional[date] = None) -> Optional[Valuation]:
        """
        获取估值数据
        
        Args:
            code: 股票代码
            trade_date: 交易日期，None表示最新
            
        Returns:
            Valuation对象或None
        """
        session = self._get_session()
        try:
            query = session.query(Valuation).filter(Valuation.code == code)
            
            if trade_date:
                query = query.filter(Valuation.trade_date == trade_date)
            else:
                query = query.order_by(Valuation.trade_date.desc())
            
            return query.first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_history(
        self,
        code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Valuation]:
        """
        获取历史估值数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            
        Returns:
            Valuation对象列表
        """
        session = self._get_session()
        try:
            query = session.query(Valuation).filter(Valuation.code == code)
            
            if start_date:
                query = query.filter(Valuation.trade_date >= start_date)
            if end_date:
                query = query.filter(Valuation.trade_date <= end_date)
            
            query = query.order_by(Valuation.trade_date.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_pe_range(
        self,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = None,
        trade_date: Optional[date] = None
    ) -> List[Valuation]:
        """
        根据PE范围查询
        
        Args:
            min_pe: 最小PE
            max_pe: 最大PE
            trade_date: 交易日期
            
        Returns:
            Valuation对象列表
        """
        session = self._get_session()
        try:
            query = session.query(Valuation)
            
            if trade_date:
                query = query.filter(Valuation.trade_date == trade_date)
            else:
                # 使用最新日期
                latest_date = session.query(Valuation.trade_date).order_by(
                    Valuation.trade_date.desc()
                ).first()
                if latest_date:
                    query = query.filter(Valuation.trade_date == latest_date[0])
            
            if min_pe is not None:
                query = query.filter(Valuation.pe_ttm >= min_pe)
            if max_pe is not None:
                query = query.filter(Valuation.pe_ttm <= max_pe)
            
            return query.all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, valuation: Valuation) -> bool:
        """
        保存估值数据
        
        Args:
            valuation: Valuation对象
            
        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            existing = session.query(Valuation).filter(
                Valuation.code == valuation.code,
                Valuation.trade_date == valuation.trade_date
            ).first()
            
            if existing:
                valuation.id = existing.id
                session.merge(valuation)
            else:
                session.add(valuation)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存估值数据失败 {valuation.code}: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def save_batch(self, valuations: List[Valuation]) -> int:
        """
        批量保存估值数据
        
        Args:
            valuations: Valuation对象列表
            
        Returns:
            成功保存的数量
        """
        if not valuations:
            return 0
        
        session = self._get_session()
        count = 0
        
        try:
            for valuation in valuations:
                existing = session.query(Valuation).filter(
                    Valuation.code == valuation.code,
                    Valuation.trade_date == valuation.trade_date
                ).first()
                
                if existing:
                    valuation.id = existing.id
                    session.merge(valuation)
                else:
                    session.add(valuation)
                count += 1
            
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"批量保存估值数据失败: {e}")
            return 0
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_undervalued_stocks(
        self,
        trade_date: Optional[date] = None,
        pe_threshold: float = 15.0,
        pb_threshold: float = 1.5,
        limit: int = 50
    ) -> List[Valuation]:
        """
        获取低估值股票
        
        Args:
            trade_date: 交易日期
            pe_threshold: PE阈值
            pb_threshold: PB阈值
            limit: 返回数量
            
        Returns:
            Valuation对象列表
        """
        session = self._get_session()
        try:
            query = session.query(Valuation)
            
            if trade_date:
                query = query.filter(Valuation.trade_date == trade_date)
            else:
                latest_date = session.query(Valuation.trade_date).order_by(
                    Valuation.trade_date.desc()
                ).first()
                if latest_date:
                    query = query.filter(Valuation.trade_date == latest_date[0])
            
            query = query.filter(
                Valuation.pe_ttm <= pe_threshold,
                Valuation.pb <= pb_threshold,
                Valuation.pe_ttm > 0  # 排除亏损股
            ).order_by(Valuation.pe_ttm.asc())
            
            return query.limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
