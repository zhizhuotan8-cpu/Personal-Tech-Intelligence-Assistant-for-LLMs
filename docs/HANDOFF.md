# 工作交接：大模型应用工程情报助手

更新时间：2026-11-10（Asia/Shanghai）。本文件用于新对话恢复工作；实现以仓库当前代码为准。

## 最新：阅读质量验收与正文复核（2026-11-10）

已核对 19:34 五条简报：发现 Haystack 归档组件前提遗漏、Langfuse 缺少 N+1 具体方法、Gemini 摘要遗漏 httpx2 变更。详见 `docs/READING_REVIEW-20261110.md`。预览现在初选最多五篇后默认补取正文并再调用模型复核；仅目录简介且正文不可用的实践文章不进入最终结果。最近二十个唯一推荐作为不可信上下文辅助判断同主题信息增量，历史链接不能当本次可引用来源。不是确定性语义去重。

同输入复核报告 `output/quality-review/report.html` 从五条减为四条，归档 Haystack 未入选，其他条目方法更具体。真实运行 `output/preview/20261110-194157-547273/` 捕获空正文 finish_reason=length、completion_tokens=5000；现预览按最多二十条分批筛选，任何批失败整体报错。新完整运行 `output/preview/20261110-194447-434702/report.html`：22 源、80 候选、5 条均有正文摘录，130 秒；跳过二十条历史推荐，与 19:34 五条无重复链接。本轮均为 Haystack，来源多样性仍有限。

全量 73 项测试、54 子场景通过。新版默认额外增加一次模型请求及最多五个网页请求；`--full-evidence` 现在表示初选阶段也尝试正文。尚未创建计划任务或发送通知。下文旧的“默认仅摘要、正文完全可选”说明以本节与最新快速开始为准。

## 最新批次：简报质量与跨次推荐（2026-11-10）

后续排查更新：客户端此前没有处理 HTTP 成功但正文为空，现已增加有界重试和安全结束原因/token 诊断；历史上游空返回原因未直接复现，不能断言是推理额度耗尽。见 `docs/AI_EMPTY_RESPONSE_DIAGNOSIS.md`。全量 68 项测试、54 子场景通过，最后正文块类型过滤调整后相关 13 项及 7 子场景再通过。

真实验收现已完成：`output/preview/20261110-193317-424986/report.html` 与 `output/preview/20261110-193447-969299/report.html` 连续成功，均为 22 源、5 条。分别跳过 12、16 条历史推荐；两份仅重复 Gemini v3.0.0 兼容性风险并标注复查。第二份耗时 74.5 秒。两次实际运行未触发空正文重试，因此重试恢复由回归测试验证，不等同于捕获并修复了上游根因。跨链接同主题仍可能重复。

已增加成功真实预览报告的 URL 推荐历史过滤、重复兼容性风险复查标签、来源/目录日期及原始日期未知提示，并修复成功状态残留无事件 message。推荐记录不代表已读；具体边界及原文审阅见 `docs/QUALITY_REVIEW.md`。

验证：62 项测试、54 个子场景全量通过；最后日期标签调整后预览相关 9 项再通过。两次真实联网采集均为 22 源成功，但第一次 AI 筛选失败，第二次 AI 简报返回空响应（`output/preview/20261110-192441-350400/`）；尚未完成连续两份成功简报的真实去重验收，不宣称模型链路稳定。下一步优先排查模型空响应并完成该验收。功能提交 `34e430cc`，推送状态需核对。

## 1. 新对话先做什么

1. 读取本文；启动与使用见 `docs/QUICKSTART-LOCAL.md`，交付顺序见 `docs/DELIVERY_PLAN.md`。需要功能演进细节时再读 `docs/ai-engineering-radar.md`，其中早期段落有历史状态，应结合后续记录和代码判断。
2. 检查 `git status --short`、当前分支、最新提交，保留下面列出的既有用户改动。核实远程状态；存在未推送提交时再重试。
3. 用户最新开发要求“先接入第一批实践渠道”已完成并经过真实运行验证。当前请求仅为生成交接文档；下一阶段依据用户新要求执行，不自行重启全部长期规划。

## 2. 用户目标和工作偏好

用户是大模型应用开发工程师，希望减少追踪技术更新的时间。项目基于 TrendRadar，已从综合热点改成个人工程情报助手。

- Agent 40%、RAG 30%、模型/API 20%、部署 10% 为选稿倾向，不是每日硬配额。
- 关注 LangChain、LangGraph、Deep Agents；国内模型包含 Qwen、DeepSeek、GLM、Kimi、豆包、MiniMax、ERNIE、混元；海外包含 GPT、Claude、Gemini、Grok。
- 最近明确偏好：尽快看到能运行的产品、更多实用信息；优先教程、排障、评测、可复现代码和有细节的生产实践，降低一般产品公告、营销和零碎 SDK 更新。
- 每份最多五条；保留重大兼容性、弃用和下线风险；提供变化、工程影响、验证建议与原始出处。
- 已持续授权代码改动验证后 commit + push 至指定 GitHub 仓库，无需重复询问。提交说明使用简短中文，说明本阶段做了什么。
- 不要再连续只做底层增强却不交付可查看结果。沿用 Python + HTML，暂缓多 Agent、向量数据库、周报、知识库和云部署。

## 3. 环境、Git 与待推送状态

- 工作区：`F:\AgentProject\LLM_last\TrendRadar`，PowerShell，Python：`.venv\Scripts\python.exe`。
- 用户仓库：https://github.com/zhizhuotan8-cpu/Personal-Tech-Intelligence-Assistant-for-LLMs
- 当前分支：`codex/personal-tech-intelligence`，跟踪 `origin/main`；推送使用 `git push origin HEAD:main`，不要依赖同名分支默认规则。
- `upstream` 为原 TrendRadar；本地 `master` 保留上游历史，保持原样。
- 本文更新前功能 HEAD：`f4e22c9e`（接入三类官方实践目录，保留日期并均衡来源）。本文自身提交会改变 HEAD。
- 本次交接首次提交 `755bbf3a` 已推送成功，远程从 `9a756dc9` 更新至该提交；本文补充推送状态后还会产生后续提交，开始工作时重新核对。
- 此前未上传的功能提交 `41f3ef98`（工程实践来源与历史阅读标注）、`f4e22c9e`（三类官方实践目录）已随 `755bbf3a` 一起成功上传。
- GitHub 间歇性连接重置/443 超时；此前有重试成功，也有连续两次失败。`git -c http.version=HTTP/1.1 push origin HEAD:main` 曾成功，功能提交曾连续失败，本次交接推送已恢复成功。不要报告未确认的推送成功，不关闭 TLS 校验或强制覆盖远程。
- 用户仓库初始快照与上游历史分离：上游历史 README 中 Slack 示例触发 Push Protection，曾通过无父提交快照发布；当前示例已改成 example.com，保留 GPL-3.0。不要重新混入被拒绝的上游历史。

必须保留的既有本地改动（本轮功能开始前即存在）：

```text
 M index.html
?? .python-version
```

仅暂存本轮实际完成的文件；避免 `git add .`、重置或清理这些文件。`output/` 是本地产物且被忽略，交接中的报告不会随 Git 上传。

## 4. 现在如何运行并查看

最方便入口：双击 `start-preview.bat`，默认真实预览近七天动态及实践阅读，完成后自动打开 HTML。离线看页面用 `start-demo.bat`，显著标为样本演示。

正式 CLI：

```powershell
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -m trendradar --preview --days 7 --no-open
# 可选正文摘录，耗时更多：
.\.venv\Scripts\python.exe -m trendradar --preview --days 7 --full-evidence --no-open
.\.venv\Scripts\python.exe -m trendradar --demo --no-open
```

- Windows 用户环境变量中已配置 `AI_API_KEY`、`AI_MODEL`、`AI_API_BASE`。当前进程可能未继承；`trendradar/preview.py` 的 `load_user_environment()` 会在进程变量缺失时补读用户变量。无需让用户重发密钥。普通正式日报入口不包含这项自动补读。
- 真实模型调用已有用户授权，会产生正常 API 用量；不要输出密钥或把凭据落盘。配置文件默认模型名不能代表账号实际可用，按用户环境变量执行。
- 预览绕过调度，不发送通知，不使用正式日报分类数据库/一次执行记录；默认仅标题和摘要，`--full-evidence` 才额外抓正文。
- `output/preview/latest.html` 为最近一次运行页面，失败也会覆盖为失败页面；每次独立目录中有 `report.html`、`status.json`，真实运行还保存 `sources.json`。
- 预览固定 Agent、RAG、模型/API、部署四类标签，不再调用模型提取标签，避免多一次调用和截断失败。每次重新筛选，不是正式日报增量缓存行为。
- CLI 支持 `--days 1/3/7/14`，不指定时遵循配置；批处理入口显式使用 7。三个新增实践目录保留 `max_age_days: 0`，不被动态时间窗口排除。
- 普通 `python -m trendradar` 仍为正式日报入口，受 19:00–23:00 晚间窗口控制；调度配置不会安装定时任务。尚未创建 Windows 计划任务，尚未配置通知渠道，不自动发送消息。

## 5. 已实现能力与代码入口

| 位置 | 当前行为 |
|---|---|
| `trendradar/preview.py` | 手动真实预览、离线演示、工程卡片 HTML、用户环境变量、明确成功/无更新/失败状态，失败退出码非零 |
| `trendradar/__main__.py` | 预览 CLI；仅启用 RSS 时允许继续并跳过热榜采集 |
| `trendradar/ai/engineering.py` | events 字段校验、输入 URL 白名单校验、同链接/标题去重、最多五条，生成兼容旧报告的正文 |
| `trendradar/ai/analyzer.py` | 结构化简报、证据标签、RSS 摘要与可选正文输入；无效/空分析不再标成功 |
| `trendradar/ai/filter.py` | 分类无效响应返回失败以便重试；有效空数组代表无匹配 |
| `trendradar/storage/sqlite_mixin.py`、`ai/filter_pipeline.py` | 摘要从采集数据库贯通到分类和报告输入 |
| `trendradar/ai/evidence.py` | HTTPS 站点白名单、有限跳转、超时/体积/摘录限制、24 小时成功缓存、失败降级 |
| `trendradar/crawler/rss/catalogs.py` | 三个官方非 RSS 实践目录解析、站内链接去重、可见 time 日期、首次发现及目录变化快照 |
| `trendradar/crawler/rss/fetcher.py` | 已知目录 URL 走目录适配器，其他来源继续 RSS/Atom；正式日报和预览共用 |
| `config/ai_interests.txt`、`config/ai_engineering_prompt.txt` | 实用性优先、事实/推断/建议区分、旧教程作为实践阅读、禁止猜测版本及实验结果 |

结构化模式由 `ai_analysis.structured_events` 控制，通用模式保持兼容。预览页面按工程语义显示，正式通用报告部分标题尚未改。五条为程序上限；排序由模型决定；跨文章语义去重没有持久化实现。

## 6. 渠道现状：22 个配置来源

原有 17 个：Qwen 博客；DeepSeek V3、GLM 4.5、Kimi K2、MiniMax M1、混元 A13B 指定仓库提交；ERNIE Releases；火山引擎 Python SDK Releases；OpenAI 新闻；Claude/Gemini/Grok SDK Releases；LangChain/LangGraph/Deep Agents/LlamaIndex Releases；Hugging Face 博客。

已新增 5 个实践渠道（精确配置见 `rss.feeds`）：

1. LangChain：`https://www.langchain.com/blog/rss.xml`，每次最多 20 条。
2. Weaviate：`https://weaviate.io/blog/rss.xml`，每次最多 20 条。
3. Anthropic：`https://www.anthropic.com/engineering`，目录适配器，每次最多 12 条。
4. Haystack：`https://haystack.deepset.ai/tutorials`，目录适配器，每次最多 12 条。
5. Langfuse：`https://langfuse.com/guides/cookbook`，目录适配器，每次最多 12 条。

重要边界：

- LangChain RSS 的近期时间可能来自迁移/更新；核验曾发现原文为历史教程。实践页面统一标记“实践阅读，订阅时间不代表原始发布日期”。
- Anthropic 从目录可见 time 取日期；Haystack/Langfuse 缺失日期保留为空。首次发现不等于新发布。
- `output/catalogs/<URL哈希>.json` 保存 first_seen、last_seen、changed_at 和标题/简介签名；不是正文版本归档，也尚未依据它发送变更通知。
- 目录只读当前列表且按顺序截取，无翻页；结构变化导致零匹配时明确失败。预览候选按来源轮流取样后受 80 条上限约束。
- 原国内固定仓库不能完整发现厂商新模型；SDK 源不等于模型公告订阅。Hugging Face 含社区作者。尚未接入公众号、知乎等综合社区。
- LlamaIndex/Haystack 之前猜测的 RSS 返回 404，未接入这些地址；Haystack 现在走可靠目录。Qdrant RSS 排序不适合现有截取，未加入。

## 7. 证据处理与质量限制

- RSS 摘要约 500 字；目录简介标为非正文。正文通过可选抓取补充，每轮最多五个不同 URL，每页最多输入 6000 字符，按候选输入顺序获取。
- 正文只支持 `evidence.py` 中的官方站点白名单，HTML 提取 article/main 并排除脚本/导航等；动态或不兼容页面会降级。
- `output/evidence` 保存原始 URL、最终 URL、UTC 抓取时间、摘录、截断标记和响应哈希/失败原因，成功缓存 24 小时；不是完整 HTML 归档，尚无自动清理。
- 输入内容都视为不可信数据。来源链接能校验，事实本身尚无自动独立验证。
- 用户要求分析质量时，曾核对官方原文：主要发布事实有依据，但出现摘要截断遗漏重要破坏性变更、把局部 API 修复泛化、对旧行为和沙箱边界推断过度等问题。提示词已强化，不代表这些问题已根除。
- 实用内容比例已提高，仍偏官方博客/版本公告；国内内容、RAG 深度实践和部署经验覆盖不足。预览缺少跨次已读/新增去重，七天窗口容易重复推荐。
- `status.json` 成功时 message 仍可能保留“模型未选出…”的默认文本；页面有事件时不显示它。这是已知元数据小问题，判断结果优先看 status/events。

## 8. 验证记录与可查看产物

最新全量结果：60 项测试、54 个子场景通过。

```powershell
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
.\.venv\Scripts\python.exe -m pytest -q tests
```

虚拟环境已安装 pytest，但项目 dev 依赖尚未记录它；重建环境后如缺失可使用 `uv pip install --python .venv/Scripts/python.exe pytest`。沙箱临时目录曾限制 MCP 子进程测试；在获准的正常权限环境下全量通过。网络请求及 Git 写操作有时需要提升权限，遵循工具审批，不重复向用户索要已授权操作的许可。

关键真实运行（均未发送通知）：

- `output/preview/20261110-152123-125786/`：17 源，近七天 55 候选，生成 5 条，109.3 秒，本地入口首次完整验收。
- `output/preview/20261110-153517-081090/`：质量复核，17 源成功，5 条，65.6 秒；与上次 4 条重复，说明新颖性不足。
- `output/preview/20261110-184912-501205/`：新增 LangChain/Weaviate 后 18 源成功、1 失败，3 条实践+2 条兼容性更新，89.8 秒。
- 最新：`output/preview/20261110-190314-913341/report.html`。22 源全部成功，80 候选筛出 25 条，生成 5 条，90.5 秒；Anthropic 记忆工程进入结果，Haystack/Langfuse 参与筛选但未入选五条。对应日志 `output/preview/catalog-live.log`。

最新运行完成后还有证据标签的小修正，已有离线测试覆盖；不要宣称最终每一行代码都重新完整联网运行过。最新 `latest.html` 可能被后续演示/失败覆盖，核查独立目录确认真实结果。

## 9. 后续建议（待用户确定下一步）

先核对本地与远程 SHA；本次交接已成功上传此前积压的功能提交。随后优先让用户阅读第一批实践渠道的输出，再改善质量：补原始日期展示、同主题多来源引用、已读/新增状态、适用版本与获取条件；修复实际发现的事实推断问题。不要只增加来源数量或把一次模型成功视为质量稳定。

本地手动版已交付。Windows 定时任务、通知渠道、长期运行与清理规则尚待做；独立弃用告警、语义事件聚类、收藏反馈、周报和长期知识库也未实现。没有用户新要求时，不把这些长期事项一次性全部展开。
