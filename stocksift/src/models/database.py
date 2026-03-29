# -*- coding: utf-8 -*-
"""
数据库管理模块

使用 SQLAlchemy < 2.0.0 作为 ORM
"""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

from config.settings import get_settings
from config.constants import DEFAULT_DB_NAME
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建基类
Base = declarative_base()


class DatabaseManager:
    """
    数据库管理器 - 单例模式
    
    负责数据库连接、会话管理和初始化
    """
    
    _instance = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        
        self._initialized = True
        self._db_path = db_path or self._get_default_db_path()
        self._engine = None
        self._session_factory = None
        
        # 初始化引擎
        self._init_engine()
    
    def _get_default_db_path(self) -> str:
        """获取默认数据库路径"""
        settings = get_settings()
        # 从 models/database.py 向上两级到 src，再向上到项目根目录
        project_root = Path(__file__).parent.parent.parent
        db_dir = project_root / "data" / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / DEFAULT_DB_NAME)
    
    def _init_engine(self):
        """初始化数据库引擎"""
        try:
            # SQLite 配置
            # 使用 StaticPool 避免多线程问题
            self._engine = create_engine(
                f"sqlite:///{self._db_path}",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False  # 生产环境设为False
            )
            
            # 创建会话工厂
            self._session_factory = sessionmaker(bind=self._engine)
            
            logger.info(f"数据库引擎初始化完成: {self._db_path}")
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise
    
    def init_db(self):
        """
        初始化数据库（创建所有表）
        """
        try:
            # 导入所有模型以确保表被创建
            from . import stock, quote, kline, financial
            
            Base.metadata.create_all(self._engine)
            logger.info("数据库表创建完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            Session: 数据库会话
        """
        return self._session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        会话上下文管理器
        
        使用示例:
            with db_manager.session_scope() as session:
                session.add(obj)
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            logger.info("数据库连接已关闭")
    
    @property
    def engine(self):
        """获取数据库引擎"""
        return self._engine
    
    @property
    def db_path(self) -> str:
        """获取数据库路径"""
        return self._db_path


# 全局实例
_db_manager = None


def get_db_manager(db_path: str = None) -> DatabaseManager:
    """
    获取数据库管理器实例
    
    Args:
        db_path: 数据库路径，None使用默认路径
        
    Returns:
        DatabaseManager实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def reset_db_manager():
    """重置数据库管理器实例（主要用于测试）"""
    global _db_manager
    _db_manager = None
    DatabaseManager._instance = None


# 便捷的上下文管理器
@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    便捷的会话上下文管理器
    
    使用示例:
        from models.database import session_scope
        with session_scope() as session:
            session.add(obj)
    """
    manager = get_db_manager()
    with manager.session_scope() as session:
        yield session
