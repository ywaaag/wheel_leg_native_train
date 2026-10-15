# Native 闭链轮腿机器人训练

当前Motion31：[已授权前进优先课程](docs/MOTION31_FORWARD_COURSE_20261015.md)，从v3/u1600推进+2→+3→+4，2000次含smoke、停车仅诊断，当前提交状态见STATUS。此前[直线/yaw晋级课程已因旧能力退化有界停止](docs/MOTION31_COURSE_TERMINAL_REVIEW_20261015.md)，formal1000＋smoke5，首档±1.5未通过、±2/yaw未解锁。保留已三seed120/120确认的v3/update1600为基线，750仅最佳新候选不代表胜过来源。不自动续训；实际状态以[STATUS](STATUS.md)及原始证据为准。

Motion31新的平地训练设计与来源能力边界见[Motion31训练设计](docs/MOTION31_TRAINING_DESIGN_20261014.md)；512env/2000formal父链见[512运行记录](docs/MOTION31_PARALLEL512_20261014.md)，最新formal已进入学习的存储恢复见[工程恢复](docs/MOTION31_PREFORMAL_STORAGE_RECOVERY_20261014.md)。状态见[STATUS](STATUS.md)，准备/plan命令见[TOOL_INDEX](TOOL_INDEX.md)。新Motion49语义不等于站立49，提交不代表能力通过。

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

## 当前能力与限制

- 代码侧提供 Motion、Recovery、教师接管与学生（31D / 25D 蒸馏）的训练、评估、播放与接口迁移诊断路径。
- **能力结论以 run 证据为准**：`terminal` 描述流程是否走完，`evaluation` 描述能力是否被接受；
  本页与导航文档不声明未经验证的能力。
- 资产、模型、checkpoint 与完整训练证据**不随源码发布**，需由模型/资产拥有者单独提供；
  缺少公开资产时，只能执行 PORTABLE CPU 检查，不能进行真实训练或评估。
- `configs/` 保留了当时的本地声明（含工作站路径），**不能直接在其他机器启动**，详见 [发布说明](docs/PUBLIC_RELEASE.md)。
- 仓库暂未添加开源许可证。

## 证据与历史

运行事实以 run 自身的 manifest、source_snapshot、progress、terminal、evaluation 与 ledger 为准：
文档里的“已提交”只属于当时握手，不证明现在存活；COMPLETED 描述流程，accepted 描述能力。
2026-10-14 的存储精简已永久删除 557 项历史 `runs/`、`isolated/` 目录，受影响报告顶部带「证据注记」，
集中说明见 [docs/README](docs/README.md#证据状态说明2026-10-14-存储精简)。
日期工程/实验报告留在 `docs/` 供按需追溯，不必逐份阅读；
[整合前原文归档](docs/history/ENTRY_DOCS_BEFORE_CONSOLIDATION_20261008.md)不是现行操作说明，
[旧工具清单](TOOL_INDEX_HISTORY.md)只用于历史复现（当前工具分类由 `tools.entrypoints` 查询）。

专项入口：受限工程恢复见 [TOOL_INDEX](TOOL_INDEX.md#受限工程恢复与motion补充诊断) 与
[WORKFLOW](WORKFLOW.md#受限-motion-工程恢复)，声明/证书/核验结果从 [STATUS：Motion](STATUS.md#motion) 进入；
预览、CPU 身份计划与 GUI 用法见 [TOOL_INDEX](TOOL_INDEX.md#gui公共模式模型身份与数值轨迹)（CPU 计划不替代 GUI 验证）。

## 长期与专项文档

| 文档 | 内容 |
|---|---|
| [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) | 长期目标、部署目标与多技能路线 |
| [manual_train/README.md](manual_train/README.md) | 人工独立配置、奖励修改、训练与 GUI 入口 |
| [deployment_protocol/README.md](deployment_protocol/README.md) | 电控协议交接（模型未选定）；不改变训练声明、不授予实机执行 |
