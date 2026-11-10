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

成功真实预览中的已推荐链接默认跳过，兼容性风险可复查；最近二十篇推荐的标题与事实作为选稿参考，减少同主题不同链接的重复，这不是确定性语义去重。记录保存在本地 output/preview，清理后会丢失。正式日报仍使用原来的 `python -m trendradar`，本次不自动创建定时任务。

## 状态与处理

- **成功生成**：查看最多五条精选和原始链接。
- **本次无值得推荐的更新**：近期没有条目，或模型未选出合适内容。不会自动混入旧新闻或演示数据。
- **部分来源失败**：页面列出失败来源，本次简报覆盖可能不完整；检查网络后重试。
- **运行失败**：页面显示失败原因，命令返回非零状态。检查模型配置、余额/权限或网络，修复后重新运行；历史成功报告仍在各自目录。
- 浏览器没有弹出：手动打开 `output/preview/latest.html`。

首次运行耗时取决于 RSS 网络和模型速度。网页摘要及厂商原文未经独立核验，建议小规模验证后再应用。

新增实践目录：Anthropic Engineering、Haystack Tutorials、Langfuse Cookbook。它们的历史教程作为“实践阅读”参与筛选，不受 --days 动态窗口限制；未知原始发布日期不会填成今天。目录简介用于初选，入选后默认尝试正文复核。候选有总量上限，按来源轮流取样。
