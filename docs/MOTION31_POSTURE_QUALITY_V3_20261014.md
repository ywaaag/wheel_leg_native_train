# Motion31姿态质量v3：纠正轻度偏差，终止严重坏姿态

用户明确同意质量优先规则，并授权“可以停止目前训练，新开一版”。本轮新任务设计不是纯工程修复；不把对照归因给单个惩罚，不保证快速收敛。

## 停止旧链与继承额度

19_43链按身份核验后，仅对本轮Motion trainer925064发送SIGTERM；既有monitor保存/结算。旧链正常STOPPED_BOUNDED，smoke49、formal0，加19_04已耗1次，总50次。累计父链墙钟1370.529508352秒；stop receipt：`artifacts/2026_10_14-19_55__motion_quality_stop/stop_receipt.json`。未停止其他任务、未改写旧run/spec/ledger。

新版：`configs/experiments/2026_10_14-20_04__motion31_posture_quality512_v3/spec.json`，run同名。新账本最多smoke50＋formal1900=1950次；历史50＋新增1950≤原2000次，不重置预算。剩余全链墙钟63429.470491648秒约17.62h，含来源/初始化/评估/清理，产物≤2GiB。

来源为原始迁移Actor：`isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt`，SHA `a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`。不从退化模型或旧smoke继续；Actor/std迁移，Motion49 Critic/Adam/seed重新建立，物理重新reset。旧来源不包含可恢复Motion Critic/Adam/RNG，不冒称完整恢复。每phase前5个critic warmup计入在线额度。

512env×128steps，L1：0/±0.5/±1m/s，固定槽128/96/96/96/96；GPU0 UUID`GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`共享→CUDA0。物理/USD/PD/限矩/动作scale/网络/PPO/LR/std/归一化不变，无retention/LQR/补偿，不解锁高速/yaw。

## 质量失败的冻结选择

显式reward `student_motion31_quality_reward_v3` 与termination `motion31_quality_termination_v1`，旧v1/v2路径保持。

| 状态量 | 持续偏差软门槛 | 极端硬门槛 |
|---|---:|---:|
| pitch绝对值 | zero 0.35rad；运动0.45rad | 0.70rad |
| roll绝对值 | 0.25rad | 0.50rad |
| 左右腿长差 | 0.05m | 0.10m |
| 轮心水平前后差 | 0.06m | 0.12m |
| hip/active镜像误差最大值 | 0.30rad | 0.60rad |
| 实际root高度 | [0.26,0.42]m以外 | [0.20,0.50]m以外 |
| 两轮同时支撑力≤2N | 持续0.20秒 | 不因单个瞬态立即终止 |

正常受控有效步骤的前0.5秒只豁免软门槛计时，给初始化后的纠正机会；软超限须同一原因连续0.25秒（失去双支撑0.20秒），恢复后该原因计时清零。极端硬超限在受控有效步立即终止，没有利用初始化owner给策略刷失败。单轮短时失触只作现有评分/诊断，不额外立刻终止。

门槛是本轮预先冻结选择，不是物理最优参数或已经验证的成功条件。允许加减速pitch lean，侧倾与几何失衡更严格。后续按真实失败原因分布判断，运行中不自动放宽。

质量失败只终止对应episode、reset回合法初态，不停止整场训练。非有限、闭链发散、初始化/控制身份错误仍属于runtime故障，停止本attempt。质量不足不拒绝进入学习。

## 奖励：不给差姿态长期累计得分

保留原tracking/支撑/高度/upright权重、宽窄核和Huber速度尾部；镜像、轮心差、腿长差改为同scale/weight的非饱和Huber，不再使用有界`x²/(1+x²)`。Huber近零曲率与旧函数不同，这是显式配方变化，不宣称只是强制检查。

新增两项density：pitch超过0.10rad后的Huber（scale0.20rad，weight−0.5），roll超过0.05rad后的Huber（scale0.10rad，weight−0.5）。只对受控/有效/未失败样本生效，density统一乘0.01秒一次。

真实物理/task质量失败步停止正向密集收益，另给一次−1事件惩罚，不乘dt；runtime故障不当作普通学习失败。所有此前失败前transition仍保留，失败步pre-action actor-valid保持，不能通过删除坏样本隐藏负回报。true terminated不bootstrap，正常timeout才bootstrap；若同一步有质量失败和timeout，terminated优先。

宽核至少25%与非饱和速度尾部保留；精修除了原tracking/物理/source姿态条件，还必须通过新的roll、腿长、轮心、镜像质量gate。没有实际通过证据不缩窄。失败事件−1与连续dt贡献分开统计，TensorBoard total是真实二者之和。

## 验收和采集

新protocol `motion31_quality_assessment_v2`，保留原30秒完整流程、tracking/parking/物理/source姿态检查，加保持段roll mean≤0.10rad、p95≤0.20rad、腿长差MAE≤0.02m、轮心差MAE≤0.04m、两镜像误差MAE≤0.10rad。仍不宣称完整精细站立认证；运动pitch继续按原tilt及source guard报告。

新源评估必须重新采集，旧协议完整来源仅作对照，不能授予新质量通过。后台 source→smoke50（真实更新/失败或正常timeout/reset/保存读回，不要求已学会质量）→新wiring校验→formal≤1900；每100次完整五命令，1900终点；两次完整通过可有界提前结束。旧能力保留/异常/存储/预算仍由后台判断，worker不轮询。

逐原因保存质量终止计数和pre-reset bool cause snapshot；顺序为pitch、roll、leg_length_difference、wheel_offset、joint_mirror、height、lost_support。质量snapshot在reset后保持，下一step覆盖，不从替换episode解释失败。

必要姿态/几何/评分证据全部保存。源/smoke zero保留完整网络诊断；其他命令保留control、31D actor及所有评分数据；formal中间保留评分/几何，终点完整。保守未压缩全链含temporary/terminal reserve为1,863,314,432bytes，低于2GiB，不以压缩比例保证通过。原始评估、reward snapshot和关键失败窗口保留，不反复复制源码或巨型数组报告。

## 验证与启动证据

- 全PORTABLE：441 passed、8 skipped（之后新增存储边界测试由最终绑定CPU覆盖）。
- 最终绑定CPU含质量timer/真实runtime方法AST/真实PPO失败storage、bootstrap、reward曲线和来源Actor/Adam/std初始化；结果在`artifacts/2026_10_14-20_04__motion31_posture_quality512_v3/cpu_storage_final/validation_result.json`。
- 最终preflight PASS、零写plan PASS，未压缩全链storage plan同名artifacts `whole_chain_storage_plan.json`。
- 实际奖励曲线/状态误差导数及源码/spec/source SHA：同名artifacts `reward_snapshot_authorized.json`；各phase在AppLauncher前再次保存绑定启动身份的snapshot。
- CPU reward导数不是Actor实际梯度；新终止规则尚缺真实物理smoke/学习效果，不预称解决姿态退化。
- 一次30秒supervisor启动握手：同名artifacts `submission_handshake.json`，SOURCE_EVAL不是formal首更新。当前owner`191bacc3-e5c7-4b8f-ae3d-5677eada837b`，既有后台结算/终态通知，TensorBoard6006。
- 实际握手：worker943877，submitted/submission_verified=true、current_stage=source_eval、state=SOURCE_EVAL，formal_first_update_verified=false；后台来源→smoke→formal，不由worker轮询。TensorBoard HTTP一次验证200，bridge945666/945667，新声明Text分组已写入，曲线只在真实metrics产生后出现。

## 本轮修改文件

- `src/native_stand/students/motion_quality.py`：纯数据质量timer、非饱和成本、事件与质量评分。
- `src/native_stand/students/motion_quality_runtime.py`：v3 runtime包装，pre-reset/task failure/timeout接线。
- `src/native_stand/students/motion_quality_budget.py`：已结算历史消耗只读核验和single claim。
- `src/native_stand/students/motion_tracking_reward.py`：显式v3、动态字段声明，旧版本保留。
- `src/native_stand/students/motion_training.py`、`motion_training_requests.py`、`requests.py`：独立质量protocol/版本/预算校验。
- `src/native_stand/students/evaluator.py`：v3派发、质量cause及完整独立评分。
- `src/native_stand/students/motion_runner.py`：16字段/事件/逐原因GPU汇总，真实总reward。
- `src/native_stand/students/motion_refinement.py`：新质量gate不得被精修忽略。
- `src/native_stand/students/motion_reward_audit.py`：实际v3曲线及新增权重。
- `src/native_stand/students/motion_statistics.py`：task failure标签区分runtime fault。
- `src/native_stand/students/training.py`：保留必要control/geometry/quality证据、减少重复网络轨迹。
- `src/native_stand/command_v6/tools/metrics_tensorboard.py`：连续reward/含事件total分离。
- `src/native_stand/command_v6/tools/storage_budget.py`：对应v3字段和全链产物估算。
- `src/native_stand/command_v6/stand_chain.py`：终态累计含历史50次及墙钟。
- `scripts/prepare_motion31_training.py`：同一准备器显式v3及历史消耗参数。
- `tests/test_motion_quality.py`：CPU回归。
- `AGENTS.md`、`STATUS.md`、`TOOL_INDEX.md`及本文。未提交Git。
