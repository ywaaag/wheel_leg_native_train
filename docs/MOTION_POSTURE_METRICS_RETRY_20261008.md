# Motion姿态统计接线修复与有界工程重试

用户明确同意修复及行动，2026-10-08。本轮只修复optional posture_balance与RolloutMetrics
字段声明不一致；不调reward权重/宽度、采样、PPO、网络、控制或物理参数。

## 修复与验证

domain.metrics.motion_reward_fields按显式reward配置返回原七项或追加posture_balance；
trainer创建RolloutMetrics调用该接口。保持严格字段集合检查，不自动吞未知reward。
新增CPU测试运行真实reward.compute→metric.add→summary，确认旧七项拒绝新增项、
显式姿态八项汇总成功，且真实trainer调用共享函数。
全量635 passed（26.30s），冻结副本7 passed（.84s），B250 actor/critic/Adam/std初始化审核通过。
真实新spec preflight PASS、health OK，默认plan无run/ledger写入。

修改src/native_stand/command_v6/domain/metrics.py、train.py、tests/test_motion_posture_reward.py；
新增独立spec/ledger/preparation_manifest/授权receipt及本报告，更新STATUS。
旧失败run/spec/ledger/快照不变，不reset旧消耗，不提交Git。

## 身份与累计预算

新spec：configs/experiments/2026_10_8-20_29__motion_b250_posture_metrics_retry/spec.json。
新run：runs/2026_10_8-20_29__motion_b250_posture_metrics_retry。
reward/ppo/curriculum/action/control/asset源于原v2冻结spec，未改实验配方。
B250来源SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。
历史链1927.081423s、online PPO0作为不可变引用保留，原总墙钟10800s；
新链上限8872.918577s，phase source2500/smoke300/formal5892.918577，另留180s余量。
新独立在线上限51=smoke1+formal50、417792samples；旧在线0，累计不会增加原上限。
来源重新完整评估，避免跨新spec/evaluator identity复用旧candidate registry；
这不是补造旧证据或免费评估，重复来源墙钟计入上述剩余额度。
沿用25/50完整9命令评估、姿态改善20%与组件保护/两次真实更新确认，不升档。
此次工程重试完成或失败后不自动重复重试。

## 提交握手

GPU1 exclusive/UUID GPU-dfc076b6-b082-3065-512a-e21064067db1，CUDA_VISIBLE_DEVICES=1。
worker462853，chain attempta3c3e7b7883447168794ac834f44cdfe。
一次5秒握手submitted/submission_verified=true、SOURCE_EVAL；argv/start/spec/output/GPU/session核验通过。
formal_first_update_verified=false，不能宣称PPO已开始或姿态改善。
负责人通知会话191bacc3-e5c7-4b8f-ae3d-5677eada837b冻结；后台owner管评估/训练/截止/结算/通知。
日志chain.log、状态chain_progress.json、终态completion_report.md/chain_terminal_report.json。
交互worker结束，不轮询、不停止其他任务、不切GPU0。
