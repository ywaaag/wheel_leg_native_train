# U50 Independent-Batch Diagnostic (2026-10-04)

本报告只分析 update50 的两个独立 PPO0 batch、各一次离线 PPO update，以及同协议 GPU0 A/B；不包含在线训练。

## 本轮交付文件

- `isolated/motion_recipe_20261004/capture_independent_batches.py` 与 `capture_independent_supervisor.py`：独立 batch 采集和 exact-attempt 监督。
- `isolated/motion_recipe_20261004/replay_independent_batches.py` 与 `settle_offline_replay.py`：native/reference 单次更新对照和离线账本结算。
- `isolated/motion_recipe_20261004/analyze_u50_independent.py`：本报告生成器；新 spec/ledger 位于 `configs/experiments/motion_recipe_u50_*_20261004*`。

## 监督与身份

- 采集 attempt `runs/motion_recipe_u50_independent_20261004_v2`：COMPLETED，16,384 samples，online PPO=0，wall=17.09s。首次脚本错误 attempt 保留在 `runs/motion_recipe_u50_independent_20261004`，没有样本。
- GPU0 为 RTX 4080，进程逻辑设备 `cuda:0`；GPU1/Recovery 未触碰。物理评估 9 个完整 model×command 组合，wall=420.90s，ledger=COMPLETED。
- child 在 Isaac cleanup 前原子写 terminal，supervisor 只在缺失时补结算；本次 terminal、supervisor_exit、ledger attempt 一致。

## 独立 batch 与离线更新

两批各 8,192 samples，均无真实 timeout/termination；因此 episode 边界没有被物理采集覆盖，不能用这两批证明 timeout bootstrap。reward/storage、command/history/action 对齐和独立 GAE 误差均低于 1e-3。native RSL-RL 与参考实现各 16 optimizer steps，参数最大差异为 0。

| batch/seed | 0 command | +0.2 command | -0.2 command |
|---|---:|---:|---:|
| batch_0.pt / 81023 | 2816 samples, adv+ 0.999 | 1408 samples, adv+ 0.058 | 1280 samples, adv+ 0.041 |
| batch_1.pt / 81024 | 3456 samples, adv+ 0.992 | 1152 samples, adv+ 0.021 | 1024 samples, adv+ 0.018 |

离线动作扫描显示 batch0 和 batch1 的物理 wheel target 变化都偏正，但腿部通道变化和幅度不同；这是冻结观测上的网络/动作证据，不是物理能力结论。

## 物理 A/B

以下均为固定 command、L1 separate tracking、linear=.04/yaw=.09、8 scored env、同 seed 的配对评估。

| command | A mean vx | B(batch0)-A | B(batch1)-A | A/B outcome |
|---|---:|---:|---:|---|
| +0.000 m/s | -0.029666 | +0.028543 | +0.025363 | all 8 completed, no runtime fault |
| +0.200 m/s | -0.011012 | +0.030530 | +0.016567 | all 8 completed, no runtime fault |
| -0.200 m/s | -0.046960 | +0.026557 | +0.034907 | all 8 completed, no runtime fault |

A update50 已有 `vx(0)=-0.029666 m/s`、`vx(+0.2)=-0.011012 m/s`、`vx(-0.2)=-0.046960 m/s`。两个独立 batch 的一次更新分别把三个 command 的 mean vx 向正方向移动约 +0.0166–+0.0349 m/s；+0.2 的方向比例从 A 的 0/8 变为两个 B 均 8/8，但绝对 tracking error 仍约 0.18–0.19 m/s，远未通过能力 gate。接触均为 1.0、饱和为 0、闭链和姿态无 runtime fault。

同协议 formal update50→100 的 mean-vx 变化为：zero -0.053260、+0.1 -0.104162、-0.1 -0.002888、+0.2 -0.155778、-0.2 +0.046353 m/s。一次独立 batch 更新的正向偏移不能解释这些累计变化。

物理控制通道的 A→B 变化保存在 JSON 的 `control_delta_vs_A`；例如 zero command 的 batch0 raw action delta=[-0.01277,+0.02536,-0.00449,-0.00336,+0.00334,-0.00447]，torque delta=[+0.106,-0.075,+0.004,+0.117,-0.015,-0.007] Nm；batch1 为另一组小幅腿部/轮速变化，不能从相关性宣称因果。

## 旧冻结 batch 对照

旧 GPU0 同一冻结 batch 的完整配对结果是 B1/B2/B3 相对 A 在 zero、+0.1、-0.1、+0.2 的 mean-vx 全部负移；幅度约 -0.0006 至 -0.00495 m/s，逐环境差异保存在 `runs/motion_recipe_u50_eval_20261004_gpu0/bias_decomposition.json`。这与本轮独立 batch 的正移相反。

## 结论与限制

- 旧的同一冻结 batch（三个 seed）曾出现一致的负向 A/B mean-vx shift；新的两个独立 batch 没有复现，反而一致为正向 shift。负向偏移因此更像 batch/状态分布条件下的优化现象，而不是一次 PPO update 的普遍必然结果。
- 共同偏置与响应斜率必须分开：A 在更新前已偏后；本次独立 batch 物理结果主要减小共同负偏置，不能称为响应反转。旧冻结 batch 的负移幅度也不足以单独解释 update50→100。
- 没有发现 command/storage/GAE、native/reference PPO 数学实现或 GPU 运行故障。来源 checkpoint 没有同协议 fixed 非零运动基线，因此不能把本次结果与来源运动能力直接比较；仍不能从两个 1.28s batch 判断长期多次更新、完整 episode timeout 分布或 update50→100 的唯一原因。
- 当前不具备长训练条件。下一项最有信息量的实验是固定 update50/Adam，至少多个独立 batch 覆盖完整 9–10s episode 边界，统一 seed/命令分布，每次只做一次 update 并在 0、+0.2、-0.2 做物理配对；设定早期 checkpoint 与 zero-command retention gate，先区分 batch variance 和累积退化。
