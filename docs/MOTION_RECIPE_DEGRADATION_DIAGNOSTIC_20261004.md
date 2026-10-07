# Native Motion Degradation Diagnostic (2026-10-04)

本报告汇总本轮实际接口验证、同协议配对评估、离线 PPO 对照和一条 15-update 有界轨迹。旧 run、checkpoint、evaluation 和 ledger 未被改写。

## 结论

物理接口和符号链已通过直接运行时检查，未发现左右轮镜像、观测符号、外部 PD 或速度坐标的接线错误。固定批次的一次 PPO 更新不是必然产生负移：旧冻结 batch 的更新为小幅负移，两个独立 batch 的更新为正移；因此更新方向依赖 batch/状态分布。

最具体的新证据是 reward/优势分布：在实际 L1 配方（linear denominator=.04、yaw denominator=.09、tracking 权重4、dt=.01）下，当前低速策略的零命令样本每步总加权 reward 约 12.42，而 ±0.2 样本约 9.9–10.6。第 15 次更新的归一化 advantage 均值为：zero +0.936、+0.2 −0.531、−0.2 −1.411。PPO 因而有充分信号保留站立并压低尚未实现的运动行为；这是一个有较强证据的优化动力学候选，不是已证明的唯一根因。

## 1. 物理接口真值

运行时 USD/Articulation 映射为：

| action | joint / DOF | USD type / axis | 目标与执行 |
|---:|---|---|---|
| 0 | left_hip_pitch / 1 | PhysicsRevoluteJoint, X, authored -X | leg position target, 0.5 rad scale |
| 1 | left_active_link_pitch / 0 | PhysicsRevoluteJoint, X, authored +X | leg position target, 0.5 rad scale |
| 2 | left_wheel_spin / 33 | PhysicsRevoluteJoint, X, authored +X | wheel velocity target, 100 rad/s scale |
| 3 | right_hip_pitch / 3 | PhysicsRevoluteJoint, X, authored +X | leg position target, 0.5 rad scale |
| 4 | right_active_link_pitch / 2 | PhysicsRevoluteJoint, X, authored +X | leg position target, 0.5 rad scale |
| 5 | right_wheel_spin / 35 | PhysicsRevoluteJoint, X, authored +X | wheel velocity target, 100 rad/s scale |

运行时 active backend 的 stiffness/damping 为0，实际由外部 effort-only PD 发送 torque；USD authored drive 参数不是第二个同时工作的控制器。`data.applied_torque` 是 actuator clipping 后送入仿真的显式 actuator torque，不是 PhysX 反作用力测量值。确定性评估中 raw-action clipping 和 near-effort-limit 均为0；训练随机采样约33%–35% 是另一统计定义，不能与评估饱和率直接比较。

速度链使用 root quaternion inverse 得到 body velocity，`vx=-linear[:,2]`、`vy=-linear[:,0]`、`yaw=angular[:,1]`。root-link 位置差分与 reward vx 在考虑 COM offset 后残差标准差约0.00046 m/s；未见符号翻转证据。heading=pi/2 的轮扰动也与旋转坐标预测一致。

## 2. surrogate -440/-391 的更正

使用

`J = mean(min(A_norm * r, A_norm * clip(r, 1-eps, 1+eps)))`，

训练的 negative surrogate loss 是 `-J`。报告中的 -440/-391 不是 loss 本身，而是零命令组的 `delta_mean * group_sample_count`：

| batch | before | after | group delta mean | group delta sum | full-batch contribution |
|---|---:|---:|---:|---:|---:|
| batch0 | 0.979958 | 0.823693 | -0.156265 | -440.042 | -0.053716 |
| batch1 | 0.850492 | 0.737328 | -0.113164 | -391.095 | -0.047741 |

它表示该组 clipped objective 下降，不是“整体改善”。历史报告的组和整体重算存在约 `7e-5`、`2e-4` 数值/统计口径差异；新分析已保留更正，未改写历史文件。

## 3. source、update50 与批次证据

同协议 GPU0 评估（8 scored env，fixed，seed=104）：

| model | v(0) | v(+0.2) | v(-0.2) | gain `(v+ - v-)/.4` | asymmetry |
|---|---:|---:|---:|---:|---:|
| source | +0.005886 | +0.035186 | -0.012956 | 0.12035 | 0.00523 |
| update50 A | -0.029666 | -0.011012 | -0.046960 | 0.08987 | 0.00068 |
| corrected batch0 | -0.029522 | -0.008267 | -0.049677 | 0.10353 | 0.00055 |
| corrected batch1 | -0.033517 | -0.015492 | -0.049958 | 0.08617 | 0.00079 |

A 已在评估前带有明显后向偏置，且 +0.2 已反向；一次更新不能被表述为造成方向反转。B0 相对 A 为轻微方向对称变化，B1 为三组共同负移。按 command 平衡的单变量离线干预后，balanced batch1 的物理结果反而相对 A 进一步下降（zero -0.00695、+0.2 -0.01008、-0.2 -0.00333 m/s），所以“仅 command 数量不均衡”尚未得到支持。

旧冻结 batch 的 command 样本数为 `[-0.2:1280, -0.1:1280, 0:2816, +0.1:1408, +0.2:1408]`；独立 batch1 为 `[1024,1664,3456,896,1152]`。同一 actor 参数上的分组梯度夹角也随 batch 改变：旧 batch 的 zero/+0.2 约 0.601、zero 与 batch0 的约 -0.260，而 batch1 的约 -0.939。actor/critic 参数不共享，不能称作共享参数梯度冲突；这些是相关和敏感性证据，不是因果证明。

## 4. 实际 15-update 轨迹

执行版本为 `isolated/motion_recipe_20261004`，source checkpoint SHA `fc51370b...631e1`，asset SHA `6bf6ce7f...031a27`，GPU0 映射为逻辑 `cuda:0`。64 env × 128 steps，在线 PPO 15 updates、122,880 samples，墙钟 524.573 s，checkpoint `model_update_15.pt` SHA `3ba1a710...0ee299`。三次完整检查（update 5/10/15）各完成 zero、+0.2、-0.2 的 8/8 env，均无 runtime fault；zero standing retention 三次均通过 8/8。

该轨迹中确定性评估均未摔倒，但运动没有达标：

| update | zero mean vx | +0.2 mean vx | -0.2 mean vx |
|---:|---:|---:|---:|
| 5 | +0.01010 | +0.02449 | +0.00399 |
| 10 | +0.01819 | +0.03852 | +0.01007 |
| 15 | +0.00722 | +0.03056 | +0.00026 |

同一轨迹的 rollout 统计显示 update 1–5 时 +0.2 和 -0.2 的 raw advantage 已明显低于 zero；update 6–10 的 -0.2 advantage 继续下降，update 11–15 的 -0.2 归一化 advantage约 -0.91 至 -1.41，而 zero 约 +0.92 至 +1.04。KL 约0.002–0.008、clip fraction 0.008–0.119，ratio pre-check 误差约2.1e-5；没有出现 PPO 数学或非有限值故障。该短链没有定位 source→update50 的最早转折点，也不支持长训。

## 5. 证据等级与未解决项

- **已证实**：物理 action/observation/USD/PD/坐标符号链运行时一致；旧 replay 的空 minibatch 证据问题已修复；surrogate -440/-391 是组和而非整体 objective；一次 PPO 更新的物理方向取决于 batch。
- **较强候选**：在当前策略尚不能运动时，zero 命令的 tracking reward 和样本量共同制造正优势，运动组制造负优势，PPO 会稳定地强化站立偏置。该关系在真实 rollout 中复现，并与动作/速度变化一致。
- **已削弱**：固定 batch 的 PPO 必然负移；左右轮符号错误；只靠 command 数量平衡即可修复；“一次更新造成 update50 的方向反转”。
- **尚不可判断**：累计 source→update50、update50→100 的最早转折点；reset/episode-age、critic bias 与 reward landscape 的相对因果贡献；长期多次更新是否会把小共同偏置累积成大退化。

## 6. 结论与下一步

当前状态为“有较强候选，根因未确认”，长训 **NO-GO**。最有信息量的下一项是固定同一 source、同一 seed 和状态分布，做两个短的 per-command hold-only 对照：保持 reward、PPO、动作和物理契约不变，只让每个 batch 在单一固定命令上采样并记录 raw reward/GAE/actor objective，再与现有混合 batch 配对评估 0/+0.2/-0.2。若运动组 advantage 仍系统性低于 zero，支持 reward/状态分布机制；若差异消失，则优先检查混合命令的状态/episode-age 关联。该方案应先用完整 evidence capture 和 early-stop 执行，不能直接进入长训。

本轮实际在线更新15、样本122,880、离线候选3（各16 optimizer steps，48 native/48 reference），物理接口探针3,880 samples，同协议模型评估共30个已完成的模型×命令组；GPU0，账本 `motion_recipe_source_trajectory_20261004/budget.json` 为 AUTHORIZED、formal 使用15/15、attempt `sourceturnpoint20261004` 为 COMPLETED。没有 accepted motion candidate。
