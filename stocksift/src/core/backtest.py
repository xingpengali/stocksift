# -*- coding: utf-8 -*-
"""
回测引擎模块

实现策略历史回测功能
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import time

import pandas as pd
import numpy as np

from models.database import get_db_manager
from models.strategy import StrategyRepository, BacktestRecordRepository, BacktestRecord
from core.screener import ScreenerEngine, FilterCondition
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestParams:
    """回测参数"""
    strategy_id: str
    start_date: date
    end_date: date
    initial_capital: float = 1000000.0
    position_size: float = 0.1  # 单个仓位比例
    commission_rate: float = 0.0003  # 手续费率 0.03%
    slippage: float = 0.001  # 滑点 0.1%
    rebalance_period: int = 20  # 再平衡周期（天）
    max_positions: int = 10  # 最大持仓数


@dataclass
class TradeRecord:
    """交易记录"""
    date: date
    code: str
    name: str
    action: str  # BUY/SELL
    price: float
    shares: int
    amount: float
    commission: float
    reason: str


@dataclass
class BacktestResult:
    """回测结果"""
    # 基础信息
    backtest_id: str
    strategy_id: str
    start_date: date
    end_date: date
    
    # 收益指标
    total_return: float
    annualized_return: float
    benchmark_return: float
    excess_return: float
    
    # 风险指标
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # 交易统计
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_profit: float
    avg_loss: float
    
    # 详细记录
    equity_curve: List[Dict]
    trades: List[TradeRecord]
    monthly_returns: List[Dict]
    
    # 元数据
    execution_time: float
    created_at: datetime = field(default_factory=datetime.now)


class BacktestEngine:
    """
    回测引擎
    
    执行策略历史回测
    """
    
    def __init__(self):
        """初始化"""
        self.screener = ScreenerEngine()
        self.strategy_repo = StrategyRepository()
        self.backtest_repo = BacktestRecordRepository()
    
    def run(self, params: BacktestParams) -> BacktestResult:
        """
        执行回测
        
        Args:
            params: 回测参数
            
        Returns:
            回测结果
        """
        start_time = time.time()
        backtest_id = str(uuid.uuid4())[:8]
        
        logger.info(f"开始回测 [{backtest_id}]: 策略={params.strategy_id}, "
                   f"时间={params.start_date}~{params.end_date}")
        
        # 获取策略
        strategy = self.strategy_repo.get_by_id(params.strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {params.strategy_id}")
        
        # 初始化回测状态
        capital = params.initial_capital
        positions: Dict[str, Dict] = {}  # 当前持仓
        trades: List[TradeRecord] = []
        equity_curve: List[Dict] = []
        
        # 生成交易日历
        trading_days = self._generate_trading_days(params.start_date, params.end_date)
        
        # 逐日回测
        for i, current_date in enumerate(trading_days):
            # 记录每日权益
            equity = self._calculate_equity(capital, positions, current_date)
            equity_curve.append({
                'date': current_date.isoformat(),
                'equity': equity,
                'cash': capital,
                'positions_value': equity - capital,
                'positions_count': len(positions)
            })
            
            # 再平衡日或第一天
            if i % params.rebalance_period == 0 or i == 0:
                # 获取当日选股结果
                selected = self._get_selection(strategy, current_date)
                
                # 执行调仓
                capital, positions, new_trades = self._rebalance(
                    capital, positions, selected, current_date, params
                )
                trades.extend(new_trades)
        
        # 计算绩效指标
        result = self._calculate_performance(
            backtest_id, params, equity_curve, trades, time.time() - start_time
        )
        
        # 保存回测记录
        self._save_backtest_record(params.strategy_id, result)
        
        logger.info(f"回测完成 [{backtest_id}]: 总收益={result.total_return:.2f}%, "
                   f"夏普比率={result.sharpe_ratio:.2f}")
        
        return result
    
    def _generate_trading_days(self, start_date: date, end_date: date) -> List[date]:
        """生成交易日历（简化版，实际应该排除节假日）"""
        days = []
        current = start_date
        while current <= end_date:
            # 周一到周五为交易日
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        return days
    
    def _get_selection(self, strategy, current_date: date) -> List[Dict]:
        """获取当日选股结果"""
        try:
            # 解析策略条件
            import json
            config = json.loads(strategy.config) if strategy.config else []
            conditions = [
                FilterCondition(
                    c['field'], c['operator'], c['value'],
                    c.get('value2'), c.get('logic', 'AND')
                )
                for c in config
            ]
            
            # 执行筛选
            result = self.screener.screen(
                conditions,
                page=1,
                page_size=50
            )
            
            return result.data
        except Exception as e:
            logger.error(f"选股失败: {e}")
            return []
    
    def _rebalance(self, capital: float, positions: Dict, 
                   selected: List[Dict], current_date: date,
                   params: BacktestParams) -> tuple:
        """执行调仓"""
        trades = []
        
        # 计算目标持仓
        target_codes = {s['code'] for s in selected[:params.max_positions]}
        
        # 卖出不在目标列表中的股票
        for code in list(positions.keys()):
            if code not in target_codes:
                position = positions[code]
                sell_price = position['price'] * (1 - params.slippage)
                sell_amount = sell_price * position['shares']
                commission = sell_amount * params.commission_rate
                
                capital += sell_amount - commission
                
                trades.append(TradeRecord(
                    date=current_date,
                    code=code,
                    name=position['name'],
                    action='SELL',
                    price=sell_price,
                    shares=position['shares'],
                    amount=sell_amount,
                    commission=commission,
                    reason='再平衡卖出'
                ))
                
                del positions[code]
        
        # 计算每只股票的目标仓位
        position_value = capital * params.position_size
        
        # 买入目标股票
        for stock in selected[:params.max_positions]:
            code = stock['code']
            if code in positions:
                continue  # 已持仓，跳过
            
            buy_price = stock.get('price', 0)
            if buy_price <= 0:
                continue
            
            # 计算可买入股数（100股为单位）
            max_shares = int(position_value / buy_price / 100) * 100
            
            if max_shares < 100:
                continue  # 资金不足
            
            buy_amount = buy_price * max_shares
            commission = buy_amount * params.commission_rate
            total_cost = buy_amount + commission
            
            if total_cost > capital:
                continue  # 资金不足
            
            capital -= total_cost
            
            positions[code] = {
                'code': code,
                'name': stock.get('name', ''),
                'price': buy_price,
                'shares': max_shares,
                'cost': total_cost
            }
            
            trades.append(TradeRecord(
                date=current_date,
                code=code,
                name=stock.get('name', ''),
                action='BUY',
                price=buy_price,
                shares=max_shares,
                amount=buy_amount,
                commission=commission,
                reason='再平衡买入'
            ))
        
        return capital, positions, trades
    
    def _calculate_equity(self, capital: float, positions: Dict, 
                          current_date: date) -> float:
        """计算当前权益"""
        equity = capital
        for code, position in positions.items():
            # 简化处理：使用持仓成本价
            # 实际应该获取当日收盘价
            equity += position['price'] * position['shares']
        return equity
    
    def _calculate_performance(self, backtest_id: str, params: BacktestParams,
                               equity_curve: List[Dict], trades: List[TradeRecord],
                               execution_time: float) -> BacktestResult:
        """计算绩效指标"""
        if not equity_curve:
            raise ValueError("回测结果为空")
        
        # 提取权益序列
        equities = [e['equity'] for e in equity_curve]
        initial_equity = params.initial_capital
        final_equity = equities[-1]
        
        # 计算收益率
        total_return = (final_equity - initial_equity) / initial_equity * 100
        
        # 计算年化收益率
        days = (params.end_date - params.start_date).days
        years = days / 365
        annualized_return = (pow(final_equity / initial_equity, 1/years) - 1) * 100 if years > 0 else 0
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(equities)
        
        # 计算波动率
        returns = [(equities[i] - equities[i-1]) / equities[i-1] 
                  for i in range(1, len(equities))]
        volatility = np.std(returns) * np.sqrt(252) * 100 if returns else 0
        
        # 计算夏普比率（假设无风险利率3%）
        risk_free_rate = 0.03
        if volatility > 0:
            sharpe_ratio = (annualized_return / 100 - risk_free_rate) / (volatility / 100)
        else:
            sharpe_ratio = 0
        
        # 交易统计
        total_trades = len(trades)
        buy_trades = [t for t in trades if t.action == 'BUY']
        
        # 简化盈亏计算（实际应该配对买卖）
        winning_trades = total_trades // 3  # 假设1/3盈利
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        # 月度收益
        monthly_returns = self._calculate_monthly_returns(equity_curve)
        
        # 基准收益（简化，假设年化8%）
        benchmark_return = 8.0
        excess_return = annualized_return - benchmark_return
        
        return BacktestResult(
            backtest_id=backtest_id,
            strategy_id=params.strategy_id,
            start_date=params.start_date,
            end_date=params.end_date,
            total_return=total_return,
            annualized_return=annualized_return,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sharpe_ratio,  # 简化
            calmar_ratio=annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=1.5,  # 简化
            avg_profit=0,  # 简化
            avg_loss=0,  # 简化
            equity_curve=equity_curve,
            trades=trades,
            monthly_returns=monthly_returns,
            execution_time=execution_time
        )
    
    def _calculate_max_drawdown(self, equities: List[float]) -> float:
        """计算最大回撤"""
        peak = equities[0]
        max_dd = 0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)
        
        return -max_dd * 100
    
    def _calculate_monthly_returns(self, equity_curve: List[Dict]) -> List[Dict]:
        """计算月度收益"""
        if not equity_curve:
            return []
        
        # 按月份分组
        monthly_data = {}
        for item in equity_curve:
            date = datetime.fromisoformat(item['date'])
            month_key = date.strftime('%Y-%m')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {'start': item['equity'], 'end': item['equity']}
            else:
                monthly_data[month_key]['end'] = item['equity']
        
        # 计算月收益率
        monthly_returns = []
        for month, data in monthly_data.items():
            ret = (data['end'] - data['start']) / data['start'] * 100
            monthly_returns.append({
                'month': month,
                'return': round(ret, 2)
            })
        
        return monthly_returns
    
    def _save_backtest_record(self, strategy_id: str, result: BacktestResult):
        """保存回测记录"""
        try:
            record = BacktestRecord(
                strategy_id=strategy_id,
                start_date=result.start_date,
                end_date=result.end_date,
                initial_capital=result.equity_curve[0]['equity'] if result.equity_curve else 1000000,
                final_capital=result.equity_curve[-1]['equity'] if result.equity_curve else 0,
                total_return=result.total_return,
                annual_return=result.annualized_return,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                trade_count=result.total_trades,
                win_count=result.winning_trades,
                loss_count=result.losing_trades,
                win_rate=result.win_rate,
                result_detail=str({
                    'equity_curve_sample': result.equity_curve[:10],
                    'trades_sample': [{'date': t.date.isoformat(), 'code': t.code, 'action': t.action} 
                                     for t in result.trades[:10]]
                })
            )
            self.backtest_repo.save(record)
            
            # 更新策略回测统计
            self.strategy_repo.update_backtest_stats(strategy_id)
        except Exception as e:
            logger.error(f"保存回测记录失败: {e}")
    
    def get_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """
        获取回测结果
        
        Args:
            backtest_id: 回测ID
            
        Returns:
            回测结果
        """
        # 实际实现应该从数据库或缓存获取
        logger.warning("获取历史回测结果功能待实现")
        return None
