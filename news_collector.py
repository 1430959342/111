"""
新闻采集模块
从 NewsAPI / Bing Search API 搜索全球资本市场新闻
支持 A股、美股、港股三个市场的多关键词搜索
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)


class NewsItem:
    """单条新闻数据结构"""

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        published_at: str,
        description: str = "",
        market: str = "",
        query_keyword: str = "",
    ):
        self.title = title
        self.url = url
        self.source = source
        self.published_at = published_at
        self.description = description
        self.market = market
        self.query_keyword = query_keyword

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "description": self.description,
            "market": self.market,
            "query_keyword": self.query_keyword,
        }

    def __repr__(self):
        return f"NewsItem({self.market}: {self.title[:50]}...)"


def collect_news() -> list[NewsItem]:
    """
    主入口：从多源采集过去24小时的资本市场新闻
    返回去重后的 NewsItem 列表
    """
    all_news: list[NewsItem] = []

    for market, queries in config.SEARCH_QUERIES.items():
        logger.info(f"  正在搜索 {market} 市场新闻...")
        for query in queries:
            try:
                if config.SEARCH_PROVIDER == "newsapi":
                    results = _search_newsapi(query, market)
                else:
                    results = _search_bing(query, market)
                all_news.extend(results)
                logger.debug(f"    关键词 [{query}]: 获取 {len(results)} 条")
            except Exception as e:
                logger.error(f"    搜索失败 [{query}]: {e}")

    # URL 去重
    seen_urls = set()
    deduped: list[NewsItem] = []
    for item in all_news:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            deduped.append(item)
        else:
            # 如果来自不同市场/关键词的相同URL，保留第一个
            pass

    logger.info(f"  共采集 {len(all_news)} 条原始新闻，去重后 {len(deduped)} 条")
    return deduped


def _search_newsapi(query: str, market: str) -> list[NewsItem]:
    """
    通过 NewsAPI 搜索新闻
    API文档: https://newsapi.org/docs/endpoints/everything
    """
    from_date = (datetime.now(timezone.utc) - timedelta(hours=config.NEWS_LOOKBACK_HOURS)).strftime("%Y-%m-%dT%H:%M:%S")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "relevancy",
        "language": "zh,en",  # 中英文
        "pageSize": config.ARTICLES_PER_QUERY,
        "apiKey": config.NEWSAPI_KEY,
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "ok":
        logger.warning(f"NewsAPI 返回非正常状态: {data.get('message', 'unknown')}")
        return []

    articles = data.get("articles", [])
    results = []
    for art in articles:
        if not art.get("title"):
            continue
        results.append(
            NewsItem(
                title=art["title"].strip(),
                url=art.get("url", ""),
                source=art.get("source", {}).get("name", "未知来源"),
                published_at=art.get("publishedAt", ""),
                description=art.get("description", ""),
                market=market,
                query_keyword=query,
            )
        )
    return results


def _search_bing(query: str, market: str) -> list[NewsItem]:
    """
    通过 Bing Web Search API 搜索新闻
    API文档: https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/
    """
    url = "https://api.bing.microsoft.com/v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": config.BING_SEARCH_API_KEY}
    params = {
        "q": query,
        "count": config.ARTICLES_PER_QUERY,
        "freshness": "Day",  # 过去24小时
        "mkt": "zh-CN" if "A股" in market or "港股" in market else "en-US",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    articles = data.get("value", [])
    results = []
    for art in articles:
        results.append(
            NewsItem(
                title=art.get("name", "").strip(),
                url=art.get("url", ""),
                source=art.get("provider", [{}])[0].get("name", "未知来源") if art.get("provider") else "未知来源",
                published_at=art.get("datePublished", ""),
                description=art.get("description", ""),
                market=market,
                query_keyword=query,
            )
        )
    return results


if __name__ == "__main__":
    # 测试用
    logging.basicConfig(level=logging.DEBUG)
    news = collect_news()
    for i, item in enumerate(news, 1):
        print(f"{i}. [{item.market}] {item.title}")
        print(f"   {item.source} | {item.published_at}")
        print(f"   {item.url}")
        print()
