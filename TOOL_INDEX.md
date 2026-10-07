# Current Tool Index

当前Recovery：docs/RECOVERY_COVERAGE_AB_20261007.md；准备工具
scripts/prepare_recovery_coverage.py。source_capability使用supervisor --evaluation-only，
A_first/B_uniform使用同一supervisor的source/smoke/formal链。一次性独立预算，
明确GPU0/shared和当前session；不得自动增强系数或扩展R1训练。

本页仅列当前公共入口。历史命令、旧会话/PID、日期配方和旧推荐保留在
[历史工具清单](TOOL_INDEX_HISTORY.md)，不能作为当前运行许可。
新实验根目录和spec名称必须以创建日期时间开头，例如
`2026_10_7-14_27__motion_width_ab`；详见[命名规则](docs/EXPERIMENT_NAMING.md)。
完整机器可读分类：`python -m native_stand.command_v6.tools.entrypoints --include-historical`。

## 唯一公开提交入口

`native_stand.command_v6.supervisor`，默认 plan-only。必须显式提供 spec/output；
运行还需当前授权、GPU、会话、独立账本和身份匹配的证据。
`launcher`、`monitor`、`stand_chain` 是内部组件，不是另一条公开提交路线。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
-m native_stand.command_v6.supervisor \
--spec <明确选择的spec.json> --output-dir <新的output目录>
```

此示例没有 `--launch`；plan 不创建 run、账本或报告。
资源默认 exclusive；shared 需要本次明确批准说明。提交确认、当前阶段与
formal 首更新验证分开，UNKNOWN 不能宣称训练已启动。

## 当前检查与报告入口

| 入口 | 职责 |
| --- | --- |
| `tools.entrypoints` | 只读公共/内部/历史工具分类，默认只显示当前入口 |
| `tools.health_check` | 只读文档、身份、账本和进程核验 |
| `tools.preflight` | CPU 前置检查与明确 reason code |
| `tools.completion` | 通用终态报告 CLI，底层实现仍在 completion.py |
| `tools.correct_evidence` | 新目录离线更正报告，不覆盖历史原始评估 |
| `scripts/audit_recovery_survival.py` | 冻结输入、身份及指标离线审计 |

表中 tools 模块前缀均为 `native_stand.command_v6.`。
精确参数以各入口 `--help` 为准；只读核验不授权仿真。
独立物理评估由 supervisor `--evaluation-only` 提交；评估执行器是内部组件。

## 当前证据与决策入口

- Motion 最终复核：[工程报告](docs/MOTION_ENGINEERING_RECHECK_20261007.md)的最终结论优先；
  B250 为推荐来源，new250 的早期推荐已被后续同协议物理证据替代。
- Recovery R0 hold10 已完成：[复盘](docs/RECOVERY_R0_HOLD10_REVIEW_20261007.md)。
  source50 仍优于已评估新模型，旧授权不允许再次提交。
- 当前 spec/候选/授权状态看 [STATUS](STATUS.md)，不从工具名或版本号猜测。
- [本次入口收敛与边界](docs/ENTRYPOINT_CONSOLIDATION_20261007.md)。
- [接口语义](docs/ENTRY_SEMANTICS_FIX_20261007.md)、[Git边界](docs/GIT_WORKFLOW.md)。

## 准备器边界

当前没有通用且不改变配方的 Motion 实验准备器。现有
`prepare_motion_course_plan.py`、`prepare_recovery_hold.py`、
`prepare_motion_recheck_20261007.py` 是特定配方/复现实验工具；
生成配置不能代替设计决策、校验或授权。本轮没有把它们包装成通用准备器。

旧高速 runtime 准备入口已禁止执行。三个固定旧路径的 Motion 准备器默认拒绝，
历史声明复现需显式 `--historical-replay`，且仍不能覆盖已有目录。
两兼容 submit/continue 包装器保留弃用提示；新提交直接使用 supervisor。
