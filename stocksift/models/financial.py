# -*- coding: utf-8 -*-
"""
财务数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Index

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class Financial(Base):
    """
    财务数据表
    
    存储股票的财务报表数据（季报、年报）
    """
    __tablename__ = 'financials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, comment='股票代码')
    report_date = Column(Date, nullable=False, comment='报告期')
    report_type = Column(String(10), comment='报告类型(Q1/Q2/Q3/annual)')
    
    # 利润表主要指标
    revenue = Column(Numeric(16, 2), comment='营业收入')
    operating_profit = Column(Numeric(16, 2), comment='营业利润')
    total_profit = Column(Numeric(16, 2), comment='利润总额')
    net_profit = Column(Numeric(16, 2), comment='净利润')
    net_profit_parent = Column(Numeric(16, 2), comment='归母净利润')
    
    # 盈利能力
    eps = Column(Numeric(10, 4), comment='每股收益')
    eps_diluted = Column(Numeric(10, 4), comment='稀释每股收益')
    roe = Column(Numeric(10, 2), comment='净资产收益率%')
    roe_diluted = Column(Numeric(10, 2), comment='稀释ROE%')
    roa = Column(Numeric(10, 2), comment='总资产收益率%')
    gross_margin = Column(Numeric(10, 2), comment='毛利率%')
    net_margin = Column(Numeric(10, 2), comment='净利率%')
    
    # 资产负债
    total_assets = Column(Numeric(16, 2), comment='总资产')
    total_liabilities = Column(Numeric(16, 2), comment='总负债')
    equity = Column(Numeric(16, 2), comment='股东权益')
    
    # 偿债能力
    debt_ratio = Column(Numeric(10, 2), comment='资产负债率%')
    current_ratio = Column(Numeric(10, 2), comment='流动比率')
    quick_ratio = Column(Numeric(10, 2), comment='速动比率')
    
    # 现金流
    operating_cash_flow = Column(Numeric(16, 2), comment='经营现金流')
    investing_cash_flow = Column(Numeric(16, 2), comment='投资现金流')
    financing_cash_flow = Column(Numeric(16, 2), comment='筹资现金流')
    free_cash_flow = Column(Numeric(16, 2), comment='自由现金流')
    
    # 成长指标（同比）
    revenue_growth = Column(Numeric(10, 2), comment='营收增长率%')
    profit_growth = Column(Numeric(10, 2), comment='净利润增长率%')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        Index('idx_financial_code', 'code'),
        Index('idx_financial_date', 'report_date'),
        Index('idx_financial_unique', 'code', 'report_date', unique=True),
    )
    
    def __repr__(self):
        return f"<Financial(code='{self.code}', date={self.report_date})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'report_date': self.report_date.strftime('%Y-%m-%d') if self.report_date else None,
            'report_type': self.report_type,
            'revenue': float(self.revenue) if self.revenue else None,
            'operating_profit': float(self.operating_profit) if self.operating_profit else None,
            'total_profit': float(self.total_profit) if self.total_profit else None,
            'net_profit': float(self.net_profit) if self.net_profit else None,
            'net_profit_parent': float(self.net_profit_parent) if self.net_profit_parent else None,
            'eps': float(self.eps) if self.eps else None,
            'eps_diluted': float(self.eps_diluted) if self.eps_diluted else None,
            'roe': float(self.roe) if self.roe else None,
            'roa': float(self.roa) if self.roa else None,
            'gross_margin': float(self.gross_margin) if self.gross_margin else None,
            'net_margin': float(self.net_margin) if self.net_margin else None,
            'total_assets': float(self.total_assets) if self.total_assets else None,
            'total_liabilities': float(self.total_liabilities) if self.total_liabilities else None,
            'equity': float(self.equity) if self.equity else None,
            'debt_ratio': float(self.debt_ratio) if self.debt_ratio else None,
            'current_ratio': float(self.current_ratio) if self.current_ratio else None,
            'quick_ratio': float(self.quick_ratio) if self.quick_ratio else None,
            'operating_cash_flow': float(self.operating_cash_flow) if self.operating_cash_flow else None,
            'free_cash_flow': float(self.free_cash_flow) if self.free_cash_flow else None,
            'revenue_growth': float(self.revenue_growth) if self.revenue_growth else None,
            'profit_growth': float(self.profit_growth) if self.profit_growth else None,
        }


class FinancialRepository:
    """财务数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_code(self, code: str, report_date=None) -> Optional[Financial]:
        """获取财务数据"""
        session = self._get_session()
        try:
            query = session.query(Financial).filter(Financial.code == code)
            if report_date:
                query = query.filter(Financial.report_date == report_date)
            else:
                # 返回最新报告期
                query = query.order_by(Financial.report_date.desc())
            return query.first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_history(
        self,
        code: str,
        years: int = 5
    ) -> List[Financial]:
        """获取历史财务数据"""
        from datetime import date, timedelta
        
        session = self._get_session()
        try:
            start_date = date.today() - timedelta(days=365 * years)
            return session.query(Financial).filter(
                Financial.code == code,
                Financial.report_date >= start_date
            ).order_by(Financial.report_date.desc()).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, financial: Financial) -> bool:
        """保存财务数据"""
        session = self._get_session()
        try:
            existing = session.query(Financial).filter(
                Financial.code == financial.code,
                Financial.report_date == financial.report_date
            ).first()
            
            if existing:
                financial.id = existing.id
                session.merge(financial)
            else:
                session.add(financial)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存财务数据失败 {financial.code}: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def save_batch(self, financials: List[Financial]) -> int:
        """批量保存财务数据"""
        if not financials:
            return 0
        
        session = self._get_session()
        count = 0
        
        try:
            for financial in financials:
                existing = session.query(Financial).filter(
                    Financial.code == financial.code,
                    Financial.report_date == financial.report_date
                ).first()
                
                if existing:
                    financial.id = existing.id
                    session.merge(financial)
                else:
                    session.add(financial)
                count += 1
            
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"批量保存财务数据失败: {e}")
            return 0
        finally:
            if not self._use_external_session:
                session.close()
