# Recovery腿探索中心与参数化候选：CPU审核

2026-10-09用户请求下一步。读取最新new25 14_00真实随机NPZ，按起步clock.01–.04s共332个受控sample，解析Gaussian尾概率/现有局部目标盒，不采新动作、不模拟或optimizer。来源SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c绑定新boundedwheel spec；未改runtime。

## 分布中心离收短方向很远

已找到局部几何方向[+,+,−,+]，target参考仍原reference，legscale1.6rad。每状态计算target超过当前q对应方向的独立Gaussian尾概率，不用有限MonteCarlo零命中冒称概率精确为零。两hip边界距离mean平均约14.46/16.43std；四通道联合方向概率均值约5.45e-92。该结果只针对这一充分局部路径，不代表所有起身动作概率。

另计算每通道相对q沿所需方向.025–.15rad的目标盒；positiveCDFtail使用survival差避免数值消减。原分布局部盒概率最大约8.33e-94。该目标盒具有前次局部闭链几何依据，但随机执行不保证闭链动力学或反弹成功。

## CPU候选比较

|候选|四通道方向概率均值|局部目标盒概率最大|结论|
|---|---:|---:|---|
|原std|5.45e-92|8.33e-94|几乎没有这条局部构型探索|
|腿std×2|6.48e-27|4.70e-27|仍很小|
|腿std×4|1.37e-9|1.47e-10|仍很小，并改变全部旧任务随机动作|
|腿std×8|1.64e-4|3.32e-7|方向覆盖增加但精确局部盒仍低，多通道裁剪增加|
|所有腿mean=tanh|1.45e-85|3.48e-87|没解决两个hip中心偏差|
|当前q作为residual参考|6.96e-76|1.77e-77|原输出本身也偏置，参考改变不自动解决|

std×8时早期四腿raw裁剪概率均值约2.49%/35.15%/6.09%/53.57%；本次不建议直接扩大std训练。alllegtanh改变旧DrawBack确定性目标峰值每通道约.126/.142/.054/.087rad，currentqresidual则峰约.835/1.432/.430/1.432rad。后者还改变动作含义/控制参考，明显不属于严格行为迁移；不自动接入，不以“残差”标签隐藏物理改变。

## 决策

这三类直接修改均未通过候选审核，**不发布可提交训练spec，不继续原分布长训，不翻转关节符号**。提升std或平滑clamp不能把远离正确构型的探索中心自动搬回来。现有高度/几何奖励在没有该类动作样本时也不能保证把策略带入支撑区域；该证据仍不唯一确诊reward或critic。

下一应审核能够覆盖第二个探索中心的显式策略分布候选，而不是固定控制偏置：例如原策略Gaussian与围绕当前实体q的局部探索分量组成可审查混合policy。必须先纯CPU比较实际盒覆盖、旧状态输出变化、普通/混合log_prob和PPO存储语义，以及动作是否可执行。分量中心不能由family隐藏开关或固定动作轨迹指定；不能在env中注入控制/托举。若引入state-conditioned prior或改变actor分布，这就是新的行为/架构变量，需明确声明和用户审查，不属当前授权runtime。

混合policy只是下一候选研究方向，尚未实现/验证，不能宣称能保旧能力、能恢复或当前边界必然允许。也可选择进一步逆向课程状态覆盖，但不得伪造来自成功Swing轨迹的初始化。应先选一个可审核方案，再提出独立最小物理验证，不同时叠多种干预。

## 产物与验证

新增`scripts/audit_recovery_leg_exploration.py`、`tests/test_recovery_leg_exploration_proposals.py`（PROJECT_DATA），1数学测试通过：零中心独立方向1/16、极尾log概率有限/目标盒非零；真实332sample审核执行成功。最终输出`isolated/recovery_leg_exploration_final_proposals_20261009/audit.json`SHA绑定spec/evaluation/NPZ，初版保留。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX和本报告。无runtime/训练源码/旧run/spec/ledger/asset/checkpoint修改，无新仿真/采样/optimizer或Git提交。
