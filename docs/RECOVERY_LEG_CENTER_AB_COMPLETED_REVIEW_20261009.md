# Recovery 腿中心 A/B 完整复盘 — 2026-10-09

B事件9fd420e98de6571340122e47，COMPLETED，smoke10/formal25、286720样本、990.28秒（16.5分钟），无剩余formal额度。A976.95秒，两臂累计1967.23秒、70更新573440样本。来源均为10_58 bounded_mean实验new25；不混淆原认证B25或Motion B250。

## 同协议结果

|模型|Swing入口/通过|Swing平均峰高m|入口前终止秒|DrawBack通过|R0通过|
|---|---|---|---|---|---|
|共同来源|0/8，0/8|.231973|.330|8/8|8/8|
|A10|0/8，0/8|.231999|.340|8/8|8/8|
|A25|0/8，0/8|.232035|.350|8/8|8/8|
|B10|0/8，0/8|.231659|.340|8/8|8/8|
|B25|0/8，0/8|.230576|.360|0/8|0/8|

Swing全部tilt终止、无入口；多活20–30ms不等于起身或连续保持。B25旧两组均完成原10秒保持窗口（8/8 complete），但continuous_contact失败、terminal_certificate失败：DrawBack平均双轮接触率95.8875%，R0 83.4750%，协议要求完整连续接触。没有把失败缩短窗口或把complete冒充passed。B10旧能力仍通过，B25真实退化。两臂overall最佳均保留共同来源，accepted=false；不能拼B10旧成功与别的checkpoint起身。

## 辅助接线与量级

B smoke wiring PASSED，leg_center_metrics_sha256与真实metrics.jsonl匹配；每更新16次optimizer hook，smoke160＋formal400=560次非空辅助应用。smoke eligible276–520/更新，formal260–520；formal每更新首个step的加权aux norm/已clip PPOactor norm约3.16%–7.83%。formal首步raw eligible均值.54349→末更新.50290（约下降7.47%），但不同rollout状态与分母不同，不是固定状态改善证明。loss下降未换来恢复能力。

actual_pre_action_policy_sampling为null：本项没有完整腿随机动作分布读回，不能宣称局部收腿路径覆盖已提高。现有证书证明声明/事件/梯度接线，不能逐样本认证mask或证明几何/动作探索有效。纯CPU测试与源码顺序支持失败step剔除，不替代未保存的完整runtime mask轨迹。

原始六份source/10/25评估经spec/manifest及checkpoint SHA核验，引用与文件SHA、量级汇总位于isolated/recovery_leg_center_ab_completed_review_20261009/summary.json。A/B单一训练随机流，不把结果泛化为任何辅助训练都无效；但本次lambda.1/前100ms局部中心项没有显示净收益，而且B25损伤旧组接触。共享actor意味着mask外直接loss为零不保证旧输出不变，这次有实际退化证据。

## 下一步

不接受B25，不继续latest，不自动增lambda/扩窗口/续训；保留原认证B25与共同来源实验new25。先利用现有冻结checkpoint和轨迹做CPU固定状态对照：同一Swing起步150D输入重放来源/A10/A25/B10/B25，量化四腿mean目标−实际q、裁剪、左右收短方向及前100ms实际构型；同一DrawBack/R0输入重放查输出迁移，再将B25保持失触与几何/腿目标/轮目标事件对齐。区分“mean确实改了却未形成动态收腿”与“loss下降但关键通道仍未覆盖”，再决定下一单变量。该离线诊断尚未执行，本复盘不授权新runtime或PPO。

本轮修改：新增本报告及isolated摘要，更新STATUS、RECOVERY_STANDING_PLAN；无源码/历史run/ledger/资产/checkpoint修改，无仿真或训练、未commit。此前A/B声明/来源/runtime动作和评分均保留。
