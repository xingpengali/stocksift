# -*- coding: utf-8 -*-
"""
估值分析模块

提供估值指标计算和估值分析
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal

import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


class ValuationAnalyzer:
    """
    估值分析器
    
    计算各类估值指标和内在价值
    """
    
    def __init__(self, stock_code: str, quote: Dict, financial: Dict,
                 historical_valuations: Optional[List[Dict]] = None):
        """
        初始化
        
        Args:
            stock_code: 股票代码
            quote: 行情数据
            financial: 财务数据
            historical_valuations: 历史估值数据
        """
        self.stock_code = stock_code
        self.quote = quote or {}
        self.financial = financial or {}
        self.historical = pd.DataFrame(historical_valuations or [])
    
    def pe_ratio(self) -> Dict:
        """
        市盈率分析
        
        Returns:
            PE相关指标
        """
        # 当前价格
        current_price = self.quote.get('close', 0)
        
        # EPS (每股收益)
        eps_ttm = self.financial.get('eps_ttm', 0)
        eps_lyr = self.financial.get('eps', 0)
        
        # 计算PE
        pe_ttm = self._safe_divide(current_price, eps_ttm)
        pe_lyr = self._safe_divide(current_price, eps_lyr)
        
        # 历史百分位
        percentile = self._calculate_percentile('pe_ttm', pe_ttm)
        
        # 评估
        assessment = self._assess_pe(pe_ttm)
        
        return {
            'pe_ttm': round(pe_ttm, 2),
            'pe_lyr': round(pe_lyr, 2),
            'eps_ttm': round(eps_ttm, 2),
            'historical_percentile': percentile,
            'assessment': assessment,
            'industry_avg': self._get_industry_avg_pe()
        }
    
    def _assess_pe(self, pe: float) -> str:
        """评估PE水平"""
        if pe <= 0:
            return "loss_making"
        elif pe < 10:
            return "undervalued"
        elif pe < 20:
            return "reasonable"
        elif pe < 30:
            return "slightly_overvalued"
        elif pe < 50:
            return "overvalued"
        return "highly_overvalued"
    
    def pb_ratio(self) -> Dict:
        """
        市净率分析
        
        Returns:
            PB相关指标
        """
        current_price = self.quote.get('close', 0)
        bps = self.financial.get('bps', 0)  # 每股净资产
        
        pb = self._safe_divide(current_price, bps)
        
        # 历史百分位
        percentile = self._calculate_percentile('pb', pb)
        
        # ROE-PB 评估（适用于价值股）
        roe = self.financial.get('roe', 0)
        roe_pb_ratio = self._safe_divide(roe, pb)
        
        return {
            'pb': round(pb, 2),
            'bps': round(bps, 2),
            'roe': round(roe, 2),
            'roe_pb_ratio': round(roe_pb_ratio, 2),
            'historical_percentile': percentile,
            'assessment': self._assess_pb(pb, roe)
        }
    
    def _assess_pb(self, pb: float, roe: float) -> str:
        """评估PB水平"""
        if pb <= 0:
            return "invalid"
        elif pb < 1:
            return "undervalued"
        elif pb < 2:
            return "reasonable"
        elif pb < 3:
            return "slightly_overvalued"
        elif pb < 5:
            return "overvalued"
        return "highly_overvalued"
    
    def ps_ratio(self) -> Dict:
        """
        市销率分析
        
        Returns:
            PS相关指标
        """
        current_price = self.quote.get('close', 0)
        total_revenue = self.financial.get('total_revenue', 0)
        total_shares = self.financial.get('total_shares', 1)
        
        # 每股营收
        revenue_per_share = self._safe_divide(total_revenue, total_shares)
        ps = self._safe_divide(current_price, revenue_per_share)
        
        return {
            'ps': round(ps, 2),
            'revenue_per_share': round(revenue_per_share, 2),
            'assessment': self._assess_ps(ps)
        }
    
    def _assess_ps(self, ps: float) -> str:
        """评估PS水平"""
        if ps <= 0:
            return "invalid"
        elif ps < 1:
            return "undervalued"
        elif ps < 3:
            return "reasonable"
        elif ps < 5:
            return "slightly_overvalued"
        return "overvalued"
    
    def pcf_ratio(self) -> Dict:
        """
        市现率分析
        
        Returns:
            PCF相关指标
        """
        current_price = self.quote.get('close', 0)
        operating_cf = self.financial.get('operating_cash_flow', 0)
        total_shares = self.financial.get('total_shares', 1)
        
        # 每股经营现金流
        cf_per_share = self._safe_divide(operating_cf, total_shares)
        pcf = self._safe_divide(current_price, cf_per_share)
        
        return {
            'pcf': round(pcf, 2),
            'cf_per_share': round(cf_per_share, 2),
            'assessment': self._assess_pcf(pcf)
        }
    
    def _assess_pcf(self, pcf: float) -> str:
        """评估PCF水平"""
        if pcf <= 0:
            return "negative_cf"
        elif pcf < 10:
            return "undervalued"
        elif pcf < 15:
            return "reasonable"
        elif pcf < 25:
            return "slightly_overvalued"
        return "overvalued"
    
    def peg_ratio(self) -> Dict:
        """
        PEG比率分析
        
        PEG = PE / 盈利增长率
        
        Returns:
            PEG相关指标
        """
        pe_data = self.pe_ratio()
        pe = pe_data.get('pe_ttm', 0)
        
        # 获取盈利增长率
        profit_growth = self.financial.get('profit_growth', 0)
        
        # 计算PEG
        peg = self._safe_divide(pe, profit_growth)
        
        return {
            'peg': round(peg, 2),
            'pe': pe,
            'growth_rate': round(profit_growth, 2),
            'assessment': self._assess_peg(peg)
        }
    
    def _assess_peg(self, peg: float) -> str:
        """评估PEG水平"""
        if peg <= 0:
            return "invalid"
        elif peg < 0.5:
            return "significantly_undervalued"
        elif peg < 1:
            return "undervalued"
        elif peg < 1.5:
            return "fairly_valued"
        elif peg < 2:
            return "slightly_overvalued"
        return "overvalued"
    
    def ev_ebitda(self) -> Dict:
        """
        EV/EBITDA分析
        
        Returns:
            EV/EBITDA指标
        """
        # 企业价值 = 市值 + 总负债 - 现金
        market_cap = self.quote.get('market_cap', 0)
        total_debt = self.financial.get('total_liabilities', 0)
        cash = self.financial.get('cash', 0)
        
        ev = market_cap + total_debt - cash
        ebitda = self.financial.get('ebitda', 0)
        
        ev_ebitda = self._safe_divide(ev, ebitda)
        
        return {
            'ev_ebitda': round(ev_ebitda, 2),
            'enterprise_value': round(ev, 2),
            'ebitda': round(ebitda, 2),
            'assessment': self._assess_ev_ebitda(ev_ebitda)
        }
    
    def _assess_ev_ebitda(self, ratio: float) -> str:
        """评估EV/EBITDA水平"""
        if ratio <= 0:
            return "invalid"
        elif ratio < 8:
            return "undervalued"
        elif ratio < 12:
            return "reasonable"
        elif ratio < 15:
            return "slightly_overvalued"
        return "overvalued"
    
    def historical_percentile(self, years: int = 5) -> Dict:
        """
        计算历史估值百分位
        
        Args:
            years: 历史年数
            
        Returns:
            历史百分位数据
        """
        if self.historical.empty:
            return {}
        
        # 过滤最近N年的数据
        cutoff_date = datetime.now().date().replace(year=datetime.now().year - years)
        recent_data = self.historical[
            pd.to_datetime(self.historical['trade_date']) >= pd.Timestamp(cutoff_date)
        ]
        
        if recent_data.empty:
            return {}
        
        current_pe = self.pe_ratio().get('pe_ttm', 0)
        current_pb = self.pb_ratio().get('pb', 0)
        
        return {
            'pe_percentile': self._calculate_series_percentile(
                recent_data['pe_ttm'].values, current_pe
            ),
            'pb_percentile': self._calculate_series_percentile(
                recent_data['pb'].values, current_pb
            ),
            'pe_min': round(recent_data['pe_ttm'].min(), 2),
            'pe_max': round(recent_data['pe_ttm'].max(), 2),
            'pe_median': round(recent_data['pe_ttm'].median(), 2),
            'pb_min': round(recent_data['pb'].min(), 2),
            'pb_max': round(recent_data['pb'].max(), 2),
            'pb_median': round(recent_data['pb'].median(), 2)
        }
    
    def _calculate_percentile(self, metric: str, current_value: float) -> int:
        """计算历史百分位"""
        if self.historical.empty or metric not in self.historical.columns:
            return 50  # 默认中位数
        
        values = self.historical[metric].dropna().values
        return self._calculate_series_percentile(values, current_value)
    
    def _calculate_series_percentile(self, values: np.ndarray, 
                                      current: float) -> int:
        """计算百分位"""
        if len(values) == 0:
            return 50
        
        return int(np.sum(values <= current) / len(values) * 100)
    
    def dcf_valuation(self, growth_rate: float = 0.05,
                      discount_rate: float = 0.10,
                      terminal_growth: float = 0.03,
                      forecast_years: int = 5) -> Dict:
        """
        DCF现金流折现估值
        
        Args:
            growth_rate: 预期增长率
            discount_rate: 折现率
            terminal_growth: 永续增长率
            forecast_years: 预测年数
            
        Returns:
            DCF估值结果
        """
        # 获取当前自由现金流
        fcf = self.financial.get('free_cash_flow', 0)
        if fcf <= 0:
            return {'error': '自由现金流为负，无法使用DCF估值'}
        
        # 预测未来现金流
        cash_flows = []
        for year in range(1, forecast_years + 1):
            cf = fcf * pow(1 + growth_rate, year)
            pv = cf / pow(1 + discount_rate, year)
            cash_flows.append({
                'year': year,
                'cash_flow': round(cf, 2),
                'present_value': round(pv, 2)
            })
        
        # 计算预测期现值
        pv_forecast = sum(cf['present_value'] for cf in cash_flows)
        
        # 计算终值
        terminal_cf = fcf * pow(1 + growth_rate, forecast_years) * (1 + terminal_growth)
        terminal_value = terminal_cf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / pow(1 + discount_rate, forecast_years)
        
        # 企业价值
        enterprise_value = pv_forecast + pv_terminal
        
        # 每股价值
        total_shares = self.financial.get('total_shares', 1)
        intrinsic_value = enterprise_value / total_shares
        
        # 与当前价格比较
        current_price = self.quote.get('close', 0)
        upside = (intrinsic_value - current_price) / current_price * 100 if current_price > 0 else 0
        
        return {
            'intrinsic_value': round(intrinsic_value, 2),
            'current_price': round(current_price, 2),
            'upside_potential': round(upside, 2),
            'enterprise_value': round(enterprise_value, 2),
            'pv_forecast': round(pv_forecast, 2),
            'pv_terminal': round(pv_terminal, 2),
            'cash_flows': cash_flows,
            'assessment': 'undervalued' if upside > 20 else 'fairly_valued' if upside > -10 else 'overvalued'
        }
    
    def graham_valuation(self) -> Dict:
        """
        格雷厄姆估值
        
        公式：内在价值 = EPS × (8.5 + 2g)
        其中g为未来7-10年的预期增长率
        
        Returns:
            格雷厄姆估值结果
        """
        eps = self.financial.get('eps_ttm', 0)
        
        # 使用历史增长率作为预期增长率
        growth_rate = self.financial.get('profit_growth', 0) / 100
        
        # 格雷厄姆公式
        intrinsic_value = eps * (8.5 + 2 * growth_rate * 100)
        
        current_price = self.quote.get('close', 0)
        upside = (intrinsic_value - current_price) / current_price * 100 if current_price > 0 else 0
        
        return {
            'intrinsic_value': round(intrinsic_value, 2),
            'current_price': round(current_price, 2),
            'upside_potential': round(upside, 2),
            'eps': round(eps, 2),
            'growth_rate': round(growth_rate * 100, 2),
            'assessment': 'undervalued' if upside > 20 else 'fairly_valued' if upside > -10 else 'overvalued'
        }
    
    def valuation_assessment(self) -> Dict:
        """
        综合估值评估
        
        Returns:
            综合评估结果
        """
        pe = self.pe_ratio()
        pb = self.pb_ratio()
        peg = self.peg_ratio()
        ps = self.ps_ratio()
        
        # 计算综合评分
        scores = []
        
        # PE评分
        pe_assessment = pe.get('assessment', '')
        if pe_assessment == 'undervalued':
            scores.append(2)
        elif pe_assessment == 'reasonable':
            scores.append(1)
        elif pe_assessment in ['overvalued', 'highly_overvalued']:
            scores.append(-1)
        
        # PB评分
        pb_assessment = pb.get('assessment', '')
        if pb_assessment == 'undervalued':
            scores.append(2)
        elif pb_assessment == 'reasonable':
            scores.append(1)
        elif pb_assessment in ['overvalued', 'highly_overvalued']:
            scores.append(-1)
        
        # PEG评分
        peg_assessment = peg.get('assessment', '')
        if peg_assessment in ['significantly_undervalued', 'undervalued']:
            scores.append(2)
        elif peg_assessment == 'fairly_valued':
            scores.append(1)
        elif peg_assessment in ['overvalued', 'slightly_overvalued']:
            scores.append(-1)
        
        total_score = sum(scores)
        
        if total_score >= 4:
            overall = "significantly_undervalued"
        elif total_score >= 2:
            overall = "undervalued"
        elif total_score >= 0:
            overall = "fairly_valued"
        elif total_score >= -2:
            overall = "slightly_overvalued"
        else:
            overall = "overvalued"
        
        return {
            'overall_assessment': overall,
            'score': total_score,
            'metrics': {
                'pe': pe,
                'pb': pb,
                'peg': peg,
                'ps': ps
            },
            'summary': self._generate_summary(overall, pe, pb, peg)
        }
    
    def _generate_summary(self, overall: str, pe: Dict, pb: Dict, 
                          peg: Dict) -> str:
        """生成估值摘要"""
        summaries = []
        
        if overall == "significantly_undervalued":
            summaries.append("该股票估值显著偏低，具备较高的安全边际")
        elif overall == "undervalued":
            summaries.append("该股票估值偏低，具有一定的投资价值")
        elif overall == "fairly_valued":
            summaries.append("该股票估值处于合理区间")
        elif overall == "slightly_overvalued":
            summaries.append("该股票估值略高，建议谨慎")
        else:
            summaries.append("该股票估值偏高，注意风险")
        
        pe_ttm = pe.get('pe_ttm', 0)
        if pe_ttm > 0:
            summaries.append(f"当前PE(TTM)为{pe_ttm}倍")
        
        return "；".join(summaries)
    
    def _get_industry_avg_pe(self) -> float:
        """获取行业平均PE"""
        # 简化实现，实际应该从行业数据获取
        return 15.0
    
    def analyze(self) -> Dict:
        """
        完整估值分析
        
        Returns:
            完整分析结果
        """
        return {
            'pe': self.pe_ratio(),
            'pb': self.pb_ratio(),
            'ps': self.ps_ratio(),
            'pcf': self.pcf_ratio(),
            'peg': self.peg_ratio(),
            'ev_ebitda': self.ev_ebitda(),
            'historical_percentile': self.historical_percentile(),
            'dcf': self.dcf_valuation(),
            'graham': self.graham_valuation(),
            'assessment': self.valuation_assessment()
        }
    
    @staticmethod
    def _safe_divide(numerator, denominator):
        """安全除法"""
        try:
            num = float(numerator) if numerator else 0
            den = float(denominator) if denominator else 0
            if den == 0:
                return 0
            return num / den
        except (TypeError, ValueError):
            return 0
