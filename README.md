# 📊 每日资本市场热点新闻 TOP10 推送

每天上午 11:00 自动收集过去 24 小时 **A股 + 美股 + 港股 + 黄金** 最值得关注的热点新闻，AI 筛选排序后通过邮件推送。

## ✨ 特性

- 🌍 **全球覆盖**：A股、美股、港股、黄金四大市场
- 🤖 **AI 筛选**：DeepSeek API 按资本市场影响力自动排序 TOP10
- 📧 **邮件推送**：精美的 HTML 邮件，支持移动端阅读
- ⏰ **定时运行**：GitHub Actions 每天北京时间 11:00 自动触发
- 💰 **零成本运行**：使用免费 API 额度，无需服务器

## 🚀 快速开始

### 1. Fork 此仓库

点击右上角 Fork 按钮，复制到你的 GitHub 账户。

### 2. 获取 API Key

#### 搜索 API（二选一，推荐 NewsAPI）

- **NewsAPI**（推荐）：访问 https://newsapi.org/register 注册，免费 100 次/天
- **Bing Search API**：Azure 门户创建 Bing Search 资源，免费 1000 次/月

#### DeepSeek API（必填）

访问 https://platform.deepseek.com/ 注册并获取 API Key。
新用户赠送 500 万 tokens，默认使用 `deepseek-chat` 模型，也可改为 `deepseek-reasoner`。

#### QQ 邮箱授权码（必填）

1. 登录 QQ 邮箱 → 设置 → 账户
2. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
3. 开启 **SMTP 服务**，生成授权码
4. 复制授权码（一串字母，不是QQ密码）

### 3. 配置 GitHub Secrets

在 Fork 后的仓库中：**Settings → Secrets and variables → Actions → New repository secret**

添加以下 Secrets：

| Secret 名称 | 说明 | 必填 |
|-------------|------|:---:|
| `NEWSAPI_KEY` | NewsAPI 的 API Key | 二选一 |
| `BING_SEARCH_API_KEY` | Bing Search API Key | 二选一 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | ✅ |
| `QQ_EMAIL_SENDER` | 发件人 QQ 邮箱地址 | ✅ |
| `QQ_EMAIL_PASSWORD` | QQ 邮箱 SMTP 授权码 | ✅ |
| `QQ_EMAIL_RECEIVER` | 收件人邮箱地址 | ✅ |

![Secrets 示例](https://docs.github.com/assets/cb-28273/mw-1440/images/help/repository/repo-secrets-settings.webp)

### 4. 手动触发测试

1. 进入仓库的 **Actions** 标签页
2. 选择 **Daily Market News TOP10** workflow
3. 点击 **Run workflow** → **Run workflow**
4. 等待完成，查看运行日志和邮箱

### 5. （可选）本地运行

```bash
# 1. 克隆仓库
git clone <your-fork-url>
cd firstcc

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 .env 文件
cp .env.example .env
# 编辑 .env，填入你的 API Key 和邮箱配置

# 4. 运行
python main.py           # 正常模式
python main.py --dry-run # 预览模式，不发送邮件
```

## 📬 邮件效果预览

邮件包含：
- 📋 **市场概况**：三大市场一句话总结
- 🔥 **TOP10 新闻卡片**：排名、标题、摘要、来源、影响等级、影响市场
- 🤖 **免责声明**：AI 生成提示

每条新闻卡片标注影响等级：
- 🔴 **高影响**：宏观政策、央行决策、重大地缘事件
- 🟠 **中等影响**：行业动态、经济数据
- 🔵 **低影响**：个股新闻、公司公告

## ⚙️ 自定义配置

可通过环境变量调整行为：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DEEPSEEK_MODEL` | `deepseek-chat` | AI 模型，可选 `deepseek-reasoner` |
| `LOG_LEVEL` | `INFO` | 日志级别：DEBUG/INFO/WARNING/ERROR |

编辑 `.github/workflows/daily-news.yml` 中的 `cron` 可修改推送时间。

## 📊 费用估算

| 项目 | 用量 | 月成本 |
|------|------|:-----:|
| NewsAPI | ~240 次/月（8次/天） | 免费 |
| DeepSeek Chat | ~150K tokens/月 | ≈¥0.1 |
| GitHub Actions | ~150 分钟/月 | 免费* |
| QQ 邮箱 SMTP | 30 封/月 | 免费 |

> *公开仓库无限分钟；私有仓库每月 2000 分钟免费额度。

## ⚠️ 免责声明

本工具由 AI 自动生成新闻摘要和排序，内容仅供参考，**不构成任何投资建议**。投资有风险，入市需谨慎。请以官方信息为准。

## 📝 License

MIT
