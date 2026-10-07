# Motion halfstep tolerance A/B 2026-10-05

本轮从 overnight `update50`（SHA `fa6dcb5eb9466b2484d3ac23688cc4a1ba7729897f02d3e393eef66b956809a9`）重新初始化，未使用 update75。GPU0/逻辑 `cuda:0`，在线 PPO 新增 52 次、样本 425,984；A/B 各 1 smoke + 25 formal。跨 motion 账本累计 2592 次，按 10000 上限剩余 7408 次。

## 单变量

- A：原命令采样 `[0.4, 0.3, 0.3]`（zero/+0.5/-0.5）。
- B：仅改为 `[0.6, 0.2, 0.2]`，其余 reward、per-command advantage normalization、Adam、LR、物理契约和课程不变。
- 新运动门槛：持续窗口 mean absolute vx error ≤0.3 m/s；移除隐含 50% 最小速度门槛。零命令 standing gate 未放宽。

## 结果

| 模型/命令 | mean vx | mean abs error | gate | 失败项 |
|---|---:|---:|---|---|
| source update50, 0 | +0.0039 | 0.0039 | 8/8 | 无（复用同协议原始评估） |
| source update50, +0.5 | +0.4014 | 0.0986 | 8/8 | 无 |
| source update50, -0.5 | -0.4117 | 0.0883 | 8/8 | 无 |
| A update25, 0 | +0.0092 | 0.0092 | 8/8 | 无 |
| A update25, +0.5 | +0.3238 | 0.1762 | 0/8 | `peak_tilt_rad` |
| A update25, -0.5 | -0.3101 | 0.1899 | 8/8 | 无 |
| B update25, 0 | +0.0674 | 0.0674 | 0/8 | `net_drift_m`, `max_excursion_m`, `mean_abs_vx_error_mps` |
| B update25, +0.5 | +0.4444 | 0.0556 | 0/8 | `peak_tilt_rad` |
| B update25, -0.5 | -0.2944 | 0.2056 | 8/8 | 无 |

## 结论

原始 overnight update50 在新 0.3 容差下确实具备零命令和 ±0.5 基线能力。25 次更新后，A 丢失正向姿态裕度；B 提高正向速度但零命令 8/8 后漂，说明把 zero 采样提高到 60% 不是足够修复，存在运动速度与站立稳定性的直接优化权衡。尚未定位唯一根因，也没有证据支持进入长训。

本轮没有物理 runtime fault；所有评估均 8/8 completed。未进入 yaw 或更高速度课程。

机器结果：`runs/motion_halfstep_tol_ab_20261005/summary.json`。
