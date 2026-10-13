# Recovery学生：站立鲁棒性辅助课程提交（2026-10-11）

用户本轮明确授权后续训练且预算不限制。执行首轮选择可审计决策段source_eval＋smoke12＋formal100；不以无限预算建立无限自动续训循环。来源仍为最佳保留BC学生isolated/recovery_mcu_v2_bc_20261011/best_validation.pt，SHA7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470，重新初始化Critic/PPO Adam，不用失败new100接棒。

## 实际配方

新recipe student_recovery_ppo_standing_rehearsal_v4，IO仍multiskill_mcu_v2：31D Actor/40D Critic，单Actor全程Recovery身份；网络、尺度、PD、USD、Plane和限矩保持。无教师运行前缀/救场，BC0，std固定腿.05rad/轮2rad/s。每阶段前5更新只训练Critic。

固定32Swing＋32motion_native_normal环境。normal姿态来自已在本资产8/8通过的B250原生站姿，复制为独立新pose_library train条目；不是DrawBack，也不改旧姿态库。normal每次reset只施加身体水平XZ轴分别uniform±.25rad/s角速度（姿态、关节和线速度保留声明值），两类沿既有±.01rad小yaw扰动。站姿评估采用同样扰动；这不是地形、冲击或宽泛鲁棒性认证。初始化扰动不等于运行时补偿，Swing运行无新增外力或状态重写。

Swing reward保持v3所有权重/公式。仅normal初态h0≥.30m时，H进展参考设为已声明.168m，从而已经站立的状态H=1、可以获得原S=H×水平×双轮接触质量奖，不要求再升高刷分。成本/事件/dt/2.5秒入口＋固定10秒保持协议保持。normal退化不触发旧任务retention停止；sampling.assessment.retained_families的normal仅为现有采样契约所需的family覆盖，training_recipe.retained_families仍空、normal_not_retention_stop显式true。

这是一项混合课程实验，新增站姿覆盖及必要的站姿奖励语义共同改变；不能事后宣称证明某一单项是唯一根因。先检验同一学生的收稳区域是否得到学习，Swing继续负责完整收腿、转腿和抬升。暂不同时叠加腿长、镜像、制动或动作滤波成本。

每更新按动作执行前pose身份分别统计两类有效Actor样本，不能把32/32槽位当成50/50有效样本。无控制样本mask及warmup语义保持；真失败末步保留GAE时间轴。选模仅用原四组Swing32环境的完整通过、入口、首次窗口有效前缀、较早候选排序；normal评估独立保存，不靠站姿8/8掩盖Swing0/32。评估后显式重建训练环境/obs缓存，normal小扰动失败属于能力结果，不停止formal。

## 预算、验证与声明

新声明configs/experiments/2026_10_11-17_12__recovery_mcu_v2_standing_rehearsal_from_bc/spec.json，独立ledger/pose_library/完整发布标记。首轮112在线更新917504样本，source48评分episode/900秒，smoke12/900秒，formal100/5400秒（25/50/100每次Swing32＋normal8；最终选定学生Swing四组复验32），最大208评分episode，全链7200秒、产物2GiB。source行为未成功不阻止PPO；共享教师组合基线若失败或工程异常则停止。GPU0显式shared，不抢占、不换卡，提交前UUID/session/resource核验；notifications=false，失败不自动重试。

CPU36针对性通过、19补充工程边界通过、冻结PORTABLE19通过；全量848通过/22errors，错误ID及configure.py fixture原因与修改前逐项相同且该文件SHA未变。两项本轮fixture因缺family字段失败，已补真实case必需字段后通过，不放宽生产验证。冻结请求误包含PROJECT_DATA测试时被公共validator正确拒绝，改为PORTABLE范围后通过；无物理attempt消耗。

24条已有首episode轨迹重放确认Swing连续reward完全不变、normal奖励有限且无需额外升高；成功事件/dt/首次窗口由现有Certificate回归验证。重放不是训练收益证明。验证证据isolated/student_standing_rehearsal_preparation_20261011，冻结包artifacts/student_standing_rehearsal_cpu_20261011，授权/提交isolated/student_standing_rehearsal_execution_20261011。

源码：students/rehearsal.py、recovery_task.py、training_recipe.py、runtime.py、evaluator.py、training.py；工具scripts/prepare_student_recovery_ppo.py新增--standing-rehearsal；测试新增test_student_standing_rehearsal.py，扩展runtime_parent、preparation_contract、training_boundary、engineering_boundary。文档为本报告、STATUS、Recovery计划、TOOL_INDEX、ARCHITECTURE；旧run/spec/checkpoint/ledger/冻结副本只读，无commit/push。

启动握手证据随后追加，仅记录实际收到阶段，不将source提交写成formal更新。后续由既有owner完成保存、评估、结算；worker不轮询守候。当前未宣布任何新能力通过。

## 实际单次握手

17_12已public supervisor detached提交，worker attempt7149315196c24d1586d685601ae00d36，worker身份与输出/当前session/CUDA映射核验OK；source_eval已开始。该握手为SOURCE_EVAL，formal_first_update_verified=false，不声称PPO已经更新。GPU0 UUID匹配，显式shared生效；源码/冻结CPU输入无漂移。授权receipt与最终spec/budget均由公共工具登记，未借历史余额。之后由既有owner按预算执行source→smoke→formal、选模及结算，worker结束交互，不轮询。

## 已结束：一次性终态核查

事件454a8361294da7da02fc9c30，chain/source/smoke/formal均COMPLETED，无工程failure；12＋100更新、917504样本、1606.8183秒。Swing25/50/100均0/32入口/保持，normal均8/8入口但0/8保持、倾角终止（来源normal入口1/8）。formal有效Actor533375：Swing144255、normal389120，Swing覆盖不足25万目标；完整训练成功事件0。best_overall仍原BC，best_new25只因同分较早，不是能力通过；accepted=null。原始完成报告和候选保留只读，本次未续训。
