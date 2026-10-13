# B250姿态短链失败复盘

事件a800778e8d785c11dbc4dd24，只读复盘，不重试或续训。
run：runs/2026_10_8-18_03__motion_b250_posture_balance_v2。
chain FAILED，source_eval COMPLETED，smoke FAILED，formal NOT_RUN。
smoke/formal实际PPO更新0、samples0，无新checkpoint/accepted候选。
整链1927.081s，source主体1916.134s，smoke主体4.695s；ledger分别结算COMPLETED/FAILED，
source_eval used1、smoke/formal used0，无RUNNING attempt；失败初始化墙钟仍已实际消耗。
剩余50额度不是自动重试授权，旧spec/ledger/快照不修改。

## 已确认实现错误

smoke traceback：train.py第551行metric.add → domain/metrics.py第27行：
ValueError('rollout metric fields changed')。
reward.compute新增posture_balance raw/weighted字段，但trainer第466–487行仍用
旧Motion七项字段创建RolloutMetrics，没有追加该项。严格集合检查拒绝是预期行为。
这是本worker新增奖励时漏接统计契约的错误，不是策略能力失败、几何测量失败或PPO数值失败。
CPU覆盖了reward、geometry、selector，却未覆盖真实trainer字段声明与reward输出一致，
因此630项通过不能证明训练入口全部接通。需要补此集成CPU回归，而不是删掉metrics检查。

## 来源真实Isaac几何

source_eval完整9命令，每项8env、30秒、运动gate各8/8；posture窗口每env801样本有效。
下表为8env保持窗口的绝对值均值，不是峰值或新模型收益。

|命令|轮心前后错位cm|左右腿长差cm|roll rad|有界姿态成本|
|---|---:|---:|---:|---:|
|0|4.950|.0105|.000003|.02778|
|+.5|4.671|.0141|.000016|.02295|
|-.5|5.798|.0118|.000008|.04479|
|+1|5.441|7.745|.17230|.32160|
|-1|7.264|.0247|.000013|.08069|
|+1.5|6.311|11.793|.25842|.54335|
|-1.5|10.237|5.972|.12931|.34015|
|+2|7.411|14.200|.30713|.65509|
|-2|13.903|8.116|.16794|.53930|

原始posture_diagnostics/per_env/trace位于source_eval/evaluation_source*.json。
native实测支持剪刀腿及中高速长短腿/roll，不能再仅称MuJoCo现象。
zero腿长几乎相同但前后错位约5cm，说明两种几何畸形不能互相替代。
+2与-2不对称；未证明腿长差到roll的唯一因果，不新增物理补偿。
来源B250 checkpoint SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。

## 下一步

唯一优先项：为显式posture_balance任务把该字段接入trainer RolloutMetrics清单，
默认旧任务保持七项；新增“真实trainer声明→reward输出→metric.add→summary”的CPU测试。
保持新奖励和冻结目标不调参，不降低strict字段检查，不改物理/PPO。
修复后若用户明确授权工程重试，再建立新输出/独立预算与身份，更正引用已完成来源几何；
不重复覆盖source评估、不凭旧余额自动formal-only。
本通知仅授权复盘，本次不修改训练代码、不启动仿真/PPO、不发送通知、不提交Git。
本轮只新增本文并更新STATUS；失败run/报告/ledger/源码快照保持只读。
