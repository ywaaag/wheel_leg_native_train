# Motion31前进优先晋级课程（2026-10-15）

## 用户目标与授权

用户明确同意先学会直线前进，不要求定点停车，授权2000次更新和晋级课程。目标调整与旧双向/yaw实验分开：本链不训练后退或yaw，不要求继承全部倒退能力。GPU0共享沿用用户授权，通知当前owner，TensorBoard沿用6006。不会停止其他任务或自动换GPU。

本链是新课程能力实验，不宣称已修复历史退化。离线检查支持取消不必要的新−1.5目标，但没有证明新课程必然收敛。

## 来源与预算

- source：`runs/2026_10_14-21_23__motion31_posture_quality512_v3/formal/model_update_1600.pt`
- SHA256：`83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`
- new spec：`configs/experiments/2026_10_15-16_56__motion31_forward512_course/spec.json`
- new run：`runs/2026_10_15-16_56__motion31_forward512_course`
- 新独立ledger：同spec目录`budget.json`，累计2000 online包含smoke5＋formal最多1995；512×128＝65536samples/update，总上限131,072,000samples。旧链消耗不改变、不挪用余额。
- 全链18h、formal16h、source/smoke各1h，先到额度停止；2GiB、单stage最多1500，不自动重试/额外续链。所有初始化、评估、smoke均计时。
- 物理GPU0 `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`→CUDA0，共享，不抢占。
- 完整恢复来源Actor/Critic/Adam/std/可恢复RNG和mix；新物理reset，CPU不能验证CUDA RNG的实际恢复，runtime按原机制验证。LR保持来源/spec/optimizer均3e−5。smoke4critic＋1actor，formal初始5critic计入额度，smoke模型不作为formal初始化。

## 冻结课程

来源+1.5已有完整8env通过证据，本链不重新训练已通过档位，直接新档+2→+3→+4。

|stage|命令|zero槽位|旧前进槽位|当前新档槽位|
|---|---|---:|---|---:|
|F2|0,+.5,+1,+1.5,+2|128|+.5/+1/+1.5各64|192|
|F3|0,+.5,+1,+1.5,+2,+3|128|四旧前进各48|192|
|F4|0,+.5,+1,+1.5,+2,+3,+4|128|五旧前进39/39/38/38/38|192|

固定整数槽位，reset按原训练机制分配，不随机追逐短期表现；不采样−1.5、其他后退或yaw；未解锁速度不出现。每250次formal评估当前全部命令、各8env，当前档及全部保留端点连续两次完整通过且有真实更新间隔才升级；同一PPO生命周期、预算不重置。各阶段accepted单独登记，只有F4通过可获得本链最终accepted，但仍非三seed最终认证。

## 奖励、接口与停车语义

原v3 reward公式/权重/dt/终止/归一化/PPO/std不变。mix按来源保留：+.5/+1仍.75 narrow，+1.5及新档初始wide；仅沿用证据门控渐进细化，不按update盲切。

Actor31、Critic49 motion_privileged49_v1、6D实体关节、legscale1.5/wheel100、physics/PD/policy1/5/10ms、40/5.5Nm、Plane与资产不变。保留原训练准备.5/升速1/保持25.5/回零1/停车2秒（受控30秒＋初始化）。本轮“不要求定点停车”通过评分边界实现，不同时修改训练时相和reward；学习平滑回零仍是辅助样本，后续若要取消必须另版说明。

新显式协议`motion31_forward_capability_v1`继承原绝对姿态与物理/跟踪窗口，只把parking门槛降为诊断，不改变旧protocol。zero仍水平速度p95≤.3m/s、yaw≤.3；非零保持MAE≤.3、direction≥.95、gain80–120%、≥80%样本达到70%目标。原最大pitch≤.1/roll≤.05和contact/closure/height等保持，短暂限矩按原门槛，不新增隐藏限矩。+4额外mean3.6–4.4m/s、连续3秒1秒滑动均值≥3.8。

评估仍30秒缓变完整窗口（准备2、升速8、保持8、回零8、停车4），保持/停车分开。不是急停、定点、后退或yaw认证。速度与姿态都必须有逐环境证据，不凭reward排名。

旧能力保护沿用适应300、每250固定检查、同一来源/已学命令3次明显退化才停止；缺证据阻止升级，不把普通新任务未学会当runtime fault。runtime故障立即停止。stagecap1500仍未通过或总1995/18h/2GiB到达则有界结算。

## 启动与证据复用

复用已结束10_26 source_eval的0,+.5,+1,+1.5四份来源JSON/trace SHA和原评分证据，原文件只读；在新candidate registry中显式记录derived_assessment及停车诊断化，新protocol不回写旧报告。仅新+2需要补评，source失败不阻断学习（runtime/身份异常例外）。smoke5仅工程接线，不附加完整能力评估。

公开supervisor source_eval→smoke→formal detached；一次有界握手后worker结束，后台monitor执行固定评估、晋级、账本结算、当前HAPI owner终态通知。提交成功不表示formal已更新或能力通过。

## 工程变更与CPU检查

新增`motion_forward_course.py`、`motion_forward_requests.py`、`prepare_motion31_forward.py`、`test_motion_forward_course.py`。在原course resolver/runner/runtime/evaluator/recipe/request/startup/storage模块增量分派新版本，旧双向/yaw版本及历史run不变。准确13个源码/测试文件及SHA见本链artifacts/implementation_manifest.json。

PORTABLE **486 passed、8 skipped、4 warnings**。覆盖槽位/白名单、两次证据升级、停车诊断不隐藏其他失败、显式recipe及旧默认兼容。源Actor/Critic/Adam结构和LR CPU恢复通过；zero-write plan/preflight PASS。source/smoke/formal存储估算分别约225/272/819MB，每阶段检查通过，可用约57GB；预计合计低于2GiB。新启动仍写reward_snapshot，不复制源码树。无Git提交。

状态及启动握手以新run/startup_handshake.json、chain_progress.json和最终completion_report.md为准。TensorBoard和启动receipt保存在同名artifacts。


## 单次提交握手

公共supervisor已detached提交，worker671774、chain attempt820b9fc254884d7faaa39f21ec164cfe；5秒握手`submitted=true/submission_verified=true/run_state=SOURCE_EVAL/formal_first_update_verified=false`，启动命令/output/spec/attempt/GPU0/session身份核验通过。此处“已提交”不等于formal首更新已验证。后台继续执行来源+2补评→smoke5→formal，普通能力未通过不阻止学习，接线/runtime错误会终止。

通知负责人：当前HAPI session `191bacc3-e5c7-4b8f-ae3d-5677eada837b`，原有owner终态hook开启，无额外watcher。TensorBoard `http://127.0.0.1:6006/`一次HTTP200，分组`2026_10_15-16_56__motion31_forward512_course`，既有只读metrics桥接smoke672051/formal672052；registration不是训练指标，真实曲线以新metrics出现为准。

握手和TensorBoard receipt在同名artifacts；最终入口为新run/completion_report.md。提交后本worker结束交互，不轮询日志、progress、PID或GPU，不等待整场训练。
