# -*- coding: utf-8 -*-
"""
策略模型

存储选股策略定义和回测结果
"""
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, Index

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class Strategy(Base):
    """
    策略定义表
    
    存储用户定义的选股策略
    """
    __tablename__ = 'strategies'
    
    id = Column(String(20), primary_key=True, comment='策略ID')
    name = Column(String(100), nullable=False, comment='策略名称')
    description = Column(Text, comment='策略描述')
    
    # 策略类型
    strategy_type = Column(String(20), comment='策略类型(technical/fundamental/combined)')
    
    # 策略配置（JSON存储筛选条件）
    config = Column(Text, comment='策略配置JSON')
    
    # 策略参数
    params = Column(Text, comment='策略参数JSON')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_default = Column(Boolean, default=False, comment='是否默认策略')
    
    # 回测统计
    backtest_count = Column(Integer, default=0, comment='回测次数')
    last_backtest_at = Column(DateTime, comment='上次回测时间')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_type', 'strategy_type'),
        Index('idx_strategy_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Strategy(name='{self.name}', type='{self.strategy_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'strategy_type': self.strategy_type,
            'config': json.loads(self.config) if self.config else {},
            'params': json.loads(self.params) if self.params else {},
            'is_active': self.is_active,
            'is_default': self.is_default,
            'backtest_count': self.backtest_count,
            'last_backtest_at': self.last_backtest_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_backtest_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class BacktestRecord(Base):
    """
    回测记录表
    
    存储策略回测结果
    """
    __tablename__ = 'backtest_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, nullable=False, comment='策略ID')
    
    # 回测时间范围
    start_date = Column(Date, nullable=False, comment='开始日期')
    end_date = Column(Date, nullable=False, comment='结束日期')
    
    # 回测结果
    initial_capital = Column(Numeric(16, 2), comment='初始资金')
    final_capital = Column(Numeric(16, 2), comment='最终资金')
    total_return = Column(Numeric(10, 4), comment='总收益率%')
    annual_return = Column(Numeric(10, 4), comment='年化收益率%')
    max_drawdown = Column(Numeric(10, 4), comment='最大回撤%')
    sharpe_ratio = Column(Numeric(10, 4), comment='夏普比率')
    
    # 交易统计
    trade_count = Column(Integer, comment='交易次数')
    win_count = Column(Integer, comment='盈利次数')
    loss_count = Column(Integer, comment='亏损次数')
    win_rate = Column(Numeric(6, 2), comment='胜率%')
    
    # 详细结果
    result_detail = Column(Text, comment='详细结果JSON')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='回测时间')
    
    # 索引
    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_id'),
        Index('idx_backtest_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BacktestRecord(strategy_id={self.strategy_id}, return={self.total_return}%)>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'initial_capital': float(self.initial_capital) if self.initial_capital else None,
            'final_capital': float(self.final_capital) if self.final_capital else None,
            'total_return': float(self.total_return) if self.total_return else None,
            'annual_return': float(self.annual_return) if self.annual_return else None,
            'max_drawdown': float(self.max_drawdown) if self.max_drawdown else None,
            'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else None,
            'trade_count': self.trade_count,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'win_rate': float(self.win_rate) if self.win_rate else None,
            'result_detail': json.loads(self.result_detail) if self.result_detail else {},
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class StrategyRepository:
    """策略数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """根据ID获取策略"""
        session = self._get_session()
        try:
            return session.query(Strategy).filter(Strategy.id == strategy_id).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_all(self, active_only: bool = True) -> List[Strategy]:
        """获取所有策略"""
        session = self._get_session()
        try:
            query = session.query(Strategy)
            if active_only:
                query = query.filter(Strategy.is_active == True)
            return query.order_by(Strategy.created_at.desc()).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_type(self, strategy_type: str) -> List[Strategy]:
        """根据类型获取策略"""
        session = self._get_session()
        try:
            return session.query(Strategy).filter(
                Strategy.strategy_type == strategy_type,
                Strategy.is_active == True
            ).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_default(self) -> Optional[Strategy]:
        """获取默认策略"""
        session = self._get_session()
        try:
            return session.query(Strategy).filter(
                Strategy.is_default == True,
                Strategy.is_active == True
            ).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, strategy: Strategy) -> bool:
        """保存策略"""
        session = self._get_session()
        try:
            if strategy.id:
                session.merge(strategy)
            else:
                session.add(strategy)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存策略失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def delete(self, strategy_id: int) -> bool:
        """删除策略"""
        session = self._get_session()
        try:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                session.delete(strategy)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除策略失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def set_default(self, strategy_id: int) -> bool:
        """设置默认策略"""
        session = self._get_session()
        try:
            # 取消其他默认策略
            session.query(Strategy).filter(Strategy.is_default == True).update(
                {Strategy.is_default: False}
            )
            
            # 设置新的默认策略
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                strategy.is_default = True
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"设置默认策略失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def update_backtest_stats(self, strategy_id: int) -> bool:
        """更新回测统计"""
        session = self._get_session()
        try:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                strategy.backtest_count += 1
                strategy.last_backtest_at = datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新回测统计失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()


class BacktestRecordRepository:
    """回测记录数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_strategy(self, strategy_id: int, limit: int = 10) -> List[BacktestRecord]:
        """获取策略的回测记录"""
        session = self._get_session()
        try:
            return session.query(BacktestRecord).filter(
                BacktestRecord.strategy_id == strategy_id
            ).order_by(BacktestRecord.created_at.desc()).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_latest(self, strategy_id: int) -> Optional[BacktestRecord]:
        """获取最新回测记录"""
        session = self._get_session()
        try:
            return session.query(BacktestRecord).filter(
                BacktestRecord.strategy_id == strategy_id
            ).order_by(BacktestRecord.created_at.desc()).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, record: BacktestRecord) -> bool:
        """保存回测记录"""
        session = self._get_session()
        try:
            session.add(record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存回测记录失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_best_performing(self, limit: int = 10) -> List[BacktestRecord]:
        """获取表现最好的回测记录"""
        session = self._get_session()
        try:
            return session.query(BacktestRecord).order_by(
                BacktestRecord.total_return.desc()
            ).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
