# Recovery纪录奖励可学习性：离线事件、几何贡献和动作别名审核

2026-10-09用户同意执行终态后的CPU审核。只读两份已有证据：08_42支撑纪录PPO0真实input_capture，以及08_59短训来源/new10/new25完整评估。没有仿真/采样/optimizer/新checkpoint；旧run、spec、ledger保持只读。

## 主要发现

1. **奖励不是零，但只覆盖早期局部进展。** 真实PPO0的8env共32个正奖励事件，均在受控起步.01–.04秒。env0总奖.00539382，折扣后.00531180；此后至约.30秒tilt失败不再刷新最好纪录。原reward含末步失败−1，env0折扣净回报约−.45756，末步总reward−.98856。不能将新增reward百分比当作PPO梯度比例。
2. **没有发现这几次奖励由机体翻转刷分。** 将每次纪录刷新相对上次最好构型的Q变化按三因素做精确Shapley几何分解：length、root系腿方向、body系重力方向。平均每env对应reward贡献约+.004006、+.009163、−.007795，总约+.005374。机体旋转在这些事件中抵消收益；收短和腿方向变化提供正贡献。分解是数学记账，不是控制干预的因果证明，不保证其他轨迹没有几何投机。
3. **起始目标与实际腿姿存在较大跳变。** 来源env0首次受控实际active q约[1.134,−1.384,−1.131,−1.398]rad，目标约[−.393,−.254,+.452,−1.600]rad。三条通道绝对误差约1.53/1.13/1.58rad。这些目标在当前动作尺度内，不能直接判成接口错误；它提示站立来源策略从Swing接管时的动作与初态明显不匹配。左腿最多只短约1.2cm，右腿几乎不收短，最终两腿又约.376米。
4. **轮控制的别名非常明显。** 来源env0 raw wheel action左右变化范围约[−2.296,−1.530]/[−2.222,−1.008]，clipped pair全程只有[−1,−1]，即两轮目标−100rad/s。new10/new25仅个别右轮样本略回界内（约−.997/−.999），主体仍相同；变动的raw输出大多映射同一物理速度目标。腿也有裁剪：来源env0 left_knee raw越界占80%，new25约46.9%；这不是新USD机械限位触发率。实体关节限位、action裁剪、轮速度目标、力矩饱和四者不能混称。

## 能排除与尚不能确定

有实际奖励、奖励分解与首步真实动作，所以不支持“奖励未接入/起点非法/观测全不响应”的解释；前次实际150D重算只核验接线，不保证观测对Swing充分。

没有完整随机training transition的record/reward/value/return/advantage。确定性动作高度裁剪与随机clip统计共同支持探索效率低的假说，但不能据此断言PPO梯度为零、critic隐record是主因、改变std就会成功，或几何奖励架构必然错误。也不能从仅一条冻结失败trajectory判定需要提高beta：现有奖励发给局部改善，最终失败是组合行为问题。

## 下一步的最小证据需求（尚未运行）

不再直接追加同配方训练或叠加制动/对称/更大beta。建议先准备一个独立有界随机rollout联合读回接口，严格冻结B25 actor/critic/Adam、保留现有sampling/control/reward，收集当前ppo.act已有样本；不执行optimizer.step，不额外采样或改变分布缓存。

建议规模为2个rollout×64env×128步=16384 transitions，PPO更新0，物理GPU0共享、墙钟≤600秒，新独立run/ledger，压缩NPZ+JSON、详细数组上限64MiB；只记录必要150D/action/mean/std/clipped action/腿目标与实际q/几何/失败mask/原始与新增reward/value/return/advantage/episode身份。需要区分controlled Swing与初始化及两个旧组，不从名义环境配额推定实际样本比例。全部统计来自同一真实序列；计算returns不等同PPO更新。当前尚无这个可提交接口/spec/授权，600秒是建议上限，不是已获许可。

该读回将直接回答：正进展事件是否与有效腿动作差异相连、裁剪后的动作有没有实际探索、收益是否被基础reward/critic误差压过，以及record历史是否出现同obs不同目标的别名迹象。若仍无可辨别探索，先选择一个动作分布干预；若探索已有有效收腿而回报排序反向，再选择reward干预。一次只改一个变量，不自动扩大150D或更换控制架构。

## 文件和验证

新增`scripts/audit_recovery_record_learnability.py`与`tests/test_recovery_record_learnability.py`；后者依赖本项目scripts，标PROJECT_DATA，不伪装为冻结PORTABLE。输出`isolated/recovery_record_learnability_20261009/audit.json`含全部输入SHA、32个正奖事件、8env贡献/回报及三个候选动作摘要，未复制大轨迹。

两项CPU数学边界测试通过：混合因素交互的贡献和严格闭合、纯机体旋转不会归因于收短。真实审核成功、actor文件SHA核验、基准FK误差约1e-6；数据均为policy100Hz和latest held PD，不冒称完整5ms子步动力学。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX和本报告。没有提交运行、通知、删除文件或Git commit。
