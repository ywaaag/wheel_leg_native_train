# B25 DrawBack小扰动冻结验证

用户明确批准原DrawBack/R0及6个±.01rad闭链合法候选的PPO0验证；共8项×8env，首入口后完整10秒、观察上限23秒，单evaluate attempt≤1200秒含清理，PPO/optimizer更新0。
新config/run根2026_10_8-13_15__recovery_b25_drawback_small_ppo0，独立账本；来源B25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。
当前session核对并写authorization_receipt；GPU0共享、逻辑CUDA0，不停止其他任务。通过唯一supervisor evaluation-only提交，前台等待自有有限evaluation monitor退出，不循环读取训练日志。

授权后共享CPU543 passed，最终冻结专项9 passed；物理/模型/pose库SHA核验，旧证据只读。
姿态变更仅主动关节±.01rad、闭链求解对应被动关节、根高度由该资产最低理想collider确定；旧DrawBack/R0完整保留。
初始化readback、闭链与真实接触决定新初态是否可用；offline_valid不替代runtime_valid或policy_certificate。
本次不训练、更改奖励/std/控制、不放宽gate，不自动启用Swing。

## 通向Swing的离线准备

[几何路径](../isolated/recovery_drawback_to_historical_swing_geometry_20261008/review.json)从实际DrawBack朝历史R1（此前GUI描述Swing）做主动joint构型插值，逐点闭链求解、限位与理想支撑检查。
目标尚未经过本轮用户重新确认，不把历史family R1等同于新课程Level1。
各点closure/limits通过，支撑高度非单调：alpha .02/.05/.1约.175/.185/.203m，.6约.312m，再下降到目标约.169m。
因此不能用root高度线性课程；近端.02/.05只作下一桥接候选，不是完整动态路径或控制示教。
没有改当前八项请求，没有运行额外几何候选模拟，runtime/policy仍UNKNOWN。

后续训练初始化注意：B25 checkpoint已经带有P2学习后的轮std；新的局部课程若从B25继续，应保留checkpoint实际std，不重复执行父B配方的0.5初始化倍率。
本次evaluation_only不调用exploration.initialize，因此没有再次减半。未来训练声明必须移除或显式改为identity初始化，并记录requested/effective，不借继承字段暗中添加第二次std干预。

## 本次实际结果与下一次准备

八项COMPLETED且各8/8 accepted：原DrawBack/R0＋6个小扰动，共64条完整10秒first-episode证书；所有初始化有效、failed_checks空、prefix10秒。
[逐环境证据审查](../isolated/recovery_b25_small_review_20261008/review.json)。terminal539.7616秒，清理后账本结算540.1750秒；attempt ea1fd6144b8e4cddb1c0e3a5b7052a0d，evaluate used1，PPO/optimizer更新0。
这是seed104、新声明小扰动范围的确定性能力，未声称任意倒地/100秒耐久/随机训练episode全成功。
审查工具single-seed初始化hash的“相同”只表示每个组本次有一个seed，不能作为额外三seed证明。

因此本轮无需再训±.01rad姿态。已准备下一组B25冻结验证：原DrawBack/R0＋朝历史Swing的alpha .05/.10桥接＋alpha1历史R1描述构型候选，共5项，建议1200秒、PPO0。
新根：[2026_10_8-13_28__recovery_b25_swing_bridge_ppo0](../configs/experiments/2026_10_8-13_28__recovery_b25_swing_bridge_ppo0/spec.json)，UNAUTHORIZED、used0/attempts空，未模拟/提交；[零写plan](../isolated/recovery_b25_swing_bridge_plan_20261008/plan.json)为READY_NEEDS_AUTH/cpu_valid=true、5requests、预算不变/run不存在。
这些是闭链求解后的静态构型，非动态PhysX状态恢复，也非policy motion prior；历史R1 target仍需本轮GUI或readback确认语义，不能仅按family名字认定Swing已经掌握。
若物理初始化合法而Swing候选策略失败，可据此准备局部逆向课程学习；若已有能力通过则直接扩大范围，不盲目追加PPO。

本轮源码只调整scripts/review_recovery_revalidation.py支持请求项数；新增本报告与独立授权/声明、PPO0结果、离线Swing几何及未授权下一spec；更新STATUS/RECOVERY_STANDING_PLAN执行进展。
旧模型、原始评估与账本使用只读审查，除既有owner按本次exact attempt正常结算外无覆盖。未停止进程、未发送通知、未提交Git。
