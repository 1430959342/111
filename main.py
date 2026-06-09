#!/usr/bin/env python3
"""
每日资本市场热点新闻 TOP10 推送系统
每天自动收集过去24小时 A股+美股+港股 重要新闻，AI排序后通过邮件推送

使用方式:
    python main.py           # 正常运行
    python main.py --dry-run # 只采集和排序，不发送邮件
"""

import argparse
import logging
import sys
from datetime import datetime

import config
from news_collector import collect_news
from news_ranker import rank_news
from email_sender import send_email

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def main():
    parser = argparse.ArgumentParser(description="每日资本市场热点新闻TOP10推送")
    parser.add_argument("--dry-run", action="store_true", help="仅采集排序，不发送邮件")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("🚀 每日资本市场热点新闻 TOP10 推送系统")
    logger.info(f"   运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    logger.info(f"   搜索源: {config.SEARCH_PROVIDER}")
    logger.info(f"   AI模型: {config.DEEPSEEK_MODEL} (DeepSeek)")
    logger.info(f"   发送邮箱: {config.QQ_EMAIL_RECEIVER}")
    logger.info(f"   Dry Run: {args.dry_run}")
    logger.info("=" * 60)

    # ---- 步骤1: 采集新闻 ----
    logger.info("📡 [1/3] 正在采集新闻...")
    raw_news = collect_news()

    if not raw_news:
        logger.error("❌ 未采集到任何新闻，程序终止")
        sys.exit(1)

    logger.info(f"✅ 采集完成: {len(raw_news)} 条去重新闻")

    # ---- 步骤2: AI 排序 ----
    logger.info("🤖 [2/3] AI 正在分析排序...")
    result = rank_news(raw_news)

    top10 = result.get("top10", [])
    # 如果 AI 返回不足 5 条，用原始新闻补齐到 10 条
    if len(top10) < 5:
        logger.warning(f"⚠️ AI 仅返回 {len(top10)} 条，用原始新闻补齐")
        next_rank = len(top10) + 1
        for item in raw_news:
            if len(top10) >= 10:
                break
            # 跳过已经在 AI 结果中的 URL
            existing_urls = {t.get("url", "") for t in top10}
            if item.url in existing_urls:
                continue
            top10.append({
                "rank": next_rank,
                "title": item.title,
                "summary": item.description[:100] if item.description else "",
                "source": item.source,
                "url": item.url,
                "impact_level": "低",
                "impact_market": [item.market],
                "impact_reason": "自动补录",
            })
            next_rank += 1
        # 重新编号
        for i, t in enumerate(top10):
            t["rank"] = i + 1
        result["top10"] = top10

    logger.info(f"✅ AI分析完成: TOP{len(top10)}")
    for item in top10[:3]:
        logger.info(f"   #{item.get('rank')}: {item.get('title', '')[:60]}...")

    # ---- 步骤3: 发送邮件 ----
    if args.dry_run:
        logger.info("📧 [3/3] Dry-run 模式，跳过邮件发送")
        logger.info("✅ 任务完成（dry-run）")
        _print_summary(result)
    else:
        logger.info("📧 [3/3] 正在发送邮件...")
        success = send_email(result)
        if success:
            logger.info("✅ 任务完成！邮件已发送")
        else:
            logger.error("❌ 邮件发送失败，请检查配置")
            sys.exit(1)


def _print_summary(result: dict):
    """打印摘要到控制台（dry-run 用）"""
    print("\n" + "=" * 60)
    print("📊 TOP10 新闻预览")
    print("=" * 60)
    for item in result.get("top10", []):
        rank = item.get("rank", "?")
        title = item.get("title", "")
        impact = item.get("impact_level", "")
        markets = "/".join(item.get("impact_market", []))
        print(f"\n  #{rank} [{impact}影响] [{markets}] {title}")
        print(f"      {item.get('summary', '')[:80]}")
        print(f"      {item.get('source', '')} | {item.get('impact_reason', '')}")


if __name__ == "__main__":
    main()
