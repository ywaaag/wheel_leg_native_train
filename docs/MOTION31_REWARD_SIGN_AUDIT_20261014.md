# Motion31质量v3：方向与奖励符号离线核查

用户因update100双向反向要求检查奖励。本轮只读已有来源/候选轨迹与训练metrics，独立CPU重算，没有修改活动trainer、reward、spec、ledger、PPO或物理，没有启动新仿真/训练或停止任务。

## 当前结论

**未发现tracking reward符号取反、命令Actor编码取反、评估native vx取反或正负命令标签互换的证据。** 这是有限轨迹与当前公式支持的结论，不能表述为完整训练实现已经正确。

**运行证据确认负响应增益一直存在。** 来源就是命令越正、实际native vx越小。update100主要将所有命令的共同速度偏置向负方向移动，没有学会反转这条响应关系。不是“原本完整双向正确，100次后忽然全部给反”的证据。

没有训练时完整rollout/old logprob/value/GAE/minibatch/optimizer前后capture，无法离线证明历史真实Actor优化方向。checkpoint中Adam存在不能替代这些数据。Critic偏差、观测不足和动作动力学探索之间的主因仍UNKNOWN；不能单凭负响应宣称global normalization或PPO有bug。

## 实际检查

1. 实际v3沿用`e=vx-command_vx`，非零tracking为`4*exp(-e²/1)-Huber(e/1)`，zero为`4*exp(-e²/.09)-Huber(e/.3)`。梯度偏好是向command靠近，非向相反方向。姿态/几何cost权重为负，质量失败事件−1；没有发现这些项正负取反。
2. 来源五个命令的actor_input列22–24乘[4,4,.5]与effective_command_pre一致。来源Actor在原观测上CPU重新前向，与记录动作最大误差4.33e-7以内。
3. 独立NumPy用xyzw四元数逆旋转root_post世界速度，native vx按−bodyZ重建。来源和u100十条case保持段全部一致，最大误差约1.045e-7m/s；不是读取state列时取反。人眼的车头方向仍应以同一native坐标校准，不能用显示朝向替代定义。
4. 每条case所有保持段样本固定其他状态，将vx向command移近0.01m/s，tracking density均增加。正负方向及zero均覆盖，35点独立导数网格同样指向目标。
5. 来源真实评估transition上，独立NumPy实现16项raw/权重/dt，与实际v3 CPU实现对照，最大dt贡献误差6.94e-18。zero来源保留完整previous_targets；其他四命令未保存该字段，action_delta在两侧均用相同替代值，明确不计为历史action_delta验证。没有存储reward，故这是评估状态公式交叉核对，不能称为真实PPO storage reward对账。
6. 实际runtime先调用v2基础reward，再由quality wrapper替换geometry为Huber、增加pitch/roll tails及失败事件。与spec v3数学目标核对未发现符号变化；精修state另由checkpoint读回。
7. 静态ControlledPPO的ratio为exp(new-old logprob)，surrogate取max(−A*ratio,−A*clipped ratio)并最小化，与常见PPO符号一致；这不构成历史optimizer step实测。

机器证据：`artifacts/2026_10_14-22_38__motion_reward_sign_audit/audit.json`，包含十条轨迹/JSON SHA、逐env MAE、速度重建误差、反事实reward差、CPU重算误差和训练reward趋势。checkpoint与当前审查代码SHA见同目录`code_and_checkpoint.json`。运行使用共享源码record-only身份，不能夸大为不可变全字节重放。

## 同协议的偏置与增益

| 指标 | 原始迁移来源 | update100 |
|---|---:|---:|
| zero保持vx m/s | +0.34756 | −0.03950 |
| +0.5实际vx | +0.22731 | −0.22151 |
| −0.5实际vx | +0.53662 | +0.08534 |
| ±0.5响应gain | −0.30931 | −0.30684 |
| +1实际vx | +0.12749 | −0.48071 |
| −1实际vx | +0.78551 | +0.27144 |
| ±1响应gain | −0.32901 | −0.37608 |

gain定义`[v(+c)-v(-c)]/(2c)`。zero漂移下降是改善，±0.5负增益基本没变，±1负增益幅度增加；所有指标都变差并不准确，但完整运动能力仍0/40通过。

zero、−0.5、−1的MAE改善；+0.5、+1的MAE恶化，符合共同偏置变化而非学会正确双向响应。姿态检查不能替代tracking，tracking也不能替代姿态。

## Reward量级：有任务竞争风险，不是反号证明

训练rollout均值（混合command、phase、reset，不可当成同命令确定性评估）：

| 更新区间 | total reward/step均值 | linear tracking density | linear Huber density | height density | upright density |
|---|---:|---:|---:|---:|---:|
| 6–25 | 0.06727 | +1.5413 | −0.7853 | +1.8040 | +1.0115 |
| 76–100 | 0.06637 | +1.9362 | −0.9092 | +1.5334 | +1.0840 |
| 101–150 | 0.06559 | +1.8117 | −0.7418 | +1.3687 | +0.9539 |

Yaw tracking约+1.87～1.92，lateral tracking约+1，支撑约+.5；这些可在直线方向错误时仍成立，但近似常量本身不自动产生反向梯度。姿态、height、失败reset、命令响应共同竞争，不能把高总reward解读成正确运动已学会。

6–25训练样本pitch终止959次，76–100为2691次（区间长度不同，不比较其原始计数为严格失败率）；说明随机探索与确定性40/40生存不同，失败事件确实在触发。阶段长保持占比及探索失稳会改变advantage分配，尚无因果capture。

## 下一步唯一优先

不应把reward或command乘−1来“纠正”GUI方向：这样会改变用户任务语义并奖励相反速度。也不应同时加权reward、改归一化、换动作符号。

最有区分力的是下一次获授权的新声明保留一次真实PPO rollout/update capture：按cohort保存command/obs/raw action/old logprob/value/reward/return/advantage/normalized advantage与minibatch顺序，以及更新前后Actor/std和实际正adv样本概率变化；对同一批数据做CPU重算。若需要物理方向校准，另做独立固定Actor轮速/位移诊断，不改控制契约。现有active chain不热加capture、不擅自停止；本轮没有新运行授权或自动续训。

本轮只新增本文和更新STATUS，训练源码未改。CPU行为反事实仅重算状态reward，没有optimizer replay或新物理采样。
