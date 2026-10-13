# Recovery动作分布与Swing入口迁移：CPU候选审核

2026-10-09用户同意100更新失败后的下一CPU审核。读取09_40 frozenB25真实16384transition，不运行Isaac/新采样/optimizer，不改现有learning/runtime或checkpoint。CPU新增候选函数不自动启用，不能称已解决起身或旧能力保持。

## 现有概率与物理控制语义

已核对安装的RSL GaussianDistribution与PPO.act/process_env_step/compute_returns。当前MLP输出Gaussian mean，sample与log_prob都在未裁剪的6D action坐标；env wrapper/contract再clamp到[-1,1]并变成实体腿位置/轮速目标。多个rawsample映射同一control属于动作别名，不等于概率密度写错或PPO梯度必为零。腿位置仍reference+1.6*action，轮仍100*action；没有改变物理尺度/PD/限矩。

旧来源权重/Adam迁移同一state_dict不保证改变distribution后的行为不变，必须把parameter warmstart与behavior retention分开。仅改wheel output不会直接修复Swing腿目标首步大跳变，也不代表已经学会收腿。

## 同一来源状态上确定性核算

使用64point Gauss-Hermite无RNG积分，报告每个状态内Gaussian采样经物理clamp的std，再跨状态求均值，不把均值trajectory变化混进探索std。两旧组仅采2.56秒含初始化，不能替代完整10秒Retention。

| 候选 | Swing轮物理目标随机std左/右 rad/s | 迁移代价/接口问题 |
|---|---|---|
| 原Gaussian→硬裁剪 | 0 / .0824 | 左轮实际探索为零，右极小 |
| 轮sample tanh(Gaussian) | .470 / .547 | std同时被压缩，概率需Jacobian与latent/cache一致；旧输出改变 |
| 六维sample tanh | 同上 | Swing腿目标峰差约.381rad，旧R0/DrawBack也改变腿目标，不优先 |
| 轮mean hardclamp，再Gaussian | 2.844 / 2.261 | deterministic物理目标可保持，但rawmean越界区clamp导数0，mean学习可能卡住，不优先 |
| **轮mean tanh，再Gaussian** | **4.182 / 3.616** | 保留原std与普通Gaussian likelihood，仍有sample硬裁剪；deterministic轮目标改变，须独立复验 |

首选准备候选为wheel bounded mean Gaussian：仅通道2/5 mean=tanh(rawMLPmean)，四腿mean保持，std参数保持、sample从该Gaussian产生；deterministic播放使用同一mean，log_prob普通Gaussian，无随机变量tanh变换的Jacobian。不能将其与tanh整个随机sample混称，也不能使用旧rawmean计算新sample的log_prob。MLP链式导数tanh在源mean≈−1.875/−1.71处非零，可区别动作变化；并不保证优化或物理能力。

## 旧能力输出变化明确存在

wheelmean tanh候选相对来源硬裁剪mean的确定性轮目标绝对差：R0均值.0164/.0925rad/s、峰.458/.789；DrawBack均值1.457/1.301、峰23.830/14.427；Swing均值4.919/7.403、峰8.953/23.494。腿目标差严格0（仅轮候选）。DrawBack起步个别状态变动较大，因此不能宣布无损迁移，必须独立三组PPO0；旧source证书不能当新distribution能力证书。

Swing原轮目标接近−100仍会变为约−90到−99，不是轮制动/轮置零。新std有效采样改善但方向仍负，可能仍无法恢复；不能只因std非零接受候选。

## Swing入口腿动作核查

首个受控posttransition实际腿q与target分开记录，左右顺序[legL0,legL1,legR0,legR1]不做镜像虚拟映射。来源Swing初接管目标与实际位置在三通道约1.1–1.6rad偏差，原先已有记录。本次首次各episode摘要可见，但采集没有precontrol全q，不能把postjointq宣称exactpre动作误差。本轮mean-only轮候选不掩盖/修复这个腿迁移问题，不同时添加action bias或初态支撑控制。

## 推荐下一步（尚未接runtime/发布训练spec）

先准备版本化wheelmean-bounded distribution接口，训练/评估/播放/导出共享model构造；给source加载声明、state_dict/Adam坐标保持证明及有效distribution参数读回。核对RSL distribution.mean/std/params/entropy/KL/log_prob/API，source_eval明确应用该candidate；不把旧actor证书误用为变换后通过。

完成CPU真实RSL测试后申请独立三组PPO0：候选DrawBack/R0完整10秒能力与Swing失败前探索联合审核。只有工程与旧能力均无明显退化才准备短训；若旧能力立即退化，不继续PPO掩盖迁移代价，而另设计迁移方案。不能加入familymask控制或隐藏状态机改变wheelmean。

未知：对完整DrawBack/R0保持的影响、是否解除真实随机裁剪并产生有效支撑动作、critic适用性和长训收益。当前无新runtime/PPO授权，本轮不直接接现有learning.py。

## 文件与验证

新增`scripts/audit_recovery_action_distribution.py`、`src/native_stand/recovery/action_distribution_proposal.py`、`tests/test_recovery_action_distribution_proposal.py`，候选函数纯CPU不在runtime调用。4tests passed：Jacobian与torch变换分布一致、轮外腿不变、源区非零导数、极限inverse拒绝、mean-only普通Gaussian概率和链式梯度。数据输出`isolated/recovery_action_distribution_audit_complete_20261009/audit.json`全部输入SHA绑定，初版审核也保留，无复制大轨迹。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX与本报告。没有模型/旧run/资产/控制/ledger修改，没有仿真或optimizer、无Gitcommit/清理。
