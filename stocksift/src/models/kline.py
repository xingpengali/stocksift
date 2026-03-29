# -*- coding: utf-8 -*-
"""
K线数据模型
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, BigInteger, Index

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class Kline(Base):
    """
    K线数据表
    
    存储股票的历史K线数据（日线、周线、月线）
    """
    __tablename__ = 'klines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, comment='股票代码')
    period = Column(String(10), nullable=False, comment='周期(daily/weekly/monthly)')
    trade_date = Column(Date, nullable=False, comment='交易日期')
    
    # 价格数据
    open = Column(Numeric(10, 2), comment='开盘价')
    high = Column(Numeric(10, 2), comment='最高价')
    low = Column(Numeric(10, 2), comment='最低价')
    close = Column(Numeric(10, 2), comment='收盘价')
    
    # 成交量额
    volume = Column(BigInteger, comment='成交量（手）')
    amount = Column(Numeric(16, 2), comment='成交额（元）')
    
    # 涨跌幅
    change = Column(Numeric(10, 2), comment='涨跌额')
    change_pct = Column(Numeric(6, 2), comment='涨跌幅%')
    
    # 复权因子（后复权）
    adj_factor = Column(Numeric(10, 6), default=1.0, comment='复权因子')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_kline_code_period', 'code', 'period'),
        Index('idx_kline_date', 'trade_date'),
        Index('idx_kline_unique', 'code', 'period', 'trade_date', unique=True),
    )
    
    def __repr__(self):
        return f"<Kline(code='{self.code}', date={self.trade_date}, close={self.close})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'period': self.period,
            'trade_date': self.trade_date.strftime('%Y-%m-%d') if self.trade_date else None,
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'volume': self.volume,
            'amount': float(self.amount) if self.amount else None,
            'change': float(self.change) if self.change else None,
            'change_pct': float(self.change_pct) if self.change_pct else None,
            'adj_factor': float(self.adj_factor) if self.adj_factor else 1.0,
        }


class KlineRepository:
    """K线数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_code(
        self,
        code: str,
        period: str = 'daily',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Kline]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            period: 周期
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
        """
        session = self._get_session()
        try:
            query = session.query(Kline).filter(
                Kline.code == code,
                Kline.period == period
            )
            
            if start_date:
                query = query.filter(Kline.trade_date >= start_date)
            if end_date:
                query = query.filter(Kline.trade_date <= end_date)
            
            query = query.order_by(Kline.trade_date.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_latest(self, code: str, period: str = 'daily') -> Optional[Kline]:
        """获取最新K线"""
        session = self._get_session()
        try:
            return session.query(Kline).filter(
                Kline.code == code,
                Kline.period == period
            ).order_by(Kline.trade_date.desc()).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, kline: Kline) -> bool:
        """保存K线"""
        session = self._get_session()
        try:
            existing = session.query(Kline).filter(
                Kline.code == kline.code,
                Kline.period == kline.period,
                Kline.trade_date == kline.trade_date
            ).first()
            
            if existing:
                kline.id = existing.id
                session.merge(kline)
            else:
                session.add(kline)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存K线失败 {kline.code}: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def save_batch(self, klines: List[Kline]) -> int:
        """批量保存K线"""
        if not klines:
            return 0
        
        session = self._get_session()
        count = 0
        
        try:
            for kline in klines:
                existing = session.query(Kline).filter(
                    Kline.code == kline.code,
                    Kline.period == kline.period,
                    Kline.trade_date == kline.trade_date
                ).first()
                
                if existing:
                    kline.id = existing.id
                    session.merge(kline)
                else:
                    session.add(kline)
                count += 1
            
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"批量保存K线失败: {e}")
            return 0
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_code_and_date_range(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = 'daily'
    ) -> List[Kline]:
        """
        根据日期范围获取K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期
            
        Returns:
            K线数据列表
        """
        return self.get_by_code(code, period, start_date, end_date)
    
    def get_date_range(self, code: str, period: str = 'daily') -> tuple:
        """获取K线日期范围"""
        session = self._get_session()
        try:
            min_result = session.query(Kline.trade_date).filter(
                Kline.code == code,
                Kline.period == period
            ).order_by(Kline.trade_date.asc()).first()
            
            max_result = session.query(Kline.trade_date).filter(
                Kline.code == code,
                Kline.period == period
            ).order_by(Kline.trade_date.desc()).first()
            
            min_date = min_result[0] if min_result else None
            max_date = max_result[0] if max_result else None
            
            return (min_date, max_date)
        finally:
            if not self._use_external_session:
                session.close()
