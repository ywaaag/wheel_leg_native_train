# Recovery仅轮均值有界：版本接口与三组PPO0迁移复验
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


2026-10-09用户同意执行。实现版本化distribution接口并完成独立三组复验；PPO/optimizer更新0，没有新checkpoint。此次证明固定seed104/已声明初态下旧两组未立即丢失，不证明训练成功或任意姿态泛化。

## 实际运行与消耗

新声明`configs/experiments/2026_10_9-10_50__recovery_b25_bounded_mean_threegroup_ppo0`；独立spec/budget/approval/authorization_receipt/poses/publication。新run同名，attempt a9a0c5dd6b9047799bb84e15a62ca1eb COMPLETED、evaluate1已结算，ledger150.157579秒，terminal149.788385秒；差额是清理。上限900秒，三组23秒/64env8scored，Swing提前tilt失败不能称完整23秒。GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda0共享，未停止其他进程。

来源认证RecoveryB25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。模型权重不变但action_distribution改变，明确不冒称行为保持的strict warmstart。新增声明`recovery_wheel_bounded_mean_gaussian_v1`：仅2/5 mean=tanh(rawMLPmean)，四腿mean/原std/普通Gaussian sample与log_prob/entropy/KL保持；环境clip/腿位置和轮速度scale/PD/限矩/reward/150D保持。

train/evaluate/play共用learning.model的版本选择，source_eval同样应用，不在某阶段偷偷使用原mean；export deterministic与训练mean一致。样本仍可能越界，不能称动作完全有界或零饱和。无sampletanh随机变量Jacobian，不能用rawMLPmean算实际Gaussian likelihood。

## 三组结果

|组|完整通过|实际mean重放最大误差|std来源误差|实际状态上预计轮目标随机std rad/s|
|---|---|---:|---:|---|
|Swing|0/8，无入口|7.15e-7|0|4.160/3.597|
|DrawBack|8/8完整10秒|3.58e-7|0|4.886/3.884|
|R0|8/8完整10秒|2.68e-7|0|4.886/3.884|

source原MLP输出与新模型之间wheelmean=tanh关系最大误差≤5.96e-8；腿输出不变。Swing峰高均值.231364、受控约.29875秒，原冻结策略仍tilt失败。CPU预测与实际state读回相符，但表中std是64point无RNG积分预计随机物理输出，不是本次确定性eval额外采样实测；下一训练必须读回真实ppo.act sampleclip/std。

三组JSON与input_captureNPZ均在新run；新离线review`isolated/recovery_bounded_mean_threegroup_review_20261009/review.json`绑定spec/terminal/raw/capture/sourcecheckpoint SHA，不复制大trajectory。旧baseline和报告只读。当前是迁移后的B25，不是新trainedbest，也未认证整个Swing课程。

## 验证及跨任务影响

专项3tests passed；最终冻结PORTABLE7 passed、schema/零写plan/来源actorcriticAdam严格初始化通过。测试覆盖版本冲突拒绝、mean/std/logprob/entropy/KL、原四腿不变、strict state_dict加载、optimizer无修改、真实JIT导出同输出。torch.jit.script弃用提示来自现有RSL导出API，无运行错误。

全回归692 passed、22 errors、2warnings。22errors全部来自Motion受限工程恢复证书fixture：明确保护learning.py与learning_distribution.py历史SHA不变。本轮新增Recovery可选分支改变这两个共享文件身份，该检查按设计阻断；未改其历史证书/测试来绕过。不启用action_distribution时原model分布路径保持，当前Motion冻结worker未改；但下一Motion新源码恢复证书仍需重新审查。这是实际跨任务接线阻塞，不能宣称全回归通过或无影响。若未来要求两任务源码证书完全独立，应明确抽离各任务model分布扩展的边界，不能在本次自动改证书或大重构。

## 下一步

此次旧两组固定seed完整通过，满足候选进入短训准备的前提。建议独立smoke10/formal最多25、10/25三组联合评估，从同一认证B25严格加载actor/critic/Adam，仅启用wheelmeanbounded这一动作分布变量，beta=.3/原reward/std/初态/control保持，来源/早期候选与旧能力退化保护保留。source重新评估必须按新分布，同一未变checkpoint不能借旧Gaussian证书作来源能力证明。

训练前应补CPU真实PPO更新ratio/梯度与distribution params读回验证，和smoke真实sample变化/限矩/入口事件证据。当前仅确认概率API与迁移，不足以预言学习；不得只因clip下降接受候选。Swing腿目标首步偏差未解决，不同时加入腿bias/对称/制动/改奖励。

本次没有发布/授权新训练spec或启动PPO；重试或短训均须新明确运行范围。保留原B25，所有旧能力结论以其原distribution协议绑定，不静默替换。

## 本轮改动

新增`src/native_stand/command_v6/domain/action_distribution.py`、`scripts/prepare_recovery_bounded_mean_probe.py`、`scripts/review_recovery_bounded_mean_probe.py`、`tests/test_recovery_bounded_mean_distribution.py`；修改`learning.py`、`learning_distribution.py`、`config.py`。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX、ARCHITECTURE与本报告；新声明/验证/run/review为证据。旧run/ledger/资产/checkpoint和其他dirty changes保留，未清理文件、未Gitcommit/push。
