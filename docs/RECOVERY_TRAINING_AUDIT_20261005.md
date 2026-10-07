# Recovery 训练链审计 — 2026-10-05

本次只读复盘对象为
`runs/recovery_dense_corrected_chain_20261004/formal`。该 run 已停止于
1418 次更新、11,616,256 个样本，仍处于 R0；500/1000 的固定评估均为
0/8 成功、`recovery_timeout`，没有 nonfinite、closure 或控制权故障。
本次没有启动 Isaac 或 PPO，也没有改写历史 run。

## 对照经验报告后的结论

运动训练报告中的 ramp/fixed 配方、双向速度 tracking、旧能力 retention 和
command 分组标准化不直接适用于当前 Recovery：本任务命令固定为零，Recovery
奖励没有运动 tracking 项。当前退化证据是高位后的线速度/角速度和姿态超限，
不是运动命令符号或 forward/backward gate 接线。

确认存在并已修复的共性工程问题：

1. warm-start 原先无条件恢复 checkpoint RNG，覆盖了新实验的 seed。现在默认
   `restore_source_rng=false`；若确实要复现实验轨迹，必须在 spec 中显式打开。
2. Recovery evaluator 会调用 `manual_seed`。现在会保存并恢复 CPU/CUDA RNG，
   不再改变后续 PPO rollout 的随机序列。
3. 反向 Recovery curriculum 原先只写摘要，未保存未完成窗口、已通过窗口和
   stage。现在 checkpoint 保存并可恢复完整状态；恢复后下一次 reset 使用保存
   的 pose family，当前 episode 不被改写。
4. per-update `task_stage` 现在读取 Recovery 的真实 stage，不再固定报告通用
   curriculum 的 stage 变量。

## 保持不变的部分

实际 optimizer learning rate 已由 `initialize_adam(..., learning_rate=spec)`
强制使用 spec 值；SIGTERM 收尾和 BrokenPipe handshake 也已有独立回归，不在本次
重复改动。Recovery 的 reward、PD、限矩、动作契约、物理资产和验收门槛未修改。

## 验证边界

新增及相关 Recovery CPU 回归为 27 passed。全仓库仍有 7 个历史失败：当前同事
YAML 的 SHA 为 `03217b...b1081`，旧 spec 保存的身份已过期；另有既有
`robot_cfg` 简 fixture 假设和 pose-capture 外部身份问题。它们保留原状，不能用
更新旧 spec 身份来掩盖历史证据。本次没有运行时性能或行为结论。

后续使用新的 Recovery checkpoint 时，应显式保留：

```json
{"restore_source_rng": false, "restore_recovery_curriculum": true}
```

这只修复实验可复现性和课程续接，不代表当前 R0 已通过，也不自动授权继续训练。
