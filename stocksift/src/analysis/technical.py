# -*- coding: utf-8 -*-
"""
技术分析模块

提供技术指标计算和信号识别
"""
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


class SignalType(Enum):
    """信号类型"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class TechnicalSignal:
    """技术信号"""
    indicator: str
    signal: SignalType
    value: float
    description: str


class TechnicalAnalyzer:
    """
    技术分析器
    
    计算各种技术指标和信号
    """
    
    def __init__(self, kline_data: pd.DataFrame):
        """
        初始化
        
        Args:
            kline_data: K线数据DataFrame，需包含open, high, low, close, volume列
        """
        self.data = kline_data.copy()
        self.signals: List[TechnicalSignal] = []
        
        # 确保数据按日期排序
        if 'trade_date' in self.data.columns:
            self.data = self.data.sort_values('trade_date')
    
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        计算MACD指标
        
        Args:
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            MACD指标数据
        """
        close = self.data['close']
        
        # 计算EMA
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        # DIF线
        dif = ema_fast - ema_slow
        
        # DEA线
        dea = dif.ewm(span=signal, adjust=False).mean()
        
        # MACD柱
        macd_bar = (dif - dea) * 2
        
        # 判断信号
        signal_type = self._macd_signal(dif, dea, macd_bar)
        
        return {
            'dif': round(dif.iloc[-1], 4),
            'dea': round(dea.iloc[-1], 4),
            'macd': round(macd_bar.iloc[-1], 4),
            'signal': signal_type,
            'trend': 'up' if macd_bar.iloc[-1] > macd_bar.iloc[-2] else 'down'
        }
    
    def _macd_signal(self, dif: pd.Series, dea: pd.Series, 
                     macd_bar: pd.Series) -> str:
        """判断MACD信号"""
        if len(dif) < 2:
            return "neutral"
        
        # 金叉：DIF上穿DEA
        if dif.iloc[-2] <= dea.iloc[-2] and dif.iloc[-1] > dea.iloc[-1]:
            if macd_bar.iloc[-1] > 0:
                return "golden_cross"
        
        # 死叉：DIF下穿DEA
        if dif.iloc[-2] >= dea.iloc[-2] and dif.iloc[-1] < dea.iloc[-1]:
            if macd_bar.iloc[-1] < 0:
                return "death_cross"
        
        return "neutral"
    
    def kdj(self, n: int = 9, m1: int = 3, m2: int = 3) -> Dict:
        """
        计算KDJ指标
        
        Args:
            n: RSV周期
            m1: K线平滑周期
            m2: D线平滑周期
            
        Returns:
            KDJ指标数据
        """
        low_list = self.data['low'].rolling(window=n, min_periods=n).min()
        high_list = self.data['high'].rolling(window=n, min_periods=n).max()
        
        # RSV
        rsv = (self.data['close'] - low_list) / (high_list - low_list) * 100
        
        # K线
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        
        # D线
        d = k.ewm(com=m2-1, adjust=False).mean()
        
        # J线
        j = 3 * k - 2 * d
        
        # 判断信号
        signal_type = self._kdj_signal(k, d, j)
        
        return {
            'k': round(k.iloc[-1], 2),
            'd': round(d.iloc[-1], 2),
            'j': round(j.iloc[-1], 2),
            'signal': signal_type
        }
    
    def _kdj_signal(self, k: pd.Series, d: pd.Series, j: pd.Series) -> str:
        """判断KDJ信号"""
        k_val, d_val, j_val = k.iloc[-1], d.iloc[-1], j.iloc[-1]
        
        # 超卖区金叉
        if k_val < 20 and d_val < 20:
            if k.iloc[-2] <= d.iloc[-2] and k_val > d_val:
                return "oversold_golden_cross"
        
        # 超买区死叉
        if k_val > 80 and d_val > 80:
            if k.iloc[-2] >= d.iloc[-2] and k_val < d_val:
                return "overbought_death_cross"
        
        # 普通金叉
        if k.iloc[-2] <= d.iloc[-2] and k_val > d_val:
            return "golden_cross"
        
        # 普通死叉
        if k.iloc[-2] >= d.iloc[-2] and k_val < d_val:
            return "death_cross"
        
        return "neutral"
    
    def rsi(self, periods: List[int] = [6, 12, 24]) -> Dict:
        """
        计算RSI指标
        
        Args:
            periods: RSI周期列表
            
        Returns:
            RSI指标数据
        """
        close = self.data['close']
        delta = close.diff()
        
        result = {}
        for period in periods:
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            result[f'rsi{period}'] = round(rsi.iloc[-1], 2)
        
        # 判断信号
        rsi6 = result.get('rsi6', 50)
        if rsi6 > 80:
            result['signal'] = "overbought"
        elif rsi6 < 20:
            result['signal'] = "oversold"
        else:
            result['signal'] = "neutral"
        
        return result
    
    def ma(self, periods: List[int] = [5, 10, 20, 60]) -> Dict:
        """
        计算均线系统
        
        Args:
            periods: 均线周期列表
            
        Returns:
            均线数据
        """
        close = self.data['close']
        result = {}
        
        for period in periods:
            ma_value = close.rolling(window=period).mean()
            result[f'ma{period}'] = round(ma_value.iloc[-1], 2)
        
        # 判断均线排列
        result['alignment'] = self._ma_alignment(periods)
        
        return result
    
    def _ma_alignment(self, periods: List[int] = [5, 10, 20, 60]) -> str:
        """判断均线排列形态"""
        close = self.data['close']
        
        if len(close) < max(periods):
            return "unknown"
        
        ma_values = {}
        for period in periods:
            ma_values[period] = close.rolling(window=period).mean().iloc[-1]
        
        # 多头排列：短期均线在长期均线上方
        if ma_values[5] > ma_values[10] > ma_values[20] > ma_values[60]:
            return "bull"
        
        # 空头排列：短期均线在长期均线下方
        if ma_values[5] < ma_values[10] < ma_values[20] < ma_values[60]:
            return "bear"
        
        return "none"
    
    def boll(self, period: int = 20, std_dev: int = 2) -> Dict:
        """
        计算布林带
        
        Args:
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            布林带数据
        """
        close = self.data['close']
        
        # 中轨（移动平均线）
        middle = close.rolling(window=period).mean()
        
        # 标准差
        std = close.rolling(window=period).std()
        
        # 上轨和下轨
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        # 当前价格在布林带中的位置
        current_price = close.iloc[-1]
        upper_val = upper.iloc[-1]
        lower_val = lower.iloc[-1]
        
        if current_price > upper_val:
            position = "above_upper"
        elif current_price < lower_val:
            position = "below_lower"
        elif current_price > middle.iloc[-1]:
            position = "upper_half"
        else:
            position = "lower_half"
        
        # 带宽（波动率）
        bandwidth = (upper_val - lower_val) / middle.iloc[-1] * 100
        
        return {
            'upper': round(upper_val, 2),
            'middle': round(middle.iloc[-1], 2),
            'lower': round(lower_val, 2),
            'position': position,
            'bandwidth': round(bandwidth, 2)
        }
    
    def volume_analysis(self) -> Dict:
        """
        成交量分析
        
        Returns:
            成交量分析结果
        """
        volume = self.data['volume']
        close = self.data['close']
        
        # 均量
        vol_ma5 = volume.rolling(window=5).mean().iloc[-1]
        vol_ma10 = volume.rolling(window=10).mean().iloc[-1]
        
        # 量比（当前成交量/5日均量）
        volume_ratio = volume.iloc[-1] / vol_ma5 if vol_ma5 > 0 else 0
        
        # 量价关系
        price_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        
        if price_change > 0 and volume.iloc[-1] > vol_ma5:
            relationship = "price_up_volume_up"
        elif price_change > 0 and volume.iloc[-1] < vol_ma5:
            relationship = "price_up_volume_down"
        elif price_change < 0 and volume.iloc[-1] > vol_ma5:
            relationship = "price_down_volume_up"
        else:
            relationship = "price_down_volume_down"
        
        return {
            'current_volume': int(volume.iloc[-1]),
            'vol_ma5': int(vol_ma5),
            'vol_ma10': int(vol_ma10),
            'volume_ratio': round(volume_ratio, 2),
            'relationship': relationship
        }
    
    def support_resistance(self, window: int = 20) -> Dict:
        """
        计算支撑位和阻力位
        
        Args:
            window: 计算窗口
            
        Returns:
            支撑阻力位
        """
        high = self.data['high'].rolling(window=window).max().iloc[-1]
        low = self.data['low'].rolling(window=window).min().iloc[-1]
        close = self.data['close'].iloc[-1]
        
        # 简单计算：最近最高价作为阻力，最近最低价作为支撑
        return {
            'resistance': round(high, 2),
            'support': round(low, 2),
            'current': round(close, 2),
            'position': (close - low) / (high - low) if high > low else 0.5
        }
    
    def composite_signal(self) -> Dict:
        """
        综合信号分析
        
        Returns:
            综合分析结果
        """
        signals = []
        score = 50  # 基础分50分
        
        # MACD信号
        macd_data = self.macd()
        if macd_data['signal'] == 'golden_cross':
            signals.append(TechnicalSignal('MACD', SignalType.BUY, macd_data['macd'], 'MACD金叉'))
            score += 10
        elif macd_data['signal'] == 'death_cross':
            signals.append(TechnicalSignal('MACD', SignalType.SELL, macd_data['macd'], 'MACD死叉'))
            score -= 10
        
        # KDJ信号
        kdj_data = self.kdj()
        if 'golden_cross' in kdj_data['signal']:
            signals.append(TechnicalSignal('KDJ', SignalType.BUY, kdj_data['j'], 'KDJ金叉'))
            score += 10
        elif 'death_cross' in kdj_data['signal']:
            signals.append(TechnicalSignal('KDJ', SignalType.SELL, kdj_data['j'], 'KDJ死叉'))
            score -= 10
        
        # RSI信号
        rsi_data = self.rsi()
        if rsi_data['signal'] == 'oversold':
            signals.append(TechnicalSignal('RSI', SignalType.BUY, rsi_data['rsi6'], 'RSI超卖'))
            score += 5
        elif rsi_data['signal'] == 'overbought':
            signals.append(TechnicalSignal('RSI', SignalType.SELL, rsi_data['rsi6'], 'RSI超买'))
            score -= 5
        
        # 均线排列
        ma_data = self.ma()
        if ma_data['alignment'] == 'bull':
            signals.append(TechnicalSignal('MA', SignalType.BUY, 0, '均线多头排列'))
            score += 10
        elif ma_data['alignment'] == 'bear':
            signals.append(TechnicalSignal('MA', SignalType.SELL, 0, '均线空头排列'))
            score -= 10
        
        # 布林带
        boll_data = self.boll()
        if boll_data['position'] == 'below_lower':
            signals.append(TechnicalSignal('BOLL', SignalType.BUY, boll_data['lower'], '触及下轨'))
            score += 5
        elif boll_data['position'] == 'above_upper':
            signals.append(TechnicalSignal('BOLL', SignalType.SELL, boll_data['upper'], '触及上轨'))
            score -= 5
        
        # 确定最终信号
        if score >= 70:
            final_signal = SignalType.STRONG_BUY
        elif score >= 55:
            final_signal = SignalType.BUY
        elif score <= 30:
            final_signal = SignalType.STRONG_SELL
        elif score <= 45:
            final_signal = SignalType.SELL
        else:
            final_signal = SignalType.HOLD
        
        return {
            'signal': final_signal.value,
            'score': score,
            'signals': [
                {
                    'indicator': s.indicator,
                    'signal': s.signal.value,
                    'value': s.value,
                    'description': s.description
                }
                for s in signals
            ],
            'summary': f"技术指标综合评分: {score}/100"
        }
    
    def analyze(self) -> Dict:
        """
        完整技术分析
        
        Returns:
            完整分析结果
        """
        return {
            'macd': self.macd(),
            'kdj': self.kdj(),
            'rsi': self.rsi(),
            'ma': self.ma(),
            'boll': self.boll(),
            'volume': self.volume_analysis(),
            'support_resistance': self.support_resistance(),
            'composite': self.composite_signal()
        }
