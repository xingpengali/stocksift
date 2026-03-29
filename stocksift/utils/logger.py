# -*- coding: utf-8 -*-
"""
日志模块
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from config.constants import (
    DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT,
    LOG_FILE_MAX_BYTES, LOG_FILE_BACKUP_COUNT, LOG_DIR
)


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI颜色码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        # 保存原始级别名称
        original_levelname = record.levelname
        
        # 添加颜色
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        result = super().format(record)
        record.levelname = original_levelname
        return result


def setup_logging(
    log_dir: Optional[str] = None,
    console_level: str = DEFAULT_LOG_LEVEL,
    file_level: str = "DEBUG",
    max_bytes: int = LOG_FILE_MAX_BYTES,
    backup_count: int = LOG_FILE_BACKUP_COUNT
) -> None:
    """
    初始化日志系统
    
    Args:
        log_dir: 日志目录，None使用默认目录
        console_level: 控制台日志级别
        file_level: 文件日志级别
        max_bytes: 单个日志文件最大字节数
        backup_count: 备份文件数量
    """
    # 确定日志目录
    if log_dir is None:
        project_root = Path(__file__).parent.parent
        log_dir = project_root / LOG_DIR
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    console_formatter = ColoredFormatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )
    file_formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（轮转）
    log_file = log_dir / "stocksift.log"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志单独存储
    error_log_file = log_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # 记录启动信息
    root_logger.info(f"日志系统初始化完成，日志目录: {log_dir}")


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 记录器名称，通常使用 __name__
        
    Returns:
        Logger实例
    """
    return logging.getLogger(name)


# 便捷的日志装饰器
def log_execution_time(logger_name: Optional[str] = None, level: str = "DEBUG"):
    """
    记录函数执行时间的装饰器
    
    Args:
        logger_name: 日志记录器名称，None使用被装饰函数的模块名
        level: 日志级别
    """
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                getattr(logger, level.lower())(
                    f"{func.__name__} 执行完成，耗时: {elapsed:.3f}s"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} 执行失败，耗时: {elapsed:.3f}s，错误: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator
