# -*- coding: utf-8 -*-
"""
K线数据模型测试
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models.database import get_db_manager, reset_db_manager
from models.kline import Kline, KlineRepository


class TestKline(unittest.TestCase):
    """测试Kline模型"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_kline.db")
        self.db_manager = get_db_manager(self.db_path)
        self.db_manager.init_db()
    
    def tearDown(self):
        """测试后清理"""
        if self.db_manager:
            self.db_manager.close()
        reset_db_manager()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_create_kline(self):
        """测试创建K线对象"""
        kline = Kline(
            code='000001',
            period='daily',
            trade_date=date(2024, 1, 15),
            open=Decimal('12.00'),
            high=Decimal('12.80'),
            low=Decimal('11.90'),
            close=Decimal('12.50'),
            volume=1000000,
            amount=Decimal('12500000.00'),
            change=Decimal('0.50'),
            change_pct=Decimal('4.17'),
            adj_factor=Decimal('1.000000')
        )
        
        self.assertEqual(kline.code, '000001')
        self.assertEqual(kline.period, 'daily')
        self.assertEqual(kline.trade_date, date(2024, 1, 15))
        self.assertEqual(float(kline.close), 12.50)
    
    def test_kline_repr(self):
        """测试K线对象的字符串表示"""
        kline = Kline(code='000001', trade_date=date(2024, 1, 15), close=Decimal('12.50'))
        repr_str = repr(kline)
        self.assertIn('000001', repr_str)
        self.assertIn('12.50', repr_str)
    
    def test_to_dict(self):
        """测试转换为字典"""
        kline = Kline(
            code='000001',
            period='daily',
            trade_date=date(2024, 1, 15),
            open=Decimal('12.00'),
            high=Decimal('12.80'),
            low=Decimal('11.90'),
            close=Decimal('12.50'),
            volume=1000000,
            amount=Decimal('12500000.00'),
            change=Decimal('0.50'),
            change_pct=Decimal('4.17'),
            adj_factor=Decimal('1.000000')
        )
        
        data = kline.to_dict()
        
        self.assertEqual(data['code'], '000001')
        self.assertEqual(data['period'], 'daily')
        self.assertEqual(data['trade_date'], '2024-01-15')
        self.assertEqual(data['open'], 12.00)
        self.assertEqual(data['high'], 12.80)
        self.assertEqual(data['low'], 11.90)
        self.assertEqual(data['close'], 12.50)
        self.assertEqual(data['volume'], 1000000)
        self.assertEqual(data['change_pct'], 4.17)
        self.assertEqual(data['adj_factor'], 1.0)
    
    def test_to_dict_default_adj_factor(self):
        """测试默认复权因子"""
        kline = Kline(code='000001', period='daily', trade_date=date(2024, 1, 15))
        data = kline.to_dict()
        self.assertEqual(data['adj_factor'], 1.0)


class TestKlineRepository(unittest.TestCase):
    """测试KlineRepository"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_kline_repo.db")
        self.db_manager = get_db_manager(self.db_path)
        self.db_manager.init_db()
        self.repo = KlineRepository()
    
    def tearDown(self):
        """测试后清理"""
        if self.db_manager:
            self.db_manager.close()
        reset_db_manager()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def _create_test_kline(self, code, trade_date, period='daily', close=10.0, **kwargs):
        """辅助方法：创建测试K线"""
        kline = Kline(
            code=code,
            period=period,
            trade_date=trade_date,
            open=kwargs.get('open', Decimal(str(close * 0.98))),
            high=kwargs.get('high', Decimal(str(close * 1.02))),
            low=kwargs.get('low', Decimal(str(close * 0.97))),
            close=Decimal(str(close)),
            volume=kwargs.get('volume', 1000000),
            amount=kwargs.get('amount', Decimal('10000000.00'))
        )
        return kline
    
    def test_save(self):
        """测试保存K线"""
        kline = self._create_test_kline('000001', date(2024, 1, 15), close=12.50)
        result = self.repo.save(kline)
        
        self.assertTrue(result)
        
        # 验证保存成功
        saved = self.repo.get_latest('000001')
        self.assertIsNotNone(saved)
        self.assertEqual(float(saved.close), 12.50)
    
    def test_save_update(self):
        """测试更新K线"""
        # 先保存
        kline = self._create_test_kline('000001', date(2024, 1, 15), close=12.50)
        self.repo.save(kline)
        
        # 更新
        kline2 = self._create_test_kline('000001', date(2024, 1, 15), close=13.00)
        result = self.repo.save(kline2)
        
        self.assertTrue(result)
        
        # 验证更新
        updated = self.repo.get_latest('000001')
        self.assertEqual(float(updated.close), 13.00)
    
    def test_save_batch(self):
        """测试批量保存"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15)),
            self._create_test_kline('000001', date(2024, 1, 16)),
            self._create_test_kline('000001', date(2024, 1, 17))
        ]
        
        count = self.repo.save_batch(klines)
        self.assertEqual(count, 3)
    
    def test_get_by_code(self):
        """测试根据代码获取K线"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15)),
            self._create_test_kline('000001', date(2024, 1, 16)),
            self._create_test_kline('000001', date(2024, 1, 17))
        ]
        self.repo.save_batch(klines)
        
        results = self.repo.get_by_code('000001')
        self.assertEqual(len(results), 3)
        # 默认按日期降序
        self.assertEqual(results[0].trade_date, date(2024, 1, 17))
    
    def test_get_by_code_with_date_range(self):
        """测试根据日期范围获取K线"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15)),
            self._create_test_kline('000001', date(2024, 1, 16)),
            self._create_test_kline('000001', date(2024, 1, 17)),
            self._create_test_kline('000001', date(2024, 1, 18))
        ]
        self.repo.save_batch(klines)
        
        results = self.repo.get_by_code(
            '000001',
            start_date=date(2024, 1, 16),
            end_date=date(2024, 1, 17)
        )
        self.assertEqual(len(results), 2)
        dates = [k.trade_date for k in results]
        self.assertIn(date(2024, 1, 16), dates)
        self.assertIn(date(2024, 1, 17), dates)
    
    def test_get_by_code_with_limit(self):
        """测试限制数量获取K线"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15)),
            self._create_test_kline('000001', date(2024, 1, 16)),
            self._create_test_kline('000001', date(2024, 1, 17))
        ]
        self.repo.save_batch(klines)
        
        results = self.repo.get_by_code('000001', limit=2)
        self.assertEqual(len(results), 2)
    
    def test_get_by_code_different_period(self):
        """测试不同周期的K线"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15), period='daily'),
            self._create_test_kline('000001', date(2024, 1, 15), period='weekly'),
            self._create_test_kline('000001', date(2024, 1, 15), period='monthly')
        ]
        self.repo.save_batch(klines)
        
        daily = self.repo.get_by_code('000001', period='daily')
        weekly = self.repo.get_by_code('000001', period='weekly')
        monthly = self.repo.get_by_code('000001', period='monthly')
        
        self.assertEqual(len(daily), 1)
        self.assertEqual(len(weekly), 1)
        self.assertEqual(len(monthly), 1)
        
        self.assertEqual(daily[0].period, 'daily')
        self.assertEqual(weekly[0].period, 'weekly')
        self.assertEqual(monthly[0].period, 'monthly')
    
    def test_get_latest(self):
        """测试获取最新K线"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15)),
            self._create_test_kline('000001', date(2024, 1, 16)),
            self._create_test_kline('000001', date(2024, 1, 17))
        ]
        self.repo.save_batch(klines)
        
        latest = self.repo.get_latest('000001')
        self.assertIsNotNone(latest)
        self.assertEqual(latest.trade_date, date(2024, 1, 17))
    
    def test_get_latest_not_found(self):
        """测试获取不存在的最新K线"""
        latest = self.repo.get_latest('999999')
        self.assertIsNone(latest)
    
    def test_get_date_range(self):
        """测试获取K线日期范围"""
        klines = [
            self._create_test_kline('000001', date(2024, 1, 15)),
            self._create_test_kline('000001', date(2024, 1, 16)),
            self._create_test_kline('000001', date(2024, 1, 17))
        ]
        self.repo.save_batch(klines)
        
        min_date, max_date = self.repo.get_date_range('000001')
        self.assertEqual(min_date, date(2024, 1, 15))
        self.assertEqual(max_date, date(2024, 1, 17))
    
    def test_get_date_range_not_found(self):
        """测试获取不存在股票的日期范围"""
        min_date, max_date = self.repo.get_date_range('999999')
        self.assertIsNone(min_date)
        self.assertIsNone(max_date)


if __name__ == '__main__':
    unittest.main()
