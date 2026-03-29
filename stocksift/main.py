# -*- coding: utf-8 -*-
"""
StockSift - A股选股助手

主入口文件
"""
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from ui.pages import (
    MarketOverviewPage,
    ScreenerPage,
    StockDetailPage,
    WatchlistPage,
    BacktestPage,
    ValueInvestingPage
)
from ui.dialogs import SettingsDialog
from config.settings import get_settings
from models.database import get_db_manager
from utils.logger import setup_logging, get_logger


def init_application():
    """初始化应用程序"""
    # 设置日志
    setup_logging()
    logger = get_logger(__name__)
    logger.info("应用启动中...")
    
    # 加载配置
    settings = get_settings()
    logger.info("配置加载完成")
    
    # 初始化数据库
    db = get_db_manager()
    db.init_db()
    logger.info("数据库初始化完成")
    
    return logger


def create_main_window():
    """
    创建主窗口
    
    Returns:
        主窗口实例
    """
    # 创建主窗口
    main_window = MainWindow()
    
    # 添加页面
    pages = [
        MarketOverviewPage(),
        ScreenerPage(),
        WatchlistPage(),
        BacktestPage(),
        ValueInvestingPage(),
    ]
    
    for page in pages:
        main_window.add_page(page)
    
    return main_window


def main():
    """主函数"""
    # 初始化
    logger = init_application()
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("StockSift")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用属性
    app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)
    
    # 创建并显示主窗口
    main_window = create_main_window()
    main_window.show()
    
    logger.info("应用启动完成")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
