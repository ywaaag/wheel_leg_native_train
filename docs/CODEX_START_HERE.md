# 新 Codex 会话：入口与用法

更新日期：2026-10-07。本页是操作交接，不是训练授权，也不是实时进程状态。
只 checkout 已提交版本时，先检查 `git status`：工作树可能包含尚未提交的新接口，
不能把工作树测试结果当成 HEAD 的验证结果。

## 先读什么

1. 最近的 `AGENTS.md`。
2. 根 `README.md`、`STATUS.md`、`ARCHITECTURE.md`。
3. STATUS 指向的任务 spec，以及对应 run 的 manifest、progress、terminal、原始评估和 ledger。
4. `TOOL_INDEX.md` 与本页。
5. 涉及训练设计、选优或验收时，读 `TRAINING_EXPERIENCE_REUSE.md`。

根 STATUS 同时可能记录 Motion 与 Recovery。先确定本次用户请求的任务，
不要用 Recovery 的状态推断 Motion，也不要用文档中的旧 PID 判断现在存活。
运行事实以对应 run 的冻结实现、配置和原始证据为准；共享源码描述下一次运行。
缺失证据标 UNKNOWN，不能从聊天摘要补造。

## 固定工作环境

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONPATH=src
PYTHON=/home/kellen/anaconda3/envs/issaclab/bin/python
git status --short
```

只修改本项目；保留已有 dirty changes。历史 run、checkpoint、evaluation、ledger、
source_snapshot 和外部仓库只读。不得停止、重启或修改其他任务。
物理 GPU 编号、shared/exclusive 模式和共享授权必须显式核对，不自动切换 GPU。

## 当前入口与安全命令

提交契约修复与 `--check-submission` 用法见
[authorization/session 提交检查](SUBMISSION_CONTRACT_FIX_20261007.md)。
该轮按要求仅提交文档，相关代码仍在工作树；只 checkout HEAD 时先核对接口是否存在。

唯一公开提交入口是 `native_stand.command_v6.supervisor`。
launcher、monitor、stand_chain 是内部组件，不是另一条供用户选择的提交路线。

以下命令只显示用法或执行只读检查，不启动 AppLauncher/PPO：

```bash
"$PYTHON" -m native_stand.command_v6.supervisor --help
"$PYTHON" -m native_stand.command_v6.tools.preflight --help
"$PYTHON" -m native_stand.command_v6.tools.health_check --project-root "$PWD"
"$PYTHON" -m native_stand.command_v6.tools.completion --help
```

使用实际 spec 和新的输出路径设置 `SPEC_PATH`、`RUN_PATH` 后，再做计划检查：

```bash
"$PYTHON" -m native_stand.command_v6.supervisor --spec "$SPEC_PATH" --output-dir "$RUN_PATH"
"$PYTHON" -m native_stand.command_v6.tools.preflight --spec "$SPEC_PATH" --output-dir "$RUN_PATH" --phase formal
```

supervisor 默认 plan-only；运行必须额外显式选择 `--launch`。
不要把本页示例、旧 ledger 剩余额度、已通过 smoke 或终态通知当成新运行授权。
`--formal-only` 仅复用同一链内已经核验的前置证据，不绕过预算和身份检查。
`--evaluation-only` 是 PPO0，但仍是物理仿真，需要用户授权。

| 工具/操作 | 写入与运行边界 |
| --- | --- |
| health_check、preflight、supervisor 默认计划 | 只读；不创建 run、不 reserve ledger、不启动仿真 |
| 准备器 | 创建新 spec/独立预算及来源清单；不等于授权运行 |
| correct_evidence、离线 audit | 仅在新输出目录写更正报告；不覆盖原证据 |
| supervisor --launch | 需要明确授权、exact attempt、身份与预算前置检查 |
| completion/通知 | 使用现有终态证据；外部通知需授权，目标是本次会话 |

详细 CLI 以本工作树的 `--help` 和 `TOOL_INDEX.md` 为准。
按日期命名的旧 preparer 只用于该实验复现，不是通用准备入口。
不得移除 historical guard；弃用包装器不能被当作续训入口。

## 一次提交的固定流程

1. 核对任务、授权、来源 checkpoint SHA、资产、spec、执行依赖与冻结副本。
2. 做一次必要资源检查；检查 ledger 未结算 attempt，不抢占其他任务。
3. CPU tests 与零写入 preflight/plan-only。
4. 有授权时才执行有界 smoke；验证真实 episode 事件，不以固定更新数代替覆盖。
5. 由 supervisor detached 提交，后台 owner 管训练、评估、预算、结算与终态通知。
6. 只做一次启动握手；反馈当前阶段与证据，然后结束交互。

SUBMITTED 仅表示提交，SOURCE_EVAL/SMOKE 不表示 formal 已开始。
只有 formal 首个真实更新、进程身份、attempt、输出路径及 progress 证据齐全，
才能报告 formal 已启动；UNKNOWN 握手不能冒充启动成功。
CPU 测试、有限 loss 和 reward 上升都不证明机器人能力通过。

## 后台训练与唤醒规则

Codex 不得循环读 progress/log，不得周期性执行 ps/nvidia-smi/tail，
不得用 sleep、反复 wait 或代理 watcher 等待整场训练。
后台 monitor 可以履行其预算与结算职责，worker 不代替它。
终态由既有 hook 通知当前 HAPI 会话；不要复制旧 session ID。
通知失败与训练失败分开记录，不因此重跑训练。
终态通知只授权读取复盘，不自动授权续训，也不重复处理已 reviewed 的事件。
规则详见 [后台执行政策](DETACHED_TRAINING_POLICY.md)。

## 新实验、协议与证据

新实验统一使用 `YYYY_M_D-HH_MM__purpose`，由集中命名函数生成。
spec.experiment、配置目录、run 与报告应对应；旧实验不重命名。
来源、latest、best_new、best_overall、accepted 和 fallback 分开登记。
未评估 checkpoint 不能 accepted，来源不能冒充新训练结果。

评估时长、窗口、终止语义和保存字段应从有效任务协议解析。
Recovery holding 与 rising 不混用时长；Motion 保持段与停车段分别评分。
诊断未采集字段必须是 null/invalid，不能伪装真实零。
summary、failure_tail、full_transition 的字段和采样率先在 plan 中核对。
若当前工作树有新的诊断准备器，先读其 `--help` 与对应工程报告；
不能因它创建了预算文件就直接运行。

冻结源码可以重定位，但声明身份与实际副本位置要分别记录并逐文件核验。
报告更正写新目录，输入路径与 SHA 留清单；不能凭“更正”追溯宣布旧能力通过。
reward、课程、网络、PPO、物理契约的改变另建实验，不能混入普通接口修复。

## 文档导航与交付

- [工具索引](../TOOL_INDEX.md)：当前工具与历史工具分类。
- [工程交接](ENGINEERING_STATUS.md)：已有接口与验证范围；其中日期是历史检查时刻。
- [命名规则](EXPERIMENT_NAMING.md)。
- [Git 工作边界](GIT_WORKFLOW.md)。

结束时列出精确修改文件、实际验证命令/结果、仍缺证据及 commit SHA。
只暂存本次授权改动，不使用 `git add .` 混入其他 worker 的训练配置或代码。
文档更新不能声称新的物理验证；没有运行就明确写“未启动仿真/PPO/续训”。
