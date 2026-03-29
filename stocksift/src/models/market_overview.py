# -*- coding: utf-8 -*-
"""
市场概览数据模型

存储大盘指数、板块排行、涨跌统计等市场概览数据
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Numeric, DateTime, BigInteger, Index, Float, func, desc

from .database import Base, get_db_manager, session_scope
from utils.logger import get_logger

logger = get_logger(__name__)


class MarketIndex(Base):
    """
    大盘指数数据表
    
    存储上证指数、深证成指、创业板指、科创50等指数数据
    """
    __tablename__ = 'market_indices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment='指数代码')
    name = Column(String(20), nullable=False, comment='指数名称')
    
    # 价格信息
    value = Column(Numeric(10, 2), comment='指数值')
    pre_close = Column(Numeric(10, 2), comment='昨收')
    open = Column(Numeric(10, 2), comment='开盘价')
    high = Column(Numeric(10, 2), comment='最高价')
    low = Column(Numeric(10, 2), comment='最低价')
    
    # 涨跌幅
    change = Column(Numeric(10, 2), comment='涨跌额')
    change_pct = Column(Numeric(6, 2), comment='涨跌幅%')
    
    # 成交量额
    volume = Column(BigInteger, comment='成交量')
    amount = Column(Numeric(16, 2), comment='成交额')
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：指数代码
    __table_args__ = (
        Index('idx_market_index_code_updated', 'code', 'updated_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'value': float(self.value) if self.value else 0,
            'pre_close': float(self.pre_close) if self.pre_close else 0,
            'open': float(self.open) if self.open else 0,
            'high': float(self.high) if self.high else 0,
            'low': float(self.low) if self.low else 0,
            'change': float(self.change) if self.change else 0,
            'change_pct': float(self.change_pct) if self.change_pct else 0,
            'volume': self.volume,
            'amount': float(self.amount) if self.amount else 0,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Sector(Base):
    """
    行业板块数据表
    
    存储行业板块排行数据
    """
    __tablename__ = 'sectors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='板块名称')
    
    # 涨跌幅
    change_pct = Column(Numeric(6, 2), comment='涨跌幅%')
    change = Column(Numeric(10, 2), comment='涨跌额')
    
    # 成交额
    amount = Column(Numeric(16, 2), comment='成交额')
    
    # 领涨股
    leader_name = Column(String(20), comment='领涨股名称')
    leader_code = Column(String(10), comment='领涨股代码')
    leader_change_pct = Column(Numeric(6, 2), comment='领涨股涨跌幅%')
    
    # 排名
    rank = Column(Integer, comment='排名')
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：板块名称
    __table_args__ = (
        Index('idx_sector_name_updated', 'name', 'updated_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'change_pct': float(self.change_pct) if self.change_pct else 0,
            'change': float(self.change) if self.change else 0,
            'amount': float(self.amount) if self.amount else 0,
            'leader_name': self.leader_name,
            'leader_code': self.leader_code,
            'leader_change_pct': float(self.leader_change_pct) if self.leader_change_pct else 0,
            'rank': self.rank,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class MarketStats(Base):
    """
    市场涨跌统计数据表
    
    存储全市场涨跌分布统计
    """
    __tablename__ = 'market_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 涨跌统计
    limit_up = Column(Integer, default=0, comment='涨停数')
    up_over_5 = Column(Integer, default=0, comment='涨5%以上')
    up_0_to_5 = Column(Integer, default=0, comment='涨0-5%')
    flat = Column(Integer, default=0, comment='平盘数')
    down_0_to_5 = Column(Integer, default=0, comment='跌0-5%')
    down_over_5 = Column(Integer, default=0, comment='跌5%以上')
    limit_down = Column(Integer, default=0, comment='跌停数')
    
    # 总股票数
    total_count = Column(Integer, default=0, comment='总股票数')
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'limit_up': self.limit_up,
            'up_over_5': self.up_over_5,
            'up_0_to_5': self.up_0_to_5,
            'flat': self.flat,
            'down_0_to_5': self.down_0_to_5,
            'down_over_5': self.down_over_5,
            'limit_down': self.limit_down,
            'total_count': self.total_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CapitalFlow(Base):
    """
    资金流向数据表
    
    存储主力、散户、北向资金等资金流向数据
    """
    __tablename__ = 'capital_flow'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 主力净流入
    main_inflow = Column(Numeric(16, 2), comment='主力净流入')
    # 散户净流入
    retail_inflow = Column(Numeric(16, 2), comment='散户净流入')
    # 北向资金
    north_inflow = Column(Numeric(16, 2), comment='北向资金净流入')
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'main_inflow': float(self.main_inflow) if self.main_inflow else 0,
            'retail_inflow': float(self.retail_inflow) if self.retail_inflow else 0,
            'north_inflow': float(self.north_inflow) if self.north_inflow else 0,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ==================== 数据访问方法 ====================

def get_latest_market_indices() -> List[Dict[str, Any]]:
    """
    获取最新的大盘指数数据
    
    Returns:
        List[Dict]: 指数数据列表
    """
    try:
        with session_scope() as session:
            # 获取每个指数的最新数据
            from sqlalchemy import func
            
            subquery = session.query(
                MarketIndex.code,
                func.max(MarketIndex.updated_at).label('max_updated')
            ).group_by(MarketIndex.code).subquery()
            
            results = session.query(MarketIndex).join(
                subquery,
                (MarketIndex.code == subquery.c.code) &
                (MarketIndex.updated_at == subquery.c.max_updated)
            ).all()
            
            return [r.to_dict() for r in results]
    except Exception as e:
        logger.error(f"获取大盘指数数据失败: {e}")
        return []


def get_latest_sectors(limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取最新的板块排行数据
    
    Args:
        limit: 返回条数
        
    Returns:
        List[Dict]: 板块数据列表
    """
    try:
        with session_scope() as session:
            # 获取最新的板块数据（按更新时间倒序，取最近一批）
            from sqlalchemy import desc
            
            # 先获取最新的更新时间
            latest_time = session.query(
                func.max(Sector.updated_at)
            ).scalar()
            
            if not latest_time:
                return []
            
            # 获取该时间的板块数据
            results = session.query(Sector).filter(
                Sector.updated_at == latest_time
            ).order_by(Sector.rank).limit(limit).all()
            
            return [r.to_dict() for r in results]
    except Exception as e:
        logger.error(f"获取板块数据失败: {e}")
        return []


def get_latest_market_stats() -> Optional[Dict[str, Any]]:
    """
    获取最新的市场涨跌统计数据
    
    Returns:
        Dict: 统计数据，如果没有则返回None
    """
    try:
        with session_scope() as session:
            result = session.query(MarketStats).order_by(
                desc(MarketStats.updated_at)
            ).first()
            
            return result.to_dict() if result else None
    except Exception as e:
        logger.error(f"获取市场统计数据失败: {e}")
        return None


def get_latest_capital_flow() -> Optional[Dict[str, Any]]:
    """
    获取最新的资金流向数据
    
    Returns:
        Dict: 资金流向数据，如果没有则返回None
    """
    try:
        with session_scope() as session:
            from sqlalchemy import desc
            result = session.query(CapitalFlow).order_by(
                desc(CapitalFlow.updated_at)
            ).first()
            
            return result.to_dict() if result else None
    except Exception as e:
        logger.error(f"获取资金流向数据失败: {e}")
        return None
