# -*- coding: utf-8 -*-
"""
策略回测页面

提供策略回测功能
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QLineEdit, QDateEdit,
    QTabWidget, QTextEdit, QSplitter, QGroupBox,
    QGridLayout, QProgressBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate

from ui.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class BacktestPage(BasePage):
    """
    策略回测页面
    
    提供策略回测和结果分析
    """
    
    page_id = "backtest"
    page_name = "策略回测"
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def _init_ui(self):
        """初始化UI"""
        super()._init_ui()
        content_layout = self.get_content_layout()
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：策略设置
        left_widget = self._create_settings_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：结果展示
        right_widget = self._create_result_panel()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([350, 850])
        content_layout.addWidget(splitter)
    
    def _create_settings_panel(self) -> QWidget:
        """创建设置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 10, 0)
        
        # 策略选择
        strategy_group = QGroupBox("策略选择")
        strategy_layout = QVBoxLayout(strategy_group)
        
        self._strategy_combo = QComboBox()
        self._strategy_combo.addItems([
            "双均线策略",
            "MACD策略",
            "KDJ策略",
            "布林带策略",
            "自定义策略"
        ])
        strategy_layout.addWidget(self._strategy_combo)
        
        # 策略参数
        self._param_edit = QTextEdit()
        self._param_edit.setPlaceholderText("策略参数 (JSON格式)")
        self._param_edit.setMaximumHeight(100)
        strategy_layout.addWidget(self._param_edit)
        
        layout.addWidget(strategy_group)
        
        # 回测设置
        settings_group = QGroupBox("回测设置")
        settings_layout = QGridLayout(settings_group)
        
        # 股票池
        settings_layout.addWidget(QLabel("股票池:"), 0, 0)
        self._pool_edit = QLineEdit()
        self._pool_edit.setPlaceholderText("000001,000002,600519")
        settings_layout.addWidget(self._pool_edit, 0, 1)
        
        # 开始日期
        settings_layout.addWidget(QLabel("开始日期:"), 1, 0)
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate().addYears(-1))
        settings_layout.addWidget(self._start_date, 1, 1)
        
        # 结束日期
        settings_layout.addWidget(QLabel("结束日期:"), 2, 0)
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        settings_layout.addWidget(self._end_date, 2, 1)
        
        # 初始资金
        settings_layout.addWidget(QLabel("初始资金:"), 3, 0)
        self._capital_edit = QLineEdit("100000")
        settings_layout.addWidget(self._capital_edit, 3, 1)
        
        # 手续费
        settings_layout.addWidget(QLabel("手续费率:"), 4, 0)
        self._commission_edit = QLineEdit("0.0003")
        settings_layout.addWidget(self._commission_edit, 4, 1)
        
        layout.addWidget(settings_group)
        
        # 运行按钮
        self._run_btn = QPushButton("▶️ 开始回测")
        self._run_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
        """)
        self._run_btn.clicked.connect(self._on_run_backtest)
        layout.addWidget(self._run_btn)
        
        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)
        
        layout.addStretch()
        
        return widget
    
    def _create_result_panel(self) -> QWidget:
        """创建结果面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 0, 0, 0)
        
        # 结果标签页
        self._result_tabs = QTabWidget()
        
        # 收益曲线
        self._curve_tab = QWidget()
        curve_layout = QVBoxLayout(self._curve_tab)
        self._curve_label = QLabel("收益曲线")
        self._curve_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        curve_layout.addWidget(self._curve_label)
        self._result_tabs.addTab(self._curve_tab, "📈 收益曲线")
        
        # 交易记录
        self._trade_tab = QWidget()
        trade_layout = QVBoxLayout(self._trade_tab)
        self._trade_text = QTextEdit()
        self._trade_text.setReadOnly(True)
        trade_layout.addWidget(self._trade_text)
        self._result_tabs.addTab(self._trade_tab, "📋 交易记录")
        
        # 绩效指标
        self._metrics_tab = QWidget()
        metrics_layout = QGridLayout(self._metrics_tab)
        
        self._metrics_labels = {}
        metrics = [
            ("总收益率", "total_return"),
            ("年化收益率", "annual_return"),
            ("最大回撤", "max_drawdown"),
            ("夏普比率", "sharpe_ratio"),
            ("胜率", "win_rate"),
            ("盈亏比", "profit_loss_ratio"),
            ("交易次数", "trade_count"),
            ("平均持仓天数", "avg_hold_days"),
        ]
        
        for i, (name, key) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            metrics_layout.addWidget(QLabel(name + ":"), row, col)
            label = QLabel("--")
            label.setStyleSheet("font-weight: bold;")
            self._metrics_labels[key] = label
            metrics_layout.addWidget(label, row, col + 1)
        
        self._result_tabs.addTab(self._metrics_tab, "📊 绩效指标")
        
        # 日志
        self._log_tab = QWidget()
        log_layout = QVBoxLayout(self._log_tab)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        log_layout.addWidget(self._log_text)
        self._result_tabs.addTab(self._log_tab, "📝 日志")
        
        layout.addWidget(self._result_tabs)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self._export_btn = QPushButton("📥 导出报告")
        self._export_btn.clicked.connect(self._on_export_report)
        self._export_btn.setEnabled(False)
        export_layout.addWidget(self._export_btn)
        
        layout.addLayout(export_layout)
        
        return widget
    
    def _on_run_backtest(self):
        """运行回测"""
        self.show_loading(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        
        try:
            # 获取参数
            strategy = self._strategy_combo.currentText()
            start_date = self._start_date.date().toString("yyyy-MM-dd")
            end_date = self._end_date.date().toString("yyyy-MM-dd")
            capital = float(self._capital_edit.text() or 100000)
            commission = float(self._commission_edit.text() or 0.0003)
            
            logger.info(f"开始回测: {strategy} {start_date} ~ {end_date}")
            
            # TODO: 调用回测引擎
            # 模拟回测过程
            import time
            for i in range(101):
                self._progress_bar.setValue(i)
                if i % 20 == 0:
                    self._log_text.append(f"回测进度: {i}%")
                time.sleep(0.02)
            
            # 显示模拟结果
            self._show_mock_results()
            
            self._export_btn.setEnabled(True)
            self.show_message("回测完成")
            
        except Exception as e:
            logger.error(f"回测失败: {e}")
            self.show_error(f"回测失败: {e}")
        finally:
            self.show_loading(False)
            self._progress_bar.setVisible(False)
    
    def _show_mock_results(self):
        """显示模拟结果"""
        # 更新绩效指标
        mock_metrics = {
            "total_return": "35.67%",
            "annual_return": "35.67%",
            "max_drawdown": "-12.34%",
            "sharpe_ratio": "1.85",
            "win_rate": "58.3%",
            "profit_loss_ratio": "1.72",
            "trade_count": "24",
            "avg_hold_days": "8.5",
        }
        
        for key, value in mock_metrics.items():
            if key in self._metrics_labels:
                self._metrics_labels[key].setText(value)
        
        # 更新交易记录
        self._trade_text.setText("""
交易记录:
==========
[买入] 2024-01-15 000001 平安银行 价格: 10.50 数量: 1000
[卖出] 2024-01-20 000001 平安银行 价格: 11.20 数量: 1000 盈利: 700.00
[买入] 2024-02-01 600519 贵州茅台 价格: 1650.00 数量: 10
[卖出] 2024-02-15 600519 贵州茅台 价格: 1720.00 数量: 10 盈利: 700.00
...
        """)
        
        # 更新日志
        self._log_text.append("回测完成!")
        self._log_text.append(f"总收益率: 35.67%")
        self._log_text.append(f"夏普比率: 1.85")
    
    def _on_export_report(self):
        """导出回测报告"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存回测报告", "回测报告.html",
            "HTML文件 (*.html);;PDF文件 (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            # TODO: 生成并保存报告
            self.show_message(f"报告已保存: {file_path}")
            
        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            self.show_error(f"导出失败: {e}")
