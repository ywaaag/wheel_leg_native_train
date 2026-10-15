# Recovery A 终态复盘与 B 首次提交 — 2026-10-09
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


A事件`0eecf02e13a71201c9a1a484`，run `runs/2026_10_9-15_10__recovery_leg_center_a_from_new25`：COMPLETED，smoke10/81920样本＋formal25/204800样本，合计35更新286720样本、976.9504秒（约16.3分钟）。ledger source_eval1/smoke10/formal25已使用，3个attempt，remaining formal=0；未重试/追加。

## 原始评估复核

读source_eval/evaluation_source.json、formal/evaluation_10_0_0.json与evaluation_25_0_0.json，并核验每份spec/manifest身份及checkpoint SHA；具名汇总与原始文件SHA位于`isolated/recovery_leg_center_a_completed_b_submission_20261009/A_raw_summary.json`。

|模型|Swing入口/通过|Swing平均峰高m|Swing到终止平均秒|DrawBack完整通过|R0完整通过|
|---|---|---|---|---|---|
|来源10_58 new25|0/8，0/8|.231973|.330|8/8|8/8|
|A new10|0/8，0/8|.231999|.340|8/8|8/8|
|A new25|0/8，0/8|.232035|.350|8/8|8/8|

Swing全部合法初始化、tilt任务失败，未进入站立；其continuous_s是入口前诊断，不是站稳时长，完整保持窗口0。峰高约增加0.062mm，延迟终止约20ms，不能算起身收益。两旧组原始hold_window_complete各8/8，并通过原要求窗口；continuous_s含入口前时间，不能拿10.78秒等当新的保持协议。

最佳overall仍为来源10_58 new25（SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c），联合accepted=false。A new25 SHA cfff0b36560fc96db9c39afbcc91df6571d14129b737f976121d3bdbb50e3d41；不作为B来源，不覆盖原始B25。链报告durability NOT_RUN是没有联合accepted候选，不代表旧组没有保持评估。此次是无腿中心loss的控制臂，不能由A结果推断辅助项有效或无效。

## B 已批准的独立首次运行

B `configs/experiments/2026_10_9-15_10__recovery_leg_center_b_from_new25/spec.json`此前用户已明确批准并登记独立AUTHORIZED，未使用/无attempt；本次通知本身未新增授权。按原定A→B顺序，A完成后复验B的session、物理GPU0 UUID、共享资源、输入身份、fresh output与账本，公共supervisor check-submission READY后只提交一次。来源仍同一10_58new25；只增加lambda=.1早期腿中心训练loss。

B新run `runs/2026_10_9-15_10__recovery_leg_center_b_from_new25`，一次5秒有界握手SOURCE_EVAL，worker身份核验成功，formal首更新未核验。每臂原预算source_eval1/900秒、smoke10/900秒、formal25/3600秒、整链5460秒，formal10/25联合评估；不追加额度。GPU0共享逻辑cuda0，不停止其他进程。终态由已有owner通知原负责人，不轮询日志/PID/GPU、不新增watcher。

下一次B终态复盘：先核实真实eligible/mask/辅助梯度与wiring，再同协议对比A/B的Swing入口/双侧动作与旧组完整保持；不只看loss或总reward。B若未成功，不自动延长或续latest。

本次只新增本报告和isolated汇总/提交证据、更新STATUS与RECOVERY_STANDING_PLAN；B新run/冻结代码由supervisor生成。A原始结果、历史checkpoint、源码与物理契约未修改；未commit。
