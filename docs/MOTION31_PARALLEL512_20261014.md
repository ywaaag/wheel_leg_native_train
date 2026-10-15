# Motion31 512env /2000formal 运行声明

用户新增授权：尝试512个PPO并行环境，完成检查后启动最多2000次formal训练。此前64env/300次人工分块声明保留，不覆盖，不消费其旧账本。

新声明：`configs/experiments/2026_10_14-16_51__motion31_parallel512_l1_2000/spec.json`；新run同名；公开提交只用supervisor。显式执行profile `motion31_parallel512_2000_v1`，不会使旧64env声明隐式变成512。

来源仍为迁移Actor `isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt`，SHA256 `a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`。Actor31D、Motion Critic49D；来源没有Critic/Adam/RNG，因此第一链新建Motion Critic/Adam并显式seed初始化，Actor/std保持。前5次Critic warmup不算Actor更新，但计真实PPO update。

唯一训练配方变化是env64→512，整数槽位等比例扩大：zero128、+0.5/−0.5/+1/−1各96。128steps/env→65536transitions/update；每minibatch16384，仍4epochs/4minibatches。reward、LR3e−5、std、网络、advantage normalization、reset/时相和物理不变。batch扩大是否改善能力尚UNKNOWN，不与64env终点直接作等样本因果比较。

此次明确扩大运行额度：formal≤2000（131072000样本），smoke≤50另计（3276800样本），总online≤2050（134348800样本）；source_eval PPO0。整个链包括初始化/评估/保存在内≤18h，产物≤2GiB、终态预留128MiB，先到即停。每100formal完整评估五命令，每命令8scored/64simulated环境，不把512训练槽位套入64评估。持久化重复通过、故障和旧能力退化停止规则不变；不自动升±2或yaw，不重试，不追加预算。

训练environment、storage mask和samples/reward统计改为消费spec中的envs/steps，移除Motion路径8192常数；64默认及旧Recovery行为不变。评估构造器按实际envs生成相同比例槽位。smoke证书检查实际批次大小，不因mask65536误判为非法。

完整评分输入每个评估保存，source/smoke/选中通过/末次保留完整control/Actor/geometry，其余保留state、posture、geometry、world root velocity、command和有效窗口，限制重复大轨迹；真实故障保存有限GPU尾窗。选模与来源角色分开。

提交前资源快照：physicalGPU0 `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`，RTX4080，约310MiB占用；GPU1约18MiB；磁盘约57GiB可用；没有发现活动trainer。快照不证明未来资源持续可用，提交前公共health再核对。逻辑CUDA0，GPU0共享有显式授权，不切GPU、不停止其他任务。

CPU：PORTABLE 412passed/8skipped（包含512env真实CPU optimizer fixture）；配置/来源Actor/std/新Critic结构核验通过。公共supervisor `--check-submission` 为preflightPASS/submitREADY/health无finding，零仿真、零PPO、零写。工程检查不意味着新Motion能力通过。

授权登记用公共register_authorization，冻结current owner会话，new2050inclusive额度；原始spec SHA与登记后SHA分别在publication marker/authorization receipt。已请求既有终态通知，唯一chain owner负责at-most-once报告投递。Codex只做一次有界启动握手，不轮询训练。

下一步由后台依次source_eval→smoke50→formal最多2000→精确结算/报告/终态通知。submitted/SOURCE_EVAL不能称formal开始，更不能称能力通过。GUI、sim2sim及更高速度本轮不运行。

## 实际提交握手

公共supervisor已detached提交；chain attempt `38eb08c61cdd4633b24fc1f350d0a6e3`，workerPID699666；来源attempt `30b0a14830594fe3bb736b89b9657aec`，monitorPID699697。唯一30秒握手确认worker argv/spec/output/attempt/启动时间/HAPI及CUDA_VISIBLE_DEVICES=0匹配，source初始化已进入Isaac。阶段SOURCE_EVAL，formal_first_update_verified=false，不能报告为2000次formal已开始/完成。后台按照证书自动衔接，不需Codex守候。

完整CPU清单/身份/授权/握手入口：`artifacts/2026_10_14-16_51__motion31_parallel512_l1_2000/`。run的chain.log、chain_progress.json为后台进度，来源source_eval.log、后续smoke.log/formal.log各自记录阶段；终态completion_report.md/report_ready.json由owner生成。现有TensorBoard6006使用同名Motion分组；桥接器只读指标，不能控制trainer。

本轮没有停止其他进程，未改旧run/checkpoint/评估/账本，未提交Git。提交后不轮询，不等待整场训练。任何通知失败不视为训练故障，也不自动重发/续训。
