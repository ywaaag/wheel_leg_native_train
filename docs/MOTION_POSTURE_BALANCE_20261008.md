# B250姿态优化：剪刀腿、长短腿与roll

2026-10-08。用户明确批准native Isaac训练、MuJoCo迁移验证，smoke最多1、formal最多50，
整链最多3小时，GPU1独占。不新增高速/yaw课程，不重用旧实验额度。

## 原始几何证据与定义

MuJoCo独立基线：sim2sim/2026_10_8-18_01__b250_leg_length_baseline，各0/±2单环境30秒，
测试主体16.106秒/PPO0。hip-pivot到wheel-center的三维欧氏距离是真实腿长，
不是关节角镜像、腿长目标或wheel height差。

|command|left/right腿长cm|绝对腿长差cm|轮心水平前后错位cm|roll绝对均值rad|
|---|---|---:|---:|---:|
|0|33.305/33.270|.0357|6.217|.00161|
|+2|25.850/39.463|13.614|7.104|.29685|
|-2|38.203/27.504|10.699|15.739|.21663|

零命令主要剪刀腿，运动时还有长短腿/roll，三者分别记录，不互相代替。
这是MuJoCo参考模型的量测；Isaac来源的真实几何由新链source_eval采集，不能直接移植数值。
hip point使用left/right_upper_leg body origin；USD hip joint localPos1=(0,0,0)已核对，
与MuJoCo对应hip hinge xanchor一致。forward为CAD-z水平投影，up为CAD+y，
roll为upright-reporting姿态，不改变actor原CAD frame观测。

## 本轮奖励选择

已读参考文献.md的奖励工程部分。本轮只借鉴测量误差、单位归一化、有界核的设计思路。
不采用WBC/LQR/补偿/虚拟腿/动作硬对称，也不增加滑移、jerk、加速度、高度门控等其他奖励。
文献中“消除局部最优/保证收敛”等概括不作为本项目证据。本轮不是PBRS，
不声称最优策略不变：用户明确要求改变原本允许畸形姿态的目标。

新增一个composite姿态成本：

```
e_i = relu(abs(measured_i) - deadband_i)
C_i = 1 - exp(-e_i² / denominator_i)
C_posture = mean(C_wheel_offset, C_leg_length_difference, C_roll)
R_total = R_original - 0.5 * C_posture * policy_dt
```

|分量|deadband|误差平方分母|对应宽度|
|---|---|---|---|
|轮心前后错位|.02m|.01m²|.10m|
|左右腿长差|.005m|.01m²|.10m|
|roll|.02rad|.04rad²|.20rad|

最大附加扣分.5/s（.005/policy step），有界且dt只乘一次。
原velocity_tracking/upright/height/contact/effort/action_delta/joint_margin公式、权重和宽度不改。
不对sampled action或actor mean加保持项；不变LR、std、Adam、normalization、network、obs。
这三个分量是一个明确的新目标，不能由本轮归因哪个分量单独贡献收益。

首版prepared配置18_02用较窄腿长宽度.03m，量测发现10–14cm误差会使该核近饱和；
保留首版UNAUTHORIZED、不执行，另生成18_03 v2采用.10m宽度。运行中不调系数。

## 训练/验收边界

恢复原B250 actor/critic/自身Adam/std/CPU+CUDA RNG。正式阶段从B250重新开始，不接smoke。
训练命令分布完整继承B250实际来源：0/±.5/±1，weights=.2/.1/.1/.3/.3，
原随机reset、31s episode、1/2/24/2s时相保持；不加入±1.5/±2的新训练分布。
独立assessment保护已验证泛化：0/±.5/±1/±1.5/±2，9命令各8env完整30秒，source及25/50。
只改姿态奖励；扩大assessment覆盖及新增诊断不改变训练采样。

原motion gate用于两次旧能力退化停止。普通姿态目标未学会不会被称为“遗忘”而提前停。
新增姿态接受条件是本实验选择，不冒充用户原话：

- 同一模型完整9命令原运动gate全部通过；
- 宏平均有界姿态成本较同协议来源至少降低20%；
- 三项分量宏平均分别不得超过来源1.1倍+.005（归一化成本单位），避免互相补偿恶化；
- 25/50两个真实更新间隔、至少25updates间距均成立；缺完整几何窗口不能accepted。

source本身只作为回退，不冒充新姿态通过模型。accepted=null仍可保存诊断候选。
不升级速度档，不自动跑三seed或MuJoCo候选验证；终态后另行复盘其是否值得验证。
姿态目标20%降低只是初步优化，不是左右完全一致、硬同步或精确roll0认证。

## 新spec与已授权预算

spec：configs/experiments/2026_10_8-18_03__motion_b250_posture_balance_v2/spec.json。
授权后SHA：6fde5147ff81e97272ad0e0d401fdfcfac08e4734964195f9b44b2f4b8b23c13。
来源B250 SHA：5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。
来源资产SHA/spec内部身份、完整Adam名字/shape/RNG审核绑定preparation_manifest。
approval_id：motion_posture_9c19164ddb1747858187d6ab2aa9c9f4。
独立ledger：source_eval1、smoke1、formal50；51updates/417792samples，formal409600。
phase墙钟2500/300/6000s，总8800s；整链10800s上限。
phase owner以提交时间核算剩余链预算，monitor wall-limit只收窄phase预算；
预留120s结算，余额不足60s不reserve下一phase，不重置预算或自动重试。

## CPU与启动握手

全量630 passed（27.33s）；针对性22 passed；冻结副本6 passed（.82s），
strict actor/critic/Adam/std初始化审核通过，optimizer_steps_executed=0。
冻结CPU副本使用零额度未授权book，故plan READY_NEEDS_AUTH/BUDGET_EXHAUSTED是预期；
真实授权spec的preflight PASS、health OK、默认supervisor plan零写，run当时不存在。

通过supervisor提交GPU1独占，CUDA_VISIBLE_DEVICES=1映射cuda:0；
UUID GPU-dfc076b6-b082-3065-512a-e21064067db1，未抢占其他任务。
一次5秒握手：worker332739、chain attempt35a08e3f5438411eac21fafc70bf0e7e；
argv/start/spec/output/GPU/session核验通过，submission_verified=true，当前SOURCE_EVAL。
formal_first_update_verified=false，不能称正式PPO已开始或姿态已改善。
run：runs/2026_10_8-18_03__motion_b250_posture_balance_v2，
入口chain.log/chain_progress.json，终态completion_report.md/chain_terminal_report.json。
通知冻结负责人：191bacc3-e5c7-4b8f-ae3d-5677eada837b；后台owner训练、评估、预算、结算、通知。
交互worker不轮询，不改其他任务，不提交Git。

## 本轮文件

新增domain/posture_geometry.py、scripts/prepare_motion_posture.py、
tests/test_posture_geometry.py、tests/test_motion_posture_reward.py、本报告及新配置/诊断目录。
修改command_v6/domain/reward.py、domain/recipe.py、config.py、runtime/env.py、
tools/evaluate_checkpoint.py、train.py、completion.py、stand_chain.py；
MuJoCo脚本补几何量测，更新TOOL_INDEX/ARCHITECTURE/STATUS。
已有dirty changes保留；Recovery共享逻辑不改。新功能仅motion_posture/posture_balance显式声明启用，
默认关闭，原实验奖励与选优行为不变。
