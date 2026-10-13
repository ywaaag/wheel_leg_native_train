# Recovery早期腿中心辅助loss：真实冻结batch梯度审核与A/B草案

用户同意实施下一有界CPU审核。已完成纯函数/mask测试及最新new25两份真实rollout的完整batch梯度审核；不执行optimizer.step、不导出模型、不模拟。首选固定lambda=.1进入A/B准备，不宣称学习有效。

## 公式与mask

e=1.6*mu四腿−frame[9:13]/2，cost=mean四腿(relu(abs(e)−.15rad)^2)。仅初始化valid/受控Swing、preclock[0,.10s)、无entry、非failed/fault样本；分母全部受控transition。未clip腿mean用于梯度，四腿同等处理，不注入[+,+,−,+]符号，不改原native动作reference。wheelmeanbounded/原reward含beta.3/std/150D/control保持。

训练外无动作覆盖、无family开关，不是示教轨迹或纯reward-PPO，而是公开PPO＋辅助正则。mask不输入actor，但通过共享权重仍可能影响旧任务。

## 两个真实batch结果

|rollout|eligible样本|原PPOactor梯度norm|unitaux梯度norm|与PPO梯度cos|lambda.1/已clipPPOactor norm|
|---|---:|---:|---:|---:|---:|
|0|520|2.41518|.78250|−.15246|7.825%|
|1|280|2.74249|.36051|−.37627|3.605%|

actor输出重放最大误差8.35e-7，probabilityratio偏离1最大2.39e-5（CPU/GPU重放误差）；使用真实已有sample、savedmean/std、normalizedadvantage重算ratio≈1完整batch surrogate加entropy，**不是历史多epoch/minibatch精确重放**。计算actorclip1→aux→actorreclip，lambda.1合成梯度norm约.991/.987，方向与原clipped梯度cos约.99695/.99943。unitaux与PPO有负cos，表示目标有实际冲突，不能藏作天然有益。

lambda候选.001/.003/.01/.03/.1，仅.1在两batch同时满足工程启发式auxnorm占比3–20%；这是选一个可测量干预的量级依据，非稳定性保证。lambda.03第一约2.35%、第二1.08%，不继续自动扫描更高系数。

actorstate完全未变，critic/Adam未执行任何变更，CPU RNG/threads恢复。旧组/init/failure/window外cost严格0的纯函数测试通过，mask外真实loss最大0。真实preclock由pre-reset postclock−.01推算，接trainer前必须读取真正preaction FSMclock确认边界，不能把这次推算冒称运行接线认证。

## 没有证明的内容

未做Adamstep，不能推断参数或旧组输出更新后不变；对当前moment仅保留继承语义，尚未做动量方向反事实。没有实际动力学或成功收腿trajectory，所以尚无法排除该loss抑制必要摆腿/把策略拉成驻留；2batch梯度量级通过不等于任务通过。局部中心带宽也不能保证所有采样闭链或安全支撑。

## 具体A/B草案

新CPU交付`isolated/recovery_leg_center_ab_draft_20261009`，A_request/B_request/scope绑定new25/parentSHA及audit。A保留现有boundedwheel/recordbeta.3；B只加上述lambda.1辅助。两臂source10_58new25 SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c，同actorcriticAdam/std/RNG，认证B25另留fallback；不从smoke接棒，不拼成功点。

每臂smoke10/formal≤25、full10/25三组，35更新/286720sample，两臂70更新/573440sample；source900/smoke900/formal3600秒每臂，清理60秒每臂，总chain上限10920秒（182分钟上限，不是预计时长）。上述预算未授权，文件标DRAFT_NOT_SUBMITTABLE，不是可提交spec/ledger。

下一CPU工程实现范围已固定：纯schema/公共course编译、默认关闭的真实optimizer hook、preactionclock/family/failuremask、实际aux/PPOgradientnorm/clip读回与旧组证书；smoke须证明eligible/nonzero梯度、mask/cap正常、真实episode事件与完整评估，不只看更新数。测试通过/冻结identity核验后才能发布正式待授权spec。只改善中心误差不算成功，必须Swing实际收腿/入口与保持净改善、旧组保住；无收益回退，不盲目增lambda或延长。

## 文件与验证

新增src/native_stand/recovery/leg_center_proposal.py、tests/test_recovery_leg_center_proposal.py（PORTABLE）、scripts/audit_recovery_leg_center_gradient.py；2tests passed，真实两batch反向传播成功、来源与原NPZ SHA绑定，输出isolated/recovery_leg_center_gradient_20261009/audit.json。新增A/B nonrunnable草案及本报告，更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX。未接trainer/runtime，无仿真/采样/optimizer更新/旧run写入或Git提交。
