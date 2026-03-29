# -*- coding: utf-8 -*-
"""
Baostock 适配器测试
"""
import unittest
from datetime import date
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datasource.baostock_adapter import BaostockAdapter
from datasource.base_adapter import ConnectionError


class MockResult:
    """模拟 Baostock 返回结果"""
    
    def __init__(self, error_code='0', data=None, error_msg=''):
        self.error_code = error_code
        self.error_msg = error_msg
        self._data = data or []
        self._index = 0
    
    def next(self):
        if self._index < len(self._data):
            self._index += 1
            return True
        return False
    
    def get_row_data(self):
        if self._index <= len(self._data):
            return self._data[self._index - 1]
        return []


class TestBaostockAdapter(unittest.TestCase):
    """测试 BaostockAdapter"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'rate_limit_delay': 0.01
        }
        self.adapter = BaostockAdapter('baostock', self.config)
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', False)
    def test_connect_without_baostock(self):
        """测试未安装 baostock 时的连接"""
        with self.assertRaises(ConnectionError) as context:
            self.adapter.connect()
        self.assertIn("baostock 模块未安装", str(context.exception))
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    def test_connect_success(self, mock_login):
        """测试成功连接"""
        mock_login.return_value = MockResult(error_code='0')
        
        result = self.adapter.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.adapter.is_connected())
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    def test_connect_failure(self, mock_login):
        """测试连接失败"""
        mock_login.return_value = MockResult(error_code='1', error_msg='登录失败')
        
        with self.assertRaises(ConnectionError):
            self.adapter.connect()
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    @patch('datasource.baostock_adapter.bs.logout')
    def test_disconnect(self, mock_logout, mock_login):
        """测试断开连接"""
        mock_login.return_value = MockResult(error_code='0')
        
        self.adapter.connect()
        self.adapter.disconnect()
        
        self.assertFalse(self.adapter.is_connected())
        mock_logout.assert_called_once()
    
    def test_normalize_code(self):
        """测试代码标准化"""
        self.assertEqual(self.adapter.normalize_code("sh.600000"), "SH")  # 小写sh.会被转为大写SH
        self.assertEqual(self.adapter.normalize_code("sz.000001"), "SZ")  # 小写sz.会被转为大写SZ
        self.assertEqual(self.adapter.normalize_code("600000.SH"), "600000")
        self.assertEqual(self.adapter.normalize_code("000001.SZ"), "000001")
    
    def test_add_exchange_suffix(self):
        """测试添加交易所后缀"""
        self.assertEqual(self.adapter.add_exchange_suffix("600000"), "600000.SH")
        self.assertEqual(self.adapter.add_exchange_suffix("000001"), "000001.SZ")
    
    def test_to_bs_code(self):
        """测试转换为 Baostock 代码格式"""
        self.assertEqual(self.adapter._to_bs_code("600000"), "sh.600000")
        self.assertEqual(self.adapter._to_bs_code("000001"), "sz.000001")
    
    def test_get_market_type(self):
        """测试市场类型判断"""
        self.assertEqual(self.adapter._get_market_type("600000"), "main")
        self.assertEqual(self.adapter._get_market_type("688001"), "star")
        self.assertEqual(self.adapter._get_market_type("000001"), "main")
        self.assertEqual(self.adapter._get_market_type("300001"), "gem")
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    @patch('datasource.baostock_adapter.bs.query_all_stock')
    def test_get_stock_list(self, mock_query, mock_login):
        """测试获取股票列表"""
        mock_login.return_value = MockResult(error_code='0')
        mock_query.return_value = MockResult(error_code='0', data=[
            ['sh.600000'],
            ['sz.000001'],
            ['sz.300001'],
        ])
        
        self.adapter.connect()
        stocks = self.adapter.get_stock_list()
        
        self.assertEqual(len(stocks), 3)
        self.assertEqual(stocks[0]['code'], '600000')
        self.assertEqual(stocks[0]['exchange'], 'SSE')
        self.assertEqual(stocks[1]['code'], '000001')
        self.assertEqual(stocks[1]['exchange'], 'SZSE')
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    @patch('datasource.baostock_adapter.bs.query_stock_basic')
    def test_get_stock_basic(self, mock_query, mock_login):
        """测试获取股票基本信息"""
        mock_login.return_value = MockResult(error_code='0')
        mock_query.return_value = MockResult(error_code='0', data=[
            ['sh.600000', '浦发银行', '', '', '', '19991110']
        ])
        
        self.adapter.connect()
        stock = self.adapter.get_stock_basic('600000')
        
        self.assertIsNotNone(stock)
        self.assertEqual(stock['code'], '600000')
        self.assertEqual(stock['name'], '浦发银行')
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    @patch('datasource.baostock_adapter.bs.query_history_k_data_plus')
    def test_get_kline_data(self, mock_query, mock_login):
        """测试获取 K 线数据"""
        mock_login.return_value = MockResult(error_code='0')
        mock_query.return_value = MockResult(error_code='0', data=[
            ['2024-01-15', 'sh.600000', '10.0', '10.5', '9.8', '10.2', '1000000', '10200000']
        ])
        
        self.adapter.connect()
        klines = self.adapter.get_kline_data(
            '600000',
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        self.assertEqual(len(klines), 1)
        self.assertEqual(klines[0]['code'], '600000')
        self.assertEqual(float(klines[0]['close']), 10.2)
        self.assertEqual(klines[0]['volume'], 1000000)
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    def test_get_index_list(self, mock_login):
        """测试获取指数列表"""
        mock_login.return_value = MockResult(error_code='0')
        
        self.adapter.connect()
        indices = self.adapter.get_index_list()
        
        self.assertGreater(len(indices), 0)
        index_codes = [i['code'] for i in indices]
        self.assertIn('sh.000001', index_codes)
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    @patch('datasource.baostock_adapter.bs.query_stock_industry')
    def test_get_industry_list(self, mock_query, mock_login):
        """测试获取行业列表"""
        mock_login.return_value = MockResult(error_code='0')
        mock_query.return_value = MockResult(error_code='0', data=[
            ['sh.600000', '浦发银行', '银行'],
            ['sz.000001', '平安银行', '银行'],
            ['sz.000002', '万科A', '房地产'],
        ])
        
        self.adapter.connect()
        industries = self.adapter.get_industry_list()
        
        self.assertEqual(len(industries), 2)
        industry_names = [i['name'] for i in industries]
        self.assertIn('银行', industry_names)
        self.assertIn('房地产', industry_names)
    
    @patch('datasource.baostock_adapter.BAOSTOCK_AVAILABLE', True)
    @patch('datasource.baostock_adapter.bs.login')
    def test_get_concept_list(self, mock_login):
        """测试获取概念板块列表"""
        mock_login.return_value = MockResult(error_code='0')
        
        self.adapter.connect()
        concepts = self.adapter.get_concept_list()
        
        # Baostock 没有概念板块接口，返回空列表
        self.assertEqual(len(concepts), 0)


if __name__ == '__main__':
    unittest.main()
