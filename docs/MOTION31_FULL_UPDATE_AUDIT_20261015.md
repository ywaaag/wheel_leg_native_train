# Motion31完整一次PPO update离线检查（2026-10-15）

## 结论与决策

已完成用户授权的完整检查。单步结论需要补充：**在同一batch完成全部16步后，包含−1.5 Actor贡献的A臂使旧任务固定样本surrogate下降；只消融该贡献的B臂使旧五任务全部改善。** 这支持“新负向任务在多minibatch/多epoch更新中挤占旧任务目标”的局部机制。不能继续用先前单步结果否定这种可能，也不能把本次结果提升为历史数百更新反转的唯一根因。

A的全batch目标仍改善，说明这里出现任务间权衡，**没有证明PPO surrogate符号反了或Adam整体在上坡**。本次没有改global normalization、Adam初始化、奖励、停车或物理；不启动仿真/在线PPO，不导出可续训模型。

下一训练决策应优先处理新旧任务更新的权重与强度，并保留来源1600；本证据不支持为了解决本次退化而同时改reward、取消停车后原样长训。可另设单变量短对照验证减少新负向任务贡献/增加旧任务保留，或减少每batch更新强度；这些是不同方案，不能一起改。本轮不执行新在线实验。

## 方法与身份

复用`runs/2026_10_15-16_00__motion31_u1600_frozen_advantage_probe`的65536条实际采样transition。来源为v3/update1600，SHA256 `83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`；capture SHA256 `b92f0bf22fcac50147c07641ff5e0d1863531a918b033c2b85ff2314d889cfde`。

直接调用当前生产实现`ControlledPPO.update`，不是另写PPO优化公式。每臂4epochs×4minibatches，使用同一新CPU shuffle seed20261015，并逐batch核验样本ID SHA及cohort计数一致。实际安装的RSL-RL在epoch间复用同一份shuffle排列；未将此误述为每epoch重新shuffle。

- 两臂完整恢复同源Actor/Critic/Adam；std固定，LR3e−5，maxgrad1，返回值/优势和归一化结果不变。
- A七cohort全部参与Actor更新。
- B只将−1.5样本的Actor advantage贡献置零，样本仍在minibatch、Actor valid分母不变，Critic仍使用全部样本；不重填或重新归一化。固定std下熵项无均值梯度，样本仍保留不会改变本对照的含义。
- Actor和Critic分别裁剪，二者无共享参数。两臂最终Critic参数改变量逐项相等。
- CPU对同一记录输入重新前向得到old log-prob/mean/std，初始ratio严格为1；原GPU log-prob仍保留在原capture。不声称CPU与历史GPU bit-exact。
- 每次step后使用固定全batch评估surrogate、KL和六通道动作变化；观察器不抽样、不改optimizer/分布缓存。生产update内部原有随机forward保留，两臂CPU RNG起点相同。
- 原来源文件和capture不变，内存source checkpoint也逐项相等；不生成新checkpoint。

## 每步结果

正surrogate gain表示相对来源的固定样本clipped surrogate改善，不等同于速度或姿态改善。

|step|A旧五组gain|B旧五组gain|A旧五组KL|B旧五组KL|
|---|---:|---:|---:|---:|
|1|+.00002070|−.00000127|.000500|.000080|
|2|+.00000406|+.00000388|.004061|.000322|
|3|−.00009289|+.00002601|.006458|.000879|
|4|−.00006924|+.00004333|.005812|.002024|
|8|−.00046407|+.00001820|.010122|.002172|
|12|−.00008145|+.00004065|.005369|.004034|
|16|−.00010979|+.00005066|.004861|.001459|

A旧五组从第3步开始至第16步均为负。B从第2步起均为正。两臂最终Actor参数改变量cosine .227982；差异不只是幅度缩放。

## 最终逐命令

|目标vx|A gain|B gain|A KL|B KL|
|---|---:|---:|---:|---:|
|0|−.00011575|+.00004854|.004467|.000923|
|+.5|−.00013840|+.00006248|.003890|.000922|
|−.5|−.00006940|+.00005236|.005505|.001628|
|+1|+.00000745|+.00000170|.003972|.001679|
|−1|−.00022291|+.00009174|.007123|.003034|
|+1.5|+.00023951|+.00056218|.004748|.002834|
|−1.5|+.00470222|+.00069268|.006908|.002978|

A全batch gain **+.00085796**，B **+.00026695**。A为−1.5取得更大目标收益，同时牺牲四个旧命令；B全batch收益较小但七组均正。A最终全batch clip fraction5.356%，B .650%；生产update报告的minibatch平均KL分别.005836/.002150，clip fraction7.160%/.937%。这些统计scope不同，不混为同一数字。

## 已支持与未支持

- 运行数据＋CPU反事实支持：本批完整生产PPO更新中，加入−1.5 Actor贡献会改变更新，使旧五任务总体surrogate变差；同一minibatch排列和Critic目标下消融能改善这个指标。
- 不是已确认实现错误：PPO总目标可以改善而部分cohort变差；clipping不保证每个任务保留，也不保证每个正advantage样本概率上升。
- 不支持：本批global centering把旧正A翻负；observation running normalizer漂移；仅靠修改pitch权重必然解决；本次单步/多步结果直接证明实际vx反向。
- UNKNOWN：更新后闭环物理行为、原训练5次Critic适应后的梯度分布、不同shuffle/其他rollout的稳定性、历史250–1000逐次更新因果。

## 覆盖限制

1. 一份来源1600的1.28秒捕获窗口，部分−1.5样本处于失败/reset后的不同episode age；不是整episode或多seed证据。
2. 没有模拟原formal最初5次Critic warmup；本次价值/优势为来源初始化反事实。
3. 执行一次完整update，不是反复对同一batch长训；新rollout状态分布变化尚未覆盖。
4. B是梯度贡献消融，不是“更改采样比例”的直接仿真实验，也不是按组归一化；不能据此指定后者一定正确。
5. 未测试Adam重置、gamma/lambda或奖励替换；不将这些假设宣告排除。

## 工具、验证与消耗

扩展`scripts/audit_motion31_adam_step.py --full-update`，保留原单步默认；扩展`tests/test_motion_adam_step.py`覆盖实际生产update的16步、同排列、Critic一致、来源/RNG不变与固定std。CPU fixture先发现并修正审计脚本的语法、sample ID dtype及ControlledPPO初始化mask重置接线问题；均未进入真实capture的optimizer重放，不是生产训练代码错误。

CPU全PORTABLE：**482 passed、8 skipped、4 warnings**；定向5 passed。只改审计脚本、测试和本报告/STATUS/TOOL_INDEX，不修改生产PPO或配方。

新证据：`artifacts/2026_10_15-16_40__motion31_full_ppo_update_offline/audit.json`、`audit.md`；包含逐步逐命令六通道动作变化、梯度范数、KL、sample ID SHA、source和实现SHA。实际约6.99秒CPU（含加载与汇总），**32次真实batch离线optimizer step＝每臂16**；与上一轮真实batch4次合计36，CPU fixture不计入真实batch重放。新增online PPO0、GPU/Isaac墙钟0、导出模型0、通知0，旧ledger不变，没有Git提交。
