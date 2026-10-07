# Native high-speed diagnostic 2026-10-05

本次只在 GPU0 完成了新“低速滑行”协议下的 9 个确定性评估：冻结 overnight update50 source、A（原 Gaussian 配方 26-update 候选）和 B（此前的命令权重对照 26-update 候选），每个模型评估 0、+0.5、-0.5 m/s，64 env、8 scored env、10 s fixed command、同 seed。旧 run 和旧 gate 未改写。

## 协议与代码

新协议 `zero_mode=low_speed` 仅对零命令跳过旧 net drift/max excursion 和 0.02 m/s 速度误差检查，改用 `mean(abs(vx)) <= 0.5 m/s`；完整时长、yaw/vy、姿态、双轮接触、闭链、限矩和 runtime fault 仍检查。非零运动仍使用 0.3 m/s 平均绝对误差、方向和支撑 gate。修改文件为 `isolated/motion_recipe_20261004/src/native_stand/command_v6/domain/protocol.py`；候选 checkpoint 的原 spec SHA 通过新 spec 的 `accepted_checkpoint_spec_sha256` 显式引用，防止身份混淆。

## 结果

| 模型/命令 | mean vx (m/s) | mean abs error | peak tilt (rad) | 新 gate |
|---|---:|---:|---:|---|
| source 0 | +0.0039 | 0.0039 | 0.0115 | 8/8 |
| source +0.5 | +0.4015 | 0.0985 | 0.0631 | 8/8 |
| source -0.5 | -0.4117 | 0.0883 | 0.0307 | 8/8 |
| A 0 | +0.0093 | 0.0093 | 0.1017 | 8/8 |
| A +0.5 | +0.3238 | 0.1762 | 0.2183 | 0/8，peak_tilt |
| A -0.5 | -0.3101 | 0.1899 | 0.0214 | 8/8 |
| B 0 | +0.0674 | 0.0674 | 0.1050 | 8/8（低速协议） |
| B +0.5 | +0.4444 | 0.0556 | 0.2479 | 0/8，peak_tilt |
| B -0.5 | -0.2944 | 0.2056 | 0.0306 | 8/8 |

A/B 的 +0.5 峰值倾斜发生在固定评估末端约 8.99 s，属于持续窗口末端的姿态超限，而非单帧早期尖峰；source 同命令峰值约 8.97–8.99 s 且仅 0.063 rad。A/B 的零命令在新协议下均通过，说明 B 的旧位移失败是协议语义差异，不再把它解释为低速能力故障。

## 高速 reward 数值检查

当前线速度 tracking 为 `exp(-(vx-command)^2 / T^2)`，linear weight=4，policy dt=0.01。对任意非零目标 T，静止 vx=0 的 raw tracking 恒为 `exp(-1)=0.367879`，每 policy step 加权值约 0.014715；目标附近 vx=0.5T 时约 0.031152，目标值约 0.040000，反向 vx=-T 时仅约 0.000733。T=0.5、1、2、4 只改变误差尺度，不使静止奖励消失。该公式有持续信号，但在高目标下每 0.1 m/s 的局部斜率随 T 增大而减小；目前没有证据证明必须立即增加 gap reward。另有姿态约束在 +0.5 已先失败，因此本轮不提交未经验证的 reward A/B 长训。

## 参考机制对照

| 参考机制 | 实现位置 | native 对应 | 可移植性 |
|---|---|---|---|
| Fudan 分阶段命令 bank、保留旧能力 | `/home/kellen/fudan_train/plane/tests/test_staged_progress_equivalence.py:39-62`、`docs/overnight_motion_goal.md` | native 当前 stage/retention | 可移植课程/评估语义；不能复制其策略或物理参数 |
| Fudan coarse/fine/gap reward 测试 | `/home/kellen/fudan_train/plane/tests/test_reward_terms.py:66-69` | native Gaussian tracking | 只能作为有界公式候选；当前 L1 信号已非零，需先解决 tilt/保持 |
| Fudan 固定 command bank | `/home/kellen/fudan_train/plane/tests/test_command_resampling.py:25-26` | native fixed command | 可移植显式 bank；不可改变 native action/asset |
| colleague rehearsal/command reward contract | `/home/kellen/桌面/11 (1)/11/wheeled-legged_RL/tests/test_rmuc_reward_contract.py:47-75,127-149` | native reward/retention | 只能借鉴记录与保留逻辑；其 feedback/residual/物理条件不适用 |
| colleague staged command ramp | `/home/kellen/桌面/11 (1)/11/wheeled-legged_RL/tests/test_rmuc_eval_command_ramp.py:16-49` | native fixed/ramp evaluator | 仅用于协议隔离，不能用于 fixed 结果冒充 ramp |

Fudan 成功证据位于其自身 wheel-legged 模型/场景和独立 sim2sim 协议，不能当作 native ±4 可达证明。native USD 的轮半径和有效滑移/扭矩关系本轮未从 USD 读回，标记 UNKNOWN；若仅以 Fudan 参考半径 0.06 m 估算，4 m/s 约需 66.7 rad/s，但这不是 native 结论。native 轮目标上限 100 rad/s，动态可达性仍需物理验证。

## 结论

source 在新低速协议下 0、±0.5 全部通过；A/B 训练后都保留零命令与 -0.5，但 +0.5 均因持续峰值倾斜失败。当前主要阻碍是训练后的正向姿态保持/能力保持，而不是旧零命令位移 gate 或 tracking reward 完全无信号。尚未满足稳定 ±0.5 晋级条件，因此不启动 ±1、yaw 或后台长训。下一项最有信息量的实验是只针对 +0.5 的姿态保持机制做同起点单变量对照，并在两次有真实更新的评估中同时复核 0、+0.5、-0.5；不同时修改 reward、课程和 PPO。
