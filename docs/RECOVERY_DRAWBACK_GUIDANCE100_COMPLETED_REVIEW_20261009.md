# DrawBack镜像稠密奖励终态复盘 — 2026-10-09

事件f5208748e0d5c8b4100d1b4f。链COMPLETED表示已正常收尾，formal实际STOPPED_BOUNDED：smoke10＋formal50，60在线更新491520样本、2747.995秒（45.8分钟）。原总100上限未用完，剩余formal40；旧两组在25/50两个完整评估连续失败，StandingRegression confirmed=true/consecutive_failures=2，保护提前停止。剩余额度不授权重新运行。

## 行为结果

|模型|Swing通过/入口|峰高均值m|入口前终止秒|镜像绝对误差均值rad（各自全受控episode）|DrawBack/R0通过|
|---|---|---|---|---|---|
|共同来源new25|0/8，无入口|.231973|.330|.36295|8/8，8/8|
|new10|0/8，无入口|.231867|.340|.35471|8/8，8/8|
|new25|0/8，无入口|.232035|.360|.34690|0/8，0/8|
|new50|0/8，无入口|.231867|.390|.32354|0/8，0/8|

各自episode变长，不能只用其全程均值比较。再限定相同受控前300ms：镜像绝对误差均值来源.328787→new10 .309912→new25 .278507→new50 .231232rad（约下降29.7%）；真实轮心到DrawBack目标平均距离.392861→.391920→.390879→.389665m，仅减少3.20mm（约.81%）。这是具名root坐标几何，不是世界位置漂移。

Swing完整episode最短腿长左右平均：来源[.36310,.37599]、new50[.36200,.37599]m。右腿仍没有明显收短，没有轮子送进DrawBack区域，更对称不代表关键任务进展。各自全受控episode镜像误差p95约.70559→.64421rad，仍远非零误差。没有严格动作投影，不能期待奖励保证完全对称。

旧DrawBack/R0在25/50均进入站立并各8/8完成原10秒保持窗口，但continuous_contact/terminal_certificate失败；不可把完整窗口冒充通过。Swing失败项retained_family是联合验收标记，还同时真实standing_entry失败。最佳仍为来源10_58new25，联合accepted=false；原认证B25保留，新10仅旧组保留的候选，不拼成功点。

## 奖励接线与证据

smoke wiring PASSED，drawback_guidance_metrics_sha256与真实metrics匹配。formal50累计eligible76840、positive74666，新增reward sum18.25678（全并行样本总和，不能当每episode收益）；记录failed/ineligible reward violations均0。说明奖励不是没接上，但当前审计计数不替代全轨迹逐步公式重放，也不能声称已消除腾空/驻留刷分。

原始source/10/25/50 evaluation经冻结specSHA及checkpointSHA核验，完整原始per-env与失触证据仍只读保留。汇总、引用SHA和配对时间统计位于isolated/recovery_guidance100_completed_review_20261009/summary.json。仅单个训练随机流；没有同预算90更新的reward-off对照，不能把全部退化唯一归因镜像项。

本轮实际有效改变主要是对称程度，目标区域的几何进展很小，起身没有收益，并损伤旧组接触。不能接受new25/new50、不能从latest续训或直接增权。

## 下一步建议

先CPU分解现有几何质量P和对称质量S在同一前300ms的幅度、奖励份额及局部构型方向变化，并用现有原生闭链扫描核查“同时收短/转腿”与当前摆腿是否同向。目标是判别位置引导在高距离处过弱、乘积被对称压制，还是策略采样仍无法到达有效动作区域；不能只因镜像下降再次提高总系数。

在这些结果之后准备单变量的双侧进展目标，明确避免“只修对称不移轮”的解，同时独立保护旧输出。现有静态DrawBack目标不证明动态路径可达，尚无成功Swing→DrawBack示教。任何新诊断runtime或PPO需新授权；当前不提交、不追加未用40更新。

本轮只新增本报告与isolated汇总，更新STATUS及RECOVERY_STANDING_PLAN。没有修改源码、run原始报告/evaluation/ledger/spec/资产/checkpoint，无新仿真、训练、通知或commit。
