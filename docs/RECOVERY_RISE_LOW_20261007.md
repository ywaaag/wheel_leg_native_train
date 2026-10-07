# Recovery首次低位自主起身

2026-10-07。用户批准按RECOVERY_STANDING_PLAN执行，GPU0共享，不停止其他进程。
当前正式config/run根：`2026_10_7-16_18__recovery_rise_formal_from50`；
来源/smoke证据根：`2026_10_7-15_58__recovery_rise_low_from50`。
默认来源source50，SHA `1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。
运行结果只以对应manifest/terminal/ledger/raw评估为准，不从本声明推断训练已开始。

首次提交根`2026_10_7-15_51__recovery_rise_low_from50`在AppLauncher之前失败：
strict execution_source_root错误地拒绝合法冻结worker路径。原链保留FAILED收据，
ledger attempts为空、used全0，未发生模拟/PPO。当前源码增加冻结receipt验证：
spec SHA、声明源码根与全部Python模块SHA匹配才接受重定位；篡改fixture拒绝。
新目录记录pre_app_failure_predecessor和原ledger SHA；累计PPO上限仍为110，
不修改原链、原账本或其冻结代码。422项CPU回归通过，新source plan-only PASS，
health无finding；当前后台阶段以新run_state/握手与terminal记录为准。

15_58新链来源阶段已COMPLETED：23秒事件协议下低位初态8/8有效、fault0、
起身证书0/8；retained R0为8/8通过。smoke已观察实际3更新与actor参数变化；
其持久证书及formal首更新尚未在本段认证，不从准备/状态字符串推断学习成功。

上述为启动时记录。后续smoke实际10更新COMPLETED，低位仍0/8，R0为8/8，fault0；
链因证书reader读取completed_episodes而producer记录completed被误挡。
原metrics有550个完成episode、最长2.18秒。当前wiring reader修复并兼容旧字段，
stand_chain.correct_smoke_receipt仅允许此确切错误，在新目录写PASSED更正证书；
旧FAILED证书、run和ledger不修改。新spec仅改提交元数据，物理/奖励/窗口/PPO不变；
新ledger导入原source/smoke的exact IDs和使用量10，外部证书及证据spec均校验SHA，
要求可复用配方完全一致；控制/reward或证书篡改仍拒绝。
原FAILED证书继续阻止旧链重复formal；全局计数以unique attempt ID去重。
公开supervisor --formal-only只启动剩余100formal，从source50初始化，不重复smoke。
423 CPU passed、新formal plan PASS，正式first-update证据见新formal/handshake.json。

正式单次握手已确认实际1更新，identity_verified/started均true；attempt
`b6ae54f673d7480f93988c6511a79345`，trainer3359946/monitor3359944，GPU0/shared。
后台owner完成有界训练/评估/结算和当前session通知；此启动事实不是起身能力认证。

## 先行能力定位

PPO0 run `runs/2026_10_7-15_46__recovery_rise_source_locator`，exact attempt
`47c359f4e2c441178508704e1c6522d2`，COMPLETED，3项完成、missing0、实际PPO0。
CPU闭链求解生成0.349m/0.273m中间姿态；无控制被动沉降后均约0.17m，
8/8初始化被拒绝。不能把它们当作策略不会起身的证据，也不加入本轮训练。
已有family R1低位约0.171m：8/8初始化有效，无runtime fault；source抬到约0.23m后
因倾角终止。10秒standing gate仅定位诊断，不等于起身后的10秒验收。
旧knee-stop低位评估的500/1000/1500/2000候选最终约0.21m，未证明成功，
本轮不通过大规模候选扫描替换来源。

## 新任务契约

一个实际有效低位姿态family R1（课程R2），训练reset60%；旧R0 reset40%。
不自动晋级，reset占比不等于实际rollout样本占比。retain source actor/critic/Adam，
150D/六实体动作、plane、1/5/10ms和40/5.5Nm均保持；teacher不执行控制，
rising_task明确跳过STAND forward。历史autonomous/holding路径不变。

恢复lift权重2、upright .5；pitch/roll成本保持-4但恢复0.30–0.36m高度gate；
standing vertical/angular costs同样恢复高度gate。其他成本不调，success_once10、
failure_once-1，连续reward乘dt一次。BC .02、all channels、256、uniform_rollout。
这是新起身任务配方，不是单变量reward实验；lift不是标准PBRS。

训练自主达到现高度/水平/接触条件连续2秒成功，成功终止；11.5秒超时属于任务失败。
仍采用现60°倾角物理失败与真实安全保护；合法低位姿态本身未被此条件拒绝。
禁止接触按现recipe实际body名单，不声称任意机体接触即失败。

新独立评分：最多23秒观测第一episode，起身deadline11.5秒（FSM active age），
从第一个满足高度0.34–0.38m、水平入口与双轮接触的sample计完整10秒。
记录每环境post_rise_window_s、post_rise_observed_s、recovery_s、peak/gain；
保持窗口中高度和接触要求连续满足，水平/闭链/限幅按声明检查。
早终/缺初态/非有限不能通过，不重选后续窗口或拼接episode。
起身前倾角不套稳态小角门槛；记录全过程倾角和安全失败。
R0也按相同事件协议独立回归，并作为retained_evaluations；两次旧能力回归失败早停。
来源可以起身失败，但必须8个有效初态、无runtime fault、gate身份一致才允许smoke。
此新baseline规则不放宽旧站立baseline。

## 独立预算与入口

source_eval<=600s/PPO0 → smoke10/600s → formal<=100/3600s。
总110更新/901120样本；chain4860s含60s余量；eval25/50/100，durability关闭。
smoke要求实际completed_episode>=1且至少2秒，真实actor更新，末次低位评估无fault；
不要求尚未学会的起身成功来放行正式学习。两个保留任务和新任务的结果分开报告。
只有公共supervisor提交，current session、GPU0/shared和exact-ID ledger预约。
不能因budget存在便重提，不能加更新/重试/更难姿态或复用历史额度。

新增纯CPUrising评分及测试；精确CPU/plan、启动握手见STATUS和新run。
prepare_recovery_rise.py仅准备声明，使用集中时间命名，不运行AppLauncher。
本轮源码接线不迁移既有run快照；源码变化与实际学习收益分开。

## 本轮增量文件

- 新增：scripts/prepare_recovery_rise.py、src/native_stand/recovery/rising.py、
  tests/test_recovery_rising.py、本文及两个起身实验声明spec/poses、PPO0定位声明spec/poses。
- 修改：src/native_stand/recovery/{recipe.py,runtime.py,validation.py}；
  src/native_stand/command_v6/domain/evidence.py；command_v6/{train.py,stand_chain.py}；
  command_v6/tools/{preflight.py,evaluate_checkpoint.py,execution_identity.py,entrypoints.py}。
- 证书更正接线：command_v6/wiring.py，tools/health_check.py；只读导入匹配证据spec，
  外部更正证书读者验证不写原结果，phase owner生成新更正文件。
- 导航/交接：README.md、STATUS.md、ARCHITECTURE.md、TOOL_INDEX.md、
  docs/RECOVERY_STANDING_PLAN.md。
- 独立local budget、预约与执行快照由新run保存；旧checkpoint/raw评估/ledger未覆盖。
  其他重构的未提交修改保持原样，不归为本轮起身实现。
