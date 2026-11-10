# 个人大模型应用工程情报助手

面向大模型应用开发工程师，关注 Agent、RAG、模型/API 和部署。基于 TrendRadar 改造，沿用 GPL-3.0；原项目为 https://github.com/sansan0/TrendRadar 。

采集官方 RSS/Atom 和工程实践目录，按个人兴趣筛选，复核入选文章正文，输出最多五条中文简报：事实、工程影响、验证建议和原文链接。报告明确区分正文摘录、摘要和标题证据，不代表独立事实核验。

## 开始使用

1. 安装 Python 3.12+ 和 uv，运行 `setup-windows.bat`，或在项目目录执行 `uv sync --frozen`。
2. 在 Windows 用户环境变量设置 `AI_API_KEY`、`AI_MODEL`（provider/model 格式），按需设置 `AI_API_BASE`。不要将密钥写入仓库。
3. 双击 `start-preview.bat` 生成真实简报；`start-demo.bat` 查看明确标注的离线演示。
4. 双击 `open-latest-report.bat` 查看最近成功且有内容的报告，注意页面日期。

默认命令 `python -m trendradar` 直接生成真实简报；`--preview` 是等效显式写法。可用 `--days 7`、`--no-open`、`--full-evidence`。`python -m trendradar --daily` 和 `python -m trendradar.daily` 均执行具有每日防重记录的入口。

## 每日运行

`install-daily-task.bat` 安装每天北京时间 20:00 的 Windows 任务。无需打开 Codex，但电脑须开机联网、用户保持登录，锁屏可；注销或关机无法运行。错过后由 Windows 补跑，不保证立即补跑。

- `daily-task-status.bat`：查看计划任务和应用状态。
- `run-daily-now.bat`：触发任务；当天已完成会跳过，失败可重试。
- `uninstall-daily-task.bat`：卸载任务，保留报告和配置。

## 配置与数据

- `config/config.yaml`：24 个来源、模型参数、筛选阈值与候选上限。
- `config/ai_interests.txt`：个人兴趣；Agent 40%、RAG 30%、模型/API 20%、部署 10% 是长期倾向，不是每日配额。
- `config/ai_engineering_prompt.txt`：选稿与证据规则。
- `output/preview/`：独立报告、采集记录、推荐历史；`latest-success.html` 为最近成功且有内容的报告。
- `output/daily/`：每日状态与脱敏日志；`output/evidence/`：正文摘录缓存。

数据保存在本地，不发送通知。仅清理超过 30 天的日志与正文缓存，报告及推荐历史保留。`output/` 不上传 Git。

## 边界与验证

国内厂商公告覆盖不完整；固定模型仓库或 SDK 更新不能代替全部模型公告。语义去重依赖模型，网页摘录可能截断；同链接内容更新未自动检测。连续多日运行与选稿效果仍需实际阅读验收。

本项目仅保留本地助手功能。旧综合热榜、舆情分析、通知、翻译、MCP、云存储、Docker 和 GitHub 定时采集已移除。

安装开发依赖后执行 `uv run pytest -q tests`。当前说明见本文件和 [交接文档](docs/HANDOFF.md)。
