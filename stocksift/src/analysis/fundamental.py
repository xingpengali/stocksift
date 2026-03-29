# -*- coding: utf-8 -*-
"""
基本面分析模块

提供财务指标计算和基本面分析
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal

import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FinancialMetrics:
    """财务指标数据类"""
    roe: float  # 净资产收益率
    roa: float  # 总资产收益率
    gross_margin: float  # 毛利率
    net_margin: float  # 净利率
    revenue_growth: float  # 营收增长率
    profit_growth: float  # 净利润增长率
    eps: float  # 每股收益
    bps: float  # 每股净资产


class FundamentalAnalyzer:
    """
    基本面分析器
    
    计算财务指标和进行基本面分析
    """
    
    def __init__(self, financial_data: List[Dict]):
        """
        初始化
        
        Args:
            financial_data: 财务数据列表，按报告期排序
        """
        self.data = pd.DataFrame(financial_data)
        if not self.data.empty and 'report_date' in self.data.columns:
            self.data = self.data.sort_values('report_date')
    
    def profitability(self) -> Dict:
        """
        盈利能力分析
        
        Returns:
            盈利能力指标
        """
        if self.data.empty:
            return {}
        
        latest = self.data.iloc[-1]
        
        # 计算ROE
        roe = self._safe_divide(
            latest.get('net_profit', 0),
            latest.get('total_equity', 0)
        ) * 100
        
        # 计算ROA
        roa = self._safe_divide(
            latest.get('net_profit', 0),
            latest.get('total_assets', 0)
        ) * 100
        
        # 毛利率
        gross_margin = self._safe_divide(
            latest.get('gross_profit', 0),
            latest.get('total_revenue', 0)
        ) * 100
        
        # 净利率
        net_margin = self._safe_divide(
            latest.get('net_profit', 0),
            latest.get('total_revenue', 0)
        ) * 100
        
        return {
            'roe': round(roe, 2),
            'roa': round(roa, 2),
            'gross_margin': round(gross_margin, 2),
            'net_margin': round(net_margin, 2),
            'assessment': self._assess_profitability(roe, gross_margin, net_margin)
        }
    
    def _assess_profitability(self, roe: float, gross_margin: float, 
                              net_margin: float) -> str:
        """评估盈利能力"""
        score = 0
        if roe > 15:
            score += 2
        elif roe > 10:
            score += 1
        
        if gross_margin > 30:
            score += 2
        elif gross_margin > 20:
            score += 1
        
        if net_margin > 15:
            score += 2
        elif net_margin > 8:
            score += 1
        
        if score >= 5:
            return "excellent"
        elif score >= 3:
            return "good"
        elif score >= 1:
            return "average"
        return "poor"
    
    def growth(self) -> Dict:
        """
        成长能力分析
        
        Returns:
            成长能力指标
        """
        if len(self.data) < 2:
            return {}
        
        # 营收增长率（同比）
        current = self.data.iloc[-1]
        previous = self.data.iloc[-2]
        
        revenue_growth = self._safe_divide(
            current.get('total_revenue', 0) - previous.get('total_revenue', 0),
            previous.get('total_revenue', 0)
        ) * 100
        
        # 净利润增长率
        profit_growth = self._safe_divide(
            current.get('net_profit', 0) - previous.get('net_profit', 0),
            previous.get('net_profit', 0)
        ) * 100
        
        # 计算多年复合增长率
        cagr_revenue = self._calculate_cagr('total_revenue')
        cagr_profit = self._calculate_cagr('net_profit')
        
        return {
            'revenue_growth': round(revenue_growth, 2),
            'profit_growth': round(profit_growth, 2),
            'revenue_cagr_3y': round(cagr_revenue, 2),
            'profit_cagr_3y': round(cagr_profit, 2),
            'assessment': self._assess_growth(revenue_growth, profit_growth)
        }
    
    def _calculate_cagr(self, column: str, years: int = 3) -> float:
        """计算复合增长率"""
        if len(self.data) < years:
            return 0
        
        start_value = self.data.iloc[-years].get(column, 0)
        end_value = self.data.iloc[-1].get(column, 0)
        
        if start_value <= 0:
            return 0
        
        return (pow(end_value / start_value, 1/years) - 1) * 100
    
    def _assess_growth(self, revenue_growth: float, profit_growth: float) -> str:
        """评估成长能力"""
        if revenue_growth > 20 and profit_growth > 20:
            return "high_growth"
        elif revenue_growth > 10 and profit_growth > 10:
            return "steady_growth"
        elif revenue_growth > 0 and profit_growth > 0:
            return "slow_growth"
        return "declining"
    
    def efficiency(self) -> Dict:
        """
        运营效率分析
        
        Returns:
            运营效率指标
        """
        if self.data.empty:
            return {}
        
        latest = self.data.iloc[-1]
        
        # 总资产周转率
        asset_turnover = self._safe_divide(
            latest.get('total_revenue', 0),
            latest.get('total_assets', 0)
        )
        
        # 存货周转率（如果有存货数据）
        inventory_turnover = self._safe_divide(
            latest.get('cost_of_revenue', 0),
            latest.get('inventory', 1)  # 避免除零
        )
        
        # 应收账款周转率
        receivable_turnover = self._safe_divide(
            latest.get('total_revenue', 0),
            latest.get('accounts_receivable', 1)
        )
        
        return {
            'asset_turnover': round(asset_turnover, 2),
            'inventory_turnover': round(inventory_turnover, 2),
            'receivable_turnover': round(receivable_turnover, 2),
            'assessment': self._assess_efficiency(asset_turnover)
        }
    
    def _assess_efficiency(self, asset_turnover: float) -> str:
        """评估运营效率"""
        if asset_turnover > 1.0:
            return "high"
        elif asset_turnover > 0.5:
            return "medium"
        return "low"
    
    def solvency(self) -> Dict:
        """
        偿债能力分析
        
        Returns:
            偿债能力指标
        """
        if self.data.empty:
            return {}
        
        latest = self.data.iloc[-1]
        
        # 流动比率
        current_ratio = self._safe_divide(
            latest.get('current_assets', 0),
            latest.get('current_liabilities', 0)
        )
        
        # 速动比率
        quick_ratio = self._safe_divide(
            latest.get('current_assets', 0) - latest.get('inventory', 0),
            latest.get('current_liabilities', 0)
        )
        
        # 资产负债率
        debt_ratio = self._safe_divide(
            latest.get('total_liabilities', 0),
            latest.get('total_assets', 0)
        ) * 100
        
        # 利息保障倍数（如果有利息费用数据）
        interest_coverage = self._safe_divide(
            latest.get('operating_profit', 0),
            latest.get('interest_expense', 1)
        )
        
        return {
            'current_ratio': round(current_ratio, 2),
            'quick_ratio': round(quick_ratio, 2),
            'debt_ratio': round(debt_ratio, 2),
            'interest_coverage': round(interest_coverage, 2),
            'assessment': self._assess_solvency(current_ratio, debt_ratio)
        }
    
    def _assess_solvency(self, current_ratio: float, debt_ratio: float) -> str:
        """评估偿债能力"""
        if current_ratio > 2 and debt_ratio < 40:
            return "excellent"
        elif current_ratio > 1.5 and debt_ratio < 60:
            return "good"
        elif current_ratio > 1 and debt_ratio < 70:
            return "average"
        return "risky"
    
    def cashflow(self) -> Dict:
        """
        现金流分析
        
        Returns:
            现金流指标
        """
        if self.data.empty:
            return {}
        
        latest = self.data.iloc[-1]
        
        # 经营现金流
        operating_cf = latest.get('operating_cash_flow', 0)
        
        # 投资现金流
        investing_cf = latest.get('investing_cash_flow', 0)
        
        # 筹资现金流
        financing_cf = latest.get('financing_cash_flow', 0)
        
        # 自由现金流（经营现金流 - 资本支出）
        capex = latest.get('capex', 0)
        free_cash_flow = operating_cf - capex
        
        # 现金流/净利润比
        net_profit = latest.get('net_profit', 0)
        cf_to_profit = self._safe_divide(operating_cf, net_profit)
        
        return {
            'operating_cf': round(operating_cf, 2),
            'investing_cf': round(investing_cf, 2),
            'financing_cf': round(financing_cf, 2),
            'free_cash_flow': round(free_cash_flow, 2),
            'cf_to_profit_ratio': round(cf_to_profit, 2),
            'assessment': self._assess_cashflow(operating_cf, free_cash_flow)
        }
    
    def _assess_cashflow(self, operating_cf: float, free_cash_flow: float) -> str:
        """评估现金流状况"""
        if operating_cf > 0 and free_cash_flow > 0:
            return "healthy"
        elif operating_cf > 0:
            return "adequate"
        return "concerning"
    
    def dupont_analysis(self) -> Dict:
        """
        杜邦分析
        
        ROE = 净利率 × 总资产周转率 × 权益乘数
        
        Returns:
            杜邦分析结果
        """
        if self.data.empty:
            return {}
        
        latest = self.data.iloc[-1]
        
        # 净利率
        net_margin = self._safe_divide(
            latest.get('net_profit', 0),
            latest.get('total_revenue', 0)
        )
        
        # 总资产周转率
        asset_turnover = self._safe_divide(
            latest.get('total_revenue', 0),
            latest.get('total_assets', 0)
        )
        
        # 权益乘数
        equity_multiplier = self._safe_divide(
            latest.get('total_assets', 0),
            latest.get('total_equity', 0)
        )
        
        # ROE
        roe = net_margin * asset_turnover * equity_multiplier * 100
        
        return {
            'roe': round(roe, 2),
            'net_margin': round(net_margin * 100, 2),
            'asset_turnover': round(asset_turnover, 2),
            'equity_multiplier': round(equity_multiplier, 2),
            'breakdown': {
                'profitability': round(net_margin * 100, 2),
                'efficiency': round(asset_turnover, 2),
                'leverage': round(equity_multiplier, 2)
            }
        }
    
    def compare_with_industry(self, industry_data: List[Dict]) -> Dict:
        """
        与行业对比
        
        Args:
            industry_data: 行业平均数据
            
        Returns:
            对比结果
        """
        if not industry_data or self.data.empty:
            return {}
        
        company_metrics = self.profitability()
        industry_avg = self._calculate_industry_avg(industry_data)
        
        comparisons = {}
        for metric in ['roe', 'roa', 'gross_margin', 'net_margin']:
            company_val = company_metrics.get(metric, 0)
            industry_val = industry_avg.get(metric, 0)
            
            comparisons[metric] = {
                'company': company_val,
                'industry_avg': industry_val,
                'difference': round(company_val - industry_val, 2),
                'percentile': self._calculate_percentile(metric, company_val, industry_data)
            }
        
        return {
            'comparisons': comparisons,
            'overall_rank': self._calculate_overall_rank(comparisons)
        }
    
    def _calculate_industry_avg(self, industry_data: List[Dict]) -> Dict:
        """计算行业平均值"""
        df = pd.DataFrame(industry_data)
        return {
            'roe': df['roe'].mean() if 'roe' in df else 0,
            'roa': df['roa'].mean() if 'roa' in df else 0,
            'gross_margin': df['gross_margin'].mean() if 'gross_margin' in df else 0,
            'net_margin': df['net_margin'].mean() if 'net_margin' in df else 0
        }
    
    def _calculate_percentile(self, metric: str, value: float, 
                              industry_data: List[Dict]) -> int:
        """计算百分位排名"""
        values = [d.get(metric, 0) for d in industry_data]
        values.append(value)
        values.sort()
        
        rank = values.index(value)
        return int((rank / len(values)) * 100)
    
    def _calculate_overall_rank(self, comparisons: Dict) -> str:
        """计算综合排名"""
        better_count = sum(1 for c in comparisons.values() if c.get('difference', 0) > 0)
        total = len(comparisons)
        
        if better_count >= total * 0.75:
            return "leading"
        elif better_count >= total * 0.5:
            return "above_average"
        elif better_count >= total * 0.25:
            return "average"
        return "below_average"
    
    def analyze(self) -> Dict:
        """
        完整基本面分析
        
        Returns:
            完整分析结果
        """
        return {
            'profitability': self.profitability(),
            'growth': self.growth(),
            'efficiency': self.efficiency(),
            'solvency': self.solvency(),
            'cashflow': self.cashflow(),
            'dupont': self.dupont_analysis()
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
