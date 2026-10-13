# 学生抬升后支撑事件与B250局部教学探测准备

当前结论：同一个31D Recovery学生已经会收腿并抬升，但未完成站立入口；下一先测真实动态状态能否被教师接住，不能继续将教师救场当作学生完整自主恢复。

本轮只做已有数据离线分析、CPU工程和新声明准备。新增仿真/PPO/BC优化均0，未修改历史run/checkpoint/spec/ledger/evaluation或冻结代码。

## 1. 已有支撑事件证据

来源为15_25 lift_rate_v3的formal new100与同轮source_eval原生B50→B250成功组合。学生原生＋三小yaw组共32首episode，教师原生8首episode。evaluation/trace/checkpoint及冻结几何源码SHA绑定，recovery_policy_trace_v1具名字段，实际受控首动作后的状态记作.01秒；不将程序时间或初始化时间当Recovery执行时间。

选定第一次抬升峰值：高度≥.35m的首个局部峰，随后50ms内下降>2mm；找不到则取前2.5秒最高点。该定义仅用于离线事件对齐，不作为新运行触发器或评分。

|事件（均值）|教师8episode|学生32episode|
|---|---:|---:|
|第一次抬升峰值时刻|.750s|.457s|
|该峰值高度|.384m|.418m|
|峰值后首次低于.30m|.930s|.630s|
|低于.30m时两腿长度|.223/.265m|.314/.368m|
|同刻左右接触合力|147.6/160.5N|59.5/45.4N|
|峰值后pitch首次>.10rad|1.050s|.553s|
|峰值后两轮目标首次均为正|1.020s|.582s|
|完整入口与保持通过|8/8|0/32|

教师也会腾空且短暂低于.30m，成功依赖随后重新支撑和收稳。因此“腾空”“回落到.30以下”不能单独判为恢复必然失败。保持gate仅在首次入口之后使用，不擅自套到动态过渡。

学生回落时右腿明显更长，没有出现教师的双侧重新收短构型。轮心相对root的body坐标（不是COM）也不同：下降到.30m时，教师左右body Z约−.067/−.112m，学生约−.172/−.203m；native前向为−bodyZ，学生轮心在该轴上更靠前。左右纵向差本身并未比教师更大，不能只归因于剪刀腿。

这些是事件和构型关联，不是哪个动作导致失稳的唯一因果证明；100Hz力矩记录不是完整200Hz PD/1kHz物理审计，接触为传感器合力而非法向载荷。

机器证据：isolated/student_support_loss_verified_20261011/support_loss.json，逐episode峰值、回落、pitch、轮目标、接触、root-relative轮心、q和requested/applied torque均保存。脚本scripts/review_student_support_loss.py可只读重现。

## 2. 真实接管接口已增量接通

旧HandoffEnv默认Recovery尺度1.6rad，不能直接解释学生1.5rad输出。新StudentMotionProbeEnv复用同一个HandoffEnv/CommandEnv/PD路径，显式prefix_leg_scale=1.5；旧Handoff默认1.6不变，Motion阶段始终.5rad/100rad/s。

学生收到31D本体当前输入、Recovery/NONE、[0,0,.40]命令，前缀全程自身Actor；B250由自己的冻结spec构造，原生25D＋125D历史持续更新，Motion命令[0,0,.40]。两者不共享归一化action或历史。Motion前一实际执行目标按.5rad/100rad/s编码，超包络原始值/裁剪/信息损失逐步保存。

切换按合法初始化后执行完N个学生interval，下一个interval由B250控制；不reset、不清root/joint速度、不重写姿态、不托举、不更换USD或控制参数、不做blend。初始化控制、学生控制、Motion控制分别记0/3/2，actor_valid只标学生实际控制，Motion动作不伪装为学生on-policy样本。本轮无optimizer。

每条件从声明初态重新物理运行学生前缀，不从旧trace拼PhysX状态。第一episode失败仍计入8环境分母，不接受reset后的后续成功。真实USD/闭链/非有限/严重穿透/全程大倾角保护保留，切换不套旧Motion低高度/腿角任务终止。HandoffClock取代自主学生2.5秒入口任务时钟；Motion接管后给2秒入口、.20秒连续确认、之后固定10秒，使用原组合协议完整保持。教师救场成功明确student_independent_accepted=false。

每步保存student31D、Motion当前frame/5帧history、previous action原始编码/裁剪/信息损失、root/q/dq前后状态、controller/switch、初始化/总受控/Motion时钟、prefix计数、raw/mean及control requested/clipped/applied torque，切换目标跳变与失败阶段。Motion模型、学生参数和std前后逐项不变，评估退出恢复模型模式/RNG。

通过现有students evaluator→公开supervisor --evaluation-only→既有monitor精确预留和结算；新evaluation版本student_motion_probe_v1严格拒绝未知字段和在线训练请求。不新增trainer、launcher或watcher。旧学生独立评估与旧legacy接管协议保持。

## 3. 新探测声明：9组72评分episode

1. B250自己的正常站姿、统一限位USD零速基线，8评分环境；8/8通过才扩大。
2. 原生Swing→冻结B50 .50秒→B250组合对照，8环境。
3. 15_25 new100分别执行.30/.40/.45/.50/.55/.60/.65秒，再交B250，七组各8环境。

时间点围绕本轮观测的上升、峰值、pitch转正和回落选择，是有限条件探测，不是部署固定时钟或已认证状态分类器。仅原生Swing，一个声明seed20261010；8评分环境为并行重复，不宣称广泛扰动、独立training seed或地形泛化。

正常基线失败后其他条件保持NOT_RUN，不自动换模型/旧USD/门槛。正常基线通过后，普通学生接管能力失败继续剩余矩阵；runtime/初始化/身份/证据故障或预算耗尽停止并保留INCOMPLETE/NOT_RUN，不自动重试。

每组64仿真环境、8评分环境；分别记录all_simulated_env_steps和scored_env_steps。最多72评分episode，PPO=0、offline optimizer=0，墙钟≤1800秒含初始化/评估/清理，输出≤512MiB。最长条件时长由组合协议duration统一推导，最大13.67秒，避免旧13.52 episode截断最后保持区间。

来源学生：runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc/formal/model_update_100.pt，SHA e5f137d4afb89fde99017f7eb34208a0844b545af1ad049611f844d17796e810；冻结parent spec SHA61e612a1af2e1730a5fb77bc83e3faf41bd03d6a1794a3e4c20b0bab16f4f3ac。它是未accepted实验候选，不是新的最优起身模型。

Motion B250 SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e，原资产不同，本轮基线重新在统一限位USD上验证；B50对照SHA46add82fa9d32c04fcc0a8b79c6339a27df3b9ca6c95050b8e13f52b644b7f75。

新声明：configs/experiments/2026_10_11-16_21__student100_motion_b250_local_probe_ppo0/spec.json，独立budget/poses/完整发布标记。UNAUTHORIZED、所有used0、attempts空、无run。公共零写plan仅缺新仿真授权，当前不提交。拟使用物理GPU0共享，真正提交前核验UUID、current session、CUDA映射、磁盘与资源，不停止其他任务、不换卡。

## 4. CPU验证与下一分支

真实公共planner严格消费9case及31D来源，checkpoint parent/spec SHA、原生正常初态来源读回已验证。真实共享父类构造/前置动作/dones覆盖学生前缀与Motion边界；10interval学生.2输出产生.3rad目标，随后Motion同归一化值产生.1rad，切换不写root或速度；旧legacy默认.32rad仍验证。

执行型CPU rollout验证50prefix＋20entry＋1000hold、历史连续刷新一次、.40Motion命令、单控制者、first-episode失败分母、Motion首interval时钟.01s、模式/RNG恢复；真实公共evaluate调用的基线失败→其余NOT_RUN也覆盖。冻结只执行PORTABLE，不把张量物理fixture称Isaac验证。

某条件被接住：确认该固定组合下的局部教学范围，下一先验证邻近状态，再补该局部恢复/落地示教给同一个学生，不把Motion长期运行当Recovery成功。

所有条件失败但基线正常：按目标跳变、动量、构型或接触失败选择下一变量；不默认B250能给任意Swing状态正确标签。若故障主导，不解释成学习失败。

不因本次准备就训练接管分类器、加GRU或短历史，不改reward/PD/std，不自动续new100。命令仅维护TOOL_INDEX，状态维护STATUS。


最终验证：43相关CPU通过、27冻结PORTABLE通过；全量840passed/22errors，与本轮前基线22项错误ID及configure SHA fixture原因逐项相同。一次新增失败来自旧测试硬编码字符串“.5,1.6”，已改为核验默认1.6的AST并补真实动作解码回归；未放宽生产SHA或改历史证据。共享源码/最终冻结副本逐文件SHA无漂移。机器交付isolated/student_motion_probe_preparation_20261011/delivery.json，最终验证artifacts/student_motion_probe_delivery_cpu_20261011。

本轮修改文件：新增scripts/review_student_support_loss.py、scripts/prepare_student_motion_probe.py；新增students/handoff_probe.py、handoff_runtime.py、handoff_rollout.py；修改students/requests.py、evaluator.py以及共享recovery/handoff_runtime.py（旧默认尺度保留）；新增test_student_motion_probe.py、test_student_motion_probe_public.py，扩展test_student_recovery_runtime_parent.py及test_recovery_handoff_interfaces.py。文档为本复盘、STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX、ARCHITECTURE；新声明目录16_21独立发布，历史产物未改，无commit/push。


## 2026-10-11 16_21已授权尝试：工程失败及reset契约修复

用户授权后公共supervisor共享GPU0提交一次，attempt `9b5470e6d0cb422fafcce8e7ab509d0f`，终态FAILED。账本evaluate已使用1次，墙钟5.3704秒，在线PPO/离线optimizer均0；正常站姿case0为INCOMPLETE，其余8组NOT_RUN，无完整评分episode或能力结论。GPU0 UUID为GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES=0映射cuda:0。历史run/spec/ledger/快照保留。

失败为`Unknown evaluation family`：motion_native_normal存在于姿态库，但来源的显式Swing-only sampler拒绝该family。这是评估reset配置缺陷，不能归为B250行为失败。

修复students.requests.evaluation_recovery：从已声明case生成独立的单family评估sampling/assessment，关闭评估课程晋级，不改训练配置。public preflight和准备器先调用真实sample_poses核验有效holdout；evaluator在共享环境构造前安装该契约，并保存effective读回。缺family/无效pose仍拒绝。补真实HandoffEnv→RecoveryEnv reset测试及原反例；公共测试不再依赖已消耗历史账本仍未授权的假设。Kit清理前先保存终态、恢复RNG及cleanup，再按工程失败返回退出码1，避免默认close以0退出。

针对性31通过，冻结PORTABLE20通过；全CPU842通过/22errors，22项错误ID和configure.py fixture原因与修复前逐项一致，configure.py SHA未变。不放宽SHA、不修改Motion或旧工程证书。共享/冻结输入SHA核验无漂移。机器复盘、测试和零写plan：isolated/student_motion_probe_resetfix_20261011；冻结包artifacts/student_motion_probe_resetfix_cpu_20261011。

新独立声明：configs/experiments/2026_10_11-16_43__student100_motion_b250_local_probe_resetfix_ppo0/spec.json，SHA c61d7beef3336d6b6e34bf826e877b2d0e7dcc291134c02dac9c0509dce3b23b。budget保持UNAUTHORIZED、zero used、零attempt、无run。9组/72评分episode/64仿真env/PPO0/1800秒/512MiB范围不变；新重试需明确授权，原失败额度不重置、不自动重试。正常站姿8/8后才扩大扫描。此处仍只测局部教学可接管性，不将教师救场算学生独立起身。

本次修复文件：students/requests.py、students/evaluator.py、scripts/prepare_student_motion_probe.py；tests/test_student_motion_probe.py、test_student_motion_probe_public.py、test_student_recovery_runtime_parent.py；本报告、STATUS、Recovery计划、TOOL_INDEX、ARCHITECTURE以及新16_43声明/独立验证产物。未新训练、未commit/push。
