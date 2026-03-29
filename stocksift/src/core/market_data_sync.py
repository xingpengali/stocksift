# -*- coding: utf-8 -*-
"""
市场数据同步服务

后台异步从AKShare获取市场数据并存储到数据库
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from utils.logger import get_logger
from models.database import session_scope
from models.market_overview import MarketIndex, Sector, MarketStats, CapitalFlow

logger = get_logger(__name__)

# 尝试导入AKShare
try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
except ImportError as e:
    AKSHARE_AVAILABLE = False
    logger.warning(f"AKShare或pandas未安装: {e}")


class MarketDataSyncService:
    """
    市场数据同步服务
    
    后台线程定期从AKShare获取数据并存储到数据库
    """
    
    # 同步间隔（秒）
    SYNC_INTERVAL = 60  # 每分钟同步一次
    
    # 交易时间配置
    TRADE_START_MORNING = (9, 30)
    TRADE_END_MORNING = (11, 30)
    TRADE_START_AFTERNOON = (13, 0)
    TRADE_END_AFTERNOON = (15, 0)
    
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
    def start(self):
        """启动同步服务"""
        if self._running:
            logger.warning("市场数据同步服务已在运行")
            return
            
        if not AKSHARE_AVAILABLE:
            logger.error("AKShare未安装，无法启动同步服务")
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("市场数据同步服务已启动")
        
    def stop(self):
        """停止同步服务"""
        if not self._running:
            return
            
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._running = False
        logger.info("市场数据同步服务已停止")
        
    def _sync_loop(self):
        """同步循环"""
        while not self._stop_event.is_set():
            try:
                # 检查是否在交易时间
                if self._is_trade_time():
                    logger.debug("开始同步市场数据...")
                    self._sync_all_data()
                else:
                    logger.debug("当前非交易时间，跳过同步")
                    
            except Exception as e:
                logger.error(f"同步市场数据失败: {e}")
                
            # 等待下一次同步
            self._stop_event.wait(self.SYNC_INTERVAL)
            
    def _is_trade_time(self) -> bool:
        """
        检查当前是否在交易时间
        
        Returns:
            bool: 是否在交易时间
        """
        now = datetime.now()
        weekday = now.weekday()
        
        # 周末不交易
        if weekday >= 5:  # 5=周六, 6=周日
            return False
            
        hour = now.hour
        minute = now.minute
        current_time = (hour, minute)
        
        # 上午交易时间 9:30-11:30
        morning_start = self.TRADE_START_MORNING
        morning_end = self.TRADE_END_MORNING
        
        # 下午交易时间 13:00-15:00
        afternoon_start = self.TRADE_START_AFTERNOON
        afternoon_end = self.TRADE_END_AFTERNOON
        
        in_morning = morning_start <= current_time <= morning_end
        in_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return in_morning or in_afternoon
        
    def _sync_all_data(self):
        """同步所有市场数据"""
        try:
            self._sync_index_data()
            self._sync_sector_data()
            self._sync_market_stats()
            self._sync_capital_flow()
            logger.info("市场数据同步完成")
        except Exception as e:
            logger.error(f"同步市场数据失败: {e}")
            
    def _sync_index_data(self):
        """同步大盘指数数据"""
        try:
            index_codes = {
                "000001": "上证指数",
                "399001": "深证成指",
                "399006": "创业板指",
                "000688": "科创50",
            }
            
            with session_scope() as session:
                for code, name in index_codes.items():
                    try:
                        # 获取指数最新行情
                        end_date = datetime.now().strftime('%Y%m%d')
                        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                        
                        df = ak.index_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date)
                        if df is None or df.empty:
                            continue
                            
                        row = df.iloc[-1]
                        
                        # 创建或更新指数数据
                        index_data = MarketIndex(
                            code=code,
                            name=name,
                            value=float(row.get('收盘', 0)),
                            pre_close=float(row.get('昨收', 0)) if '昨收' in row else float(row.get('开盘', 0)),
                            open=float(row.get('开盘', 0)),
                            high=float(row.get('最高', 0)),
                            low=float(row.get('最低', 0)),
                            change=float(row.get('涨跌额', 0)),
                            change_pct=float(row.get('涨跌幅', 0)),
                            volume=int(row.get('成交量', 0)) if '成交量' in row else 0,
                            amount=float(row.get('成交额', 0)) if '成交额' in row else 0,
                            updated_at=datetime.now()
                        )
                        
                        session.add(index_data)
                        
                    except Exception as e:
                        logger.warning(f"同步指数 {name} 数据失败: {e}")
                        
        except Exception as e:
            logger.error(f"同步指数数据失败: {e}")
            
    def _sync_sector_data(self):
        """同步板块数据"""
        try:
            # 获取行业板块排行
            df = ak.stock_board_industry_name_em()
            
            if df is None or df.empty:
                logger.warning("获取板块数据为空")
                return
                
            # 按涨跌幅排序
            df = df.sort_values('涨跌幅', ascending=False)
            
            with session_scope() as session:
                # 清空旧数据（保留最近10条）
                session.query(Sector).delete()
                
                for rank, (_, row) in enumerate(df.head(20).iterrows(), 1):
                    try:
                        sector = Sector(
                            name=row.get('板块名称', ''),
                            change_pct=float(row.get('涨跌幅', 0)),
                            change=float(row.get('涨跌额', 0)) if '涨跌额' in row else 0,
                            amount=float(row.get('总市值', 0)) if '总市值' in row else 0,
                            leader_name=row.get('领涨股', '') if '领涨股' in row else '',
                            leader_code='',  # AKShare不直接提供领涨股代码
                            leader_change_pct=float(row.get('领涨股涨跌幅', 0)) if '领涨股涨跌幅' in row else 0,
                            rank=rank,
                            updated_at=datetime.now()
                        )
                        session.add(sector)
                    except Exception as e:
                        logger.warning(f"处理板块数据失败: {e}")
                        
        except Exception as e:
            logger.error(f"同步板块数据失败: {e}")
            
    def _sync_market_stats(self):
        """同步市场涨跌统计"""
        try:
            # 获取全部A股实时行情
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                logger.warning("获取行情数据为空")
                return
                
            # 计算涨跌分布
            change_col = '涨跌幅'
            if change_col not in df.columns:
                logger.warning("涨跌幅列不存在")
                return
                
            # 转换为数值
            df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
            
            stats = MarketStats(
                limit_up=len(df[df[change_col] >= 9.9]),
                up_over_5=len(df[(df[change_col] >= 5) & (df[change_col] < 9.9)]),
                up_0_to_5=len(df[(df[change_col] > 0) & (df[change_col] < 5)]),
                flat=len(df[df[change_col] == 0]),
                down_0_to_5=len(df[(df[change_col] < 0) & (df[change_col] > -5)]),
                down_over_5=len(df[(df[change_col] <= -5) & (df[change_col] > -9.9)]),
                limit_down=len(df[df[change_col] <= -9.9]),
                total_count=len(df),
                updated_at=datetime.now()
            )
            
            with session_scope() as session:
                session.add(stats)
                
        except Exception as e:
            logger.error(f"同步市场统计失败: {e}")
            
    def _sync_capital_flow(self):
        """同步资金流向数据"""
        try:
            # 获取北向资金
            north_inflow = 0
            try:
                north_df = ak.stock_hsgt_hist_em(symbol="沪股通")
                if north_df is not None and not north_df.empty:
                    latest = north_df.iloc[-1]
                    north_inflow = float(latest.get('当日资金流入', 0))
            except Exception as e:
                logger.warning(f"获取北向资金失败: {e}")
                
            # 获取大盘资金流向（简化处理）
            main_inflow = 0
            retail_inflow = 0
            
            try:
                spot_df = ak.stock_zh_a_spot_em()
                if spot_df is not None and not spot_df.empty:
                    # 使用主力净流入列（如果存在）
                    if '主力净流入' in spot_df.columns:
                        main_inflow = spot_df['主力净流入'].sum()
                        retail_inflow = -main_inflow  # 简化估算
            except Exception as e:
                logger.warning(f"获取主力净流入失败: {e}")
                
            flow = CapitalFlow(
                main_inflow=main_inflow,
                retail_inflow=retail_inflow,
                north_inflow=north_inflow,
                updated_at=datetime.now()
            )
            
            with session_scope() as session:
                session.add(flow)
                
        except Exception as e:
            logger.error(f"同步资金流向失败: {e}")


# 全局同步服务实例
_sync_service: Optional[MarketDataSyncService] = None


def get_sync_service() -> MarketDataSyncService:
    """获取同步服务实例（单例）"""
    global _sync_service
    if _sync_service is None:
        _sync_service = MarketDataSyncService()
    return _sync_service


def start_market_data_sync():
    """启动市场数据同步服务"""
    service = get_sync_service()
    service.start()
    

def stop_market_data_sync():
    """停止市场数据同步服务"""
    service = get_sync_service()
    service.stop()
