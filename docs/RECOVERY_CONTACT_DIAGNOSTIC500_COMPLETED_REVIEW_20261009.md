# Recovery contact-only总500预算终态复盘 — 2026-10-09

事件f77a567810d5adc4592023ba，链COMPLETED、formal STOPPED_BOUNDED。实际source_eval1、smoke10＋formal100，共110在线更新901120样本、2167.308秒（36.1分钟）；formal余额390未使用。500是预算上限，不是完成数；不自动续余额、不重启。

## 停止条件

25/50两次旧DrawBack/R0完整10秒保持但连续接触失败，contact_only_failure=true，允许继续到100，说明新contact-only记录规则实际有作用。100更新DrawBack失败变为saturation/terminal_certificate，contact_only_failure=false；R0反而恢复8/8。standing_regression confirmed=true/consecutive_failures=3/stop_requested=true/stop_effective=true，原其他退化保护正常阻断。progress guard stop=false，不是Swing失触或entry-loss停止，亦不是故障/预算用完。

DrawBack100各8env均完整窗口、双轮接触率100%，但触限超过原5%上限。env0保持saturation_fraction_policy15.7%，env1 18.5%；env0按100Hz held applied torque分解右hip触限15.7%、左active2.1%、轮0。主要指向腿通道，不应误报轮饱和或继续接触失败。held采样不是完整physics/PD峰值，未因本报告放松限矩/评分。

## 起身及旧能力

|模型|Swing入口/通过|峰高均值m|同前300ms镜像误差rad|同前300ms轮心目标距m|DrawBack/R0通过|
|---|---|---|---|---|---|
|来源10_58new25|无，0/8|.231973|.328787|.392861|8/8，8/8|
|new10|无，0/8|.231867|.309912|.391920|8/8，8/8|
|new25|无，0/8|.232035|.278507|.390879|0/8，0/8|
|new50|无，0/8|.231867|.231232|.389665|0/8，0/8|
|new100|无，0/8|.231546|.132837|.385797|0/8，8/8|

相同前300ms镜像平均误差下降约59.6%，但轮心目标仅靠近7.06mm（约1.8%），右腿最短仍.37599m，左腿约.36278m。Swing终止时长.33→.44秒，并无站立入口，不把存活多110ms当起身。镜像改善与有效收腿明确分离；当前引导更容易改善对称，未把轮子送进DrawBack支撑区。

奖励smoke wiring PASSED，metrics SHA匹配；原始source/10/25/50/100 eval逐份核验冻结spec与checkpoint SHA。量化表/引用SHA在isolated/recovery_contact500_completed_review_20261009/summary.json。只有一个随机流且未跑满490，不声称已经证明任何500更新都会失败；但已有100 formal并无有效几何突破，不能继续以迭代不足作为唯一解释。

最佳仍为来源10_58new25，联合accepted=false；new10保旧但不恢复Swing；new100只R0通过，不能拼其他checkpoint宣称全能力。来源与原认证B25保持，不接受new100/不续latest。

## 下一步建议

不自动取消新触限保护或执行剩余390。先CPU反事实比较“乘积位置×对称”与允许更强双侧收腿进展的目标，检查同一真实起步构型的引导方向，避免对称项成为主要可优化捷径。镜像已能改善，真正未建立的是有效收腿/转腿动态路径；需明确位置/双侧进展的辨别力与旧网络动作迁移代价，再发布新的单变量实验。奖励不保证完全对称或动力学可达。

可利用本轮new100的腿力矩/目标差复核旧DrawBack触限，区分提高发力与持续PD预载；这是待做CPU诊断，不是限矩调大授权。若考虑进一步取消触限退化停训，必须另行说明它只改变训练保护，不更改物理40/5.5Nm和最终评分；当前无该授权。

本轮仅新增本报告、isolated摘要，更新STATUS与RECOVERY_STANDING_PLAN；无源码/历史run/evaluation/spec/ledger/checkpoint/资产修改，无仿真/PPO或新通知，未commit。
