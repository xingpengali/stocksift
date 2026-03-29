# -*- coding: utf-8 -*-
"""
行情数据模型测试
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models.database import get_db_manager, reset_db_manager
from models.quote import Quote, QuoteRepository


class TestQuote(unittest.TestCase):
    """测试Quote模型"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_quote.db")
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
    
    def test_create_quote(self):
        """测试创建行情对象"""
        quote = Quote(
            code='000001',
            price=Decimal('12.50'),
            pre_close=Decimal('12.00'),
            open=Decimal('12.10'),
            high=Decimal('12.80'),
            low=Decimal('11.90'),
            change=Decimal('0.50'),
            change_pct=Decimal('4.17'),
            volume=1000000,
            amount=Decimal('12500000.00'),
            pe_ttm=Decimal('8.50'),
            pb=Decimal('0.85'),
            quote_time=datetime(2024, 1, 15, 15, 0, 0)
        )
        
        self.assertEqual(quote.code, '000001')
        self.assertEqual(float(quote.price), 12.50)
        self.assertEqual(float(quote.change_pct), 4.17)
    
    def test_quote_repr(self):
        """测试行情对象的字符串表示"""
        quote = Quote(code='000001', price=Decimal('12.50'))
        repr_str = repr(quote)
        self.assertIn('000001', repr_str)
        self.assertIn('12.50', repr_str)
    
    def test_to_dict(self):
        """测试转换为字典"""
        quote = Quote(
            code='000001',
            price=Decimal('12.50'),
            pre_close=Decimal('12.00'),
            change=Decimal('0.50'),
            change_pct=Decimal('4.17'),
            volume=1000000,
            amount=Decimal('12500000.00'),
            bid5_data='[[12.49, 1000], [12.48, 2000]]',
            ask5_data='[[12.51, 1500], [12.52, 3000]]',
            pe_ttm=Decimal('8.50'),
            quote_time=datetime(2024, 1, 15, 15, 0, 0)
        )
        
        data = quote.to_dict()
        
        self.assertEqual(data['code'], '000001')
        self.assertEqual(data['price'], 12.50)
        self.assertEqual(data['change_pct'], 4.17)
        self.assertEqual(data['volume'], 1000000)
        self.assertEqual(data['bid5'], [[12.49, 1000], [12.48, 2000]])
        self.assertEqual(data['ask5'], [[12.51, 1500], [12.52, 3000]])
        self.assertEqual(data['quote_time'], '2024-01-15 15:00:00')
    
    def test_to_dict_none_values(self):
        """测试空值处理"""
        quote = Quote(code='000001')
        data = quote.to_dict()
        
        self.assertIsNone(data['price'])
        self.assertIsNone(data['pe_ttm'])
        self.assertEqual(data['bid5'], [])
        self.assertEqual(data['ask5'], [])


class TestQuoteRepository(unittest.TestCase):
    """测试QuoteRepository"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_quote_repo.db")
        self.db_manager = get_db_manager(self.db_path)
        self.db_manager.init_db()
        self.repo = QuoteRepository()
    
    def tearDown(self):
        """测试后清理"""
        if self.db_manager:
            self.db_manager.close()
        reset_db_manager()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def _create_test_quote(self, code, price=None, change_pct=None, amount=None, **kwargs):
        """辅助方法：创建测试行情"""
        quote = Quote(
            code=code,
            price=Decimal(str(price)) if price else None,
            pre_close=kwargs.get('pre_close'),
            change_pct=Decimal(str(change_pct)) if change_pct else None,
            volume=kwargs.get('volume'),
            amount=Decimal(str(amount)) if amount else None,
            quote_time=kwargs.get('quote_time', datetime.now())
        )
        return quote
    
    def test_save(self):
        """测试保存行情"""
        quote = self._create_test_quote('000001', price=12.50)
        result = self.repo.save(quote)
        
        self.assertTrue(result)
        
        # 验证保存成功
        saved = self.repo.get_by_code('000001')
        self.assertIsNotNone(saved)
        self.assertEqual(float(saved.price), 12.50)
    
    def test_save_update(self):
        """测试更新行情"""
        # 先保存
        quote = self._create_test_quote('000001', price=12.50)
        self.repo.save(quote)
        
        # 更新
        quote2 = self._create_test_quote('000001', price=13.00)
        result = self.repo.save(quote2)
        
        self.assertTrue(result)
        
        # 验证更新
        updated = self.repo.get_by_code('000001')
        self.assertEqual(float(updated.price), 13.00)
    
    def test_save_batch(self):
        """测试批量保存"""
        quotes = [
            self._create_test_quote('000001', price=12.50),
            self._create_test_quote('000002', price=15.00),
            self._create_test_quote('000003', price=8.80)
        ]
        
        count = self.repo.save_batch(quotes)
        self.assertEqual(count, 3)
        
        # 验证
        all_quotes = self.repo.get_all()
        self.assertEqual(len(all_quotes), 3)
    
    def test_get_by_code(self):
        """测试根据代码获取行情"""
        quote = self._create_test_quote('000001', price=12.50)
        self.repo.save(quote)
        
        result = self.repo.get_by_code('000001')
        self.assertIsNotNone(result)
        self.assertEqual(float(result.price), 12.50)
    
    def test_get_by_code_not_found(self):
        """测试获取不存在的行情"""
        result = self.repo.get_by_code('999999')
        self.assertIsNone(result)
    
    def test_get_by_codes(self):
        """测试批量获取行情"""
        quotes = [
            self._create_test_quote('000001', price=12.50),
            self._create_test_quote('000002', price=15.00),
            self._create_test_quote('000003', price=8.80)
        ]
        self.repo.save_batch(quotes)
        
        results = self.repo.get_by_codes(['000001', '000002'])
        self.assertEqual(len(results), 2)
        codes = [q.code for q in results]
        self.assertIn('000001', codes)
        self.assertIn('000002', codes)
    
    def test_get_by_codes_empty(self):
        """测试空列表获取"""
        results = self.repo.get_by_codes([])
        self.assertEqual(len(results), 0)
    
    def test_get_all(self):
        """测试获取所有行情"""
        quotes = [
            self._create_test_quote('000001', price=12.50),
            self._create_test_quote('000002', price=15.00)
        ]
        self.repo.save_batch(quotes)
        
        results = self.repo.get_all()
        self.assertEqual(len(results), 2)
    
    def test_get_top_gainers(self):
        """测试获取涨幅榜"""
        quotes = [
            self._create_test_quote('000001', price=12.50, change_pct=5.5),
            self._create_test_quote('000002', price=15.00, change_pct=10.0),
            self._create_test_quote('000003', price=8.80, change_pct=2.5)
        ]
        self.repo.save_batch(quotes)
        
        results = self.repo.get_top_gainers(limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(float(results[0].change_pct), 10.0)  # 涨幅最高的在前
        self.assertEqual(float(results[1].change_pct), 5.5)
    
    def test_get_top_losers(self):
        """测试获取跌幅榜"""
        quotes = [
            self._create_test_quote('000001', price=12.50, change_pct=-5.5),
            self._create_test_quote('000002', price=15.00, change_pct=-10.0),
            self._create_test_quote('000003', price=8.80, change_pct=2.5)
        ]
        self.repo.save_batch(quotes)
        
        results = self.repo.get_top_losers(limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(float(results[0].change_pct), -10.0)  # 跌幅最大的在前
        self.assertEqual(float(results[1].change_pct), -5.5)
    
    def test_get_most_active(self):
        """测试获取活跃榜"""
        quotes = [
            self._create_test_quote('000001', price=12.50, amount=1000000),
            self._create_test_quote('000002', price=15.00, amount=5000000),
            self._create_test_quote('000003', price=8.80, amount=2000000)
        ]
        self.repo.save_batch(quotes)
        
        results = self.repo.get_most_active(limit=2)
        self.assertEqual(len(results), 2)
        # 按成交额排序
        amounts = [float(q.amount) for q in results]
        self.assertEqual(amounts[0], 5000000.0)
        self.assertEqual(amounts[1], 2000000.0)


if __name__ == '__main__':
    unittest.main()
