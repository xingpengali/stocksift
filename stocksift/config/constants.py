# -*- coding: utf-8 -*-
"""
全局常量定义
"""
from enum import Enum

# ==================== 应用常量 ====================
APP_NAME = "StockSift"
APP_VERSION = "1.0.0"
APP_DISPLAY_NAME = "StockSift A股选股助手"

# ==================== 窗口默认设置 ====================
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_THEME = "light"
DEFAULT_LANGUAGE = "zh_CN"

# ==================== 交易所常量 ====================
EXCHANGE_SSE = "SSE"      # 上交所
EXCHANGE_SZSE = "SZSE"    # 深交所
EXCHANGE_BSE = "BSE"      # 北交所

EXCHANGE_NAMES = {
    EXCHANGE_SSE: "上海证券交易所",
    EXCHANGE_SZSE: "深圳证券交易所",
    EXCHANGE_BSE: "北京证券交易所"
}

# ==================== 市场板块 ====================
MARKET_MAIN = "main"          # 主板
MARKET_GEM = "gem"            # 创业板
MARKET_STAR = "star"          # 科创板
MARKET_BJ = "bj"              # 北交所

MARKET_NAMES = {
    MARKET_MAIN: "主板",
    MARKET_GEM: "创业板",
    MARKET_STAR: "科创板",
    MARKET_BJ: "北交所"
}

# ==================== 数据周期 ====================
PERIOD_DAILY = "daily"
PERIOD_WEEKLY = "weekly"
PERIOD_MONTHLY = "monthly"

PERIOD_NAMES = {
    PERIOD_DAILY: "日线",
    PERIOD_WEEKLY: "周线",
    PERIOD_MONTHLY: "月线"
}

PERIOD_MAP = {
    "1D": PERIOD_DAILY,
    "1W": PERIOD_WEEKLY,
    "1M": PERIOD_MONTHLY,
}

# ==================== 财务报告类型 ====================
REPORT_TYPE_Q1 = "Q1"
REPORT_TYPE_Q2 = "Q2"
REPORT_TYPE_Q3 = "Q3"
REPORT_TYPE_ANNUAL = "annual"

REPORT_TYPE_NAMES = {
    REPORT_TYPE_Q1: "一季报",
    REPORT_TYPE_Q2: "半年报",
    REPORT_TYPE_Q3: "三季报",
    REPORT_TYPE_ANNUAL: "年报"
}

# ==================== 筛选运算符 ====================
OPERATOR_GT = ">"
OPERATOR_LT = "<"
OPERATOR_GTE = ">="
OPERATOR_LTE = "<="
OPERATOR_EQ = "="
OPERATOR_BETWEEN = "between"
OPERATOR_IN = "in"

OPERATORS = [
    (OPERATOR_GT, "大于"),
    (OPERATOR_LT, "小于"),
    (OPERATOR_GTE, "大于等于"),
    (OPERATOR_LTE, "小于等于"),
    (OPERATOR_EQ, "等于"),
    (OPERATOR_BETWEEN, "区间"),
    (OPERATOR_IN, "包含")
]

# ==================== 技术指标类型 ====================
INDICATOR_MACD = "macd"
INDICATOR_KDJ = "kdj"
INDICATOR_RSI = "rsi"
INDICATOR_MA = "ma"
INDICATOR_BOLL = "boll"

INDICATOR_NAMES = {
    INDICATOR_MACD: "MACD",
    INDICATOR_KDJ: "KDJ",
    INDICATOR_RSI: "RSI",
    INDICATOR_MA: "均线",
    INDICATOR_BOLL: "布林带"
}

# ==================== 均线周期 ====================
MA_PERIODS = [5, 10, 20, 60, 120, 250]
DEFAULT_MA_PERIODS = [5, 10, 20, 60]

# ==================== 预警类型 ====================
ALERT_TYPE_PRICE = "price"
ALERT_TYPE_CHANGE = "change"
ALERT_TYPE_VOLUME = "volume"
ALERT_TYPE_INDICATOR = "indicator"

ALERT_TYPE_NAMES = {
    ALERT_TYPE_PRICE: "价格预警",
    ALERT_TYPE_CHANGE: "涨跌幅预警",
    ALERT_TYPE_VOLUME: "成交量预警",
    ALERT_TYPE_INDICATOR: "指标预警"
}

# ==================== 预警运算符 ====================
ALERT_ABOVE = "above"
ALERT_BELOW = "below"
ALERT_CROSS_UP = "cross_up"
ALERT_CROSS_DOWN = "cross_down"

# ==================== 数据库配置 ====================
DEFAULT_DB_NAME = "stocksift.db"
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 3600

# ==================== 缓存配置 ====================
DEFAULT_CACHE_TTL = 3600  # 1小时
MAX_CACHE_SIZE = 1000

# ==================== 分页配置 ====================
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
MIN_PAGE_SIZE = 10

# ==================== 图表配置 ====================
DEFAULT_KLINE_DAYS = 120
MAX_KLINE_DAYS = 1000

# ==================== 数据刷新配置 ====================
DEFAULT_REFRESH_INTERVAL = 5  # 秒
MIN_REFRESH_INTERVAL = 3
MAX_REFRESH_INTERVAL = 60

# ==================== 数据源配置 ====================
DATA_SOURCE_TUSHARE = "tushare"
DATA_SOURCE_BAOSTOCK = "baostock"

DEFAULT_DATA_SOURCE_PRIORITY = [DATA_SOURCE_TUSHARE, DATA_SOURCE_BAOSTOCK]

# ==================== 路径配置 ====================
DATA_DIR = "data"
CACHE_DIR = "data/cache"
DB_DIR = "data/db"
LOG_DIR = "data/logs"
RESOURCES_DIR = "resources"
ICONS_DIR = "resources/icons"
THEMES_DIR = "resources/themes"

# ==================== 日志配置 ====================
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5

# ==================== 枚举类 ====================
class Theme(Enum):
    """主题枚举"""
    LIGHT = "light"
    DARK = "dark"


class DataSourceType(Enum):
    """数据源类型枚举"""
    TUSHARE = "tushare"
    BAOSTOCK = "baostock"


class AlertOperator(Enum):
    """预警运算符枚举"""
    ABOVE = "above"
    BELOW = "below"
    CROSS_UP = "cross_up"
    CROSS_DOWN = "cross_down"


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class TrendDirection(Enum):
    """趋势方向枚举"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


# ==================== 错误码 ====================
class ErrorCode:
    """错误码定义"""
    SUCCESS = 0
    
    # 网络错误 (1000-1999)
    NETWORK_ERROR = 1001
    CONNECTION_TIMEOUT = 1002
    CONNECTION_REFUSED = 1003
    
    # 数据源错误 (2000-2999)
    DATA_SOURCE_ERROR = 2001
    DATA_SOURCE_NOT_AVAILABLE = 2002
    DATA_NOT_FOUND = 2003
    RATE_LIMIT_EXCEEDED = 2004
    
    # 数据库错误 (3000-3999)
    DATABASE_ERROR = 3001
    DATABASE_CONNECTION_ERROR = 3002
    DATABASE_QUERY_ERROR = 3003
    
    # 验证错误 (4000-4999)
    VALIDATION_ERROR = 4001
    INVALID_PARAMETER = 4002
    MISSING_REQUIRED_FIELD = 4003
    
    # 业务错误 (5000-5999)
    NOT_FOUND = 5001
    ALREADY_EXISTS = 5002
    OPERATION_NOT_ALLOWED = 5003
    
    # 系统错误 (9000-9999)
    SYSTEM_ERROR = 9001
    UNKNOWN_ERROR = 9999
