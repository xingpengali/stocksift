# -*- coding: utf-8 -*-
"""
预警模型

存储预警规则和预警记录
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text, Index

from .database import Base, get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class AlertRule(Base):
    """
    预警规则表
    
    存储用户设置的预警规则
    """
    __tablename__ = 'alert_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='规则名称')
    code = Column(String(10), nullable=False, comment='股票代码')
    
    # 预警类型
    alert_type = Column(String(20), nullable=False, comment='预警类型(price/change/volume/indicator)')
    
    # 条件配置（JSON存储）
    condition_config = Column(Text, comment='条件配置JSON')
    
    # 运算符
    operator = Column(String(20), comment='运算符(above/below/cross_up/cross_down)')
    
    # 阈值
    threshold = Column(Numeric(16, 4), comment='阈值')
    threshold_secondary = Column(Numeric(16, 4), comment='次要阈值（区间用）')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_triggered = Column(Boolean, default=False, comment='是否已触发')
    
    # 通知设置
    notify_popup = Column(Boolean, default=True, comment='弹窗通知')
    notify_sound = Column(Boolean, default=True, comment='声音通知')
    
    # 触发统计
    trigger_count = Column(Integer, default=0, comment='触发次数')
    last_triggered_at = Column(DateTime, comment='上次触发时间')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_alert_rule_code', 'code'),
        Index('idx_alert_rule_active', 'is_active'),
        Index('idx_alert_rule_type', 'alert_type'),
    )
    
    def __repr__(self):
        return f"<AlertRule(name='{self.name}', code='{self.code}', type='{self.alert_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'alert_type': self.alert_type,
            'condition_config': json.loads(self.condition_config) if self.condition_config else {},
            'operator': self.operator,
            'threshold': float(self.threshold) if self.threshold else None,
            'threshold_secondary': float(self.threshold_secondary) if self.threshold_secondary else None,
            'is_active': self.is_active,
            'is_triggered': self.is_triggered,
            'notify_popup': self.notify_popup,
            'notify_sound': self.notify_sound,
            'trigger_count': self.trigger_count,
            'last_triggered_at': self.last_triggered_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_triggered_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class AlertRecord(Base):
    """
    预警记录表
    
    存储预警触发历史
    """
    __tablename__ = 'alert_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, nullable=False, comment='规则ID')
    code = Column(String(10), nullable=False, comment='股票代码')
    
    # 触发时的数据
    trigger_price = Column(Numeric(10, 2), comment='触发价格')
    trigger_value = Column(Numeric(16, 4), comment='触发值')
    
    # 触发信息
    message = Column(String(500), comment='预警消息')
    
    # 状态
    is_read = Column(Boolean, default=False, comment='是否已读')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='触发时间')
    
    # 索引
    __table_args__ = (
        Index('idx_alert_record_rule', 'rule_id'),
        Index('idx_alert_record_code', 'code'),
        Index('idx_alert_record_read', 'is_read'),
        Index('idx_alert_record_time', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AlertRecord(rule_id={self.rule_id}, code='{self.code}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'code': self.code,
            'trigger_price': float(self.trigger_price) if self.trigger_price else None,
            'trigger_value': float(self.trigger_value) if self.trigger_value else None,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class AlertRuleRepository:
    """预警规则数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_id(self, rule_id: int) -> Optional[AlertRule]:
        """根据ID获取规则"""
        session = self._get_session()
        try:
            return session.query(AlertRule).filter(AlertRule.id == rule_id).first()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_by_code(self, code: str, active_only: bool = True) -> List[AlertRule]:
        """获取股票的所有预警规则"""
        session = self._get_session()
        try:
            query = session.query(AlertRule).filter(AlertRule.code == code)
            if active_only:
                query = query.filter(AlertRule.is_active == True)
            return query.all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_all_active(self) -> List[AlertRule]:
        """获取所有启用的规则"""
        session = self._get_session()
        try:
            return session.query(AlertRule).filter(AlertRule.is_active == True).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, rule: AlertRule) -> bool:
        """保存规则"""
        session = self._get_session()
        try:
            if rule.id:
                session.merge(rule)
            else:
                session.add(rule)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存预警规则失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def delete(self, rule_id: int) -> bool:
        """删除规则"""
        session = self._get_session()
        try:
            rule = session.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if rule:
                session.delete(rule)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除预警规则失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def update_trigger_status(self, rule_id: int, triggered: bool) -> bool:
        """更新触发状态"""
        session = self._get_session()
        try:
            rule = session.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if rule:
                rule.is_triggered = triggered
                if triggered:
                    rule.trigger_count += 1
                    rule.last_triggered_at = datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新触发状态失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()


class AlertRecordRepository:
    """预警记录数据访问对象"""
    
    def __init__(self, session=None):
        self.session = session
        self._use_external_session = session is not None
    
    def _get_session(self):
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def get_by_rule(self, rule_id: int, limit: int = 100) -> List[AlertRecord]:
        """获取规则的触发记录"""
        session = self._get_session()
        try:
            return session.query(AlertRecord).filter(
                AlertRecord.rule_id == rule_id
            ).order_by(AlertRecord.created_at.desc()).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_unread(self, limit: int = 50) -> List[AlertRecord]:
        """获取未读记录"""
        session = self._get_session()
        try:
            return session.query(AlertRecord).filter(
                AlertRecord.is_read == False
            ).order_by(AlertRecord.created_at.desc()).limit(limit).all()
        finally:
            if not self._use_external_session:
                session.close()
    
    def save(self, record: AlertRecord) -> bool:
        """保存记录"""
        session = self._get_session()
        try:
            session.add(record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存预警记录失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def mark_as_read(self, record_id: int) -> bool:
        """标记为已读"""
        session = self._get_session()
        try:
            record = session.query(AlertRecord).filter(AlertRecord.id == record_id).first()
            if record:
                record.is_read = True
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"标记已读失败: {e}")
            return False
        finally:
            if not self._use_external_session:
                session.close()
    
    def mark_all_as_read(self) -> int:
        """标记所有为已读"""
        session = self._get_session()
        try:
            count = session.query(AlertRecord).filter(AlertRecord.is_read == False).update(
                {AlertRecord.is_read: True}
            )
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"标记全部已读失败: {e}")
            return 0
        finally:
            if not self._use_external_session:
                session.close()
    
    def get_count(self, unread_only: bool = False) -> int:
        """获取记录数量"""
        session = self._get_session()
        try:
            query = session.query(AlertRecord)
            if unread_only:
                query = query.filter(AlertRecord.is_read == False)
            return query.count()
        finally:
            if not self._use_external_session:
                session.close()
