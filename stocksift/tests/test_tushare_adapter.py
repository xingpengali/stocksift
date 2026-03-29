# -*- coding: utf-8 -*-
"""
Tushare 适配器测试
"""
import unittest
from datetime import date
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datasource.tushare_adapter import TushareAdapter, pd_not_null
from datasource.base_adapter import (
    ConnectionError, AuthenticationError, RateLimitError, DataSourceError
)


class MockDataFrame:
    """模拟 pandas DataFrame"""
    
    def __init__(self, data):
        self._data = data
        self.empty = len(data) == 0
    
    def iterrows(self):
        for i, row in enumerate(self._data):
            yield i, MockRow(row)
    
    def iloc(self, idx):
        return MockRow(self._data[idx])
    
    @property
    def iloc(self):
        return MockIloc(self._data)


class MockIloc:
    """模拟 iloc"""
    
    def __init__(self, data):
        self._data = data
    
    def __getitem__(self, idx):
        if idx >= len(self._data):
            raise IndexError()
        return MockRow(self._data[idx])


class MockRow:
    """模拟 DataFrame 行"""
    
    def __init__(self, data):
        self._data = data
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)


class TestPdNotNull(unittest.TestCase):
    """测试 pd_not_null 函数"""
    
    def test_none_value(self):
        """测试 None 值"""
        self.assertFalse(pd_not_null(None))
    
    def test_valid_value(self):
        """测试有效值"""
        self.assertTrue(pd_not_null(1.0))
        self.assertTrue(pd_not_null(0))
        self.assertTrue(pd_not_null("test"))


class TestTushareAdapter(unittest.TestCase):
    """测试 TushareAdapter"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'token': 'test_token',
            'rate_limit_delay': 0.01
        }
        self.adapter = TushareAdapter('tushare', self.config)
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', False)
    def test_connect_without_tushare(self):
        """测试未安装 tushare 时的连接"""
        with self.assertRaises(ConnectionError) as context:
            self.adapter.connect()
        self.assertIn("tushare 模块未安装", str(context.exception))
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    def test_connect_without_token(self):
        """测试没有 token 时的连接"""
        adapter = TushareAdapter('tushare', {})
        with self.assertRaises(AuthenticationError) as context:
            adapter.connect()
        self.assertIn("缺少 Tushare token", str(context.exception))
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_connect_success(self, mock_pro_api):
        """测试成功连接"""
        mock_pro = Mock()
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        result = self.adapter.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.adapter.is_connected())
        mock_pro_api.assert_called_once_with('test_token')
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_connect_authentication_error(self, mock_pro_api):
        """测试认证失败"""
        mock_pro = Mock()
        mock_pro.trade_cal = Mock(side_effect=Exception("token invalid"))
        mock_pro_api.return_value = mock_pro
        
        with self.assertRaises(AuthenticationError):
            self.adapter.connect()
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_disconnect(self, mock_pro_api):
        """测试断开连接"""
        mock_pro = Mock()
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        self.adapter.disconnect()
        
        self.assertFalse(self.adapter.is_connected())
    
    def test_normalize_code(self):
        """测试代码标准化"""
        self.assertEqual(self.adapter.normalize_code("000001.SZ"), "000001")
        self.assertEqual(self.adapter.normalize_code("600000.sh"), "600000")
        self.assertEqual(self.adapter.normalize_code(" 000001 "), "000001")
    
    def test_add_exchange_suffix(self):
        """测试添加交易所后缀"""
        self.assertEqual(self.adapter.add_exchange_suffix("600000"), "600000.SH")
        self.assertEqual(self.adapter.add_exchange_suffix("000001"), "000001.SZ")
        self.assertEqual(self.adapter.add_exchange_suffix("300001"), "300001.SZ")
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_get_stock_list(self, mock_pro_api):
        """测试获取股票列表"""
        mock_pro = Mock()
        mock_df = MockDataFrame([
            {
                'ts_code': '000001.SZ',
                'name': '平安银行',
                'exchange': 'SZSE',
                'market': '主板',
                'industry': '银行',
                'list_date': '19910403'
            },
            {
                'ts_code': '600000.SH',
                'name': '浦发银行',
                'exchange': 'SSE',
                'market': '主板',
                'industry': '银行',
                'list_date': '19911127'
            }
        ])
        mock_pro.stock_basic = Mock(return_value=mock_df)
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        stocks = self.adapter.get_stock_list()
        
        self.assertEqual(len(stocks), 2)
        self.assertEqual(stocks[0]['code'], '000001')
        self.assertEqual(stocks[0]['name'], '平安银行')
        self.assertEqual(stocks[1]['code'], '600000')
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_get_stock_basic(self, mock_pro_api):
        """测试获取股票基本信息"""
        mock_pro = Mock()
        mock_df = MockDataFrame([
            {
                'ts_code': '000001.SZ',
                'name': '平安银行',
                'exchange': 'SZSE',
                'market': '主板',
                'industry': '银行',
                'list_date': '19910403'
            }
        ])
        mock_pro.stock_basic = Mock(return_value=mock_df)
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        stock = self.adapter.get_stock_basic('000001')
        
        self.assertIsNotNone(stock)
        self.assertEqual(stock['code'], '000001')
        self.assertEqual(stock['name'], '平安银行')
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_get_daily_quotes(self, mock_pro_api):
        """测试获取日线行情"""
        mock_pro = Mock()
        mock_df = MockDataFrame([
            {
                'ts_code': '000001.SZ',
                'trade_date': '20240115',
                'open': 10.0,
                'high': 10.5,
                'low': 9.8,
                'close': 10.2,
                'vol': 100000,  # 手
                'amount': 1020000  # 千元
            }
        ])
        mock_pro.daily = Mock(return_value=mock_df)
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        quotes = self.adapter.get_daily_quotes(['000001'])
        
        self.assertEqual(len(quotes), 1)
        self.assertEqual(float(quotes[0]['close']), 10.2)
        self.assertEqual(quotes[0]['volume'], 10000000)  # 转换为股
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_get_kline_data(self, mock_pro_api):
        """测试获取 K 线数据"""
        mock_pro = Mock()
        mock_df = MockDataFrame([
            {
                'ts_code': '000001.SZ',
                'trade_date': '20240115',
                'open': 10.0,
                'high': 10.5,
                'low': 9.8,
                'close': 10.2,
                'vol': 100000,
                'amount': 1020000
            }
        ])
        mock_pro.daily = Mock(return_value=mock_df)
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        klines = self.adapter.get_kline_data(
            '000001',
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        self.assertEqual(len(klines), 1)
        self.assertEqual(klines[0]['code'], '000001')
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_get_industry_list(self, mock_pro_api):
        """测试获取行业列表"""
        mock_pro = Mock()
        mock_df = MockDataFrame([
            {
                'ts_code': '000001.SZ',
                'name': '平安银行',
                'industry': '银行'
            },
            {
                'ts_code': '000002.SZ',
                'name': '万科A',
                'industry': '房地产'
            }
        ])
        mock_pro.stock_basic = Mock(return_value=mock_df)
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        industries = self.adapter.get_industry_list()
        
        self.assertEqual(len(industries), 2)
        industry_names = [i['name'] for i in industries]
        self.assertIn('银行', industry_names)
        self.assertIn('房地产', industry_names)
    
    @patch('datasource.tushare_adapter.TUSHARE_AVAILABLE', True)
    @patch('datasource.tushare_adapter.ts.pro_api')
    def test_rate_limit_error(self, mock_pro_api):
        """测试频率限制错误"""
        mock_pro = Mock()
        mock_pro.stock_basic = Mock(side_effect=Exception("请求频率限制"))
        mock_pro.trade_cal = Mock(return_value=Mock(empty=False))
        mock_pro_api.return_value = mock_pro
        
        self.adapter.connect()
        
        with self.assertRaises(RateLimitError):
            self.adapter.get_stock_list()


if __name__ == '__main__':
    unittest.main()
