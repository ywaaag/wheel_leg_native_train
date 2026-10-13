# B250 ±2.5来源复核与有界课程扩展

本轮来源复核已完成；短训链已提交，当前启动握手SOURCE_EVAL，formal_first_update_verified=false。后续状态以run终态为准。

|目标m/s|mean vx|mean MAE|max env MAE|方向率最低|接触率最低|peak tilt|通过|
|---|---|---|---|---|---|---|---|
|2.5|2.901622|0.401626|0.401917|1.000|1.000|0.337761|0/8，仅hold_absolute_error|
|-2.5|-2.843146|0.343384|0.343456|1.000|1.000|0.216539|0/8，仅hold_absolute_error|

PPO0终态COMPLETED/exit0，wall含清理417.317s，预算1200s；无物理运行故障、无缺项，模型SHA不变。流程完成与能力未达标分别记录。

原始与逐环境机器证据：`/home/kellen/wheel_leg_native_train/runs/2026_10_7-20_18__motion_b250_endpoint2p5/baseline/baseline_review.json`、evaluation_00/01.json、terminal_report、monitor_exit；独立账本`/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_7-20_18__motion_b250_endpoint2p5/budget.json`。

短训spec：`/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_7-20_29__motion_b250_2p5_short/spec.json`，SHA `ba51218b1362b32b52dfc003d643938c681ec26c9d12e39d19ab9e1a9a6fc1a0`；run `/home/kellen/wheel_leg_native_train/runs/2026_10_7-20_29__motion_b250_2p5_short`；ledger同spec目录；worker 3641776。

从B250严格恢复actor/critic/自身Adam与RNG；formal重新从B250开始，smoke模型仅接线证据。新reset不恢复PhysX。原reward/LR3e-5/std/全rolloutnormalization/物理接口不变。零/±.5宽度.04，其余1.0；随机reset采样保留，零25%、旧8端点各4.6875%、±2.5各18.75%。仅新增端点组成为实验变量，状态分布也随组成变化，不能单独归因normalization。

总在线上限100=smoke1+formal99，最多819200训练samples；source墙钟2500s/smoke600s/formal14400s，含评估清理。正式每25更新评完整11命令，最终99也评；两次相隔真实更新通过才视作保留确认，不解锁更高端点、不进入yaw/长训。已测旧能力失败两次确认停止；未学会±2.5不计遗忘。

历史motion账本全仓库去重已用5293、保守剩余4707，审计保存于baseline spec目录historical_usage_audit.json；新链最多用100，历史账本只读。

CPU438通过；新spec实际resolver/调度/guard回归通过，plan-only PASS且零写。两次入口元数据拒绝均在预约/物理启动前：baseline缺显式HAPI参数，short spec authorization初始string与链dictionary契约冲突；补当前会话元数据后plan通过。保留首次声明/plan，没有重复物理attempt。

后台共享supervisor/monitor/冻结worker执行前置、PPO、评估、保护、checkpoint及结算；startup submission_verified=true，但尚未验证formal首更新。启动后不轮询，终态由现有completion通知本执行会话。
