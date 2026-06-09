"""
邮件推送模块
通过 QQ 邮箱 SMTP 发送 HTML 格式的每日TOP10新闻邮件
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)

# 影响等级对应的颜色
IMPACT_COLORS = {"高": "#e74c3c", "中": "#f39c12", "低": "#3498db"}
IMPACT_LABELS = {"高": "🔥 高影响", "中": "⭐ 中等", "低": "📌 关注"}

# 市场标签颜色
MARKET_COLORS = {"A股": "#e74c3c", "美股": "#2980b9", "港股": "#27ae60"}


def send_email(result: dict) -> bool:
    """
    发送每日新闻邮件
    参数:
        result: news_ranker 返回的结构化数据
    返回:
        bool: 发送成功返回 True
    """
    if not result.get("top10"):
        logger.warning("没有TOP10数据，跳过发送")
        return False

    html_content = _build_html(result)
    subject = f"📊 每日资本市场热点 TOP10 - {result.get('date', datetime.now().strftime('%Y-%m-%d'))}"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.QQ_EMAIL_SENDER
        msg["To"] = config.QQ_EMAIL_RECEIVER
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, timeout=30) as server:
            server.login(config.QQ_EMAIL_SENDER, config.QQ_EMAIL_PASSWORD)
            server.sendmail(config.QQ_EMAIL_SENDER, config.QQ_EMAIL_RECEIVER, msg.as_string())

        logger.info(f"✅ 邮件发送成功 → {config.QQ_EMAIL_RECEIVER}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("QQ邮箱认证失败，请检查授权码是否正确")
        return False
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def _build_html(result: dict) -> str:
    """构建 HTML 邮件内容"""
    date_str = result.get("date", datetime.now().strftime("%Y-%m-%d"))
    top10 = result.get("top10", [])
    summary = result.get("market_summary", {})

    # 生成新闻卡片
    cards_html = ""
    for item in top10:
        rank = item.get("rank", "?")
        title = item.get("title", "无标题")
        desc = item.get("summary", "")
        source = item.get("source", "")
        url = item.get("url", "#")
        impact = item.get("impact_level", "中")
        markets = item.get("impact_market", [])
        reason = item.get("impact_reason", "")

        impact_color = IMPACT_COLORS.get(impact, "#f39c12")
        impact_label = IMPACT_LABELS.get(impact, "⭐ 中等")

        # 市场标签
        market_tags = ""
        for m in markets:
            mc = MARKET_COLORS.get(m, "#666")
            market_tags += (
                f'<span style="display:inline-block;background:{mc};color:#fff;'
                f'padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px;">{m}</span>'
            )

        cards_html += f"""
        <div style="border-left:4px solid {impact_color}; margin-bottom:24px; padding:16px 20px;
                    background:#fff; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            <!-- 标题行 -->
            <div style="display:flex; align-items:flex-start; margin-bottom:10px;">
                <span style="background:{impact_color}; color:#fff; font-size:14px; font-weight:bold;
                      min-width:28px; height:28px; display:inline-flex; align-items:center;
                      justify-content:center; border-radius:50%; margin-right:12px; flex-shrink:0;
                      margin-top:2px;">{rank}</span>
                <div>
                    <a href="{url}" style="color:#1a1a1a; text-decoration:none; font-size:17px;
                          font-weight:700; line-height:1.5;">{title}</a>
                    <div style="margin-top:4px;">
                        {market_tags}
                        <span style="font-size:12px; color:{impact_color}; font-weight:600;">{impact_label}</span>
                    </div>
                </div>
            </div>
            <!-- 摘要正文 -->
            <div style="color:#333; font-size:14px; line-height:1.8; margin:12px 0;
                        padding:10px 14px; background:#f8f9fa; border-radius:6px;">
                {desc}
            </div>
            <!-- 底部信息 -->
            <div style="display:flex; align-items:center; justify-content:space-between;
                        font-size:12px; color:#888; margin-top:8px;">
                <span>📰 {source}</span>
                <span style="color:#666;">💡 {reason}</span>
            </div>
        </div>"""

    # 市场概况
    summary_html = ""
    market_icons = {"A股": "🇨🇳", "美股": "🇺🇸", "港股": "🇭🇰"}
    for market in ["A股", "美股", "港股"]:
        text = summary.get(market, "暂无数据")
        icon = market_icons.get(market, "📊")
        summary_html += (
            f'<span style="display:inline-block;margin-right:16px;font-size:14px;">'
            f"{icon} <b>{market}:</b> {text}</span>"
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#f4f6f9; font-family:-apple-system, BlinkMacSystemFont,
      'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;">

<!-- 头部 -->
<div style="background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding:28px 24px;
     text-align:center; border-radius:0 0 16px 16px;">
    <h1 style="color:#fff; margin:0; font-size:24px; font-weight:700;">
        📊 每日资本市场热点 TOP10
    </h1>
    <p style="color:#aab; margin:8px 0 0; font-size:13px;">{date_str} · 过去24小时全球资本市场最值得关注的新闻</p>
</div>

<!-- 主内容 -->
<div style="max-width:680px; margin:0 auto; padding:16px;">

    <!-- 市场概况 -->
    <div style="background:#fff; border-radius:8px; padding:14px 18px; margin-bottom:18px;
                box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="font-size:13px; color:#666; margin-bottom:6px;">📋 市场概况</div>
        {summary_html}
    </div>

    <!-- 新闻列表 -->
    {cards_html}

    <!-- AI 提示 -->
    <div style="background:#fef9e7; border:1px solid #f9e79f; border-radius:8px; padding:12px 16px;
                margin-top:20px; font-size:12px; color:#7d6608;">
        🤖 本报告由 AI（DeepSeek）自动生成，基于公开新闻源聚合筛选。<br>
        ⚠️ 内容仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。
    </div>
</div>

<!-- 底部 -->
<div style="text-align:center; padding:20px; color:#999; font-size:11px;">
    Generated by MarketNews Digest · {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC<br>
    若有问题请联系发件人
</div>

</body>
</html>"""

    return html


if __name__ == "__main__":
    # 测试用
    logging.basicConfig(level=logging.DEBUG)
    mock_result = {
        "date": "2026-06-09",
        "market_summary": {
            "A股": "政策利好推动大盘上涨",
            "美股": "美联储鸽派表态，科技股大涨",
            "港股": "跟随A股回暖",
        },
        "top10": [
            {
                "rank": 1,
                "title": "美联储维持利率不变，暗示年内降息三次",
                "summary": "美联储6月FOMC会议决定维持基准利率不变，最新点阵图显示年内可能降息三次",
                "source": "Reuters",
                "url": "https://example.com/1",
                "impact_level": "高",
                "impact_market": ["A股", "美股", "港股"],
                "impact_reason": "全球流动性拐点信号",
            },
            {
                "rank": 2,
                "title": "中国5月CPI同比上涨0.8%，PPI降幅收窄",
                "summary": "国家统计局公布5月通胀数据，CPI温和回升略超预期",
                "source": "国家统计局",
                "url": "https://example.com/2",
                "impact_level": "高",
                "impact_market": ["A股", "港股"],
                "impact_reason": "影响货币政策预期",
            },
        ],
    }
    send_email(mock_result)
