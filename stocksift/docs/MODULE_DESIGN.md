# StockSift 模块设计文档

## 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        StockSift 选股软件                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│  │   表现层    │  │   业务层    │  │   数据层    │  │ 基础层  │ │
│  │    UI      │  │   Core     │  │  Data      │  │ Common │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───┬────┘ │
│         │                │                │             │      │
│         ▼                ▼                ▼             ▼      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│  │ 主窗口      │  │ 筛选引擎    │  │ 数据源适配  │  │ 配置   │ │
│  │ 页面路由    │  │ 策略引擎    │  │ 本地数据库  │  │ 日志   │ │
│  │ 组件库      │  │ 回测引擎    │  │ 数据缓存    │  │ 工具   │ │
│  │ 对话框      │  │ 预警引擎    │  │ 数据模型    │  │ 常量   │ │
│  │ 主题管理    │  │ 分析引擎    │  │             │  │        │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 一、表现层 (UI Layer) - `src/ui/`

### 1.1 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **主窗口** | `main_window.py` | 应用主窗口、布局框架、菜单栏、状态栏 |
| **主题管理** | `theme_manager.py` | 浅色/深色主题切换、样式管理 |
| **页面基类** | `base_page.py` | 页面通用基类、生命周期管理 |

### 1.2 页面模块 (`src/ui/pages/`)

| 页面 | 文件 | 功能描述 |
|------|------|----------|
| 市场概览 | `market_overview.py` | 大盘指数、板块热点、涨跌分布、估值概览 |
| 股票筛选 | `screener_page.py` | 筛选条件面板、结果表格、条件保存/加载 |
| 股票详情 | `stock_detail.py` | K线图表、技术指标、资金流向、财务数据、价值投资面板 |
| 自选股 | `watchlist_page.py` | 分组管理、股票列表、实时刷新、预警设置 |
| 策略回测 | `backtest_page.py` | 策略编辑、回测参数、结果展示、绩效分析 |
| 价值投资 | `value_investing_page.py` | 估值工具、股票对比、优质股票池、财报分析 |

### 1.3 组件模块 (`src/ui/widgets/`)

| 组件 | 文件 | 功能描述 |
|------|------|----------|
| K线图表 | `kline_chart.py` | 股票K线图、技术指标叠加、缩放平移 |
| 股票表格 | `stock_table.py` | 股票列表表格、排序筛选、分页 |
| 筛选面板 | `filter_panel.py` | 筛选条件编辑器、条件组合 |
| 指标卡片 | `metric_card.py` | 关键指标展示卡片 |
| 资金流向图 | `capital_flow_chart.py` | 资金流向饼图、趋势图 |
| 估值图表 | `valuation_chart.py` | 历史估值百分位图、估值区间 |
| 财务雷达图 | `financial_radar.py` | 财务指标雷达图 |
| 分页器 | `pagination.py` | 表格分页组件 |
| 搜索框 | `search_box.py` | 股票搜索自动完成 |
| 条件标签 | `filter_tag.py` | 已选筛选条件标签展示 |
| 预警列表 | `alert_list.py` | 预警规则列表展示 |

### 1.4 对话框模块 (`src/ui/dialogs/`)

| 对话框 | 文件 | 功能描述 |
|--------|------|----------|
| 设置 | `settings_dialog.py` | 应用配置、数据源配置、主题设置 |
| 预警设置 | `alert_dialog.py` | 预警条件设置、通知方式 |
| 估值计算 | `valuation_dialog.py` | DCF/格雷厄姆/PEG估值计算 |
| 股票对比 | `compare_dialog.py` | 多股票对比选择、对比维度 |
| 数据导出 | `export_dialog.py` | 导出选项、格式选择 |
| 关于 | `about_dialog.py` | 版本信息、开源协议 |

---

## 二、业务层 (Core Layer) - `src/core/`

| 模块 | 文件 | 职责描述 |
|------|------|----------|
| **筛选引擎** | `screener.py` | 多维度条件筛选、SQL动态构建、结果排序分页 |
| **策略引擎** | `strategy.py` | 策略定义、条件组合管理、策略保存/加载 |
| **回测引擎** | `backtest.py` | 历史数据回测、交易模拟、绩效计算 |
| **预警引擎** | `alert_engine.py` | 实时监控、预警触发、通知推送 |
| **数据获取** | `data_fetcher.py` | 统一数据获取接口、数据聚合 |

---

## 三、分析层 (Analysis Layer) - `src/analysis/`

| 模块 | 文件 | 职责描述 |
|------|------|----------|
| **技术分析** | `technical.py` | MACD/KDJ/RSI/均线/布林带计算、信号识别 |
| **基本面分析** | `fundamental.py` | 财务指标计算、同行业对比、财务健康评分 |
| **资金流向** | `capital_flow.py` | 主力/大单/散户资金流向分析、连续净流入计算 |
| **情绪分析** | `sentiment.py` | 市场情绪指标、板块热度分析 |
| **估值分析** | `valuation.py` | PEG/PCF/DCF/格雷厄姆估值、历史估值百分位 |
| **财务健康度** | `financial_health.py` | 财务风险评分、异常指标检测、杜邦分析 |

---

## 四、数据层 (Data Layer)

### 4.1 数据源适配器 (`src/datasource/`)

| 模块 | 文件 | 职责描述 |
|------|------|----------|
| **基类** | `base_adapter.py` | 数据源抽象基类、统一接口定义 |
| **Tushare** | `tushare_adapter.py` | Tushare Pro API 接入、数据获取 |
| **Baostock** | `baostock_adapter.py` | Baostock API 接入、数据获取 |
| **数据源管理** | `data_source_manager.py` | 多数据源协调、优先级管理、故障切换 |

### 4.2 数据模型 (`src/models/`)

| 模型 | 文件 | 职责描述 |
|------|------|----------|
| **数据库** | `database.py` | SQLAlchemy ORM、连接管理、会话管理 |
| **股票** | `stock.py` | 股票基本信息模型（代码、名称、行业等） |
| **行情** | `quote.py` | 实时行情数据模型（价格、涨跌、成交量等） |
| **K线** | `kline.py` | 历史K线数据模型（日/周/月线） |
| **财务** | `financial.py` | 财务报表数据模型（季报/年报数据） |
| **估值** | `valuation.py` | 估值历史数据模型（PE/PB百分位） |
| **预警** | `alert.py` | 预警规则、预警记录模型 |
| **策略** | `strategy.py` | 策略定义、策略参数模型 |
| **回测** | `backtest_result.py` | 回测结果、交易记录模型 |
| **自选股** | `watchlist.py` | 自选股分组、股票关联模型 |

---

## 五、基础层 (Common Layer)

### 5.1 配置模块 (`config/`)

| 模块 | 文件 | 职责描述 |
|------|------|----------|
| **设置** | `settings.py` | 应用配置管理、用户偏好、配置文件读写 |
| **常量** | `constants.py` | 应用常量、枚举定义、默认配置 |

### 5.2 工具模块 (`src/utils/`)

| 模块 | 文件 | 职责描述 |
|------|------|----------|
| **日志** | `logger.py` | 日志记录、日志轮转、分级输出 |
| **导出** | `exporter.py` | Excel/CSV导出、数据格式化 |
| **工具函数** | `helpers.py` | 通用工具函数、日期处理、数值格式化 |
| **事件总线** | `event_bus.py` | 组件间通信、事件发布订阅 |
| **缓存** | `cache.py` | 内存缓存管理、缓存过期策略 |
| **验证** | `validators.py` | 数据验证、输入校验 |
| **装饰器** | `decorators.py` | 通用装饰器（重试、计时、缓存等） |

---

## 六、资源层 (`resources/`)

| 目录 | 用途 |
|------|------|
| `icons/` | 应用图标、按钮图标、状态图标 |
| `themes/` | 主题样式文件（QSS）、颜色定义 |
| `strategies/` | 预设策略模板、策略示例 |
| `fonts/` | 自定义字体文件 |

---

## 七、模块依赖关系

```
                    ┌─────────────────┐
                    │   UI Layer      │
                    │  (pages/widgets)│
                    └────────┬────────┘
                             │ 使用
                             ▼
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│  Common     │◄────►│   Core Layer    │◄────►│  Analysis   │
│  Layer      │      │ (screener/alert)│      │   Layer     │
└─────────────┘      └────────┬────────┘      └─────────────┘
                              │ 调用
                              ▼
                    ┌─────────────────┐
                    │   Data Layer    │
                    │(datasource/     │
                    │  models)        │
                    └─────────────────┘
```

### 依赖规则
1. **上层可以调用下层，下层不能调用上层**
2. **同层之间尽量减少依赖，通过事件总线通信**
3. **Common Layer 可被所有层调用**
4. **Data Layer 不依赖其他业务层**

---

## 八、开发优先级

### P0 - 基础设施（必须先完成）
- [ ] `config/settings.py` - 配置管理
- [ ] `config/constants.py` - 常量定义
- [ ] `utils/logger.py` - 日志系统
- [ ] `models/database.py` - 数据库连接
- [ ] `datasource/base_adapter.py` - 数据源基类
- [ ] `datasource/tushare_adapter.py` - Tushare接入

### P1 - 核心功能（MVP）
- [ ] `models/stock.py`, `quote.py` - 核心模型
- [ ] `ui/main_window.py` - 主窗口
- [ ] `ui/pages/screener_page.py` - 筛选页面
- [ ] `ui/widgets/stock_table.py` - 股票表格
- [ ] `core/screener.py` - 筛选引擎
- [ ] `ui/pages/stock_detail.py` - 详情页面
- [ ] `ui/widgets/kline_chart.py` - K线图表

### P2 - 功能增强
- [ ] `ui/pages/watchlist.py` - 自选股
- [ ] `core/alert_engine.py` - 预警引擎
- [ ] `analysis/technical.py` - 技术分析
- [ ] `ui/pages/market_overview.py` - 市场概览
- [ ] `analysis/capital_flow.py` - 资金流向

### P3 - 高级功能
- [ ] `core/backtest.py` - 回测引擎
- [ ] `ui/pages/backtest_page.py` - 回测页面
- [ ] `core/strategy.py` - 策略引擎

### P4 - 价值投资功能
- [ ] `analysis/fundamental.py` - 基本面分析
- [ ] `analysis/valuation.py` - 估值分析
- [ ] `analysis/financial_health.py` - 财务健康度
- [ ] `ui/pages/value_investing_page.py` - 价值投资页面
- [ ] `ui/widgets/valuation_chart.py` - 估值图表
- [ ] `ui/dialogs/valuation_dialog.py` - 估值计算对话框

### P5 - 优化完善
- [ ] `ui/theme_manager.py` - 主题管理
- [ ] `utils/exporter.py` - 数据导出
- [ ] `utils/event_bus.py` - 事件总线
- [ ] 性能优化、代码重构

---

## 九、文件目录结构

```
stocksift/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── screener.py
│   │   ├── strategy.py
│   │   ├── backtest.py
│   │   ├── alert_engine.py
│   │   └── data_fetcher.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── technical.py
│   │   ├── fundamental.py
│   │   ├── capital_flow.py
│   │   ├── sentiment.py
│   │   ├── valuation.py
│   │   └── financial_health.py
│   ├── datasource/
│   │   ├── __init__.py
│   │   ├── base_adapter.py
│   │   ├── tushare_adapter.py
│   │   ├── baostock_adapter.py
│   │   └── data_source_manager.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── stock.py
│   │   ├── quote.py
│   │   ├── kline.py
│   │   ├── financial.py
│   │   ├── valuation.py
│   │   ├── alert.py
│   │   ├── strategy.py
│   │   ├── backtest_result.py
│   │   └── watchlist.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── theme_manager.py
│   │   ├── base_page.py
│   │   ├── pages/
│   │   │   ├── __init__.py
│   │   │   ├── market_overview.py
│   │   │   ├── screener_page.py
│   │   │   ├── stock_detail.py
│   │   │   ├── watchlist.py
│   │   │   ├── backtest_page.py
│   │   │   └── value_investing_page.py
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── kline_chart.py
│   │   │   ├── stock_table.py
│   │   │   ├── filter_panel.py
│   │   │   ├── metric_card.py
│   │   │   ├── capital_flow_chart.py
│   │   │   ├── valuation_chart.py
│   │   │   ├── financial_radar.py
│   │   │   ├── pagination.py
│   │   │   ├── search_box.py
│   │   │   ├── filter_tag.py
│   │   │   └── alert_list.py
│   │   └── dialogs/
│   │       ├── __init__.py
│   │       ├── settings_dialog.py
│   │       ├── alert_dialog.py
│   │       ├── valuation_dialog.py
│   │       ├── compare_dialog.py
│   │       ├── export_dialog.py
│   │       └── about_dialog.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── exporter.py
│       ├── helpers.py
│       ├── event_bus.py
│       ├── cache.py
│       ├── validators.py
│       └── decorators.py
├── resources/
│   ├── icons/
│   ├── themes/
│   ├── strategies/
│   └── fonts/
├── docs/
│   ├── PRD.md
│   └── MODULE_DESIGN.md
├── data/
│   ├── cache/
│   ├── db/
│   └── logs/
├── main.py
└── requirements.txt
```
