# Motion站立与支撑对齐：停止旧配方及下一实验设计

## 已停止与保留来源

用户明确“停止训练，并且设计新的训练”。停止对象仅Motion standing034_symmetry_adamfix_20261013；原owner已在更新边界保存并结算，task STOPPED、active_spec=null。累计522在线PPO（formal472、smoke50）、4276224samples、6801.6507535秒、64评分episode。原run/spec/checkpoint/rawevaluation/ledger只读，Recovery未停止或修改。

来源恢复为此前零速站立最佳：runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt，SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb。source实际zero8/8，vxMAE.00124m/s、meanheight.35225m、mirror.310/.313rad、轮前后错位.09185m。不是镜像或部署accepted。不得继承退化latest，只因它更新更多。

## 为什么停止

旧源→新block0/200→block0/300→block1/100：

|候选|hip/active镜像MAE rad|轮前后MAE m|零速vxMAE m/s|
|---|---|---|---|
|原站立来源|.310/.313|.0919|.00124|
|新block0/200|.421/.471|.1300|.0833|
|新block0/300|.297/.581|.1341|.4400|
|新block1/100|.221/.567|.1248|.5855|

hip改善不等于整个腿姿改善。原两镜像通道平均成本允许一项改善抵消另一项变差；这是优化目标风险，不是唯一动力学根因证明。旧owner按最差mirror排序仍不能替代新的实际wheel位置约束。原相同评估仍均0/8联合通过。

## 冻结的新设计

同一legacy150D MotionActor、原网络/动作/PD/限矩/USD/std配置，64zero、heightcommand.34，不同时推进±2，不硬投影、不低通。

保留原effective Motion站立reward及原mirror密度，只拆开日志：

```
eHip = leftHip+rightHip
eActive = leftActive-rightActive
Jhip = Huber(eHip/.20)
Jactive = Huber(eActive/.20)
Huber(x) = .5*x² (|x|≤1)，否则|x|−.5
原成本 = −.5*Jhip −.5*Jactive
新增最差关节成本 = −.5*max(Jhip,Jactive)
新增轮位成本 = −.5*Huber(relu(|dWheelForward|−.01)/.10)
```

dWheelForward为leftWheelCenter−rightWheelCenter在机体前向水平投影上的分量，m。用实际postphysics/prereset状态，不用target、世界固定轴或速度代替位置；heading无效不能伪造0。正常站立学生实际控制期间生效，每项密度乘dt=.01一次，事件与原reward保持。

这个系数是首轮待验证设计。PPO由实际采样回报学习，CPU cost梯度不是物理因果证明。最差项增加关注另一关节，轮位项明确惩罚剪刀腿，不要求固定腿角或固定动作表。

新recipe首次Actor/std从来源加载、Critic/Adam/RNG独立、前5更新Critic-only；同配方后续恢复完整状态。旧Adam空state转换修复必须保留。

## 联合验收与选模

原30秒流程/固定10–20秒完整保持窗、每条件8评分环境，缺字段/短窗口失败。

- hip MAE≤.05rad，P95≤.10rad。
- active MAE≤.05rad，P95≤.10rad。
- 两轮前后差MAE≤.02m，P95≤.03m。
- 零速mean(abs(vx))≤.05m/s，vy≤.02m/s、yaw≤.03rad/s。
- 保持平均高度.32–.36m，保持每样本≤.36m；保留原低高度、接触、倾角、闭链与限矩检查，不放宽物理gate。

上述是新协议，不回填旧结果。zero严格门槛用于本站立专项，不声称所有实机应用必须精确定点。

排序先联合通过数；未通过时先保证实际站稳与零速、再比较hip/active/wheel三项最差归一化偏差，不用平均mirror、reward或latest选模。连续两次完整8/8且中间至少一次PPO，再独立小yaw复核；只认证零速站立对齐，不代表±2或yaw驾驶。

0.36m完整部署限高仍需核验合法低高度启动。原合法初态和整个启动峰高未完成该认证；不能把固定保持窗≤.36说成完整部署通过。此次设计不硬改初态姿态造成穿透，后续独立处理启动。

## 实际完成与执行边界

CPU奖励原型、5回归测试通过；已有4份完整8000sample窗口分别重放，1份不完整窗口拒绝重放。来源新成本约−1.759/秒，新block1/100约−2.959/秒，其中worstJoint约−1.167/秒、wheel约−.324/秒；没有为使结论好看删除普通行为失败。schema/SHA和单位记录机器结果。

文件：manual_train/motion/alignment_design_20261013/{reward_design.py,test_reward_design.py,replay.py,reward_replay.json,experiment_design.json,stop_readback.json}。

**新方案未启动**：设计声明runnable=false，未注册runtime版本、未创建新训练attempt或授权账本，未声称公共plan通过。公共接线/冻结PORTABLE/planner/optimizer链回归需在提交前完成，不能只把设计字段塞入spec。

建议首块：source8episode，smoke25＋formal300，325更新/2662400samples/4小时/2GiB，GPU0共享；100/200/300联合评估。首块后先按三项与站立趋势决策，不继续盲目自动5000更新。资源/身份/存储在公共reserve前核验。当前用户指令是停止并设计，未为这份新设计启动物理执行；等待用户确认新方案后再接通并提交。
