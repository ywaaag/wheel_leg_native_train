# Per-command Advantage Intervention (2026-10-04)

本轮在已通过接口和坐标检查的基础上，只改变一个因素：actor 使用每个 command 组内标准化的 advantage，critic、reward、command 采样比例、Adam、LR、探索 std、物理契约全部保持不变。

## Offline A/B

输入是 source update500、完整 update1 rollout、同一 Adam 状态和 shuffle seed 81023。old value/log-prob 最大误差分别约 `1.9e-6`、`1.9e-5`；native/reference 各16 optimizer steps，参数最大差异为0。离线模型：

`isolated/motion_recipe_20261004/diagnostics/per_command_norm_replay_20261004/model_batch_1_seed_81023.pt`

同协议 deterministic GPU0 评估结果：

| model | zero vx | +0.2 vx | -0.2 vx | zero abs error | +0.2 abs error | -0.2 abs error |
|---|---:|---:|---:|---:|---:|---:|
| source | +0.00589 | +0.03519 | -0.01296 | .00589 | .16481 | .18704 |
| per-command normalized | +0.00405 | +0.03509 | -0.01631 | .00405 | .16491 | .18369 |

这只消除了少量共同偏置并改善了负向误差，正向命令没有改善，不能作为长训候选。

## Online validation

第一次启动在0 update失败，原因是 PyTorch inference tensor 被新增 normalization 逻辑原地写入；这是隔离诊断代码错误，不是仿真/GPU故障。已修复为离开 inference mode 后写入独立可写 tensor，CPU plan 重新通过；按一次启动故障重试规则使用新输出目录执行。

重试 attempt `pcnormseed20261001retry1`：

- GPU0，逻辑设备 `cuda:0`
- 30 online PPO updates
- 245,760 samples（64×128/update）
- wall clock 1,044.14 s
- checkpoint `model_update_30.pt` SHA `d71c6c49c0d90ab18a8ac42b9561ae7848f725d2b5660735447a94b53e63d5de`
- 无非有限值、闭链、接触或 runtime fault
- zero standing 在 update 5/10/15/20/25/30 均 8/8 通过

| update | zero vx | +0.2 vx | -0.2 vx |
|---:|---:|---:|---:|
| 5 | +0.00779 | +0.03806 | -0.01674 |
| 10 | +0.00483 | +0.03668 | -0.02587 |
| 15 | +0.00013 | +0.03596 | -0.03469 |
| 20 | -0.00316 | +0.03549 | -0.04127 |
| 25 | -0.00610 | +0.04048 | -0.05273 |
| 30 | -0.00942 | +0.03482 | -0.05406 |

负向响应绝对幅度增大，正向响应没有持续增大，zero 漂移逐渐向负方向移动但仍在 standing gate 内。它证明该 intervention 会改变 command response，未证明已学会 `±0.2 m/s` tracking。

## 放行判断

长训 **NO-GO**。冻结门槛要求 zero、正负运动 gate 连续两次通过，并至少一个独立 training seed 复现；本轮正负 tracking error 仍约 `.145–.165 m/s`，远高于 `.03 m/s` gate，且只有一个 training seed。没有启动800-update长训。

当前最强机制候选仍是混合命令状态下的 credit assignment：zero 与运动的 reward/advantage 基线不同，per-command normalization 能减少负向偏置，却不能单独提高正向物理响应。下一步应固定相同 reset/episode-age 分布，比较 critic calibration 或 hold-only command 数据；不要同时改 reward、LR 或课程。

## 独立 training seed 复核

最初的 seed20261001 与 seed20261002 结果逐值相同，审计发现 source checkpoint 的 CPU/CUDA RNG 被 trainer 无条件恢复，spec seed 被覆盖；两次只能作为同 RNG 对照，不能算独立复现。随后在新隔离 spec 中显式设置 `restore_source_rng=false`，使用 seed20261003 重新运行30 updates：245,760 samples、1035.67 s、无 runtime fault，zero standing 每个检查点8/8通过。

真正独立 seed20261003 的结果：

| update | zero vx | +0.2 vx | -0.2 vx |
|---:|---:|---:|---:|
| 5 | +0.00448 | +0.03482 | -0.00173 |
| 10 | +0.00561 | +0.03030 | -0.00555 |
| 15 | +0.01613 | +0.03382 | -0.00010 |
| 20 | +0.00435 | +0.02532 | -0.01569 |
| 25 | +0.00260 | +0.02769 | -0.02175 |
| 30 | -0.00999 | +0.02789 | -0.04764 |

它没有复现 seed20261001 的负向改善幅度，且正向命令更差；因此该干预对训练 RNG/状态分布敏感，不能放行长训。
