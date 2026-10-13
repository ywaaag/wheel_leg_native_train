# 平滑低位几何进展候选：CPU信号与防驻留审核

用户同意执行平滑几何项的CPU设计/核算。本轮完成具体公式、现有8env×3family反事实及合成边界测试，未模拟/PPO/optimizer，未改150D/控制/原reward/历史run/checkpoint。不发布可提交spec或自动应用于训练。

## 固定候选公式

每侧原生hip到主轮中心距离L_i、与重力向下的cos_i，定义
q_i=exp(−((L_i−.15m)/.225m)^2)*(1+clamp(cos_i,−1,1))/2
Q=mean_left_right(q_i)，范围[0,1]。

这是平滑宽核，当前L≈.375米处有非零斜率；不硬截断lengthquality，也不要求一侧未改善则全乘积为零。两侧平均保留单侧小进展，但不宣称对称/支撑安全。原机体tilt/closure/限位保护和完整站立证书不变。

对Swing合法初始化完成时baseline B0=Q_initial，受控pre_entry每步Bnext=max(B,Q_next)。候选奖励r=.3*(Bnext−B)，同epoch累计上限.3*(1−B0)≤.3；只有刷新本episode纪录给奖，未刷新驻留0，重复往复不能重复拿同一纪录。初始化/旧组/首次入口之后0，episode reset独立清baseline；失败/物理fault当步奖励0但纪录可更新，不做terminal释放。没有heightgate，抬高机体本身不减免负cost或增加Q。它不是PBRS、不保持原最优策略，不乘policy dt，因为单位是一次episode进展总预算。

β=.3为可审核固定起始候选，不是已验证最优值；最大额外预算小于failure_once幅度1和success_once10，但不保证全部回报排序，因为延迟折扣/其他reward/任务时域不同。已经得到的进展在后续失败时不撤销，因此仍有“改善构型但不站立”的目标权衡，完整gate不能放宽。

## 实际信号

来源同一认证B25在17_39真实PPO0保存trajectory。Swing env0首控制后Q=.237154、peak=.252981，8env平均新增候选回报.004728，env0有3个纪录刷新样本；不是原hardproduct全0。DrawBack首Q≈.862（在低位短腿更接近支点），R0首Q≈.470；因family mask，两个旧组新增reward严格0。

本次trace是post-controlgeometry，没有exactprefirstcontrolwheelcenter；以首控制后Q作为离线baseline，省略首transition。runtime必须在初始化完成接管前采exactgeometry，用同一物理坐标与baseline，不能假称反事实完整等价。

质量上升也可来自转向重力，而非真的收短；length/direction分别读回及左右各侧贡献，避免把机体翻转使cos变好当安全收腿。当前原tiltfailure挡住部分路径，但仅相关性/终止保护不保证没有几何投机。

## 合成质量序列（非物理轨迹）

- Q=.235持续100步：奖励0。
- .235→.30→.40后驻留：总.0495；驻留阶段0。
- .235↔.30往复25轮：总仅.0195，不每轮重复发奖。
- 相同几何仅高度越gate：奖励0（公式不读height）。
- 失败末步Q突然=.9：末步奖励0，无terminal释放。
- .235→1单调改善：总.2295（≤.3），discounted约.223665；更早达到纪录的折扣回报更高。

并非合成完整成功动力学；不能据此宣称真实动作可达或没有早死偏好。新增项非负且有episodecap，不像连续负成本直接奖励更短失败，但基础reward和既得bonus仍可能令某些失败路径有利。

## 隐状态及实施决策

纪录B是明确episode任务状态，当前150D没有直接输入它，相同物理obs可能因不同历史纪录得到不同reward，critic条件化可能有别名。这一代价必须冻结在新实验声明和诊断，不用hidden control补偿，也不暗扩actor输入。当前finiteRiseHold本就有未直接输入的entry/clock，新增纪录不能因此被说成无影响。

首个可行下一步是CPU/runtime接口准备和有界PPO0reward读回（不是直接长训）：episodebaseline/reset边界、真实pre/postgeometry、非有限/失败mask、currentfamilymetadata、每步record/cap及日志。输入150D仍保持，若用户不接受这项任务状态设计，可另设计memoryless目标reward，但必然重新面临驻留/时间偏好；不能暗换。

发布前CPU必须验证开启只改变附加reward、不改变动作/初始化/RNG/history/optimizer、关闭路径完全等价。reward schema明确版本、beta=.3、geometrylength.15/width.225、bilateralmean、pre-entry/failuremask、reset基准。公共Recovery准备器发布新spec/budget/poses/manifest及完整SHA，meanaux必须删除、轮矩cost关闭，从B25严格warmstart/固定26/25/13，原reward/gates保留。

建议独立PPO0读回三组23秒、总墙钟≤900秒，8scored/64layout，验证非零progress与total/additional reward一致、oldgroups0、状态reset/终态不拼接；该runtime尚未授权。通过之后才申请smoke10/formal≤25、10/25联合验收；不靠几何更优接受模型，旧组保护保持。用户已授权自动终态通知当前session，未来新spec显式启用并绑定实际负责人。

## 改动及验证

新增support_record_proposal.py（纯CPU质量/record_step）、tests/test_recovery_support_record_proposal.py4项、scripts/audit_recovery_support_record.py、本报告；更新计划/STATUS/TOOL_INDEX。相关7tests passed（新4、既有target3），.81秒，真实8env反事实执行成功。输出isolated/recovery_support_record_audit_20261009/audit.json，全部来源SHA绑定；AST/diff通过。无checkpoint/旧run写入，无runtime接线或提交。
