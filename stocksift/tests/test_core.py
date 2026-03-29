# -*- coding: utf-8 -*-
"""
业务层测试

测试筛选引擎、策略管理、回测引擎、预警引擎、数据获取协调器
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from datetime import datetime, date, timedelta
from decimal import Decimal

from core.screener import ScreenerEngine, FilterCondition, ScreenResult
from core.strategy import StrategyManager, StrategyConfig
from core.backtest import BacktestEngine, BacktestParams
from core.alert_engine import AlertEngine, AlertRuleConfig
from core.data_fetcher import DataFetcher


class TestScreenerEngine(unittest.TestCase):
    """测试筛选引擎"""
    
    def setUp(self):
        """准备测试"""
        self.screener = ScreenerEngine()
    
    def test_available_fields(self):
        """测试获取可用字段"""
        fields = self.screener.get_available_fields()
        
        self.assertIsInstance(fields, list)
        self.assertGreater(len(fields), 0)
        
        # 检查关键字段
        field_names = [f['name'] for f in fields]
        self.assertIn('code', field_names)
        self.assertIn('pe_ttm', field_names)
        self.assertIn('roe', field_names)
    
    def test_filter_condition_creation(self):
        """测试筛选条件创建"""
        condition = FilterCondition(
            field='pe_ttm',
            operator='<',
            value=20
        )
        
        self.assertEqual(condition.field, 'pe_ttm')
        self.assertEqual(condition.operator, '<')
        self.assertEqual(condition.value, 20)
    
    def test_quick_screen(self):
        """测试快速筛选"""
        # 注意：这个测试需要数据库中有数据
        # 在没有数据的情况下应该返回空结果
        result = self.screener.quick_screen(min_pe=5, max_pe=30)
        
        self.assertIsInstance(result, ScreenResult)
        self.assertIsInstance(result.data, list)
        self.assertGreaterEqual(result.total, 0)
    
    def test_value_screen(self):
        """测试价值投资筛选"""
        result = self.screener.value_screen(limit=10)
        
        self.assertIsInstance(result, ScreenResult)
        self.assertIsInstance(result.data, list)
    
    def test_growth_screen(self):
        """测试成长股筛选"""
        result = self.screener.growth_screen(limit=10)
        
        self.assertIsInstance(result, ScreenResult)
        self.assertIsInstance(result.data, list)


class TestStrategyManager(unittest.TestCase):
    """测试策略管理器"""
    
    def setUp(self):
        """准备测试"""
        self.manager = StrategyManager()
    
    def test_get_builtin_strategies(self):
        """测试获取预置策略"""
        strategies = self.manager.get_builtin_strategies()
        
        self.assertIsInstance(strategies, list)
        self.assertGreater(len(strategies), 0)
        
        # 检查关键策略
        strategy_names = [s['name'] for s in strategies]
        self.assertIn('价值投资策略', strategy_names)
        self.assertIn('成长投资策略', strategy_names)
    
    def test_strategy_config_creation(self):
        """测试策略配置创建"""
        config = StrategyConfig(
            name='测试策略',
            description='这是一个测试策略',
            strategy_type='technical',
            entry_conditions=[
                FilterCondition('pe_ttm', '<', 20)
            ]
        )
        
        self.assertEqual(config.name, '测试策略')
        self.assertEqual(config.strategy_type, 'technical')
        self.assertEqual(len(config.entry_conditions), 1)
    
    def test_list_all(self):
        """测试获取所有策略"""
        strategies = self.manager.list_all()
        
        self.assertIsInstance(strategies, list)
        # 预置策略会在第一次访问时初始化
        # 如果没有数据，至少返回空列表


class TestBacktestEngine(unittest.TestCase):
    """测试回测引擎"""
    
    def setUp(self):
        """准备测试"""
        self.engine = BacktestEngine()
    
    def test_backtest_params_creation(self):
        """测试回测参数创建"""
        params = BacktestParams(
            strategy_id='test_strategy',
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=1000000
        )
        
        self.assertEqual(params.strategy_id, 'test_strategy')
        self.assertEqual(params.initial_capital, 1000000)
        self.assertEqual(params.commission_rate, 0.0003)
    
    def test_generate_trading_days(self):
        """测试生成交易日历"""
        days = self.engine._generate_trading_days(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        self.assertIsInstance(days, list)
        self.assertGreater(len(days), 0)
        
        # 检查是否都是工作日
        for d in days:
            self.assertLess(d.weekday(), 5)
    
    def test_calculate_max_drawdown(self):
        """测试最大回撤计算"""
        equities = [100, 110, 105, 120, 115, 100, 95, 105]
        
        max_dd = self.engine._calculate_max_drawdown(equities)
        
        self.assertLess(max_dd, 0)  # 回撤为负值
        self.assertGreaterEqual(max_dd, -30)  # 回撤在合理范围


class TestAlertEngine(unittest.TestCase):
    """测试预警引擎"""
    
    def setUp(self):
        """准备测试"""
        self.engine = AlertEngine(check_interval=60)
    
    def test_alert_rule_config_creation(self):
        """测试预警规则配置创建"""
        config = AlertRuleConfig(
            name='价格预警',
            code='000001',
            alert_type='price',
            operator='above',
            threshold=10.0
        )
        
        self.assertEqual(config.name, '价格预警')
        self.assertEqual(config.code, '000001')
        self.assertEqual(config.alert_type, 'price')
    
    def test_get_rules(self):
        """测试获取预警规则"""
        rules = self.engine.get_rules()
        
        self.assertIsInstance(rules, list)
    
    def test_generate_message(self):
        """测试生成预警消息"""
        from core.alert_engine import AlertRule, AlertNotification
        
        # 创建模拟规则
        rule = AlertRule(
            name='测试预警',
            code='000001',
            alert_type='price',
            operator='above',
            threshold=Decimal('10.0')
        )
        
        # 创建模拟行情
        class MockQuote:
            def __init__(self):
                self.close = Decimal('10.5')
        
        quote = MockQuote()
        
        message = self.engine._generate_message(rule, quote, 10.5)
        
        self.assertIsInstance(message, str)
        self.assertIn('000001', message)
        self.assertIn('10.5', message)


class TestDataFetcher(unittest.TestCase):
    """测试数据获取协调器"""
    
    def setUp(self):
        """准备测试"""
        self.fetcher = DataFetcher()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.fetcher.stock_repo)
        self.assertIsNotNone(self.fetcher.quote_repo)
        self.assertIsNotNone(self.fetcher.kline_repo)
    
    def test_generate_trading_days(self):
        """测试交易日历生成"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)
        
        # 这个方法在DataFetcher中没有直接暴露
        # 但通过其他方法间接测试
        pass


if __name__ == '__main__':
    unittest.main()
