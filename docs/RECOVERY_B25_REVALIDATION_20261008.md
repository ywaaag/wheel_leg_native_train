# B25冻结复验与通向Swing的准备

用户明确批准执行B25三seed/双初态PPO0复验，并希望尽快进入Swing。
已重读最新AGENTS/README；按RECOVERY_STANDING_PLAN第9/10节，先复验完整候选，再扩合法DrawBack小扰动，再设计Swing，不把未认证新难度加入本次请求。

配置根：2026_10_8-12_12__recovery_b25_three_seed_ppo0；独立授权evaluate=1、PPO=0，墙钟上限1800秒包括初始化/保存/清理。
checkpoint为P2 B/formal/model_update_25.pt，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。
六项请求：seed104/205/306各DrawBack及R0，8env/组，同一minimum-height协议，观察上限23秒，首入口后完整10秒。
GPU0共享，无停止其他进程；只通过supervisor evaluation-only提交，前台等待自有有界evaluation monitor，不轮询长训。

工具准备时发现继承full_trace_updates=[25,50,100]与PPO0 formal_updates=0冲突，prepare_checkpoint_diagnostic现在清空旧training milestone列表，保存范围由各request full_transition声明。
共享最小修改与回归：src/native_stand/command_v6/tools/prepare_checkpoint_diagnostic.py、tests/test_recovery_geometry_request.py；旧source/spec/raw不改。
工具自身的默认发布仍UNAUTHORIZED，本次另按用户批准登记新预算和session。

初始化覆盖限制：当前holdout_sampling=balanced_pose_cycle，seed不一定生成不同初态；须比较真实pose ID、初始state/control轨迹，不能单凭三seed标签称独立泛化。
未三seed通过前不训练新课程。即使通过，也需新pose的真实初始化证据；几何通过不代替PhysX沉降和策略通过。

同步准备6个±.01rad的小幅镜像DrawBack几何候选，复用实际捕获关节、当前USD、闭链分支，根高度只由理想最低碰撞间隙推导。
[离线候选](../isolated/2026_10_8-12_12__recovery_b25_three_seed_ppo0_drawback_small_perturbations/candidates.json)：6/6离线闭链/限位通过，root约.16847–.17016m；runtime/策略能力UNKNOWN。
这些仅准备下一小扰动初态，不是Swing，未改变本次模型、姿态库或请求，也未启动额外模拟/PPO。

本次结果将在自有evaluation monitor退出后读取一次并记录；无自动耐久、重复评估或PPO追加。

## 实际完成结果

六项全部COMPLETED/accepted：seed104/205/306各DrawBack8/8与R0 8/8，共48条完整10秒first-episode证书。
模型SHA相同，未更新权重；双轮接触100%，采样触限0%，高度/mean及peak姿态/闭链全部按逐环境gate通过。
[完整复验审查](../isolated/recovery_b25_three_seed_review_20261008/review.json)。
实际attempt 5845f022bf544fc49cf2723e6d13c064；terminal墙钟401.5378秒，monitor退出后结算402.0458秒（约6.70分钟），evaluate used1，PPO/optimizer updates0。

覆盖审查：R0三个seed初始化逐字节相同，属于重复性；DrawBack同一pose ID，首次样本主动q差异最大4.91e-5rad、root pose最大2.62e-6，force差约1.43N。
初始化完整轨迹的hash部分不同，不代表新倒地姿态或独立training seed泛化。因此只能声明三seed运行均通过当前声明范围，不宣称随机姿态全面掌握。
初态差异是沉降/数值路径差异，未人为增加随机化或追溯修改协议。

## 下一步已准备，未运行

新未授权PPO0声明：configs/experiments/2026_10_8-13_15__recovery_b25_drawback_small_ppo0。
[Spec](../configs/experiments/2026_10_8-13_15__recovery_b25_drawback_small_ppo0/spec.json)：原DrawBack/R0＋6个±.01rad闭链合法DrawBack候选，8项目×8env，同B25，建议1200秒，PPO0。
新pose库保留原姿态并记录闭链/限位离线证据；根高度由理想碰撞最低点推导，runtime初始化与能力仍UNKNOWN。
supervisor evaluation-only plan：READY_NEEDS_AUTH/cpu_valid=true、8requests、零写、预算SHA未变、run不存在；见[plan](../isolated/recovery_b25_small_plan_20261008/plan.json)。
新预算仍UNAUTHORIZED，used0、attempts空；未借用本次复验余额，不启动小扰动或Swing模拟/PPO。
这一步通过后再扩大至可达Swing支撑组；若新增姿态行为失败但物理初始化合法，可准备该局部课程学习，无须强制先学会才训练。

本轮验证：准备器最小修复后的共享全量543 passed；冻结副本9 passed；入口/准备器专项16 passed，git diff --check通过。
精确共享改动：tools/prepare_checkpoint_diagnostic.py、tests/test_recovery_geometry_request.py、tools/entrypoints.py、TOOL_INDEX.md；新增scripts/review_recovery_revalidation.py及本文。
新增两套独立声明/pose候选与验证报告；STATUS和RECOVERY_STANDING_PLAN补结果导航。历史checkpoint、raw、账本结算记录保留，不删除/覆盖。
