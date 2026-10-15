# Motion31 512env直线与原地自转有界课程

## 用户授权与来源

用户明确新增2000次在线PPO，要求直线1.5/2.0m/s、自转1/1.5rad/s，允许晋级、TensorBoard。新额度含smoke≤5＋formal≤1995，失败尝试也占用；全链18h、2GiB，任一上限到即停，不自动重试/再开新链。

来源v3/update1600完整路径：
`runs/2026_10_14-21_23__motion31_posture_quality512_v3/formal/model_update_1600.pt`

SHA：`83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`。

前置确认：`runs/2026_10_15-09_12__motion31_u1600_three_seed_ppo0`，3评估seed×5命令×8scored env，120/120新绝对姿态协议通过，PPO0。不是3个训练seed；normal reset随机性有限，不称为广泛域随机化认证。源旧v3判定保持原样，新协议通过不能回写旧39/40结果。

## 冻结课程

1. L1p5：新±1.5m/s，保留0/±.5/±1。
2. L2：新±2m/s，保留以上全部。
3. Y1：新原地±1rad/s，保留0和全部已学直线端点。
4. Y1p5：新原地±1.5rad/s，保留全部直线和±1rad/s。

512env固定128 zero、192旧运动、192当前新端点（正反各96）。旧任务按配对轮转整数配额，实际槽位保存在spec/preparation，各阶段均精确512、正负均衡；不能提前采样未解锁端点。旧运动槽位逐阶段：L1p5四命令各48；L2六命令各32；Y1八命令各24；Y1p5十命令以配对20/19分配。该分配是本轮设计，不宣称最优。

同一formal进程持有Actor/Critic/Adam/std/RNG。每250全评当前全部命令、每命令8env，所有命令连续两次完整通过且间有真实PPO更新才晋级；source/smoke不解锁。通过后保存stage checkpoint及原始评估SHA引用，再创建下一档环境；global formal计数不重置。单stage最多1500、全formal最多1995；前级未学会则停止并报告能力边界，不靠预算推进。最后1995额外完整评估，未评checkpoint不能accepted。

## 配方不变项

v3奖励权重、原准备.5/加速1/保持25.5/回零1/停车2秒训练时相不变，高度.34，Actor31/Critic49、PPO/LR3e−5/固定std/归一化/物理与动作契约不变；不使用v4翻倍姿态奖励或取消停车方案。无域随机化、推力或控制补偿。

从1600完整恢复Actor/Critic/Adam/std/RNG，正向已学narrow mix=.75按命令保留；新端点mix=0起始宽核，负向原mix=0保留，数值refinement规则不变。新绝对姿态协议用pitch/roll绝对检查替代旧相对姿态作为精修资格；不因微弧度相对roll而阻断学习。yaw沿用已实现可分离tracking exp核与Huber误差，目标yaw进入同一command→Actor22–24→reward→score链；无“直线速度为0就消除yaw奖励”的门。yaw原地运动必须同时满足保持段水平速度均值≤.3m/s，不将绕圈称自转。

新任务分布下显式smoke4critic＋1actor、formal前5critic适应，仍恢复critic和Adam而非重新初始化，均占在线更新预算。smoke模型不作为formal来源；formal从冻结1600开始。

## 验收与保护

原30秒缓变独立评估：准备2/升速8/保持8/回零8/停车4；绝对保持max|pitch|≤.1、max|roll|≤.05；非零MAE≤.3m/s或rad/s、方向≥.95、gain .8–1.2、至少80%保持样本达到目标70%；zero水平p95≤.3及yaw≤.3；保留原contact/tilt/closure/height/clearance/geometry/saturation/parking条件。相对来源姿态仅诊断，不授予独立站立或高速认证。

宽容保护按stage学习进度：前300次普通表现只记录，固定检查同一旧任务连续3次“明显退化”才停止；跨命令不合并、缺失检查打断计数、UNKNOWN阻止晋级。runtime/nonfinite/闭链/控制权故障立即停止；普通episode严重姿态按原阈值reset并保留失败样本。新命令不会因尚未学会就立即终止整场。

## 自动化与存储

新增`motion_course.py`纯数据阶段/整数槽位/晋级/角色选优，`motion_course_requests.py`文件边界完整来源确认与恢复，`prepare_motion31_course.py`仅CPU发布。复用公共supervisor/monitor/runner/PPO/evaluator，不新增watcher或trainer。通过者按stage登记，不跨不同任务分布比较reward；来源只作fallback，未完成最后yaw阶段不把中间stage accepted当全课程accepted。

每update保留reward raw/weighted/dt、分cohort速度/姿态/接触、KL/entropy/LR、stage与global计数，TensorBoard只读bridge接现有6006。只保存固定里程碑紧凑评分轨迹和失败tail；按所有里程碑都已解锁13命令保守估算，整链未压缩+peak+reserve见storage_plan，硬上限2GiB，不复制源码树。

实际声明：`configs/experiments/2026_10_15-10_26__motion31_straight_yaw512_course/spec.json`。

证据：`artifacts/2026_10_15-10_26__motion31_course_launch/`（原始确认汇总、reward快照、CPU、零写plan、存储、提交握手）；运行：`runs/2026_10_15-10_26__motion31_straight_yaw512_course/`。

是否已提交以submission_handshake和STATUS为准；提交不代表formal已更新或新能力通过。后台负责评估/升级/预算/通知当前owner，worker一次握手后结束交互，不轮询。2000更新不保证拿下四个阶段，未完成则诚实报告阶段和失败原因，不自动加预算。

## 提交结果

已public supervisor detached提交，一次30秒握手确认worker440748、submitted/submission_verified=true，当前SOURCE_EVAL，formal_first_update_verified=false、started=false。这是来源阶段已提交，不冒称正式训练已有更新。终态通知绑定当前HAPI负责人191bacc3-e5c7-4b8f-ae3d-5677eada837b，不使用其他历史session。

CPU最终PORTABLE469通过、8跳过、4弃用警告；绑定定向38通过、完整Critic/Adam/LR3e−5/std形状核验、零写plan与完整提交READY。额外全状态CPU fixture核对Actor/Critic/Adam所有矩张量，未执行optimizer.step；yaw目标到Actor与Critic列、yaw奖励方向/无平移乘法门、4档切换/白名单/角色选优及预算不重置均通过fixture。AST静态编译与历史证据SHA检查通过。

TensorBoard `http://127.0.0.1:6006/` 一次HTTP200，选择 `2026_10_15-10_26__motion31_straight_yaw512_course` 的smoke/formal。具名reward各分项、cohort物理统计和course stage/global update随真实metrics写入；source阶段尚无PPO曲线是正常现象。桥接进程只读，不作为训练控制watcher。

精确改动清单、授权、来源确认、CPU、存储及启动回执在同名artifacts。未改历史模型/账本/协议、未提交Git、未运行其他外部仓库；本worker结束交互，不守候整场训练。
