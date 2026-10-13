# Recovery动态课程：失触成本与工程停止后恢复 — 2026-10-12

## 已确认事实

11_42 B级已结算FAILED，smoke12＋formal185，共197次更新；此前A312，任务累计509更新、4,169,728 samples、3,696,930有效Actor样本、6046.626269秒。B100三组24/24确认入口、24/24完整窗口，但0/24证书；contact/saturation/vx（部分vy）失败。仍是教师前缀1.80秒的辅助后缀，非学生独立Swing恢复。

故障报告将runtime fault、initial_rejected、nonfinite reward合并。failure_tail只保存env0–7的最后32步，这些环境fault/rejected均为0、reward有限。其余56环境没有原始故障尾部，具体物理原因UNKNOWN；不能假称已经修复机械/初始化原因。此次增强证据并保留全部原保护，按用户新授权进行一次新attempt；再次工程异常仍停止，禁止自动重试。

## 本次唯一reward增量

在v9动态配方上新增v10入口后失触成本：
`−0.2 × entered × student_controlled × mean(clamp(relu((2N−wheel_contact)/2N),0,1)^2)` 分/秒，乘dt=.01一次。测量为传感器合力阈值，不认证法向载荷。入口前不生效，初始化/教师/工程fault不给学生reward。六项原奖励、角速度、零速Huber、弱镜像和轮平滑保持；不加滤波、制动、限矩或网络变化。

32条既有评分episode离线重放（24学生＋8教师）：B100各组新增累计成本每环境约−0.0465/−0.0491/−0.0470分；教师控制无学生任务成本。该量级核算不证明有效学习。重放可复用scripts/review_student_contact_cost.py，机器结果contact_replay.json保留evaluation/trace SHA。

## 来源与恢复语义

来源为已保存且同协议评估过的B100：
`runs/2026_10_12-11_42__recovery_course_b_prefix180_block0001/formal/model_update_100.pt`
SHA `cfb7e5175adc166f8fe72b307c471728e2ece1f8e4f11e2f50adbd02e5a547cb`。
只继承Actor及固定std；v10配方新Critic/PPO Adam/RNG、5次Critic warmup、smoke12。此为新配方，不冒称同配方精确续训。未保存的旧formal101–185不恢复，但实际85次更新与样本消耗保留。课程保留B1.80级与历史认证范围，不重跑A、不新BC。

新task复制历史结算并追加恢复来源/SHA、scope及dynamic_recipe；原manifest/账本/spec/checkpoint/evaluation不修改。后续同v10块恢复Actor/Critic/Adam/RNG/课程，不重复warmup；每块300formal/4小时/2GiB，累计无上限。原停滞、晋级、最终无教师认证与工程停止规则保持。

## 工程与验证

新增全环境pre-reset故障证据：runtime fault/rejection/nonfinite reward、env ID、closure/penetration/joint-outside、初始化年龄/settle dwell/速度/高度/pose/episode。不变更谓词与采样RNG，不只保存前8环境；保存异常附secondary，不能覆盖原异常。轻量每update记录contact raw/density/dt，选定smoke rollout记录同项。

共享CPU：34项课程/奖励针对性通过，最终23项真实runtime/新奖励/恢复通过。修改前全量901 passed/22 errors；修改后909 passed/22 errors，22项逐ID与基线完全一致，均既有Motion工程证书fixture SHA冲突。未降低生产SHA检查。实际冻结副本36 PORTABLE通过，schema/公共supervisor零写plan通过；verification.json列出基线和最终错误ID/SHA。

## 新声明与提交

Spec：`/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_12-13_29__recovery_course_b_prefix180_block0002/spec.json`
Run：`/home/kellen/wheel_leg_native_train/runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002`
Task：`/home/kellen/wheel_leg_native_train/isolated/recovery_course_contact_restart_20261012/task/task_manifest.json`

public check READY；physical GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`，shared显式批准，逻辑CUDA_VISIBLE_DEVICES=0。当前session绑定新manifest，无通知。未停止其他进程、未换卡。已调用公共supervisor一次提交；一次600秒有界握手返回SMOKE、submission_verified=true、worker身份OK，formal_first_update_verified=false、started=false。实际冻结执行副本全部模块SHA与已执行36 PORTABLE测试的副本一致，spec SHA与授权声明一致。不能把source/smoke当formal更新。后台owner负责预算、评估、结算和自动课程推进。

## 本轮修改文件

- `src/native_stand/students/course.py`
- `src/native_stand/students/course_io.py`
- `src/native_stand/students/course_requests.py`
- `src/native_stand/students/course_runtime.py`
- `src/native_stand/students/fault_evidence.py`
- `src/native_stand/students/recovery_task.py`
- `src/native_stand/students/training_recipe.py`
- `src/native_stand/students/training.py`
- `src/native_stand/recovery/runtime.py`
- `scripts/prepare_student_recovery_ppo.py`
- `scripts/review_student_contact_cost.py`
- `tests/test_student_contact_suffix.py`
- `tests/test_student_course_recovery.py`
- `tests/test_student_recovery_runtime_parent.py`
- `STATUS.md`
- `TOOL_INDEX.md`
- `WORKFLOW.md`
- `ARCHITECTURE.md`
- `docs/RECOVERY_STANDING_PLAN.md`
- `docs/RECOVERY_CONTACT_SUFFIX_RESTART_20261012.md`

本轮未commit/push、未改变旧run/模型/账本、未删除产物；CPU测试中的optimizer操作仅内存副本，未新BC训练。
