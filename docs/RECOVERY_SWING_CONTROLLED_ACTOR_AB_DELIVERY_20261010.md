# Swing-only受控actor与腿输出初始化A/B交付 — 2026-10-10

用户明确授权两臂各source_eval≤900秒、smoke10≤900秒、formal100≤3500秒，全链各5400秒/合计10800秒，合计220在线更新1802240原始transition。GPU0共享、顺序A→B，失败无重试/追加，不借历史余额；A终态唤醒后按此授权核验首次提交B。

## 已完成源码与语义

公共course接受空retained；sampling/assessment均Swing唯一family，64/64环境、weight1。source_eval和formal只评Swing，smoke要求有效初始化completed episode而非先学会；candidate gate缺实际rows仍不通过。旧组不分配槽位、不在线评估、不作为retention stop；禁用来源课程恢复及原Swing进展退化提前stop。最终同episode起身后10秒保持协议未改，60°全程终止和.18rad站立阈值区分，机械40/5.5Nm与原USD/PD不变。

Recovery专用ControlledPPO默认关闭。pre-action actor_valid由INITIALIZING/initialization_checked取得，失败末步仍有效；训练元数据作为storage TensorDict独立bool字段，不在网络obs_groups中，150D保持。GAE/returns保留完整原时间轴及timeout处理，重新按全rollout有效样本advantage统计归一；surrogate/entropy/KL/clip只读有效样本。全invalid minibatch仅critic loss，actor.grad=None避免Adam momentum推动，actor/critic无共享参数显式拒绝。仅支持当前fixed/feedforward/noRND/noaugmentation配置，未知组合拒绝。

mask随原storage shuffle索引，runtime核对存储valid样本数与pre-action统计一致。紧凑计数包含全部/受控/初始化、恢复与保持样本、actor step、左右长度、同刻≤.34m持续50ms事件、局部方向/clip/触限、接触/姿态/支撑方向/保持前缀与成功pulse。里程碑不是accepted，也不是恢复必要路径；预算内每臂formal受控25万为目标，不足不追加。未保存全训练轨迹，无额外actor采样/RNG。

## 既有数据复算

14_00 NPZ16384transition具名pre metadata，Swing6656/受控2504=37.62%，DrawBack6400/5400，R03328/3328。更新前ratio≈1 score surrogate梯度无控制/受控范数1.87046/0.30436；不含entropy/critic/Adam。audit入口scripts/audit_recovery_controlled_gradient.py，机器结果isolated/recovery_controlled_gradient_20261010/audit.json；未改原checkpoint，不称唯一因果根因。

## 初始化候选B

一次性确定性SLSQP约束最小参数变化，仅最后mlp.6四腿行与bias；同隐层/轮行/std/critic/完整Adam逐项保持。读取真实pre_joint_pos具名四腿、early .01–.04秒对应preaction，目标q_pre+.10[+,+,−,+]按原reference/1.6编码。该方向是局部几何先验不是成功示教，runtime无偏置或再次应用初始化。

来源checkpoint SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c，谱系parent为10_58自身formal/source_snapshot/spec.json SHA085487d9d538bede323d899ec0262398a58dbb8f6c2040146791d028af28751f。数据14_00 evaluation与NPZ SHA分别817a3a2090a34ece3bb69941f1d77f29b422eddebf3cb68cdf32f5e488040ba9/b35d9863f4630895df9ca512702ef6c982c8ea7105a92a410247dca4af9db7e7。

B候选isolated/recovery_swing_leg_initialization_qualified_20261010/initialization_candidate.pt，SHA d074488410257e02b44704f8b2119612617cf44267c50d6e4561f72d39a9ab51；标trained=false，保留原update/spec训练谱系，公共loader识别未训练初始化source、不伪造PPO历史。calibration269样本71episode groups/holdout63样本18groups，anchors1725条旧组保持输入；校准最大误差.029990315rad、锚点RMS.049989998rad，solver每通道收敛。留出最大.030043077rad，超过.03，明确不是通过留出门槛或独立泛化证据。内部求解余量更严，最终门槛不放宽。

四腿局部方向Gaussian联合概率44.325%，非真实收腿/起身成功率；各通道clip概率、残差/iterations/数据SHA在report.json。early mean动作包络和USD authored active limits通过；Gaussian尾仍可被原环境clip，不能声称全状态无裁剪。limits_identity.json绑定joint/schema SHA。早期探索mean发生实质变化，后续由同一策略自由学习。

## 配方、声明和验证

奖励完全来自21_58 formal冻结配方（含support record beta.3和位置×镜像引导），parent/checkpoint仍10_58。reward_recipe_source显式绑定路径SHA；不拆P×S、不删record、不加权。A/B差异只在初始化source身份及实验/姿态库输出路径；reward/ppo/control/std/采样/seed同一。seed20261010、restore_source_rng=false、restore_recovery_curriculum=false，不是独立训练seed。source_eval/smoke/formal均加载该臂同一source，formal不接smoke末尾。

当前有效config：2026_10_10-14_18__recovery_swing_controlled_actor_a及_b；各spec/budget/poses/manifest/publication/authorization_receipt。此前14_13准备声明未授权、不提交（发现旧课程restore默认后另立新声明，旧产物不覆盖）。评估点source PPO0基线、formal25/50/100，checkpoint每25/full每50及指定点，保留来源和早期候选，run_final_durability=false。

针对性24 tests通过，共享提交/通知边界50通过；最终冻结每臂8 PORTABLE通过/strict初始化。完整pytest732 passed/22 errors/2 warnings：22均定位Motion工程恢复certificate fixture拒绝既存runtime/configure.py，当前SHA c6db5373a6371a1c6dec8437c52b24ee8a2b4708b826339c3d4bd2b15f1b76e5与21_58 frozen副本相同，本轮未改，未绕过Motion证书。后续新增紧凑diag及chain墙钟路径已做对应targeted/frozen验证，不将全suite错误豁免成通过。

CPU optimizer仅测试内存副本，无在线预算消耗、checkpoint未改。allvalid实际PPO/GAE/update/RNG一致；无效动作不影响actor更新、无效adv不污染valid归一；两rollout/reset/done、mask重排/缺失、allinvalid有Adam momentum后actor及state完全不变、参数分离均有测试。实际runtime mask优化读回仍待smoke，wiring要求非零valid与真实optimizer事件、计数一致，缺项阻断formal。

## 提交状态

公共授权已登记两臂，A check-submission READY，一次supervisor提交/5秒有界握手SOURCE_EVAL、worker身份OK，formal首更新未核验。B已授权未提交，按本轮完整授权待A终态事件唤醒后只读复盘，重新核验GPU资源/身份/session/输出/ledger再首次提交；不新增watcher/不循环查log/PID/GPU。物理GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72逻辑cuda0，共享不停止他人，提交前盘约19GiB/ GPU127MiB瞬时，仅此快照。

existing owner按hash report_ready及at-most-once终态通知session7bbabd67-183d-4185-b686-1aefcd55781b。source/smoke提交不是formal首更新或能力通过。A/B结束后回答初始化是否保留、是否实际双侧收短、卡在方向/支撑/落地/保持哪一步；两支没跨瓶颈不自动长训。

## 精确文件

新增recovery/controlled_ppo.py、initialization_candidate.py、swing_training_diagnostics.py；scripts/audit_recovery_controlled_gradient.py、prepare_recovery_leg_initialization.py、prepare_recovery_swing_actor_ab.py；tests/test_recovery_controlled_ppo.py、test_recovery_swing_only.py。修改command_v6/domain/recovery_course.py、tools/prepare_recovery_course.py、tools/checkpoint_input.py、train.py、wiring.py、stand_chain.py、recovery/validation.py。文档仅STATUS状态、TOOL_INDEX命令、ARCHITECTURE结构、Recovery plan本轮决策与本交付报告。新candidate/config/artifact/isolated输出，旧run/checkpoint/evaluation/ledger及Motion代码、外部项目不改，无commit/push。
