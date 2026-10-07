# motion_recipe formal 复盘

本报告只读分析既有运行，无新增物理采样或 PPO。

证据目录：`runs/motion_recipe_20261004_formal_20261004/formal_run/`，使用该目录 source_snapshot、terminal_report.json、metrics.jsonl、evaluation_50/100_*.json 和 retention_confirmations.jsonl。准备 spec/账本：`configs/experiments/motion_recipe_20261004_formal/`。

## 结论

不是摔倒或旋转导致的假速度提升。两次检查所有命令均8/8完成，无runtime fault，双轮接触100%，yaw均值绝对值小于.01rad/s，闭链最大误差约2.2–2.8e-5m。策略逐渐形成向后漂移，并破坏正向响应。零命令gate失败是实际速度与位置退化，不能用“允许加减速倾斜”解释。

确定性评估，每项为8个env平均；速度/误差单位m/s：

|目标|50 vx|50 MAE|100 vx|100 MAE|
|---|---:|---:|---:|---:|
|0|-.02968|.02968|-.08294|.08294|
|+.1|-.02032|.12032|-.12448|.22448|
|-.1|-.03868|.06132|-.04157|.05843|
|+.2|-.01104|.21104|-.16682|.36682|
|-.2|-.04694|.15306|-.00059|.19941|

50和100正向方向比例均0；负向比例均1。但100的-.2实际仅-.00059m/s，说明当前方向率采用符号判据，可把几乎静止记为方向正确，不能单独作为能力证据。所有运动gate均0/8，仅-.1略有改善，整体未改善。

零命令50/100均0/8：全部env失败项是net_drift_m、max_excursion_m、mean_abs_vx_error_mps。漂移分别.278/.780m；阈值漂移/位移.20m、速度误差.02m/s。峰值tilt平均.0097/.0222rad，未因姿态gate失败。没有证据支持upright导致失败是唯一根因，也不应放宽gate掩盖漂移。

## Reward与优化证据

训练随机rollout窗口1–10与91–100，weighted mean（乘dt前）分别：upright1.99894→1.99929；height1.99547→1.99515；linear tracking3.06440→2.46834；yaw tracking3.94691→3.95908；contact恒.5；effort惩罚-.00357→-.00343；action_delta惩罚-.00521→-.00469。linear项下降约19.5%，姿态/接触收益近乎不变。正向跟踪恶化确实被其它高且稳定的项在总reward中部分掩盖，但这些均值不能证明哪个reward造成梯度退化。

姿态项已接近饱和；没有证据支持“upright太强”这一单一解释。需要看已保存真实更新数据的逐命令优势及梯度归因，而非继续增大奖励。PPO并不对物理reward公式直接反传。

保存了前3个完整transition/update诊断（ppo_transition_update_1/2/3.pt与ppo_diagnostics.jsonl）；50/100没有同样完整更新数据。没有本轮新发现的GAE或surrogate数学错误。动作、力矩只能按已有证据报告：eval任意通道饱和50为0、100约.001；训练约.3量级。未保存完整逐电机时间序列，逐通道饱和持续时长UNKNOWN，不能断言轮电机饱和或提高限矩。

## 发现的执行/可追溯性问题

1. 来源运动CLI使用stages[0]创建环境，且未向evaluate_actor传入evaluation.command_mode；实际采用ramp，而formal明确传入fixed。来源评估还是10秒，formal非零评估9秒、统计窗口2–6秒。此前宣称“同协议来源基线完成”不成立。现有来源运动MAE不能与formal直接比较，保留缺口，不新采集。
2. 新账本从短验证账本复制；清空历史条目的脚本因裸python不存在未执行，后来未发现。这导致新账本包含旧source/smoke历史，formal前置检查借用了旧完成记录。保留账本事实，不清零旧数据或改写成独立新历史。formal条目本身结算100次、1538.02秒有效。
3. 没有实际后台monitor进程，本轮trainer直接启动并自行停止/保存/结算。此前说“现有monitor负责”不准确。未发生通知唤醒实现；未来提交需要真实monitor和总预算监督。
4. terminal的best_standing_candidate指向50但accepted=false；它只是排序最优的失败候选，不能称已验收站立模型。best_motion_candidate为null。

这些问题影响来源对照、前置与报告可靠性；没有证据证明它们导致训练策略反向。formal自身fixed评估、零命令retention在50/100如期执行。

## 结算与模型

STOPPED_BOUNDED，stop_kind=retention，100次、819200样本、1538.023秒；两次完整零命令失败后停止。150/200未到达。没有运行故障。来源SHA fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1；asset SHA 6bf6ce7f64f8d46cdc759bdf48dba0def85f6e9e6915acca27c543dbcf031a27。

最新100 SHA 370bdb2d472e8c48635298c152c20acd22a28026768baf82b331ac2df6aaeeb1；50 SHA af990e413b636b218b4fe35eae2a8a0b32c2c985975b0707dc8d9cbda6b3e4a8。formal无accepted运动或站立候选。来源站立与smoke3仍保留；不从100续训。

## 下一项建议（未授权，不执行）

先修复并CPU验证评估CLI协议、全新账本前置引用及真实后台监督；保持历史产物只读。这些属于证据链修复，不调reward。

优化实验只建议一个变量：保持来源actor/critic、奖励/采样/PPO/物理不变，仅对照Adam一阶矩保留与清零，保留二阶矩及step计数；先用已有冻结rollout做CPU离线重放，比较标准surrogate、逐命令logprob和零命令动作偏移。此处只是候选假设，需先对照之前motion_momentum实验原报告，若同变量已充分覆盖则不重复。不得同时warmup critic或改advantage normalization。

物理实验前仍需补齐真正fixed、同seed/时长/窗口的来源对照；另行授权。当前不建议扩大训练预算，原因是正向和站立随更新显著退化，没有双向学习改善证据。
