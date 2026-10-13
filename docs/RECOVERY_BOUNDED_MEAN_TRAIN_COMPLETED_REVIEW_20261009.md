# Recovery轮均值有界短训：终态复盘

事件cb801f133eceed910c103888，run `runs/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25`。COMPLETED，smoke10/formal25，合计35更新/286720samples，链994.294147秒（16.57分钟）。所有exact phase ledger已结算，无新运行/自动续训。最佳new25未通过Swing联合协议；保留认证B25，不能称本次已训练出起身。

## 同协议行为

|候选|Swing通过/入口|峰高均值m|受控时长s|DrawBack/R0完整10秒|
|---|---|---:|---:|---|
|迁移sourceB25|0/8，入口0|.231364|.29875|各8/8|
|new10|0/8，入口0|.231855|.31|各8/8|
|new25|0/8，入口0|.231970|.33|各8/8|

Swing全部倾斜失败，合法初始化，无新站立窗口。峰高变化约.61mm、时长增加.031秒，不算实质起身收益。旧两组完整保持100%双轮接触，gate通过；本次没有观察到旧能力证书退化。未做100秒耐久。new25 SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c，new10 SHA7a12645d7d5a5999144a0f813e81e23ccb6161fd8f0b3f8976eeb7a9d3a0b578，按raw evaluation及文件核验；来源仍8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。

## 有干预证据的改善与剩余阻碍

实际eligibleSwing训练样本35702，占formal17.43%。两轮真实sampleclip eligible加权17.08%/8.76%，明显低于原Gaussian支撑纪录25更新的100%/98.48%；末批mean绝对值.94972/.92771、meanclip0，std .04840/.03888。相比原分布，单变量wheelmeanbounded实质改善了随机wheel control变化空间；这是采样指标收益，不是恢复技能或长期保留保证。

formal25/25 rollout新增纪录reward非零；当前rewardaudit在末批累计reset1989、baseline1234，failed/ineligible/episodebudget违规均0（完整逐批证据保留CPU review）。smoke证书绑定实际mean/未全clip采样、rewardbaseline/reset及episode/group事件，formal真实执行，未发生工程阻断。

new25 env0左右hip→wheel最短.36308/.37596米，末段约.37593/.37599米；右腿仍几乎没收短。旧入口第一步腿目标/实际位置偏差已有证据，轮分布干预没有改变四腿坐标，所以不能期待它自动解决腿部协同。当前不能唯一归因reward、critic或腿探索，但本轮足以否定“只看轮clip是否下降就接受”的做法。

## 下一建议

暂停自动追加本分支。下一优先已有轨迹的腿部动作—真实关节—力矩—几何事件对齐：逐通道核对首次接管目标、action/关节限位裁剪、PD限矩、实际收短和tilt先后，重点解释右腿不收短及首步target jump。对照成功DrawBack构型与原Swing真实passive branch，区分目标未探索到、目标达到却机构不收短、或力矩/接触导致动作未执行。先CPU离线，不额外加对称、腿bias、制动或reward。若缺完整preq/子步，明确证据缺口再提出最小有界诊断，而非伪造因果。

保留认证B25作为原分布完整来源；本次new25以新action_distribution身份保留为实验候选，不能无spec直接按旧Gaussian播放或训练。未来若更长训练，要以本次探索改善而无起身的证据选择具体假说，独立授权，不暗续latest。

## 文件与验证

新增本报告与`isolated/recovery_bounded_mean_train_completed_review_20261009/review.json`，更新STATUS/RECOVERY_STANDING_PLAN。CPU reviewer绑定source spec/原评估/候选checkpoint/metrics SHA，比较三组各8env/完整窗口/实际采样及奖励audit；不复制原始大数组，执行成功。本次仅复盘，未改训练源码/历史raw/spec/ledger/资产，无仿真/PPO/GUI/清理或Git提交；通知已收到不重发。
