# -*- coding: utf-8 -*-
"""
通用工具函数
"""
import re
import time
import functools
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional, Union, List, Dict


def format_number(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    thousands_separator: bool = True
) -> str:
    """
    格式化数字
    
    Args:
        value: 数值
        decimal_places: 小数位数
        thousands_separator: 是否显示千分位
        
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "--"
    
    try:
        d = Decimal(str(value))
        d = d.quantize(Decimal('0.1') ** decimal_places, rounding=ROUND_HALF_UP)
        
        if thousands_separator:
            return f"{d:,.{decimal_places}f}"
        else:
            return f"{d:.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percent(value: Union[int, float], decimal_places: int = 2) -> str:
    """
    格式化百分比
    
    Args:
        value: 数值（如 0.0523 表示 5.23%）
        decimal_places: 小数位数
        
    Returns:
        格式化后的百分比字符串
    """
    if value is None:
        return "--"
    
    try:
        return f"{value * 100:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_volume(value: Union[int, float]) -> str:
    """
    格式化成交量（自动转换为万/亿）
    
    Args:
        value: 成交量（手）
        
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "--"
    
    try:
        v = float(value)
        if v >= 100000000:
            return f"{v / 100000000:,.2f}亿"
        elif v >= 10000:
            return f"{v / 10000:,.2f}万"
        else:
            return f"{v:,.0f}"
    except (ValueError, TypeError):
        return str(value)


def format_amount(value: Union[int, float]) -> str:
    """
    格式化金额（自动转换为万/亿）
    
    Args:
        value: 金额（元）
        
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "--"
    
    try:
        v = float(value)
        if v >= 100000000:
            return f"{v / 100000000:,.2f}亿"
        elif v >= 10000:
            return f"{v / 10000:,.2f}万"
        else:
            return f"{v:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_date(dt: Union[datetime, date, str], fmt: str = "%Y-%m-%d") -> str:
    """
    格式化日期
    
    Args:
        dt: 日期对象或字符串
        fmt: 格式字符串
        
    Returns:
        格式化后的日期字符串
    """
    if dt is None:
        return "--"
    
    if isinstance(dt, str):
        # 尝试解析字符串
        for parse_fmt in ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                dt = datetime.strptime(dt, parse_fmt)
                break
            except ValueError:
                continue
        else:
            return dt
    
    if isinstance(dt, (datetime, date)):
        return dt.strftime(fmt)
    
    return str(dt)


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> Optional[date]:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串
        fmt: 格式字符串
        
    Returns:
        date对象或None
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, fmt).date()
    except ValueError:
        return None


def get_trade_date(dt: Optional[date] = None) -> date:
    """
    获取交易日（如果给定日期是周末，返回最近的周五）
    
    Args:
        dt: 日期，None表示今天
        
    Returns:
        交易日
    """
    if dt is None:
        dt = date.today()
    
    # 周六 -> 周五
    if dt.weekday() == 5:
        return dt - timedelta(days=1)
    # 周日 -> 周五
    elif dt.weekday() == 6:
        return dt - timedelta(days=2)
    
    return dt


def get_date_range(days: int, end_date: Optional[date] = None) -> tuple:
    """
    获取日期范围
    
    Args:
        days: 天数
        end_date: 结束日期，None表示今天
        
    Returns:
        (开始日期, 结束日期)
    """
    if end_date is None:
        end_date = date.today()
    
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码（去除后缀，统一格式）
    
    Args:
        code: 股票代码（如 "000001.SZ" 或 "000001"）
        
    Returns:
        标准化后的代码（如 "000001"）
    """
    if not code:
        return ""
    
    # 去除空格
    code = code.strip().upper()
    
    # 去除后缀
    if '.' in code:
        code = code.split('.')[0]
    
    # 验证格式（6位数字）
    if re.match(r'^\d{6}$', code):
        return code
    
    return code


def add_exchange_suffix(code: str) -> str:
    """
    为股票代码添加交易所后缀
    
    Args:
        code: 股票代码（如 "000001"）
        
    Returns:
        带后缀的代码（如 "000001.SZ"）
    """
    code = normalize_stock_code(code)
    
    if not code:
        return ""
    
    # 根据代码规则判断交易所
    if code.startswith('6'):
        return f"{code}.SH"
    else:
        return f"{code}.SZ"


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟增长倍数
        exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return wrapper
    return decorator


def singleton(cls):
    """单例装饰器"""
    instances = {}
    
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 每块大小
        
    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(a: Union[int, float], b: Union[int, float], default: float = 0.0) -> float:
    """
    安全除法
    
    Args:
        a: 被除数
        b: 除数
        default: 除数为0时的默认值
        
    Returns:
        除法结果
    """
    try:
        if b == 0:
            return default
        return a / b
    except (TypeError, ValueError):
        return default


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的字符串
    """
    if not s or len(s) <= max_length:
        return s
    
    return s[:max_length - len(suffix)] + suffix
