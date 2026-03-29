# -*- coding: utf-8 -*-
"""
数据验证模块

提供数据验证、输入校验等功能
"""
import re
from datetime import datetime, date
from typing import Optional, List, Any, Callable
from decimal import Decimal


class ValidationError(Exception):
    """验证错误异常"""
    pass


class Validator:
    """验证器基类"""
    
    @staticmethod
    def validate_stock_code(code: str) -> bool:
        """
        验证股票代码格式
        
        Args:
            code: 股票代码
            
        Returns:
            是否有效
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not code:
            raise ValidationError("股票代码不能为空")
        
        # 去除空格和后缀
        code = code.strip().upper()
        if '.' in code:
            code = code.split('.')[0]
        
        # A股代码规则：6位数字
        if not re.match(r'^\d{6}$', code):
            raise ValidationError(f"股票代码格式错误: {code}")
        
        # 验证代码范围
        if code.startswith('6') or code.startswith('0') or code.startswith('3'):
            return True
        elif code.startswith('8') or code.startswith('4'):
            # 北交所/新三板
            return True
        else:
            raise ValidationError(f"不支持的股票代码: {code}")
    
    @staticmethod
    def validate_date(date_str: str, date_format: str = '%Y-%m-%d') -> date:
        """
        验证日期格式
        
        Args:
            date_str: 日期字符串
            date_format: 日期格式
            
        Returns:
            日期对象
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not date_str:
            raise ValidationError("日期不能为空")
        
        try:
            return datetime.strptime(date_str, date_format).date()
        except ValueError:
            raise ValidationError(f"日期格式错误，期望格式: {date_format}")
    
    @staticmethod
    def validate_number(value: Any, min_value: Optional[float] = None, 
                       max_value: Optional[float] = None, 
                       allow_zero: bool = True) -> float:
        """
        验证数值
        
        Args:
            value: 数值
            min_value: 最小值
            max_value: 最大值
            allow_zero: 是否允许为零
            
        Returns:
            浮点数值
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            num = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"无效的数值: {value}")
        
        if not allow_zero and num == 0:
            raise ValidationError("数值不能为零")
        
        if min_value is not None and num < min_value:
            raise ValidationError(f"数值不能小于 {min_value}")
        
        if max_value is not None and num > max_value:
            raise ValidationError(f"数值不能大于 {max_value}")
        
        return num
    
    @staticmethod
    def validate_price(price: Any) -> Decimal:
        """
        验证价格
        
        Args:
            price: 价格
            
        Returns:
            Decimal价格
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            price_decimal = Decimal(str(price))
        except Exception:
            raise ValidationError(f"无效的价格: {price}")
        
        if price_decimal < 0:
            raise ValidationError("价格不能为负数")
        
        if price_decimal > 100000:
            raise ValidationError("价格超出合理范围")
        
        return price_decimal
    
    @staticmethod
    def validate_change_pct(change_pct: Any) -> Decimal:
        """
        验证涨跌幅
        
        Args:
            change_pct: 涨跌幅
            
        Returns:
            Decimal涨跌幅
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            pct = Decimal(str(change_pct))
        except Exception:
            raise ValidationError(f"无效的涨跌幅: {change_pct}")
        
        # A股涨跌幅限制一般为 ±20%（科创板/创业板）或 ±10%（主板）
        if pct < -30 or pct > 30:
            raise ValidationError("涨跌幅超出合理范围")
        
        return pct
    
    @staticmethod
    def validate_volume(volume: Any) -> int:
        """
        验证成交量
        
        Args:
            volume: 成交量
            
        Returns:
            整数成交量
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            vol = int(float(volume))
        except (ValueError, TypeError):
            raise ValidationError(f"无效的成交量: {volume}")
        
        if vol < 0:
            raise ValidationError("成交量不能为负数")
        
        return vol
    
    @staticmethod
    def validate_not_empty(value: Any, field_name: str = "字段") -> Any:
        """
        验证非空
        
        Args:
            value: 值
            field_name: 字段名称
            
        Returns:
            原值
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value is None:
            raise ValidationError(f"{field_name}不能为空")
        
        if isinstance(value, str) and not value.strip():
            raise ValidationError(f"{field_name}不能为空")
        
        if isinstance(value, (list, dict)) and len(value) == 0:
            raise ValidationError(f"{field_name}不能为空")
        
        return value
    
    @staticmethod
    def validate_in_list(value: Any, valid_list: List[Any], field_name: str = "字段") -> Any:
        """
        验证值在列表中
        
        Args:
            value: 值
            valid_list: 有效值列表
            field_name: 字段名称
            
        Returns:
            原值
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if value not in valid_list:
            raise ValidationError(
                f"{field_name}必须是以下值之一: {', '.join(map(str, valid_list))}"
            )
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            邮箱地址
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not email:
            raise ValidationError("邮箱不能为空")
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError(f"邮箱格式错误: {email}")
        
        return email
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        验证手机号格式
        
        Args:
            phone: 手机号
            
        Returns:
            手机号
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not phone:
            raise ValidationError("手机号不能为空")
        
        # 中国手机号格式
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, phone):
            raise ValidationError(f"手机号格式错误: {phone}")
        
        return phone


def validate_params(**validators: Callable) -> Callable:
    """
    参数验证装饰器
    
    使用示例:
        @validate_params(
            code=Validator.validate_stock_code,
            price=Validator.validate_price
        )
        def buy_stock(code: str, price: Decimal, amount: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 获取函数参数名
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # 验证位置参数
            for i, arg in enumerate(args):
                if i < len(param_names):
                    param_name = param_names[i]
                    if param_name in validators:
                        validators[param_name](arg)
            
            # 验证关键字参数
            for key, value in kwargs.items():
                if key in validators:
                    validators[key](value)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
