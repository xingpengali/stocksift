# -*- coding: utf-8 -*-
"""
数据源适配器基类测试
"""
import sys
import unittest
from datetime import date
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datasource.base_adapter import (
    BaseDataAdapter, AdapterFactory,
    DataSourceError, ConnectionError, DataNotFoundError,
    RateLimitError, AuthenticationError
)


class MockDataAdapter(BaseDataAdapter):
    """模拟数据源适配器，用于测试"""
    
    def __init__(self, name="mock", config=None):
        super().__init__(name, config or {})
        self._mock_connected = False
    
    def connect(self) -> bool:
        self._mock_connected = True
        self._connected = True
        return True
    
    def disconnect(self) -> None:
        self._mock_connected = False
        self._connected = False
    
    def get_stock_list(self):
        return [{'code': '000001', 'name': '平安银行'}]
    
    def get_stock_basic(self, code: str):
        return {'code': code, 'name': '测试股票'}
    
    def get_daily_quotes(self, codes):
        return [{'code': c, 'close': 10.0} for c in codes]
    
    def get_realtime_quotes(self, codes):
        return [{'code': c, 'price': 10.5} for c in codes]
    
    def get_kline_data(self, code, start_date, end_date, period="daily"):
        return [{'code': code, 'date': start_date, 'close': 10.0}]
    
    def get_financial_data(self, code, report_type="annual"):
        return {'code': code, 'eps': 1.0}
    
    def get_income_statement(self, code, start_date, end_date):
        return [{'code': code, 'revenue': 1000000}]
    
    def get_balance_sheet(self, code, start_date, end_date):
        return [{'code': code, 'assets': 5000000}]
    
    def get_cash_flow(self, code, start_date, end_date):
        return [{'code': code, 'cash': 100000}]
    
    def get_index_list(self):
        return [{'code': '000001.SH', 'name': '上证指数'}]
    
    def get_index_quotes(self, index_code):
        return [{'code': index_code, 'close': 3000}]
    
    def get_industry_list(self):
        return [{'code': 'J01', 'name': '银行'}]
    
    def get_concept_list(self):
        return [{'code': 'C01', 'name': '人工智能'}]
    
    def get_capital_flow(self, code, trade_date):
        return {'code': code, 'inflow': 1000000}


class TestDataSourceExceptions(unittest.TestCase):
    """测试数据源异常类"""
    
    def test_data_source_error(self):
        """测试数据源异常基类"""
        error = DataSourceError("测试错误")
        self.assertEqual(str(error), "测试错误")
        self.assertIsInstance(error, Exception)
    
    def test_connection_error(self):
        """测试连接异常"""
        error = ConnectionError("连接失败")
        self.assertEqual(str(error), "连接失败")
        self.assertIsInstance(error, DataSourceError)
    
    def test_data_not_found_error(self):
        """测试数据不存在异常"""
        error = DataNotFoundError("数据不存在")
        self.assertEqual(str(error), "数据不存在")
        self.assertIsInstance(error, DataSourceError)
    
    def test_rate_limit_error(self):
        """测试请求频率限制异常"""
        error = RateLimitError("请求过于频繁")
        self.assertEqual(str(error), "请求过于频繁")
        self.assertIsInstance(error, DataSourceError)
    
    def test_authentication_error(self):
        """测试认证异常"""
        error = AuthenticationError("认证失败")
        self.assertEqual(str(error), "认证失败")
        self.assertIsInstance(error, DataSourceError)


class TestBaseDataAdapter(unittest.TestCase):
    """测试BaseDataAdapter基类"""
    
    def setUp(self):
        """测试前准备"""
        self.adapter = MockDataAdapter("test_mock", {"api_key": "test_key"})
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.adapter.name, "test_mock")
        self.assertEqual(self.adapter.config, {"api_key": "test_key"})
        self.assertFalse(self.adapter.is_connected())
    
    def test_connect(self):
        """测试连接"""
        result = self.adapter.connect()
        self.assertTrue(result)
        self.assertTrue(self.adapter.is_connected())
    
    def test_disconnect(self):
        """测试断开连接"""
        self.adapter.connect()
        self.adapter.disconnect()
        self.assertFalse(self.adapter.is_connected())
    
    def test_check_connection_connected(self):
        """测试连接检查 - 已连接"""
        self.adapter.connect()
        # 不应该抛出异常
        try:
            self.adapter._check_connection()
        except ConnectionError:
            self.fail("已连接时不应抛出异常")
    
    def test_check_connection_not_connected(self):
        """测试连接检查 - 未连接"""
        with self.assertRaises(ConnectionError) as context:
            self.adapter._check_connection()
        self.assertIn("未连接", str(context.exception))
    
    def test_normalize_code(self):
        """测试代码标准化"""
        # 测试普通代码
        self.assertEqual(self.adapter.normalize_code("000001"), "000001")
        # 测试带空格
        self.assertEqual(self.adapter.normalize_code("  000001  "), "000001")
        # 测试带后缀
        self.assertEqual(self.adapter.normalize_code("000001.SZ"), "000001")
        self.assertEqual(self.adapter.normalize_code("000001.SH"), "000001")
        # 测试大写
        self.assertEqual(self.adapter.normalize_code("000001.sz"), "000001")
        # 测试空值
        self.assertEqual(self.adapter.normalize_code(""), "")
        self.assertEqual(self.adapter.normalize_code(None), "")
    
    def test_add_exchange_suffix_sh(self):
        """测试添加交易所后缀 - 上海"""
        result = self.adapter.add_exchange_suffix("600000")
        self.assertEqual(result, "600000.SH")
        
        result = self.adapter.add_exchange_suffix("688001")
        self.assertEqual(result, "688001.SH")
    
    def test_add_exchange_suffix_sz(self):
        """测试添加交易所后缀 - 深圳"""
        result = self.adapter.add_exchange_suffix("000001")
        self.assertEqual(result, "000001.SZ")
        
        result = self.adapter.add_exchange_suffix("300001")
        self.assertEqual(result, "300001.SZ")
    
    def test_add_exchange_suffix_with_suffix(self):
        """测试添加交易所后缀 - 已有后缀"""
        result = self.adapter.add_exchange_suffix("000001.SZ")
        self.assertEqual(result, "000001.SZ")
    
    def test_add_exchange_suffix_empty(self):
        """测试添加交易所后缀 - 空值"""
        result = self.adapter.add_exchange_suffix("")
        self.assertEqual(result, "")
    
    def test_handle_error_data_source_error(self):
        """测试错误处理 - 数据源异常"""
        error = DataSourceError("数据源错误")
        with self.assertRaises(DataSourceError) as context:
            self.adapter.handle_error(error, "测试上下文")
        # handle_error方法会包装错误消息
        self.assertIn("数据源错误", str(context.exception))
    
    def test_handle_error_connection_error(self):
        """测试错误处理 - 连接异常"""
        error = ConnectionError("连接失败")
        with self.assertRaises(ConnectionError) as context:
            self.adapter.handle_error(error, "测试上下文")
        self.assertEqual(str(context.exception), "连接失败")
    
    def test_handle_error_other_error(self):
        """测试错误处理 - 其他异常"""
        error = ValueError("值错误")
        with self.assertRaises(DataSourceError) as context:
            self.adapter.handle_error(error, "测试上下文")
        self.assertIn("值错误", str(context.exception))


class TestAdapterFactory(unittest.TestCase):
    """测试AdapterFactory"""
    
    def setUp(self):
        """测试前准备"""
        # 清除已注册的适配器
        AdapterFactory._adapters = {}
    
    def tearDown(self):
        """测试后清理"""
        AdapterFactory._adapters = {}
    
    def test_register(self):
        """测试注册适配器"""
        AdapterFactory.register("mock", MockDataAdapter)
        self.assertIn("mock", AdapterFactory._adapters)
    
    def test_register_invalid_class(self):
        """测试注册无效类"""
        class NotAnAdapter:
            pass
        
        with self.assertRaises(ValueError) as context:
            AdapterFactory.register("invalid", NotAnAdapter)
        self.assertIn("必须继承 BaseDataAdapter", str(context.exception))
    
    def test_create(self):
        """测试创建适配器"""
        AdapterFactory.register("mock", MockDataAdapter)
        adapter = AdapterFactory.create("mock", {"key": "value"})
        
        self.assertIsInstance(adapter, MockDataAdapter)
        self.assertEqual(adapter.name, "mock")
        self.assertEqual(adapter.config, {"key": "value"})
    
    def test_create_not_found(self):
        """测试创建未注册的适配器"""
        with self.assertRaises(ValueError) as context:
            AdapterFactory.create("not_exist", {})
        self.assertIn("未找到适配器", str(context.exception))
    
    def test_list_adapters(self):
        """测试获取适配器列表"""
        AdapterFactory.register("mock1", MockDataAdapter)
        AdapterFactory.register("mock2", MockDataAdapter)
        
        adapters = AdapterFactory.list_adapters()
        self.assertEqual(len(adapters), 2)
        self.assertIn("mock1", adapters)
        self.assertIn("mock2", adapters)
    
    def test_is_registered(self):
        """测试检查适配器是否已注册"""
        self.assertFalse(AdapterFactory.is_registered("mock"))
        
        AdapterFactory.register("mock", MockDataAdapter)
        self.assertTrue(AdapterFactory.is_registered("mock"))


class TestMockAdapterMethods(unittest.TestCase):
    """测试模拟适配器的具体方法"""
    
    def setUp(self):
        """测试前准备"""
        self.adapter = MockDataAdapter()
        self.adapter.connect()
    
    def test_get_stock_list(self):
        """测试获取股票列表"""
        result = self.adapter.get_stock_list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], '000001')
    
    def test_get_stock_basic(self):
        """测试获取股票基本信息"""
        result = self.adapter.get_stock_basic('000001')
        self.assertEqual(result['code'], '000001')
    
    def test_get_daily_quotes(self):
        """测试获取日线行情"""
        result = self.adapter.get_daily_quotes(['000001', '000002'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['code'], '000001')
    
    def test_get_realtime_quotes(self):
        """测试获取实时行情"""
        result = self.adapter.get_realtime_quotes(['000001'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['price'], 10.5)
    
    def test_get_kline_data(self):
        """测试获取K线数据"""
        result = self.adapter.get_kline_data(
            '000001',
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], '000001')
    
    def test_get_financial_data(self):
        """测试获取财务数据"""
        result = self.adapter.get_financial_data('000001')
        self.assertEqual(result['code'], '000001')
        self.assertEqual(result['eps'], 1.0)
    
    def test_get_income_statement(self):
        """测试获取利润表"""
        result = self.adapter.get_income_statement(
            '000001',
            date(2023, 1, 1),
            date(2023, 12, 31)
        )
        self.assertEqual(len(result), 1)
    
    def test_get_balance_sheet(self):
        """测试获取资产负债表"""
        result = self.adapter.get_balance_sheet(
            '000001',
            date(2023, 1, 1),
            date(2023, 12, 31)
        )
        self.assertEqual(len(result), 1)
    
    def test_get_cash_flow(self):
        """测试获取现金流量表"""
        result = self.adapter.get_cash_flow(
            '000001',
            date(2023, 1, 1),
            date(2023, 12, 31)
        )
        self.assertEqual(len(result), 1)
    
    def test_get_index_list(self):
        """测试获取指数列表"""
        result = self.adapter.get_index_list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], '000001.SH')
    
    def test_get_index_quotes(self):
        """测试获取指数行情"""
        result = self.adapter.get_index_quotes('000001.SH')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['close'], 3000)
    
    def test_get_industry_list(self):
        """测试获取行业列表"""
        result = self.adapter.get_industry_list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], 'J01')
    
    def test_get_concept_list(self):
        """测试获取概念板块列表"""
        result = self.adapter.get_concept_list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['code'], 'C01')
    
    def test_get_capital_flow(self):
        """测试获取资金流向"""
        result = self.adapter.get_capital_flow('000001', date(2024, 1, 15))
        self.assertEqual(result['code'], '000001')
        self.assertEqual(result['inflow'], 1000000)


if __name__ == '__main__':
    unittest.main()
