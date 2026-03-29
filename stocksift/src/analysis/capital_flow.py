# -*- coding: utf-8 -*-
"""
资金流向分析模块

提供主力资金流向分析和趋势判断
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FlowData:
    """资金流向数据"""
    date: datetime
    main_inflow: float  # 主力净流入
    super_large: float  # 超大单
    large: float  # 大单
    medium: float  # 中单
    small: float  # 小单


class CapitalFlowAnalyzer:
    """
    资金流向分析器
    
    分析主力资金流向和趋势
    """
    
    def __init__(self, flow_data: List[Dict]):
        """
        初始化
        
        Args:
            flow_data: 资金流向数据列表
        """
        self.data = pd.DataFrame(flow_data)
        if not self.data.empty and 'trade_date' in self.data.columns:
            self.data['trade_date'] = pd.to_datetime(self.data['trade_date'])
            self.data = self.data.sort_values('trade_date')
    
    def today_flow(self) -> Dict:
        """
        当日资金流向
        
        Returns:
            当日资金流向数据
        """
        if self.data.empty:
            return {}
        
        today = self.data.iloc[-1]
        
        # 计算主力净流入（超大单+大单）
        main_inflow = today.get('super_large', 0) + today.get('large', 0)
        
        # 散户资金流向（中单+小单）
        retail_flow = today.get('medium', 0) + today.get('small', 0)
        
        # 总成交额
        total_amount = abs(main_inflow) + abs(retail_flow)
        
        # 主力占比
        main_ratio = (main_inflow / total_amount * 100) if total_amount > 0 else 0
        
        return {
            'date': today.get('trade_date').strftime('%Y-%m-%d') if pd.notna(today.get('trade_date')) else '',
            'main_inflow': round(main_inflow, 2),
            'super_large': round(today.get('super_large', 0), 2),
            'large': round(today.get('large', 0), 2),
            'medium': round(today.get('medium', 0), 2),
            'small': round(today.get('small', 0), 2),
            'retail_flow': round(retail_flow, 2),
            'main_ratio': round(main_ratio, 2),
            'direction': 'inflow' if main_inflow > 0 else 'outflow'
        }
    
    def consecutive_inflow_days(self) -> Dict:
        """
        连续净流入天数统计
        
        Returns:
            连续流入天数分析
        """
        if self.data.empty:
            return {}
        
        # 计算每日主力净流入
        self.data['main_flow'] = self.data['super_large'] + self.data['large']
        
        # 判断每日是否净流入
        self.data['is_inflow'] = self.data['main_flow'] > 0
        
        # 计算连续天数
        consecutive = 0
        for i in range(len(self.data) - 1, -1, -1):
            if self.data.iloc[i]['is_inflow']:
                consecutive += 1
            else:
                break
        
        # 历史最大连续流入天数
        max_consecutive = self._calculate_max_consecutive(self.data['is_inflow'].values)
        
        return {
            'current_consecutive': consecutive,
            'max_consecutive_30d': max_consecutive,
            'total_inflow_days': int(self.data['is_inflow'].sum()),
            'total_outflow_days': int((~self.data['is_inflow']).sum())
        }
    
    def _calculate_max_consecutive(self, bool_array: np.ndarray) -> int:
        """计算最大连续True天数"""
        max_count = 0
        current_count = 0
        
        for val in bool_array:
            if val:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def period_flow(self, days: int = 5) -> Dict:
        """
        N日资金流向统计
        
        Args:
            days: 统计天数
            
        Returns:
            N日资金流向数据
        """
        if self.data.empty or len(self.data) < days:
            return {}
        
        recent_data = self.data.tail(days)
        
        # 计算累计流入
        total_main = (recent_data['super_large'] + recent_data['large']).sum()
        total_super = recent_data['super_large'].sum()
        total_large = recent_data['large'].sum()
        total_medium = recent_data['medium'].sum()
        total_small = recent_data['small'].sum()
        
        # 日均流入
        avg_main = total_main / days
        
        # 流入天数占比
        inflow_days = (recent_data['super_large'] + recent_data['large'] > 0).sum()
        inflow_ratio = inflow_days / days * 100
        
        return {
            'period_days': days,
            'total_main_inflow': round(total_main, 2),
            'total_super_large': round(total_super, 2),
            'total_large': round(total_large, 2),
            'total_medium': round(total_medium, 2),
            'total_small': round(total_small, 2),
            'avg_daily_inflow': round(avg_main, 2),
            'inflow_days': int(inflow_days),
            'inflow_days_ratio': round(inflow_ratio, 2),
            'direction': 'inflow' if total_main > 0 else 'outflow'
        }
    
    def flow_trend(self, window: int = 5) -> Dict:
        """
        资金流向趋势分析
        
        Args:
            window: 趋势计算窗口
            
        Returns:
            趋势分析结果
        """
        if self.data.empty or len(self.data) < window:
            return {}
        
        # 计算主力净流入
        self.data['main_flow'] = self.data['super_large'] + self.data['large']
        
        # 计算移动平均
        self.data['flow_ma'] = self.data['main_flow'].rolling(window=window).mean()
        
        # 近期流向
        recent_flow = self.data['main_flow'].tail(window).values
        recent_ma = self.data['flow_ma'].tail(window).values
        
        # 判断趋势
        if len(recent_flow) >= 3:
            # 使用线性回归判断趋势
            x = np.arange(len(recent_flow))
            slope = np.polyfit(x, recent_flow, 1)[0]
            
            if slope > recent_flow.mean() * 0.1:
                trend = "increasing"
                strength = "strong" if slope > recent_flow.mean() * 0.3 else "moderate"
            elif slope < -recent_flow.mean() * 0.1:
                trend = "decreasing"
                strength = "strong" if slope < -recent_flow.mean() * 0.3 else "moderate"
            else:
                trend = "stable"
                strength = "neutral"
        else:
            trend = "insufficient_data"
            strength = "unknown"
        
        # 计算趋势得分
        trend_score = self._calculate_trend_score(recent_flow)
        
        return {
            'trend': trend,
            'strength': strength,
            'trend_score': round(trend_score, 2),
            'recent_avg_flow': round(recent_flow.mean(), 2),
            'momentum': 'accelerating' if trend_score > 0.5 else 'decelerating' if trend_score < -0.5 else 'stable'
        }
    
    def _calculate_trend_score(self, flows: np.ndarray) -> float:
        """计算趋势得分 (-1 到 1)"""
        if len(flows) < 2:
            return 0
        
        # 计算变化率
        changes = np.diff(flows)
        
        # 正变化占比
        positive_ratio = np.sum(changes > 0) / len(changes)
        
        # 归一化到 -1 到 1
        return (positive_ratio - 0.5) * 2
    
    def main_force_control(self, days: int = 10) -> Dict:
        """
        主力控盘度分析
        
        Args:
            days: 分析天数
            
        Returns:
            主力控盘度数据
        """
        if self.data.empty or len(self.data) < days:
            return {}
        
        recent_data = self.data.tail(days)
        
        # 主力资金
        main_flow = (recent_data['super_large'] + recent_data['large']).sum()
        
        # 总成交额
        total_flow = (
            recent_data['super_large'].abs() +
            recent_data['large'].abs() +
            recent_data['medium'].abs() +
            recent_data['small'].abs()
        ).sum()
        
        # 主力控盘度
        control_degree = (abs(main_flow) / total_flow * 100) if total_flow > 0 else 0
        
        # 判断控盘状态
        if control_degree > 60:
            control_status = "high_control"
        elif control_degree > 40:
            control_status = "moderate_control"
        elif control_degree > 20:
            control_status = "low_control"
        else:
            control_status = "no_control"
        
        # 主力态度
        if main_flow > 0:
            attitude = "accumulating"  # 吸筹
        elif main_flow < -total_flow * 0.3:
            attitude = "distributing"  # 出货
        else:
            attitude = "watching"  # 观望
        
        return {
            'control_degree': round(control_degree, 2),
            'control_status': control_status,
            'main_attitude': attitude,
            'accumulation_estimate': round(main_flow, 2) if main_flow > 0 else 0,
            'analysis_days': days
        }
    
    def fund_flow_distribution(self) -> Dict:
        """
        资金流向分布分析
        
        Returns:
            资金分布数据
        """
        if self.data.empty:
            return {}
        
        # 计算各类资金累计
        total_super = self.data['super_large'].sum()
        total_large = self.data['large'].sum()
        total_medium = self.data['medium'].sum()
        total_small = self.data['small'].sum()
        
        total = abs(total_super) + abs(total_large) + abs(total_medium) + abs(total_small)
        
        if total == 0:
            return {}
        
        return {
            'super_large_ratio': round(abs(total_super) / total * 100, 2),
            'large_ratio': round(abs(total_large) / total * 100, 2),
            'medium_ratio': round(abs(total_medium) / total * 100, 2),
            'small_ratio': round(abs(total_small) / total * 100, 2),
            'super_large_direction': 'inflow' if total_super > 0 else 'outflow',
            'large_direction': 'inflow' if total_large > 0 else 'outflow',
            'main_force_net': round(total_super + total_large, 2)
        }
    
    def detect_abnormal_flow(self, threshold: float = 2.0) -> List[Dict]:
        """
        检测异常资金流向
        
        Args:
            threshold: 异常阈值（标准差倍数）
            
        Returns:
            异常流向列表
        """
        if self.data.empty or len(self.data) < 10:
            return []
        
        self.data['main_flow'] = self.data['super_large'] + self.data['large']
        
        # 计算均值和标准差
        mean_flow = self.data['main_flow'].mean()
        std_flow = self.data['main_flow'].std()
        
        anomalies = []
        for idx, row in self.data.iterrows():
            flow = row['main_flow']
            z_score = (flow - mean_flow) / std_flow if std_flow > 0 else 0
            
            if abs(z_score) > threshold:
                anomalies.append({
                    'date': row['trade_date'].strftime('%Y-%m-%d') if pd.notna(row['trade_date']) else '',
                    'flow': round(flow, 2),
                    'z_score': round(z_score, 2),
                    'type': 'abnormal_inflow' if flow > 0 else 'abnormal_outflow'
                })
        
        return anomalies
    
    def analyze(self) -> Dict:
        """
        完整资金流向分析
        
        Returns:
            完整分析结果
        """
        return {
            'today': self.today_flow(),
            'consecutive': self.consecutive_inflow_days(),
            'period_5d': self.period_flow(5),
            'period_10d': self.period_flow(10),
            'trend': self.flow_trend(),
            'control': self.main_force_control(),
            'distribution': self.fund_flow_distribution(),
            'anomalies': self.detect_abnormal_flow()
        }
