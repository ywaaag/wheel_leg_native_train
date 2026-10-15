# 文档目录

新用户先读根 [README](../README.md)。Codex执行读 [AGENTS](../AGENTS.md)，再从
[STATUS](../STATUS.md) 定位任务。命令、流程与模块结构分别维护于 TOOL_INDEX、WORKFLOW、ARCHITECTURE。

本目录按文件名保留工程修复、实验复盘和证据解释，不将历史结果写成最新能力保证。
`history/` 为旧导航/操作记录，`RECOVERY_STANDING_PLAN.md` 为 Recovery 专项说明。
具体实验结果应核对对应 manifest、冻结 spec、原始 evaluation 和 terminal。

## 证据状态说明（2026-10-14 存储精简）

2026-10-14 的一次存储精简**永久删除**了 557 项历史 `runs/`、`isolated/` 目录
（执行回执见 `artifacts/prune_execution_receipts/`）。此后阅读本目录报告时：

- 报告正文顶部带「**证据注记**」的文件，表示其**部分**引用目标已不可访问；未带注记的文档不引用已清理数据。
- 这些报告的文字、数值、模型身份与当时结论**未被改写**，仍按当时的 run 身份与协议阅读；
  顶部所述结论**来自历史报告**，不再声称现场复核通过。
- 已清理的数据**不作重建、不作补零、不重新认定能力通过**。
- 需要复现时，按报告声明的独立 spec/run/ledger 重新运行，而不是引用已删除路径。
- 报告区分三类信息：**事实**（当时 run 的原始记录）、**摘要**（本目录的归纳）、**当前验证**（本轮可复核项，
  标注为 PORTABLE CPU 检查或当前入口审计）。

报告链接到本地 `runs/`、`artifacts/`、`isolated/` 时，公开 checkout 可能没有这些数据。
路径是可追溯引用，不代表附件已发布；模型、资产和完整轨迹由拥有者单独提供。
发布与依赖说明见 [PUBLIC_RELEASE](PUBLIC_RELEASE.md)；本文不复制工具命令或任务状态。
