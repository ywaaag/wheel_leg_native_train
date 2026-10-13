# Swing静态中间支撑：动作范围与PPO0复盘

## 授权与执行

用户批准离线动作/路径检查及少量合法中间支撑PPO0；未授权新PPO。新实验2026_10_8-16_53__recovery_b25_swing_support_probe_ppo0，六请求各8scored env、23sminimum-height协议，总墙钟上限1800秒；物理GPU0共享，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda:0。不停止其他任务、不自动重试/延长或通知。

来源认证B25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44，新USD/reward/控制/终止/std/验收均不改。公开supervisor --evaluation-only有界前台等待自身退出；终态COMPLETED，evaluate使用1次，实际结算171.884秒，PPO/optimizer0。terminal记录171.511秒，差额为退出/清理结算；不混用。

## 离线发现

150D原接口、零reference、腿目标±1.6rad：原Swing实际主动关节约±1.14/-1.41rad都在目标范围，没有发现目标位置无法表达的硬限制；这不证明完整起身动作序列力学可行。
B25接管Swing首步目标与初态差较大，三腿请求约67–100Nm、双轮约−97/−99Nm被裁至原40/5.5Nm。成功DrawBack在.15秒越过约.32米、.30秒峰约.444米；Swing.30秒仍约.23米并tilt终止。这是适用状态/动作线索，不认定唯一根因，不改限矩或引入控制器。
证据：isolated/recovery_swing_support_action_audit_20261008/review.json。

## 合法几何不等于可用reset

在原Swing闭链分支调整hip/active-link（对侧hip镜像），四候选q为[1.1,-1.3,-1.1,-1.3]、[1,-1.2,-1,-1.2]、[.9,-1.1,-.9,-1.1]、[.8,-1,-.8,-1]rad。被动闭链求解残差约5.12e-9米、关节无越限；理想支撑root约.194/.228/.259/.289米。全速度清零，非原PhysX动态恢复。

| 请求 | 初始化有效 | 完整通过 | 实际构型解释 |
|---|---:|---:|---|
| 原DrawBack |8/8|8/8|旧能力保留 |
| R0 |8/8|8/8|旧能力保留，direct reset无沉降末帧 |
| .194米支撑 |8/8|0/8|接受前沉降至.16847米，主动q回原Swing约[1.14264,-1.40932,-1.14261,-1.40932]，与请求差最大.1093rad；不能认证独立桥接状态 |
| .228米支撑 |0/8|0/8|1秒沉降预算结束，初态拒绝；末高.16885米，已趋Swing |
| .259米支撑 |0/8|0/8|初态拒绝；末高.16908米，已趋Swing |
| .289米支撑 |0/8|0/8|初态拒绝；末高.16879米，已趋Swing |

后3项未交策略控制，恢复时钟为0，不能当policy学不会。现有trace缺全被动关节速度及全部逐时刻沉降predicate，不能认定唯一拒绝项。不得延长沉降、改root bounds或加PD保持来冒充本次合法中间初态。

原始结果runs/2026_10_8-16_53__recovery_b25_swing_support_probe_ppo0/evaluation_00..05.json；初始化读回isolated/recovery_swing_support_probe_review_20261008/review.json。

## 工程与验证

新增scripts/prepare_recovery_swing_support_probe.py（CPU几何/独立声明）与scripts/review_recovery_support_probe.py（终态一次读取/请求-实际姿态对照）；完整发布标记绑定spec/budget/manifest/library SHA，独立授权登记。已有prepare_checkpoint_diagnostic不支持新pose，因此本轮专用声明只服务六项固定验证，不替换公共训练准备器。
项目geometry-request/submission27测试通过，冻结schema/plan与8个PORTABLE事件接口测试通过，两脚本AST/diff检查通过。一次冻结测试请求被新PORTABLE规则拒绝，未启动仿真；改用标明PORTABLE测试完成，不绕过规则。

## 下一决策

保留认证B25；不从退化new75接棒。本轮没有找到保留构型且更接近Swing成功的新静态中间reset，不启动新PPO。两条静态几何桥接路径均发生沉降回落，继续按root高度堆静态标签缺乏收益证据。
修正：原Swing已是合法训练起点；本轮“不启动新PPO”仅表示没有把失败静态候选自动接入训练，不是动态restore/成功Swing轨迹前置门槛。DrawBack成功轨迹不提供Swing→DrawBack路径证据。
下一优先准备真实150D输入—动作—奖励联合诊断，观测/奖励适用性与探索裁剪并列排查；动态restore仅可选，需完整状态/历史/时钟和短时readback，现有部分trace不足。零方差不是自动的字段失接或网络无用判据。详细诊断、身份区别及实施边界见RECOVERY_STANDING_PLAN第8.5节。
