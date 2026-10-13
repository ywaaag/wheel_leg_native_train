# 站立专项update50继续训练：Motion反馈＋弱镜像约束

## 来源与任务

用户明确要求继续站立专项update50、增强站立、参考Motion祖先训练并希望对称。本轮从实际20_46 formal/model_update_50.pt出发，SHA d1db35ffe83fe462edab55934621cf4ea59b59ff8d60665b4e06720cb66a5a92。谱系parent使用它自己的formal/source_snapshot/spec.json，SHA f56c1fbca7c8e55bfdd22d949b331f3fec2813bf523acbd06b3fdabfe7a35965；不从最新300、镜像蒸馏失败模型或旧BC重新开始。

继承update50 Actor及固定std，Critic与PPO Adam重新建立（奖励发生变化，旧value/optimizer不冒充对应新回报）；source RNG/旧课程不恢复。smoke/formal各独立从update50开始，不继承smoke末尾。全程同一个Recovery Actor、31D/40D、BC0、无teacher救场；仍64normal站姿、小yaw±.01。Swing原生初态仅回归，不将专项站立成功说成Swing完整恢复。

## Motion祖先：实际代码先于字段

只读B250自己的冻结spec和domain_reward.py，继续核对其父motion_forward_cohort25及再前motion_retention off49。B250来源SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e，实际父forward25 SHA bacd31f34a1e3917afa8e5dd9648bb5985c023dd0bc9ffd6a96ad1e1eed6fbad。

冻结实现raw项：up夹0~1平方；命令高度Gaussian；联合vx/vy/yaw Gaussian；双轮接触；effort归一化；action_delta；joint_margin。实际按raw×weights×dt再加终止惩罚，不是单项dt clip。虽然配置tracking_mode=separate，冻结代码联合exp(-(vx-vcmd)^2/d-vy²/d-(yaw-ycmd)^2/.09)，因此不把字段宣称已试分项奖励。B250旧零速cohort denominator=.04(m/s)^2，yaw=.09(rad/s)^2，velocity_tracking权重8、upright2/height2/contact.5/effort−.02/action_delta−.01/joint_margin−.05。零速回归/阶段候选保留值得复用。

不照搬原模型.5rad腿尺度/旧USD/低高度或腿角终止、窄高度.06Gaussian、joint_margin门槛.25rad；当前Recovery1.5rad和允许.42m高度不改。此前terminal−1延后失败偏好已有证据，本轮failure_once继续0，不混入旧惩罚。保持当前31D网络、PPO3e-5、4/4epochs/minibatch、gamma/lam.99/.95、clip.2、std腿.05rad/轮2rad_s、原PD/限矩/Plane/USD。

## 新recipe及奖励

student_recovery_ppo_motion_mirror_from50_v6 / student_recovery_reward_motion_mirror_v6。原v4站姿六项、pre-entry角速度成本、事件/证书/dt/固定窗口完全保持，新增两项连续density：

1. Motion零速质量 T=exp(-(vx²+vy²)/.04-yaw_rate²/.09)，新增 +4×H×U×T /秒。H为已有站姿有效高度质量，U为已有pitch/roll质量。目标零速度不等于验收要求高精度定点：主mean(abs(vx))≤.5m/s gate完全不改，strict .02仍诊断；未加位置漂移门槛。该正奖励让缓慢滑走也有可辨别回报，不是只有超过.5才给成本。
2. 物理关节镜像cost M=H×clamp(mean(((q_Lhip+q_Rhip)/.20)²,((q_Lactive−q_Ractive)/.20)²),0,4)，新增 −.05×M /秒。输入为post-physics/pre-reset实体四腿q，不是目标label，不要求左右q值相同。最大−.2分/秒，小于零速质量最高+4分/秒和原站姿正项，不硬锁左右、不平均实际动作、不强迫轮速相同。

每项乘dt=.01一次，初始化/无控制/fault均0，受控失败末步正常计入；完整事件奖励不再乘dt。三种形式raw/weighted_density/dt独立保存，镜像物理误差另记。它鼓励对称，但不能保证完全对称；倾斜或一侧接触下必要差异仍允许。此次由用户目标新增tracking与弱镜像两项，是联合配方，不据结果单独宣称其中某项根因已经证明。

正常站姿不满10秒不得accepted；入口/完整窗/证书区分保持，不为更多正奖励而发假success。Progress当前仍只CPU提案，不进入本轮输入/运行；不混接口迁移、滤波、制动、示教loss或新地形。

## 已有轨迹量级重放

readonly B250正常8条、update50原生8条、旧update300原生8条共24episode。具名schema与trace/teacher/祖先源码SHA核验；按post物理状态/actual q/实际执行目标重算新旧连续项，六项及事件未改（重放事件0，事件单独回归）。

B250首2秒：tracking约+3.9719分/秒、镜像−.0250；末.5秒tracking3.9677/镜像−.0274、vx abs约.008m/s。update50首2秒tracking1.210/镜像−.0564、vx abs.498m/s；倾角前末.5秒tracking约0/镜像−.1665、vx abs2.820m/s。update300末段vx约4.098、tracking0。体现新增tracking对滑走有量级区分，不证明唯一机制或保证训练成功。

原B250真实目标非完全镜像，先前离线平均teacher目标虽腿更齐却normal.56秒即倒，因此本轮不用该label介入，不从失败镜像模型续训。优先真实站立反馈，弱镜像只辅助，稳定和对称分别报告。

## 新声明、预算与选模

22_43独立config/run/spec：configs/experiments/2026_10_11-22_43__recovery_standing_motion_mirror_from50/spec.json；独立ledger、poses、完整发布标记及parent SHA，新用户本轮授权登记不借20_46余额。

source40评分episode/900秒（normal原生＋两yaw各8、Swing原生8、B250正常对照8）；smoke12/900秒与normal原生8评估；formal最多300/10800秒。总312updates2555904samples/12600秒含初始化评估清理/2GiB产物，64sim env、8scored/case。formal25/50/100/200/300各normal24＋Swing8，最终选单模型normal32＋Swing8，总评分episode248。

站立主协议选模：完整正常保持数→入口→首次窗口有效前缀→更早候选；source/latest/best_new/best_overall/accepted分别保留，actual镜像误差辅助量化，不能因腿更齐/训练reward更高采用退化模型。Swing回归不与normal拼能力，accepted scope明确normal standing only。沿2.5秒deadline/连续.20秒入口/固定1000interval10秒、height≥.30允许.42/原姿态接触闭链触限速度要求。没有旧retention停止；普通行为跌倒继续预算，工程故障/数值/机械异常按规则停止，不自动重试/无限续训。

## 实现及验证

源码students/recovery_task.py新增明确v6 reward并要求具名post四腿q，students/runtime.py将actual q实接reward，training_recipe.py固定update50源/版本，students/training.py记录新项raw/density/dt与实际q镜像误差；prepare_student_recovery_ppo.py新增--motion-mirror、验证update50自己的谱系parent/spec与dataset/manifest，复用公共supervisor，不另建trainer。

测试新增test_student_motion_mirror_reward.py（零速/yaw/横速、slow drift、镜像符号/上限、mask、.42高度/dt），扩展runtime_parent真实路径及preparation_contract真实public声明/新source内存CPUwarmup和Actor更新。CPU第一次失败是合成fixture复用了同一个bool Tensor、success写入同步污染fault，已修正独立clone，生产代码未降低mask；最终测试记录见验证目录。

证据isolated/recovery_motion_mirror_preparation_20261011（准备、差异、24episode重放、CPU验证）、artifacts/recovery_motion_mirror_cpu_20261011（实际冻结副本及PORTABLE）、isolated/recovery_motion_mirror_execution_20261011（授权/资源/单次握手）。GPU0 shared显式核验UUID/session/CUDA/资源/输出/ledger、未停止其他任务不换卡；notifications=false。提交后只握手一次，既有owner监督保存评估结算，worker不轮询守候。待实际提交再追加阶段事实，不将提交source写成formal更新。

无新增BC优化、旧checkpoint原文件不变，旧run/spec/ledger/evaluation/冻结副本只读，不commit/push。

最终验证：30 targeted通过、22冻结PORTABLE通过，全CPU867passed/22errors；22项ID及configure.py fixture原因与修改前一致，该源码SHA不变。update50内存独立CPU PPO回归验证Critic warmup不改Actor、后续Actor真实更新、std及源文件不变，测试optimizer调用不计在线物理预算。

## 实际单次启动握手

22_43已首次public supervisor detached提交，实际状态SOURCE_EVAL，worker身份/输出/current session/CUDA_VISIBLE_DEVICES=0核验OK，shared GPU0 UUID匹配。formal_first_update_verified=false，不将来源评估阶段说成PPO已更新。全部共享源码/冻结inputs核验无漂移；之后既有owner监督预算、保存、评估、结算，worker结束交互，不轮询或新watcher。不自动采用latest或失败模型，不追加无界训练。

## 已结束：一次性终态复盘

事件06438889551a28297bf917ca，COMPLETED，无工程failure；12＋300更新、2555904samples、formal有效Actor2416640、3596.5292秒。update200正常24/24完成固定10秒窗口且未倾角终止，但主协议0/24，累计水平/触限/vx失败、部分contact/level_peak失败；平均abs vx约1.55m/s。原source约5秒后倾倒，新200更能持续支撑但仍快速滑行，不能宣布站稳。实际镜像hip/active均值约.323/.367rad，弱对称未取得明确改善。update300接触和yaw退化，保留200实验候选而非latest。最终200正常0/32、Swing0/8。prefix9.68秒仅瞬时高度/姿态/接触/净空/闭链前缀，不包括累计速度/触限，不能替代完整证书。early_failure含Certificate最终窗口验收失败，不应全解释为提前跌倒；200实际走完10秒窗口。未自动续训，下一重点是持续滑行/力矩触限及保持姿态，而非继续声称完整稳定。
