# -*- coding: utf-8 -*-
"""
分析层测试

测试技术分析、基本面分析、估值分析、资金流向分析、财务健康度分析
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from datetime import datetime, date
import pandas as pd
import numpy as np

from analysis.technical import TechnicalAnalyzer, SignalType
from analysis.fundamental import FundamentalAnalyzer
from analysis.valuation import ValuationAnalyzer
from analysis.capital_flow import CapitalFlowAnalyzer
from analysis.financial_health import FinancialHealthChecker


class TestTechnicalAnalyzer(unittest.TestCase):
    """测试技术分析器"""
    
    def setUp(self):
        """准备测试数据"""
        # 生成模拟K线数据
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        base_price = 10.0
        prices = [base_price]
        for i in range(99):
            change = np.random.normal(0, 0.02)
            prices.append(prices[-1] * (1 + change))
        
        self.kline_data = pd.DataFrame({
            'trade_date': dates,
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        self.analyzer = TechnicalAnalyzer(self.kline_data)
    
    def test_macd(self):
        """测试MACD计算"""
        result = self.analyzer.macd()
        
        self.assertIn('dif', result)
        self.assertIn('dea', result)
        self.assertIn('macd', result)
        self.assertIn('signal', result)
        
        self.assertIsInstance(result['dif'], float)
        self.assertIsInstance(result['dea'], float)
        self.assertIsInstance(result['macd'], float)
    
    def test_kdj(self):
        """测试KDJ计算"""
        result = self.analyzer.kdj()
        
        self.assertIn('k', result)
        self.assertIn('d', result)
        self.assertIn('j', result)
        
        # K、D值应在0-100之间
        self.assertGreaterEqual(result['k'], 0)
        self.assertLessEqual(result['k'], 100)
        self.assertGreaterEqual(result['d'], 0)
        self.assertLessEqual(result['d'], 100)
    
    def test_rsi(self):
        """测试RSI计算"""
        result = self.analyzer.rsi()
        
        self.assertIn('rsi6', result)
        self.assertIn('rsi12', result)
        self.assertIn('rsi24', result)
        
        # RSI值应在0-100之间
        self.assertGreaterEqual(result['rsi6'], 0)
        self.assertLessEqual(result['rsi6'], 100)
    
    def test_ma(self):
        """测试均线计算"""
        result = self.analyzer.ma([5, 10, 20, 60])
        
        self.assertIn('ma5', result)
        self.assertIn('ma10', result)
        self.assertIn('ma20', result)
        self.assertIn('ma60', result)
        self.assertIn('alignment', result)
        
        # 均线值应为正数
        self.assertGreater(result['ma5'], 0)
    
    def test_boll(self):
        """测试布林带计算"""
        result = self.analyzer.boll()
        
        self.assertIn('upper', result)
        self.assertIn('middle', result)
        self.assertIn('lower', result)
        self.assertIn('position', result)
        
        # 上轨 > 中轨 > 下轨
        self.assertGreater(result['upper'], result['middle'])
        self.assertGreater(result['middle'], result['lower'])
    
    def test_volume_analysis(self):
        """测试成交量分析"""
        result = self.analyzer.volume_analysis()
        
        self.assertIn('current_volume', result)
        self.assertIn('vol_ma5', result)
        self.assertIn('volume_ratio', result)
        self.assertIn('relationship', result)
    
    def test_composite_signal(self):
        """测试综合信号"""
        result = self.analyzer.composite_signal()
        
        self.assertIn('signal', result)
        self.assertIn('score', result)
        self.assertIn('signals', result)
        
        # 评分应在0-100之间
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
    
    def test_analyze(self):
        """测试完整分析"""
        result = self.analyzer.analyze()
        
        self.assertIn('macd', result)
        self.assertIn('kdj', result)
        self.assertIn('rsi', result)
        self.assertIn('ma', result)
        self.assertIn('boll', result)
        self.assertIn('composite', result)


class TestFundamentalAnalyzer(unittest.TestCase):
    """测试基本面分析器"""
    
    def setUp(self):
        """准备测试数据"""
        self.financial_data = [
            {
                'report_date': '2022-12-31',
                'total_revenue': 1000000000,
                'net_profit': 100000000,
                'gross_profit': 400000000,
                'total_assets': 2000000000,
                'total_equity': 1000000000,
                'total_liabilities': 1000000000,
                'current_assets': 800000000,
                'current_liabilities': 400000000,
                'inventory': 200000000,
                'operating_cash_flow': 120000000,
                'cost_of_revenue': 600000000
            },
            {
                'report_date': '2023-12-31',
                'total_revenue': 1200000000,
                'net_profit': 150000000,
                'gross_profit': 480000000,
                'total_assets': 2200000000,
                'total_equity': 1150000000,
                'total_liabilities': 1050000000,
                'current_assets': 900000000,
                'current_liabilities': 420000000,
                'inventory': 220000000,
                'operating_cash_flow': 180000000,
                'cost_of_revenue': 720000000
            }
        ]
        
        self.analyzer = FundamentalAnalyzer(self.financial_data)
    
    def test_profitability(self):
        """测试盈利能力分析"""
        result = self.analyzer.profitability()
        
        self.assertIn('roe', result)
        self.assertIn('roa', result)
        self.assertIn('gross_margin', result)
        self.assertIn('net_margin', result)
        self.assertIn('assessment', result)
        
        # ROE = 净利润 / 净资产 = 150M / 1150M ≈ 13%
        self.assertAlmostEqual(result['roe'], 13.04, places=1)
    
    def test_growth(self):
        """测试成长能力分析"""
        result = self.analyzer.growth()
        
        self.assertIn('revenue_growth', result)
        self.assertIn('profit_growth', result)
        
        # 营收增长 = (1200-1000)/1000 = 20%
        self.assertAlmostEqual(result['revenue_growth'], 20.0, places=1)
        # 利润增长 = (150-100)/100 = 50%
        self.assertAlmostEqual(result['profit_growth'], 50.0, places=1)
    
    def test_solvency(self):
        """测试偿债能力分析"""
        result = self.analyzer.solvency()
        
        self.assertIn('current_ratio', result)
        self.assertIn('debt_ratio', result)
        
        # 流动比率 = 900/420 ≈ 2.14
        self.assertAlmostEqual(result['current_ratio'], 2.14, places=1)
    
    def test_dupont_analysis(self):
        """测试杜邦分析"""
        result = self.analyzer.dupont_analysis()
        
        self.assertIn('roe', result)
        self.assertIn('net_margin', result)
        self.assertIn('asset_turnover', result)
        self.assertIn('equity_multiplier', result)
    
    def test_analyze(self):
        """测试完整分析"""
        result = self.analyzer.analyze()
        
        self.assertIn('profitability', result)
        self.assertIn('growth', result)
        self.assertIn('solvency', result)
        self.assertIn('dupont', result)


class TestValuationAnalyzer(unittest.TestCase):
    """测试估值分析器"""
    
    def setUp(self):
        """准备测试数据"""
        self.quote = {
            'close': 15.0,
            'market_cap': 1500000000
        }
        
        self.financial = {
            'eps_ttm': 1.0,
            'eps': 0.9,
            'bps': 8.0,
            'total_shares': 100000000,
            'total_revenue': 1000000000,
            'operating_cash_flow': 120000000,
            'free_cash_flow': 80000000,
            'profit_growth': 20.0,
            'roe': 12.5,
            'total_liabilities': 500000000,
            'cash': 200000000,
            'ebitda': 150000000
        }
        
        self.historical = [
            {'trade_date': '2020-01-01', 'pe_ttm': 12.0, 'pb': 1.5},
            {'trade_date': '2021-01-01', 'pe_ttm': 15.0, 'pb': 1.8},
            {'trade_date': '2022-01-01', 'pe_ttm': 14.0, 'pb': 1.6},
            {'trade_date': '2023-01-01', 'pe_ttm': 16.0, 'pb': 1.9},
        ]
        
        self.analyzer = ValuationAnalyzer('000001', self.quote, self.financial, self.historical)
    
    def test_pe_ratio(self):
        """测试PE计算"""
        result = self.analyzer.pe_ratio()
        
        self.assertIn('pe_ttm', result)
        self.assertIn('pe_lyr', result)
        
        # PE = 股价 / EPS = 15 / 1 = 15
        self.assertEqual(result['pe_ttm'], 15.0)
    
    def test_pb_ratio(self):
        """测试PB计算"""
        result = self.analyzer.pb_ratio()
        
        self.assertIn('pb', result)
        
        # PB = 股价 / BPS = 15 / 8 = 1.875
        self.assertAlmostEqual(result['pb'], 1.88, places=1)
    
    def test_peg_ratio(self):
        """测试PEG计算"""
        result = self.analyzer.peg_ratio()
        
        self.assertIn('peg', result)
        
        # PEG = PE / 增长率 = 15 / 20 = 0.75
        self.assertAlmostEqual(result['peg'], 0.75, places=1)
    
    def test_graham_valuation(self):
        """测试格雷厄姆估值"""
        result = self.analyzer.graham_valuation()
        
        self.assertIn('intrinsic_value', result)
        self.assertIn('upside_potential', result)
        
        # 格雷厄姆估值 = EPS * (8.5 + 2g) = 1 * (8.5 + 40) = 48.5
        self.assertAlmostEqual(result['intrinsic_value'], 48.5, places=1)
    
    def test_dcf_valuation(self):
        """测试DCF估值"""
        result = self.analyzer.dcf_valuation()
        
        self.assertIn('intrinsic_value', result)
        self.assertIn('enterprise_value', result)
    
    def test_valuation_assessment(self):
        """测试综合估值评估"""
        result = self.analyzer.valuation_assessment()
        
        self.assertIn('overall_assessment', result)
        self.assertIn('score', result)
        self.assertIn('metrics', result)


class TestCapitalFlowAnalyzer(unittest.TestCase):
    """测试资金流向分析器"""
    
    def setUp(self):
        """准备测试数据"""
        # 生成10天的资金流向数据
        self.flow_data = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(10):
            self.flow_data.append({
                'trade_date': base_date + pd.Timedelta(days=i),
                'super_large': 1000000 + i * 100000,
                'large': 500000 + i * 50000,
                'medium': -200000 - i * 20000,
                'small': -300000 - i * 30000
            })
        
        self.analyzer = CapitalFlowAnalyzer(self.flow_data)
    
    def test_today_flow(self):
        """测试当日资金流向"""
        result = self.analyzer.today_flow()
        
        self.assertIn('main_inflow', result)
        self.assertIn('main_ratio', result)
        self.assertIn('direction', result)
        
        # 主力资金 = 超大单 + 大单
        self.assertGreater(result['main_inflow'], 0)
    
    def test_consecutive_inflow_days(self):
        """测试连续流入天数"""
        result = self.analyzer.consecutive_inflow_days()
        
        self.assertIn('current_consecutive', result)
        self.assertIn('total_inflow_days', result)
    
    def test_period_flow(self):
        """测试周期资金流向"""
        result = self.analyzer.period_flow(5)
        
        self.assertIn('total_main_inflow', result)
        self.assertIn('avg_daily_inflow', result)
        self.assertIn('inflow_days', result)
    
    def test_flow_trend(self):
        """测试资金流向趋势"""
        result = self.analyzer.flow_trend()
        
        self.assertIn('trend', result)
        self.assertIn('strength', result)
        self.assertIn('trend_score', result)
    
    def test_main_force_control(self):
        """测试主力控盘度"""
        result = self.analyzer.main_force_control()
        
        self.assertIn('control_degree', result)
        self.assertIn('control_status', result)
        self.assertIn('main_attitude', result)


class TestFinancialHealthChecker(unittest.TestCase):
    """测试财务健康度检查器"""
    
    def setUp(self):
        """准备测试数据"""
        self.financial_data = [
            {
                'report_date': '2021-12-31',
                'total_revenue': 800000000,
                'net_profit': 80000000,
                'gross_profit': 320000000,
                'total_assets': 1800000000,
                'total_equity': 900000000,
                'total_liabilities': 900000000,
                'current_assets': 700000000,
                'current_liabilities': 350000000,
                'inventory': 180000000,
                'operating_cash_flow': 100000000,
                'accounts_receivable': 150000000
            },
            {
                'report_date': '2022-12-31',
                'total_revenue': 900000000,
                'net_profit': 90000000,
                'gross_profit': 360000000,
                'total_assets': 1900000000,
                'total_equity': 950000000,
                'total_liabilities': 950000000,
                'current_assets': 750000000,
                'current_liabilities': 370000000,
                'inventory': 190000000,
                'operating_cash_flow': 110000000,
                'accounts_receivable': 160000000
            },
            {
                'report_date': '2023-12-31',
                'total_revenue': 1000000000,
                'net_profit': 120000000,
                'gross_profit': 400000000,
                'total_assets': 2000000000,
                'total_equity': 1100000000,
                'total_liabilities': 900000000,
                'current_assets': 800000000,
                'current_liabilities': 350000000,
                'inventory': 200000000,
                'operating_cash_flow': 150000000,
                'accounts_receivable': 170000000
            }
        ]
        
        self.checker = FinancialHealthChecker(self.financial_data)
    
    def test_health_score(self):
        """测试健康评分"""
        result = self.checker.health_score()
        
        self.assertIn('total_score', result)
        self.assertIn('grade', result)
        self.assertIn('dimension_scores', result)
        
        # 总分应在0-100之间
        self.assertGreaterEqual(result['total_score'], 0)
        self.assertLessEqual(result['total_score'], 100)
    
    def test_detect_anomalies(self):
        """测试异常检测"""
        result = self.checker.detect_anomalies()
        
        self.assertIsInstance(result, list)
    
    def test_risk_assessment(self):
        """测试风险评估"""
        result = self.checker.risk_assessment()
        
        self.assertIn('overall_risk', result)
        self.assertIn('risks', result)
    
    def test_audit_opinion(self):
        """测试审计意见"""
        result = self.checker.audit_opinion()
        
        self.assertIsInstance(result, str)
        self.assertIn(result, ['标准无保留意见', '带强调事项段的无保留意见', '保留意见'])
    
    def test_fraud_warning(self):
        """测试造假预警"""
        result = self.checker.fraud_warning()
        
        self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()
