# 开链训练经验复用指南

2026-10-07 工程入口更正：下文的“当前”事实属于各自注明日期的历史配方。
现行接口与证据约束见[工程补齐记录](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md)，
版本控制边界见[Git 工作流](docs/GIT_WORKFLOW.md)。本轮仅提交已有代码、配置和文档，
未改变 reward、课程、PPO 或物理契约，未新增训练授权。Git 中的旧 spec、
成功描述或剩余额度不得被用作当前启动许可。

本文件服务于本项目下一位 Codex 的训练决策，不是历史聊天或新的训练授权。证据核对时间：2026-10-01 20:37 CST。设计或修改奖励、课程、训练实验、候选筛选和验收前先读本文件；**真正执行时以本项目当次 spec、run manifest、账本和原始逐环境评估为准**。来源的[日记](/home/kellen/fudan_train/日记.md)、[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)及[playbook](/home/kellen/wheel_leg_migration_audit/training_playbook/README.md)是经验入口，不是当前运行状态。

## 1. 当前决策摘要与证据优先级

| 当前事实 / 决策 | 执行规则 | 依据 |
| --- | --- | --- |
| 唯一当前能力目标是原生闭链**静止站立**；使用完整 `[vx,yaw,height]` 接口，但命令固定 `[0,0,0.363]`。 | 不把模型命名、完整命令接口或历史 Gym 结果写成已学会移动、转弯、可变高度。 | [当前 spec](configs/experiments/stand_plane.json) 的 `control.height_command_m`、`curriculum.active_stage/stages`；[架构](ARCHITECTURE.md)。 |
| 用户接受约 0.363 m。当前完整 10 s 站立 gate 的高度区间是 **0.34–0.38 m**，不是旧 v2 的 0.34–0.36 m。 | 旧 B200 在旧 mesh、旧高度 gate 下 0/8 接受，不能仅因此阻止本轮；也不能在新 plane 上直接记通过。 | [当前 spec](configs/experiments/stand_plane.json) 的 `evaluation.standing_height_m`；[B200 逐环境复核](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/B_formal/review_adapt_200_ten_second.json)。 |
| 地面为 USD **Plane**，静/动摩擦各 0.5、恢复系数 0；原生物理主动关节动作，40/5.5 Nm 限矩。 | 第一个物理检查必须在**新 plane** 上读取实际碰撞/材质绑定、接触、闭环与控制权限；旧 mesh 的 B200 和 Gym 47250 不能代替。 | [当前 spec](configs/experiments/stand_plane.json) 的 `ground/control/action`；[场景实现](src/native_stand/env.py)；[历史 ground A/B](/home/kellen/wheel_leg_migration_audit/sim2sim_47250_bridge_20261001/GROUND_AB_REPORT_20261001.md)。 |
| 当前账本 `NOT_AUTHORIZED`、全部计数为 0；本项目 `runs/` 仅有占位文件。现有 spec 为固定 6 s episode，**没有启用**可选 episode 时长课程。 | 本文件不提供启动许可。未来若另有授权和新 spec，以实际 manifest/账本为准，不从计划、聊天或代码支持能力推断已启用。 | [账本](configs/experiments/budget.json)、[当前 spec](configs/experiments/stand_plane.json) 的 `curriculum`、[STATUS](STATUS.md)、[课程组装](src/native_stand/command_v6/runtime/configure.py)。 |
| B200、Gym 47250、当前新项目候选身份分开。当前新项目没有已测或接受模型。 | 候选表始终列完整路径/SHA、资产/地面/协议及最后、筛查最佳、完整接受的不同身份。 | [STATUS](STATUS.md)、[旧 B200 终态](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/chain_terminal_report.json)、[Gym 47250 review](/home/kellen/fudan_train/plane/outputs/sampling_ablation_20260929_100205/sampling_ablation_20260929_B/phase_reviews/endpoint/cornering_task_v2.json)。 |

**证据顺序：**当前用户授权与有效 spec/账本 → 当前 run 的 manifest、源码/资产 SHA、进程终态 → 原始逐环境评估 → 同身份结构化摘要 → 模块文档 → 本指南/历史日记。`STATUS.md` 是带时间戳的导航快照。类别标签：**已确认**=源码及对应运行/评估可定位；**对照支持**=同身份、同预算并列结果；**相关性**=多因素变化或缺严格对照；**假设**=待测试；**过时**=不能用于当前决策。复用表不构成自动执行指令。

## 2. 当前项目已采纳的原则

- **原生闭链而非虚拟串腿。** 当前策略的 25D 物理关节帧+五帧 oldest→newest 125D history 构成 150D actor/critic 输入；六维 left-first 动作是四个**实体主动腿关节位置目标**与两个轮速度目标。物理 1 ms、PD 5 ms、策略 10 ms；封闭链由 PhysX 约束处理。Gym 恰好也用 25D/125D/6D，**维数相同不代表关节、尺度、顺序、网络或权重兼容**。见[当前 spec](configs/experiments/stand_plane.json) `observation/history/action/control` 与[架构](ARCHITECTURE.md)。
- **可观察的训练链。** CPU preflight 先于 AppLauncher；新 run 存有效 spec、源码/资产快照、控制回读、精确 attempt；普通跌倒属于任务数据，非有限值/闭环故障才是运行故障。以存活时长、跌倒率判断持续学习是否可行，以漂移、`mean(abs(v))`、双轮接触、姿态、限矩和闭环判断是否真的站稳。见[工具入口](TOOL_INDEX.md)、[环境终止](src/native_stand/command_v6/runtime/env.py) `_get_dones` 与[独立评估](src/native_stand/command_v6/domain/protocol.py)。
- **少评估、长训由授权 spec 决定。** 当前配置每 100 更新保存一次 checkpoint/做 2 s 轻评估，每 200 更新做一次 10 s 全评估；这些是**准备中的 spec 值，不是已经运行的安排或额外预算**。下一轮若用户授权不同的 episode/预算/频率，以新 spec 为准，不能因本指南延续旧 200 更新安排。见[当前 spec](configs/experiments/stand_plane.json) `ppo/budget/evaluation`。

## 3. 历史关键经验及证据

| 历史发生了什么 → 证据等级 | 得到的经验 → 本项目如何采用 | 不能直接照搬 |
| --- | --- | --- |
| aggressive 转弯训练 spec 声称连续采样/既定占比，实际 20 槽及固定 bank 不符；另一次 reset 设了目标却没在每步调用 scheduler，legacy 接触历史不更新，turn reward 因而长期为 0。**已确认代码/运行接线故障**。[采样审计](/home/kellen/fudan_train/plane/outputs/cornering_bug_audit_20260927_092941/bug_audit_report.md)、[故障终报](/home/kellen/fudan_train/plane/outputs/high_load_cornering_v3_20260927_112124/completion_report.md)。 | 长训前按 **采样 → 每步调度 → observation/history → action/PD → 当前物理状态 → reward/mask → PPO** 留一段跨越目标事件的运行证据。对非连续 env ID、部分 reset、实际占比与命令 ramp 作 fixture；把事件数与生效 reward 分开记录。 | 1 更新 smoke 只证明能更新参数；若尚未进入入弯/跌倒窗口，两个 turn 标量为 0 不能证明接线好坏。也不为了非零 contact 惩罚主动制造危险失触。 |
| 旧 Gym 从站立→正负低速→±4 直线/原地 yaw 保留已学端点；9500 动态验证 +4 停车需 2.16 s/3.66 m，−4 停车需 4.26 s/12.59 m；10000 独立 MuJoCo 闭链五项只在 10 s 线性入速及缓变减速协议通过。**能力边界已确认，课程收益仅相关性支持**。[课程报告](/home/kellen/fudan_train/docs/overnight_motion_goal.md)、[动态验收](/home/kellen/fudan_train/docs/basic_motion_dynamics.md)、[闭链验收](/home/kellen/fudan_train/docs/sim2sim_10000_acceptance.md)。 | 当前先站稳；将来逐步扩展双向速度、双向 yaw，并永久保留零命令/旧端点的独立回归。命令的进入、保持、退出与停车恢复分别冻结时序、测响应和接触。 | 缓变完成不等于急启急停；不把旧树模型的 10000 当成本项目已通过的闭链策略。 |
| 旧 3° 内倾参考曾与验收共享错误符号；独立几何才发现方向问题。38250 旧 37/48 在新 `cornering_task_v2` 下为 39/48，属于**协议变化**而非新训练收益。**已确认**。[坐标协议](/home/kellen/fudan_train/docs/modules/turn_lean_long.md)、[协议重评](/home/kellen/fudan_train/plane/outputs/cornering_protocol_automation_fix_20260928_100848/completion_report.md)。 | 将来转弯需要独立轨迹几何、逐环境 vx/yaw/接触/滑移/恢复证据；保存新旧 gate 身份。 | 不照搬旧 roll 符号、3° 引导或轮载荷猜方向；当前原地站立不需要人为增大倾角。 |
| 同源 roll 成本 1.0 vs .25 对照为 40/48 vs 38/48；同源 yaw 宽度 `.25` vs 高负荷 `.125` 两组各 5000 更新后为 26/48 vs 24/48，来源 47250 为 41/48。**对照支持这些具体改动无整体收益**。[roll 对照](/home/kellen/fudan_train/plane/outputs/roll_constraint_ablation_20260928_110822/ablation_comparison.json)、[yaw 对照](/home/kellen/fudan_train/plane/outputs/yaw_width_ablation_20260929_145248/ablation_comparison.json)。 | 先做公式/clip 分析，再以同起点、同预算、同协议 A/B 判断“继续训练收益”和“变量收益”；保留来源候选。 | 更大 roll 或更窄 Gaussian 不天然更好；不能以不同 reward 的总分直接比较模型能力。 |
| 47250 在 Isaac `cornering_task_v2` 下原 25 命令 25/25、转弯 41/48、holdout 8/8、过渡 24/24；仍有 7 个高负荷失败点。**限定协议已确认**。[逐点 review](/home/kellen/fudan_train/plane/outputs/sampling_ablation_20260929_100205/sampling_ablation_20260929_B/phase_reviews/endpoint/cornering_task_v2.json)。 | 轻量筛查后只给少量候选做完整多 seed/逐环境验收；安全或原能力退化时不因新点数增加而晋升。 | 没有该 Gym checkpoint 在本项目原生 plane 环境的运动接受证据；评估 seed19/37/53 不是 3 个独立训练 seed。 |
| 原生历史 B200 在旧 mesh 的 10 s 全评估 8/8 存活、均值漂移约 0.072 m，但旧高度区间 0.34–0.36 m 下 0/8，实测约 0.3631 m；其早期 v1 750 为 8/8 存活、完整 gate 1/8。**已确认，均属历史场景**。[B200 对照终态](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/chain_terminal_report.json)、[B200 逐环境](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/B_formal/review_adapt_200_ten_second.json)。 | 生存、低漂移、双轮接触和目标高度必须分开报告；新 plane 的 B200 源端基线是首先要测的事实。 | 旧高度 gate 不阻塞本轮；B200 不是新项目已接受模型，也不能因同一个 checkpoint/策略来源就跨物理场景填通过。 |

## 4. 奖励设计与运行接线

**当前公式先于历史配方。** 当前[纯奖励实现](src/native_stand/command_v6/domain/reward.py)对逐环境当前状态计算 `upright`、高度 Gaussian、命令速度 Gaussian、双轮接触、归一化 effort、动作差分和关节余量；`raw × spec 权重` 求和后乘 **policy dt=0.01 s**，普通提前终止再加 `-1`。当前管线**没有旧 Gym 的单项 ±dt clip 或总正值 clip**。高度目标为公开命令 `.363 m`，高度宽度 `.06 m`；速度分母 `.01 (m/s)^2`、yaw 分母 `.09 (rad/s)^2`。改 width、权重或 gate 前，以真实误差分布画 `e→raw→weighted→dt 后` 曲线，并用相同状态输入测试目标项的变化，不能直接照搬旧 Gym 的 `.25` 或 `-100`。

| 经验与证据 | 可执行检查 / 迁移边界 |
| --- | --- |
| 旧 Gym legacy reward 非零 raw scale 先乘 policy dt，再逐项裁剪；拟议 yaw 正项乘 1.5 会让关键误差区形成平台，而 `.25→.125` 宽度 A/B 最终退化。**源码计算与对照均已确认**。[旧环境](/home/kellen/fudan_train/plane/wheel_legged_gym/envs/base/legged_robot.py)、[离线尺度](/home/kellen/fudan_train/plane/outputs/yaw_reward_ablation_20260929_143915/offline_width_analysis.md)。 | 每项都记录输入单位/坐标、raw、实际权重、dt、单项/总 clip、mask 覆盖、reset 顺序；Gaussian `exp(-e²/d)` 的 `d` 是误差**平方**单位，不是可直接称作传感器噪声的 sigma。 |
| 正常双轮接触下 contact loss 为 0 合理；旧接触历史为零则是另一回事。**实现故障及修复分别有证据**。[故障终报](/home/kellen/fudan_train/plane/outputs/high_load_cornering_v3_20260927_112124/completion_report.md)、[修复说明](/home/kellen/fudan_train/docs/modules/rewards.md)。 | 用双轮接触、单轮失触和 reset fixture 分别检查 mask 与数值；真实运行必须覆盖相应命令/事件。0 惩罚本身不是故障判据。 |
| 轮心前进与正常左右差速不是滑移；旧转弯项用逐轮 `−ωr−(vx−yaw·wheel_y)` 残差并按接触门控。**源码确认，具体收益不可单归因**。[纯 Torch 公式](/home/kellen/fudan_train/plane/wheel_legged_gym/domain/rewards/terms.py)。 | 闭链需重新核对轮轴符号、轮心/接触点、轮半径和真实接触；滑移指标独立于双轮接触 gate。 |
| 旧虚拟腿角度对称奖励不等于树 URDF 的真实镜像，左右 raw action 相等也可能妨碍平衡。**几何审计确认语义错配**。[审计](/home/kellen/fudan_train/docs/motion_asymmetry_audit.md)。 | 如需对称性，先在本 USD 上测关节与几何镜像并仅对适用任务加弱约束；不硬锁左右动作。 |
| effort 大小、`|τ·qdot|` 机械功率代理、动作一阶/二阶差分是不同物理量。**代码/方法论确认**。[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)、[旧奖励源码](/home/kellen/fudan_train/plane/wheel_legged_gym/domain/rewards/equations.py)。 | 当前 `effort/40或5.5` 是限幅归一化代价；它不是完整电耗或电机热模型。平滑项也不是 jerk 或实际低通滤波器；增加滤波会改延迟，须单独实验。 |

理论边界：[方法论 4.6](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)写出 PBRS 标准形式 `γΦ(s')−Φ(s)` 的适用条件，并明确不保证 PPO 收敛/安全；旧源码虽有名为 `*_pbrs` 的相邻差值项，未据此证明标准 PBRS 性质或本项目收益。[旧公式](/home/kellen/fudan_train/plane/wheel_legged_gym/domain/rewards/equations.py)。普通误差平方不是经证明的 CLF。除方法论段落外，未定位一份单独完整的 CLF/PBRS 原文；不把理论建议冒充当前配方成果。

### 4.1 新参考文献可用的诊断线索

[参考文献](参考文献.md)提供了动作分层、奖励门控、渐进随机化和故障排查思路，但文件没有可追溯的论文链接或本项目实验数据。以下均是**待检验假设**，不是已确认根因或修改当前 spec 的依据；先采集区分性证据，再设计单变量实验。

| 如果出现 | 先比较哪些量 | 本轮不直接采取的做法 |
| --- | --- | --- |
| 站立高频抖动 | 逐时刻比较 observation 噪声、策略原始/裁剪后动作、PD 目标与实际关节状态、请求/实际力矩及限幅、策略 10 ms 与 PD 5 ms 的时序；检查 reward 宽度与真实误差分布。 | 不仅凭抖动就提高动作差分权重、加滤波或另建 actuator net；滤波会改变延迟，力矩差分也不是 jerk。 |
| 高度达不到或仿真能站而实际执行无力 | 同一命令下核对目标/实际高度、关节目标和行程、闭环误差、接触、请求/限幅后力矩、PD 单位与执行器力矩-速度边界；区分可达性、单位和负载假设。 | 不先提高 40/5.5 Nm 限矩、扩大质量随机化或假定奖励不足；root height 也不能代替 COM height。 |
| 站立依赖异常接触、换场景后退化 | 核对 USD 碰撞表示、材质 readback、穿透/接触力峰值、闭链误差，并在相同初态和来源身份下做有界场景对照。 | 不由单个异常推定 contact solver 是唯一根因，也不为提高通过率临时修改接触刚度或验收 gate。 |
| 以后训练起立/恢复或鲁棒性 | 可把目标姿态附近的小扰动 reset 与更远初态做分层对照；分别统计恢复率、旧能力回归和各扰动范围的失败环境。 | 不把目标姿态自动视为已证明的稳定不变集；不以“倒放课程”保证学会恢复，也不先用无限力矩或极端随机化改变冻结物理契约。 |

参考文献讨论的高层策略加 WBC/CBF/QP、任务空间阻抗和足端 `F_n\|v_{xy}\|²` 滑移项，**不是当前实现**。本项目是策略位置/轮速目标加 PD；滚动轮的合法前进与左右差速不能按静止足端滑动惩罚。文中“PD 自动保证渐近稳定”“门控彻底消除奖励规避”“CLF/PBRS 消除局部最优”“机械功率等于完整电耗”等断言均不能据此当作项目事实；若未来考虑其中任何新控制层或奖励，先核实适用条件、物理接口和独立验收，再单独立项。见[当前 spec](configs/experiments/stand_plane.json) `action/control/reward`、[复用决策](docs/REUSE_DECISIONS.md)和[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)。

## 5. 课程、episode 与能力保留

- **当前已生效的是固定站立。** `curriculum.active_stage=0`，唯一命令 `(0,0)`，height `.363`，`minimum_zero_fraction=1`；`future_order` 只是未来顺序。当前 episode `6 s`，命令 schedule `[entry .5, ramp .5, hold 3, exit .5] s`，由于运动命令为零，它不是“已训练动态启停”。见[当前 spec](configs/experiments/stand_plane.json) `curriculum` 与[每步命令](src/native_stand/command_v6/runtime/env.py) `_pre_physics_step`。
- **可选 episode 时长课程目前未启用。** 代码有 `EpisodeTracker/EpisodeWindows`：若**未来已授权 spec** 显式含 `curriculum.episode_curriculum`，可按每环境 deadline、已完成 episode 窗口与连续通过窗口升级；该实现的 schema 规定 `lengths_s=[6,10,20,30]`、每窗口 128 episode、连续 2 窗口，但这不是当前有效 spec 的内容。新期限在环境下次 reset 时赋值；`timeout = deadline reached AND NOT terminated`，跌倒/碰撞/关节故障不得混算正常 timeout。见[配置组装](src/native_stand/command_v6/runtime/configure.py)、[episode 追踪](src/native_stand/command_v6/domain/episode_curriculum.py)、[终止语义](src/native_stand/command_v6/runtime/env.py)。**延长 episode ≠ 延长每次 PPO rollout**：当前每次更新仍取 `64 env × 128 policy steps = 8192 samples`，长 episode 可跨多个 rollout 继续，不能按“每更新一次跑完一个 30 秒 episode”预算。
- **后续运动按一个主难度轴推进。** 先零命令保留，再分别加前/后低速、正/反 yaw，再组合；保持每个方向的逐环境计数与旧能力回归，随机进入/保持/退出，最终 holdout 不反复用于调参。已通过的缓变不能称为急启急停；如要制动，另定切换斜率、反向速度、停止距离、回正和瞬态失触 gate。见[历史课程](/home/kellen/fudan_train/docs/overnight_motion_goal.md)、[动态缺口](/home/kellen/fudan_train/docs/basic_motion_dynamics.md)。
- **没有第一轮就不必强行执行所有后续课程。** 来源能力突然消失时查模型身份、初态、scene、命令/观测、动作及 actor/critic/Adam 恢复；一个普通跌倒是任务数据，不能因 smoke 还没学会而取消正式实验。只有 nonfinite、闭环破坏或来源/契约错误才是接线阻断。当前项目的 source baseline、smoke 和 formal 边界见[工具索引](TOOL_INDEX.md)。

## 6. 预算、评估与候选选择

| 规则 | 本项目落点 |
| --- | --- |
| 更新数、样本数与墙钟一起记。 | 当前**未授权**的准备 spec 写 formal 上限 200 更新、64×128=8192 样本/更新、至多 1,638,400 样本和 3600 s；授权后必须以实际 ledger、进程退出码及 run manifest 结算，失败/中断更新不能漏记。不同 env 数下的 200 更新样本数不同，不得直接比较学习量。[spec](configs/experiments/stand_plane.json)、[ledger](configs/experiments/budget.json)。 |
| smoke 检查接线，不是行为验收。 | 最多 3 更新的准备值仅测试来源严格加载、动作/奖励/接触/重置时序及有限 PPO；目标事件若晚于 smoke 窗口，用有界无 PPO trace 补；普通跌倒计入训练数据。 |
| 保存、标量汇总、轻量/完整评估可分频。 | 当前 spec 100 更新 checkpoint 与 2 s light、200 更新 10 s full；2 s 仅完成测量窗口，不能宣布 10 s 站立通过。只对少量候选完整复核，避免高频长评估挤占 PPO。[评估日程](configs/experiments/stand_plane.json) `evaluation`、[调度](src/native_stand/command_v6/config.py) `schedule`。 |
| 选候选优先独立行为证据。 | 保留来源、最后保存、最后已评估、最佳完整评估、accepted 各自身份；不拼不同模型成功点。存活与静止分开：连续 10 s 后仍须漂移、`mean(abs(v))`、双轮接触、姿态、高度和保护通过；失败环境、reset 与缺测不删除。[候选流程](ARCHITECTURE.md)、[站立协议](src/native_stand/command_v6/domain/protocol.py)。 |
| 对照要回答两个问题。 | A/B 相同来源/预算/协议比较变量收益；任一组相对来源才说明继续训练收益。3 个评估 seed ≠ 3 个独立训练 seed；协议改门槛带来的通过数变化不算能力增长。[历史对照](/home/kellen/fudan_train/plane/outputs/roll_constraint_ablation_20260928_110822/ablation_comparison.json)、[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)。 |

## 7. 闭链、Plane 与 sim2sim 复用边界

旧 Gym 资产是树模型的虚拟串联腿；实机/并联闭链需要 Jacobian、零点与力矩映射。当前项目直接用**物理主动关节位置目标**和轮速度目标，由 PhysX 求解闭链；`τ_virtual`、并联关节轴力矩与 motor-side 力矩不是一个量，任何外部日志须说明位置和单位。旧 Gym 的 25D/125D/6D、PD、动作 scale、47.294118 Nm 轮限矩及内倾符号都不能因“维度同”而直接移植。见[当前架构](ARCHITECTURE.md)、[复用决策](docs/REUSE_DECISIONS.md)、[历史 Gym 边界](/home/kellen/fudan_train/AGENTS.md)。

历史 ground A/B 固定摩擦 0.5/0.5、恢复系数 0，仅换 mesh/plane；同一 Gym 47250 桥接策略在 2 s 诊断中，Plane 的左轮离地窗口/接触力峰值与漂移明显更小。**相关性强，但仅对该资产、初态、材料及短窗口成立**；它支持“碰撞表示参与异常”，不证明所有 mesh 都不适用，也不等于本项目 B200 在新 Plane 已通过。[ground A/B](/home/kellen/wheel_leg_migration_audit/sim2sim_47250_bridge_20261001/GROUND_AB_REPORT_20261001.md)。新项目必须在自己当前 plane 上验证物理 readback、来源模型和独立评估；历史 MuJoCo 10000 的缓变五项、Gym 47250 的 Isaac 转弯、旧 mesh B200 的站立都分别保留原场景/协议身份。

不主动加入 V14 弹簧补偿、Gym 虚拟腿映射、LQR、完美世界位置或第三方策略网络接口；这些会改变当前冻结的物理/策略实验，并需机构/执行器证据及新 spec。[本项目复用决策](docs/REUSE_DECISIONS.md)。root 高度不等于质量加权 COM；轮心投影也不是求解器接触点。[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)。

## 8. 自动化与性能规则

CPU 身份/schema/preflight、授权账本校验先于 AppLauncher。detached 提交只做一次有界握手；后台 monitor 拥有 trainer 退出、精确 attempt 结算和终态报告。一次更新末端在 GPU 汇总 raw/weighted reward、终止与接触，再传少量标量到 CPU；保留非有限、闭环与限矩故障检查，不因性能优化丢逐环境评估。每 update 记录实际更新和样本数；完整轨迹只留来源、选中候选及故障窗口。checkpoint、训练标量、轻量/完整评估频率分开，报告区分未评估和失败。[训练循环](src/native_stand/command_v6/train.py)、[自动化链](ARCHITECTURE.md)、[工具副作用](TOOL_INDEX.md)。

终态顺序：确认子进程退出/退出码 → 结算 ledger → 从已有证据写报告与候选身份 → report-ready → 按明确绑定会话最多通知一次。HAPI 通知只表示任务终态和报告位置，**不证明模型成功，也不授权续训**；reviewed 是复盘后的独立确认。未知投递不猜收件人或盲目重发。[completion 架构](ARCHITECTURE.md)。

## 9. 修改训练前的最小检查表

1. 当前用户授权、`STATUS` 时间、实际进程、`spec/manifest/ledger` 是否一致？本轮是什么**一个**待检验问题？
2. 来源 checkpoint、USD、源码、评估协议的 SHA 与实际加载是否吻合？scene 是新 Plane 而非旧 mesh 吗？
3. 目标命令是否真实经历采样、reset、每步推进并同步进入最新 observation/history？物理动作和 reward mask 的有效窗口是否可达？
4. Reward 的单位、raw/weighted/dt/clip、事件触发和可规避路径是否已验证？普通跌倒与 runtime fault、timeout 是否区分？
5. 当前 6 s 固定 episode 还是**新授权 spec** 的 episode 时长课程？每次 PPO rollout 的 env×128 样本数、预算/墙钟和课程升级条件是否分别记录？
6. 基础站立、双轮接触、漂移、速度、高度、闭环与最差环境 gate 是否冻结？轻筛/完整验收/holdout 是否分开？
7. 停止、回退、候选和最终通知由哪一个后台 owner 执行？若实验失败，证据能否区分接线、物理可达性、奖励权衡和采样问题？

## 10. 证据索引与过时结论

- 历史结论到原文件/JSON 字段的机器索引：[playbook evidence_index.json](/home/kellen/wheel_leg_migration_audit/training_playbook/evidence_index.json)。重点原始锚点： [采样/接线审计](/home/kellen/fudan_train/plane/outputs/cornering_bug_audit_20260927_092941/bug_audit_report.md)、[高负荷失效](/home/kellen/fudan_train/plane/outputs/high_load_cornering_v3_20260927_112124/completion_report.md)、[47250 三 seed review](/home/kellen/fudan_train/plane/outputs/sampling_ablation_20260929_100205/sampling_ablation_20260929_B/phase_reviews/endpoint/cornering_task_v2.json)、[B200 旧场景终态](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/chain_terminal_report.json)、[ground A/B](/home/kellen/wheel_leg_migration_audit/sim2sim_47250_bridge_20261001/GROUND_AB_REPORT_20261001.md)。
- **过时：**playbook 2026-09-30 称原生 v2 B 还在运行；实际[链终态](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/chain_terminal_report.json)是 COMPLETED。playbook 对旧 v2 `.35 m` 和 `.34–.36 m` gate 的“先做漂移可观测性诊断”不是当前 Plane 任务的自动下一步。
- **过时：**[日记](/home/kellen/fudan_train/日记.md)中的“下一步减弱 roll 约束”已由后续 A/B 否定；[历史 method_v1 交接](/home/kellen/fudan_train/HANDOFF_METHOD_V1.md)的运行进度和推荐命令不能用于本项目。
- **未知：**新 Plane 的来源 B200 逐环境基线、有效 PhysX 接触/恢复偏移、任何本项目的新 checkpoint 能力，以及迁移到实机后的稳定性。缺少这些证据时写“未评估”，不能用 Gym/MuJoCo/旧 mesh 的通过数填空。[STATUS](STATUS.md)、[工具索引](TOOL_INDEX.md)。
