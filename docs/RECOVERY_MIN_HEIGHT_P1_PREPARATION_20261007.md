# Recovery P0复评与P1目标迁移准备
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


最新终态纠正：事件0809b5e45005c37591bb8494，链FAILED，source reset inference tensor错误；source一次/70.26秒、PPO0更新，无新候选。复盘与CPU修复（该报告已按文档整理删除，长期结论见 TRAINING_EXPERIENCE_REUSE.md §12）。下方批准/提交与SOURCE_EVAL仅为历史握手，未自动重试。

## P1新链已获批准并提交 — 2026-10-07

用户本轮明确批准source≤900秒、smoke≤20更新/900秒、formal≤100更新/7200秒，总120更新/983040样本；当前会话已绑定。独立根`runs/2026_10_7-22_10__recovery_min_height_p1_from_s50`。一次提交握手为`SOURCE_EVAL`，submitted=true、submission_verified=true；formal_first_update_verified=false，不声称formal已更新。共享物理GPU0，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，未抢占其他进程。授权后CPU509 passed、冻结副本53 passed、plan PASS。后台owner按预算执行并终态通知，交互worker不轮询、不自动延长。

[提交回执](../artifacts/2026_10_7-22_10__recovery_min_height_p1/authorized_submission_stdout.json)及[授权记录](../configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/authorization_receipt.json)。后文UNAUTHORIZED是准备时历史状态，实际状态以独立账本/manifest/终态为准。

依据：AGENTS.md及RECOVERY_STANDING_PLAN.md第0–13节。本文记录执行结果，不改写最终计划或历史证据。
本轮完成离线分析、版本化代码、CPU验证和UNAUTHORIZED声明；没有AppLauncher、仿真、PPO、GPU检查、后台提交或通知发送。

## P0：旧轨迹按新目标重评分

输入为20_55链source_eval及formal25/50/100；逐项核对原始JSON、冻结spec、模型和当前USD SHA。
输出：[独立复评](../isolated/recovery_min_height_p0_20261007_verified/review.json)。
Torch评分与独立NumPy循环交叉核验首次入口、保持前缀及通过决定，原始报告不覆盖。
R0只保存失败末窗，缺完整state/posture，四个模型均8个UNKNOWN，不可从均值补出10秒通过。

| 模型 | DrawBack入口数 | 首次入口恢复时钟 | 保持前缀 | 新完整证书 |
| --- | ---: | --- | --- | --- |
| S50（18_06 update50） | 8/8 | 0.89–0.90s | 8.37–8.54s | 0/8：高度、接触与倾角失守 |
| 20_55 new25 | 8/8 | 0.83–0.84s | 10s | 0/8：采样饱和失败；env0为49% |
| 20_55 new50 | 0/8 | 未确认入口 | 无入口 | 0/8：standing_entry |
| 20_55 new100 | 8/8 | 1.67–1.81s | 10s | 0/8：roll、饱和；env0为0.10785rad/82.3% |

前缀不含全窗均值与饱和判据，不能代替完整认证。新入口不使用旧7.8秒窄高度带。
模型角色：旧latest=new100，旧best_new/best_overall=new50（SHA并列排序）；accepted=null；new75未完整评估。
P1 fallback/source为S50，SHA `de06b39d2a88c44250309b4ae0509188b532cc5c51a681d456a545c307243694`。
对齐候选新增确定性轮振荡且未取得完整收益，不接棒、不提高对齐权重。
这是旧轨迹的离线重评分，没有新的学习收益或物理复验。

## P1：新版本语义

新协议 `autonomous_rise_min_height_v2`：高度>=0.30m，无任务高度上限，机体正净空、双轮>2N、入口abs角度<=0.10、tilt<=0.18，连续20个有效100Hz样本确认。
初始化接受当步不计入口；锁存首入口，随后独立采1000个保持样本，禁止重新选窗或拼接episode。
入口前11.5秒deadline；入口后不受该deadline截断。瞬时硬条件失败锁存证书失败，物理合法时继续至约定终点。
全窗角度均值<=0.10、峰值<=0.15、tilt<=0.18、采样饱和<=5%、闭链<=5mm；0.11短暂倾角不因入口门槛被永久判败。
完整1000样本后task_success/task_failure有限任务终止，奖励+10/-1一次；不做timeout bootstrap。旧版本行为保留。
R0明确采用同一首次入口任务，最大23秒，而非标成固定10秒。所有family独立报告。

高度项为2*clamp((h-.168)/(.30-.168),0,1)+3*clamp((h-.30)/(.34-.30),0,1)。
0.34以上均为5/秒，连续项dt=0.01只乘一次；overshoot权重0。历史height command .36只作兼容输入。
其余reward、std、gamma/lambda、LR、actor/critic/Adam、DrawBack、USD、PD、40/5.5Nm和1.6/100动作尺度保留。
[奖励曲线](../artifacts/2026_10_7-22_10__recovery_min_height_p1/height_reward.png)及[数据](../artifacts/2026_10_7-22_10__recovery_min_height_p1/height_reward.csv)只比较高度项。

新增family×pose×互斥phase实际transition统计：入口前、入口后0–2/2–5/5–10秒；raw、weighted dt和逐通道100Hz触限计数。
非零raw计数不冒称通用gate激活率，未进入阶段明确NO_TRANSITIONS；尚无真实运行的覆盖数据。
控制诊断仅来源及formal25/50/100评估启用，含R0完整轨迹；没有真实optimizer梯度探针。

提前停止声明：入口数相对来源减少>=2个环境连续两次完整检查；或来源同env无振荡而新候选连续两次出现新振荡。
振荡固定窗为首次入口后1–2秒，100Hz目标变化>=10rad/s、交替比例>=80%、同轮held限矩比例>=50%。
缺少窗口为UNKNOWN，不当作无振荡；失败计数遇正常检查清零。已认证R0两次退化沿用既有StandingRegression，不额外维护R0计数器。
这些是运行前固定的保护指标，不是已证实的根因或每5ms力矩认证。

## 未授权声明与验证

[spec](../configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/spec.json)，独立budget.json仍UNAUTHORIZED，used全零、attempts为空、session=null。
建议额度：source900秒/PPO0、smoke20/900秒、formal100/7200秒，共120更新/983040样本，chain含60秒清理上限9060秒。
保存25/50/75/100，完整评估25/50/100，不做100秒耐久，不继承smoke权重。smoke要求有效R0/DrawBack episode，而非已学会任务。

共享代码全CPU回归509 passed，冻结worker专项53 passed，git diff --check通过；具体结果见[verification](../isolated/recovery_min_height_p1_cpu_20261007_verified/verification.json)。
冻结worker实际导入新副本并核对每个module SHA；supervisor plan为READY_NEEDS_AUTH，cpu_valid=true、simulation/PPO/files_written=0。
预算SHA前后相同、计划output目录不存在。缺少当前session/GPU映射及新运行授权，不能描述为submit-ready。
测试涵盖真实评估函数、有限task_success终止、候选分类、新版本source证据放行、RNG/模式恢复、首入口/1000样本/时钟/episode隔离、跨rollout状态、一次性事件及旧Recovery/Motion回归。
CPU验证不是物理成功；未声称真实PhysX初始化、新训练覆盖或学习改善已验证。

## 本轮精确改动文件

- 新增 scripts/review_recovery_min_height.py、scripts/prepare_recovery_min_height.py、src/native_stand/recovery/min_height.py、tests/test_recovery_min_height.py。
- 修改 src/native_stand/recovery/{rising,domain,runtime,recipe,selection,task_protocol,validation}.py。
- 修改 src/native_stand/command_v6/train.py、domain/evidence.py、tools/{evaluate_checkpoint,preflight}.py。
- 新增本报告及configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/{spec,poses,budget,preparation_manifest}.json。
- 更新根README.md、STATUS.md、ARCHITECTURE.md、TOOL_INDEX.md，仅增加本轮准备说明。

保留其他worker已有dirty changes；AGENTS和最终计划未由本轮重写。历史runs、USD和外部项目保持只读。
