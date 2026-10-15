# 25D Motion学生PPO完成评估复盘

本轮调用scripts/review_motion_frame25_ppo.py，消费已执行原始评估；simulation0、offlineoptimizer0，无新增仿真/训练。核验source/checkpoint/evaluation SHA、8环境分母与motion_standing034_v1原协议。原run/账本/模型不修改。

run：2026_10_13-17_09__motion_frame25_asymmetric_ppo_closurefix_from_bc，source_eval＋smoke25＋formal300正常COMPLETED，共325PPO/2662400rawsamples/7198.85秒。formal有效Actor样本2416640，实际Actor minibatch optimizer steps4720（不是4720个PPO update），前5次Critic-only，BC0，来源Actor独立初始化而非继承smoke末模型。

|候选|最短首episode秒|平均秒|完整协议通过|终止|
|---|---:|---:|---:|---|
|source0|2.08|2.109|0/8|{'tilt': 8}|
|formal25|1.77|1.778|0/8|{'tilt': 8}|
|formal50|1.94|1.960|0/8|{'body_contact': 2, 'tilt': 6}|
|formal75|1.42|1.424|0/8|{'tilt': 8}|
|formal100|3.38|3.594|0/8|{'tilt': 8}|
|formal125|2.21|2.218|0/8|{'tilt': 8}|
|formal150|2.10|2.104|0/8|{'tilt': 8}|
|formal175|1.80|1.800|0/8|{'tilt': 8}|
|formal200|2.02|2.029|0/8|{'tilt': 8}|
|formal225|1.79|1.799|0/8|{'tilt': 8}|
|formal250|1.53|1.530|0/8|{'tilt': 8}|
|formal275|1.36|1.363|0/8|{'tilt': 8}|
|formal300|1.58|1.588|0/8|{'tilt': 8}|

本次12个formal评估全部0/8、complete hold windows0；保持高度/速度指标缺测保持null，不能以失败前短窗代替10秒。诊断排序source与各checkpoint按完整通过/完整窗、最短再平均首episode存活时间，仅在全失败情况下选生存最长，不等于正式accepted。best诊断候选update100：/home/kellen/wheel_leg_native_train/runs/2026_10_13-17_09__motion_frame25_asymmetric_ppo_closurefix_from_bc/formal/model_update_100.pt，SHA1b5ece600b1ab5345c9a36bd2d6ee9a979d19dd1bed2013e0316ac97c76c1bcb。最短3.38/平均3.594秒，来源2.08秒，u300平均1.588秒；不是稳定提升，不采用latest或声称有闭环站稳能力。

结论：现接口下PPO真实更新，出现过短期行为改善，但仍倾角失败且后期退化。Critic特权未足以解决闭环稳定性。下一最小工作优先用update100与BC来源在同条件有限PPO0录制最早偏离与确定性动作，对照Actor输出反馈、轮力矩/限位、value/advantage及状态覆盖；不继续原样无限加更新，也不直接认定25D不够。非零运动NOT_RUN，原31D Recovery与150D教师能力不迁移给25D学生。本次没有启动新PPO0；如果需要独立新模型复测，应新spec/ledger并明确预算。

机器结果isolated/motion_frame25_ppo_review_20261013/result.json包含全部逐环境结果与输入SHA。工具命令见TOOL_INDEX。
