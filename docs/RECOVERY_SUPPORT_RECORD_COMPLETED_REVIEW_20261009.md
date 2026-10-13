# Recovery支撑纪录短训终态复盘

事件d88f3ab24fe16fe693d27f3e；run `runs/2026_10_9-08_59__recovery_swing_support_record_from_b25`。COMPLETED仅表示授权流程完成；Swing没有学会，没有新的三组完整接受候选。保留认证Recovery B25作为DrawBack/R0来源，不接本次latest，不自动续训。

## 预算和身份

smoke10/81920 samples，formal25/204800 samples，合计35/286720。链墙钟979.008447秒（约16.32分钟）；三个exact-ID ledger均COMPLETED且结算，额度已用完，无RUNNING记录。source144.17、smoke256.09、formal568.96秒；phase wall和chain wall分别记录，不混用。未做100秒耐久，原因无三组完整接受候选。

source checkpoint仍为`runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt`，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。本次formal10/25 checkpoint SHA按原始evaluation实际文件核验。新CPU复盘输出`isolated/recovery_support_record_completed_review_20261009/review.json`，包含来源/原始评估/metrics输入SHA及几何复算；没有复制轨迹数组或修改旧run。链原completion_report保持只读，通知已送达，不重发。

## 同协议完整比较

| 候选 | Swing通过/入口 | Swing最高高度均值m | Swing受控时长均值s | DrawBack完整10秒 | R0完整10秒 |
|---|---|---:|---:|---|---|
| 来源B25 | 0/8，入口0 | .2313744 | .30 | 8/8 | 8/8 |
| 本次new10 | 0/8，入口0 | .2314994 | .30 | 8/8 | 8/8 |
| 本次new25 | 0/8，入口0 | .2318428 | .32 | 8/8 | 8/8 |

三组原始初态有效，Swing8env均因tilt失败，非runtime fault；没有到.30米入口或任何保持窗口。最高高度变化约0.47毫米、时长增加.02秒，是微小诊断变化，不构成实质起身改善。来源与候选使用同一v2首次confirmed entry后下一1000样本的10秒窗口，提前失败不缩短要求。

链最佳来源“通过False”指Swing+两旧组联合完整能力不成立；不能据此说来源B25已经丢掉此前认证的DrawBack/R0能力。本次来源和两个新检查点均再次证明两旧组完整10秒通过。

## Reward确实进入训练，仍未产生恢复动作

smoke wiring_certificate PASSED；该证书绑定实际metrics SHA、actor变化、真实episode/family初始化事件及至少一次正纪录奖励，并非单凭10更新。本次formal25/25 rollout都有非零support_record_progress，全部env合计新增6.23408；这是跨env/episode总和，不是单episode6.23。每transition weighted均值范围1.6594e-5至3.5130e-5，受控Swing pre-entry累计35178样本，占全部formaltransition17.18%。原始mask/基准/公式由前次独立PPO0核验；本次缺随机逐episode record全轨迹，不能冒称再次逐帧证明所有reset/cap。

随机训练轮动作真实sampleclip按eligible加权：左100%，右98.482%。最后rollout normalized absmean约1.8727/1.7469，std约.04887/.03848，仍深处动作[-1,1]裁剪区；这是ppo.act实际样本统计，不是解析概率。不能仅从裁剪推断PPO梯度为零，或断言它是唯一原因。

原生hip到wheel距离的完整确定性geometry复算：env0起点左右约.3756/.3760米；来源/new10/new25的左侧最短约.36361/.36351/.36373米，右侧最短均约.37596米，末段两侧又约.37593/.37599米。新增几何奖励没有让策略形成明显双侧收腿。env0 peakQ .25298→.25314→.25278，也没有持续改善。数据为post-control真实几何，不当作exact reset baseline或全部随机训练动作。

## 结论与下一准备

本轮排除了“新增reward从未接入trainer”的解释：有实际正奖励、真实更新与完整评估；但beta=.3这一配方在25更新内无Swing起身收益。两旧组保住；成功点不拼模型。不能外推更长训练必然失败，也不能因此直接认为提高beta就会成功。

暂停相同配方追加训练。下一优先CPU离线做奖励可学习性审核：对已有真实几何/control/动作轨迹，区分收短、向下方向变化及机体翻转对Q的贡献，检查进展奖励出现在哪些动作/终止前时刻；核算其相对原reward的时域回报，以及wheel rawmean不同但clipped control相同的动作别名。结合左右腿真实目标/实际运动确认可产生进展的通道，不直接叠加std、对称、制动或限矩。

本次诊断没有完整按family advantage/return/critic梯度或随机逐步输入轨迹，不能回答critic别名是否主因；若离线证据不足，下一应提出最小有界runtime采集的时长/字段/存储/授权，不能暗做仿真。reward state仍未显式输入150D这一限制保持公开，不以工程通过替代观测充分性证明。

## 本次文件变更

新增本报告与独立CPU review.json；更新STATUS与RECOVERY_STANDING_PLAN的最新终态/下一准备。本次未改训练源码、原spec/ledger/checkpoint/raw报告，不启动仿真/PPO/GUI、不删除文件、不停止进程、无Git commit/push。离线工具成功执行并验证候选文件SHA，文档改动无需新增测试。
