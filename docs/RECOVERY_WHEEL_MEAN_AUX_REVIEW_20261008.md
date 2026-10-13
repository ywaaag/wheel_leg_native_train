# 轮mean辅助loss终态复盘

事件3c6042835931b1b67ab2b1d3；run2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25。COMPLETED，smoke10/formal50，共491520样本、1538.56秒。smoke与formal各自从B25加载，不是连续60更新的同一分支。无完整accepted、不做耐久，不自动续训；通知已按用户新明确权限补发一次，回执独立保存。

## 行为与保持

| checkpoint | Swing通过/入口 | 平均峰高m | DrawBack | R0 |
|---|---|---:|---|---|
| 来源B25 |0/8|.23137|8/8完整10s|8/8完整10s|
| new10 |0/8|.23147|8/8完整10s|8/8完整10s|
| new25 |0/8|.23184|8/8完整10s|8/8完整10s|
| new50 |0/8|.23270|8/8完整10s|8/8完整10s|

Swing全部无首次入口、holdprefix0；env0恢复控制寿命约.30/.32/.37秒，微小前缀增加不算起身改善。报告最佳新10为诊断排序，不能说新增完整能力。来源B25继续是认证fallback。

## 接线、量级与mean

formal50更新共800次公开optimizer hook，每更新16次，有eligible输入及实际非零aux梯度。总eligible72809、全部受控分母309809，占23.50%。第一optimizer step各更新辅助norm/传入PPO+entropy已裁剪actor norm为.2608%–.3801%，平均.3157%；incoming通常约1。不是原始未裁剪PPO梯度，也不是单任务梯度冲突证明。

formal1→50第一步auxnorm .002923→.002879；raw eligible excess .7878→.9044，未稳定下降。随机训练轮mean越界比例仍近100%/100%，真实sample裁剪左轮100%、右轮98.72%→98.05%；std左轮.04886→.05135、右轮.03884→.04168。这是实际训练读回，不是PPO0解析概率。

确定性env0：new10轮rawmean左−2.281..−1.537、右−2.197..−1.004；new25左−2.281..−1.539、右−2.215..−1.004；new50左−2.248..−1.555、右−2.197..−1.000005。仍被裁到同一−100rad/s边界；没有实现计划首个机制目标“解除持续mean越界”。

结论：不是hook未调用/eligible0；本lambda.001首块未提供Swing起身净收益，旧组保留。辅助较小是量级线索，不证明增大lambda必有收益。不能将“mean没有真正移入边界”的实验解释成已证伪解除裁剪机制，也不能据此保证方案B能成功。

## 下一建议

不从new50/latest自动续训，不加长原预算。先用已有真实on-policy读回与保存150D输入做CPU比例核算，准备一次独立、固定更强但有界的mean辅助系数候选，优先验证mean能否移动而旧组不丢。当前schema固定lambda.001，若改变需版本化新声明及梯度/clip/Adam步审核；不能改旧spec或自动把系数扩大数十倍。

方案B仍独立后备：若实际mean已移入可探索区但Swing行为无进步，才更有依据转向低位reward；若其他证据支持reward优先，也需另作单变量声明，不能与mean loss一起开启。观测充分性与critic/Adam适用性仍未证实，已确认的字段/history正确不等于任务完全可观测。

仅本轮离线复盘；新工程准备或runtime需按用户新范围实施。没有新增PPO或发送重复通知。

原始评估与metrics只读；输入SHA摘要isolated/recovery_wheel_mean_aux_terminal_review_20261008/review.json。
