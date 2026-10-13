# Recovery P1来源评估完成、smoke保护器接线失败复盘

事件53acf4f6cdbc0c19ec7fd48c已核对report SHA并通过既有CLI确认reviewed。
run：2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50，终态FAILED。
[输入SHA、分组数据及原始证据重放](../isolated/recovery_min_height_p1_guard_review_20261007/review.json)。

## 阶段与消耗

source_eval COMPLETED，attempt c3ebcd81b42a4d2f9cbee562a9791eee，134.5718秒；完整原始DrawBack与R0评估已持久化。
前次RiseHold inference reset故障本次未复现，两个family初始化均8/8有效，runtime_fault=0。
smoke FAILED，attempt 05b2aa0a267e424a9e7b74532fff31dd，worker墙钟0.2345秒，在manifest阶段、AppLauncher前失败。
smoke/formal均0更新/0PPO样本，整链159.7012秒。最佳角色是原来源S50，没有训练产生的新候选，没有accepted模型。
两次链累计墙钟232.9681秒；来源阶段累计204.8366秒；PPO仍0更新，不能把剩余额度当自动重试授权。

## 工程故障

我新增的ProgressGuard在smoke初始化读取baseline_registry[-1]['result']。
候选登记按设计删去control_diagnostics_100hz等大数组，原始evaluation_source.json则完整保留。
保护器是完整控制轨迹消费者，因此报“Declared wheel oscillation control trace missing”。
这是生产者/消费者的数据范围接线错误，非轮振荡已经出现，非来源行为失败阻止训练，非GPU或物理故障。
原始来源控制轨迹每env1128–1129行，R0为1063–1065行；不会通过给缺字段补零绕过检查。

## 来源的实际能力

| family | 初始化/入口 | 10秒观察 | 完整接受 | 主要实测失败 |
| --- | --- | --- | --- | --- |
| DrawBack | 8/8有效、8/8入口；0.88–0.89秒 | 各env均1000保持样本 | 0/8 | 前缀8.37–8.54秒后高度/接触/倾角失守 |
| R0 | 8/8有效、8/8入口；0.63–0.65秒 | 各env均1000保持样本 | 0/8 | 接触99.7–99.9%，不满足连续100%；前缀0.23–0.27秒 |

DrawBack保持窗最小高度约0.239m；R0约0.418m，R0 mean abs pitch约0.0904rad、roll约0.0182rad、采样饱和0。
R0的短前缀由首次短暂失触打断，不等于0.25秒后倒地；不得改成“不会平衡”。
原报告另列continuous：当前评分器对正常完整task_failure终止仍附加通用终止拒绝。实际post_rise_observed_s=10且窗口COMPLETE。
完整物理观察与证书失败需要分开；本次不回填原评分，也不放宽连续接触或其他验收。两组都有独立真实失败项。
本次是冻结S50的PPO0复核，不是新的学习收益；R0从历史证据不足转为本次有完整测量、尚未通过。

## 最小接线修复及CPU验证

新增CLI边界loader recovery_progress_baseline.load，从source phase原始evaluation_source.json读取数据。
它校验source角色、固定评估文件、checkpoint SHA，以及manifest的spec/source/asset身份和raw的spec/checkpoint身份。
train只把原始证据传给ProgressGuard，记录证据路径/SHA；候选摘要保持紧凑，纯域保护器不读文件。

CPU重放本次原始source成功：8个入口，固定“入口后1–2秒”窗口轮振荡指标均False；只代表声明指标/窗口，不保证全时段无振荡。
新回归覆盖真实持久化摘要→原始证据→保护器、身份冲突拒绝、原始轨迹缺失仍拒绝。全量515 passed，21.17秒；git diff --check通过。
修改：src/native_stand/command_v6/train.py；新增tools/recovery_progress_baseline.py、tests/test_recovery_progress_baseline.py及本文。
更新README、STATUS、ARCHITECTURE与重试说明的终态记录；保留其他worker dirty changes。
旧源码快照、评估、模型、账本不改；review标记是既有事件确认接口。

没有重新启动仿真/PPO、提交、轮询或发送通知；本通知不授权自动续训。
最小修复尚无新的真实smoke验证。下一运行需明确新授权、独立路径/账本与修复版冻结CPU/plan；保留S50与最终P1任务目标。
