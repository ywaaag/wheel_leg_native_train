# B25 Swing桥接冻结验证

用户同意执行已准备五项PPO0：原DrawBack、R0、朝历史Swing描述构型5%/10%桥接和完整历史R1候选；8env/项，同一B25与minimum-height协议，≤1200秒含清理，PPO/optimizer updates0。
config/run根2026_10_8-13_28__recovery_b25_swing_bridge_ppo0，独立exact-ID ledger授权当前session，shared GPU0，不停止其他进程。
共享CPU543 passed，实际冻结专项9 passed；source/model/asset/library SHA已核验，原证据只读。
提交只走supervisor --evaluation-only --launch --wait，前台等待自有有限评估退出，不轮询长训。

## 任务身份

B25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。
原DrawBack active q约[-.02339,1.43179,+.02338,1.43216]rad，root.16847m。
5%桥接约[+.03488,1.28969,-.03493,1.29010]rad，root.18542m；10%约[+.09315,1.14759,-.09323,1.14803]rad，root.20268m。
历史Swing描述候选约[1.14203,-1.41021,-1.14273,-1.40911]rad，root.16869m。
根高度均由当前资产理想最低collider推导，闭链被动关节沿求解分支；不是按root高度插值、动态reset或示教控制。
目标语义仍需用户GUI确认，family名不代替实际姿态；成功也仅覆盖该静态初态。

本次不执行std再减半，evaluation-only不会调用训练探索初始化；保留B25已有轮std与全部权重。
新能力失败与初始化失败分开：物理初始化有效而策略失败可以成为下一局部学习任务，初始化非法需先修构型/沉降声明。
不自动启动Swing PPO、不加对称/制动/reward变量、不改USD或限矩。

## 实际结果与初始化读回纠正

五项COMPLETED，terminal墙钟258.0385秒，monitor退出后exact账本结算258.4058秒（4.31分钟）。
attempt7490f7e34ca0426f951c4d30708871db；evaluate used1，PPO/optimizer updates0。
[逐项结果审查](../isolated/recovery_b25_swing_bridge_review_20261008/review.json)及[初始化关节读回](../isolated/recovery_b25_swing_initialization_readback_20261008/review.json)。

| 请求family | 初始化有效 | 完整起身保持 | 解释 |
| --- | --- | --- | --- |
| 原DrawBack | 8/8 | 8/8 | 原能力保持 |
| R0 | 8/8 | 8/8 | 原能力保持 |
| 5%桥接 | 8/8 | 8/8 | **沉降回原DrawBack后才获接受，不能认证独立桥接能力** |
| 10%桥接 | 0/8 | 0/8 | 初始化拒绝，尚不是policy能力结论 |
| 历史Swing候选 | 8/8 | 0/8 | 构型保留、合法初始化，策略未进入入口后因tilt终止 |

5% env0首样本主动q约[.03515,1.29286,-.03520,1.29333]，接受时（trace98）已变为[-.02339,1.43180,.02338,1.43219]，几乎原DrawBack。
因此请求pose标签与实际控制起点不同；8/8只是沉降后原构型能力，不把source_pose_id或总episode数当新路径覆盖。
10%首样本约[.09366,1.15053,-.09373,1.15093]，尾部也趋向原DrawBack，trace101结束、initial_valid=false；未保存全部被动关节速度/各沉降predicate，不能断言唯一拒绝项是主动关节速度，也不直接延长settle预算掩盖构型漂移。
历史Swing候选接受trace39主动q约[1.14264,-1.40933,-1.14261,-1.40931]，与请求相符；控制后峰高约.231m，未达.30入口，recovery约.52秒tilt≈1.067rad触真实任务终止；runtime_fault0、闭链合法。
普通tilt失败说明当前actor未掌握该静态Swing起身，不是工程障碍阻止新任务学习，也不是必须先会Swing才允许训练。
原DrawBack/R0证书依旧有效；未改gate/std/动作/资产，没有新增训练或重复评估。

## 下一步建议

用户希望尽快进入Swing：本次已经找到8/8有效、保持构型的历史Swing候选，可作为Level3学习起点，先GUI确认它确为目标姿态。
不继续用会自行沉降回DrawBack的插值标签堆课程。下一版本优先从完整认证B25准备一块有界Swing学习，保留原DrawBack/R0分别评估。
训练时继承B25实际std，不再次应用父B的0.5初始化倍率；保持奖励/物理/协议，初态分布作为课程变量单列。
建议新组40%、已认证原DrawBack40%、R0 20%，或按原课程约定保持旧组总占比≥40%；具体比例需在新spec中冻结，不改当前已完成评估。
新增Swing课程runtime/PPO预算尚未授权，本轮不续训。新任务尚未通过不作为smoke的工程拒绝理由，初始化/闭链/实际事件接线必须通过。
