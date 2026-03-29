# -*- coding: utf-8 -*-
"""
数据库管理器测试
"""
import os
import tempfile
import unittest
from pathlib import Path

from models.database import DatabaseManager, get_db_manager, reset_db_manager, Base
from models.stock import Stock
from models.quote import Quote
from models.kline import Kline
from models.financial import Financial


class TestDatabaseManager(unittest.TestCase):
    """测试数据库管理器"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        reset_db_manager()
        
        # 创建临时数据库文件
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """测试后清理"""
        # 关闭数据库连接
        if self.db_manager:
            self.db_manager.close()
        
        # 重置单例
        reset_db_manager()
        
        # 删除临时文件
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        db1 = DatabaseManager(self.db_path)
        db2 = DatabaseManager(self.db_path)
        
        # 应该是同一个实例
        self.assertIs(db1, db2)
        
        # 但重置后应该创建新实例
        reset_db_manager()
        db3 = DatabaseManager(self.db_path)
        self.assertIsNot(db1, db3)
    
    def test_init_engine(self):
        """测试数据库引擎初始化"""
        self.assertIsNotNone(self.db_manager.engine)
        self.assertEqual(self.db_manager.db_path, self.db_path)
    
    def test_init_db(self):
        """测试数据库初始化（创建表）"""
        # 初始化数据库
        self.db_manager.init_db()
        
        # 验证表是否创建
        from sqlalchemy import inspect
        inspector = inspect(self.db_manager.engine)
        tables = inspector.get_table_names()
        
        self.assertIn('stocks', tables)
        self.assertIn('quotes', tables)
        self.assertIn('klines', tables)
        self.assertIn('financials', tables)
    
    def test_get_session(self):
        """测试获取会话"""
        session = self.db_manager.get_session()
        self.assertIsNotNone(session)
        session.close()
    
    def test_session_scope(self):
        """测试会话上下文管理器"""
        # 先初始化数据库表
        self.db_manager.init_db()
        
        with self.db_manager.session_scope() as session:
            # 会话应该可用
            self.assertIsNotNone(session)
            # 创建一个测试对象
            stock = Stock(code='000001', name='测试股票', exchange='SZSE')
            session.add(stock)
        
        # 验证数据已提交
        with self.db_manager.session_scope() as session:
            result = session.query(Stock).filter_by(code='000001').first()
            self.assertIsNotNone(result)
            self.assertEqual(result.name, '测试股票')
    
    def test_session_scope_rollback(self):
        """测试会话上下文管理器回滚"""
        # 先初始化数据库表
        self.db_manager.init_db()
        
        class TestError(Exception):
            pass
        
        try:
            with self.db_manager.session_scope() as session:
                stock = Stock(code='000002', name='回滚测试', exchange='SZSE')
                session.add(stock)
                raise TestError("测试异常")
        except TestError:
            pass
        
        # 验证数据未提交
        with self.db_manager.session_scope() as session:
            result = session.query(Stock).filter_by(code='000002').first()
            self.assertIsNone(result)
    
    def test_close(self):
        """测试关闭数据库连接"""
        self.db_manager.close()
        # 关闭后引擎应该被释放
        # 注意：SQLAlchemy的dispose只是释放连接池，引擎对象仍然存在


class TestGetDbManager(unittest.TestCase):
    """测试获取数据库管理器函数"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_global.db")
    
    def tearDown(self):
        """测试后清理"""
        reset_db_manager()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_get_db_manager_singleton(self):
        """测试全局函数返回单例"""
        db1 = get_db_manager(self.db_path)
        db2 = get_db_manager()
        
        self.assertIs(db1, db2)
        
        db1.close()


class TestSessionScope(unittest.TestCase):
    """测试便捷的session_scope函数"""
    
    def setUp(self):
        """测试前准备"""
        reset_db_manager()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_scope.db")
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
    
    def test_session_scope_import(self):
        """测试从模块导入的session_scope"""
        from models.database import session_scope as module_scope
        
        with module_scope() as session:
            stock = Stock(code='000003', name='模块测试', exchange='SZSE')
            session.add(stock)
        
        # 验证
        with module_scope() as session:
            result = session.query(Stock).filter_by(code='000003').first()
            self.assertIsNotNone(result)
            self.assertEqual(result.name, '模块测试')


if __name__ == '__main__':
    unittest.main()
