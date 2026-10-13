# Recovery同配方100更新终态复盘

事件3f64aae0ea6447e0ce3bea95。run `runs/2026_10_9-09_53__recovery_swing_support_record100_from_b25`。同配方延长至100更新没有获得Swing起身能力，且50/100旧两组完整接触证书退化。不继续该分支；保留认证来源B25，不接latest100。报告best_new25只是本轮诊断排序最优，不能称新的Swing成功模型。

## 完成与消耗

链COMPLETED描述后台流程完整，formal实际STOPPED_BOUNDED，原因standing regressed in two consecutive full evaluations。停止发生在update100：full50/100连续两次旧能力失败；不是工程异常，不是墙钟耗尽。smoke10、formal100，合计110更新/901120训练样本，独立账本全部结算、无RUNNING。链墙钟2133.247269秒，约35.55分钟；source142.889/smoke256.750/formal1723.422秒按各phase实际记录。未做100秒耐久，accepted为空。

来源认证RecoveryB25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44；每候选checkpoint按raw evaluation SHA核验。独立CPU复盘`isolated/recovery_record100_completed_review_20261009/review.json`绑定source spec、原始评估、候选文件、metrics、formalterminal SHA；旧证据不改，未重发已收到通知。

## 同协议行为结果

|候选|Swing通过/入口|Swing峰高均值m|受控时长均值s|DrawBack完整通过|R0完整通过|
|---|---|---:|---:|---|---|
|sourceB25|0/8，入口0|.231374|.300|8/8|8/8|
|new10|0/8，入口0|.231499|.300|8/8|8/8|
|new25|0/8，入口0|.231843|.320|8/8|8/8|
|new50|0/8，入口0|.231843|.34875|0/8|0/8|
|new100|0/8，入口0|.230508|.440|0/8|0/8|

Swing全部8env均tilt终止，合法初始化、无runtime fault，没有.30米入口或保持窗口。存活前缀延长.14秒但末点峰高较来源降低约.87毫米，不能当起身进展；env0 new100左右最短hip→wheel .36549/.37597米，末段又约.37593/.37599米，仍没有明显双侧收短。

旧两组50/100均观测到完整10秒窗口，失败项continuous_contact与依赖它的terminal_certificate。不是缺测、不能通过缩短窗口补救。其余高度/倾角/限矩/closure等证书检查通过；不能说旧两组全部摔倒。dual_contact保持窗口均值：source/new10/new25均100%；new50 DrawBack91.08%/R0 89.59%；new100恢复到99.46%/99.41%，仍不满足冻结协议要求的连续100%接触，所有env至少有失触。100比50接触改善，不等于恢复完整能力。运动/漂移不是当前gate，本次不新增门槛。

## 奖励与探索

formal100/100 rollout有真实新增支撑纪录reward，smoke wiring_certificate PASSED。累计受控Swing pre_entry152231transition，占formal样本18.58%；权重不变而仅增加次数的实验确实执行完毕。

轮随机实际sampleclip eligible加权左100%、右98.13%；update100 normalizedmean绝对值1.7780/1.7133，std .04922/.03883，主体仍越界。限制是有效动作差异不足，不把rawmean变化或更长失败前缀当物理技能。此前冻结随机rollout已证明左轮clipped action std0，右很小；本次训练没有解决这一现象。存在腿目标和初态不匹配、新reward弱、共享actor旧能力退化等多项证据，不能仅凭clip认定唯一根因或PPO梯度为零。

## 对“迭代太少”的判断

25更新不足的可能性已用相同配方100更新受控验证；结果没有Swing净收益，还出现旧能力损失。这削弱“只要多训即可”的判断，不证明所有更长训练或所有RL配方都不可学。继续同配方到200/500目前缺乏净进展支持，而且已触发冻结保护，不授权自动延长。

## 下一方向

暂停支撑纪录beta=.3单独持续更新分支，保留B25作为来源，new25仅保留本轮早期比较候选。优先处理实际动作探索与Swing起步策略不匹配：准备纯CPU动作分布候选审核，明确raw mean/sample、clipped actuator target、log_prob及warmstart语义；同时读取旧DrawBack/R0的输出变化，防止靠改变两旧任务解决新任务。必须有版本声明和独立新实验，不把失败meanaux复用成“已解决”、不只是加std/增beta，不暗加轮制动/状态机/限矩。

当前诊断尚不能选择唯一方案；若涉及distribution接口变化，先做CPU对照和可追溯声明，再提交用户审查。150D/原控制边界保留，不在本轮擅自更改。无新runtime/PPO授权。

## 本轮文件变化与验证

新增本报告、独立SHA绑定review.json，更新STATUS和RECOVERY_STANDING_PLAN最新状态/下一分支。核验原始五组候选、各8env结果、完整保持窗口、ledger计数、停止原因及实际reward/sampleclip。纯CPU复盘成功，未修改源码/旧run/raw/spec/ledger/checkpoint、未启动仿真/GUI/PPO、未删除文件、无Git commit/push。
