# -*- coding: utf-8 -*-
"""
财务健康度分析模块

提供财务风险评分和异常检测
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskIndicator:
    """风险指标"""
    name: str
    level: RiskLevel
    value: float
    threshold: float
    description: str


class FinancialHealthChecker:
    """
    财务健康度检查器
    
    评估财务风险和检测异常指标
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
    
    def health_score(self) -> Dict:
        """
        综合健康评分
        
        Returns:
            健康评分结果
        """
        if self.data.empty:
            return {'total_score': 0, 'assessment': 'no_data'}
        
        latest = self.data.iloc[-1]
        
        scores = {}
        
        # 1. 盈利能力评分 (25分)
        roe = self._safe_divide(latest.get('net_profit', 0), latest.get('total_equity', 0)) * 100
        if roe > 15:
            scores['profitability'] = 25
        elif roe > 10:
            scores['profitability'] = 20
        elif roe > 5:
            scores['profitability'] = 15
        elif roe > 0:
            scores['profitability'] = 10
        else:
            scores['profitability'] = 0
        
        # 2. 偿债能力评分 (25分)
        debt_ratio = self._safe_divide(latest.get('total_liabilities', 0), latest.get('total_assets', 0)) * 100
        if debt_ratio < 30:
            scores['solvency'] = 25
        elif debt_ratio < 50:
            scores['solvency'] = 20
        elif debt_ratio < 70:
            scores['solvency'] = 15
        elif debt_ratio < 85:
            scores['solvency'] = 10
        else:
            scores['solvency'] = 5
        
        # 3. 现金流评分 (25分)
        operating_cf = latest.get('operating_cash_flow', 0)
        net_profit = latest.get('net_profit', 0)
        cf_coverage = self._safe_divide(operating_cf, net_profit)
        
        if cf_coverage > 1.2:
            scores['cashflow'] = 25
        elif cf_coverage > 0.8:
            scores['cashflow'] = 20
        elif cf_coverage > 0.5:
            scores['cashflow'] = 15
        elif operating_cf > 0:
            scores['cashflow'] = 10
        else:
            scores['cashflow'] = 0
        
        # 4. 成长能力评分 (15分)
        if len(self.data) >= 2:
            revenue_growth = self._calculate_growth('total_revenue')
            if revenue_growth > 20:
                scores['growth'] = 15
            elif revenue_growth > 10:
                scores['growth'] = 12
            elif revenue_growth > 0:
                scores['growth'] = 8
            else:
                scores['growth'] = 5
        else:
            scores['growth'] = 10
        
        # 5. 运营效率评分 (10分)
        asset_turnover = self._safe_divide(latest.get('total_revenue', 0), latest.get('total_assets', 0))
        if asset_turnover > 1:
            scores['efficiency'] = 10
        elif asset_turnover > 0.5:
            scores['efficiency'] = 8
        elif asset_turnover > 0.3:
            scores['efficiency'] = 5
        else:
            scores['efficiency'] = 3
        
        total_score = sum(scores.values())
        
        # 评级
        if total_score >= 90:
            grade = "A"
            assessment = "excellent"
        elif total_score >= 75:
            grade = "B"
            assessment = "good"
        elif total_score >= 60:
            grade = "C"
            assessment = "average"
        elif total_score >= 40:
            grade = "D"
            assessment = "poor"
        else:
            grade = "E"
            assessment = "risky"
        
        return {
            'total_score': total_score,
            'grade': grade,
            'assessment': assessment,
            'dimension_scores': scores,
            'max_score': 100
        }
    
    def detect_anomalies(self) -> List[Dict]:
        """
        异常指标检测
        
        Returns:
            异常指标列表
        """
        if self.data.empty:
            return []
        
        anomalies = []
        latest = self.data.iloc[-1]
        
        # 1. 应收账款异常增长
        if len(self.data) >= 2:
            ar_growth = self._calculate_growth('accounts_receivable')
            revenue_growth = self._calculate_growth('total_revenue')
            
            if ar_growth > revenue_growth * 2 and ar_growth > 30:
                anomalies.append({
                    'type': 'receivable_surge',
                    'severity': 'high',
                    'value': round(ar_growth, 2),
                    'description': f'应收账款增长({ar_growth:.1f}%)远超营收增长({revenue_growth:.1f}%)'
                })
        
        # 2. 存货异常增长
        if len(self.data) >= 2:
            inventory_growth = self._calculate_growth('inventory')
            if inventory_growth > 50:
                anomalies.append({
                    'type': 'inventory_surge',
                    'severity': 'medium',
                    'value': round(inventory_growth, 2),
                    'description': f'存货大幅增长({inventory_growth:.1f}%)'
                })
        
        # 3. 毛利率异常波动
        if len(self.data) >= 3:
            gross_margins = []
            for idx in range(len(self.data)):
                row = self.data.iloc[idx]
                gm = self._safe_divide(row.get('gross_profit', 0), row.get('total_revenue', 0)) * 100
                gross_margins.append(gm)
            
            if len(gross_margins) >= 3:
                margin_std = np.std(gross_margins)
                if margin_std > 10:
                    anomalies.append({
                        'type': 'margin_volatility',
                        'severity': 'medium',
                        'value': round(margin_std, 2),
                        'description': f'毛利率波动较大(标准差{margin_std:.1f}%)'
                    })
        
        # 4. 现金流与利润背离
        operating_cf = latest.get('operating_cash_flow', 0)
        net_profit = latest.get('net_profit', 0)
        
        if net_profit > 0 and operating_cf < 0:
            anomalies.append({
                'type': 'cf_profit_divergence',
                'severity': 'high',
                'value': round(operating_cf, 2),
                'description': '净利润为正但经营现金流为负，盈利质量存疑'
            })
        
        # 5. 资产负债率过高
        debt_ratio = self._safe_divide(latest.get('total_liabilities', 0), latest.get('total_assets', 0)) * 100
        if debt_ratio > 80:
            anomalies.append({
                'type': 'high_leverage',
                'severity': 'critical',
                'value': round(debt_ratio, 2),
                'description': f'资产负债率过高({debt_ratio:.1f}%)'
            })
        elif debt_ratio > 70:
            anomalies.append({
                'type': 'high_leverage',
                'severity': 'high',
                'value': round(debt_ratio, 2),
                'description': f'资产负债率偏高({debt_ratio:.1f}%)'
            })
        
        # 6. 流动比率过低
        current_ratio = self._safe_divide(latest.get('current_assets', 0), latest.get('current_liabilities', 0))
        if current_ratio < 0.8:
            anomalies.append({
                'type': 'low_liquidity',
                'severity': 'critical',
                'value': round(current_ratio, 2),
                'description': f'流动比率过低({current_ratio:.2f})，短期偿债风险高'
            })
        elif current_ratio < 1:
            anomalies.append({
                'type': 'low_liquidity',
                'severity': 'high',
                'value': round(current_ratio, 2),
                'description': f'流动比率偏低({current_ratio:.2f})'
            })
        
        return anomalies
    
    def risk_assessment(self) -> Dict:
        """
        财务风险评估
        
        Returns:
            风险评估结果
        """
        if self.data.empty:
            return {}
        
        risks = []
        latest = self.data.iloc[-1]
        
        # 1. 流动性风险
        current_ratio = self._safe_divide(latest.get('current_assets', 0), latest.get('current_liabilities', 0))
        quick_ratio = self._safe_divide(
            latest.get('current_assets', 0) - latest.get('inventory', 0),
            latest.get('current_liabilities', 0)
        )
        
        if current_ratio < 1 or quick_ratio < 0.8:
            risks.append(RiskIndicator(
                'liquidity_risk',
                RiskLevel.HIGH if current_ratio < 0.8 else RiskLevel.MEDIUM,
                current_ratio,
                1.0,
                '流动性风险：短期偿债能力不足'
            ))
        
        # 2. 偿债风险
        debt_ratio = self._safe_divide(latest.get('total_liabilities', 0), latest.get('total_assets', 0)) * 100
        if debt_ratio > 70:
            risks.append(RiskIndicator(
                'solvency_risk',
                RiskLevel.CRITICAL if debt_ratio > 85 else RiskLevel.HIGH,
                debt_ratio,
                70.0,
                '偿债风险：资产负债率过高'
            ))
        
        # 3. 盈利风险
        roe = self._safe_divide(latest.get('net_profit', 0), latest.get('total_equity', 0)) * 100
        if roe < 5:
            risks.append(RiskIndicator(
                'profitability_risk',
                RiskLevel.HIGH if roe < 0 else RiskLevel.MEDIUM,
                roe,
                5.0,
                '盈利风险：净资产收益率过低'
            ))
        
        # 4. 经营风险
        operating_cf = latest.get('operating_cash_flow', 0)
        if operating_cf < 0:
            risks.append(RiskIndicator(
                'operating_risk',
                RiskLevel.HIGH,
                operating_cf,
                0.0,
                '经营风险：经营现金流为负'
            ))
        
        # 5. 成长风险
        if len(self.data) >= 2:
            revenue_growth = self._calculate_growth('total_revenue')
            profit_growth = self._calculate_growth('net_profit')
            
            if revenue_growth < -10 or profit_growth < -20:
                risks.append(RiskIndicator(
                    'growth_risk',
                    RiskLevel.HIGH,
                    min(revenue_growth, profit_growth),
                    0.0,
                    '成长风险：营收或利润大幅下滑'
                ))
        
        # 汇总风险等级
        risk_levels = [r.level for r in risks]
        overall_risk = self._determine_overall_risk(risk_levels)
        
        return {
            'overall_risk': overall_risk.value,
            'risk_count': len(risks),
            'critical_count': sum(1 for r in risks if r.level == RiskLevel.CRITICAL),
            'high_count': sum(1 for r in risks if r.level == RiskLevel.HIGH),
            'risks': [
                {
                    'name': r.name,
                    'level': r.level.value,
                    'value': r.value,
                    'threshold': r.threshold,
                    'description': r.description
                }
                for r in risks
            ]
        }
    
    def _determine_overall_risk(self, risk_levels: List[RiskLevel]) -> RiskLevel:
        """确定整体风险等级"""
        if RiskLevel.CRITICAL in risk_levels:
            return RiskLevel.CRITICAL
        elif risk_levels.count(RiskLevel.HIGH) >= 2:
            return RiskLevel.HIGH
        elif RiskLevel.HIGH in risk_levels:
            return RiskLevel.MEDIUM
        elif RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def audit_opinion(self) -> str:
        """
        模拟审计意见
        
        实际应用中应该从数据库获取真实审计意见
        
        Returns:
            审计意见类型
        """
        anomalies = self.detect_anomalies()
        risks = self.risk_assessment()
        
        critical_count = sum(1 for a in anomalies if a['severity'] == 'critical')
        
        if critical_count > 0:
            return "保留意见"
        elif len(anomalies) > 3:
            return "带强调事项段的无保留意见"
        elif risks.get('high_count', 0) > 0:
            return "带强调事项段的无保留意见"
        
        return "标准无保留意见"
    
    def fraud_warning(self) -> List[Dict]:
        """
        财务造假预警
        
        Returns:
            预警信号列表
        """
        warnings = []
        
        if self.data.empty or len(self.data) < 3:
            return warnings
        
        # 1. 利润与现金流长期背离
        divergences = 0
        for idx in range(len(self.data)):
            row = self.data.iloc[idx]
            if row.get('net_profit', 0) > 0 and row.get('operating_cash_flow', 0) < 0:
                divergences += 1
        
        if divergences >= len(self.data) * 0.5:
            warnings.append({
                'type': 'persistent_cf_profit_divergence',
                'risk_level': 'high',
                'description': f'多期({divergences}期)净利润为正但经营现金流为负'
            })
        
        # 2. 应收账款增速持续高于营收增速
        ar_surge_count = 0
        for i in range(1, len(self.data)):
            current = self.data.iloc[i]
            previous = self.data.iloc[i-1]
            
            ar_growth = self._safe_divide(
                current.get('accounts_receivable', 0) - previous.get('accounts_receivable', 0),
                previous.get('accounts_receivable', 1)
            ) * 100
            
            revenue_growth = self._safe_divide(
                current.get('total_revenue', 0) - previous.get('total_revenue', 0),
                previous.get('total_revenue', 1)
            ) * 100
            
            if ar_growth > revenue_growth * 1.5 and ar_growth > 20:
                ar_surge_count += 1
        
        if ar_surge_count >= 2:
            warnings.append({
                'type': 'receivable_growth_anomaly',
                'risk_level': 'medium',
                'description': f'多期({ar_surge_count}期)应收账款增速异常高于营收增速'
            })
        
        # 3. 毛利率异常波动
        gross_margins = []
        for idx in range(len(self.data)):
            row = self.data.iloc[idx]
            gm = self._safe_divide(row.get('gross_profit', 0), row.get('total_revenue', 0)) * 100
            gross_margins.append(gm)
        
        if len(gross_margins) >= 3:
            for i in range(1, len(gross_margins)):
                if abs(gross_margins[i] - gross_margins[i-1]) > 15:
                    warnings.append({
                        'type': 'margin_volatility',
                        'risk_level': 'medium',
                        'description': '毛利率出现异常波动'
                    })
                    break
        
        return warnings
    
    def analyze(self) -> Dict:
        """
        完整财务健康度分析
        
        Returns:
            完整分析结果
        """
        return {
            'health_score': self.health_score(),
            'anomalies': self.detect_anomalies(),
            'risk_assessment': self.risk_assessment(),
            'audit_opinion': self.audit_opinion(),
            'fraud_warnings': self.fraud_warning()
        }
    
    def _calculate_growth(self, column: str) -> float:
        """计算增长率"""
        if len(self.data) < 2:
            return 0
        
        current = self.data.iloc[-1].get(column, 0)
        previous = self.data.iloc[-2].get(column, 0)
        
        if previous == 0:
            return 0
        
        return (current - previous) / previous * 100
    
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
