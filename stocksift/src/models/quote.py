# -*- coding: utf-8 -*-
"""
实时行情数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Numeric, DateTime, BigInteger, Index

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class Quote(Base):
    """
    实时行情数据表
    
    存储股票的实时行情数据，包括价格、成交量、涨跌幅等
    """
    __tablename__ = 'quotes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment='股票代码')
    
    # 价格信息
    price = Column(Numeric(10, 2), comment='最新价')
    pre_close = Column(Numeric(10, 2), comment='昨收')
    open = Column(Numeric(10, 2), comment='开盘价')
    high = Column(Numeric(10, 2), comment='最高价')
    low = Column(Numeric(10, 2), comment='最低价')
    
    # 涨跌幅
    change = Column(Numeric(10, 2), comment='涨跌额')
    change_pct = Column(Numeric(6, 2), comment='涨跌幅%')
    
    # 成交量额
    volume = Column(BigInteger, comment='成交量（手）')
    amount = Column(Numeric(16, 2), comment='成交额（元）')
    
    # 盘口数据（买一卖一）
    bid1_price = Column(Numeric(10, 2), comment='买一价')
    bid1_volume = Column(BigInteger, comment='买一手数')
    ask1_price = Column(Numeric(10, 2), comment='卖一价')
    ask1_volume = Column(BigInteger, comment='卖一手数')
    
    # 五档盘口（JSON存储）
    bid5_data = Column(String(500), comment='五档买盘JSON')
    ask5_data = Column(String(500), comment='五档卖盘JSON')
    
    # 市场指标
    pe_ttm = Column(Numeric(10, 2), comment='市盈率TTM')
    pb = Column(Numeric(10, 2), comment='市净率')
    total_mv = Column(Numeric(16, 2), comment='总市值')
    float_mv = Column(Numeric(16, 2), comment='流通市值')
    turnover = Column(Numeric(6, 2), comment='换手率%')
    
    # 时间戳
    quote_time = Column(DateTime, comment='行情时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_quote_time', 'quote_time'),
        Index('idx_quote_change_pct', 'change_pct'),
    )
    
    def __repr__(self):
        return f"<Quote(code='{self.code}', price={self.price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        import json
        return {
            'code': self.code,
            'price': float(self.price) if self.price else None,
            'pre_close': float(self.pre_close) if self.pre_close else None,
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'change': float(self.change) if self.change else None,
            'change_pct': float(self.change_pct) if self.change_pct else None,
            'volume': self.volume,
            'amount': float(self.amount) if self.amount else None,
            'bid1_price': float(self.bid1_price) if self.bid1_price else None,
            'bid1_volume': self.bid1_volume,
            'ask1_price': float(self.ask1_price) if self.ask1_price else None,
            'ask1_volume': self.ask1_volume,
            'bid5': json.loads(self.bid5_data) if self.bid5_data else [],
            'ask5': json.loads(self.ask5_data) if self.ask5_data else [],
            'pe_ttm': float(self.pe_ttm) if self.pe_ttm else None,
            'pb': float(self.pb) if self.pb else None,
            'total_mv': float(self.total_mv) if self.total_mv else None,
            'float_mv': float(self.float_mv) if self.float_mv else None,
            'turnover': float(self.turnover) if self.turnover else None,
            'quote_time': self.quote_time.strftime('%Y-%m-%d %H:%M:%S') if self.quote_time else None,
        }


class QuoteRepository:
    """行情数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_code(self, code: str) -> Optional[Quote]:
        """根据代码获取行情"""
        session = self._get_session()
        try:
            return session.query(Quote).filter(Quote.code == code).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_codes(self, codes: List[str]) -> List[Quote]:
        """批量获取行情"""
        if not codes:
            return []
        
        session = self._get_session()
        try:
            return session.query(Quote).filter(Quote.code.in_(codes)).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_all(self) -> List[Quote]:
        """获取所有行情"""
        session = self._get_session()
        try:
            return session.query(Quote).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, quote: Quote) -> bool:
        """保存行情"""
        session = self._get_session()
        try:
            existing = session.query(Quote).filter(Quote.code == quote.code).first()
            if existing:
                quote.id = existing.id
                session.merge(quote)
            else:
                session.add(quote)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存行情失败 {quote.code}: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def save_batch(self, quotes: List[Quote]) -> int:
        """批量保存行情"""
        if not quotes:
            return 0
        
        session = self._get_session()
        count = 0
        
        try:
            for quote in quotes:
                existing = session.query(Quote).filter(Quote.code == quote.code).first()
                if existing:
                    quote.id = existing.id
                    session.merge(quote)
                else:
                    session.add(quote)
                count += 1
            
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"批量保存行情失败: {e}")
            return 0
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_top_gainers(self, limit: int = 20) -> List[Quote]:
        """获取涨幅榜"""
        session = self._get_session()
        try:
            return session.query(Quote).filter(
                Quote.change_pct.isnot(None)
            ).order_by(Quote.change_pct.desc()).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_top_losers(self, limit: int = 20) -> List[Quote]:
        """获取跌幅榜"""
        session = self._get_session()
        try:
            return session.query(Quote).filter(
                Quote.change_pct.isnot(None)
            ).order_by(Quote.change_pct.asc()).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_most_active(self, limit: int = 20) -> List[Quote]:
        """获取活跃榜（按成交额）"""
        session = self._get_session()
        try:
            return session.query(Quote).filter(
                Quote.amount.isnot(None)
            ).order_by(Quote.amount.desc()).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
