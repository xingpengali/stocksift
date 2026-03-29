# -*- coding: utf-8 -*-
"""
预警引擎模块

实现股票预警功能
"""
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from decimal import Decimal

from models.database import get_db_manager
from models.alert import AlertRule, AlertRecord, AlertRuleRepository, AlertRecordRepository
from models.quote import Quote, QuoteRepository
from utils.logger import get_logger
from utils.event_bus import event_bus

logger = get_logger(__name__)


@dataclass
class AlertRuleConfig:
    """预警规则配置"""
    name: str
    code: str
    alert_type: str  # price, change, volume, indicator
    operator: str  # above, below, cross_up, cross_down
    threshold: float
    threshold_secondary: float = None  # 区间用
    condition_config: Dict = field(default_factory=dict)
    notify_popup: bool = True
    notify_sound: bool = True


@dataclass
class AlertNotification:
    """预警通知"""
    rule_id: int
    code: str
    trigger_price: float
    trigger_value: float
    message: str
    timestamp: datetime


class AlertEngine:
    """
    预警引擎
    
    实时监控股票数据并触发预警
    """
    
    def __init__(self, check_interval: int = 60):
        """
        初始化
        
        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.rule_repo = AlertRuleRepository()
        self.record_repo = AlertRecordRepository()
        self.quote_repo = QuoteRepository()
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        
        # 缓存当前行情
        self._quote_cache: Dict[str, Quote] = {}
        self._last_check: Dict[int, datetime] = {}  # 记录上次检查时间
    
    def add_rule(self, config: AlertRuleConfig) -> int:
        """
        添加预警规则
        
        Args:
            config: 规则配置
            
        Returns:
            规则ID
        """
        import json
        
        rule = AlertRule(
            name=config.name,
            code=config.code,
            alert_type=config.alert_type,
            operator=config.operator,
            threshold=Decimal(str(config.threshold)),
            threshold_secondary=Decimal(str(config.threshold_secondary)) if config.threshold_secondary else None,
            condition_config=json.dumps(config.condition_config) if config.condition_config else None,
            notify_popup=config.notify_popup,
            notify_sound=config.notify_sound,
            is_active=True,
            is_triggered=False
        )
        
        if self.rule_repo.save(rule):
            logger.info(f"添加预警规则: {config.name} ({config.code})")
            return rule.id
        else:
            raise Exception("添加预警规则失败")
    
    def update_rule(self, rule_id: int, config: AlertRuleConfig) -> bool:
        """
        更新预警规则
        
        Args:
            rule_id: 规则ID
            config: 规则配置
            
        Returns:
            是否成功
        """
        import json
        
        rule = self.rule_repo.get_by_id(rule_id)
        if not rule:
            logger.warning(f"预警规则不存在: {rule_id}")
            return False
        
        rule.name = config.name
        rule.code = config.code
        rule.alert_type = config.alert_type
        rule.operator = config.operator
        rule.threshold = Decimal(str(config.threshold))
        rule.threshold_secondary = Decimal(str(config.threshold_secondary)) if config.threshold_secondary else None
        rule.condition_config = json.dumps(config.condition_config) if config.condition_config else None
        rule.notify_popup = config.notify_popup
        rule.notify_sound = config.notify_sound
        
        return self.rule_repo.save(rule)
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除预警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功
        """
        return self.rule_repo.delete(rule_id)
    
    def get_rules(self, code: str = None, active_only: bool = True) -> List[Dict]:
        """
        获取预警规则
        
        Args:
            code: 股票代码，None则获取所有
            active_only: 仅返回启用的规则
            
        Returns:
            规则列表
        """
        if code:
            rules = self.rule_repo.get_by_code(code, active_only)
        else:
            rules = self.rule_repo.get_all_active() if active_only else []
        
        return [self._rule_to_dict(r) for r in rules]
    
    def _rule_to_dict(self, rule: AlertRule) -> Dict:
        """规则转换为字典"""
        import json
        return {
            'id': rule.id,
            'name': rule.name,
            'code': rule.code,
            'alert_type': rule.alert_type,
            'operator': rule.operator,
            'threshold': float(rule.threshold) if rule.threshold else None,
            'threshold_secondary': float(rule.threshold_secondary) if rule.threshold_secondary else None,
            'condition_config': json.loads(rule.condition_config) if rule.condition_config else {},
            'is_active': rule.is_active,
            'is_triggered': rule.is_triggered,
            'trigger_count': rule.trigger_count,
            'last_triggered_at': rule.last_triggered_at.strftime('%Y-%m-%d %H:%M:%S') if rule.last_triggered_at else None
        }
    
    def start(self):
        """启动预警监控"""
        if self._running:
            logger.warning("预警引擎已在运行")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("预警引擎已启动")
    
    def stop(self):
        """停止预警监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("预警引擎已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                self.check_alerts()
            except Exception as e:
                logger.error(f"预警检查异常: {e}")
            
            time.sleep(self.check_interval)
    
    def check_alerts(self):
        """检查预警触发"""
        # 获取所有启用的规则
        rules = self.rule_repo.get_all_active()
        
        for rule in rules:
            try:
                # 检查是否满足冷却时间（同一规则5分钟内不重复触发）
                if rule.id in self._last_check:
                    elapsed = (datetime.now() - self._last_check[rule.id]).total_seconds()
                    if elapsed < 300:  # 5分钟冷却
                        continue
                
                # 获取最新行情
                quote = self._get_quote(rule.code)
                if not quote:
                    continue
                
                # 检查是否触发
                triggered, trigger_value = self._check_rule(rule, quote)
                
                if triggered:
                    self._trigger_alert(rule, quote, trigger_value)
                    self._last_check[rule.id] = datetime.now()
                    
            except Exception as e:
                logger.error(f"检查规则 {rule.id} 异常: {e}")
    
    def _get_quote(self, code: str) -> Optional[Quote]:
        """获取行情数据"""
        # 优先从缓存获取
        if code in self._quote_cache:
            return self._quote_cache[code]
        
        # 从数据库获取
        quote = self.quote_repo.get_latest(code)
        if quote:
            self._quote_cache[code] = quote
        
        return quote
    
    def _check_rule(self, rule: AlertRule, quote: Quote) -> tuple:
        """
        检查规则是否触发
        
        Returns:
            (是否触发, 触发值)
        """
        threshold = float(rule.threshold)
        operator = rule.operator
        alert_type = rule.alert_type
        
        # 获取检查值
        if alert_type == 'price':
            current_value = float(quote.close) if quote.close else 0
        elif alert_type == 'change':
            current_value = float(quote.change_pct) if quote.change_pct else 0
        elif alert_type == 'volume':
            current_value = float(quote.volume) if quote.volume else 0
        else:
            return False, 0
        
        # 判断条件
        if operator == 'above':
            triggered = current_value > threshold
        elif operator == 'below':
            triggered = current_value < threshold
        elif operator == 'between':
            threshold2 = float(rule.threshold_secondary) if rule.threshold_secondary else threshold
            triggered = threshold <= current_value <= threshold2
        elif operator == 'cross_up':
            # 需要历史数据判断是否上穿
            triggered = False  # 简化处理
        elif operator == 'cross_down':
            triggered = False  # 简化处理
        else:
            triggered = False
        
        return triggered, current_value
    
    def _trigger_alert(self, rule: AlertRule, quote: Quote, trigger_value: float):
        """触发预警"""
        # 生成预警消息
        message = self._generate_message(rule, quote, trigger_value)
        
        # 保存预警记录
        record = AlertRecord(
            rule_id=rule.id,
            code=rule.code,
            trigger_price=float(quote.close) if quote.close else 0,
            trigger_value=trigger_value,
            message=message,
            is_read=False
        )
        self.record_repo.save(record)
        
        # 更新规则状态
        self.rule_repo.update_trigger_status(rule.id, True)
        
        # 发送通知
        notification = AlertNotification(
            rule_id=rule.id,
            code=rule.code,
            trigger_price=float(quote.close) if quote.close else 0,
            trigger_value=trigger_value,
            message=message,
            timestamp=datetime.now()
        )
        
        self._send_notification(notification, rule)
        
        # 发布事件
        event_bus.publish('alert.triggered', {
            'rule_id': rule.id,
            'code': rule.code,
            'message': message
        })
        
        logger.info(f"预警触发: {rule.name} - {message}")
    
    def _generate_message(self, rule: AlertRule, quote: Quote, 
                          trigger_value: float) -> str:
        """生成预警消息"""
        operator_desc = {
            'above': '突破',
            'below': '跌破',
            'between': '进入区间',
            'cross_up': '上穿',
            'cross_down': '下穿'
        }
        
        type_desc = {
            'price': '价格',
            'change': '涨跌幅',
            'volume': '成交量'
        }
        
        op = operator_desc.get(rule.operator, rule.operator)
        type_name = type_desc.get(rule.alert_type, rule.alert_type)
        
        return f"{rule.code} {type_name}{op}{float(rule.threshold):.2f}，当前{trigger_value:.2f}"
    
    def _send_notification(self, notification: AlertNotification, rule: AlertRule):
        """发送通知"""
        # 调用注册的回调函数
        for callback in self._callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"通知回调异常: {e}")
        
        # 弹窗通知
        if rule.notify_popup:
            event_bus.publish('alert.popup', {
                'title': f"股票预警: {rule.code}",
                'message': notification.message
            })
        
        # 声音通知
        if rule.notify_sound:
            event_bus.publish('alert.sound', {})
    
    def register_callback(self, callback: Callable):
        """
        注册预警回调函数
        
        Args:
            callback: 回调函数，接收AlertNotification参数
        """
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable):
        """注销回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_alert_history(self, rule_id: int = None, limit: int = 100) -> List[Dict]:
        """
        获取预警历史
        
        Args:
            rule_id: 规则ID，None则获取所有
            limit: 限制数量
            
        Returns:
            预警记录列表
        """
        if rule_id:
            records = self.record_repo.get_by_rule(rule_id, limit)
        else:
            # 获取所有记录（简化实现）
            records = []
        
        return [self._record_to_dict(r) for r in records]
    
    def _record_to_dict(self, record: AlertRecord) -> Dict:
        """记录转换为字典"""
        return {
            'id': record.id,
            'rule_id': record.rule_id,
            'code': record.code,
            'trigger_price': record.trigger_price,
            'trigger_value': record.trigger_value,
            'message': record.message,
            'is_read': record.is_read,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else None
        }
    
    def get_unread_count(self) -> int:
        """获取未读预警数量"""
        return self.record_repo.get_count(unread_only=True)
    
    def mark_as_read(self, record_id: int) -> bool:
        """标记预警为已读"""
        return self.record_repo.mark_as_read(record_id)
    
    def mark_all_as_read(self) -> int:
        """标记所有预警为已读"""
        return self.record_repo.mark_all_as_read()
    
    def update_quote_cache(self, code: str, quote: Quote):
        """更新行情缓存"""
        self._quote_cache[code] = quote
