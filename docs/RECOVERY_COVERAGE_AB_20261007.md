# Recovery来源能力复核与BC覆盖对照

当前用户明确要求执行本方案；已允许共享GPU0，不得停止其他进程。
配置根`configs/experiments/recovery_coverage_ab_20261007`，run根同名置于runs。
每项独立spec/budget；旧hold10及所有历史证据不改写。
source50 SHA：`1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。

## 冻结来源复核

source_capability：R0及课程R1（family=R0_perturbed），各seed104/205，
每项8env×10s；balanced_pose_cycle使4个已声明holdout姿态各2env。
共4项/32env certificates，无optimizer/PPO，墙钟<=1200s，evaluate attempt1。
公共supervisor --evaluation-only -> monitor ->共享batch evaluator。
这是初态能力测量，不是新的训练收益或任意扰动认证；原USD/pose数据不变。

## A/B唯一变量

两组source50 strict actor/critic/Adam，同seed/LR3e-5，64env×128steps，
R0原加权初态、10s持续horizon、success_once0、stage cap0；所有连续reward、
物理、BC系数.02、all channels、256有效样本和16个optimizer steps保持一致。
A_first取step-major前256个eligible；B_uniform按整个eligible列表等距区间
中点选256个，无额外RNG或重复索引。覆盖rollout，不保证单batch覆盖整个10s。
各组source10s/PPO0/300s -> smoke10/450s -> formal<=100/2400s，
各<=110updates/901120samples，合计<=220/1802240，完整25/50/100评估。
不做coefficient增强、critic/reward调整、R1训练或final100s。
连两次完整回归失败保持原有界早停。历史hold10不充当本轮同代码控制组。
两组通过公共supervisor独立冻结源码/身份，GPU共享；墙钟不作为算法优劣证据。

## 实现与核验

standing.py新增显式sample_selection，默认first保留旧语义，索引不消耗RNG。
runtime仅在显式holdout_sampling下改变评估初态覆盖，训练reset不变。
共享batch evaluator支持Recovery family/seed/seconds，旧motion默认行为不变。
准备工具scripts/prepare_recovery_coverage.py；tests/test_recovery_coverage.py
检查有效索引、覆盖、RNG、TensorDict/metadata对应及配方一致性。
CPU403 passed，source_capability/A_first/B_uniform plan-only均PASS，无写入。
actual run结果以manifest/terminal/raw evaluation优先，不以latest/BC loss代替能力。
完成后另写复盘；本次不授权自动下一轮或增加系数。

## 本次实证和提交

source_capability终态COMPLETED/exit0，墙钟329.2028s；四项R0/R0_perturbed
seed104/205均8/8，总32/32，PPO0、failure=null、无missing requests。
每项四个holdout姿态各2env。来源已具备这组R1初态能力，未启动R1 PPO。
离线同输入核查：isolated/recovery_coverage_ab_20261007/source_completed/review.json，
包含旧hold10的5批saved BC输入与source/new25/new50/new100 actor比较及输入SHA。
所有批次旧模型normalized RMS随25->50->100增长；这些局部输入不代表全状态分布。

A_first/B_uniform通过公共supervisor提交，submitted=true/submission_verified=true，
current_stage=source_eval；此启动记录不等于formal首更新通过。
worker3225689/3225690；chain attempts
78cdb63ddc9f4595aea309e0fac610b8 / c9514748c6e543549cf85cd44e1ac085。
双方各自冻结代码与spec、独立账本，shared GPU0/preemption=false。
monitor/worker负责后续证书、formal、评估、终态结算及完成通知，不重复提交。

## 修改清单

src/native_stand/recovery/{standing.py,runtime.py,validation.py}；
src/native_stand/command_v6/{train.py,tools/evaluate_checkpoint.py}；
scripts/{prepare_recovery_coverage.py,review_recovery_coverage.py}；
tests/test_recovery_coverage.py；本实验三个子目录spec/poses及独立本地budget；
README.md、STATUS.md、ARCHITECTURE.md、TOOL_INDEX.md与本文。
没有修改历史checkpoint/raw evaluation/ledger，无其他进程停止。
