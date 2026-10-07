# 状态、任务请求与历史入口修复

后续工程与当前总览见[ENGINEERING_STATUS](ENGINEERING_STATUS.md)。本文415项
测试及当时任务描述是阶段验证，不冒充当前GPU运行或最新全量验证结果。

范围：当前共享源码、CPU回归及文档；不启动仿真/训练、不修改运行快照，
不修改reward、PPO、物理或已有spec/ledger。现场已存在另一worker的coverage
实现，保留并增量接线，不把全部工作树变化归为本轮新实现。

## 生命周期

tools.run_state提供RunState和共享事件写入：
PLANNED → SUBMITTED → SOURCE_EVAL → SMOKE → FORMAL → COMPLETED/FAILED。
额外保留STOPPED_BOUNDED，预算/用户停止不能伪装成runtime失败。
run_state.json为canonical事件，chain_progress及supervisor_terminal是其投影。
startup_handshake经同一模块观察事件；state/status一致，legacy_handshake_status
保留兼容含义。started、identity_verified、formal_first_update_verified仅为证据，
SUBMITTED或FORMAL状态本身不证明首更新或行为验收。收据不回退worker状态。
durability属于FORMAL之后的证据阶段，不另建RUNNING状态。

本轮迁移共享stand_chain，覆盖public supervisor的标准source/smoke/formal链。
旧独立A/B协调器、Recovery历史链与phase monitor旧终态记录没有追溯迁移；
它们不是当前公开提交入口，也不能据此宣称所有历史输出都已有统一状态。
活动coverage任务继续执行原冻结实现，其状态文件保持原样。

## Motion/Recovery请求

tools.motion_batch与tools.recovery_batch各自校验task，使用独立纯schema；
底层AppLauncher、模型恢复、环境创建和结果保存仍复用evaluate_checkpoint。
不是新增两条公开提交CLI。Motion不能带family/Recovery字段；Recovery不能带
Motion窗口/调度字段。未知字段拒绝，校验SHA/target/seed/seconds，合法role保留。
Recovery batch目前只接受明确family、zero target和10秒，保留当前已验证边界，
不默认扩大为100秒任务。独立durability仍使用其原有效协议路径。

## 历史工具与命名

两旧高速wrapper仅提示弃用并退出2，不再转发supervisor。
hold、Motion课程/重评估/报告、retention创建、settling复盘等已列历史CLI
须--historical-replay；旧watch和固定高速runtime禁用。
make_retention_reeval_spec原来import即可读写历史路径，本轮收进guarded main，
existing目录拒绝、exclusive-create，不改旧评价公式。
未批量移动/删除所有日期脚本；其他历史工具仍以历史清单及AGENTS约束。

集中命名函数位于domain.experiment_naming，Asia/Shanghai，日期有效性检查。
当前公开coverage准备器的CLI与prepare均校验时间前缀，已有配置不重命名。
未来新增公开prepare必须复用此函数；旧历史复现不伪造新时间或授权。

## holding与采样诊断

continuous_holding已经跳过STAND forward，本轮不再次重写控制路径。
新增显式requires_stand布尔校验：false仅允许无STAND依赖的continuous_holding；
与已声明teacher路径冲突时拒绝。没有更改现有spec；去掉teacher依赖属于后续
新实验声明，不能直接修改当前A/B。

仅选定update诊断扩展metadata：env/reset_count（联合episode身份）、pose index、
rollout step；汇总每episode/pose/family计数、10bin时间位置及eligible/selected差。
不改变first/uniform_rollout索引、coefficient或更新；不能称实现了均衡采样。
丢弃原因仅区分ineligible mask和selection/sample limit，未分解各predicate，
缺metadata明确标missing，不反推历史数据。设备采集，update结束时汇总。

一次资源inventory新增memory.total/memory.used/utilization.gpu及并发提示，
缺字段null，不改变exclusive/shared授权、进程匹配或资源准入。不抢占任务。

## 验证与限制

全量CPU pytest命令见AGENTS，本轮415 passed（17.68秒）；121个Python文件AST
语法检查通过，git diff --check通过。prepared v4 plan-only返回
READY_NEEDS_AUTH/AUTHORIZATION_MISSING，未创建output，spec/ledger SHA未变。
fixture覆盖状态顺序、
终态不可回退、握手观察、跨task拒绝、命名、sample coverage和wrapper不提交。
未运行新Isaac验证，UNKNOWN runtime吞吐与真实GPU状态事件投递可靠性。
历史评价、checkpoint、ledger及冻结快照不被覆盖；工程修复不是学习收益。

本轮文件：tools/run_state.py、motion_batch.py、recovery_batch.py、entrypoints.py、
health_check.py、evaluate_checkpoint.py；domain/evaluation_requests.py、
experiment_naming.py、episode_result.py、selected_diagnostics.py；stand_chain.py、
train.py；scripts/{submit_motion_high_speed_formal,continue_motion_high_speed_submission,
create_motion_retention_ab_20261006,create_retention_spec,make_retention_reeval_spec,
prepare_motion_course_plan,prepare_motion_recheck_20261007,prepare_recovery_hold,
prepare_recovery_coverage,report_motion_recheck_20261007,review_recovery_settling,
watch_recovery_submission}.py；tests/test_run_state_requests_naming.py、
test_entrypoint_catalog.py、test_recovery_coverage.py、test_health_submission_followup.py；
AGENTS、README、ARCHITECTURE、TOOL_INDEX、docs/EXPERIMENT_NAMING及本文。
