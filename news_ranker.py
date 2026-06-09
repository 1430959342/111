"""
AI 筛选排序模块
调用 DeepSeek API 对新闻去重、筛选、按资本市场影响力排序
输出 TOP10 结构化数据
"""

import json
import logging
from datetime import datetime
from typing import Optional

from openai import OpenAI

import config
from news_collector import NewsItem

logger = logging.getLogger(__name__)

# ============================================================
# 系统提示词
# ============================================================
SYSTEM_PROMPT = """你是一位资深全球资本市场分析师，你的任务是筛选和排序过去24小时最重要的资本市场新闻。

## 你的任务
1. 阅读提供的新闻列表
2. 只过滤掉明显无关的新闻（纯娱乐八卦、体育赛事、与商业市场无关的社会新闻）
3. 合并同一事件的多篇报道（去重）
4. 按**资本市场影响力**从高到低排序
5. **必须输出至少8条新闻**，最多10条。即使有些新闻影响力较低，也要保留凑够数量

## ⚠️ 关键规则
- **宁可宽松，不要严格**：涉及股票、经济、央行、政策、公司财报、行业动态、贸易、能源、科技公司的新闻都算资本市场相关
- **必须输出8-10条**：如果收集到的新闻不足8条就全输出；如果超过10条就选TOP10
- **不要因为"不够重要"而删除**：impact_level 用"低"来标记即可，但新闻本身要保留

## 影响力评判标准（权重从高到低）
- 🔴 宏观政策：央行货币政策、财政政策、监管重大变化、地缘政治事件
- 🟠 宏观数据：GDP、CPI、非农就业、PMI、贸易数据
- 🟡 行业动态：重大产业政策、技术突破、行业监管变化
- 🟢 个股/公司：龙头公司财报、重大并购、CEO变动（中小公司也算）

## 输出格式
严格按以下 JSON 格式输出，不要包含任何其他文字：

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
- **top10 数组必须包含 8-10 条，少于8条视为不合格**"""


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

    logger.info(f"  正在用 DeepSeek AI 分析 {len(news_items)} 条新闻...")

    # 构建用户消息
    news_text = _format_news_for_prompt(news_items)

    try:
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )

        response = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": news_text},
            ],
        )

        response_text = response.choices[0].message.content
        result = _parse_response(response_text)

        logger.info(f"  DeepSeek AI 排序完成，输出 TOP{len(result.get('top10', []))}")
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
