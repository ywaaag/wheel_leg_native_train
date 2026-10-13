# update50/100轮控制与不对称时序诊断

用户批准离线诊断，不授权新增模拟/PPO。本次只读已结束18_06 run的
evaluation_50_0_0.json、evaluation_100_0_0.json，原始SHA执行前后重查。
复用脚本scripts/audit_recovery_wheel_timeline.py；机器结果
isolated/recovery_wheel_timeline_20261007/audit.json。原报告/模型/账本未修改。

## update100：明确的逐策略步交替振荡

8个环境最后5秒全部出现：两个轮通道各499次力矩符号反转（500个100Hz采样点），
左右轮各50%采样点触及5.5Nm，任意轮触限100%。这是约50Hz的两步振荡，
不是恒定单向饱和。带符号平均力矩约+.55/-.63Nm掩盖了绝对力矩约4.95/4.88Nm。
env0最后6步的轮目标交替约[-11,-13]与[+6.7,-1.4]rad/s；实际轮速也交替，
请求力矩约[-4.4,-7]与[+13,+4.2]Nm，经物理clip成为[-4.4,-5.5]与[+5.5,+4.2]。
raw wheel actions在此窗口没有超过[-1,1]，所以不是归一化动作先裁剪产生的振荡。
actual applied torque与physical_clipped逐点相等，未发现clip后另一路隐藏力矩。
同窗口双轮接触gate全满足，不能把最后阶段振荡简单解释为失触空转。

控制轨迹列须按声明索引：dq=6:12，wheel dq取8/11；executed normalized action
18:24，wheel目标取20/23乘100；请求34/37、限幅40/43、applied46/49。
target_before/after_joint_limit24:32只有四个腿目标，不能从该列读取轮目标。
先前复盘中若以q列2/5当轮速或四腿target列当轮目标得到的解释不成立。

latest-held5ms PD力矩与policy-end速度存在时相差。其误差约1.77Nm不单独证明
PD接线错误；本次发现是目标、速度、请求、clip均同步交替。policy10ms/frame-history
反馈与wheel Kv=1可能共同参与，尚不能单凭输出轨迹归因于网络、PD增益或某个奖励。
下一实验前先离线同输入检查wheel action delta、历史previous-action编码、reward
action_delta轮尺度及PPO更新差异；不得直接制动/增阻尼/降限矩或更换控制频率。

## update50：不是相同的轮饱和问题

8个环境最后5秒轮力矩均0次符号反转、0%触限、双轮接触gate100%。env0轮目标
约13.32/15.39rad/s、实际14.26/14.44，绝对误差约.94/.95rad/s，applied=clip。
它仍有明显关节镜像偏差（env0最后5秒约.567rad），但可以同时保持接触。

在env0约10.68秒发生失触前100ms，镜像偏差已约1.64rad，失触时约1.68rad；
这属于站立入口约7.88秒后的评分窗口。事件前存在明显不对称，但不证明它导致失触：
瞬态平衡补偿也可能共同改变姿态与接触。各环境事件和前后100ms数值在audit.json。
阈值仅用于诊断，未改变评价gate。接触flag为sensor resultant>2N，非实测法向负载。

update50全过程active joint/control与contact gate已保存，但全过程height、root姿态、
轮几何/腿长未保存，仅末1秒failure tail和原保持窗口聚合。不能精确重建每次失触
与高度偏离先后。末1秒env0高度约.418m而腿长差只有0.063mm；env1高度约.404m、
腿长差约4.24mm。关节镜像大不一定对应腿长差大，不能把“加腿长惩罚”当成已证实解法。
原保持窗口平均腿长差约2.04cm/镜像误差.755rad是窗口聚合，不是全程逐点证据。

## 决策

保留GUI认可的update50作为行为候选，不从update100续训。不再提前选择腿长成本。
目前确认两类独立现象：new100后段50Hz轮目标/力矩振荡；new50窗口中几何不对称、
失触与高度超目标，但末段可以双轮接触且腿长几乎相同。
先继续无需仿真的wheel action delta/历史编码/成本尺度检查；如要证明几何事件关系，
需独立授权的冻结update50 PPO0复核，保存完整height/posture/geometry/control轨迹。
仅重复相同模型评估，不同时改变reward或物理，不把补采诊断当作学习改善。
本次无新的budget、spec或运行，没有加对称惩罚/制动/限矩变更。

本次新增：scripts/audit_recovery_wheel_timeline.py、本文与isolated新证据目录；
修改STATUS和RECOVERY_STANDING_PLAN交接导航。脚本AST与输出有限数值、输入SHA复核通过。
纯离线工具未改运行代码，不需重复整套训练CPU回归；不调用AppLauncher。
