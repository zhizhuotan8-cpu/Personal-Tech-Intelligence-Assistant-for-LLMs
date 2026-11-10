# 工作交接：大模型应用工程情报助手

更新时间：2026-11-10（Asia/Shanghai）。本文用于在新的 Codex 对话中恢复上下文。

## 1. 用户目标与已确认偏好

用户是大模型应用开发工程师，希望基于 TrendRadar 减少追踪技术更新的时间，把综合热点工具改为个人行业情报助手。

- 国内模型：通义千问/Qwen、DeepSeek、智谱/GLM、Kimi、豆包、MiniMax、文心/ERNIE、混元等，可扩充。
- 海外模型：GPT、Claude（用户曾写 cluade）、Gemini、Grok。
- 核心框架：LangChain、LangGraph、Deep Agents（用户写 deepagent，当前对应 langchain-ai/deepagents）。
- 内容倾向：Agent 40%、RAG 30%、模型/API 20%、部署 10%。这是选稿偏好，不是严格每日配额。
- 每日日报精选最多 5 条，分为重点更新和工程实践；解释变化、工程影响、验证建议，附原始出处。
- 降低融资、财报、人事、营销、泛科技、重复转载、缺少实验条件的跑分宣传的优先级。
- 重点关注模型/API 弃用、下线与框架破坏性变更。
- 用户已要求：代码修改后提交到指定 GitHub 仓库。后续相关改动继续 commit + push，不需要重复询问是否连接仓库。

原始项目说明位于 `C:\Users\猿王\Desktop\项目说明.txt`，已阅读，仅作为项目背景；仓库实现才是当前行为依据。

## 2. 工作目录、Git 与发布状态

- 工作目录：`F:\AgentProject\LLM_last\TrendRadar`
- Shell：PowerShell；Python 虚拟环境：`.venv\Scripts\python.exe`。
- 用户仓库：https://github.com/zhizhuotan8-cpu/Personal-Tech-Intelligence-Assistant-for-LLMs
- `origin`：上述用户仓库；`upstream`：https://github.com/sansan0/TrendRadar.git
- 当前本地分支：`codex/personal-tech-intelligence`，跟踪 `origin/main`。
- 交接文档创建前，已推送功能提交：`a2235ce09c6e631feb15eb779a8fa8263874f406`。
- 原本地 `master` 仍保留上游历史及首次功能提交 `9d479d14`，不应强制覆盖或删除。
- 后续推送可用 `git push origin HEAD:main`。本地分支与远程分支名称不同，不要假定无参数 `git push` 一定成功。

用户仓库最初为空。第一次试图连同上游历史推送，被 GitHub Push Protection 拒绝：上游 README 历史中的 Slack Webhook 示例触发密钥检测。已将当前中英文 README 的示例 URL 替换为 `https://example.com/slack-webhook`，通过 `git commit-tree` 创建无父提交的独立项目快照，再推送到 `main`，已确认远程 SHA 与本地一致。没有绕过密钥保护，也没有删除原本地历史。仓库保留原 GPL-3.0 LICENSE。

### 必须保留的现有本地改动

在本轮交接文档创建前，`git status --short` 为：

```text
 M index.html
?? .python-version
```

这两项在本次功能改造前就存在，来源未核实，未提交、未覆盖。不要使用 `git add .`、`git reset --hard` 或清理命令把它们混入提交或丢弃。已有输出数据库和 HTML 也是本地运行产物。

## 3. 第一版实际完成的内容

| 文件 | 改动 |
|---|---|
| `config/config.yaml` | 停止综合热榜采集；17 个行业 RSS/Atom；`filter.method: ai`；日报模式；分析包含 RSS；最多分析 80 条；新鲜度 3 天；AI 简报优先显示 |
| `config/ai_interests.txt` | 四类工程兴趣、模型与框架名单、标题筛选与排除规则 |
| `config/ai_engineering_prompt.txt` | 新增技术简报提示词；最多 5 个事件、工程影响、原文出处、事实/建议区分、标题证据限制 |
| `config/frequency_words.txt` | Agent、RAG、模型/API、部署的宽松关键词备用规则 |
| `config/timeline.yaml` | 新增 `ai_engineering_daily` 预设；全天采集，19:00–23:00 窗口首次执行时分析/推送，启用 once |
| `trendradar/ai/analyzer.py` | `_prepare_news_content` 为 RSS 条目传递原始 URL，供模型引用 |
| `tests/test_engineering_sources.py` | 原文链接传递、无链接不编造、数量限制、禁用 RSS 的离线测试 |
| `docs/ai-engineering-radar.md` | 使用说明、来源覆盖、运行方式与边界 |
| `.gitignore` | 忽略虚拟环境、Python 缓存、本地 `.env` 与 `output/`；已经跟踪的旧输出文件仍在 Git 中 |
| `README.md`、`README-EN.md` | Webhook 示例换成无敏感信息的占位 URL |

### 提示词与程序约束的区别

- 40/30/20/10 目前只写在兴趣和分析提示词中，没有程序级配额。
- 最多 5 条是模型输出要求，尚无结构化事件列表和程序级条数校验。
- RSS 原始列表仍保留，可多于 5 条。
- 同事件合并依赖模型提示词，尚未实现持久化事件聚类。
- 分析输入只有标题、来源、时间与 URL；没有正文抓取，也没有让模型访问链接。
- `signals` 是日报中的兼容性/弃用提醒栏目，不是独立实时告警。
- 沿用原分析结果字段：`core_trends`、`sentiment_controversy`、`signals`、`rss_insights`、`outlook_strategy`、`standalone_summaries`。现有 HTML 和推送部分标题仍是通用舆情用语。

## 4. 信息源现状

2026-11-10 已联网核验配置中的 17 个地址均返回 HTTP 200，且 feedparser 能解析到条目。精确 URL 位于 `config/config.yaml` 的 `rss.feeds`。这只是当时的连通性和解析验证，不保证持续更新或完整覆盖。

- Qwen：官方博客。
- DeepSeek V3、GLM 4.5、Kimi K2、MiniMax M1、混元 A13B：对应官方仓库 main 提交 Atom。它们是固定项目补充源，不能自动发现后继新模型和新仓库。
- ERNIE：官方仓库 Releases。
- 豆包生态：火山引擎 Python SDK Releases；这是综合云服务 SDK，需要过滤无关更新。
- GPT 等：OpenAI 官方新闻 RSS。
- Claude、Gemini、Grok：各自官方 Python SDK Releases，不能等同于完整模型公告订阅。
- LangChain、LangGraph、Deep Agents、LlamaIndex：官方 Releases。
- Hugging Face：官方站点博客，包含社区作者，不代表所有文章经独立验证。

曾检查 LangChain 博客 `/rss/`，虽 HTTP 200 但无可解析条目，未接入。若恢复此类来源，必须验证内容而非只看状态码。

## 5. 验证与运行条件

以下测试已通过，共 14 项：

```powershell
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_engineering_sources.py'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_ai_analysis_response.py'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_rss_total_count.py'
```

另已完成配置加载、17 个 feed 读取、提示词加载，以及 12/19/22/23 点的调度边界检查。新改动范围内的 `git diff --check` 通过。全仓检查会报告原有 `index.html` 尾随空白，该文件尚未处理。

未调用付费模型、未发送通知、未完成真实全链路简报质量验证。此前配置加载输出“未配置任何通知渠道”；不要假定用户已配置通知或定时启动。

运行需要用户实际可用的模型和密钥，通过环境变量配置：

```powershell
$env:AI_API_KEY = '由用户在本地配置，不写进文档或提交'
$env:AI_MODEL = '提供商/实际可用的模型名'
# 如需兼容接口，再设置 AI_API_BASE。
.\.venv\Scripts\python.exe -m trendradar
```

订阅的模型厂商与执行筛选/简报的模型是两回事。当前配置仍保留原先的 `deepseek/deepseek-v4-flash` 默认名称，尚未验证该名称或用户账号可用性；不要据此承诺可以直接调用。

`schedule.enabled: true` 只控制每次启动的行为，不会创建常驻任务。必须另有 Docker cron、GitHub Actions 或 Windows 任务计划定时启动，至少覆盖北京时间晚间窗口。窗口外一般只采集，筛选等调用的实际时机需要结合主流程核实。手动预览简报时，可使用临时配置关闭 schedule 和 notification，避免误发。跨运行 once 去重依赖保留存储数据。

环境中普通沙箱网络请求曾出现 ProxyError，提升权限后的只读网络核验成功。写 `.git/config` 和索引需要提升权限；使用已授权的 Git 操作即可，不要反复要求用户确认。不得输出环境中的密钥。

## 6. 建议后续顺序（尚未实现）

1. 先用真实可用的 AI 配置完成一次安全预览，核验有效条数、事实与建议区分、原始链接和主题分布；处理空内容和模型失败。
2. 改善来源覆盖：补国内外厂商公告、Changelog、API 弃用页；避免固定旧模型仓库成为唯一入口。没有 RSS 的页面增加适配器或快照差分。
3. 增加正文获取、清洗、证据保存和来源时间/版本信息。抓取失败应明确降级为标题证据。
4. 将日报改为结构化事件，程序执行事件去重、排序和五条上限；为兼容性与弃用建立独立告警逻辑。
5. 将报告标题改成工程语义，同时保持通用模式兼容；不要仅改提示词就宣称前端已改。
6. 增加收藏/忽略反馈，每周专题，以及含适用版本、最后核验时间的长期知识库。

不必立即引入复杂多 Agent 或向量数据库。先让高质量采集—筛选—简报—反馈闭环可用。以有用内容占比、重复率、阅读时间和重要更新漏报率衡量，而非采集数量。

## 7. 新上下文开始时

先读取本文和 `docs/ai-engineering-radar.md`，然后检查 `git status`、当前分支与最新提交；本文中的提交号是交接文档提交前的功能基线，不要把它当作永久 HEAD。按用户下一条需求继续，尚未获得“立即做完所有后续阶段”的指令。

修改前核实实现，不把上面的建议当作现成功能。保留已有工作区改动；仅暂存自己完成的文件；做必要检查后提交并推送 `origin` 的 `main`，汇报提交链接与真实验证范围。
