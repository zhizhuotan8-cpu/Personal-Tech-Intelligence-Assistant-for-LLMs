# 本地快速开始

## 立即查看

在项目目录双击 `start-preview.bat`（默认预览近七天，页面会标明时间范围）。它会使用已配置的 AI 模型，采集来源、筛选近期内容并自动打开工程简报。运行会产生正常模型 API 用量；不会发送通知，不受晚间日报时间限制。控制台会显示进度，完成后按任意键关闭。

只想先看页面：双击 `start-demo.bat`。演示离线可用，页面明确标注样本日期，内容不是实时情报。

如提示缺少 Python 环境，在项目目录运行 `uv sync`，再双击启动。当前电脑已有 `.venv` 可直接使用。

## 配置与结果

使用现有 Windows 用户环境变量 `AI_API_KEY`、`AI_MODEL`，兼容接口可加 `AI_API_BASE`。预览入口优先使用当前进程变量，缺失时自动读取用户变量，无需把密钥复制到项目文件。

- 最近一次运行结果：`output/preview/latest.html`，失败时也会更新为失败页面。
- 每次独立报告：`output/preview/<运行时间>/report.html`。
- 对应状态：同目录 `status.json`；真实采集记录为 `sources.json`。
- 演示和真实运行均保留独立历史，页面显示模式、生成时间和运行结果。

命令行方式：

```powershell
.\.venv\Scripts\python.exe -m trendradar --preview
.\.venv\Scripts\python.exe -m trendradar --demo
# 不自动打开浏览器
.\.venv\Scripts\python.exe -m trendradar --preview --no-open
# 可选：扩大到近七天，页面会明确标注范围
.\.venv\Scripts\python.exe -m trendradar --preview --days 7
# 可选：初选时也增加原文摘录，运行时间更长
.\.venv\Scripts\python.exe -m trendradar --preview --full-evidence
```

预览使用固定的 Agent、RAG、模型/API、部署标签及完整兴趣说明。初选使用标题和 RSS 摘要；默认再对最终入选的最多五篇补取正文并调用模型复核维护状态、具体方法及适用条件，因此比仅摘要版多一次模型调用和有限网页请求。正文不可用时，有信息的 RSS 摘要仍可降级使用；只有目录简介的实践文章不进入最终结果。每次不一定有五条。

成功真实预览中的已推荐链接默认跳过，兼容性风险可复查；最近二十篇推荐的标题与事实作为选稿参考，减少同主题不同链接的重复，这不是确定性语义去重。记录保存在本地 output/preview，手动清理后会丢失。普通 `python -m trendradar` 仍是原有正式日报入口；下面的本地每日任务使用隔离预览流程，不发送通知。

## 每天自动生成

当前开发电脑已安装 Windows 任务 `LLMEngineeringRadar-Daily`，每天北京时间 **20:00** 自动生成近七天动态及实践简报；不需要打开 Codex。其他电脑需先运行安装入口。电脑需开机联网，并保持当前用户登录，锁屏可以；不保存 Windows 密码。关机或注销期间不能执行，错过时间后由 Windows 在可运行时补跑，不保证立即补跑。

- 阅读入口：双击 `open-latest-report.bat`，打开最近一份成功且有内容的真实报告；页面会显示生成日期。失败、演示和本次无更新都不会覆盖它。
- 任务状态：双击 `daily-task-status.bat`，查看任务状态、上次结果、下次执行时间及应用状态。
- 手动补跑或失败重试：双击 `run-daily-now.bat`。当天已经成功完成（包括明确无更新）时会直接跳过，不重复调用模型；失败可以重试。
- 重新安装：双击 `install-daily-task.bat`，核对并更新当前项目的同名任务。移动项目或虚拟环境前，先从原目录卸载再在新目录安装。
- 停止自动生成：双击 `uninstall-daily-task.bat`，只删除本项目匹配的计划任务，保留报告与配置。

任务使用 `.venv\Scripts\pythonw.exe` 的绝对路径和项目工作目录，在后台运行。重复实例由 Windows 与应用文件锁共同拦截；崩溃后系统释放锁，文件仍存在不影响重试。失败每隔 30 分钟自动重试，最多两次；单次任务上限 30 分钟。

日志在 `output/daily/logs/`；最近状态在 `output/daily/latest.json`，每日完成记录在 `output/daily/runs/`，日期统一为北京时间。当天无更新也算正常完成；可查看 `output/preview/latest.html` 确认本次状态。要主动重新分析当天内容，仍可用 `start-preview.bat`，它是手动预览，不受每日任务完成记录限制。

每日运行后只清理超过 30 天的任务日志及 `output/evidence` 正文缓存，不清理简报、采集记录、推荐历史或每日完成记录。最近成功报告为 `output/preview/latest-success.html`；长期保留报告会逐步占用磁盘。

## 状态与处理

- **成功生成**：查看最多五条精选和原始链接。
- **本次无值得推荐的更新**：近期没有条目，或模型未选出合适内容。不会自动混入旧新闻或演示数据。
- **部分来源失败**：页面列出失败来源，本次简报覆盖可能不完整；检查网络后重试。
- **运行失败**：页面显示失败原因，命令返回非零状态。检查模型配置、余额/权限或网络，修复后重新运行；历史成功报告仍在各自目录。
- 浏览器没有弹出：手动打开 `output/preview/latest.html`。

首次运行耗时取决于 RSS 网络和模型速度。网页摘要及厂商原文未经独立核验，建议小规模验证后再应用。

新增实践目录：Anthropic Engineering、Haystack Tutorials、Langfuse Cookbook。它们的历史教程作为“实践阅读”参与筛选，不受 --days 动态窗口限制；未知原始发布日期不会填成今天。目录简介用于初选，入选后默认尝试正文复核。候选有总量上限，按来源轮流取样。
