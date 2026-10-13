# Recovery：Actor时间平滑A/B执行 — 2026-10-12

## 决策与原始状态

按新版RECOVERY_STANDING_PLAN第7节执行有限A/B，当前前缀固定1.80秒，不推进更难级，不同时改对称、reward、PD、std或观测。v10上一块smoke12/formal300已COMPLETED，update200/300全部未完成保持；保留update100。原owner续块14_54因状态机SOURCE_EVAL→FORMAL不允许而FAILED，formal0；历史task ENGINEERING_STOP保持只读。新task继承821更新、6,725,632 samples、5,606,334有效Actor样本、432评分episode、11273.390633秒，不重置用量。

## 接线与唯一对照变量

来源：runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt，SHA bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d。

A/B恢复同一Actor、Critic、Adam16个状态与训练RNG。reward仍v10，recipe仅里程碑50/100用于本对照；不重新初始化Critic，不重复warmup，每臂重新smoke12。smoke与formal各自从同一来源完整状态开始。原物理31D/40D/尺度/限矩/BC0保持。B新增loss 0.01×mean(((100μwheel(o_t)−100μwheel(o_t−1))/10)^2)，A系数0。

有效对必须同env/episode、相邻10ms、两步学生控制且首次入口后、不跨terminal/reset/交接/评估重建。每minibatch最多256对，从独立generator抽样；两侧当前mean参与梯度，obs detached。直接actor.mean不修改distribution缓存、不采样policy动作。记录term、配对数、加权正则梯度范数及总Actor/Critic梯度。空学生mask跳过所有优化，BC仍0。

ControlledPPO默认None保持旧路径，新增hook只显式A/B启用。checkpoint记录aux配置，学生严格load继续绑定原recipe及接口。source迁移核验完整phase manifest/全部旧冻结模块/资产/reward/control/PPO/SHA；不是通过放宽普通continuation校验加载旧源码CP。两臂显式绑定共同新执行SHA，B前有漂移则拒绝。

## 续块状态机修复

SOURCE_EVAL→FORMAL只有在verify_continuation实际验证既有smoke/完整resume身份后，传入版本化证据才能转换；普通transition仍拒绝。真实chain CPU回归证明source→formal顺序及持久化proof。无需伪造新smoke阶段，不更改旧FAILED。

## 声明与预算

A：/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_12-20_49__recovery_wheel_temporal_a_from100/spec.json
B：/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_12-20_49__recovery_wheel_temporal_b_from100/spec.json
Task：/home/kellen/wheel_leg_native_train/isolated/recovery_temporal_ab_20261012/final_task/task_manifest.json
每臂smoke12＋formal100，112updates／917,504 samples，source900s＋smoke900s＋formal12600s，chain≤14400s，2GiB；两臂合计最多224updates／1,835,008 samples／28800s／4GiB。这是原持续授权下有限对照，不将总授权改为224上限。

source评估当前后缀24＋normal24＋独立Swing8＋teacher8；formal50/100评估后缀24＋normal24＋Swing8，smoke末后缀8。来源、50、100及A/B使用同一声明case/seed。8环境是重复评估，不冒称独立training seed。完整固定窗口与共同首2秒分别比较，失败/不完整留分母，不以早倒换平滑指标。

preparation.json对应早期未授权声明；最终仅final_preparation.json与final_task用于运行。早期声明零attempt、未授权，保留不删除。

## 验证与提交

修改前全量911pass/22errors，最终919pass/22逐ID同基线；22相关边界测试通过（含真实source phase receipt），A/B实际冻结副本各30 PORTABLE通过。真实ControlledPPO内存副本证明A与原PPO逐参数一致，B有非零正则梯度、policy RNG一致、distribution缓存不变；无在线PPO计入CPU测试。源参数/历史证据只读。机器结果verification.json、final_regression.txt、release_cpu.txt、frozen_A_release.json、frozen_B_release.json。

公共A check PASS/READY，GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，共享显式批准，逻辑CUDA_VISIBLE_DEVICES=0；一次快照可用32333MiB，不能推断后续持续空闲。一次30秒有界握手SOURCE_EVAL，submission_verified=True，formal_first_update_verified=False。真实A冻结模块与测试副本逐SHA一致。此时只确认source阶段，未声称实际optimizer已恢复或PPO已更新。

既有stand_chain owner在A正常COMPLETED结算后首次授权/资源核验/提交B；A工程故障或用户停止阻断B。每臂独立账本；B结束生成comparison.json并停止本有限对照，不自动调lambda或追加长训。比较模块保存normal/后缀/Swing分组及逐env完整窗口、共同首2秒的实际轮目标RMS、触限、姿态、速度和接触，要求人工核准收益。原完整Recovery尚未通过。

## 文件职责

新增students/temporal.py（纯配对与mean loss）、temporal_ab_io.py（公共准备/授权/owner串行调度）、temporal_review.py（离线比较）。ControlledPPO增加可选hook；students/training接入配对/完整恢复/评估/存储；course_io/course_requests/requests严格消费A/B声明；model/ppo/training_evidence记录checkpoint和真实smoke恢复。tools/run_state与stand_chain修复受验证续块转换。新增test_student_temporal、test_student_temporal_owner、test_student_temporal_public。公共命令TOOL_INDEX、结构ARCHITECTURE、流程WORKFLOW、状态STATUS、Recovery计划仅补本次执行入口。无commit/push、未停其他任务、未改USD/限矩、未删除历史产物。
