# Recovery学生工程边界收口（2026-10-11）

本轮仅CPU工程，未启动仿真、GUI、PPO0/在线PPO、通知、重试或提交；未查询后台训练进度。历史run/checkpoint/spec/ledger与活动冻结源码保持只读。

## 实际修复与兼容性

- 首步测试执行真实CommandEnv、RecoveryEnv、StudentEnv、TrainingStudentEnv与HandoffEnv构造和实际_get_dones。只替换最低层Isaac物理数据fixture；包含部分reset、task_phase故障检测、pre-reset快照和安全终止，不以替换共享parent/dones掩盖依赖。
- prepare_student_recovery_ppo显式parent/source、SHA及31D版本核验；case_id选择五项，缺项/重复/错误来源拒绝。发布记录parent/source SHA及完整配置差异；不再使用日期路径或数组索引。训练来源/最终复评也按case_id/kind选，不改变实际原矩阵与算法。
- students.artifacts将checkpoint、完整rollout、故障NPZ原子落盘，临时写入fsync后rename；失败保留旧文件、清理临时文件。评估保存或close错误附secondary notes，不覆盖原异常；训练terminal/progress保存故障仍尽力close，并在app.close前和finally恢复进入前RNG。
- 存储上限读取student_training.storage_max_bytes、student_evaluation.max_output_bytes和声明terminal_reserve_bytes；runtime/evaluation/preflight共用。原128MiB终态余量仍为兼容默认，新准备器显式写入；reward/PPO/网络/控制/物理未改变。
- 公共validate_frozen_cpu增加submission-package与严格reuse-validation。只复制指定PORTABLE tests+conftest，完整包含spec/budget/identity/frozen validation/zero-write plan/authorization template/supervisor command。审阅副本不用于直接授权，模板指向原未授权声明；不另造launcher/trainer/watcher。
- watcher的循环与通知逻辑删除为纯退役拒绝壳，import finish亦拒绝。select_recovery_checkpoint只支持显式historical-replay、legacy150D Recovery，拒绝student/receiver/handoff；外部新output必填，旧run不回写。静态引用仍含目录/测试/历史文档，文件保留。
- audit_storage categories-only只统计元数据并输出保留建议；runs整体排除，不以大文件名/体积作为删除依据。

## 新CPU声明与准备包

- 声明：`configs/experiments/2026_10_11-14_22__recovery_mcu_v2_task_ppo_from_bc`（UNAUTHORIZED，zero used，empty attempts）。
- 来源：`/home/kellen/wheel_leg_native_train/isolated/recovery_mcu_v2_bc_20261011/best_validation.pt`；SHA `7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470`。该工具复现既有版本，换来源必须新版本配方，不静默放宽固定source条件。
- 包：`artifacts/student_engineering_boundary_20261011/frozen_final/submission_preparation/`。
- 真共享supervisor plan：`artifacts/student_engineering_boundary_20261011/shared_supervisor_plan.json`；preflight {'status': 'FAIL', 'errors': ['new simulation/PPO budget has not been authorized'], 'cpu_valid': False}，未创建run或reserve。未授权不是提交就绪。
- 冻结schema为[]、plan exit0且run_created=false；其零预算隔离ledger导致前置FAIL/未授权与phase exhausted，属于CPU隔离声明，不能报告物理PASS。真实新声明另行plan，错误见上项。
- 复用收据：`artifacts/student_engineering_boundary_20261011/validation_reuse/validation_result.json`；只有精确spec/source/tests/conftest/interpreter匹配才复用，不重复源码复制。

## 测试、磁盘与证据限制

- 相关CPU18 passed；最终冻结PORTABLE9 passed。真实异常fixture覆盖rollout错误＋NPZ保存错误＋close错误，原错误/RNG仍保留；execute fixture验证app.close前RNG及terminal主错误。
- 全量783 passed、4 warnings、22 errors。22项均是旧Motion证书fixture当前critical module SHA冲突，单独保留tests_full.txt，不修改生产证书或测试断言来全绿。
- 初次冻结通过7项，最终追加异常/复用测试后9项；两份验证保留初次/最终证据，不是无限复制。
- 排除所有runs及本次目录后：冻结验证copy109.22MiB，JSON/声明1228.06MiB，checkpoint300.02MiB，派生报告15.08MiB；另105个artifacts目录分类。不含runs，不能解释成全项目总占用。保留历史raw/checkpoint/首次失败和最终成功收据；后续优先精确复用、引用摘要。未删除任何历史证据。
- 真实共享首步在CPU数据fixture通过不代表PhysX启动或物理能力通过；本轮没有PPO在线/采样、训练预算使用或运行授权。

## 精确改动文件

- `tests/test_student_recovery_runtime_parent.py`
- `tests/test_student_engineering_boundary.py`
- `tests/test_student_preparation_contract.py`
- `scripts/prepare_student_recovery_ppo.py`
- `src/native_stand/students/training.py`
- `src/native_stand/students/artifacts.py`
- `src/native_stand/students/requests.py`
- `src/native_stand/command_v6/tools/validate_frozen_cpu.py`
- `src/native_stand/command_v6/tools/submission_preparation.py`
- `src/native_stand/command_v6/tools/audit_storage.py`
- `src/native_stand/command_v6/tools/entrypoints.py`
- `scripts/watch_recovery_submission.py`
- `scripts/select_recovery_checkpoint.py`
- `TOOL_INDEX.md`
- `ARCHITECTURE.md`
- `WORKFLOW.md`
- `STATUS.md`

额外新产物只在本次CPU artifacts和新未授权声明；源码dirty changes保留，不commit/push。工具命令集中TOOL_INDEX，结构ARCHITECTURE，流程WORKFLOW，状态STATUS。
