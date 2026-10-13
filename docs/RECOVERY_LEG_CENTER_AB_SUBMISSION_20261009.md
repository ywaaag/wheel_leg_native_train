# Recovery 腿中心 A/B 授权与提交 — 2026-10-09

用户本轮“同意”批准两臂训练。公共register_authorization核验完整发布SHA后登记两臂独立授权：每臂source_eval1、smoke10、formal25，共70更新573440样本；每臂整链5460秒，两臂10920秒上限。固定物理GPU0/UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，逻辑cuda0，共享，不停止他人、不切GPU。

A：`runs/2026_10_9-15_10__recovery_leg_center_a_from_new25`已通过唯一公共supervisor提交，提交检查READY。一次5秒有界握手记录SOURCE_EVAL，worker身份核验成功；formal首更新未核验，started=false。worker attempt为`e7d756cdb48947f49057b54a5492b0ad`，一次性回执位于`isolated/recovery_leg_center_ab_submission_20261009/A_launch_receipt.json`。这不证明当前持续存活，不轮询日志/进程/GPU。

B：`configs/experiments/2026_10_9-15_10__recovery_leg_center_b_from_new25/spec.json`已AUTHORIZED、preflight PASS、CPU计划READY_METADATA；尚未提交，无B run。按批准的顺序执行，待A终态通知唤醒本会话后一次只读复盘A，核验B当前session/GPU/身份/fresh output/ledger再经supervisor提交B。B正常首次运行在本轮授权范围内，无需用户再次批准；A失败重试、预算扩展或新配方不在授权范围内。项目无现成顺序多臂owner，因此不新增watcher或守候脚本。

两臂终态通知按spec发给当前session `7bbabd67-183d-4185-b686-1aefcd55781b`，at-most-once。比较Swing起身与DrawBack/R0完整保持，A/B不能拼checkpoint能力，保留来源。B仅增加lambda=.1早期腿中心训练辅助loss；控制/reward/std不变。

本轮修改：两臂spec/budget（公共授权登记）、各authorization_receipt及锁文件；新增授权请求与上述isolated提交证据、本报告；更新STATUS和RECOVERY_STANDING_PLAN。A新run/冻结源码由supervisor创建，旧run/checkpoint/原评估未修改。未commit，未停止其他进程。

此前CPU工程验证：两臂各9项冻结PORTABLE通过，全回归720pass/22 Motion历史源码身份ERROR，详见RECOVERY_LEG_CENTER_AB_PREPARATION_20261009.md。本轮资源快照GPU0 502MiB/32760MiB、项目盘21GiB可用，仅代表提交时瞬时核查。行为结果待原始terminal/evaluation。
