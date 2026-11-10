# 简报质量与推荐记录（2026-11-10）

本批次检查此前五条简报，优先处理重复推荐与日期误读。

## 原文核对

- [检索与上下文工程](https://www.langchain.com/blog/context-engineering-starts-with-retrieval)：原文标注 2026-10-23，支持先搜后读、超大工具结果落盘和子 Agent 阅读的主要描述。
- [Stripe Kai 案例](https://www.langchain.com/blog/how-stripe-built-their-knowledge-ai-platform-on-deep-agents)：原文标注 2026-08-03，属于历史实践；厂商案例不能作为性能和安全的独立验证。
- [Agent 记忆组件](https://www.anthropic.com/research/components-of-agent-memory)：原文标注 2026-11-06，主要讨论记忆捕捉、巩固和 dreaming。
- [浏览器工具优化](https://www.langchain.com/blog/how-we-optimized-browser-use-for-deep-agents)：原文标注 2026-11-03，支持工具选型应结合 trace 与评测的阅读方向。
- [Gemini SDK 发布页](https://github.com/googleapis/python-genai/releases/tag/v3.0.0)：保留为兼容性复查对象。本批次不声称已完成所有迁移细节的独立验证。

## 当前行为

预览从同目录下成功的真实 status.json 读取已推荐 URL；失败与演示不计入历史。只过滤以前最终入选的文章，未入选候选仍可参与。历史依赖本地产物，清理 output/preview 会清除记录。

同链接默认不再占用推荐名额；标题或摘要含 breaking、deprecation 等风险信号时仍允许模型复查，并显示“此前已推荐”。这是关键词保留策略，不能保证识别所有风险，也不处理同链接正文变更和跨链接同主题去重。

“新增推荐”只代表此前没有推荐记录，不代表新发布或已经阅读。目录日期标注为“目录标注日期”；普通 RSS 为“来源标注日期”；实践 RSS 的原始日期未经核实，明确显示未核实。此次未增加通用原文日期抓取器。

验收时分别记录离线测试与真实运行；模型失败不得记作无更新或成功推荐。
