# 工作交接：个人大模型应用工程情报助手

更新：2026-11-10（Asia/Shanghai）。当前代码已移除无关上游功能，历史实现以 Git 记录为准。

## 目标与范围

面向个人大模型应用开发工程师，关注 Agent、RAG、模型/API、部署。优先教程、排障、评测、可复现代码和有细节的工程实践。Agent 40%、RAG 30%、模型/API 20%、部署 10% 是长期倾向，不是每日硬配额；每份最多五条，区分事实、工程影响推断与验证建议，并保留原文出处。

保留本地 Python + HTML、24 个 RSS/Atom/实践目录来源、AI 兴趣筛选、最终正文复核、推荐历史、Windows 每日任务和离线演示。移除综合热榜、舆情统计、多渠道通知、翻译、MCP、云存储、数据库分类缓存、旧时段调度、Docker、旧 GitHub 采集与推广/配置编辑站点资源。

## 当前入口

安装和配置见 [README](../README.md)。`setup-windows.bat` 执行 `uv sync --frozen`，测试依赖已纳入 dev。

- 默认 `python -m trendradar` 或 `start-preview.bat`：近七天真实分析，完成后打开本地 HTML；手动运行可重复调用模型。
- `start-demo.bat`：明确标注的离线样本。
- `open-latest-report.bat`：最近成功且有内容的报告，失败或无更新不覆盖；注意页面日期。
- `python -m trendradar.daily` 或 `python -m trendradar --daily`：北京时间每日完成记录和 OS 文件锁。
- 安装、状态、触发、卸载 Windows 任务：相应 daily-task 批处理；任务名仍为 LLMEngineeringRadar-Daily。

既有 Windows 任务保持解释器绝对路径、工作目录、每天北京时间 20:00、普通用户 InteractiveToken，无需打开 Codex。电脑须开机联网且用户保持登录，锁屏可；关机或注销不运行，错过时 Windows 可补跑。失败每隔 30 分钟重试，最多两次；单次上限 30 分钟。未发送通知。

## 凭据与数据

Windows 用户变量已有 AI_API_KEY、AI_MODEL、AI_API_BASE，预览会在进程缺失时补读；不输出凭据、不写入仓库。真实模型调用及正常 API 用量已获授权。

保留现有 output/：preview 独立报告、status.json、sources.json 和推荐历史；daily 状态、完成记录和脱敏日志；evidence 正文摘录；catalogs 实践目录快照。仅清理超过 30 天的任务日志与正文缓存。历史数据库不再被新流程使用，本轮未删除用户数据。

## 核心实现

- trendradar/__main__.py：单一本地 CLI，不再进入旧日报路径。
- trendradar/core/loader.py：只加载来源、模型、筛选和简报配置。
- trendradar/preview.py：完整真实/演示流程、来源取样、推荐历史、正文复核与 HTML。
- trendradar/daily.py：每日记录、锁、脱敏日志和有限清理。
- trendradar/ai/：模型客户端、分类、正文证据与结构化工程事件；已移除热榜、独立展示区、舆论字段及标签数据库生命周期。
- trendradar/crawler/rss/：订阅解析和实践目录适配。
- trendradar/storage/base.py：仅保留 RSS 数据模型，不再提供云或数据库后端。

## 质量边界与待修问题

- 国内厂商与海外模型公告覆盖不完整；固定模型仓库/SDK 源不能发现所有新模型或商业 API 变化。
- 推荐历史只表示已推荐，不表示已读；同链接内容变化未检测；最近二十条上下文辅助语义去重。
- 普通条目按主机名/GitHub 组织限制最多两条，同标题跨链接过滤；风险词仍是字符串匹配，会受否定句影响，两处词表尚未统一。
- 非空但全部无效的分类数组仍可能返回空匹配；部分来源失败仍可能使每日完成记录封存当天。这些是前次审查已发现问题，本轮功能精简没有宣称修复。
- 正文每次最多五页、每页最多 6000 字符、成功缓存 24 小时；不是网页归档或独立事实核验。
- 连续多日稳定性、有用率、重复率与阅读耗时仍待实际使用观察；不以测试数量代替内容质量。

## 工作区与提交

必须保留用户已有 index.html 和 .python-version 改动，不能全量暂存。根 index.html 是用户既有页面，本轮未修改；当前阅读入口为 output/preview，不依赖它。

仓库：https://github.com/zhizhuotan8-cpu/Personal-Tech-Intelligence-Assistant-for-LLMs 。分支 codex/personal-tech-intelligence，推送目标 origin HEAD:main。用户此前已明确批准推送该仓库 main；测试验证后提交并推送，失败如实报告。

旧源码均通过 Git 删除，可从历史恢复。首次批量文件删除被自动审批拦截；核查目标受 Git 管理且无用户改动后，受保护的 git rm 获准完成。

## 本轮精简验收

- `uv sync --frozen` 成功，旧服务依赖已卸载；保留 22 个运行时 Python 文件，约 2358 行。
- 全量保留测试 73 项、22 个子场景通过；覆盖默认/每日 CLI、配置环境变量优先级，以及真实筛选器和分析器贯通的离线集成。
- 离线演示、全部模块导入和任务状态检查通过。
- 首次真实预览24源采集成功，但模型连续两次空响应（length/5000 tokens）而明确失败，未覆盖成功页。再次真实预览 `output/preview/20261110-212810-935937/report.html` 成功：24源、71候选、2条、190.8秒；已检查原文链接和 latest-success 一致。
