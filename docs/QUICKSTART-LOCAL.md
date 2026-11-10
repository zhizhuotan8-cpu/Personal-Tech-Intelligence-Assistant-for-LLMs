# 本地使用

当前安装、运行、配置和输出位置统一见 [README](../README.md)。

首次运行 `setup-windows.bat`，设置 Windows 用户环境变量 `AI_API_KEY`、`AI_MODEL` 和可选 `AI_API_BASE`，再双击 `start-preview.bat`。离线可用 `start-demo.bat`。

每天自动运行：安装 `install-daily-task.bat`，状态查看 `daily-task-status.bat`。阅读入口为 `open-latest-report.bat`。

失败时检查 `output/preview/latest.html` 或 `output/daily/latest.json` 指向的日志。凭据缺失请检查用户环境变量；网络/模型失败可重试手动预览。每日任务当天已完成则跳过，再次完整分析请用 `start-preview.bat`。
