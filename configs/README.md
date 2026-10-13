# 配置与运行身份

- `contracts/`：固定接口、模型和物理契约。
- `experiments/`：已跟踪的历史实验声明，用于解释当时运行，不是通用启动配置。
- `tools/`：工具配置；使用前检查资产和机器路径。

新的实验由公共准备器生成独立 spec 和 ledger。源码 checkout 不授予运行授权。
新声明、预算、授权回执和运行快照默认保留本地，不能把旧额度作为新额度。

本仓库中的 `/home/kellen/...`、GPU UUID、来源 SHA 和 session 字段是历史工作站身份；
它们不能直接用于其他机器。按 [TOOL_INDEX](../TOOL_INDEX.md) 的公共准备/授权流程生成新声明，
保持 requested/effective/实际执行身份可审计，勿批量改写旧 spec。
