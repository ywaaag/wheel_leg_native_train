# update50 完整更新诊断结果

本次授权链只运行一次。物理GPU1为RTX3060，进程内`cuda:0`；GPU0 Recovery未触碰。update50 checkpoint SHA `af990e...b3e4a8`，资产SHA `6bf6...31a27`，身份与manifest读回一致。在线PPO更新为0。

## 采集结算

输出：`runs/motion_recipe_u50_capture_20261004/`。8个完整`rollout_0..7.pt`和`frozen_initial.pt`均存在，64×128×8=65,536 samples；无重试、无第9块。账本exact attempt `b2308c34889d41d8a2ea4dec5dd5bb0e`，source_eval槽消耗1，formal/smoke为0，墙钟约78.36s。

child最终报告没有被monitor保留下来，monitor按“无terminal report”补写FAILED终态；这是监督交付缺陷，不能把终态称正常完成。数据文件和manifest仍可独立核对，全部8块字段齐全，因而没有重新采集。该缺陷不改变物理数据本身，但说明监督者应在未来先等待/原子写入child terminal再补结算。

episode边界：rollout0–6每块timeout=0、terminated=0；rollout7出现64个timeout、0真实终止，最大episode step=899。故实际覆盖了9秒timeout边界，但没有真实终止覆盖。不能把10.24秒或CPU fixture当作真实摔倒验证。

每块reward均为完整raw/weighted/storage字段。rollout7均值reward约.11585、return约11.5339；独立reward误差≤1.1e-6，storage reward误差1.06e-6，return误差5.8e-6，normalized advantage误差3.8e-5。command/action/done/returned-observation/episode边界对齐均通过；timeout采用安装版`V(obs_t)`，以pre-reset终态value替代的反事实在最后块会改变return最大约.0954、normalized advantage约.827。该差异被记录，不能直接解释为长期退化原因。

## CPU replay

使用最后完整块、update50自身actor/critic/Adam，固定shuffle seeds `81023,81024,81025`，每个实际PPO与参考实现各4 epochs×4 minibatches=16 optimizer steps，共实际48、参考48。输出：`isolated/motion_recipe_20261004/diagnostics/u50_replay_20261004d/replay.json`。没有导出模型、覆盖checkpoint或加入训练候选。

old value/logprob/mean/std重建和全字段minibatch对齐通过；实际与参考参数最大差异均为0。整体 surrogate 改善分别约 .003402、.005410、.004244。各命令组改善（seed81023/24/25）：

| vx | seed81023 | seed81024 | seed81025 |
|---:|---:|---:|---:|
| -.2 | .003848 | .008379 | .006410 |
| -.1 | .001820 | .000747 | .000813 |
| 0 | .001096 | .002310 | .001932 |
| +.1 | .000843 | .002309 | .000513 |
| +.2 | .015600 | .022042 | .017719 |

KL约.0026–.0101，clip fraction约.017–.154；+0.2组的优势加权改善明显最大，说明这个冻结批次上整体目标改善主要由+0.2样本贡献。所有组的目标均为正，没有发现一次更新中某组surrogate必然恶化的实现错误。CPU动作均值、std、scaled leg/wheel target和一致修改所有history frame的command反事实已保存于JSON；它们是网络敏感度，不是物理能力或真实漂移。

## 结论

确认的问题：监督链没有保留child terminal report，造成账本终态被补写为FAILED；这属于证据/监督缺陷，不是物理故障。采集数据本身证明：reward→storage→GAE→return链在已记录块上数值一致，timeout边界确实出现，真实终止未覆盖；实际PPO和最小参考实现一致，未发现shape、符号、minibatch对齐或optimizer归属错误。

被削弱的假设：本批次没有支持“PPO实现数学错误”、actor/critic共享梯度冲突、timeout跨episode泄漏或reward dt重复乘；也没有支持物理全面崩溃。+0.2组占据较大优势加权收益，支持“批次优化偏向命令组”的优化动力学假设，但不足以证明它造成后期反向运动或长期站立退化。新采集是update50新reset分布，不是历史update51或50→100轨迹；一次CPU更新不能推出真实漂移加重。

下一步确实仍需要物理对照，但不是长训：先修复monitor child-terminal原子交付，再做一次同一update50 checkpoint、同一完整字段采集的重复性对照，重点比较timeout前后优势和正负/+0.2命令的加权贡献；若重复稳定，再设计单变量命令采样/优势归因实验。不要从本次数据直接续训，不调reward/LR/std/课程。
