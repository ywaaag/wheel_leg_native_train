# B250 姿态formal工程恢复提交

用户2026-10-09明确授权GPU1 formal提交及终态通知当前会话。恢复证书版本motion_light_none_window_recovery_v1，证书SHA `7c60d4776692505ca9418fef032bdbf3602ed58ce38818ec7f5d5b7560f21df7`。

新spec：`configs/experiments/2026_10_9-10_14__motion_posture_engineering_recovery/spec.json`。授权后SHA `e2fec82cefc4dbe8f288af87cdfeb8e5b8c312344fed2caadf5c3ab9ce043e6c`，授权前SHA保留在receipt。独立ledger，历史消费不重置，source/smoke新额度0，formal最多50更新/409600样本，25/50完整九命令运动与姿态评估。不升速度，不改配方，不从smoke模型续训。

来源：`runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`，SHA `5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。恢复actor/critic/自身Adam/std/RNG，新物理reset。旧已用5834.829444秒，原累计10800秒剩4965.170556秒；此spec formal阶段墙钟上限4013.327793秒，先到即停，不能追加smoke或formal预算。

一次GPU快照GPU1无compute任务，UUID GPU-dfc076b6-b082-3065-512a-e21064067db1，CUDA_VISIBLE_DEVICES=1、逻辑cuda:0；GPU0未触碰。当前负责人HAPI session `191bacc3-e5c7-4b8f-ae3d-5677eada837b`。恢复专项53 passed；登记后submit_ready=true，preflight PASS、storage PASS，stages仅formal/terminal_reconciliation。

公开supervisor --formal-only --launch --handshake-wait-s 10提交；一次有界握手返回RUNNING、identity_verified=true、started=true、actual_updates=1。formal exact attempt `c80ded162b1444c5a2656aef831fe7a7`，trainer PID1017417，monitor PID1017415。这证明首个真实更新完成，不证明姿态改善或运动能力通过。

run：`runs/2026_10_9-10_14__motion_posture_engineering_recovery/formal/`。progress、checkpoint、原始评估、terminal_report与completion_report均在此；启动日志按launcher/monitor记录在run相邻formal日志。后台monitor负责预算、退出、结算和已授权终态通知。本次交互不轮询，不自动重试。

证据：`artifacts/motion_recovery_readiness_recheck_20261009/`中的authorization_request.json、authorized_submission_check.json和launch_receipt.json。旧FAILED、原source/smoke/PPO0证据及账本未改写。
