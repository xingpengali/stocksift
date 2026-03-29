# -*- coding: utf-8 -*-
"""
价值投资页面

提供价值投资分析工具
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTabWidget, QGroupBox,
    QGridLayout, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt

from ui.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ValueInvestingPage(BasePage):
    """
    价值投资页面
    
    提供估值计算、股票对比、优质股票池等功能
    """
    
    page_id = "value"
    page_name = "价值投资"
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def _init_ui(self):
        """初始化UI"""
        super()._init_ui()
        content_layout = self.get_content_layout()
        
        # 标签页
        self._tab_widget = QTabWidget()
        
        # 估值计算器
        self._calculator_tab = self._create_calculator_tab()
        self._tab_widget.addTab(self._calculator_tab, "🧮 估值计算")
        
        # 股票对比
        self._compare_tab = self._create_compare_tab()
        self._tab_widget.addTab(self._compare_tab, "⚖️ 股票对比")
        
        # 优质股票池
        self._pool_tab = self._create_pool_tab()
        self._tab_widget.addTab(self._pool_tab, "⭐ 优质股票池")
        
        # 财报分析
        self._report_tab = self._create_report_tab()
        self._tab_widget.addTab(self._report_tab, "📊 财报分析")
        
        content_layout.addWidget(self._tab_widget)
    
    def _create_calculator_tab(self) -> QWidget:
        """创建估值计算器标签页"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        
        # 左侧：输入参数
        input_group = QGroupBox("输入参数")
        input_layout = QGridLayout(input_group)
        
        # 股票代码
        input_layout.addWidget(QLabel("股票代码:"), 0, 0)
        self._calc_code_edit = QLineEdit()
        self._calc_code_edit.setPlaceholderText("如: 600519")
        input_layout.addWidget(self._calc_code_edit, 0, 1)
        
        # 当前EPS
        input_layout.addWidget(QLabel("每股收益(EPS):"), 1, 0)
        self._eps_edit = QLineEdit()
        input_layout.addWidget(self._eps_edit, 1, 1)
        
        # 预期增长率
        input_layout.addWidget(QLabel("预期增长率(%):"), 2, 0)
        self._growth_edit = QLineEdit("10")
        input_layout.addWidget(self._growth_edit, 2, 1)
        
        # 无风险利率
        input_layout.addWidget(QLabel("无风险利率(%):"), 3, 0)
        self._risk_free_edit = QLineEdit("3")
        input_layout.addWidget(self._risk_free_edit, 3, 1)
        
        # 计算按钮
        calc_btn = QPushButton("🧮 计算估值")
        calc_btn.clicked.connect(self._on_calculate_valuation)
        calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
        """)
        input_layout.addWidget(calc_btn, 4, 0, 1, 2)
        
        layout.addWidget(input_group, 1)
        
        # 右侧：计算结果
        result_group = QGroupBox("估值结果")
        result_layout = QVBoxLayout(result_group)
        
        # DCF估值
        dcf_group = QGroupBox("DCF现金流折现")
        dcf_layout = QGridLayout(dcf_group)
        
        dcf_layout.addWidget(QLabel("内在价值:"), 0, 0)
        self._dcf_value = QLabel("--")
        self._dcf_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #1890ff;")
        dcf_layout.addWidget(self._dcf_value, 0, 1)
        
        dcf_layout.addWidget(QLabel("安全边际价格:"), 1, 0)
        self._dcf_margin = QLabel("--")
        dcf_layout.addWidget(self._dcf_margin, 1, 1)
        
        result_layout.addWidget(dcf_group)
        
        # 格雷厄姆估值
        graham_group = QGroupBox("格雷厄姆估值")
        graham_layout = QGridLayout(graham_group)
        
        graham_layout.addWidget(QLabel("内在价值:"), 0, 0)
        self._graham_value = QLabel("--")
        self._graham_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #1890ff;")
        graham_layout.addWidget(self._graham_value, 0, 1)
        
        result_layout.addWidget(graham_group)
        
        # 分析建议
        advice_group = QGroupBox("分析建议")
        advice_layout = QVBoxLayout(advice_group)
        
        self._advice_text = QTextEdit()
        self._advice_text.setReadOnly(True)
        self._advice_text.setPlaceholderText("点击计算按钮获取分析建议...")
        advice_layout.addWidget(self._advice_text)
        
        result_layout.addWidget(advice_group)
        
        layout.addWidget(result_group, 2)
        
        return widget
    
    def _create_compare_tab(self) -> QWidget:
        """创建股票对比标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("对比股票:"))
        
        self._compare_edit = QLineEdit()
        self._compare_edit.setPlaceholderText("输入股票代码，用逗号分隔，如: 000001,000002,600519")
        input_layout.addWidget(self._compare_edit, 1)
        
        compare_btn = QPushButton("⚖️ 开始对比")
        compare_btn.clicked.connect(self._on_compare_stocks)
        input_layout.addWidget(compare_btn)
        
        layout.addLayout(input_layout)
        
        # 对比表格
        self._compare_table = QTableWidget()
        self._compare_table.setColumnCount(8)
        self._compare_table.setHorizontalHeaderLabels([
            "股票代码", "股票名称", "PE(TTM)", "PB", "ROE%", "营收增长率%", 
            "净利润增长率%", "综合评分"
        ])
        self._compare_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._compare_table)
        
        return widget
    
    def _create_pool_tab(self) -> QWidget:
        """创建优质股票池标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 筛选条件
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选条件:"))
        
        filters = [
            ("PE < 20", "pe<20"),
            ("PB < 3", "pb<3"),
            ("ROE > 15%", "roe>15"),
            ("股息率 > 3%", "dividend>3"),
        ]
        
        for text, value in filters:
            btn = QPushButton(text)
            btn.setCheckable(True)
            filter_layout.addWidget(btn)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._on_refresh_pool)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # 股票池表格
        self._pool_table = QTableWidget()
        self._pool_table.setColumnCount(9)
        self._pool_table.setHorizontalHeaderLabels([
            "股票代码", "股票名称", "行业", "PE(TTM)", "PB", "ROE%", 
            "股息率%", "综合评分", "操作"
        ])
        self._pool_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._pool_table)
        
        return widget
    
    def _create_report_tab(self) -> QWidget:
        """创建财报分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 股票输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("股票代码:"))
        
        self._report_code_edit = QLineEdit()
        self._report_code_edit.setPlaceholderText("输入股票代码")
        input_layout.addWidget(self._report_code_edit)
        
        analyze_btn = QPushButton("📊 分析财报")
        analyze_btn.clicked.connect(self._on_analyze_report)
        input_layout.addWidget(analyze_btn)
        
        input_layout.addStretch()
        layout.addLayout(input_layout)
        
        # 分析结果
        self._report_text = QTextEdit()
        self._report_text.setReadOnly(True)
        self._report_text.setPlaceholderText("财报分析结果将显示在这里...")
        layout.addWidget(self._report_text)
        
        return widget
    
    def _on_calculate_valuation(self):
        """计算估值"""
        code = self._calc_code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return
        
        try:
            eps = float(self._eps_edit.text() or 0)
            growth = float(self._growth_edit.text() or 0)
            risk_free = float(self._risk_free_edit.text() or 0)
            
            # DCF简化计算
            dcf_value = eps * (1 + growth/100) / (risk_free/100)
            margin_price = dcf_value * 0.7  # 30%安全边际
            
            self._dcf_value.setText(f"¥{dcf_value:.2f}")
            self._dcf_margin.setText(f"¥{margin_price:.2f}")
            
            # 格雷厄姆估值
            graham_value = eps * (8.5 + 2 * growth)
            self._graham_value.setText(f"¥{graham_value:.2f}")
            
            # 分析建议
            advice = f"""
基于DCF模型和格雷厄姆估值法的分析:

1. DCF内在价值: ¥{dcf_value:.2f}
2. 安全边际买入价: ¥{margin_price:.2f} (7折)
3. 格雷厄姆估值: ¥{graham_value:.2f}

建议:
- 如果当前股价低于 ¥{margin_price:.2f}，具备足够的安全边际
- 关注公司基本面是否支撑 {growth}% 的增长预期
- 建议分散投资，单只股票不超过总资产的10%
            """
            self._advice_text.setText(advice)
            
            logger.info(f"估值计算完成: {code}")
            
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", "请检查输入的数值格式")
    
    def _on_compare_stocks(self):
        """对比股票"""
        codes_text = self._compare_edit.text().strip()
        if not codes_text:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return
        
        codes = [c.strip() for c in codes_text.split(",")]
        
        # TODO: 获取真实数据
        # 模拟数据
        mock_data = [
            ["000001", "平安银行", 6.5, 0.8, 12.5, 8.3, 15.2, "85"],
            ["000002", "万科A", 8.2, 0.9, 10.8, 5.2, 8.5, "78"],
            ["600519", "贵州茅台", 28.5, 8.5, 25.6, 18.5, 22.3, "92"],
        ]
        
        self._compare_table.setRowCount(len(mock_data))
        for i, row_data in enumerate(mock_data):
            for j, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._compare_table.setItem(i, j, item)
        
        logger.info(f"股票对比: {codes}")
    
    def _on_refresh_pool(self):
        """刷新股票池"""
        # TODO: 获取优质股票池数据
        # 模拟数据
        mock_data = [
            ["600000", "浦发银行", "银行", 5.2, 0.6, 11.5, 4.5, "88", "关注"],
            ["601398", "工商银行", "银行", 4.8, 0.5, 10.8, 5.2, "87", "关注"],
            ["601288", "农业银行", "银行", 4.5, 0.5, 11.2, 5.5, "86", "关注"],
            ["600900", "长江电力", "电力", 18.5, 2.8, 15.6, 3.8, "90", "关注"],
            ["600887", "伊利股份", "食品", 22.3, 5.2, 20.5, 3.2, "89", "关注"],
        ]
        
        self._pool_table.setRowCount(len(mock_data))
        for i, row_data in enumerate(mock_data):
            for j, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._pool_table.setItem(i, j, item)
        
        self.show_message("股票池已刷新")
        logger.info("刷新优质股票池")
    
    def _on_analyze_report(self):
        """分析财报"""
        code = self._report_code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入股票代码")
            return
        
        # TODO: 获取并分析财报数据
        analysis = f"""
股票代码: {code}

=== 财务指标分析 ===

【盈利能力】
- 毛利率: 45.2% (行业平均: 35%) ✓ 优秀
- 净利率: 18.5% (行业平均: 12%) ✓ 优秀
- ROE: 22.3% (行业平均: 15%) ✓ 优秀

【成长能力】
- 营收增长率: 25.6% (同比) ✓ 良好
- 净利润增长率: 28.3% (同比) ✓ 良好

【偿债能力】
- 资产负债率: 35.2% ✓ 健康
- 流动比率: 2.1 ✓ 健康

【运营能力】
- 存货周转率: 8.5次/年
- 应收账款周转率: 12.3次/年

【综合评价】
该股票财务状况良好，盈利能力和成长能力均优于行业平均水平，
偿债能力健康，建议关注。
        """
        
        self._report_text.setText(analysis)
        logger.info(f"财报分析完成: {code}")
