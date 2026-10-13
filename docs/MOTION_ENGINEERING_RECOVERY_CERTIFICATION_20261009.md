# Motion None-window 工程恢复认证：2026-10-09

本轮工程资格为 **READY**；公共 supervisor 的实际零写计划为 **READY_NEEDS_AUTH / cpu_valid=true**。仅阻断于未授权账本，不存在需再次PPO0补测的工程证据缺口。没有启动任何仿真、PPO0或训练，没有增加预算，没有修改原FAILED。

## 恢复契约与真实证据

优化接线、故障修复、来源能力、新候选能力分层审核：

| 层次 | 结论 | 边界 |
|---|---|---|
| 原smoke优化接线 | 1次真实更新、8192样本、actor参数确有变化；actor/critic/Adam/RNG完整 | 不证明运动能力改善 |
| None窗口修复 | 同smoke checkpoint独立PPO0，0/±.5各8env完整4秒；151姿态样本/env；窗口[.5,2] | engineering-only，capability NOT_RUN，accepted=false |
| 原B250来源 | 九命令0/±.5/±1/±1.5/±2，逐项30秒、8/8；来源与失败smoke历史源码身份相同 | 审核后迁移引用，历史raw/manifest不改 |
| smoke新候选完整能力 | UNKNOWN | 不能把light补测升级为九命令能力认证 |

来源B250 SHA：`5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。smoke SHA：`51444ce99f439f046157ba0313d0715731680c9c6f6286dfb195109a7a8727c0`。
资产SHA：`6bf6ce7f64f8d46cdc759bdf48dba0def85f6e9e6915acca27c543dbcf031a27`。formal仍从原B250恢复actor/critic/自身Adam/std/CPU+CUDA RNG，不从smoke继续；新物理reset沿用原语义。

## 工程修复

- 新受限证书版本`motion_light_none_window_recovery_v1`只支持已知milestone轻评估None窗口异常，物理故障/配方改变不适用。
- 各检查独立收集，窗口、checkpoint、模块或审核异常保留身份/预算/其他已核验事实及全部拒绝原因。
- task_subsystem_v2保留全项目快照，显式记录Motion未调用的Recovery子树/专属工具排除及理由；所有共享Motion模块仍保守审核。
- 24项下一次执行差异、6项补测差异逐文件绑定旧/新SHA及具体理由；原占位unapproved_change_review未改。reward、网络、PD/环境关键模块以及外部PPO/依赖版本严格不变。
- 支持零写计划和事务发布，完整标记最后写入；同一失败exact attempt＋terminal SHA只能发布/预约一次。
- preflight、wiring.completed_smoke、Ledger.reserve、supervisor formal-only、trainer与completion复用同一证书。恢复接线不冒充新候选accepted；来源迁移保留原identity/raw引用。
- 严格迁移对未知运行字段、reward/物理/PPO/seed/RNG恢复变化拒绝；预算、授权与命名只按明确规则迁移。
- 证书JSON路径/SHA序列在生成时规范化；实际冻结模块身份校验与稳定声明路径绑定分开，避免合法snapshot重定位误拒绝。

原窗口修复和独立update_proof工具属于本轮前已存在的修复，本轮核验并接入，不改reward或优化算法。

## 累计预算与发布

历史链3806.672207秒＋失败重试链1939.752001秒（含链开销/清理）＋补测已结算ledger88.405236秒＝5834.829444秒。
原10800秒剩4965.170556秒；smoke已用1，formal已用0。新source/smoke额度为0，formal最多50、409600样本。
新formal墙钟继续采用更小的原formal上限4013.327793秒，未扩大到全部余额；新链上限4965.170556秒。
中央recovery_accounting被准备与证书消费者复用；新ledger zero used、empty attempts、UNAUTHORIZED，历史消耗仅SHA引用，不复制COMPLETED。

- 新声明：`configs/experiments/2026_10_9-10_14__motion_posture_engineering_recovery/spec.json`
- 新账本：`configs/experiments/2026_10_9-10_14__motion_posture_engineering_recovery/budget.json`
- 证书：`configs/experiments/2026_10_9-10_14__motion_posture_engineering_recovery/engineering_recovery_certificate.json`
- 证书SHA：`7c60d4776692505ca9418fef032bdbf3602ed58ce38818ec7f5d5b7560f21df7`
- 审核SHA：`2873c129a5307e7207535bdf9fcbe5fc5189a65e756ab0600fbe3b3fd90a8cb0`
- 机器结果：`artifacts/motion_engineering_recovery_v1_20261009/result.json`

## CPU验证与实际调用链

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q tests/test_motion_engineering_recovery_certificate.py tests/test_engineering_recovery_interfaces.py tests/test_submission_contract.py tests/test_publication_and_recovery_fields.py tests/test_motion_preparer.py
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q tests
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_9-10_14__motion_posture_engineering_recovery/spec.json --output-dir runs/2026_10_9-10_14__motion_posture_engineering_recovery --formal-only
```

专项76 passed；全量676 passed / 97.34秒。专项真实历史证据只读，授权/预约在临时fixture完成；实际公共supervisor dispatcher、preflight、授权登记、wiring、reserve及重复拒绝路径覆盖。
新声明真实supervisor plan返回READY_NEEDS_AUTH，唯一preflight错误为“new simulation/PPO budget has not been authorized”；stages仅formal/terminal_reconciliation。
另用import audit hook运行真实入口，Isaac/omni/pxr导入会立即拒绝，实际plan正常完成。核对publication各文件SHA、zero used/empty attempts、run不存在，证明未reserve/写run。
覆盖错误checkpoint、缺环境、短窗口、runtime fault、light虚假capability、未审核/过期审核、配方变化、异常保留事实、预算不重置、一次性发布/预约和冻结位置差异。首次验证暴露JSON元组/数组复验错误，已修；测试期间源码变化曾触发正确的SHA拒绝，最终固定源码重跑全部通过，未降低断言。

## 历史保护与证据局限

30份原始输入文件前后SHA一致，包括原FAILED、旧账本、原spec、checkpoint和来源raw。失败链完整冻结代码138项与manifest匹配。补测旧快照仅归档38项；另89项与当前字节的运行SHA一致，12项只有运行manifest追溯，不能称完整冻结归档。None窗口helper当前字节与补测记录SHA严格一致，evaluator冻结字节也匹配；未补造历史快照。详见frozen_snapshot_readback.json。
本轮新增物理样本0、在线PPO0、真实模型离线optimizer steps0、attempt0。没有进程控制、通知、Recovery修改或Git提交。
尚未物理验证新恢复formal启动、当前审核版本的新训练效果及smoke完整九命令能力。工程READY不等于能力改善；运行前仍需新的明确授权和实时session/GPU/receipt核验。

## 精确改动文件

- `src/native_stand/command_v6/domain/recovery_accounting.py`
- `src/native_stand/command_v6/tools/motion_recovery_certificate.py`
- `src/native_stand/command_v6/tools/prepare_engineering_recovery.py`
- `src/native_stand/command_v6/tools/execution_identity.py`
- `src/native_stand/command_v6/tools/source_evidence.py`
- `src/native_stand/command_v6/config.py`
- `src/native_stand/command_v6/tools/preflight.py`
- `src/native_stand/command_v6/wiring.py`
- `src/native_stand/command_v6/ledger.py`
- `src/native_stand/command_v6/supervisor.py`
- `src/native_stand/command_v6/train.py`
- `src/native_stand/command_v6/completion.py`
- `src/native_stand/command_v6/tools/entrypoints.py`
- `tests/test_engineering_recovery_interfaces.py`
- `tests/test_motion_engineering_recovery_certificate.py`
- `TOOL_INDEX.md`
- `WORKFLOW.md`
- `ARCHITECTURE.md`
- `STATUS.md`

新增CPU报告/审核/plan位于`artifacts/motion_engineering_recovery_v1_20261009/`，新声明五文件事务发布；本报告只追加当前工程结果，不改历史结论。
