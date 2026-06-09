"""
AI 筛选排序模块
调用 Anthropic Claude API 对新闻去重、筛选、按资本市场影响力排序
输出 TOP10 结构化数据
"""

import json
import logging
from datetime import datetime
from typing import Optional

import anthropic

import config
from news_collector import NewsItem

logger = logging.getLogger(__name__)

# ============================================================
# 系统提示词
# ============================================================
SYSTEM_PROMPT = """你是一位资深全球资本市场分析师，你的任务是筛选和排序过去24小时最重要的资本市场新闻。

## 你的任务
1. 阅读提供的新闻列表
2. 过滤掉与资本市场无关的新闻（娱乐八卦、社会新闻、体育等）
3. 合并同一事件的多篇报道（去重）
4. 按**资本市场影响力**从高到低排序
5. 选出 TOP 10 最重要的新闻

## 影响力评判标准（权重从高到低）
- 🔴 宏观政策：央行货币政策、财政政策、监管重大变化、地缘政治事件
- 🟠 宏观数据：GDP、CPI、非农就业、PMI、贸易数据
- 🟡 行业动态：重大产业政策、技术突破、行业监管变化
- 🟢 个股/公司：龙头公司财报、重大并购、CEO变动（仅限市值超千亿公司）

## 输出格式
必须严格按照以下 JSON 格式输出，不要包含任何其他文字：

```json
{
  "date": "YYYY-MM-DD",
  "market_summary": {
    "A股": "30字以内A股市场概况",
    "美股": "30字以内美股市场概况",
    "港股": "30字以内港股市场概况"
  },
  "top10": [
    {
      "rank": 1,
      "title": "新闻标题（中文，简洁准确）",
      "summary": "50字以内摘要，说清事件和影响",
      "source": "来源媒体名称",
      "url": "原文链接",
      "impact_level": "高",
      "impact_market": ["A股", "美股"],
      "impact_reason": "一句话解释为什么重要"
    }
  ]
}
```

## 注意事项
- impact_level 取值为: "高" / "中" / "低"
- impact_market 是数组，可包含多个市场: "A股" / "美股" / "港股"
- 确保输出是合法 JSON，不要有尾随逗号
- title 和 summary 都使用中文
- 新闻总数不足10条时，有多少输出多少（rank 从1连续编号）"""


def rank_news(news_items: list[NewsItem]) -> dict:
    """
    主入口：对新闻进行AI筛选排序
    参数:
        news_items: 原始新闻列表
    返回:
        dict: 包含 top10 和市场概况的结构化数据
    """
    if not news_items:
        logger.warning("没有新闻数据可供排序")
        return _empty_result()

    logger.info(f"  正在用 AI 分析 {len(news_items)} 条新闻...")

    # 构建用户消息
    news_text = _format_news_for_prompt(news_items)

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": news_text}],
        )

        response_text = message.content[0].text
        result = _parse_response(response_text)

        logger.info(f"  AI 排序完成，输出 TOP{len(result.get('top10', []))}")
        return result

    except Exception as e:
        logger.error(f"AI 排序失败: {e}")
        return _empty_result(error=str(e))


def _format_news_for_prompt(news_items: list[NewsItem]) -> str:
    """将新闻列表格式化为给 AI 的输入文本"""
    lines = ["以下是过去24小时的全球资本市场相关新闻列表：\n"]
    for i, item in enumerate(news_items, 1):
        lines.append(
            f"[{i}] 【{item.market}】{item.title}\n"
            f"    来源: {item.source}\n"
            f"    时间: {item.published_at}\n"
            f"    摘要: {item.description}\n"
            f"    链接: {item.url}\n"
        )
    return "\n".join(lines)


def _parse_response(text: str) -> dict:
    """解析 AI 返回的 JSON，处理可能的格式问题"""
    # 尝试提取 JSON 块
    text = text.strip()

    # 去掉可能的 markdown 代码块标记
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试找到 JSON 对象
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.error(f"无法解析 AI 返回的 JSON: {text[:500]}...")
        return _empty_result(error="JSON解析失败")


def _empty_result(error: str = "") -> dict:
    """返回空结果"""
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "market_summary": {
            "A股": "暂无数据",
            "美股": "暂无数据",
            "港股": "暂无数据",
        },
        "top10": [],
        "error": error,
    }


if __name__ == "__main__":
    # 测试用
    logging.basicConfig(level=logging.DEBUG)
    mock_news = [
        NewsItem("美联储宣布降息50个基点", "http://example.com/1", "Reuters", "2026-06-09", "美联储降息"),
        NewsItem("某明星演唱会门票售罄", "http://example.com/2", "娱乐日报", "2026-06-09", "娱乐新闻"),
    ]
    result = rank_news(mock_news)
    print(json.dumps(result, ensure_ascii=False, indent=2))
