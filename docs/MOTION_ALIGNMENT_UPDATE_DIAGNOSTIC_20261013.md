# Motion对齐奖励与一次更新诊断准备

本轮只完成工程与CPU验证，simulation=0、optimizer_steps=0，未启动GPU或PPO。历史11_19 run只读。用户同意下一诊断方向；新物理额度尚待明确登记，不沿用旧325次额度。

## 核查结论

历史冻结domain.reward确实将hip_mirror、active_mirror、worst_joint、wheel_heading加入sum(weighted)*dt，再由trainer process_env_step/compute_returns消费。metrics显示非零负值；原冻结CPU反例同状态对称reward=.125、非对称=.095，dt=.01一次。训练采样镜像MAE在u100约.223/.234rad，u200约.444/.460，u300约.454/.470；这不是固定窗能力证书。u6–25平均总密度10.574，末25平均8.879，不能把后期退化直接解释为总回报改善。

旧alignment模块固定CONFIG而spec没有逐项权重，是配置可追溯性缺口。新独立bundle把四项尺度/权重显式列入reward.joint_mirror.terms，并由实际reward.compute传入；有效值严格等于旧CONFIG，未知或漂移值拒绝。不改变权重、控制或gate。旧源码/旧声明不变。

## 实际新增执行路径

独立公共bundle：manual_train/motion/alignment_update_diagnostic_20261013/engine/src。
改动：motion_course/symmetry.py（完整配置）；command_v6/domain/reward.py（消费）；motion_course/domain.py/io.py（有限独立声明、一次结算、不续块）；motion_course/update_diagnostic.py（观察器）；command_v6/train.py（真实rollout与更新前后挂接）。

选定u1/5/6/12/25记录：实际reward总和、各项密度；value/return/raw与normalized advantage；Actor/Critic实际梯度、KL/clip/std；每项低/高成本样本advantage/return及成本相关系数；同一stored observations更新前后的确定性mean目标镜像误差。只copy分布cache，不采样，不改变RNG或梯度。奖励成本是执行后状态量，mean目标是请求量，不能冒称真实q改善。成本/advantage相关也不是因果证明或逐奖励项梯度分解。新诊断不是成功证书。

## 最终声明

spec：configs/experiments/2026_10_13-13_35__motion_alignment_update_diagnostic_block0000/spec.json。
独立任务账本：manual_train/motion/alignment_update_diagnostic_20261013/task_final/task_ledger.json。
来源：旧05_39 Motion block0003/formal/model_update_300.pt，SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb；64zero、height.34、legacy150D、原物理。新Critic/Adam，前5更新Critic-only，smoke/formal各独立初始化来源。

拟运行source8环境基线、smoke25与末8环境行为评估、formal25与末8环境评估；最多50PPO、409600rawsamples、24评分episode、GPU0shared、全链2400秒、512MiB，失败不重试，到块结束停止。smoke25是为覆盖真实30秒episode结束事件，不能用6次更新替代工程证书。

首次13_34声明是CPU准备中间版本，无attempt；最终只用13_35。两份均UNAUTHORIZED。无物理运行结果。

## 验证

新CPU6项＋现有真实MLP诊断4项，共10passed；真实训练_snapshot及完整221+模块冻结SHA相同，冻结PORTABLE10passed。检查公共reward确实消费新参数、符号/dt、真实Actor/cache/RNG不变、cost与storage数量错位拒绝。公共supervisor零写plan cpu_valid=true、READY_NEEDS_AUTH/AUTHORIZATION_MISSING、files_written=0，attempts={}。这是工程准备通过，不是submit_ready或能力通过。原文件和其他任务未改。命令统一见TOOL_INDEX。

## 决策

若低对齐成本样本没有更有利的advantage，进一步分阶段看reward冲突及Critic误估；若有利但同obs目标一次更新反向移动，检查KL/clip/梯度及多个目标冲突；若一次更新方向改善但闭环退化，检查状态分布及持续更新稳定性。短诊断未复现后期退化时明确证据不足，不据此直接追加长训。

## 用户授权后的实际提交

2026-10-13本会话用户明确“授权”，公共register_authorization登记独立50更新/2400秒授权；13_35 spec授权后SHA 5dc9a22b14807b0b34f0f55f81bd05ba1c460dade2d40d12caa08f59bb54bf4f。source与asset及bundle核验通过；submission_check preflight PASS/submit_ready=true，GPU0 UUID-e704e7d4-2965-4712-9759-ba6b9910bd72，共享模式CLI实际生效，CUDA_VISIBLE_DEVICES=0，提交瞬时可用29647MiB。原其他GPU0进程未停止。

公共supervisor已一次提交，attempt3f84e54c350444d18850039f0818600e；单次30秒有界握手SOURCE_EVAL，submitted=true、submission_verified=true，formal_first_update_verified=false，started=false（只指formal启动未证实）。真实执行冻结模块与CPU bundle逐SHA一致。receipt/actual_submission_identity/submission_check保存在同一诊断目录。此后不轮询，由原owner处理source→smoke→formal与结算；有限块完成即停止，notifications仍disabled。现在没有训练能力通过结论；前面UNAUTHORIZED描述为准备时的历史状态。
