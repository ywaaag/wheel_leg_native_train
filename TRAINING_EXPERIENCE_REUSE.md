# 训练经验复用指南
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


## 2026-10-07：native 运动学习与能力保持的推荐实践

本节记录 native 闭链 motion 的新证据，供后续实验决策优先参考。下文第1–10节中
“当前”“没有已测模型”“仅静止站立”等描述是2026-10-01阶段的历史快照；
请按日期和对应任务读取。Recovery与motion分别使用各自spec、账本和运行证据。
本次文档更新仅整理经验，运行预算按用户针对新实验的授权另行登记。

### 一、推荐先明确“训练改善”与“能力复核”的区别

2026-10-07在GPU1完成的是冻结模型PPO0复核：9个完整model×command项目、
每项8个scored env，全部通过本次运动协议；在线PPO与离线optimizer更新均为0。
包含初始化、保存、清理和结算共1942.31s，终态COMPLETED。
推荐将该结果表述为“已有模型能力得到新证据”，将训练收益留给同协议来源/候选对照。

优先证据：[完整机器结果](isolated/motion_recheck_20261007/final_gpu1/result.json)、
[逐项原始评估目录](runs/motion_recheck_20261007_gpu1/attempt1/)、
[工程与协议说明](docs/MOTION_ENGINEERING_RECHECK_20261007.md)。
原始trace、manifest、源码快照、terminal、monitor_exit和ledger构成可审计的证据链。

推荐用完整路径和SHA指代模型，尤其把同名update250分开：

|模型身份|checkpoint|SHA256|
|---|---|---|
|来源B250|`runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`|`5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`|
|后续高速运行new250|`runs/motion_high_speed_course_20261007/formal/model_update_250.pt`|`5edcd3fb78bed39b131a12e56552674a62c8993d03a57e01cfe9b32770a799c4`|
|后续高速运行new500|`runs/motion_high_speed_course_20261007/formal/model_update_500.pt`|`95ec1c0bc4786684ee63d20e5c582d8ef73653d5b9657dd2d14adbed67adc270`|

### 二、优先采用已有对照支持的cohort宽度分配

2026-10-06的cohort-width A/B，从同一个actor/critic/Adam/RNG开始，
使用相同命令采样、更新数、评估协议和物理契约。主要变量为线速度tracking宽度：
A全部cohort denominator=1.0；B保留任务0/±0.5使用.04，新任务±1使用1.0。
实际每个update各cohort样本计数一致，保持段比例约75.9%–76.6%。

|250次更新后的保持段指标|A：全部宽核1.0|B：旧任务.04、新任务1.0|
|---|---:|---:|
|零命令mean vx|+0.2019|+0.0081|
|−0.5实际mean vx|−0.2779|−0.4552|
|+1实际mean vx|+0.7515|+0.9600|
|旧协议完整通过数|24/40|40/40|

B在125与250两个检查点均40/40通过。推荐把“旧任务保留较窄辨别力，
新任务使用覆盖其初始误差的较宽核”作为当前有干预收益证据的起点。
具体选择仍应以来源误差分布和公式分析为依据；这次仅一个训练随机流，
其证据等级是**对照支持**，独立training seed的可重复性仍待确认。

公式为`exp(-e²/d)`，d的单位是(m/s)²，属于误差平方分母。
仅看线速度项，当e=.2m/s时，d=1.0得到约.9608，d=.04得到约.3679。
因此宽核对已有低速能力偏差的区分较弱。推荐同时画raw、weighted、dt后值和局部斜率，
评估旧任务的辨别力与新任务的探索覆盖，再冻结配方。
较窄核也可能在大误差区使信号接近零，适宜宽度需要按任务选择。
本项目PPO通过采样回报和advantage优化策略；上述曲线解释奖励偏好，
物理学习收益由训练对照判断。

本次B的宽度选择按**episode采样目标**识别旧cohort，而非按ramp瞬时命令。
推荐保留这一身份语义：±1的新任务在升速经过±0.5时仍属于新任务，
各cohort宽度与有效样本一起记录，便于检查阶段切换。
详见[cohort A/B复盘](isolated/root_cause_audit_20261006/COHORT_WIDTH_AB_REVIEW_20261006.md)
及`runs/motion_cohort_width_ab_20261006/A|B/formal/evaluation_250_*.json`。

### 三、推荐把已有能力边界测清，再决定训练端点

本轮来源B250的30s缓变评估，保持窗口10–18s、停车诊断26–30s，得到：

|目标vx m/s|保持段mean vx m/s|逐环境MAE的均值m/s|新协议通过数|
|---:|---:|---:|---:|
|0|+.008057|.008057|8/8|
|+1|+.960034|.039965|8/8|
|−1|−.929039|.070960|8/8|
|+1.5|+1.521571|.036631|8/8|
|−1.5|−1.536903|.059934|8/8|
|+2|+2.169730|.174264|8/8|
|−2|−2.162456|.168429|8/8|

B250历史±0.5原始轨迹新评分也通过，实际约+.4669/−.4552、MAE约.0331/.0448；
本轮未重新采集±0.5，其历史身份与本轮身份分别保留。
推荐优先选择B250作为下一轮来源与回退模型，准备待学习±2.5，
同时由启动前置校验确认所需旧端点的协议和执行兼容性。
更高命令的独立探测支持能力边界判断，课程解锁仍按持久化证据和预定确认规则执行。
±4、yaw、急停及多个独立评估seed仍有证据缺口。

此结果证明B250已有±2泛化能力。推荐在新增训练前先测来源在目标端点的同协议基线，
再比较“新增学习收益”和“继续更新损失”。这样可以把预算投到真实未掌握的端点。

### 四、用两个维度分析遗忘：共同偏置与命令响应

从B250继续训练±2的历史实验中，零命令保留，但多个运动端点响应收缩：

|目标|来源B250|new250|new500|
|---|---:|---:|---:|
|+0.5|+.4669|+.3913|+.3846|
|−0.5|−.4552|−.4181|−.3864|
|+1|+.9600|+.7914|+.7838|
|−1|−.9290|−.8507|−.7766|

推荐分别记录`b=v(0)`、双向响应增益`g=[v(+c)-v(-c)]/(2c)`、
不对称量`a=[v(+c)+v(-c)]/2-v(0)`及逐环境MAE。
这可以区分“共同后漂”“运动增益下降”和“两者同时发生”。
仅用零命令通过或负向命令改善，容易遗漏其他能力损失。

保留旧命令是推荐的rehearsal基础，但共同actor仍受全部任务更新。
历史高速实验同时新增±2、降低旧任务占比、采用固定env槽位，
因此目前支持“多速度响应收缩”的现象，主导机制尚待单变量对照。
推荐下一轮保留B的cohort宽度、reward、LR、std和Adam语义，
只研究新增端点组成及旧能力保持；采样/actor权重调整可在出现对应证据后作为独立变量。
各组梯度、advantage和状态分布属于机制诊断，收益以更新后真实配对评估确认。

### 五、让验收协议准确表达用途，同时保留物理约束

推荐在启动前冻结目标协议，并将结果按协议版本并列呈现。
本次`motion_absolute_v3`采用逐环境保持段MAE≤.3，方向率≥.95；
零命令采用`mean(abs(vx))≤.5`并称为低速滑行，位移继续作为诊断及场地边界指标。
完整时长、姿态、高度、双轮接触、闭链和执行约束共同参与gate。
当前本次协议tilt阈值.5rad；它属于本次冻结协议，其他实验按各自阈值解释。

旧协议额外使用80%目标响应。例如new250的+.5实际.3913、MAE.1087，
符合新用途，但旧最低.4规则失败。推荐区分“同轨迹按新目标重新评分”
与“新模型能力提升”，保留原评估、失败项和新协议身份。
new500的−2 MAE约.3821仍超新.3容差，说明确实存在能力不足；
其+2 MAE约.3007也在边界外。逐环境结果优先于四舍五入的平均数。

推荐用统一effective protocol指定保持10–18s、停车26–30s，
在线gate、离线重评分和报告消费同一窗口。
稳态tracking、缓变全流程、停车尾窗与急停分项记录，
每项证据说明自身覆盖范围。限矩统计标注采样频率：
100Hz policy读回能支持该频率的统计，完整5ms PD审计需额外对应数据。

### 六、将执行语义和候选选择做成可复用的工程基础

推荐启动前生成一份requested→effective→runtime readback对照：

1. command模式、schedule、episode时长和当前命令白名单。
2. tracking公式、实际权重、active-stage/cohort denominator与dt。
3. PPO真实实现路径/SHA、normalization、LR、optimizer恢复语义。
4. 实际执行模块路径/SHA、checkpoint/asset/protocol身份。

本次来源实际配方为**ramp、combined tracking、全rollout advantage normalization**。
历史spec的fixed/separate/per-command字段曾与执行不符；
推荐严格新配置在CPU阶段拒绝冲突，历史配置保留原值并披露兼容字段实际含义。
将行为等价迁移与算法/奖励实验分开，可以提高结论可信度。

推荐统一使用公开supervisor，内部复用monitor、trainer、evaluator、ledger和completion。
一次性日期脚本承担历史复现，通用入口显式接收spec/model/output/device；
资产依赖路径在运行模块导入前设置，AppLauncher先于Isaac runtime导入。
后台owner保存逐项结果、清理前child terminal、退出后monitor状态和exact结算。
本轮Conda Python缺少os.pidfd_open暴露接口只影响报告交付，兼容修复后报告生成；
该问题与策略能力、物理运行及PPO分开归因。

候选推荐按完整命令覆盖/通过、逐方向误差与稳定性排序，
分别记录source、latest、best evaluated、accepted和回退身份。
本次B250的±1.5误差.0366/.0599，比new250的.2448/.1837小；
结合±2证据，B250是更有依据的起点。
模型名、update编号、零漂移最小值和流程exit0各自只表达一部分信息。

### 七、下一轮推荐执行顺序

1. 核验B250完整恢复状态、旧端点证据、当前授权与跨实验预算。
2. 冻结新spec：优先保持来源实际配方，只增加待学端点±2.5，持续保留旧任务。
3. 做针对性CPU回归、零写plan和必要来源回归，复用已有接口/PPO检查证据。
4. 有界短训在真实更新之间安排独立评估，分别判断新任务进展和旧能力保持。
5. 当前级正负端点、零命令与已掌握端点连续确认后，下一rollout/reset边界解锁一级。
6. 保留退化前候选与latest，发生保护失败时按预定复评和停止规则结算。
7. 再依据真实双向误差和独立复现决定扩大预算；后台owner负责保护和终态，
   交互worker完成有限启动确认后交付路径。

本节的经验等级总结：cohort宽度分配收益属于**单次对照支持**；
B250当前±2能力属于**真实物理复核**；后续多速度响应收缩属于**已观察现象**；
旧任务占比/固定槽位/actor任务竞争的主导因果关系属于**待验证机制**。
推荐让下一次实验只区分其中一个最有信息量的机制，逐步积累可重复收益。

2026-10-07 工程入口更正：下文的“当前”事实属于各自注明日期的历史配方。
现行接口与证据约束见[工程补齐记录](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md)，
版本控制边界见[Git 工作流](WORKFLOW.md)。本轮仅提交已有代码、配置和文档，
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

参考文献讨论的高层策略加 WBC/CBF/QP、任务空间阻抗和足端 `F_n\|v_{xy}\|²` 滑移项，**不是当前实现**。本项目是策略位置/轮速目标加 PD；滚动轮的合法前进与左右差速不能按静止足端滑动惩罚。文中“PD 自动保证渐近稳定”“门控彻底消除奖励规避”“CLF/PBRS 消除局部最优”“机械功率等于完整电耗”等断言均不能据此当作项目事实；若未来考虑其中任何新控制层或奖励，先核实适用条件、物理接口和独立验收，再单独立项。见[当前 spec](configs/experiments/stand_plane.json) `action/control/reward`、[复用决策](#11-复用决策台账自-docsreuse_decisionsmd-迁入2026-10-14)和[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)。

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

旧 Gym 资产是树模型的虚拟串联腿；实机/并联闭链需要 Jacobian、零点与力矩映射。当前项目直接用**物理主动关节位置目标**和轮速度目标，由 PhysX 求解闭链；`τ_virtual`、并联关节轴力矩与 motor-side 力矩不是一个量，任何外部日志须说明位置和单位。旧 Gym 的 25D/125D/6D、PD、动作 scale、47.294118 Nm 轮限矩及内倾符号都不能因“维度同”而直接移植。见[当前架构](ARCHITECTURE.md)、[复用决策](#11-复用决策台账自-docsreuse_decisionsmd-迁入2026-10-14)、[历史 Gym 边界](/home/kellen/fudan_train/AGENTS.md)。

历史 ground A/B 固定摩擦 0.5/0.5、恢复系数 0，仅换 mesh/plane；同一 Gym 47250 桥接策略在 2 s 诊断中，Plane 的左轮离地窗口/接触力峰值与漂移明显更小。**相关性强，但仅对该资产、初态、材料及短窗口成立**；它支持“碰撞表示参与异常”，不证明所有 mesh 都不适用，也不等于本项目 B200 在新 Plane 已通过。[ground A/B](/home/kellen/wheel_leg_migration_audit/sim2sim_47250_bridge_20261001/GROUND_AB_REPORT_20261001.md)。新项目必须在自己当前 plane 上验证物理 readback、来源模型和独立评估；历史 MuJoCo 10000 的缓变五项、Gym 47250 的 Isaac 转弯、旧 mesh B200 的站立都分别保留原场景/协议身份。

不主动加入 V14 弹簧补偿、Gym 虚拟腿映射、LQR、完美世界位置或第三方策略网络接口；这些会改变当前冻结的物理/策略实验，并需机构/执行器证据及新 spec。[本项目复用决策](#11-复用决策台账自-docsreuse_decisionsmd-迁入2026-10-14)。root 高度不等于质量加权 COM；轮心投影也不是求解器接触点。[方法论](/home/kellen/fudan_train/TRAINING_METHODOLOGY.md)。

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

---

## 11. 复用决策台账（自 docs/REUSE_DECISIONS.md 迁入，2026-10-14）

本节原文来自 `docs/REUSE_DECISIONS.md`（核对于 2026-10-01），已**逐字迁入**本文，内容未改写。
“复用”指具体的物理/配置元素或工程模式，不是其他团队的政策或 reward 表。
表中 `/home/kellen/...` 为**外部或本机参考路径**，保留原身份供追溯，不是可移植示例；
对方仓库为只读，本项目未复制其代码。

Checked 2026-10-01. Source projects are read-only. "Reuse" below means a
specific physical/configuration element or engineering pattern, not another
team's policy or reward table.

| Source and location | Useful part | Decision / side effect |
| --- | --- | --- |
| Colleague `wheeled-legged_RL/source/agent_world/agent_world/assets/rmuc_wheel_leg.py`, `configs/rmuc_wheel_leg.yaml` | Immutable closed-loop USD path, articulation root/solver setup, active leg/wheel and passive/guide actuator groups. | Import the SHA-pinned `RMUC_WHEEL_LEG_CFG` at the CLI boundary, copy it per environment, zero only active gains for one explicit effort path, and read back all active bindings/limits. The module reads YAML at import; preflight hashes both before Isaac. Do not mutate the shared cfg or import the colleague task env. |
| Colleague closed-loop USD `.../assets/usd_files/rmuc_wheel_leg/rmuc_robot_closed_loop.usd` | Closed-loop constraints, bodies, collision assets and inertia. | Use the immutable SHA-pinned source. `native_stand/env.py` resolves six motor joints by name and four closure endpoints; no USD edit or Jacobian lookup. Authored properties are distinct from runtime effective values. |
| Colleague `source/agent_tasks/agent_tasks/direct/rmuc_wheel_leg/env.py` | Scene cloning, body-name contact binding, passive/guide separation, closure-consistent reset ideas. | Reuse only these physical-interface principles. Do **not** inherit right-first action order, wheel-effort action, its 8 ms policy, radial spring, extra feedback, motor-response compensation, reward, curriculum or PPO. |
| Local [ground A/B report](/home/kellen/wheel_leg_migration_audit/sim2sim_47250_bridge_20261001/GROUND_AB_REPORT_20261001.md) and `ground_env.py` | On fixed 0.5/0.5 friction, zero restitution, the USD Plane reduced left-wheel separation and force spikes relative to the mesh. | Implement only the physical Plane and explicit material in this project; verify composed binding at runtime. This was 47250 diagnostic evidence, **not** native-training acceptance. PhysX contact/rest offsets remain UNKNOWN until readback. |
| Local `native_stand/command_v6/domain`, `ledger.py`, `train.py`, `tools/preflight.py` | 25D/125D native contract, B200 warmstart by named columns, exact attempt ledger, GPU rollout aggregation, independent terminal snapshot. | Carry one audited kernel into this long-term project. Old v6 runs and their consumed ledger stay at the audit path; the new project has one code tree and new spec/budget. Remove unreachable benchmark phase. |
| Local `native_stand/contract.py`, `env.py` | Physical-joint targets/PD, named joints, reset/closure/body motion. | Carry only these needed source modules and change ground to Plane as an explicit new physics experiment. `native_stand/train.py`/`probe.py` are **not** runtime imports. |
| Fudan Gym `ARCHITECTURE.md`, `CODEX_WORKFLOW.md`, `TRAINING_METHODOLOGY.md` | Clear layer ownership, true command/observation/reward/PPO wiring checks, retained baseline tasks, independent candidate selection. | Reuse process and tests. Do not import its tree asset, virtual joint map, 47.294118 Nm wheel limit or actor weights into the native physical-joint policy. |
| Third-party `/home/kellen/wheeled-legged_RL/README.md`, `scripts/rsl_rl/play.py`, `source/agent_tasks/agent_tasks/direct/wheelbipe/wheelbipe_V14/env_cfg.py`, `.../agents/rsl_rl_ppo_cfg.py` | Separate task config/runner config, a play CLI with keyboard and bounded steps, per-run velocity/reward traces and explicit multiple RL recipes. | Reference architecture and operator UX only. Its Wheelbipe V14 topology, older documented Isaac Lab version, domain randomization, action/reward definitions and PPO numbers are not this RMUC closed-chain contract. Existing dirty files remain untouched. No code was copied from it. |

The V14 action implementation in `wheelbipe25_v3/env.py:_apply_action`
sets leg position targets, but its wheel branch is **conditional**: configured
velocity control uses velocity targets, otherwise the default branch uses
effort targets. It does not prove our RMUC wheel control without our own
readback. Its `_apply_spring` models forces on V14 prismatic spring joints;
the current RMUC native environment has passive-link damping and no copied
V14 spring force. Adding one would change the frozen physical experiment and
requires mechanism/force-curve evidence and a new spec. V14's 35D/78D saved
run and delay/randomization settings remain references, not our 25D/125D
interface or a reason to inject new delay now.

The current project therefore owns the observation, six-channel physical
action, reward, standing recipe and independent gate. The colleague provides
the closed-loop asset and validated physical organization; the third-party
project and Fudan provide design experience.

---

## 12. 模型与实验证据摘要（自 198 份按日期报告压缩，2026-10-14）

本节把 `docs/*_2026MMDD.md` 这批按日期的实验/工程报告中**有长期价值**的部分压缩到这里：
模型身份与祖先、实际协议、关键能力结果与失败边界。过程细节、逐次故障与命令输出不迁入。

**方法与覆盖**：由 5 个并行只读任务按固定列（类别/模型身份/协议/能力结果/失败边界/独有价值）读取全部
198 份报告，本节据其合并去重。日期报告本身不因此成为“能力当前有效”的证明 —— 能力结论一律以 run 的
`terminal` 与原始 `evaluation` 为准（见 `docs/README.md` 的证据状态说明）。

### 12.1 模型身份与祖先（权威台账，SHA 已现场核验）

来自 `artifacts/2026_10_14-11_05__storage_prune_audit_rev3/protected_models.json`（2026-10-14 13:42 逐项核验）。

| id | 类别 | 路径 | SHA256（前 16） | 角色 |
|---|---|---|---|---|
| M1 | Motion 教师 | `runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt` | `4750ee5661ade1e9` | 当前选定教师（PPO Actor），五命令 40/40；已成 ONNX |
| M1b | Motion 候选 | `runs/2026_10_13-07_21__motion_standing034_pm2_block0004/formal/model_update_100.pt` | `df60f53cc4bcca08` | 最强运动候选（七命令 40/56） |
| R1 | Recovery | `runs/2026_10_13-10_39__recovery_standing034_mirror_huber_block0007/formal/model_update_300.pt` | `cdcbae696f224e9b` | v11 最后成功 formal 块（block0008 预算耗尽 FAILED） |
| S1 | 31D 学生 | `runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt` | `2af573b318d7ebd6` | v13 终态，也是活动 v14 的来源 checkpoint |
| S1c | 31D 学生 | `runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_700.pt` | `73a7a09e713afcb5` | v13 **实际使用**的来源（不是 v12 终态 S1b） |
| D1 | 25D 蒸馏 | `isolated/motion_frame25_actual034_bc_20261013/best_validation.pt` | `e86b7922d099f251` | 真实 .34 教师教学的 25D 学生；13,862 参数 |
| D1b | 25D 蒸馏 | `isolated/motion_frame25_zero_distilled_20261013/best_validation.pt` | `e56dc7f5b07f15bc` | 更早 zero-only 版本（标签来自 .40 离线 query） |

**关键祖先事实**（报告明确写出，按当时 run 身份保留）：

- **共同分叉点**：`runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/model_update_300.pt`
  （v7 u300，`2a587c31…37a9a`）同时是 Recovery v11 链与 31D 学生主干的祖先。
- **B250 是 Motion pm2 全链根模型**：`runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`
  （`5d3389d5…b89e`）。B250 → 父 `motion_forward_cohort…forward25 (bacd31f3)`，上游六级 random 初始化
  祖先为 `wide_leg_from_scratch_20261002_formal`（stage0 零命令）。B250 同时是活动 v14/v13/v12 spec
  显式引用的教师，属活动依赖。
- **31D 两链共同根**：`isolated/recovery_mcu_v2_bc_20261011/best_validation.pt`（`7b306936…f470`）；
  PPO 链再由 `isolated/recovery_standing_reset_distilled_20261011/best_validation.pt`（`06c33cf7…e365`）分出。
- **蒸馏教师 = Motion M1**（跨类共享祖先）。
- **Recovery 旧站立链（与 B250 无关）**：`wide_leg_from_scratch_20261002_formal/model_update_500.pt`
  （STAND500，`fc51370b…631e1`）→ `standing_scissor_20261006/formal/model_update_50.pt`
  （source50，`1fa4255a`）→ `recovery_survival_level_from50_20261006 u200`（new200）。
- **v13 → v14 链**：v13 `u988`（S1）→ v14 `model_update_100/200/300`；v14 存储续跑 u300/688 再接
  `v14_wiring2 u300`。
- **v12 来源**：`runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt`
  （`bc524561…be4d`）。
- **未决（不据以删除）**：Recovery 与 31D 是否同类、v12 终态是否保留、25D 更早版本 D1b、Motion M1b —— 均已保护。

### 12.2 实际协议

| 族 | 协议要点 |
|---|---|
| Motion 教师（legacy 150D） | 教师策略确定性导出；评估五命令 / 七命令；40/40 与 40/56 两档口径 |
| Recovery（31D） | 31D Actor；Critic 演进 34D → 40D → 49D（特权）；站立高度 0.34m / 0.36m；`rising` 23s + `holding` 10s；策略 100Hz、物理 1/5/10 ms |
| 学生 25D 蒸馏 | 25D Actor + 34D 特权 Critic；ONNX 55 KiB；数值误差 1.79e-7（D1）/ 5.96e-8（D1b） |
| 闭链物理契约 | Plane 场景、六路物理动作、40 / 5.5 Nm 上限、25D 帧 + 125D 历史 |

### 12.3 关键能力结果（可长期引用）

- M1 教师五命令 **40/40**；M1b 七命令 **40/56**（同模型 ±2 档最高）。
- Recovery **B25（`8c3f74f9…f4f9`）与 u50（`a646b6d0`）：DrawBack / R0 各 8/8、完整 10 秒** —— 这条链首次通过；
  其后再没有同等级的完整认证。
- Recovery **B50（`46add82f`）0.50s + Motion 组合 7/8**：目前唯一被记录的自主起身接近成功组合。
  **直接 Swing 全程 0/8。**
- v13 `u988` 独立 30 秒 PPO0：**首 30 秒存活 8/8，但质量 0/8**（末 10 秒 abs vx 2.720 m/s）。
- 31D 迁移 Motion：**存活 40/40、质量 0/40**。

### 12.4 失败边界（合并去重后的长期结论）

1. **学生闭环普遍不达标**：mcu_v2 学生 0/32 与 0/8；25D 学生 0/40（1.38–2.09s 倾角终止）；25D PPO 300 更新后 13 候选全 0/8。
2. **入口 ≠ 保持**：多个学生 normal 入口 8/8，完整保持仍 0/8（倾角/滑走/触限）；v10 入口 8/8、保持仅 2/8。
3. **单策略自主起身全 0/8**：直接 Swing 0/8；缩腿 ≠ 转腿/支撑/抬升。
4. **单变量奖励/动作修改无效**：`λ=0.001` mean aux、几何 cost、`speed_scale 0.1`、取消 failure 事件、
   退火 BC、几何惩罚 —— 均未解决 Swing 入口与收稳，Swing 恒 0/8 ~ 0/32。
5. **对称/镜像改善 ≠ 收腿**：镜像仅改善对称 ~29.7%，轮心几何只减 3.2mm，右腿不收短，且损伤旧组接触；
   镜像学生（~0.56s）比未镜像 BC（~1.17s）**更早倒**。
6. **轮动作别名**：轮 raw 变化但 clipped 恒 [−1,−1]（−100 rad/s），轮 mean 越界；增大轮探索不改变腿协同。
7. **静态几何桥接失败**：0.228 / 0.259 / 0.289 m 支撑初态 8/8 被拒并回落 Swing；静态闭链几何**不证明**
   动态 Swing→DrawBack 可达（b=0.20 地面穿入）。
8. **探索覆盖不足**：联合收短方向概率 ~1e-92 量级；提 std×8、平滑 clamp、混合 policy 均未过审核。
9. **时间平滑 ≠ 改善平衡**：A100 无额外正则也变平滑。
10. **成功门槛与验收门槛不一致**：在线 2s 成功（roll ≤ .15）与 10s 验收（mean ≤ .10）存在缺口，roll≈.13 可在线成功却完整失败。
11. **宽松零速门槛 ≠ 零速能力**：0.5 m/s 门槛下可通过，但后滑 0.0895 / 0.346 / 0.468 m/s，不能称定点站立。
12. **更全输入不保证稳定**：25D+ / 34D 特权 Critic PPO 最好 u100 3.38s，仅略好于来源 2.08s 且后期退化。
13. **长训非 GO**：正向与站立随更新退化，无双向改善；tracking 误差 .145–.165 ≫ .03 gate。
14. **来源同协议基线缺失**：fixed 非零运动基线缺失，旧评估与 formal 不可直接比较。
15. **CPU / BC 拟合 ≠ 闭环**：CPU 通过、提交握手均不转化为闭环能力，也不等于 formal 首更新。
16. **sim2sim 未认证**：首轮 0.18s 失败因坐标基接错，该结论作废；`height034_v2` 速度后偏，contact/friction/inertia parity 未认证。
17. **硬件与实机空白**：真机、ONNX Runtime 均为 NOT_RUN / HARDWARE_UNVERIFIED；实机 0.36m 限高无证据（启动峰高 ≈0.3997–0.3998 m）。
18. **速度/yaw 菜单空白**：±4 与 yaw 从无证据；new250 ±2 旧证据缺失；±2.5 未测；姿态对齐未 accepted。
19. **窗口聚合不能作因果证据**：多个 run 缺全过程 height/geometry 保存，末段窗口结论不可当因果。
20. **关节点镜像误差小推不出实体几何**：0.56 rad 对应实际 17–18 cm；hip 镜像 ≠ 腿长差。

### 12.5 不可复核项与证据状态

- 本摘要引用的 run 路径若已在 2026-10-14 存储精简中删除，**原始证据不可再访问**；相关数值按当时报告的
  run 身份与协议保留，**不重建、不补零、不重新认定能力通过**。
- 逐份报告的原文仍保留在 `docs/`（本轮未删除），其顶部「证据注记」标明哪些引用目标已清理。
- 报告间的相互引用（多数为台账式列举）不构成调用依赖。
