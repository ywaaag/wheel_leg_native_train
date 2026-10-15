# Motion31质量v3终态复盘与水平保持v4提交准备

## 结论

父链完成smoke5＋formal1900，共1905次新增在线更新；formal124,518,400条样本，smoke327,680条，总124,846,080。此前历史50次独立列账，原授权累计1955/2000。链33144.32秒约9.21小时。未获得旧协议连续两次完整矩阵accepted；不是runtime故障。

中途100–300的反向/弱响应没有代表最终结果。约700次开始所有非零方向正确，1400与1600全部32个非零环境同时满足tracking、direction、gain、持续比例；1500等波动，不能拼不同checkpoint通过点。按事先冻结排序，选update1600，SHA `83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`。

来源完整路径：`/home/kellen/wheel_leg_native_train/runs/2026_10_14-21_23__motion31_posture_quality512_v3/formal/model_update_1600.pt`。这是下一轮学习来源，不冒称原协议完整认证。

## update1600逐命令摘要

以下速度、pitch、轮心差来自保持段；高度、腿长差、接触、饱和来自全episode，窗口不混用。原始逐环境证据见selection.json内evaluations路径及父formal/evaluation_75..79.json。

|命令|保持vx|MAE|方向|pitch rad|轮心差mm|高度m|腿长差mm|旧gate通过|失败原因|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
|+0|0.0403|0.0403|—|0.03177|5.345|0.34279|0.038|8/8|无|
|+0.5|0.4934|0.0066|1.000|0.02918|5.667|0.34321|0.037|8/8|无|
|-0.5|-0.4011|0.0989|1.000|0.03353|5.656|0.34251|0.040|8/8|无|
|+1|0.9949|0.0142|1.000|0.02658|4.513|0.34375|0.054|8/8|无|
|-1|-0.8404|0.1596|1.000|0.03221|7.686|0.34257|0.064|7/8|{'roll_source_guard': 1}|

全部命令全episode双轮接触约99.967%，饱和0；全窗口几何比早期显著改善。−1有1个环境roll_source_guard失败（来源接近零，零相对容差），旧39/40不能改成40/40。单seed评估不等于多训练seed能力。

## 新实验冻结差异

1. 只训练0/±0.5/±1，512env固定配额不变；准备0.5＋加速1＋保持28.5秒，取消训练回零/停车，保留独立zero；normal timeout bootstrap不变。
2. 新reward `student_motion31_hold_level_reward_v4`：upright2→4、pitch/roll tail各−0.5→−1；核宽、其他奖励、质量终止、PPO/物理/动作全部不变。
3. Actor/Critic/Adam/std/RNG及cohort混合状态从1600完整恢复；+0.5与+1已学mix=.75，负向mix=0，不能重置宽窄状态。reward变化后Critic保留权重/Adam，仅smoke4与formal5次显式Critic适应，均占预算。smoke模型不作为formal来源，formal仍重新加载1600。
4. 评估仍原缓变完整窗口与原物理/姿态guard；新评分身份 `motion31_hold_level_assessment_v3` 只将停车gate移为诊断，不把旧失败改写为通过。
5. 同时改时相与姿态权重，不能因果归因为单因素。

## 检查与交付

CPU PORTABLE（最终见artifacts portable_tests.txt）、绑定CPU初始化/定向测试（cpu_authorized_result.json）；零写plan及提交READY（submission_plan_corrected.json）。whole_chain_storage.json给出1,913,729,536 bytes含peak/reserve，低于2GiB。新额度2000总online=5smoke+1995formal，18h；不自动重试/升速/第三链。
新增版本实现、恢复验证、零exit处理、quality runtime权重传入、schema/health/storage/评估接线与CPU测试；旧v3默认未改。没有复制源码/测试树、没有覆盖历史run/spec/账本/评估或提交Git。
下一优先检查：双向gain/最差MAE与旧能力保留、pitch/roll、高度/几何，按真实同协议checkpoint评估，不凭reward上升。真实历史PPO capture仍缺，未声称已证明优化因果方向。

## 状态

新spec：`configs/experiments/2026_10_15-06_41__motion31_hold_level512_v4/spec.json`。已public supervisor detached提交，worker325129、attempt9c724b38f6bc4e8081883d9b4e8a3532，GPU0共享→CUDA0。一次30秒握手submitted/submission_verified=true、SOURCE_EVAL，formal_first_update_verified=false、started=false：这是已提交来源评估，不冒称formal已经更新。新run为 `runs/2026_10_15-06_41__motion31_hold_level512_v4`。

最终CPU：PORTABLE452通过、8跳过、4弃用警告；绑定CPU62通过，完整Critic/Adam恢复和LR3e-5核验，offline optimizer0。额外PROJECT_DATA旧学生健康fixture失败（已缺旧checkpoint的actor_input_shape）；未伪修旧证据，该历史fixture不作为新实验通过依据。当前真实来源的完整提交健康检查READY。首次将此PROJECT_DATA测试传给PORTABLE验证器被正确拒绝，随后仅用显式PORTABLE重新验证通过。

健康检查另修显式successor对已训练Motion来源的识别：从SHA绑定父spec引用教师manifest谱系，不再要求它仍是最初迁移初始化，也未绕过完整来源/结构/SHA核验。完整修改清单见 `artifacts/2026_10_15-06_40__motion31_terminal_successor/change_manifest.json`。

TensorBoard `http://127.0.0.1:6006/` 一次HTTP200，新分组 `2026_10_15-06_41__motion31_hold_level512_v4` 已注册、smoke/formal既有只读metrics bridge导入真实指标。终态通知冻结当前owner，不新增训练watcher、不守候训练，不自动重试/第三链。历史终态和账本保持原样，未提交Git。
