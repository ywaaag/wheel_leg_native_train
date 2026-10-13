# Swing → DrawBack 镜像对称稠密引导候选 — 2026-10-09

用户已选择“先做镜像对称奖励实验，量化实际误差”，不要求新增严格动作投影。此文为CPU设计与反事实核算：无仿真/PPO、无runtime接线、无可提交spec或预算登记。

## 引导的物理定义

参照参考文献.md的有界距离质量、平滑门控及对称性思路。材料中“CLF/PBRS彻底消除局部最优”等保证不采纳；本候选不是CLF，也不宣称PBRS保持最优策略。使用本机器人真实实体关节和轮心，不复制虚拟腿或LQR。

DrawBack目标来自A来源评估的真实合法DrawBack初始化轮心root坐标，经镜像平均消除保存姿态微小不对称：左[.2204999,−.1084742,−.0966187]m，右[−.2204999,−.1084742,−.0966187]m。root X为左右轴，保持root坐标语义，不能当世界坐标。该静态目标已用于成功DrawBack起身，但Swing到目标动态路径尚未验证。

镜像误差使用实体left-first四腿q：e_hip=q_Lhip+q_Rhip，e_active=q_Lactive−q_Ractive；不是全部关节直接左右相减。对称目标误差零，不是数值q相等。奖励鼓励零误差，不能保证随机动作或物理状态完全对称。

## 单一耦合奖励原型

两轮到DrawBack目标距离为d_L,d_R。位置质量P=exp(−[logsumexp(d_L²/.25²,d_R²/.25²)−log2])，平滑强调较差侧；镜像质量S=1/[1+mean((e/.10rad)²)]。候选新增r=w·dt·P·S，仅有效受控Swing起身前样本，失败/fault step为0；初候选w=1/秒，dt=.01秒，最大.01/步，不改已有物理控制/观测/action/std。

选择乘积避免“在Swing原地对称”单独拿满分。P针对轮子进DrawBack支撑位置，而不只腿长；S以完全镜像为最优。窄Gaussian对称项在真实约.708rad误差时S≈3.2e−22，切断引导，因此试算后替换为缓衰减有理式，S≈.01980。此式改变目标偏好，不是历史record奖励翻名；不自动替换原beta.3项，不与失败腿中心loss叠加。

## 实际核算与局限

原来源Swing env0：P从首受控.03823到末.08317，S从.98991降至.01980；w1候选整个失败episode反事实新增约.006853，失败步0。原始8env及旧组输出、SHA绑定见isolated/recovery_drawback_guidance_rational_20261009/audit.json。旧DrawBack/R0 mask为0。

理想目标且镜像时quality=1；一轮离目标15cm时P≈.82192，关节hip镜像误差.15rad时S≈.47059。CPU六项检查通过：目标最大、单侧偏离降低、非对称降低且非零、失败0、旧mask0、左右物理镜像不改变质量。两组尺度是工程候选，不是已验证最优宽度；轮心目标接近不认证真实接触支撑，也不保证有能力到达。

瞬时正质量仍可能鼓励在DrawBack附近驻留、空中收腿和改变episode时长；失败步0不能抵消先前刷分。不存在有证据的动态Swing→DrawBack示教，不生成虚假轨迹。更不能因参考文章提出PBRS就忽略此前固定初态完整吸收端点回报抵消的结果。

## 独立实验的准备顺序

来源选同一10_58实验new25，腿中心aux关闭，USD/control/std/三组任务和完整起身保持协议保持。新引导只作用Swing阶段；同时报告双hip/active镜像误差峰值/均值/95分位、腿长差、轮心三维误差、收腿进展、接触与完整站立。旧组不能只测镜像改善不测原保持。

正式接线前需CPU明确：DrawBack目标完成后的平滑退场/衔接起身语义（不永久短腿、不heightgate刷分、不暗中切换actor）、驻留/反复摆腿/腾空/早终止的回报对照、与原reward实际量级的比较。若为进度引入记忆变量，必须披露当前150D未观察该变量的critic别名；优先显式当前状态契约。必要接触可能为机体/腿与地面，不能用“双轮必须接触”预设整个Swing动作。

这些检查通过后才接纯domain/runtime显式几何输入、reward字段、实际读回和smoke证书，再新发布独立声明。建议smoke10/formal25、10/25完整三组评估，来源900/smoke900/formal3600秒；当前仅未授权预算建议。一次只验证这个耦合reward包，不能从结果分别归因位置/对称子项；需要归因时另做分臂。奖励实验得到用户方向确认，不把它视为任意预算运行授权。

本轮新增recovery/drawback_guidance_proposal.py、scripts/audit_recovery_drawback_guidance.py、本报告与两个新isolated核算目录（首版Gaussian保留避免覆盖）；更新计划/STATUS/TOOL_INDEX。未改历史run/资产/checkpoint、未启动runtime。
