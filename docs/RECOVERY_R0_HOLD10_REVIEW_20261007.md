# R0 hold10完成复盘

事件cdedeeee2e52939ec1435cc0。只读复核已有run、metrics、diagnostics和原始评估，
不启动仿真/PPO，不覆盖旧结果。run：runs/recovery_r0_hold10_from50_20261007。

## 实际完成与行为结果

source/smoke/formal均COMPLETED、exit0、failure=null。独立账本结算
source_eval1/evaluate0/smoke10/formal100；总110PPO更新、901120样本。
整链1616.2936s（26.94分钟），formal1397.2587s。无剩余formal额度。
无最终100s评估，无R1扩展，无自动续训授权。

| 模型 | 完整10s/通过 | mean abs pitch/roll rad | 稳态高度m | peak abs roll均值rad |
| --- | --- | --- | --- | --- |
| source50 | 8/8、8/8 | .021962/.072339 | .366665 | .073296 |
| 新25 | 8/8、8/8 | .026721/.085057 | .366226 | .085603 |
| 新50 | 8/8、8/8 | .032518/.097937 | .364407 | .100900 |
| 新100 | 8/8、0/8 | .032270/.144463 | .357107 | .171224 |

100次全部仅失败roll（mean<=.10、peak<=.15）；高度、接触、closure、采样
saturation等gate通过，无runtime fault。source仍优于所有已评估新候选。
25/50虽通过，但水平余量逐步减少；50已接近均值roll门槛，不能当作稳定改善。
75只保存、未评估，不推断其能力。

## 本次修改是否生效

formal完成768个episode，均长10.0s；正常timeout768，窗口未通过768，
完整成功0、physical task failures0、runtime faults0。success_once0，
2s成功不再reset，普通截断独立记录并通过installed PPO bootstrap。
这些证明接线生效，不能证明修正提高了水平保持能力。

训练随机策略每update policy采样saturation .25867–.31018，而确定性评估约.002。
因此训练窗口全部失败与确定性25/50通过可以同时成立；不能把窗口失败误报为跌倒，
也不能仅凭总失败计数推断某个gate主导，当前未保存逐训练episode失败gate分解。

| 区间 | 正常10s timeout | 连续reward/step | value loss均值 |
| --- | --- | --- | --- |
| 1–25 | 192 | +.017182 | .018976 |
| 26–50 | 192 | +.011551 | .002111 |
| 51–100 | 384 | +.000032 | .004916 |

新100当次roll weighted-.063245、pitch-.003694、height+.029623、support+.005。
持续训练的连续reward也在恶化；本轮不支持“策略通过增加总reward换取更大roll”的解释。
原短hold新100 mean roll约.130036，本轮新100约.144463；两轮episode、
reward事件、bootstrap和评估reset频率不同，不能据此单独判断哪个修改更差。
但已排除“只有+10与短reset导致退化”的充分解释，不能称联合修正解决了问题。

## critic、更新与来源保持

选定真实在线diagnostics见formal/diagnostics_update_{1,8,25,50,100}.json。
新1：value均值-1.094740、return-.674653、raw advantage+.420087；
新25：value1.517670、return1.480116；新50：1.030875/1.053746；
新100：-1.427588/-1.702010，raw advantage mean-.274422。
critic随目标变化适应；loss未出现旧200分支的大幅膨胀或nonfinite。
这些不是独立真实回报校准，不能排除估计偏差，也不支持critic崩溃是本轮唯一根因。

Full-rollout before/after actual PPO update mean KL在1/8/25/50/100分别
.019950/.016964/.013856/.021858/.005427；clip fractions分别
.298218/.262939/.218750/.306274/.058594。不是minibatch scheduler KL，
不能直接当作某一KL控制器的输入或累计source漂移。

实际first optimizer-step BC weighted norm/PPO actor norm：
8=.02281%，25=.07183%，50=.13372%，100=.36600%。
整体cosine分别-.3270/+.1717/+.2141/-.1465；leg分量更常逆向，
但其贡献也很小。范围仅选定update第一个step、clipped PPO+entropy与BC，
不能泛化为所有minibatch或所有reward项的因果梯度。
证据支持现有BC并未强力保留来源，而非BC梯度主导训练。

BC选前256个eligible输入：新25/50实际age仅.72–.75s，新100为2.72–2.75s，
新8为8.96–8.99s。长episode已让它有时见到晚期，但每个batch仍高度集中于
rollout开头约4步、同步的64env；没有均匀覆盖整个episode。
新100六通道MSE中右active约.008049、右wheel约.014961；这里只是已选on-policy
输入上的teacher/student差异，不能当作同输入跨checkpoint对照或物理因果结论。

## 下一步决策

保留source50为已验证基线，不从新100继续，不直接扩展R1。
25/50作为通过但退化的诊断候选保存，非升级来源。
优先准备来源保持的受控实验：先在CPU/离线核查同输入通道误差，再改变BC
样本的时相覆盖；coefficient增强另作对照，避免同时改reward/critic/物理。
目标是连续更新后R0不退化，不是让critic loss更低。需要新spec、新预算和明确授权。
同时保留训练随机策略与确定性评估的差异诊断，补episode逐gate失败统计。

## 报告工程缺口

运行冻结candidate_selection的best_new_evaluated_candidate错误指向source；
best_observed/accepted指向source是正确的。本轮按原始25/50/100评估复核，
不把该角色误标当作新模型通过。当前共享代码已存在candidate_roles改动，
不能用它覆盖历史运行JSON，应另行核验修复。
completion_report.md约9132080bytes，内嵌wheel_geometry等完整轨迹；
摘要应排除数组并链接raw JSON，避免层层重复序列化。原报告未改写。
