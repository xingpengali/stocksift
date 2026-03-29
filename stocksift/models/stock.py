# -*- coding: utf-8 -*-
"""
股票基本信息模型
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, Index
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, get_db_manager, session_scope
from utils.logger import get_logger

logger = get_logger(__name__)


class Stock(Base):
    """
    股票基本信息表
    
    存储A股所有股票的基本信息，包括代码、名称、行业、上市日期等
    """
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True, comment='股票代码')
    name = Column(String(50), nullable=False, comment='股票名称')
    exchange = Column(String(10), nullable=False, comment='交易所(SSE/SZSE/BSE)')
    market_type = Column(String(10), comment='市场类型(main/gem/star/bj)')
    
    # 行业信息
    industry_code = Column(String(10), comment='行业代码')
    industry_name = Column(String(50), comment='行业名称')
    sub_industry_code = Column(String(10), comment='子行业代码')
    sub_industry_name = Column(String(50), comment='子行业名称')
    
    # 概念板块（JSON存储）
    concept_list = Column(String(500), comment='概念板块JSON列表')
    
    # 地域信息
    province = Column(String(20), comment='省份')
    city = Column(String(20), comment='城市')
    
    # 上市信息
    list_date = Column(Date, comment='上市日期')
    total_shares = Column(BigInteger, comment='总股本')
    float_shares = Column(BigInteger, comment='流通股本')
    
    # 状态
    is_active = Column(Integer, default=1, comment='是否活跃(1:是,0:否)')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_stock_industry', 'industry_code'),
        Index('idx_stock_market', 'market_type'),
        Index('idx_stock_exchange', 'exchange'),
        Index('idx_stock_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Stock(code='{self.code}', name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'exchange': self.exchange,
            'market_type': self.market_type,
            'industry_code': self.industry_code,
            'industry_name': self.industry_name,
            'sub_industry_code': self.sub_industry_code,
            'sub_industry_name': self.sub_industry_name,
            'concept_list': json.loads(self.concept_list) if self.concept_list else [],
            'province': self.province,
            'city': self.city,
            'list_date': self.list_date.strftime('%Y-%m-%d') if self.list_date else None,
            'total_shares': self.total_shares,
            'float_shares': self.float_shares,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stock':
        """从字典创建对象"""
        stock = cls()
        stock.code = data.get('code', '')
        stock.name = data.get('name', '')
        stock.exchange = data.get('exchange', '')
        stock.market_type = data.get('market_type', '')
        stock.industry_code = data.get('industry_code', '')
        stock.industry_name = data.get('industry_name', '')
        stock.sub_industry_code = data.get('sub_industry_code', '')
        stock.sub_industry_name = data.get('sub_industry_name', '')
        
        # 处理概念列表
        concept_list = data.get('concept_list', [])
        if isinstance(concept_list, list):
            stock.concept_list = json.dumps(concept_list, ensure_ascii=False)
        else:
            stock.concept_list = str(concept_list)
        
        stock.province = data.get('province', '')
        stock.city = data.get('city', '')
        
        # 处理日期
        list_date = data.get('list_date')
        if list_date and isinstance(list_date, str):
            from datetime import datetime
            try:
                stock.list_date = datetime.strptime(list_date, '%Y-%m-%d').date()
            except ValueError:
                stock.list_date = None
        
        stock.total_shares = data.get('total_shares')
        stock.float_shares = data.get('float_shares')
        stock.is_active = 1 if data.get('is_active', True) else 0
        
        return stock


class StockRepository:
    """
    股票数据访问对象
    
    提供股票数据的增删改查操作
    """
    
    def __init__(self, session: Session = None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_code(self, code: str) -> Optional[Stock]:
        """
        根据代码获取股票
        
        Args:
            code: 股票代码
            
        Returns:
            Stock对象或None
        """
        session = self._get_session()
        try:
            return session.query(Stock).filter(
                Stock.code == code,
                Stock.is_active == 1
            ).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_codes(self, codes: List[str]) -> List[Stock]:
        """
        批量获取股票
        
        Args:
            codes: 股票代码列表
            
        Returns:
            Stock对象列表
        """
        if not codes:
            return []
        
        session = self._get_session()
        try:
            return session.query(Stock).filter(
                Stock.code.in_(codes),
                Stock.is_active == 1
            ).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_all(self, active_only: bool = True) -> List[Stock]:
        """
        获取所有股票
        
        Args:
            active_only: 是否只返回活跃股票
            
        Returns:
            Stock对象列表
        """
        session = self._get_session()
        try:
            query = session.query(Stock)
            if active_only:
                query = query.filter(Stock.is_active == 1)
            return query.all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_industry(self, industry_code: str) -> List[Stock]:
        """
        根据行业获取股票
        
        Args:
            industry_code: 行业代码
            
        Returns:
            Stock对象列表
        """
        session = self._get_session()
        try:
            return session.query(Stock).filter(
                Stock.industry_code == industry_code,
                Stock.is_active == 1
            ).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_market(self, market_type: str) -> List[Stock]:
        """
        根据市场类型获取股票
        
        Args:
            market_type: 市场类型
            
        Returns:
            Stock对象列表
        """
        session = self._get_session()
        try:
            return session.query(Stock).filter(
                Stock.market_type == market_type,
                Stock.is_active == 1
            ).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def search(self, keyword: str, limit: int = 20) -> List[Stock]:
        """
        搜索股票（代码或名称模糊搜索）
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            Stock对象列表
        """
        if not keyword:
            return []
        
        session = self._get_session()
        try:
            keyword = f"%{keyword}%"
            return session.query(Stock).filter(
                Stock.is_active == 1
            ).filter(
                (Stock.code.like(keyword)) | (Stock.name.like(keyword))
            ).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, stock: Stock) -> bool:
        """
        保存股票（新增或更新）
        
        Args:
            stock: Stock对象
            
        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            # 检查是否已存在
            existing = session.query(Stock).filter(Stock.code == stock.code).first()
            if existing:
                # 更新
                stock.id = existing.id
                stock.created_at = existing.created_at
                session.merge(stock)
            else:
                # 新增
                session.add(stock)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存股票失败 {stock.code}: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def save_batch(self, stocks: List[Stock]) -> int:
        """
        批量保存股票
        
        Args:
            stocks: Stock对象列表
            
        Returns:
            成功保存的数量
        """
        if not stocks:
            return 0
        
        session = self._get_session()
        count = 0
        
        try:
            for stock in stocks:
                existing = session.query(Stock).filter(Stock.code == stock.code).first()
                if existing:
                    stock.id = existing.id
                    stock.created_at = existing.created_at
                    session.merge(stock)
                else:
                    session.add(stock)
                count += 1
            
            session.commit()
            logger.info(f"批量保存股票完成: {count}条")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"批量保存股票失败: {e}")
            return 0
        finally:
            if not self._use_external_session:
                session.close()
    
    def delete(self, code: str, soft_delete: bool = True) -> bool:
        """
        删除股票
        
        Args:
            code: 股票代码
            soft_delete: 是否软删除
            
        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            stock = session.query(Stock).filter(Stock.code == code).first()
            if not stock:
                return False
            
            if soft_delete:
                stock.is_active = 0
            else:
                session.delete(stock)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"删除股票失败 {code}: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_count(self) -> int:
        """获取股票总数"""
        session = self._get_session()
        try:
            return session.query(Stock).filter(Stock.is_active == 1).count()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_industries(self) -> List[Dict[str, str]]:
        """
        获取所有行业列表
        
        Returns:
            行业列表，每项包含code和name
        """
        session = self._get_session()
        try:
            results = session.query(
                Stock.industry_code,
                Stock.industry_name
            ).filter(
                Stock.is_active == 1,
                Stock.industry_code.isnot(None)
            ).distinct().all()
            
            return [
                {'code': code, 'name': name}
                for code, name in results
                if code and name
            ]
        finally:
            if not self._use_external_session:
                session.close()
