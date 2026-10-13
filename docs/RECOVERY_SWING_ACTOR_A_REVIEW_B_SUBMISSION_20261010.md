# Swing-only受控actor A终态与B首次提交 — 2026-10-10

A事件4376e197211f60da7543593e，14_23 A链COMPLETED，source/smoke/formal正常，smoke10＋formal100、901120原始样本、1378.72285秒（23.0分钟），formal余额0。不续A。

## 受控更新与行为

smoke wiring PASSED，controlled_actor_metrics_sha256与真实metrics匹配。Formal100真实valid actor samples420668/819200=51.35%，超过25万目标；actor optimizer1600次，无全invalid minibatch。每更新valid样本与preaction受控Swing计数一致，初始化仍进入原critic/GAE时间轴，无旧任务训练/评估。工程计数一致不代表已证明该修正是唯一原因或保证恢复。

|update|Swing通过/入口|峰高均值m|终止前恢复秒|左右最短腿长均值m|双侧≤.34m持续50ms环境|
|---|---|---|---|---|---|
|来源|0/8，无|.231973|.330|.36310/.37599|0/8|
|25|0/8，无|.232399|.370|.36627/.37599|0/8|
|50|0/8，无|.230518|.42875|.36989/.37599|0/8|
|100|0/8，无|.230258|.84125|.37593/.37599|0/8|

Formal训练累计双侧缩短里程碑0，保持sample/成功pulse0。最后rollout双侧长度均值≈.37592/.37599，四腿同局部方向命中0。A学到更长失败前缀，但收腿没有进展，左腿反而更接近长腿构型，不能把new100成为diagnostic best等同起身成功。最终0/8/standing_entry failure，durability NOT_RUN。

source/25/50/100原始eval分别核验spec及checkpoint SHA；汇总/引用SHA与真实mask/里程碑读回在isolated/recovery_swing_a_review_b_submission_20261010/A_summary.json。不同candidate访问状态不同，没有用这些汇总宣称动作初始化干预因果。

## B

B此前明确授权且原账零attempt/used；A终态后核验fresh输出、session、GPU0 UUID/shared资源、独立账本和初始化candidate身份，公共supervisor check READY后仅首次提交。来源是未训练初始化候选SHA d074488410257e02b44704f8b2119612617cf44267c50d6e4561f72d39a9ab51，不接A100；source_eval/smoke/formal各加载同B，formal不继承smoke。

B run runs/2026_10_10-14_23__recovery_swing_controlled_actor_b。唯一5秒握手SOURCE_EVAL、worker身份OK、formal首更新未核验。仍smoke10/formal100/901120样本、chain5400秒，source900/smoke900/formal3500；两臂累计上限不追加。已有owner终态at-most-once通知当前session，不轮询、不新建watcher、不停止其他任务。

下一B终态比较：初始化后真实动作/双侧收短是否出现、PPO是否保留，以及卡在转腿/支撑/落地/入口/保持哪一步。A结果只说明本次common基础未学会，不先改reward/std或延长A。

本轮新增本报告、isolated摘要/B提交证据，更新STATUS与Recovery plan；B新run由supervisor创建。旧A run/evaluation/ledger/checkpoint只读，源码未改，无commit。通知不是新增授权，B首次运行依据原明确两臂授权。
