# 同一Recovery学生基本站立专项PPO：2026-10-11提交

用户明确要求执行下一步并允许PPO。本轮不新增BC，也不继续17_12失败模型；来源为第二版站立关键帧蒸馏学生，单Actor、全程Recovery标识。专项目标为正常站姿保持10秒，Swing仅回归，最终完整Swing起身目标不取消。

## 来源与已有偏离证据

来源isolated/recovery_standing_reset_distilled_20261011/best_validation.pt，SHA06c33cf7552d2f43b015fca589b927d4634a914a1e9680a4c07da38109e4e365；对应dataset/manifest逐SHA核准，新声明依赖显式保留。该模型normal初态8/8入口，但1.16–1.18秒后倾角终止、完整保持0/8；B250同资产对照8/8。

已有20_19轨迹readonly对齐：env0首动作腿目标最大误差.00094rad；约.49秒学生腿执行目标与教师差>.02rad，.77秒pitch/roll差>.05rad，.79秒高度差>1cm，.83秒双轮接触丢失，1.18秒倾角终止。逐env及输入SHA见isolated/recovery_standing_ppo_preparation_20261011/deviation.json。先后关系不是唯一根因证明，支持用学生自身闭环状态进行站立学习；不在未知失败状态强行贴B250专家标签。

## 冻结课程和有效接线

recipe student_recovery_ppo_standing_from_distilled_v5，31D Actor/40D privileged Critic，Actor31→128→64→32→6、ELU/tanh，Critic40→256→128→64→1。腿1.5rad、轮100rad/s，原USD/Plane/PD60/2/1、physics/PD/policy1/5/10ms、40/5.5Nm真实限矩与机械限位。不能根据初态切换技能标识，站立仍是Recovery学生。

64训练env全部motion_native_normal，以已核验B250原生站姿声明初始化，仅既有uniform小yaw±.01rad；首轮不追加±.25rad/s角速度扰动、不学地形/高速。无Swing训练样本稀释，Swing原生初态作为每检查点的8env回归，不参与站立专项选模或退化停训。

继承仅学生Actor；Critic/PPO Adam新建，源BC Adam/Critic/RNG均不恢复。无教师执行前缀/切换/救场，BC系数0、std固定腿.05rad/轮2rad_s、不优化log_std。LR3e-5、epochs/minibatches4/4、gamma/lam.99/.95、clip.2、value.5、entropy.001、gradnorm1.0。每阶段前5更新仅Critic，之后Actor/Critic同更。预动作mask、失败末步、真实GAE时间轴与无有效样本Actor梯度None保持。

reward直接复用v4已声明正常站姿有效高度参考与质量奖励：初态h0≥.30时参考.168，不要求站立后再升高；H/支撑水平质量、努力/动作变化、入口后角速度与速度成本、首次入口+1/完整证书+10、failure0、dt一次均不改。此次改课程和来源，不同时设计腿长、镜像、制动或BC辅助。全程保留真实故障、倾角终止和首次固定保持窗口，不为了站立专项降低验收。

协议沿student_autonomous_swing_v1参数：受控≤2.5秒确认.20秒入口，随后固定1000interval完整10秒；高度≥.30允许.42、既有水平/接触/闭链/触限与速度/yaw标准。名称沿用协议而初态不同，因此结果明确只认证normal standing，绝不声称Swing自主起身通过。

## 预算与评估

公共准备器新增--standing-only，独立configs/experiments/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/spec.json、run、ledger及poses发布。source40episode/900秒（normal原生/两组yaw各8、新学生Swing8、B250正常对照8）；smoke12更新/900秒及normal原生8评估；formal300更新/10800秒。总312在线更新2555904原始样本、12600秒含评估清理、2GiB产物。

formal25/50/100/200/300各评估三组normal共24及Swing8=32评分env，共160；最后按正常站姿主协议选定单模型，再原生＋3新小yaw组复核32、Swing回归8=40。整链最大248评分episode。Normal三组完整保持通过数→入口数→首次固定保持有效前缀→更早候选选模；源、latest/best_new/best_overall/accepted分开。选模输出capability_scope=normal standing only; Swing not certified。最终normal accepted与Swing regression分别报告，chain报告显式加认证scope，避免将专项站立通过写成完整起身。

source学生未通过仍可训练，只需完整有效工程证据及B250正常对照8/8。事件smoke验证真实episode结束、reward进入storage、warmup冻结与后续Actor更新/checkpoint读回，不要求先学会站稳才能放formal。普通倾倒继续formal预算；工程故障/数值非有限/物理契约异常/预算/用户停止按规则结算，不自动重试或无限续训。GPU0明确shared，不停止其他任务不换卡；notifications=false。

## 验证与本次修改

31相关CPU通过；10公共声明/实际CPU optimizer测试通过（两个内存独立测试更新，不计在线PPO、未改源checkpoint）；20冻结PORTABLE通过；全CPU856passed/22errors，与本轮前基线22项fixture ID及原因一致，无生产SHA放宽。共享与冻结源码inputs无漂移、真实supervisor零写plan通过，授权/提交前session/GPU UUID/逻辑映射/输出/ledger再核验READY。

源码修改students/training_recipe.py（明确v5来源/课程/预算）、students/training.py（主family选模、可声明milestones、standalone最终复验/回归分开）、scripts/prepare_student_recovery_ppo.py（--standing-only独立完整发布）、command_v6/stand_chain.py（仅对声明selection_scope的学生报告插入scope）。测试新增test_student_standing_only.py，扩展test_student_preparation_contract.py真实新源CPU warmup/Actor更新。文档本报告、STATUS、Recovery计划、TOOL_INDEX；旧run/checkpoint/spec/ledger冻结副本只读，不commit/push。

验证isolated/recovery_standing_ppo_preparation_20261011，冻结artifacts/recovery_standing_ppo_cpu_20261011；执行isolated/recovery_standing_ppo_execution_20261011。提交后只做一次有界握手，后续既有owner负责执行/保存/评估/结算，worker不轮询守候。阶段事实随后追加。

## 单次启动握手

public supervisor已首次detached提交20_46链，worker身份/输出/当前session/CUDA_VISIBLE_DEVICES=0核验OK，物理GPU0 UUID匹配，resource_mode shared生效。实际握手SOURCE_EVAL；formal首更新未核验，不声称已完成PPO更新。共享/冻结源码SHA无漂移。之后由既有owner完成source→smoke→formal预算/保存/评估/结算，worker不轮询、不另建watcher、不自动追加。

## 终态一次性核查

事件0fed4ea8ce4dccfafe8e50d6，链COMPLETED，无工程failure。smoke12/formal300，共312在线更新2555904samples，链3181.2668秒，formal有效Actor2416640。normal25/50/100/200/300均24/24入口但0/24完整保持、倾角终止；Swing各点0/8。update50为站立专项best_overall实验候选，accepted=null；最终normal0/32、Swing0/8。逐候选实际控制时间/固定窗口有效前缀见completed_summary.json；不把入口称站稳，不自动续训。
