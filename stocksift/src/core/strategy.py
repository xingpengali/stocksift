# -*- coding: utf-8 -*-
"""
策略管理模块

实现策略定义、管理和执行
"""
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime

from sqlalchemy.orm import Session

from models.database import get_db_manager
from models.strategy import Strategy, StrategyRepository
from core.screener import ScreenerEngine, FilterCondition, ScreenResult
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    description: str = ""
    strategy_type: str = "technical"  # technical/fundamental/combined
    
    # 筛选条件
    entry_conditions: List[FilterCondition] = field(default_factory=list)
    exit_conditions: List[FilterCondition] = field(default_factory=list)
    
    # 策略参数
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 持仓设置
    max_positions: int = 10
    position_size: float = 0.1  # 单个仓位比例
    
    # 止损止盈
    stop_loss: float = 0.08  # 止损比例
    take_profit: float = 0.15  # 止盈比例
    
    # 再平衡周期
    rebalance_days: int = 20


class StrategyManager:
    """
    策略管理器
    
    管理选股策略的CRUD和执行
    """
    
    # 预置策略模板
    BUILTIN_STRATEGIES = {
        'value_strategy': {
            'name': '价值投资策略',
            'description': '低PE、低PB、高ROE的经典价值投资',
            'strategy_type': 'fundamental',
            'entry_conditions': [
                {'field': 'pe_ttm', 'operator': 'between', 'value': 5, 'value2': 25},
                {'field': 'pb', 'operator': '<=', 'value': 3},
                {'field': 'roe', 'operator': '>=', 'value': 10},
            ],
            'parameters': {'sort_by': 'roe', 'ascending': False}
        },
        'growth_strategy': {
            'name': '成长投资策略',
            'description': '高营收增长、高利润增长',
            'strategy_type': 'fundamental',
            'entry_conditions': [
                {'field': 'revenue_growth', 'operator': '>=', 'value': 20},
                {'field': 'profit_growth', 'operator': '>=', 'value': 20},
                {'field': 'pe_ttm', 'operator': '<=', 'value': 50},
            ],
            'parameters': {'sort_by': 'profit_growth', 'ascending': False}
        },
        'technical_breakout': {
            'name': '技术突破策略',
            'description': '股价突破均线、成交量放大',
            'strategy_type': 'technical',
            'entry_conditions': [
                {'field': 'price', 'operator': '>=', 'value': 0},
                {'field': 'turnover', 'operator': '>=', 'value': 3},
            ],
            'parameters': {'ma_period': 20, 'volume_ratio': 2}
        },
        'dividend_strategy': {
            'name': '高分红策略',
            'description': '选择稳定分红、低估值的股票',
            'strategy_type': 'fundamental',
            'entry_conditions': [
                {'field': 'pe_ttm', 'operator': 'between', 'value': 5, 'value2': 20},
                {'field': 'pb', 'operator': '<=', 'value': 2},
                {'field': 'roe', 'operator': '>=', 'value': 8},
            ],
            'parameters': {'sort_by': 'pe_ttm', 'ascending': True}
        },
        'low_debt_strategy': {
            'name': '低负债策略',
            'description': '选择财务稳健、低负债的公司',
            'strategy_type': 'fundamental',
            'entry_conditions': [
                {'field': 'debt_ratio', 'operator': '<=', 'value': 40},
                {'field': 'current_ratio', 'operator': '>=', 'value': 1.5},
                {'field': 'roe', 'operator': '>=', 'value': 8},
            ],
            'parameters': {'sort_by': 'debt_ratio', 'ascending': True}
        }
    }
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化
        
        Args:
            session: 数据库会话
        """
        self.session = session
        self._use_external_session = session is not None
        self.repo = StrategyRepository(session)
        self.screener = ScreenerEngine(session)
        
        # 初始化预置策略
        self._init_builtin_strategies()
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session is None:
            return get_db_manager().get_session()
        return self.session
    
    def _init_builtin_strategies(self):
        """初始化预置策略到数据库"""
        for strategy_id, config in self.BUILTIN_STRATEGIES.items():
            existing = self.repo.get_by_id(strategy_id)
            if not existing:
                strategy = Strategy(
                    id=strategy_id,
                    name=config['name'],
                    description=config['description'],
                    strategy_type=config['strategy_type'],
                    config=json.dumps(config['entry_conditions']),
                    params=json.dumps(config['parameters']),
                    is_active=True,
                    is_default=(strategy_id == 'value_strategy')
                )
                self.repo.save(strategy)
                logger.info(f"初始化预置策略: {config['name']}")
    
    def create(self, config: StrategyConfig) -> str:
        """
        创建策略
        
        Args:
            config: 策略配置
            
        Returns:
            策略ID
        """
        strategy_id = str(uuid.uuid4())[:8]
        
        strategy = Strategy(
            id=strategy_id,
            name=config.name,
            description=config.description,
            strategy_type=config.strategy_type,
            config=json.dumps([self._condition_to_dict(c) for c in config.entry_conditions]),
            params=json.dumps(config.parameters),
            is_active=True,
            is_default=False
        )
        
        if self.repo.save(strategy):
            logger.info(f"创建策略成功: {config.name} (ID: {strategy_id})")
            return strategy_id
        else:
            raise Exception("创建策略失败")
    
    def update(self, strategy_id: str, config: StrategyConfig) -> bool:
        """
        更新策略
        
        Args:
            strategy_id: 策略ID
            config: 策略配置
            
        Returns:
            是否成功
        """
        strategy = self.repo.get_by_id(strategy_id)
        if not strategy:
            logger.warning(f"策略不存在: {strategy_id}")
            return False
        
        strategy.name = config.name
        strategy.description = config.description
        strategy.strategy_type = config.strategy_type
        strategy.config = json.dumps([self._condition_to_dict(c) for c in config.entry_conditions])
        strategy.params = json.dumps(config.parameters)
        strategy.updated_at = datetime.now()
        
        return self.repo.save(strategy)
    
    def delete(self, strategy_id: str) -> bool:
        """
        删除策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功
        """
        return self.repo.delete(strategy_id)
    
    def get(self, strategy_id: str) -> Optional[StrategyConfig]:
        """
        获取策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略配置
        """
        strategy = self.repo.get_by_id(strategy_id)
        if not strategy:
            return None
        
        return self._strategy_to_config(strategy)
    
    def list_all(self, active_only: bool = True) -> List[Dict]:
        """
        获取所有策略
        
        Args:
            active_only: 仅返回启用的策略
            
        Returns:
            策略列表
        """
        strategies = self.repo.get_all(active_only)
        return [self._strategy_to_dict(s) for s in strategies]
    
    def run(self, strategy_id: str, limit: int = 50) -> ScreenResult:
        """
        执行策略筛选
        
        Args:
            strategy_id: 策略ID
            limit: 结果限制
            
        Returns:
            筛选结果
        """
        config = self.get(strategy_id)
        if not config:
            raise ValueError(f"策略不存在: {strategy_id}")
        
        # 执行筛选
        result = self.screener.screen(
            config.entry_conditions,
            order_by=config.parameters.get('sort_by'),
            order_desc=not config.parameters.get('ascending', False),
            page=1,
            page_size=limit
        )
        
        logger.info(f"执行策略 [{config.name}]，筛选出 {result.total} 只股票")
        return result
    
    def get_builtin_strategies(self) -> List[Dict]:
        """
        获取预置策略列表
        
        Returns:
            预置策略列表
        """
        return [
            {
                'id': k,
                'name': v['name'],
                'description': v['description'],
                'type': v['strategy_type']
            }
            for k, v in self.BUILTIN_STRATEGIES.items()
        ]
    
    def clone_builtin(self, builtin_id: str, new_name: str = None) -> str:
        """
        克隆预置策略
        
        Args:
            builtin_id: 预置策略ID
            new_name: 新策略名称
            
        Returns:
            新策略ID
        """
        if builtin_id not in self.BUILTIN_STRATEGIES:
            raise ValueError(f"预置策略不存在: {builtin_id}")
        
        builtin = self.BUILTIN_STRATEGIES[builtin_id]
        
        config = StrategyConfig(
            name=new_name or f"{builtin['name']}(副本)",
            description=builtin['description'],
            strategy_type=builtin['strategy_type'],
            entry_conditions=[
                FilterCondition(
                    c['field'], c['operator'], c['value'],
                    c.get('value2'), c.get('logic', 'AND')
                )
                for c in builtin['entry_conditions']
            ],
            parameters=builtin['parameters']
        )
        
        return self.create(config)
    
    def _condition_to_dict(self, condition: FilterCondition) -> Dict:
        """转换条件为字典"""
        return {
            'field': condition.field,
            'operator': condition.operator,
            'value': condition.value,
            'value2': condition.value2,
            'logic': condition.logic
        }
    
    def _dict_to_condition(self, data: Dict) -> FilterCondition:
        """字典转换为条件"""
        return FilterCondition(
            field=data['field'],
            operator=data['operator'],
            value=data['value'],
            value2=data.get('value2'),
            logic=data.get('logic', 'AND')
        )
    
    def _strategy_to_config(self, strategy: Strategy) -> StrategyConfig:
        """策略模型转换为配置"""
        config_data = json.loads(strategy.config) if strategy.config else []
        params_data = json.loads(strategy.params) if strategy.params else {}
        
        return StrategyConfig(
            name=strategy.name,
            description=strategy.description or "",
            strategy_type=strategy.strategy_type or "technical",
            entry_conditions=[self._dict_to_condition(c) for c in config_data],
            parameters=params_data
        )
    
    def _strategy_to_dict(self, strategy: Strategy) -> Dict:
        """策略模型转换为字典"""
        return {
            'id': strategy.id,
            'name': strategy.name,
            'description': strategy.description,
            'strategy_type': strategy.strategy_type,
            'is_active': strategy.is_active,
            'is_default': strategy.is_default,
            'backtest_count': strategy.backtest_count,
            'created_at': strategy.created_at.strftime('%Y-%m-%d %H:%M:%S') if strategy.created_at else None
        }
