# Recovery0.34m站立与对称专项（2026-10-12）

## 用户目标与授权

用户要求同一Recovery学生先从正常站姿站稳，强调双腿对称，允许不限累计训练（例如5000更新），随后明确高度为0.34m。新任务只训练normal，不自动转入动态后缀或Swing、不训练Motion/Jump。不把正常站姿通过冒充完整Recovery。

累计update_limit=null，每块formal300、4小时、2GiB，初块smoke12。5000不是伪造的无限上限：以至少5000formal作为停滞审查起点，持续有实质改善可以继续；通过或用户停止/工程故障时提前结束。5000后连续三块无实质改善，允许一次完整状态回退，再次三块停滞结束NEEDS_DESIGN；故障不自动重试。

本次明确绑定当前HAPI session和GPU0 shared，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72。通知关闭。不停止其他任务、不换卡，资源不足不启动。每块独立新spec/run/ledger，owner累计真实用量，不从旧余额扣除、不改历史任务。

## 参考Motion祖先的实际证据

已核对B250向前六级checkpoint谱系并逐SHA确认，最终random初始化祖先wide_leg_from_scratch_20261002_formal，stage0仅零命令。其update500旧协议站立8/8通过，整run最终FAILED（保存能力与最终生命周期不同）。旧资产SHA6bf6ce…a27，与当前限位USD32a56e…01b7不同，不能迁移旧证书。

Motion冻结代码实际奖励是up²(+2)、高度exp(-((h-command)/.06)²)(+2)、**联合**vx/vy/yaw Gaussian、双轮接触(+.5)、归一化effort(−.02)、action_delta(−.01)、腿绝对角离开.25rad区的joint_margin(−.05)，连续乘dt，terminal−1不乘dt。B250配置写tracking_mode=separate，但实际冻结domain_reward/runtime仍消费联合velocity_tracking权重8；不要仅凭配置字段宣称已训练分项tracking。

祖先动作腿.5rad、轮100rad/s；action_delta_wheel_factor=100/6约16.67，把轮差转换回6rad/s归一化坐标。不可把normalized action_delta系数原样复制到学生1.5rad/100rad/s后宣称相同物理成本。祖先终止包含低于.20m、up<.5、大body接触和腿任务范围.5rad；最后一个是旧任务边界，不是当前机械限位，不能给Swing直接套用。

祖先没有显式镜像reward，也没有严格左右对称验收。B250站稳不证明符合用户新对称要求。过去v6已做过Motion反馈加项，v7已替换零速Huber，不能当作尚未尝试的全新方案重做。

## 来源与精确变化

回退至正常专项v7 update300：runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/model_update_300.pt，SHA2a587c31bbf81f2db669561965431cc97598c9e13b87043553582b8a09237a9a；其自己的冻结spec作为parent。

来源normal三组24/24完成10秒，高度/水平/接触/速度/闭链通过，触限失败且未accepted；其中early_failure标志是完整证书失败，不全是提前摔倒。来源镜像MAE hip/active=.428/.412rad，P95=.468/.454rad，旧封顶成本在91.13%保持样本失去大误差辨别。

新recipe student_recovery_ppo_standing_mirror_huber_v11 / reward student_recovery_reward_standing_mirror_huber_v11，仅下列两项相对v7变化：

1. 用户高度目标0.34m：Actor命令高度输入=.34/.5=.68；slot0由饱和H改为exp(-((h-.34)/.04)²)，权重+2/秒。明确slot0新语义，其他连续项保持，不假称仍是height_progress。出生root/q/dq不改，保持合法normal reset，策略从原姿态自行调节。
2. 对称项：−.20×H×mean(Huber([left_hip+right_hip,left_active-right_active]/.20rad))/秒，Huberδ=1，无封顶。左右符号沿实际physical镜像定义，不强制左右action相等、不硬投影、不平均教师动作。

BC0，固定腿std.05rad/轮2rad/s；31D Actor128/64/32，40D Critic256/128/64，ELU、mean tanh；LR3e-5、64×128、4epoch/4minibatch、gamma.99/lam.95、clip.2/value.5/entropy.001/grad1保持。共享USD/Plane/PD60/2/1、1/5/10ms、40/5.5Nm、动作腿1.5/轮100不变。不加时间正则、运行滤波、Progress或历史。

本次并非全套复制Motion奖励：保留v7已经改善normal窗口的其他项，只修复对称大误差和用户新高度目标。固定轨迹重放仅核符号/单位，不证明策略将学会；B250旧.40m姿态会被新高度目标降分，不能视为.34m专家。

## 在线与离线完整验收

新协议student_standing_height034_symmetry_v1，不改旧评分。2.5秒内在.34±.02m并满足原入口姿态/接触/有效状态连续20样本，随后固定1000样本10秒，不重选窗口。

保留原height≥.30、pitch/roll mean≤.10/peak≤.15、tilt≤.18、双轮>2N、正净空、闭链≤5mm、policy采样触限≤5%、vx均绝对≤.5/vy≤.02/yaw≤.03等；增加高度MAE≤.02m、峰误差≤.04m，物理腿镜像两项MAE≤.05rad、P95≤.10rad。对称容差是新首轮工程目标，不声称数学完全相等。

StandingCertificate累计同一首窗口高度误差、1000×2镜像误差，只有高度/对称/原物理证书一起通过才发success_once。窗口结束不等于成功；均值与P95失败发任务失败，事件dt不重复。Actor输入不含height测量/阶段或教师ID，31D不变。student_interface内.40默认值是legacy默认命令，实际本实验通过recipe.target_height_m=.34显式覆盖并测试；其他旧模型路径不改。

每100更新评估当前normal三组24；每300再加第三yaw组共32、无教师Swing8回归。teacher B250正常native基线按其原生命令.40和旧组合协议单独核验；它不是新高度/对称证书。要求两次不同评估、至少一次更新间隔均24/24，且最终四组32/32，才accepted_standing_symmetry。accepted_full_recovery始终null，不自动晋级Swing。

## 续训与选模

初块Actor继承v7，Critic/Adam新建、前5update仅Critic；smoke/formal独立从同一来源开始。后续同配方恢复Actor/Critic/Adam/RNG/recipe_updates/课程状态，无重复smoke/warmup，环境真实重置记录，不声称PhysX恢复。

每块至少保存100/200/300及边界；评估保留source/latest/best与physical/symmetry分开。owner以联合通过数、物理通过、其他站立项、完整窗口、有效前缀、镜像和触限排序；不以更齐或reward高取代站稳。持续有收益才续训，有限回退从本专项最佳完整训练状态开始，不拿旧source_actor重置optimizer冒充resume。

## 工程故障取证

之前B70只保存越界bool，缺具体关节。本次诊断开关在v11显式启用，故障包保存全joint_names/q/dq/limits、root、实体目标和requested/clipped/applied torque；动作前控制归属沿storage保留，保护阈值1mrad不改。故障发生后保存结算并停止，不默认放宽阈值、换USD或重试。

## 证据与当前执行状态

Task：isolated/recovery_standing034_symmetry_20261012/task。
首块：configs/experiments/2026_10_12-23_25__recovery_standing034_mirror_huber_block0000/spec.json。
来源谱系/replay：isolated/recovery_standing_motion_reference_20261012与本任务reward_replay.json。
CPU/frozen/preflight/授权/握手证据在本任务verification目录，实际提交后记录；准备完成不等于smoke或formal已通过。公共命令维护TOOL_INDEX、结构ARCHITECTURE、流程WORKFLOW、事实STATUS。

## 实际首次提交

CPU全量942passed/8skipped/22errors；22项逐ID与此前baseline相同，configure.py SHA一致，三个本轮接口fixture/历史冻结身份问题已定位修正后零新增失败。冻结47pass，真实执行源码与CPU副本逐SHA一致。GPU0 shared check READY/逻辑CUDA_VISIBLE_DEVICES=0/当前session匹配；一次30秒启动握手状态source_eval，worker身份OK，formal首更新核验=False。此时仅说明实际提交阶段，未声称学生已经学习更新或技能通过。既有owner按本次授权结算/续块，worker结束交互，不轮询或守候。
