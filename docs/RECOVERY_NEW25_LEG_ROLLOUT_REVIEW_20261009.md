# 最新有界轮均值new25：随机腿探索诊断

2026-10-09用户同意执行。独立run `runs/2026_10_9-14_00__recovery_new25_leg_rollout_probe`，attempt ab62b0ca773f465a90deb499f8c348d3 COMPLETED、evaluate1结算；terminal28.186811秒，monitor账本另含退出清理（见monitor_exit）。采集2×128×64=16384transition、PPO/optimizer更新0，actor/critic/Adam逐项未变，无新checkpoint。GPU0共享、墙钟上限600秒，未停止其他任务。

## 模型身份与实际字段

来源是10_58 formal/model_update_25.pt，SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c，严格匹配它的formal/source_snapshot/spec.json及资产。不是早期认证B25；声明将候选作为独立诊断source，明确action_distribution bounded wheel mean，β.3/std/控制/150D/fixed26/25/13不改。

新增fullpre/post全关节pos/vel、joint_names、activeindices；postjoint直接engine数据的done transition可能已reset，必须排除。state/control/geometry保持pre-resetsnapshot。preframe推算target−preq与fullprejoint独立复算误差0，防止拿postq或错误全joint顺序推符号。

NPZ16.62MiB，小于64MiB上限，metadata记录具名轴/字段/SHA；CPU专项及冻结10passed，schema/plan/sourceactorcriticAdam严格继承通过，supervisor READY后一次有界前台诊断运行。没有额外actorforward/采样/优化器调用来改原随机序列。

## 最新策略真实探索

受控Swing2504样本。0.01–0.04秒332样本中，目标相对preq朝局部收短方向[+,+,−,+]的四通道比例[0%,83.43%,0%,1.20%]，平均delta[−1.2366,+.5543,+1.5278,−.2052]rad；两hip仍全部反向。0.05–.10秒468sample两hip方向也均0%。三段共2504sample均没有四通道同时命中已找到局部缩腿组合；对应advantage缺样本为null，不能称差/好。

该组合只是CPU找到的一条充分局部路径，不是所有收腿方案的必要条件；大目标变化也不在小幅linear范围，不能将这个零覆盖直接称完整起身概率0。然而真实轮心长度独立证实没有明显双侧收短：左最小.358485米、右.375417米，没有双侧都<.30米样本。

轮真实sampleclip15.65%/8.51%，相比旧Gaussian100%/98%改善。物理轮目标跨状态std约4.483/5.753rad/s，包含状态/episode变化，不等同固定状态探索std。轮分布改进已经生效，但没有转化为腿有效构型覆盖。此诊断每env仅2.56秒含初始化，非完整旧组保持认证、非学习收敛实验。

## 下一分支

当前证据更支持检查腿探索中心/迁移，而不是翻转实体关节符号或继续优化轮clip。下一纯CPU审核腿分布与目标表达的候选：是否能够增加当前合法Swing区域收短方向覆盖、对DrawBack/R0旧动作的偏移有多大、log_prob/Adam坐标如何声明。先比较不改变输入/控制的显式策略参数化或经证据核验的课程覆盖，不直接加固定腿偏置、mirror硬约束、隐藏控制、限矩。

若候选需要改实体目标参考或引入学习先验，必须显式说明这是超出当前单变量动作分布的接口/行为变化，先审查再授权；不能偷偷将CPU几何方向写入runtime控制。局部支撑反力/反弹＋收腿动力学还缺5ms子步和相关碰撞体接触力，不因本次探索缺口直接断言动力学一定可恢复。

原认证B25继续保留；new25绑定其分布身份留作实验候选，仍Swing未通过，不自动续训。

## 改动与证据

修改`scripts/prepare_recovery_rollout_probe.py`允许显式匹配parent候选checkpoint、source身份重绑定；修改`src/native_stand/command_v6/tools/frozen_rollout_probe.py`增加可选全关节读回及validity，`domain/rollout_probe.py`严格选项；新增`scripts/review_recovery_leg_rollout.py`。独立声明/授权登记仅写新14_00目录。CPUreview `isolated/recovery_new25_leg_rollout_review_20261009/review.json`保存输入SHA和阶段覆盖，没有复制大数组。更新STATUS、任务计划、TOOL_INDEX与本报告。旧checkpoint/spec/raw/ledger、资产和其他dirtychanges保留，无commit/push或清理。
