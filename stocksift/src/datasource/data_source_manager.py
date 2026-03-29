# -*- coding: utf-8 -*-
"""
数据源管理器

管理多个数据源适配器，提供统一的数据获取接口
支持故障自动切换和优先级管理
"""
from typing import Dict, List, Optional, Callable, Any, Type
from datetime import datetime

from datasource.base_adapter import BaseDataAdapter, AdapterFactory
from datasource.tushare_adapter import TushareAdapter
from datasource.baostock_adapter import BaostockAdapter
from config.settings import get_settings
from utils.logger import get_logger
from utils.cache import cache_manager

logger = get_logger(__name__)


class DataSourceManager:
    """
    数据源管理器
    
    管理多个数据源适配器，提供统一的数据获取接口
    支持故障自动切换和优先级管理
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._adapters: Dict[str, BaseDataAdapter] = {}
        self._adapter_status: Dict[str, dict] = {}
        self._primary_adapter: Optional[str] = None
        self._priority_list: List[str] = []
        
        # 加载配置
        self._load_config()
        
        # 初始化适配器
        self._init_adapters()
    
    def _load_config(self):
        """加载数据源配置"""
        settings = get_settings()
        
        # 获取数据源优先级
        self._priority_list = settings.get(
            'data_source.priority',
            ['tushare', 'baostock']
        )
        
        # 设置主数据源
        if self._priority_list:
            self._primary_adapter = self._priority_list[0]
    
    def _init_adapters(self):
        """初始化数据源适配器"""
        settings = get_settings()
        
        # 注册 Tushare
        try:
            tushare_config = {
                'token': settings.get('data_source.tushare_token', ''),
                'rate_limit_delay': 0.5
            }
            AdapterFactory.register('tushare', TushareAdapter)
            self._adapters['tushare'] = TushareAdapter('tushare', tushare_config)
            self._adapter_status['tushare'] = {
                'connected': False,
                'last_error': None,
                'last_success': None
            }
            logger.info("Tushare 适配器已注册")
        except Exception as e:
            logger.warning(f"Tushare 适配器注册失败: {e}")
        
        # 注册 Baostock
        try:
            baostock_config = {
                'rate_limit_delay': 0.3
            }
            AdapterFactory.register('baostock', BaostockAdapter)
            self._adapters['baostock'] = BaostockAdapter('baostock', baostock_config)
            self._adapter_status['baostock'] = {
                'connected': False,
                'last_error': None,
                'last_success': None
            }
            logger.info("Baostock 适配器已注册")
        except Exception as e:
            logger.warning(f"Baostock 适配器注册失败: {e}")
    
    def connect(self, adapter_name: Optional[str] = None) -> bool:
        """
        连接数据源
        
        Args:
            adapter_name: 适配器名称，None表示连接所有
            
        Returns:
            是否成功
        """
        if adapter_name:
            return self._connect_single(adapter_name)
        
        # 连接所有适配器
        success = False
        for name in self._adapters:
            if self._connect_single(name):
                success = True
        
        return success
    
    def _connect_single(self, adapter_name: str) -> bool:
        """连接单个适配器"""
        adapter = self._adapters.get(adapter_name)
        if not adapter:
            logger.error(f"适配器不存在: {adapter_name}")
            return False
        
        try:
            if adapter.connect():
                self._adapter_status[adapter_name]['connected'] = True
                self._adapter_status[adapter_name]['last_success'] = datetime.now()
                logger.info(f"{adapter_name} 连接成功")
                return True
        except Exception as e:
            self._adapter_status[adapter_name]['connected'] = False
            self._adapter_status[adapter_name]['last_error'] = str(e)
            logger.warning(f"{adapter_name} 连接失败: {e}")
        
        return False
    
    def disconnect(self, adapter_name: Optional[str] = None):
        """
        断开数据源连接
        
        Args:
            adapter_name: 适配器名称，None表示断开所有
        """
        if adapter_name:
            adapter = self._adapters.get(adapter_name)
            if adapter:
                adapter.disconnect()
                self._adapter_status[adapter_name]['connected'] = False
                logger.info(f"{adapter_name} 已断开")
        else:
            for name, adapter in self._adapters.items():
                adapter.disconnect()
                self._adapter_status[name]['connected'] = False
            logger.info("所有数据源已断开")
    
    def get_adapter(self, adapter_name: str) -> Optional[BaseDataAdapter]:
        """
        获取指定适配器
        
        Args:
            adapter_name: 适配器名称
            
        Returns:
            适配器实例或None
        """
        return self._adapters.get(adapter_name)
    
    def get_primary_adapter(self) -> Optional[BaseDataAdapter]:
        """
        获取主适配器
        
        Returns:
            主适配器实例或None
        """
        if self._primary_adapter:
            return self._adapters.get(self._primary_adapter)
        
        # 如果没有设置主适配器，返回第一个可用的
        for name in self._priority_list:
            adapter = self._adapters.get(name)
            if adapter and self._adapter_status[name]['connected']:
                return adapter
        
        return None
    
    def set_primary(self, adapter_name: str) -> bool:
        """
        设置主数据源
        
        Args:
            adapter_name: 适配器名称
            
        Returns:
            是否成功
        """
        if adapter_name not in self._adapters:
            logger.error(f"适配器不存在: {adapter_name}")
            return False
        
        self._primary_adapter = adapter_name
        
        # 更新优先级列表
        if adapter_name in self._priority_list:
            self._priority_list.remove(adapter_name)
        self._priority_list.insert(0, adapter_name)
        
        # 保存配置
        settings = get_settings()
        settings.set('data_source.priority', self._priority_list)
        
        logger.info(f"主数据源已设置为: {adapter_name}")
        return True
    
    def get_available_adapters(self) -> List[str]:
        """
        获取可用的适配器列表
        
        Returns:
            适配器名称列表
        """
        return [
            name for name, status in self._adapter_status.items()
            if status['connected']
        ]
    
    def get_adapter_status(self) -> Dict[str, dict]:
        """
        获取所有适配器状态
        
        Returns:
            状态字典
        """
        return self._adapter_status.copy()
    
    def fetch_with_fallback(self, fetch_func: Callable, *args, **kwargs) -> Any:
        """
        带故障转移的数据获取
        
        依次尝试所有可用的数据源，直到成功
        
        Args:
            fetch_func: 数据获取函数
            *args, **kwargs: 函数参数
            
        Returns:
            获取结果
            
        Raises:
            Exception: 所有数据源都失败时抛出
        """
        errors = []
        
        # 按优先级尝试
        for adapter_name in self._priority_list:
            adapter = self._adapters.get(adapter_name)
            if not adapter or not self._adapter_status[adapter_name]['connected']:
                continue
            
            try:
                result = fetch_func(adapter, *args, **kwargs)
                self._adapter_status[adapter_name]['last_success'] = datetime.now()
                return result
            except Exception as e:
                error_msg = f"{adapter_name}: {e}"
                errors.append(error_msg)
                logger.warning(f"数据源 {adapter_name} 获取失败: {e}")
                
                # 标记为断开
                self._adapter_status[adapter_name]['connected'] = False
                self._adapter_status[adapter_name]['last_error'] = str(e)
        
        # 所有数据源都失败
        raise Exception(f"所有数据源获取失败: {'; '.join(errors)}")
    
    # ==================== 便捷数据获取方法 ====================
    
    def get_stock_list(self, use_cache: bool = True, cache_ttl: int = 3600) -> List[Dict]:
        """
        获取股票列表
        
        Args:
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期（秒）
            
        Returns:
            股票列表
        """
        cache_key = 'stock_list'
        
        if use_cache:
            cache = cache_manager.get_cache('data_source')
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        result = self.fetch_with_fallback(lambda adapter: adapter.get_stock_list())
        
        if use_cache:
            cache = cache_manager.get_cache('data_source')
            cache.set(cache_key, result, cache_ttl)
        
        return result
    
    def get_daily_quotes(self, codes: List[str]) -> List[Dict]:
        """
        获取日线行情
        
        Args:
            codes: 股票代码列表
            
        Returns:
            行情数据列表
        """
        return self.fetch_with_fallback(
            lambda adapter: adapter.get_daily_quotes(codes)
        )
    
    def get_kline_data(self, code: str, start_date, end_date, period: str = 'daily') -> List[Dict]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期
            
        Returns:
            K线数据列表
        """
        return self.fetch_with_fallback(
            lambda adapter: adapter.get_kline_data(code, start_date, end_date, period)
        )
    
    def get_financial_data(self, code: str, report_type: str = 'annual') -> Optional[Dict]:
        """
        获取财务数据
        
        Args:
            code: 股票代码
            report_type: 报告类型
            
        Returns:
            财务数据字典或None
        """
        return self.fetch_with_fallback(
            lambda adapter: adapter.get_financial_data(code, report_type)
        )


# 全局数据源管理器实例
data_source_manager = DataSourceManager()
