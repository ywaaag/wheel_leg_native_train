# 姿态轻评估PPO0工程验证

用户明确授权独立PPO0验证，不授权formal。仅物理GPU1，GPU0其他任务未触碰。公开supervisor --evaluation-only --launch --wait执行有界评估，等待自身结束而非长训轮询。

## 身份和预算

新spec：`configs/experiments/2026_10_9-09_11__motion_posture_smoke_light_ppo0/spec.json`，SHA `31ca1bba57425cec1d769708d6652042b9275d861d6407dcb5a0600963bbcd4b`。
run：`runs/2026_10_9-09_11__motion_posture_smoke_light_ppo0`。
评估checkpoint：原失败smoke的`model_update_1.pt`，SHA `51444ce99f439f046157ba0313d0715731680c9c6f6286dfb195109a7a8727c0`，内部spec/asset/update身份与冻结父声明核验。不是正式训练来源。

独立账本evaluate=1、online PPO=0。exact attempt `7ecb9b0071bc4baa87a17d57ee5afb1f` COMPLETED/exit0；账本实际墙钟88.405236秒（含cleanup）。累计原3小时消耗5834.829444秒，余4965.170556秒（82.75分钟），smoke累计1，formal0。上限600秒未超，未增加smoke/训练额度。

## 实际物理验证

0、+.5、-.5每项8env，各4秒连续完成、无评估异常。协议motion_window_s=null，steady_window_s=[.5,2]。每环境姿态统计151个valid样本，短窗口完整。证明修复路径真实运行成功，不能证明完整保持或姿态改善。

每份raw均`engineering_diagnostic_only=true`；capability_gate NOT_RUN/accepted=false。没有授予能力、阶段或更正smoke证书通过。原FAILED终态/ledger/certificate保留原样。

## 接口改动

- domain/evaluation_requests.py：Motion请求支持显式evaluation_mode full/light，默认full；Recovery拒绝该字段。
- tools/evaluate_checkpoint.py：batch_protocol生成与smoke一致的light协议，light runtime不注入完整standing_protocol；light gate明确NOT_RUN，不按历史source能力回归逻辑提前阻断诊断。
- tests/test_posture_geometry.py：覆盖请求模式、时长一致性、Recovery字段隔离与轻窗口协议。
- TOOL_INDEX.md：登记新增light PPO0语义。
- STATUS.md及本文：登记结果和授权边界。

原reward、物理、控制、网络和PPO配方未变。CPU全量663 passed（26.66秒），专项16 passed，相关py_compile/diff检查通过。计划与submit_ready核验通过后运行。

证据索引：`artifacts/motion_posture_ppo0_light_20261009/`下plan.json、declaration.json、submission_check.json、cpu_tests.txt、result_review.json；result_review绑定三项raw的路径/SHA与终态/账本SHA。run有evaluation_00/01/02.json、terminal_report.json、manifest.json及独立账本，monitor日志在run同级`.monitor.log`。

## 下一步

修复已得到真实PPO0接线证据，但formal前还需合法的工程恢复证书和来源执行依赖迁移审核。不能把本次短评自动写成旧smoke PASSED；不能直接绕过formal前置检查。formal若获得新的明确授权，仍从原始B250恢复，在剩余累计墙钟内最多50更新，25/50完整运动和姿态验收，不升速度、不再次增加smoke更新。
