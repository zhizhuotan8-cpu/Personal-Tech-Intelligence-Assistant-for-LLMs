# 工作交接：大模型应用工程情报助手

更新时间：2026-11-10（Asia/Shanghai）。本文为当前状态摘要，替代此前按时间追加的交接段落；具体实现以代码为准。

## 1. 恢复工作

1. 先读本文。启动与任务管理看 `docs/QUICKSTART-LOCAL.md`；交付阶段及验收记录看 `docs/DELIVERY_PLAN.md`。
2. 检查 `git status --short`、当前分支和本地/远程 SHA。保留下述用户既有改动，只提交本轮文件。
3. 用户本轮要求是更新交接文档。每日自动生成已交付并实际验收，后续开发依据用户新要求执行。

## 2. 当前交付状态

项目基于 TrendRadar，已改为面向个人的大模型应用工程情报助手，沿用 Python + HTML。

- 手动真实预览、离线演示、第一批实践渠道、跨次推荐记录、最终入选正文复核均已交付。
- Windows 当前用户任务 `LLMEngineeringRadar-Daily` 已安装，每天北京时间 **20:00**；任务 XML 固定 `+08:00`。
- 动作使用本仓库 `.venv/Scripts/pythonw.exe -u -m trendradar.daily` 的绝对路径，并设置绝对工作目录。后台运行，无需打开 Codex。
- 使用普通用户 `InteractiveToken`，不保存 Windows 密码；电脑须开机联网并保持当前用户登录，锁屏可。关机或注销时不能运行，错过时间由 Windows 在可运行时补跑，不保证立即补跑。
- 失败每隔 30 分钟重试，最多两次；单次任务上限 30 分钟。Windows 的 IgnoreNew 与应用 OS 文件锁共同限制并发。
- 每日入口按北京时间保存完成记录：成功或明确无更新后当天直接跳过，失败可重试；进程退出会释放锁，残留锁文件不阻塞。
- 未配置通知渠道，以上入口均不发送通知。普通 `python -m trendradar` 是独立的旧正式日报入口，仍受 19:00–23:00 时间窗口控制；它不是新 Windows 任务的执行命令。

本次交接核对：任务 Ready，LastTaskResult=0，应用状态 completed；下次执行时间为 **2026-11-11 20:00 北京时间**。这是 11 月 10 日的核对结果，下次工作应重新读取状态。

## 3. 用户目标与工作约定

用户希望减少追踪技术更新的时间，优先教程、排障、评测、可复现代码和有细节的生产实践，降低一般公告、营销和零碎 SDK 更新。

- Agent 40%、RAG 30%、模型/API 20%、部署 10% 是长期选稿倾向，不是每日硬配额。
- 关注 LangChain、LangGraph、Deep Agents，以及国内外主流模型。每份最多五条，保留重大兼容性、弃用和下线风险，说明事实、工程影响推断、验证建议及原始出处。
- 优先交付能查看和使用的结果。暂缓多 Agent、向量数据库、周报、长期知识库和云部署。
- 已持续授权改动验证后使用简短中文 commit，并 push 到指定用户仓库，无需重复确认。推送失败如实报告。
- Windows 用户环境变量已有 `AI_API_KEY`、`AI_MODEL`、`AI_API_BASE`。预览会在当前进程缺失时补读用户变量；无需让用户重发密钥。真实模型调用及正常 API 用量已有授权，凭据只留在环境中。

## 4. 日常入口与产物

| 入口 | 用途 |
|---|---|
| `open-latest-report.bat` | 阅读最近成功且有内容的真实报告 |
| `daily-task-status.bat` | 查询 Windows 任务、上次结果、下次时间和应用状态 |
| `run-daily-now.bat` | 触发每日任务或失败补跑；当天已完成时跳过 |
| `install-daily-task.bat` | 安装或更新匹配本项目动作的同名任务 |
| `uninstall-daily-task.bat` | 卸载匹配任务，保留报告和配置 |
| `start-preview.bat` | 主动重新分析近七天；不受每日完成记录限制，完成后打开页面 |
| `start-demo.bat` | 离线样本演示，明确标注非实时内容 |

任务管理脚本为 `scripts/daily-task.ps1`，操作前检查同名任务的解释器、参数和工作目录归属。移动项目或虚拟环境前先从原目录卸载，再在新目录安装。

CLI 示例：

```powershell
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -m trendradar.daily
.\.venv\Scripts\python.exe -m trendradar --preview --days 7 --no-open
# 初选阶段也补正文；最终入选复核已默认启用：
.\.venv\Scripts\python.exe -m trendradar --preview --days 7 --full-evidence --no-open
.\.venv\Scripts\python.exe -m trendradar --demo --no-open
```

- `output/preview/latest-success.html`：最近成功且有内容的报告，失败、演示、无更新均不会覆盖它；核对页面日期，可能不是当天内容。
- `output/preview/latest.html`：最近一次预览结果，失败也会覆盖为失败页。
- `output/preview/<时间>/report.html`、`status.json`、`sources.json`：独立报告、状态及真实采集记录。
- `output/daily/latest.json`：最近一次实际每日运行状态；同日完成后再触发，状态保持不变。
- `output/daily/runs/<北京时间日期>.json`：每日完成/失败记录；`output/daily/logs/`：实时脱敏日志。
- 每日运行后只清理超过 30 天的任务日志和 `output/evidence` 正文缓存。简报、采集记录、推荐历史及每日完成记录保留，磁盘占用会增长。
- `output/` 被 Git 忽略，报告不会随推送上传。

## 5. 实现入口及质量边界

| 位置 | 当前职责 |
|---|---|
| `trendradar/daily.py` | 每日完成记录、OS 锁、日志脱敏和有限清理 |
| `trendradar/preview.py` | 手动/演示流程、候选均衡取样、跨次链接过滤、近期主题参考、最终正文复核、HTML 与成功页保留 |
| `trendradar/ai/client.py` | LiteLLM 调用；空正文按配置有限重试，持续失败记录安全结束原因和 token 用量 |
| `trendradar/ai/analyzer.py` | 结构化分析、证据标签、正文摘录及近期推荐上下文 |
| `trendradar/ai/engineering.py` | 必填字段与本次输入 URL 校验、同链接/标题去重、最多五条 |
| `trendradar/ai/filter.py` | 分类解析，失败返回 None，有效无匹配返回空数组 |
| `trendradar/ai/evidence.py` | HTTPS 官方站点白名单、有限跳转/体积/超时、正文提取、24 小时成功缓存 |
| `trendradar/crawler/rss/catalogs.py`、`fetcher.py` | RSS/Atom 与官方非 RSS 实践目录采集 |
| `config/ai_interests.txt`、`ai_engineering_prompt.txt` | 实用性优先、维护状态与适用条件、事实/推断/建议区分 |

当前有 22 个配置来源，精确列表见 `config/config.yaml` 的 `rss.feeds`。新增五个实践来源为 LangChain、Weaviate、Anthropic Engineering、Haystack Tutorials、Langfuse Cookbook；后三个走目录适配器，保留历史实践阅读，不受动态天数窗口排除。

预览流程与限制：

1. 采集后按来源轮流取样，候选默认上限 80 条；筛选拆为每批最多 20 条，保留原 ID，任一批失败则整轮失败。
2. 初选使用标题和摘要，最多五篇入选后默认补正文，并额外调用一次模型复核。仅目录简介且正文不可用的实践文章从最终结果剔除；有信息的 RSS 摘要仍允许降级。
3. 成功真实报告中的已推荐 URL 默认跳过；标题/摘要含 breaking、弃用、下线等风险信号时仍可复查。只记录“已推荐”，不代表用户已读；同链接正文变化尚未自动检测。
4. 最近二十个唯一推荐的标题与 facts 作为不可信上下文辅助判断不同链接下的主题增量，历史链接不能作为本次可引用来源。这是模型辅助，不能保证语义去重；同一期来源可能集中。
5. 实践文章不把订阅时间当发布日期：页面区分来源/目录日期及原始日期未核实。Anthropic 目录可见 time 有日期，Haystack/Langfuse 缺失日期保持未知。
6. 每次正文获取最多五个 URL，每页最多输入 6000 字符，摘录可能截断；`--full-evidence` 会在初选阶段再增加最多五个 URL 获取。正文缓存不是完整网页归档，事实没有自动独立核验。
7. 原国内固定仓库无法完整发现新模型，SDK 源不等于模型公告；国内内容、部署经验覆盖仍有限。目录只读当前列表，不翻页；零匹配明确失败。
8. 预览不读写旧正式日报的分类数据库和一次执行记录；每日包装层有独立防重复记录。手动预览可以重新调用模型。

## 6. 已完成验收

最新全量：**80 项测试、54 个子场景通过**。

```powershell
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
.\.venv\Scripts\python.exe -m pytest -q tests
```

虚拟环境已有 pytest，但尚未记录在 dev 依赖；重建缺失时可运行 `uv pip install --python .venv/Scripts/python.exe pytest`。沙箱曾限制临时目录及 MCP 子进程握手，获准的正常权限环境全量通过；网络和 Git 写操作遵循工具审批。

关键可查看结果（均未发送通知）：

- `output/quality-review/report.html`：对 19:34 原五篇做同输入正文复核，最终四条；归档 Haystack 教程未入选，Gemini 补充 httpx2、Langfuse 提炼 N+1 方法。它是历史对比，不计入成功预览推荐历史。
- `output/preview/20261110-194447-434702/report.html`：22 源成功、80 候选、5 条均有正文，130 秒；五篇均来自 Haystack，说明来源多样性仍有限。
- **最新真实任务报告**：`output/preview/20261110-200413-394015/report.html`。2026-11-10 20:04:13 启动、20:07:00 完成，22 源成功、4 条、167.6 秒。任务日志 `output/daily/logs/20261110-200413-384650.log`；Windows LastTaskResult=0。
- 2026-11-10 20:07:34 再次通过 Windows 任务触发：返回 0；日志和报告数量未增加、完成记录哈希不变，未进入模型流程。`latest-success.html` 已核对与本次成功报告一致。
- 本轮测试覆盖同日/跨日、失败重试、活锁和残留文件、异常日志脱敏、清理边界，以及失败/演示/无更新保留成功页。

空响应排查结论：确已捕获 finish_reason=length、completion_tokens=5000 的空正文；单批 80 条筛选已拆小。首次每日任务正文复核仍出现一次该情况，客户端有限重试后成功恢复，已真实验证恢复路径。不能保证所有请求都不截断，也不能回溯断定历史所有空响应都是同一原因。

## 7. 下一步建议与未完成事项

下一阶段优先观察接下来 2–3 次每日运行：核对 Windows 返回码、当天完成记录、报告日期、有用内容比例、重复主题及阅读耗时。当前只验收了一次真实任务和同日重复触发，尚未验证连续多日稳定性；不需要继续重复开发已经交付的定时任务或正文复核。

根据实际阅读问题再选一个小批次，例如减少同主题重复、补来源多样性或提高国内/部署实践覆盖。已读反馈、同主题多来源合并、独立弃用告警、通知渠道、收藏、周报和长期知识库均未交付，按用户需求逐项确定。当前请求只更新文档，不新增后台监控或其他功能。

按需阅读：

- 排查模型失败：`docs/AI_EMPTY_RESPONSE_DIAGNOSIS.md`。
- 理解原五篇质量问题和正文复核：`docs/READING_REVIEW-20261110.md`。
- 理解推荐记录和日期边界的早期设计：`docs/QUALITY_REVIEW.md`，其中验证数字属于当时阶段。
- 追踪早期演进：`docs/ai-engineering-radar.md`，含历史状态，需结合后续记录和代码判断。

## 8. Git 与保留项

- 工作区：`F:\AgentProject\LLM_last\TrendRadar`；分支 `codex/personal-tech-intelligence`，跟踪 `origin/main`。
- 用户仓库：https://github.com/zhizhuotan8-cpu/Personal-Tech-Intelligence-Assistant-for-LLMs 。推送使用 `git push origin HEAD:main`。
- 本次文档更新前功能 HEAD：`78e4f3b0`（每日自动简报），已成功推送；本地 origin/main 同 SHA。前序质量提交 `87d1972d`、空正文修复 `3eb3a496` 均已上传，没有此前积压的功能提交。本次文档提交会改变 HEAD，下次重新核对。
- GitHub 曾出现连接重置及 443 超时，`git -c http.version=HTTP/1.1 push origin HEAD:main` 曾恢复成功；以实际结果为准，保留 TLS 校验，不强推。
- `upstream` 为原 TrendRadar；本地 `master` 保留上游历史。用户仓库曾因上游 README 的 Slack 示例触发 Push Protection，已用无父提交快照发布；保留 GPL-3.0，不重新混入被拒绝的上游历史。

必须保留的既有用户改动：

```text
 M index.html
?? .python-version
```

仅暂存本轮实际修改的文件，避免 `git add .`、重置或清理上述改动。
