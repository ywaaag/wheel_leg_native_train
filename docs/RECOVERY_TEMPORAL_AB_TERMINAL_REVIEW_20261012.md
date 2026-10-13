# Recovery Actor时间平滑A/B终态复盘（2026-10-12）

本轮只读已完成run、冻结源码和具名原始轨迹，执行CPU分析及2项回归；仿真/PPO/optimizer训练更新均0。原run、checkpoint、spec、ledger、冻结源码不改，不重试。

## 生命周期与结算

A：smoke12/formal100，COMPLETED，链2620.11秒。B：smoke12/formal69，第70次更新rollout_step26触发物理保护，FAILED，链1913.39秒。新增完整PPO更新193，对应1581056条完整更新样本，有效Actor1222214，链合计4533.50秒（75.56分钟）；B第70次更新未执行optimizer，另有27个policy interval×64环境的已执行但中断采样，不把它计成一次PPO更新。这里不把评分episode当全部仿真计算量。

任务账本ENGINEERING_STOP、active_spec=null；累计包含历史1014更新/8306688完整更新samples/6828548有效Actor/15806.89秒/744评分episode。既有owner已结算，不自动追加。A/B的best_overall均为update0等Actor副本，即原v10 update100，accepted为空。

## B故障的已确认事实与缺口

故障环境env53属于normal槽位（48–55），pose_index3读回为motion_native_normal/train。故障是post-physics/pre-reset实际关节位置超出姿态库限位至少1mrad，冻结实现检查全关节q与joint_limits。

fault_all_environments明确：joint_outside=true；nonfinite/closure/penetration/initial_rejected/restricted_contact/tilt_termination均false。线速度模4.659m/s、角速度模3.664rad/s、高度.2129m、净空.1173m、闭链误差.000241m、最小间隙为正。不能把此故障说成初始化失败、NaN或闭链故障，也不能归因于时间平滑loss已经证明导致故障。

原故障包只有39D state及标量component，未保存env53全q/dq、具名限位、请求/执行目标与控制者，不能确定越界关节或越界量。已有B50确定性normal评估的全关节pre-action数据中，最接近保护界的是膝关节，右膝最小margin约−0.000596rad，未超过−0.001rad保护阈值。该结果仅提示后续优先读回膝关节；不是env53故障定位结论。不得以此放宽机械保护或更换USD。

## 同协议行为比较

当前教师前缀仍1.80秒，辅助后缀24评分episode（三个相近初态组各8），不是24个独立training seed。入站后固定第一个保持窗口，失败保留分母。

| 候选 | 入口 | 10秒数据窗口完成 | 主协议通过 | 瞬时合格保持前缀中位数 | 最早接触不达标的侧别 |
|---|---:|---:|---:|---:|---|
| 来源v10 update100 |24/24|24/24|0/24|3.180s|左24/24|
| A50 |24/24|1/24|0/24|3.030s|左24/24|
| A100 |24/24|0/24|0/24|2.510s|左20、右4|
| B50 |24/24|0/24|0/24|2.355s|左24/24|

来源完成10秒数据窗口也不合格：触限、速度、接触及部分姿态失败。A50的唯一完成窗口同样不合格。valid_hold_prefix只累计现有瞬时条件，不是累计速度/触限/平均姿态的完整认证。

来源/A50/A100/B50的首次瞬时保持违例均是轮合力不再>2N；B50左轮在该时刻为0N，右轮平均约128.3N。B50违例前100ms平均pitch/roll约−.087/−.098rad，hip/active镜像误差约.423/−.684rad，表明双侧构型不对称已存在；随后后缀评估24/24最终倾角终止。事件先后不证明腿不对称、轮动作或接触之一是唯一根因。>2N是传感器合力条件，不能冒称法向载荷认证。

## 动作平滑有局部变化，不能代替完整稳定

所有候选接管后共同前200interval均有24个完整窗口，避免用提前摔倒的短轨迹制造低RMS：

| 候选 | 左/右轮目标逐步变化RMS(rad/s) | 任一通道policy采样触限 | mean(abs(vx))(m/s) |
|---|---|---:|---:|
| 来源 |3.263 /3.429|3.3%|.460|
| A50 |2.768 /2.808|3.4%|.397|
| A100 |1.248 /.986|2.5%|.419|
| B50 |2.396 /2.313|2.6%|.424|

B50相比A50轮目标变化RMS均值约下降15.6%，但有效保持前缀更短，完整窗口0而非1。无额外正则的A100也明显变平滑，说明不能把所有平滑收益归于B项；更不能认为变平滑必然改善平衡。A100入口后的前2秒轮目标RMS仅.204/.192rad/s，仍全部失去完整保持。

normal三组结果：来源24/24完成窗口但0/24主协议；A50、B50均0/24窗口；A100仅1/24窗口且不合格。无教师Swing在来源、A50、A100、B50均0/8入口/保持，倾角终止。没有证据支持晋级更短前缀。

B实际optimizer日志确认辅助loss已消费（非零配对数/加权梯度），A系数0；两支无warmup重置、BC仍0。不能由正则loss数值或梯度范数直接推断物理因果。

## 决策与下一最小工作

不采用A/B新模型，不增加时间平滑系数，不续训B69或把其未保存状态当checkpoint。保留原v10 update100 Actor及各实验候选，不拼接不同模型的通过片段。

先补齐故障取证：仅故障触发时保存该env全joint names/q/dq/limits、逐关节越界量、控制者、上一与当前实际物理目标、requested/clipped/applied torque和root状态；检查保护阈值与实际USD/pose库一致，保护本身不放宽。随后可准备一次独立、有界PPO0（来源与B50、normal及当前后缀）定位关节边界；B50确定性未复现随机B69故障时如实记录，不宣称已消除。

行为路线按计划第24节“动作平滑但姿态倒了”回退处理。取证完成后，下一学习候选应聚焦入口后侧向姿态/支撑保持，单变量检验；不同时叠加对称投影、std、PD或新观测。本复盘不冻结新reward权重、不启动新训练，先以具体关节诊断排除物理保护问题。

## 可重复证据

机器报告：isolated/recovery_temporal_terminal_review_20261012/final_review.json。逐case/env包含evaluation和trace SHA、完整与截断窗口、首次违例及前100ms状态、目标、镜像误差；具名schema由每个run的冻结trace_schema加载，校验时间连续、首episode、控制归属及trace/checkpoint SHA。

脚本：scripts/review_recovery_temporal_terminal.py；精确命令维护TOOL_INDEX。2项CPU回归核验截断窗口不进入完整窗口均值、left-first轮目标物理单位。原始source/formal候选证据只读，报告不能替代新物理认证。
