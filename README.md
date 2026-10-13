# Native 闭链轮腿机器人训练

基于 Isaac Lab / RSL-RL 的 native 闭链轮腿训练工程，包含 Motion、Recovery、教师接管、学生策略与接口迁移诊断。
训练、评估和播放共享 native 环境及物理动作契约；运行证据、能力验收与工程检查分别记录。

> 当前是持续演进的研究工程。资产、模型与完整训练证据不随源码发布；暂未添加开源许可证。
> 本地历史配置包含工作站路径，不能直接在其他机器上启动。详见 [发布说明](docs/PUBLIC_RELEASE.md)。

## 快速开始：CPU检查

Python 3.12，先安装适合自己的 Torch（纯CPU可用2.10.0），再执行：

```bash
python -m pip install -r requirements-cpu.txt
python -m pip install --no-deps -e .
python scripts/test_portable_cpu.py
```

CPU检查使用显式 PORTABLE fixtures，不启动仿真或PPO。真实运行还需要Isaac Lab/Sim、外部机器人资产、
模型与新实验身份；准备、授权和公共supervisor命令见 [TOOL_INDEX](TOOL_INDEX.md)。

## 目录

| 路径 | 职责 |
|---|---|
| `src/native_stand/` | native环境、Motion/Recovery、学生与共享工程接口 |
| `tests/` | CPU契约、回归和本地证据检查 |
| `scripts/` | 准备、审计、复盘和历史包装器 |
| `configs/` | 固定契约及历史声明；新运行配置留本地 |
| `docs/` | 工程说明和按日期追溯的实验报告 |
| `manual_train/` | 人工工作台接口；本地引擎/模型独立配置 |
| `deployment_protocol/` | 部署输入/动作协议与参考适配器 |
| `sim2sim/` | 迁移诊断说明；数值产物留本地 |

`runs/`、`artifacts/`、`isolated/`、资产、checkpoint及mutable ledger不进入源码提交。

## 新会话先读

**AGENTS → STATUS → 该任务 spec/run 原始证据**。需要命令、流程、接线时再读下表对应文件。
Motion与Recovery分别选择任务；根STATUS中另一任务的状态不代表本任务授权。

| 唯一正文 | 回答什么 |
|---|---|
| [AGENTS.md](AGENTS.md) | 可以做什么、必须保留什么、后台与授权边界 |
| [STATUS.md](STATUS.md) | 本次任务最新spec/run/terminal和证据在哪里 |
| [TOOL_INDEX.md](TOOL_INDEX.md) | 用哪个工具、精确参数、写入与运行副作用 |
| [WORKFLOW.md](WORKFLOW.md) | 准备→验证→提交→握手→结算/复盘的执行顺序 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 模块职责、共享调用链、数据/协议接口 |
| [TRAINING_EXPERIENCE_REUSE.md](TRAINING_EXPERIENCE_REUSE.md) | 设计reward/课程/选模前复用哪些证据 |

## 工程故障恢复入口

工具用法见 [TOOL_INDEX：受限工程恢复](TOOL_INDEX.md#受限工程恢复与motion补充诊断)，
执行顺序见 [WORKFLOW：受限 Motion 工程恢复](WORKFLOW.md#受限-motion-工程恢复)。
当前声明、证书与核验结果从 [STATUS：Motion](STATUS.md#motion) 进入；模块接线见 ARCHITECTURE。
本页只导航，不复制授权、预算或认证结论。

## GUI与证据审计入口

Motion/Recovery预览、CPU身份计划和新数值轨迹用法见 [TOOL_INDEX](TOOL_INDEX.md#gui公共模式模型身份与数值轨迹)。
实际显示效果与当前证书状态从STATUS读取，CPU计划不替代GUI验证。

## 证据读取

运行事实优先读取run的manifest、source_snapshot、progress、terminal、evaluation和对应ledger。
文档中的“已提交”属于当时握手，不证明现在存活；COMPLETED描述流程，accepted描述能力。
日期工程/实验报告留在docs供按需追溯，不必逐份阅读。
[旧工具清单](TOOL_INDEX_HISTORY.md)仅用于历史复现；当前工具分类由tools.entrypoints查询。
[整合前原文归档](docs/history/ENTRY_DOCS_BEFORE_CONSOLIDATION_20261008.md)不是现行操作说明。

长期目标与部署协议：[PROJECT_MASTER_PLAN](PROJECT_MASTER_PLAN.md)。

人工独立配置、奖励修改、训练与GUI入口：[人工训练工作台](manual_train/README.md)。

电控协议交接（模型未选定）：[deployment_protocol](deployment_protocol/README.md)。该包不改变训练声明或授予实机执行。
