# -*- coding: utf-8 -*-
"""
股票模型测试
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, date
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models.database import get_db_manager, reset_db_manager
from models.stock import Stock, StockRepository


class TestStock(unittest.TestCase):
    """测试Stock模型"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stock.db")
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
    
    def test_create_stock(self):
        """测试创建股票对象"""
        stock = Stock(
            code='000001',
            name='平安银行',
            exchange='SZSE',
            market_type='main',
            industry_code='J01',
            industry_name='银行',
            concept_list='["银行", "金融"]',
            province='广东',
            city='深圳',
            list_date=date(1991, 4, 3),
            total_shares=19405918000,
            float_shares=19405841800,
            is_active=1
        )
        
        self.assertEqual(stock.code, '000001')
        self.assertEqual(stock.name, '平安银行')
        self.assertEqual(stock.exchange, 'SZSE')
        self.assertEqual(stock.market_type, 'main')
    
    def test_stock_repr(self):
        """测试股票对象的字符串表示"""
        stock = Stock(code='000001', name='平安银行', exchange='SZSE')
        repr_str = repr(stock)
        self.assertIn('000001', repr_str)
        self.assertIn('平安银行', repr_str)
    
    def test_to_dict(self):
        """测试转换为字典"""
        stock = Stock(
            code='000001',
            name='平安银行',
            exchange='SZSE',
            concept_list='["银行"]',
            list_date=date(1991, 4, 3)
        )
        
        data = stock.to_dict()
        
        self.assertEqual(data['code'], '000001')
        self.assertEqual(data['name'], '平安银行')
        self.assertEqual(data['exchange'], 'SZSE')
        self.assertEqual(data['concept_list'], ['银行'])
        self.assertEqual(data['list_date'], '1991-04-03')
        self.assertIsInstance(data['is_active'], bool)
    
    def test_to_dict_empty_concept(self):
        """测试空概念列表转换"""
        stock = Stock(code='000001', name='测试', exchange='SZSE')
        data = stock.to_dict()
        self.assertEqual(data['concept_list'], [])
    
    def test_from_dict(self):
        """测试从字典创建对象"""
        data = {
            'code': '000001',
            'name': '平安银行',
            'exchange': 'SZSE',
            'market_type': 'main',
            'industry_code': 'J01',
            'industry_name': '银行',
            'concept_list': ['银行', '金融'],
            'province': '广东',
            'city': '深圳',
            'list_date': '1991-04-03',
            'total_shares': 19405918000,
            'float_shares': 19405841800,
            'is_active': True
        }
        
        stock = Stock.from_dict(data)
        
        self.assertEqual(stock.code, '000001')
        self.assertEqual(stock.name, '平安银行')
        self.assertEqual(stock.concept_list, '["银行", "金融"]')
        self.assertEqual(stock.list_date, date(1991, 4, 3))
        self.assertEqual(stock.is_active, 1)
    
    def test_from_dict_string_concept(self):
        """测试概念列表为字符串的情况"""
        data = {
            'code': '000001',
            'name': '测试',
            'exchange': 'SZSE',
            'concept_list': '银行,金融'
        }
        
        stock = Stock.from_dict(data)
        self.assertEqual(stock.concept_list, '银行,金融')
    
    def test_from_dict_invalid_date(self):
        """测试无效日期处理"""
        data = {
            'code': '000001',
            'name': '测试',
            'exchange': 'SZSE',
            'list_date': 'invalid-date'
        }
        
        stock = Stock.from_dict(data)
        self.assertIsNone(stock.list_date)


class TestStockRepository(unittest.TestCase):
    """测试StockRepository"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_repo.db")
        self.db_manager = get_db_manager(self.db_path)
        self.db_manager.init_db()
        self.repo = StockRepository()
    
    def tearDown(self):
        """测试后清理"""
        if self.db_manager:
            self.db_manager.close()
        reset_db_manager()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def _create_test_stock(self, code, name, **kwargs):
        """辅助方法：创建测试股票"""
        stock = Stock(
            code=code,
            name=name,
            exchange=kwargs.get('exchange', 'SZSE'),
            market_type=kwargs.get('market_type', 'main'),
            industry_code=kwargs.get('industry_code'),
            industry_name=kwargs.get('industry_name'),
            is_active=kwargs.get('is_active', 1)
        )
        return stock
    
    def test_save(self):
        """测试保存股票"""
        stock = self._create_test_stock('000001', '平安银行')
        result = self.repo.save(stock)
        
        self.assertTrue(result)
        
        # 验证保存成功
        saved = self.repo.get_by_code('000001')
        self.assertIsNotNone(saved)
        self.assertEqual(saved.name, '平安银行')
    
    def test_save_update(self):
        """测试更新股票"""
        # 先保存
        stock = self._create_test_stock('000001', '平安银行')
        self.repo.save(stock)
        
        # 更新
        stock2 = self._create_test_stock('000001', '平安银行新版')
        result = self.repo.save(stock2)
        
        self.assertTrue(result)
        
        # 验证更新
        updated = self.repo.get_by_code('000001')
        self.assertEqual(updated.name, '平安银行新版')
    
    def test_save_batch(self):
        """测试批量保存"""
        stocks = [
            self._create_test_stock('000001', '平安银行'),
            self._create_test_stock('000002', '万科A'),
            self._create_test_stock('000003', '国农科技')
        ]
        
        count = self.repo.save_batch(stocks)
        self.assertEqual(count, 3)
        
        # 验证
        self.assertEqual(self.repo.get_count(), 3)
    
    def test_get_by_code(self):
        """测试根据代码获取股票"""
        stock = self._create_test_stock('000001', '平安银行')
        self.repo.save(stock)
        
        result = self.repo.get_by_code('000001')
        self.assertIsNotNone(result)
        self.assertEqual(result.name, '平安银行')
    
    def test_get_by_code_not_found(self):
        """测试获取不存在的股票"""
        result = self.repo.get_by_code('999999')
        self.assertIsNone(result)
    
    def test_get_by_code_inactive(self):
        """测试获取已删除的股票"""
        stock = self._create_test_stock('000001', '平安银行', is_active=0)
        self.repo.save(stock)
        
        result = self.repo.get_by_code('000001')
        self.assertIsNone(result)  # 软删除的股票不应被获取
    
    def test_get_by_codes(self):
        """测试批量获取股票"""
        stocks = [
            self._create_test_stock('000001', '平安银行'),
            self._create_test_stock('000002', '万科A'),
            self._create_test_stock('000003', '国农科技')
        ]
        self.repo.save_batch(stocks)
        
        results = self.repo.get_by_codes(['000001', '000002'])
        self.assertEqual(len(results), 2)
        codes = [s.code for s in results]
        self.assertIn('000001', codes)
        self.assertIn('000002', codes)
    
    def test_get_by_codes_empty(self):
        """测试空列表获取"""
        results = self.repo.get_by_codes([])
        self.assertEqual(len(results), 0)
    
    def test_get_all(self):
        """测试获取所有股票"""
        stocks = [
            self._create_test_stock('000001', '平安银行'),
            self._create_test_stock('000002', '万科A')
        ]
        self.repo.save_batch(stocks)
        
        results = self.repo.get_all()
        self.assertEqual(len(results), 2)
    
    def test_get_all_include_inactive(self):
        """测试获取包括非活跃的股票"""
        stocks = [
            self._create_test_stock('000001', '平安银行', is_active=1),
            self._create_test_stock('000002', '万科A', is_active=0)
        ]
        self.repo.save_batch(stocks)
        
        active_only = self.repo.get_all(active_only=True)
        all_stocks = self.repo.get_all(active_only=False)
        
        self.assertEqual(len(active_only), 1)
        self.assertEqual(len(all_stocks), 2)
    
    def test_get_by_industry(self):
        """测试根据行业获取股票"""
        stocks = [
            self._create_test_stock('000001', '平安银行', industry_code='J01', industry_name='银行'),
            self._create_test_stock('000002', '万科A', industry_code='J02', industry_name='房地产')
        ]
        self.repo.save_batch(stocks)
        
        results = self.repo.get_by_industry('J01')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '平安银行')
    
    def test_get_by_market(self):
        """测试根据市场类型获取股票"""
        stocks = [
            self._create_test_stock('000001', '平安银行', market_type='main'),
            self._create_test_stock('688001', '科创板', market_type='star')
        ]
        self.repo.save_batch(stocks)
        
        results = self.repo.get_by_market('star')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '科创板')
    
    def test_search(self):
        """测试搜索股票"""
        stocks = [
            self._create_test_stock('000001', '平安银行'),
            self._create_test_stock('000002', '万科A'),
            self._create_test_stock('600000', '浦发银行')
        ]
        self.repo.save_batch(stocks)
        
        # 按代码搜索 - 600000也包含"000"
        results = self.repo.search('000')
        self.assertEqual(len(results), 3)
        
        # 按名称搜索
        results = self.repo.search('银行')
        self.assertEqual(len(results), 2)
        
        # 搜索单个
        results = self.repo.search('万科')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '万科A')
    
    def test_search_empty(self):
        """测试空搜索"""
        results = self.repo.search('')
        self.assertEqual(len(results), 0)
    
    def test_search_limit(self):
        """测试搜索限制数量"""
        stocks = [self._create_test_stock(f'00000{i}', f'股票{i}') for i in range(1, 10)]
        self.repo.save_batch(stocks)
        
        results = self.repo.search('股票', limit=5)
        self.assertEqual(len(results), 5)
    
    def test_delete_soft(self):
        """测试软删除"""
        stock = self._create_test_stock('000001', '平安银行')
        self.repo.save(stock)
        
        result = self.repo.delete('000001', soft_delete=True)
        self.assertTrue(result)
        
        # 验证软删除
        deleted = self.repo.get_by_code('000001')
        self.assertIsNone(deleted)
        
        # 但数据还在数据库中
        all_stocks = self.repo.get_all(active_only=False)
        self.assertEqual(len(all_stocks), 1)
        self.assertEqual(all_stocks[0].is_active, 0)
    
    def test_delete_hard(self):
        """测试硬删除"""
        stock = self._create_test_stock('000001', '平安银行')
        self.repo.save(stock)
        
        result = self.repo.delete('000001', soft_delete=False)
        self.assertTrue(result)
        
        # 验证硬删除
        all_stocks = self.repo.get_all(active_only=False)
        self.assertEqual(len(all_stocks), 0)
    
    def test_delete_not_found(self):
        """测试删除不存在的股票"""
        result = self.repo.delete('999999')
        self.assertFalse(result)
    
    def test_get_count(self):
        """测试获取股票数量"""
        stocks = [
            self._create_test_stock('000001', '平安银行'),
            self._create_test_stock('000002', '万科A')
        ]
        self.repo.save_batch(stocks)
        
        count = self.repo.get_count()
        self.assertEqual(count, 2)
    
    def test_get_industries(self):
        """测试获取行业列表"""
        stocks = [
            self._create_test_stock('000001', '平安银行', industry_code='J01', industry_name='银行'),
            self._create_test_stock('000002', '万科A', industry_code='J02', industry_name='房地产'),
            self._create_test_stock('000003', '招商银行', industry_code='J01', industry_name='银行')
        ]
        self.repo.save_batch(stocks)
        
        industries = self.repo.get_industries()
        self.assertEqual(len(industries), 2)
        
        codes = [i['code'] for i in industries]
        self.assertIn('J01', codes)
        self.assertIn('J02', codes)


if __name__ == '__main__':
    unittest.main()
