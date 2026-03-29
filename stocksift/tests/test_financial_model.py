# -*- coding: utf-8 -*-
"""
财务数据模型测试
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models.database import get_db_manager, reset_db_manager
from models.financial import Financial, FinancialRepository


class TestFinancial(unittest.TestCase):
    """测试Financial模型"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_financial.db")
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
    
    def test_create_financial(self):
        """测试创建财务数据对象"""
        financial = Financial(
            code='000001',
            report_date=date(2023, 12, 31),
            report_type='annual',
            revenue=Decimal('164647000000.00'),
            net_profit=Decimal('46400000000.00'),
            eps=Decimal('2.31'),
            roe=Decimal('11.38'),
            total_assets=Decimal('5584710000000.00')
        )
        
        self.assertEqual(financial.code, '000001')
        self.assertEqual(financial.report_date, date(2023, 12, 31))
        self.assertEqual(financial.report_type, 'annual')
        self.assertEqual(float(financial.revenue), 164647000000.00)
    
    def test_financial_repr(self):
        """测试财务数据对象的字符串表示"""
        financial = Financial(code='000001', report_date=date(2023, 12, 31))
        repr_str = repr(financial)
        self.assertIn('000001', repr_str)
        self.assertIn('2023-12-31', repr_str)
    
    def test_to_dict(self):
        """测试转换为字典"""
        financial = Financial(
            code='000001',
            report_date=date(2023, 12, 31),
            report_type='annual',
            revenue=Decimal('164647000000.00'),
            net_profit=Decimal('46400000000.00'),
            eps=Decimal('2.31'),
            roe=Decimal('11.38'),
            roa=Decimal('0.85'),
            gross_margin=Decimal('35.50'),
            net_margin=Decimal('28.20'),
            total_assets=Decimal('5584710000000.00'),
            debt_ratio=Decimal('91.50'),
            operating_cash_flow=Decimal('120000000000.00'),
            revenue_growth=Decimal('8.50'),
            profit_growth=Decimal('12.30')
        )
        
        data = financial.to_dict()
        
        self.assertEqual(data['code'], '000001')
        self.assertEqual(data['report_date'], '2023-12-31')
        self.assertEqual(data['report_type'], 'annual')
        self.assertEqual(data['revenue'], 164647000000.00)
        self.assertEqual(data['eps'], 2.31)
        self.assertEqual(data['roe'], 11.38)
        self.assertEqual(data['debt_ratio'], 91.50)
        self.assertEqual(data['revenue_growth'], 8.50)
    
    def test_to_dict_none_values(self):
        """测试空值处理"""
        financial = Financial(code='000001', report_date=date(2023, 12, 31))
        data = financial.to_dict()
        
        self.assertIsNone(data['revenue'])
        self.assertIsNone(data['eps'])
        self.assertIsNone(data['roe'])


class TestFinancialRepository(unittest.TestCase):
    """测试FinancialRepository"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_financial_repo.db")
        self.db_manager = get_db_manager(self.db_path)
        self.db_manager.init_db()
        self.repo = FinancialRepository()
    
    def tearDown(self):
        """测试后清理"""
        if self.db_manager:
            self.db_manager.close()
        reset_db_manager()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def _create_test_financial(self, code, report_date, report_type='annual', **kwargs):
        """辅助方法：创建测试财务数据"""
        financial = Financial(
            code=code,
            report_date=report_date,
            report_type=report_type,
            revenue=kwargs.get('revenue', Decimal('1000000000.00')),
            net_profit=kwargs.get('net_profit', Decimal('100000000.00')),
            eps=kwargs.get('eps', Decimal('1.00')),
            roe=kwargs.get('roe', Decimal('10.00'))
        )
        return financial
    
    def test_save(self):
        """测试保存财务数据"""
        financial = self._create_test_financial(
            '000001',
            date(2023, 12, 31),
            revenue=Decimal('164647000000.00')
        )
        result = self.repo.save(financial)
        
        self.assertTrue(result)
        
        # 验证保存成功
        saved = self.repo.get_by_code('000001')
        self.assertIsNotNone(saved)
        self.assertEqual(float(saved.revenue), 164647000000.00)
    
    def test_save_update(self):
        """测试更新财务数据"""
        # 先保存
        financial = self._create_test_financial('000001', date(2023, 12, 31))
        self.repo.save(financial)
        
        # 更新
        financial2 = self._create_test_financial(
            '000001',
            date(2023, 12, 31),
            revenue=Decimal('2000000000.00')
        )
        result = self.repo.save(financial2)
        
        self.assertTrue(result)
        
        # 验证更新
        updated = self.repo.get_by_code('000001')
        self.assertEqual(float(updated.revenue), 2000000000.00)
    
    def test_save_batch(self):
        """测试批量保存"""
        financials = [
            self._create_test_financial('000001', date(2021, 12, 31)),
            self._create_test_financial('000001', date(2022, 12, 31)),
            self._create_test_financial('000001', date(2023, 12, 31))
        ]
        
        count = self.repo.save_batch(financials)
        self.assertEqual(count, 3)
    
    def test_get_by_code(self):
        """测试根据代码获取财务数据"""
        financial = self._create_test_financial('000001', date(2023, 12, 31))
        self.repo.save(financial)
        
        result = self.repo.get_by_code('000001')
        self.assertIsNotNone(result)
        self.assertEqual(result.report_date, date(2023, 12, 31))
    
    def test_get_by_code_with_date(self):
        """测试根据代码和日期获取财务数据"""
        financials = [
            self._create_test_financial('000001', date(2022, 12, 31)),
            self._create_test_financial('000001', date(2023, 12, 31))
        ]
        self.repo.save_batch(financials)
        
        # 不指定日期，应该返回最新的
        latest = self.repo.get_by_code('000001')
        self.assertEqual(latest.report_date, date(2023, 12, 31))
        
        # 指定日期
        specific = self.repo.get_by_code('000001', date(2022, 12, 31))
        self.assertEqual(specific.report_date, date(2022, 12, 31))
    
    def test_get_by_code_not_found(self):
        """测试获取不存在的财务数据"""
        result = self.repo.get_by_code('999999')
        self.assertIsNone(result)
    
    def test_get_history(self):
        """测试获取历史财务数据"""
        # 创建5年的财务数据
        financials = []
        for year in range(2019, 2024):
            financials.append(
                self._create_test_financial('000001', date(year, 12, 31))
            )
        self.repo.save_batch(financials)
        
        # 获取最近5年的历史数据（因为当前日期是2026年，3年前是2023年，数据从2019-2023都在范围内）
        history = self.repo.get_history('000001', years=10)
        self.assertEqual(len(history), 5)  # 2019, 2020, 2021, 2022, 2023
        
        # 验证按日期降序
        self.assertEqual(history[0].report_date, date(2023, 12, 31))
        self.assertEqual(history[1].report_date, date(2022, 12, 31))
        self.assertEqual(history[2].report_date, date(2021, 12, 31))
    
    def test_get_history_no_data(self):
        """测试获取不存在股票的历史数据"""
        history = self.repo.get_history('999999', years=5)
        self.assertEqual(len(history), 0)


if __name__ == '__main__':
    unittest.main()
