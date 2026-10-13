# Level3 Swing 首块学习：准备与提交

用户确认Swing候选姿态符合预期、DrawBack起身可以，并明确批准本块运行。

## 冻结声明

- 实验：`2026_10_8-14_51__recovery_level3_swing_from_b25`。
- spec：`configs/experiments/2026_10_8-14_51__recovery_level3_swing_from_b25/spec.json`；新独立budget/授权receipt；历史账本不改。
- 来源：P2 B/formal/model_update_25.pt，SHA `8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44`。
- 新库保留实际旧DrawBack/R0初态；Swing family=`swing_candidate_from_historical_r1`，GUI语义确认、此前PPO0初始化8/8有效、起身0/8。
- reset抽样质量：Swing40%、DrawBack40%、R0 20%；不是transition占比保证，原有family×phase诊断记录真实覆盖。
- 移除父B的轮std乘0.5初始化，严格继承B25全actor/critic/Adam/std；两轮物理std4.88557/3.88416rad/s。
- reward/协议/USD/控制/150D输入/动作尺度保持；不加对称、制动、teacher控制、随机倒地。
- source≤900s/PPO0；smoke10≤900s；formal≤100≤7200s，25/50/100完整三组评估；chain≤9060s含60s清理，最多110更新、901120样本。
- smoke要求三组真实有效初始化的completed episode事件；新Swing尚不会起身不作为行为前置拒绝。
- 已有StandingRegression检查所有retained组：来源旧组通过后，连续两次完整旧组失败停止；现有entry/振荡保护保留。
- 同模型全部三组完整通过才accepted；保留B25和早期checkpoint，不拼接、不续latest、不自动扩额。

## 最小接线扩展

`recovery.rising.validate_rise`保留旧严格配方分支；新增显式sampling_version允许多retained family与≥40%保留质量，不改变minimum-height协议。
pose_sampling现有sample_weight用于在retained60%内分配DrawBack40%/R0 20%；两个split独立核算。
train的StandingRegression日志scope改为retained_families，列出真实family。
新spec显式notifications.enabled=false，completion按冻结声明禁止外部投递；报告仍由后台写出。

## 验证与提交

- 全CPU556 passed；随后新增禁通知边界测试，相关15 passed；授权冻结schema/plan/严格checkpoint初始化和34项CPU测试通过。
- 初始化所有参数差异0、Adam不变，未执行CPU optimizer.step。
- 公开supervisor零写plan、check-submission READY，shared物理GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`，映射cuda:0；未停止其他进程。
- 一次detached提交成功，worker身份核验；握手SOURCE_EVAL，formal首更新未验证。
- run：`runs/2026_10_8-14_51__recovery_level3_swing_from_b25`；启动回执：`configs/experiments/2026_10_8-14_51__recovery_level3_swing_from_b25/submission_review.json`。
- 后台所有终态/评估/实际预算以run原始证据为准；不轮询、不另建watcher。终态不会自动向外投递，新续训另需授权。
