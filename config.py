"""
配置管理模块
从环境变量读取所有配置，支持 .env 文件本地开发
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件（本地开发用，GitHub Actions 通过 Secrets 注入）
load_dotenv()


def _require(key: str) -> str:
    """读取必需的环境变量，缺失时退出"""
    value = os.getenv(key, "").strip()
    if not value:
        print(f"[ERROR] 缺少必需的环境变量: {key}")
        print(f"  请在 .env 文件或 GitHub Secrets 中设置 {key}")
        sys.exit(1)
    return value


def _optional(key: str, default: str = "") -> str:
    """读取可选的环境变量"""
    return os.getenv(key, default).strip()


# ============================================================
# 搜索 API 配置
# ============================================================
# 优先使用 NewsAPI（更简单），备选 Bing
NEWSAPI_KEY = _optional("NEWSAPI_KEY")
BING_SEARCH_API_KEY = _optional("BING_SEARCH_API_KEY")

# 至少需要配置一个搜索 API
if not NEWSAPI_KEY and not BING_SEARCH_API_KEY:
    print("[ERROR] 至少需要配置一个搜索 API: NEWSAPI_KEY 或 BING_SEARCH_API_KEY")
    print("  - NewsAPI 注册: https://newsapi.org/register (免费 100次/天)")
    print("  - Bing Search API: Azure 门户创建 (免费 1000次/月)")
    sys.exit(1)

# 默认搜索源
SEARCH_PROVIDER = "newsapi" if NEWSAPI_KEY else "bing"

# ============================================================
# DeepSeek API 配置
# ============================================================
DEEPSEEK_API_KEY = _require("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = _optional("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ============================================================
# QQ 邮箱配置
# ============================================================
QQ_EMAIL_SENDER = _require("QQ_EMAIL_SENDER")
QQ_EMAIL_PASSWORD = _require("QQ_EMAIL_PASSWORD")
QQ_EMAIL_RECEIVER = _require("QQ_EMAIL_RECEIVER")

# SMTP 服务器配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465  # SSL

# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL = _optional("LOG_LEVEL", "INFO")

# ============================================================
# 搜索关键词配置（覆盖 A股 / 美股 / 港股）
# ============================================================
SEARCH_QUERIES = {
    "A股": [
        "A股 重大政策 证监会 央行 今日",
        "沪深股市 资金流向 板块轮动",
        "中国经济 宏观数据 GDP CPI PMI",
    ],
    "美股": [
        "US stock market Federal Reserve interest rate today",
        "NASDAQ S&P500 tech stocks AI semiconductor",
        "美股 美联储 非农 CPI 科技股",
    ],
    "港股": [
        "港股 恒生指数 恒生科技",
        "Hong Kong stock market China policy",
    ],
    "黄金": [
        "gold price COMEX spot today Federal Reserve",
        "黄金价格 上海金交所 国际金价 今日",
        "gold inflation hedge central bank buying",
    ],
}

# 每次搜索返回的文章数
ARTICLES_PER_QUERY = 10

# 新闻时间范围（小时）
NEWS_LOOKBACK_HOURS = 24
