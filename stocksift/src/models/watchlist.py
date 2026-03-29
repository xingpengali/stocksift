# -*- coding: utf-8 -*-
"""
自选股模型

存储用户自选股分组和股票
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class WatchlistGroup(Base):
    """
    自选股分组表
    """
    __tablename__ = 'watchlist_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='分组名称')
    description = Column(String(200), comment='分组描述')
    
    # 排序
    sort_order = Column(Integer, default=0, comment='排序顺序')
    
    # 是否是默认分组
    is_default = Column(Boolean, default=False, comment='是否默认分组')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    stocks = relationship("WatchlistStock", back_populates="group", 
                         cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_watchlist_group_order', 'sort_order'),
    )
    
    def __repr__(self):
        return f"<WatchlistGroup(name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_default': self.is_default,
            'stock_count': len(self.stocks) if self.stocks else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class WatchlistStock(Base):
    """
    自选股表
    """
    __tablename__ = 'watchlist_stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('watchlist_groups.id'), nullable=False, comment='分组ID')
    code = Column(String(10), nullable=False, comment='股票代码')
    
    # 备注
    remark = Column(String(200), comment='备注')
    
    # 排序
    sort_order = Column(Integer, default=0, comment='排序顺序')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='添加时间')
    
    # 关联
    group = relationship("WatchlistGroup", back_populates="stocks")
    
    # 索引
    __table_args__ = (
        Index('idx_watchlist_stock_group', 'group_id'),
        Index('idx_watchlist_stock_code', 'code'),
        Index('idx_watchlist_unique', 'group_id', 'code', unique=True),
    )
    
    def __repr__(self):
        return f"<WatchlistStock(group_id={self.group_id}, code='{self.code}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'code': self.code,
            'remark': self.remark,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class WatchlistGroupRepository:
    """自选股分组数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_id(self, group_id: int) -> Optional[WatchlistGroup]:
        """根据ID获取分组"""
        session = self._get_session()
        try:
            return session.query(WatchlistGroup).filter(WatchlistGroup.id == group_id).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_all(self) -> List[WatchlistGroup]:
        """获取所有分组"""
        session = self._get_session()
        try:
            return session.query(WatchlistGroup).order_by(
                WatchlistGroup.sort_order.asc()
            ).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_default(self) -> Optional[WatchlistGroup]:
        """获取默认分组"""
        session = self._get_session()
        try:
            return session.query(WatchlistGroup).filter(
                WatchlistGroup.is_default == True
            ).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, group: WatchlistGroup) -> bool:
        """保存分组"""
        session = self._get_session()
        try:
            if group.id:
                session.merge(group)
            else:
                session.add(group)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存分组失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def delete(self, group_id: int) -> bool:
        """删除分组"""
        session = self._get_session()
        try:
            group = session.query(WatchlistGroup).filter(WatchlistGroup.id == group_id).first()
            if group:
                session.delete(group)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除分组失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def set_default(self, group_id: int) -> bool:
        """设置默认分组"""
        session = self._get_session()
        try:
            # 取消其他默认分组
            session.query(WatchlistGroup).filter(WatchlistGroup.is_default == True).update(
                {WatchlistGroup.is_default: False}
            )
            
            # 设置新的默认分组
            group = session.query(WatchlistGroup).filter(WatchlistGroup.id == group_id).first()
            if group:
                group.is_default = True
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"设置默认分组失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()


class WatchlistStockRepository:
    """自选股数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_group(self, group_id: int) -> List[WatchlistStock]:
        """获取分组的所有股票"""
        session = self._get_session()
        try:
            return session.query(WatchlistStock).filter(
                WatchlistStock.group_id == group_id
            ).order_by(WatchlistStock.sort_order.asc()).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_code(self, code: str) -> List[WatchlistStock]:
        """获取股票所在的所有分组"""
        session = self._get_session()
        try:
            return session.query(WatchlistStock).filter(
                WatchlistStock.code == code
            ).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def is_in_watchlist(self, code: str, group_id: Optional[int] = None) -> bool:
        """检查股票是否在自选列表中"""
        session = self._get_session()
        try:
            query = session.query(WatchlistStock).filter(WatchlistStock.code == code)
            if group_id:
                query = query.filter(WatchlistStock.group_id == group_id)
            return query.first() is not None
        finally:
            if not self._use_external_session:
                session.close()
    
    def add(self, group_id: int, code: str, remark: str = "") -> bool:
        """添加股票到分组"""
        session = self._get_session()
        try:
            # 检查是否已存在
            existing = session.query(WatchlistStock).filter(
                WatchlistStock.group_id == group_id,
                WatchlistStock.code == code
            ).first()
            
            if existing:
                return True  # 已存在，视为成功
            
            stock = WatchlistStock(
                group_id=group_id,
                code=code,
                remark=remark
            )
            session.add(stock)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"添加自选股失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def remove(self, group_id: int, code: str) -> bool:
        """从分组移除股票"""
        session = self._get_session()
        try:
            stock = session.query(WatchlistStock).filter(
                WatchlistStock.group_id == group_id,
                WatchlistStock.code == code
            ).first()
            
            if stock:
                session.delete(stock)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"移除自选股失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def update_remark(self, watchlist_id: int, remark: str) -> bool:
        """更新备注"""
        session = self._get_session()
        try:
            stock = session.query(WatchlistStock).filter(
                WatchlistStock.id == watchlist_id
            ).first()
            
            if stock:
                stock.remark = remark
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新备注失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def move_to_group(self, watchlist_id: int, new_group_id: int) -> bool:
        """移动股票到另一个分组"""
        session = self._get_session()
        try:
            stock = session.query(WatchlistStock).filter(
                WatchlistStock.id == watchlist_id
            ).first()
            
            if stock:
                # 检查目标分组是否已有该股票
                existing = session.query(WatchlistStock).filter(
                    WatchlistStock.group_id == new_group_id,
                    WatchlistStock.code == stock.code
                ).first()
                
                if existing:
                    # 目标分组已有，删除当前记录
                    session.delete(stock)
                else:
                    stock.group_id = new_group_id
                
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"移动股票失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_count(self, group_id: Optional[int] = None) -> int:
        """获取股票数量"""
        session = self._get_session()
        try:
            query = session.query(WatchlistStock)
            if group_id:
                query = query.filter(WatchlistStock.group_id == group_id)
            return query.count()
        finally:
            if not self._use_external_session:
                session.close()
