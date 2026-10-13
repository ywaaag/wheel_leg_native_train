# Recovery冻结随机rollout：实际探索、Reward与Advantage读回

2026-10-09用户明确批准09_40有界重试。run `runs/2026_10_9-09_40__recovery_b25_frozen_rollout_guardfix`，attempt `1d7e70e80ee34f028d60bb8eda72e3e3` 已COMPLETED，monitor结算28.666214秒，前次失败5.328720秒累计33.994934秒。没有PPO/optimizer更新、没有新checkpoint，不自动续训。

## 边界与身份

来源认证RecoveryB25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。保留fixed26/25/13、beta=.3支撑纪录reward、150D、新USD及原控制/限矩，sharedphysicalGPU0→cuda0，未停止其他任务。

完整采集2×128×64=16384 transitions。`frozen_rollout.npz`压缩约11.19MiB，小于64MiB上限；JSON记录每数组shape/轴/字段与SHA。实际actor/critic/Adam state_dict逐项相等。RSL compute_returns保持原timeout bootstrap及每rollout全局advantage normalization，不执行update/optimizer.step。工程诊断gate NOT_RUN，不冒充完整起身/10秒保持认证。

本轮授权登记与独立receipt、spec/budget/publication身份核验完成；提交前frozenPORTABLE5项及完整初始化通过、check-submission READY。此前修复后全CPU683通过，本轮未额外改变源码。现runtime成功覆盖前次失败的adapter分支。

## 实际分布

| 组 | 受控样本数/全部占比 | 轮样本裁剪率左/右 | value均值 | raw advantage均值 | normalized advantage正比例 |
|---|---|---|---:|---:|---:|
| Swing | 2496 / 15.23% | 100% / 98.60% | −.4102 | −.2131 | 49.00% |
| DrawBack | 5400 / 32.96% | 3.94% / 0% | 5.1507 | +.05866 | 90.96% |
| R0 | 3328 / 20.31% | 0% / 0% | 5.3178 | +.05880 | 92.58% |

剩余样本是初始化等非受控阶段；不能按名义40.625%推定Swing有效份额。只采每env累计2.56秒，旧组未覆盖完整10秒保持，不能据此新增保持证书。

Swing轮mean绝对值均值1.8753/1.7104，物理clipped normalized action std左0、右.003205（轮目标std约0/.3205rad/s）。四腿clipped action std约.150/.219/.131/.240，腿有随机变化，但真实hip到wheel长度范围左.35834–.37593、右.37537–.37599米；无双侧都低于.30米样本。小规模采样尚未探索到类似DrawBack的双侧收短构型。

## 新奖励有没有影响学习目标

Swing新增正reward样本403个；其中raw advantage平均−.50742，normalized advantage为正仅5.955%，零新增reward样本raw advantage均值−.15646。这个比较混合不同起步时相，不能说“奖励进展方向被学反”或新增奖励导致负advantage。局部进展仍属于最终失败trajectory，critic与原回报共同决定advantage。

固定轨迹和冻结values下，沿原GAE递推单独计算bonus贡献：eligible样本平均+.0005236、最高+.006880；实际raw advantage std约.30002。扣除bonus后0个eligible样本raw advantage改变正负号。这是本次beta=.3对这些轨迹信号较小的直接证据，不是梯度比例，也不是重训反事实。value均值低/advantage负不能唯一证明critic不适配、record隐状态别名或全局归一化是主因。

读回检查：reward公式误差0，rawadv=returns−value误差0，全局adv normalization复算最大误差4.77e-7，旧组新增bonus严格0，权重/Adam不变。原始与bootstrap后storage reward分开保存。

## 下一决策

用户提出“更新太少”仍是合理假说：短训25更新与两个冻结rollout都不能测收敛。当前证据同时说明有效轮探索受裁剪限制、几何新奖励对实际advantage影响小；不能把这些问题假定随更新次数自动消失。

建议下一先在已有NPZ上做纯CPU配对审核：按同family/episode受控时相比较腿动作变化、收短进展与advantage，核算多个候选reward预算对GAE的敏感性但不应用到模型、检查是否值得改系数。若用户优先验证迭代次数假说，可准备独立同配方更长100更新块，保留B25与10/25/50/100候选、旧组退化保护、不自动提高beta/std；须明确新增训练授权。该块是检验长期学习的实验，不宣称已有收敛趋势。

本次没有决定改150D或控制架构，不叠对称/制动/限矩。保留B25；本轮没有新策略可播放。

## 产物与变更

新run原始NPZ/evaluation/terminal/monitor_exit；离线`isolated/recovery_frozen_rollout_guardfix_review_20261009/review.json`绑定输入SHA，不复制轨迹。运行声明授权登记更新仅限09_40独立spec/budget/receipt/approval。新增本报告并更新STATUS与RECOVERY_STANDING_PLAN；未改训练源码/旧失败证据/外部项目、未清理文件或Git commit。
