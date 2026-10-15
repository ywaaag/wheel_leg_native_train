# Native 实现与接口：Codex 接线地图

显式Motion31晋级课程 `motion31_straight_yaw_progression_v1` 在既有Motion runner内执行：`motion_course`提供阶段白名单、512整数槽位、两次完整证据升级及stage-scoped选优；`motion_course_requests`核验三seed来源与全状态恢复；`motion_runner`保持同一PPO/Adam实例和全局预算，仅在固定评估后重建下一阶段环境。冻结spec不原位改写，active-stage view及stage checkpoint/evaluation引用单独持久化；原始v3配方/停车与Actor31/Critic49语义不变。最终accepted只对应最后yaw档，之前通过单独登记accepted_by_stage。见[课程声明](docs/MOTION31_STRAIGHT_YAW_COURSE_20261015.md)。

Motion31新训练（CPU交付、未运行）：显式 `student_motion31_training_v1` 由既有 `command_v6/train.py` 分派到Motion adapter；公开提交仍只有supervisor。单一target_xy → controlled-age schedule → Actor22–24 → pre-action command快照 → Motion reward，evaluator校验实际任务槽位。新 `motion_privileged49_v1` 为Actor31+18D具名Motion信息，不能用standing49 encoder。旧诊断及Recovery默认不启用，设计及证据边界见[Motion31方案](docs/MOTION31_TRAINING_DESIGN_20261014.md)。

v14学生站立链：纯standing_survival_reward→TrainingStudentEnv真实pre-reset状态→standing_survival_task.Clock（30秒truncated/物理terminated）→受控PPO存储。正常timeout从reset前Critic49输入bootstrap，raw reward不混入价值项。在线ring buffer与离线trace共用quality_features/quality_checks，固定末10秒world水平速度/姿态/几何评分；training.rank仅对v14分派联合质量选优，旧协议不变。身份、预算和原子产物仍消费共享工程接口，具体声明与验证见[接入记录](docs/STANDING_SURVIVAL_V14_INTEGRATION_20261014.md)。

本文件只维护结构和契约。命令见TOOL_INDEX，执行步骤见WORKFLOW，任务状态见STATUS。
当前实现是 `src/native_stand/`；旧isolated/source_snapshot只解释对应历史run。

## 主调用链

Motion可选posture_balance：domain.posture_geometry只处理显式世界坐标/旋转矩阵；
runtime.measure_posture_geometry读取真实hip pivot/wheel center并在GPU上聚合，
reward仅在显式配置时增加有界状态成本，不改动作/PD/观测/critic接口。
evaluation对显式姿态任务保存有效几何窗口，completion分别核验motion保留、
source-relative几何改善与两个真实更新检查点。assessment_commands与training_commands分开，
不以扩大验收清单改变B250训练分布。默认无此字段时沿用原路径。

独立CPU MuJoCo迁移诊断由scripts/validate_native_mujoco.py处理：只读参考MJCF与
native checkpoint，显式CAD/native坐标基，实际6关节q/qdot，复用native frame/history/
targets/PD域函数。wheel传动只做output-Nm→motor-ctrl单位换算，不做虚拟腿映射。
此诊断不替代CommandEnv训练/评估链，模型物理差异与parity限制写入独立manifest。

MuJoCo actor angular/gravity必须保留raw CAD frame，匹配native `_motion_state`：
up=-gravity_y、vx=-linear_z、vy=-linear_x、yaw=angular_y。CAD→upright只服务roll/
pitch/轮心几何，不转换actor输入。root速度采用COM语义，与安装版root_lin_vel_w一致。
sim2sim目录集中放独立验证与更正证据，不复制trainer，不修改参考MJCF。

Motion键盘播放复用共享tools.play：纯domain.keyboard_command处理按键/有界命令斜坡，
runtime.interactive_env只替换命令来源，沿用CommandEnv的动作、PD和物理实现。
推理前仅同步当前帧及历史最新帧的command通道，不额外移动history；GUI只消费
确定性actor，不创建PPO/ledger。兼容play_motion_keyboard.py不再加载旧isolated。
桌面事件与GPU映射在CLI边界处理；未实际运行GUI的CPU验证不构成物理认证。

```text
prepare CLI → config.validate / recipe.resolve / input identity
            → spec + independent budget + preparation manifest
supervisor  → preflight + submission_contract + health/resource check
            → stand_chain / launcher → monitor → train 或 evaluate_checkpoint
            → AppLauncher → runtime/configure → CommandEnv 或 RecoveryEnv
            → actor / installed RSL-RL PPO → evaluator → score / resolve_gate
            → curriculum / retention → candidate selection
            → child terminal → real exit → exact ledger → report_ready / notify
```

公开提交只有supervisor；phase启动/链worker/monitor是内部组件。准备器不提交、不授予运行权限。
不新增第二套PPO/trainer或临时watcher。共享代码升级不改变已运行任务的冻结副本。

## 模块职责

| 位置（native_stand/） | 单一职责 |
|---|---|
| `command_v6/config.py`、`domain/recipe.py` | spec schema、requested/effective解析、冲突拒绝与legacy披露 |
| `tools/preflight.py`、`domain/submission_contract.py`、`tools/health_check.py` | 配置/身份/前置证据与session/GPU/资源提交契约 |
| `tools/execution_identity.py` | 实际__file__/Python/模块SHA/依赖/PPO SHA；声明根和冻结执行根分开 |
| `ledger.py`、`domain/accounting.py` | exact-ID预留/charge/finalize与limit/actual/settled摘要 |
| `tools/experiment_preparation.py` | 有限JSON＋SHA核验原始/派生JSON字节发布；完整标记最后写，失败回滚 |
| `domain/recovery_course.py`、`tools/prepare_recovery_course.py` | 独立采样请求→sampling/assessment声明；旧姿态/初始化审核，Swing薄包装 |
| `recovery/sampling.py` | 唯一采样解析/概率编译与assessment保护范围；旧字段只读适配，混用拒绝 |
| `tools/register_authorization.py` | 新声明授权计划/显式登记，当前session、全臂预算与receipt；不提交 |
| `domain/action_std.py`、`tools/checkpoint_initialization.py` | scalar/log、output factor、物理尺度的裁剪前std；CPU strict/Adam保留/逐参数差异 |
| `domain/trace_schema.py`、`tools/compare_arms.py` | 版本化raw布局、结束后同源A/B一次比较 |
| `runtime/configure.py`、`runtime/control_readback.py` | 场景组装及物理/控制/资产readback |
| `runtime/env.py`、`domain/command_schedule.py` | CommandEnv命令、reset/history、目标/状态/reward时序 |
| `domain/reward.py`、`tracking_width.py` | 显式张量reward/宽度，dt乘一次；无文件/Isaac读取 |
| `learning.py`、`learning_distribution.py` | 训练/评估/播放共用网络与动作分布；算法来自安装版RSL-RL |
| `domain/gui_device.py` | GUI CUDA可见性→逻辑cuda:0及Kit物理renderer；兼容入口只转发 |
| `domain/command_sampling.py` | categorical/fixed_slots声明与冲突校验；名义配比/分配次数/transition数分开 |
| `tools/compare_motion.py`、`tools/submission_summary.py` | 身份绑定原始Motion比较、冻结授权/握手一次交付摘要；无进度查询 |
| `domain/evaluation_config.py`、`diagnostic_profiles.py` | scoring/schedule/storage分离；唯一storage_plan及legacy适配 |
| `tools/evaluate_checkpoint.py`、`evaluation_state.py` | source/候选/CLI/batch评估与异常恢复actor状态、临时设置、RNG |
| `domain/protocol.py`、`evidence.py` | raw逐环境score、gate、协议身份、完整性/缺测/冲突分类 |
| `domain/time_axis.py` | 半开索引、边界时间/post-step时间、恢复时钟及持续事件 |
| `tools/evaluation_loader.py` | registry引用→身份核验raw；摘要不能冒充完整轨迹 |
| `domain/task_curriculum.py` | 新任务晋级与已认证能力保护分开，统一连续失败计数 |
| `completion.py`、`domain/candidate_roles.py` | 完整候选、角色与认证排序；诊断并列项不授予accepted |
| `tools/validate_cpu.py`、`audit_terminal.py`、`audit_entrypoints.py` | 共享源码CPU验证、一次终态事件核验、历史引用/guard审计 |

## 物理与模型接口

25D实体关节frame＋五帧oldest-to-newest history125D，actor/critic共150D。
六通道left-first：左两主动腿位置、左轮速、右两主动腿位置、右轮速。
Plane摩擦.5/.5、恢复系数0；physics1ms/PD5ms/policy10ms；腿40Nm、轮5.5Nm。
具体尺度、offset、USD与初态由实验spec冻结；6D/150D相同不代表外部Gym模型兼容。
reset用新环境状态，不声称恢复完整PhysX。严格warmstart核对actor/critic/Adam参数映射、RNG与normalizer。

## Recovery适配

`recovery/runtime.py`在共享场景/PD/实体观测上实现初始化、FSM或RiseHold；不替换控制架构。
`task_protocol.py`拥有holding/rising身份、deadline、hold与batch时长；不能在工具里硬编码第二份。
`min_height.py`首入口确认后从下一interval收满1000样本，窗口完整性与certificate分别记录。
`recipe.py`组装环境/evaluator，`selection.py`认证排序，`effective.py`枚举每个声明叶子和legacy用途。
旧FSM/height command可能仍参与兼容存储/actor输入；被task protocol覆盖的阈值明确披露。
未核验consumer为待核验，不从字段名断言执行；条件reward激活由实际raw指标确认。
持久tensor为普通可变存储，支持inference collection→普通reset→下一rollout。

## 证据与版本边界

spec/asset/model/source/dependency/protocol身份分别保存；requested/effective/runtime读回分别可审计。
raw trace时间、恢复时间、初始化时长不能混算；评分slice显式半开，缺初始化时间为UNKNOWN。
policy100Hz的held torque不代表每5ms PD/每1ms物理子步审计。
registry只存压缩摘要和raw引用；loader核验路径/SHA/字段，诊断缺测不能补零。
多臂声明原位受限子目录发布，完整标记最后落盘；授权后新spec身份单独留receipt。
声明std倍率、初始化回读和训练后checkpoint std分开；随机动作std不等同实际torque变化。
协议scoring hash不依赖诊断保存选项；未知字段与矛盾结果在CPU阶段拒绝。
UNKNOWN/MISSING_EVIDENCE/普通任务失败/runtime fault/终态退出分别表达。
source/smoke真实事件证书由phase owner写，消费者只校验；来源通过不能代替更新后模型通过。
selected_diagnostics按指定update启用，不改变动作、RNG、分布缓存、梯度或optimizer。

模块历史修复和CPU结果在日期工程报告中；新会话按任务需要追溯，架构正文不堆叠PID、预算或旧“当前”。

## Recovery轮探索初始化

recovery/exploration.py是纯域初始化干预：校验显式声明，只在smoke/formal严格加载actor/critic与Adam后、首次act前，把distribution.std_param的2/5通道乘声明倍率；其他参数、Adam和RNG不变。source_eval继续使用未干预来源。
CLI prepare_recovery_wheel_std_ab复用experiment_preparation与集中命名，发布同源A/B未授权声明；review_recovery_takeoff复用身份raw loader、time_axis和原生水平纵向几何定义。均不新增trainer/monitor。

课程准备独立接收family权重请求。新声明分成三个契约：
`recovery.sampling`负责reset概率，`recovery.assessment`负责完整评估与旧能力保护范围，
`recovery.rising_task`仅负责起身deadline/保持/高度和entry验收。runtime reset与recipe retention
统一调用sampling模块，不读取评分声明中的比例。新旧契约同时出现拒绝；历史字段只在
sampling中的只读适配器解析，再剥离后交评分校验。历史spec/冻结代码不改写。
旧standing.pose_sampling只是兼容API；实际概率实现位于sampling。当前新契约用于单块课程，
后续多阶段若需不同质量，应显式扩展采样版本，不能借旧level字段覆盖。姿态库Infinity仅在身份核验的原始/派生字节中保留，
spec/budget仍要求有限JSON。完整标记是发布可用判据，不是断电时跨文件原子事务承诺。

Motion比较采用evaluation_components_v1侧栏身份，保留历史protocol SHA；不修改旧hash含义。
新summary与absolute gate共用time_axis.window_indices的policy_post_step_closed_v1；
原始trace闭区间切片在float64时间约定下复算。窗口/完整时长缺失时仅诊断，gain不得认证。

Recovery allocation_plan是config/preflight/prepare/effective公共槽位校验器；runtime原有固定family分配
继续复用，评估不采用训练env分组。coverage明确分开累计reset、有效transition和名义配额。
`domain.recovery_events`提供版本字段、第一episode事件及三类保持窗口；
`tools.review_recovery_events`负责结束态/registry/raw身份与输入文件，Swing脚本薄包装。
`tools.review_recovery_takeoff`复用事件核心，另作几何专项；不再在scripts复制核心实现。
`tools.test_resources`区分导入源码与历史项目资源；冻结CPU工具只执行已标PORTABLE的fixture。

## sim2sim语义与配对证据

纯域sim2sim_contract描述native_cad_com_v1；CAD actor坐标与upright几何报告隔离，COM/link origin区分。
trace_loader统一解析motion_policy_control_v1与motion_paired_state_v1的具名轴/组/validity；
历史缺声明的控制轨迹仅经显式已知生产者适配。共享audit_native_parity负责文件身份／静态对比，
不硬编码模型；MuJoCo实际控制仍只有validate_native_mujoco的headless/viewer循环。
paired_state profile通过storage_plan接真实Motion evaluator，记录pre actor输入及pre/post engine state，
与已有控制trace按policy index对齐；validity排除terminal/reset。预算是独立诊断schema，非native ledger。

Recovery PPO0输入采集：显式spec.input_capture由batch_plan校验，recipe执行每步一次actor调用并将pre-action150D/物理量及同transition pre-reset reward/control传给纯domain.input_capture.Recorder。Recorder无文件/Isaac/RNG/optimizer；tools.evaluate_checkpoint是NPZ/JSON写入与存储上限边界。诊断默认关闭，独立离线reader核验身份、输入重算与统计；解析clip不冒称随机探索实测。

Recovery轮mean辅助优化：schema由mean_auxiliary.validate校验；train在真实ppo.act前复制本rollout150D和family/entry/初始化mask，公共optimizer pre-step hook复用固定eligiblebatch，分母全部受控transition。PPO已裁剪→aux gradient→actor合成梯度再裁剪；不是minibatch数据，也不更新分布cache/RNG。wiring消费真实eligible/nonzero gradient证据才允许formal。mean/std/sample读回使用本次ppo.act已有分布，不额外采样。

存储边界：tools.storage_budget在preflight与locked ledger.reserve两次核验分区容量；
domain.evidence_summary递归剥离派生JSON中的轨迹数组，raw evaluation身份引用仍保留。
Motion reward.fields是reward输出与RolloutMetrics共享声明，weighted/raw字段一致性在CPU回归验证。
source_evidence严格只读证书由preflight/reserve/stand_chain/train共同消费；复用来源不创建虚构attempt，
不变更旧消耗。源码/effective/protocol不兼容即拒绝；没有新PPO算法或控制层。

Recovery可选support_record_reward：validation验证完整版本声明，纯recovery.support_record_proposal.RecordState维护每episode纪录；runtime在首次合法precontrol建立真实几何基准，在pre-reset reward加入有界纪录刷新奖，partial reset清除对应env状态。input_capture保存七列preQ/prebest/postQ/nextbest/reward/eligible/failed snapshot，reset不擦除刚发生transition的snapshot。该项不读文件、不改变150D/action/control/RNG；record未显式输入actor/critic属于公开任务状态风险，不冒称PBRS。

支撑纪录短训沿用公共course准备链，request严格support_record_reward版本且拒绝meanaux组合。train登记新增reward字段；只读PolicyReadback消费同一次ppo.act的已有分布/样本。wiring_certificate绑定实际metrics SHA，需finite非负且至少一次正纪录刷新奖励，再叠加既有episode/group事件要求。该证书只认证学习接线，不认证Swing成功。

发布校验verify_publication统一覆盖单臂/多臂，授权receipt解释显式可变字段；课程准备只构建一个文件包。
Recovery reward_fields.resolve/verify供runtime及RolloutMetrics消费，新增奖励不再维护trainer手写列表。
RecordState轻量计数进入task_metrics和wiring_certificate，reset/基准/范围预算分开；无额外actor调用。
存储估算来自storage_plan，audit_storage仅做显式排除范围内的历史盘点；actual_bytes在终态一次统计。

工程恢复边界：experiment_identity.sections隔离behavior/budget/storage；execution_identity记录全树与
任务子系统依赖两层SHA。prepare_engineering_recovery消费失败exact记录、补测及明确代码审核，
默认零写计划，可事务发布未授权工程恢复声明，不改历史终态或伪造smoke。
motion_recovery_certificate.v1分层绑定原FAILED、更新证明、原来源完整能力、轻补测及逐文件变更审核；
recovery_accounting是准备/校验/运行共用的累计预算计算，历史消耗不复制成新attempt。
preflight、wiring.completed_smoke、Ledger.reserve、supervisor formal-only、trainer/候选来源引用共同消费证书；
工程接线资格不冒充能力认证。发布与预约各有单次锁定，未知或行为相关变化拒绝。
全项目快照用于追溯，实际任务依赖与冻结模块用于执行校验，原来源只通过审核后的内存引用迁移。
update_proof在checkpoint保存后独立落盘；
通用checkpoint诊断准备器同时服务Motion/Recovery，batch继续策略由显式group定义。

显式rollout_probe是共享evaluate_batch下的独立Recovery工程诊断分支，domain声明固定2×64×128/PPO0，不冒充23秒能力评估。tools.frozen_rollout_probe使用现有PPO.act/process_env_step/compute_returns及真实RolloutStorage，从来源严格加载actor/critic/Adam；不调用update/optimizer.step，结束比较完整state_dict、恢复RNG和actor模式。CLI保存压缩NPZ+具名schema，capture≤64MiB，独立evaluate attempt由既有monitor结算。returns包含原PPO timeout bootstrap，advantage global normalization保持原实现。

Recovery显式action_distribution字段由domain.action_distribution严格校验；tools.model_factory按task选择recovery.learning，在该字段存在时选Recovery独立WheelBoundedMeanGaussianDistribution。MLP和std_param/state_dict/Adam坐标保持，distribution.mean只将2/5通道tanh，sample/log_prob/entropy/KL保持普通Gaussian坐标；deterministic与导出同mean，环境clip与物理targets不变。未启用字段使用原分布。Recovery分布实现不再写入Motion共享learning；共享调用边界的真实变化仍会使旧证书失效，须如实披露、不能改旧证书掩盖。

公共Recovery course request可显式action_distribution版本声明，prepare复用单一发布链，wiring绑定实际support_record_policy metrics SHA验证eligible Swing、两轮finiteboundedmean和至少一批未全clip样本；仍需reward/episode/group事件及原完整评估。真实PPO概率比率/更新测试验证mean重参数化API，与physics控制变化分开。

预览执行意图：domain.environment_mode只解析training/evaluation/preview，runtime.configure在创建前写入cfg，
Recovery runtime据此初始化training/holdout选择，runtime.execution_mode统一切换，不改变spec采样声明。
play与独立evaluator显式选择模式；evaluation_state恢复进入评估前模式。preview仅1env，不使用训练64slot。
GUI设备统一走domain.gui_device；CPU preview_plan绑定strict actor、分布声明/实现SHA及合法holdout。
runtime_cleanup按序尽力清理并保留primary exception，清理错误显式报告；Kit真实关闭行为仍需GUI证据。

分布隔离：command_v6.learning/learning_distribution保持Motion原实现；recovery.learning/learning_distribution
维护Recovery bounded-mean。tools.model_factory只按task路由，train/evaluate/play和CPU初始化共用它。
Recovery分布变化不再修改Motion共享实现；共享factory、实际运行模块仍属于执行依赖，变化不能免审核。
已有证书保留原SHA，失效须重新审核，不自动修饰历史证书。

可选evaluation_numeric_npz_v1只影响新证据存储：evaluation_storage独占NPZ、最后原子发布JSON摘要/SHA，
evaluation_loader验证sidecar后透明还原；公共terminal/event工具复用。训练行为和历史JSON默认不变。

recovery.dynamic_diagnostic目前仅纯CPU显式实体target/encode/measurement契约，无runtime调用；拒绝越动作包络和缺字段，不在env注入bias。诊断adapter尚未完成；未来若启用须具名actionorigin/override、substepcontact生产/validity与独立预算，不能混同RL自主策略。

Recovery可选`leg_center_auxiliary`由纯声明校验，LegCenterAuxiliary复用MeanAuxiliary optimizer hook与梯度统计；train只在明确smoke/formal启用，pre-step采集frame/family/control/clock/entry，post-step由pre-reset failure/fault过滤。每rollout冻结eligible batch，PPOclip→aux→actor reclip；不改变采样RNG、分布缓存或环境动作。wiring要求真实eligible及非零辅助梯度，默认/评估/播放关闭。

Recovery可选drawback_guidance由纯版本声明校验；runtime明确传入root wheel centers/native active q/height/mask/failure，纯模块返回镜像×目标位置×平滑高度退场reward。统一reward_fields和task_metrics/wiring绑定positive与mask证据；默认关闭，无新增obs/动作覆盖/actor切换，评估全轨迹用于实际误差分布。

纯recovery.regression_policy将退化counter结果和显式retained per-env证据分离：仅完整hold/contact-only失败可按声明抑制stop；accepted评分不变、UNKNOWN不放行。train记录requested/effective stop，默认保持原停止，声明准备及validation同版本核验。

Recovery controlled_ppo为显式默认关闭PPO适配，actor_valid为preaction训练metadata，storage bool随原minibatch索引，网络仍150D。valid全rollout normalization/actor-only loss，critic与GAE原时间轴；allinvalid actor grad None，未知extension拒绝。initialization_candidate仅文件边界校验并原样加载、不重施变换；recipe与谱系身份分开。Swing-only assessment空retained不触发旧能力保护，smoke仍要求真实初始化episode和validoptimizer读回；chain按预算墙钟扣除预留清理。

recovery.motion_handoff纯接口分别encode/decode两策略物理target，Motion独立native命令/history，输出超包络信息损失；有限settle+hold评分与旧Recovery autonomous gate独立。当前尚无runtime/public PPO0执行调用，不把旧stand_policy切换视为新B250接管。

显式motion_handoff PPO0请求由evaluate_checkpoint.batch_plan/evaluate_batch路由Recovery handoff_evaluator；HandoffEnv复用RecoveryEnv sharedPD/safety，仅独立策略physical decode、双history及handoff_clock。planner/online/offline消费handoff_protocol v2；JSON+NPZ atomic/存储限额由CLI负责，exception保留INCOMPLETE证据、monitor exact结算。Motion普通分支不变。


## 多策略第一阶段：可配置接管与receiver PPO

handoff_requests读取dual_frozen_handoff_v1固定22组或v2显式case ID/各模型spec SHA/seed/任意10ms整倍前缀/独立协议/storage cap。v1评分保持原定义，v2支持主组合或延长收稳诊断；diagnostic identity不得等同main accepted。handoff_protocol同时供planner/在线clock/offline score；source/readback与effective独立。v2 reset_yaw_v1只在新episode初始化追加world-yaw，记录root读回/seed；正常基线不扰动，切换处不写物理状态。

评估调用：public supervisor --evaluation-only →既有monitor → evaluate_checkpoint batch → handoff_evaluator → HandoffEnv共享RecoveryEnv/CommandEnv PD。按case原子保存8评分env；新增actor_valid/control owner/scoring phase/switch event/Recovery controlled clock，原始双frame/history/action/实体目标/torque保持。0初始化、1Recovery、2receiver控制；评分phase3表示已确认入口后的保持，控制者仍是receiver。

训练调用：同一public supervisor → stand_chain(source_eval/smoke/formal) → train.py可选receiver_training → receiver_recipe.environment → ReceiverEnv(HandoffEnv)。source=Motion B250 actor/critic/Adam/std，冻结B50与原Motion额外加载，不进optimizer。32Swing/B50前缀＋32原生正常零命令；requested receiver sample保存PPO action，不用冻结动作替换它；compose_training_action只生成真正执行动作。pre_action actor_valid仅receiver=true；初始化/冻结前缀false，受控失败末步true。ControlledPPO对valid样本全rollout归一化、actor loss/entropy/KL/clip与更新，all-invalid actor grad=None；完整GAE/critic timeline保留。storage另存phase/time/实际动作/left-first物理目标，不扩150D网络输入。critic读native_motion150，阶段/时间仅元数据，partial-observability别名风险明确声明，不能称新增critic privileged输入。

Motion reward使用B250冻结effective combined formula、zero retained width .04、height .40、dt.01一次与原terminal项；仅receiver受控样本reward生效，前缀reward0但GAE不拼接。无support-record/DrawBack位置奖励，无std/网络/PD变化。episode clock允许2秒收稳+入口.20秒后1000interval，不使用旧11.5秒deadline截断。

receiver_recipe.evaluate_actor真实重新运行Swing前缀/候选接管和正常零速两family，合并同env证书；另新episode候选同episode10s之后继续原Motion ±.5m/s各5s诊断。此处仅defer物理窗口结束以避免reset，评分仍是原1000interval；不得把驾驶诊断等同高速能力。isolated_evaluation恢复模式、family/config/RNG，清理异常保留primary exception。wiring smoke要求真实handoff/有效optimizer/episode结束/保存和身份，不要求能力先8/8。

Jump/Traverse/0.5s本体历史只是契约规划，代码声明在handoff_ownership.interface_contract，不自动替换旧模型。任务状态只在STATUS，路线图在PROJECT_MASTER_PLAN「多技能路线图细节」，命令只在TOOL_INDEX。

## multiskill_student_v1：完整起身学生（2026-10-11）

legacy150D路由不变；config/model_factory/preflight/evaluate_checkpoint/play仅在显式interface_version匹配时分派students模块，未知版本失败。students.interface纯函数生产22D frame、51帧valid历史和9D任务，共1182D Actor。历史按真实policy时间更新一次；reset仅清对应env，真实初始化帧可入历史但无监督标签。body角速度/重力为USD root本体轴；native线速度[-bodyZ,-bodyX,+bodyY]仅进入1191D Critic追加字段，不进Actor。reference六通道零，left-first legs0/1/3/4、wheels2/5；±1.5rad/±100rad/s目标先动作裁剪再真实USD关节限位，原PD/40、5.5Nm不变。

students.data边界读取具名pre-action trace、target_pre物理四腿＋两轮、实际post-execution control target，先物理还原再编码，拒绝学生包络不可表示标签。成功组合四阶段分层只用于采样，整条Recovery输入保持Recovery标识，不输入teacher ID/切换/未来标签；episode完整划分，失败只登记诊断。BC新MLP256/128/64 ELU，新Actor/Critic/Adam；六通道tanh mean＋普通未squash Gaussian likelihood，std对应腿.05rad/轮2rad/s，BC不拟合std或Critic。

公共PPO0：supervisor→既有monitor→evaluate_checkpoint batch→students.evaluator→StudentEnv(RecoveryEnv)。学生runtime重写观测/实体目标适配，复用原scene/PhysX/PD/机械保护，无冻结前缀或教师forward；ForbiddenTeacher哨兵使误调用明确失败。独立学生clock≤2.5s确认20interval入口，然后1000interval保持，旧组合及旧gate不改。每case保存100Hz pre/post/root/q/dq/输入/目标/力矩/owner/first-episode有效性及逐env评分；异常partial证据与terminal先于Isaac cleanup原子保存。模型模式、临时配置、RNG退出恢复。

students.model由train/eval/play模型工厂共享；students.ppo可装配真实ControlledPPO＋1191D critic storage，BC Actor加载、新Critic/empty PPO Adam、raw动作和自己的old log probability、pre-action mask、原GAE时间轴。独立demo loss不进on-policy storage。该装配已CPU验证，完整在线训练配方/reward及public formal证书尚未准备，不声称可以直接长训；当前发布声明仅PPO0。Jump/Traverse只占task字段，未实现技能控制或认证。

## MCU学生v2：独立小Actor

显式multiskill_mcu_v2路由到共享students模块，legacy150D与1182D v1保持原语义。
纯mcu_interface复用22D本体frame/物理解码，仅拼接当前9D命令/技能/跳跃标识，得到31D；不堆叠历史。
Actor31→128→64→32→6、ELU/tanh；Critic40→256→128→64→1，末9D训练特权不部署。
上一执行目标来自同一PD路径的限位后缓存，reset采用声明初始化目标；切换不改物理状态/缓存。
model_factory/config/preflight/evaluate/play/health均按显式版本分派。StudentEnv仍复用RecoveryEnv物理/安全，独立学生不调用教师。
在线reward尚未定义：requests/preflight禁止source_eval/smoke/formal，ppo.assemble也拒绝v2；零reward仅用于PPO0。
data直接重新消费带schema/SHA的原始pre-action轨迹；distill仅优化新Actor mean，critic/std不BC优化。
export封装仅Actor确定性mean为固定[1,31]→[1,6] ONNX，不包含Critic/std/Adam，使用ReferenceEvaluator与固定goldens验证。

## 同一Recovery学生task PPO recipe

student_training显式绑定student_recovery_ppo_bc_v1；输入仍multiskill_mcu_v2。公共prepare/config/preflight/supervisor/stand_chain/monitor/train.py保持owner/ledger，不新造launcher或日期trainer。students.training是公共train.py内的学生recipe适配器，消费共享ControlledPPO与RolloutStorage、TrainingStudentEnv（共享RecoveryEnv物理/PD）；不执行教师动作。source里的教师组合是单独冻结对照。

recovery_task纯显式post-state reward与Certificate在线累计，第一次入口后下一固定1000样本完整高度/姿态/接触/闭链/触限/速度证书；complete与passed分开。TrainingStudentEnv在_get_dones后、reset前留存reward和事件，_get_rewards消费该结果。Actor31D不加阶段；Critic40D实际消费年龄/入口/保持等9D特权。

ControlledPPO新增默认开启Actor开关和默认关闭梯度诊断，旧行为保持；本recipe前5update actor梯度None、固定log_std requires_grad false、BC完全不调用。无效actor样本不影响surrogate/entropy/归一化，critic/GAE原时间轴保留。
每阶段独立来源Actor、新Critic/Adam，smoke不接棒formal。阶段评估在完整rollout后另建同物理env，之后训练明确重建/reset，并使用新obs，不拼GAE。
train checkpoint绑定接口/recipe/dataset/asset/spec/source源码SHA；wiring消费真实非零reward、mask/warmup/actor step/reset/save-load，不消费起身通过前置。monitor/chain生成本recipe报告和exact-ID结算。

学生工程边界：StudentEnv/TrainingStudentEnv/HandoffEnv共用真实CommandEnv→RecoveryEnv构造及pre-reset _get_dones；
PORTABLE首步契约测试仅替换最低层Isaac物理数据，不替换共享环境或dones。学生训练reward/Certificate仍按原版本。
students.artifacts集中原子tensor/NPZ落盘与声明存储上限；training保存/清理二次错误不覆盖主异常，进入前RNG必恢复。
prepare_student_recovery_ppo是显式parent/source的配方包装，case_id选择并记录SHA/有效声明差异，来源/算法版本严格。
submission_preparation是公共validate_cpu的审阅包扩展；authorization template仍交公共register_authorization，
提交仍只supervisor/launcher/monitor，不新增worker。缓存复用是精确SHA收据引用，不能豁免源码变化。
watcher退役拒绝，legacy selector仅历史150D schema；历史freeze不迁移、不删除。


Recovery学生reward recipe新增显式student_recovery_ppo_failure_zero_v2，对应student_recovery_reward_failure_zero_v2；与multiskill_mcu_v2接口版本分开。仅失败事件奖励−1→0，终止/Certificate独立且不变。准备器--failure-event-zero声明→strict validate→PPO assemble/runtime显式reward_configuration→checkpoint recipe版本严格加载；旧v1默认−1保持。该候选目前未物理执行。


GUI外观由command_v6/tools/ground_visual.setup与camera_view统一提供，legacy play和students/play共同消费同一floor/light/camera设置；USD视觉mesh无碰撞，不进入物理或训练路径。学生保持独立Actor控制，外观复用不改变接口/previous target/评分。


student_recovery_ppo_lift_rate_v3沿failure-zero baseline只加入口前角速度成本：current post高度smoothstep(.20,.25)×clamp(relu(norm(bodyOmega[X,Z])−3)^2,0,9)，密度−.20，dt=.01一次。纯reward独立函数；Actor31D/Critic40D、Certificate终止/gate不变。追加成本raw/density/dt分列进入metric和selected rollout，不改变旧六项布局。history_diagnostic只提供CPU时序probe，不是已实现的新学生接口。


student_motion_probe_v1是学生评估声明版本，不更改31D/150D接口。students/handoff_probe定义严格PPO0请求与控制归属；StudentMotionProbeEnv继承共享HandoffEnv，前缀腿尺度显式1.5而legacy默认1.6保留；两者Motion为.5。学生输入由统一mcu encode生成，Motion frame/history由原motion_frame持续生成；students/handoff_rollout每interval只调用一个执行Actor，换控制者不reset，记录3学生/2Motion/0初始化。公共students evaluator/supervisor复用exact-ID/原子保存/monitor，baseline失败保留后续NOT_RUN，接管评分用原组合协议，救场不宣称独立学生能力。

学生PPO0 case的reset契约由students.requests.evaluation_recovery纯函数从声明family生成，public preflight先验证真实holdout采样，evaluator.environment在共享环境构造前安装并保存effective读回。此作用域仅评估，不改来源训练sampling/retention；训练路径仍按各recipe配置。

学生standing_rehearsal_v4复用公共train/ControlledPPO/TrainingStudentEnv，以固定32/32环境槽位采样Swing与原生normal。rehearsal.angular_reset纯函数声明native身体XZ速度扰动，仅在normal episode reset消费随机数。高度参考兼容在版本化reward内，不加Actor字段或隐藏控制；family统计按pre-action pose记录，选模Swing主协议与normal诊断分开。

Recovery站立教学复用students.distill的显式source-checkpoint接口：新BC Adam、新Critic，继承仅Actor；normal教师数据仅将Motion one-hot重编码Recovery，物理标签不变。standing_priority_recovery_v1五阶段50/12.5/12.5/12.5/12.5采样；reset_v2仅在normal内部划分首动作/下一19动作/保持，保持episode split。学生评估仍全程Recovery自身控制，无教师切换。

standing_mirror.py纯函数只生成离线镜像教学候选与elapsed_progress提案，不在运行时修改动作。镜像目标[e_hip=0,e_active=0]与原B250目标有差异，manifest保存原标签，normal仅改目标、previous执行缓存不伪造。Progress未来32D/41D仅CPU_PROPOSAL_NOT_RUNTIME，当前所有运行仍31D，旧接口规则保持。

站立continue-update50 v6在Recovery reward中增量实现Motion零速联合Gaussian与有界physical-q镜像成本：runtime传入post-physics/pre-reset四腿实际q，no actor input change/no action projection。原六项/证书/事件不变，training保存extra raw/weighted_density/dt及独立actual_q_mirror_abs_mean；弱约束不宣称严格动作或状态对称。prepare --motion-mirror核验实际update50 SHA与其自己parent spec，不改旧加载配方。

站立v7 `student_recovery_ppo_velocity_huber_from200_v7`沿v6共享runtime/ControlledPPO，仅替换零速反馈：−H×sum(smooth_l1([vx/.5,vy/.5,yaw/.3]))每秒，dt一次；不乘姿态U、不截平大误差。weak physical-q mirror和原任务项/证书保持。公共prepare --velocity-huber严格绑定update200及自身parent；新Critic/Adam，不恢复旧RNG。输入输出仍multiskill_mcu_v2，旧配方版本不变。

Recovery持续课程v1：task_manifest不可变授权、task_ledger累计与exact active spec；stand_chain完成并结算子run后调用students.course_io，仅通过公共supervisor提交下一块。course.py纯决策与有限停滞规则，course_runtime共享TrainingStudentEnv物理/PD、双教师原生历史与实体目标尺度、学生后缀Certificate；controlled_ppo显式critic_control_only默认关闭。resume.py完整训练状态，物理restart reset另记。学生31D无前缀/教师/阶段输入，辅助证书不等于独立Swing。旧入口与有限授权语义保留。

Recovery course dispatch以新子spec.execution_source_root构造subprocess PYTHONPATH，不能复用父spec路径；prepare从实际导入的bundle声明root，公共identity继续严格校验共享/冻结receipt。人工未启动首B恢复创建新task累计账本，旧task/失败子spec不可变；恢复入口拒绝已有物理attempt。

Recovery动态v10保留v9，只加首次入口后接触合力不足的有界成本（−.2分/秒，dt一次）；task_manifest.dynamic_recipe显式选择，缺字段仍为旧v9，未知版本拒绝。已结算故障恢复通过prepare的独立recover_failed_block入口发布新task并继承真实累计消耗；从该失败phase已评估的checkpoint加载Actor，新reward重新初始化Critic/Adam，后续同配方完整resume。course_runtime启用纯记录fault components（默认其他路径关闭），training在任何64环境触发保护时原子保存pre-reset具名证据，附加保存失败不覆盖主异常；不修改物理或初始化保护谓词。

students.play显式请求environment(autonomous_preview=True,envs=1)：跳过CourseStudentEnv及teacher_models，仍共享TrainingStudentEnv/PD和学生输入解码；只允许单学生、无teacher/handoff。课程训练/正式评估的默认False保持原行为。GUI选择family时只匹配独立student case，不把辅助student_suffix case改称独立成功；checkpoint仍严格绑定原spec/asset/recipe/interface和发布receipt。

Actor时间平滑A/B：students.temporal仅消费固定rollout观测与具名控制/episode/时间/入口/terminal元数据，纯mean双侧梯度，不修改分布缓存；ControlledPPO可选hook默认None。temporal_ab_io复用course公共发布、register与stand_chain owner，完整旧训练状态初始化须核准source phase receipt/旧冻结模块、共同新执行SHA及同reward/control/PPO；两臂均新smoke，普通continuation校验不放宽。A结算后owner仅首次提交B，B结算由temporal_review比较分组完整窗口与共同首2秒并停止。run_state的SOURCE_EVAL→FORMAL特例只接受stand_chain通过verify_continuation产生的版本化证据。

## 人工 Recovery 工作台（manual_experiment_v1）

steps.py提供相互独立的init-source/freeze/publish/validate/authorize/env/inspect/resume；manual.sh仅分派一次所选命令。step_runtime.py在声明指定bundle下调用公共prepare_block/授权登记及CPU续训核验，不另造trainer、monitor或物理控制器。人直接调用公共supervisor进行plan、资源检查和launch。旧workbench.py/prepare.sh/train.sh保留兼容，不作为推荐人工流程。

editable/src/native_stand是真实可编辑副本。初始化借用workbench.make_bundle增量安装manual_recovery_ppo_v1/reward_v1及continuation_contract；后续freeze复制editable，更新声明参数并计算逐模块及奖励SHA，不重拷共享src覆盖人工修改。共享src与活动冻结代码保持不变。奖励真源为editable中的manual_reward.py；根reward.py仅是旧入口模板。

runtime_support校验settings/reward/session/GPU/exact-ID并有限结算。budget(resume=False)保留smoke12，resume=True为smoke0且重新分配来源/formal墙钟。同配方resume复用原bundle的身份，不复制当前editable；continuation_contract核验已结算formal、完整checkpoint、原公共smoke证书、奖励和源码SHA，再由既有course_requests.verify_continuation/学生restore执行真实状态恢复。没有放宽公共continuation检查或替换smoke证据。新配方重新建Critic/Adam/RNG，同配方保留，进程重启PhysX真实reset单独记录。

swing/standing/bridge继续复用slot_groups和CourseStudentEnv；零前缀smoke不要求teacher handoff，正前缀保持真实交接证据要求。冻结测试明确指定snapshot pythonpath，不得回到共享src或静默skip人工测试。单块完成只结算STOP，无自动新实验。

models/catalog.json记录固定副本身份，不是实时best指针。配置与执行源码按实验冻结；人工工作区可并行修改，不能修改正在执行的副本。GUI继续使用公共play/StudentEnv的网格、灯光和视角。具体文件导航见人工手册，命令只维护TOOL_INDEX。

## 0.34m站立对称专项

students/standing.py为纯任务约束、物理镜像测量、排序/停滞/有限回退决策；standing_io.py沿course_io公共prepare/授权及既有stand_chain owner结算后提交有限子块，不新增trainer/watchers。standing_training显式task版本绑定normal64、0.34m目标、固定镜像误差及32条件认证，普通连续Swing课程默认不变。

reward v11继承v7，仅改slot0为目标0.34m Gaussian以及弱镜像为无封顶Huber；新配方新Critic/Adam，正常resume全状态。StudentEnv增加显式student_command_height参数，默认.40保持旧31D语义；v11从recipe读.34进入命令槽位，不输入实际高度给Actor。

StandingCertificate与standing_certificate.score消费同一首20＋1000interval窗口，除原物理项增加目标高度与物理腿镜像均值/P95；只有联合通过才success_once。normal专项accepted与完整Swingaccepted分开。评估保存control/actor实际目标证据，不将截断窗口或姿态变齐当成通过。

fault_evidence.capture支持具名全关节q/dq/limits/root/实际目标/力矩扩展，RecoveryEnv仅显式故障诊断开关启用时采集，全部post-physics/pre-reset；初始化/教师样本mask与机械保护不改。共享代码新版本不用于解释旧A/B行为，历史测试从实际冻结执行副本验证旧SHA，严格拒绝新共享源码冒用旧A/B共同执行SHA。

## 旧Motion0.34m持续适配与并行隔离

manual_train/motion/standing034_engine_v2为独立、版本绑定的公共代码副本，保持legacy150D及原Motion模型/动作/PD/USD。motion_course.domain是纯声明、联合候选汇总与决策；io负责SHA、发布、授权及账本，由现有stand_chain在正常终态首次提交下一有限子块。父任务累计更新null，子账本有界。初始化/物理重置与网络/Adam/RNG完整恢复分别记录，不声称恢复PhysX瞬间。

新增motion_course显式请求允许0.34m，旧声明高度校验保持原行为；新gate_identity=motion_standing034_v1消费.32–.36m高度带、90%保持样本在带内及每个保持样本≥.30m，旧协议不回填。26/19/19固定槽位训练0/+2/-2，actual transition分布由原指标保存。30秒缓变评估中10–20秒为固定保持窗，原Motion速度/姿态/接触/限矩阈值保留，不冒充Recovery较严格证书。

STOP是原训练循环模块级信号状态；新检查不得把它变成main局部变量。入口注入异常CPU测试实际执行main/ledger/finally，保证原异常和结算落盘。新接口只改变显式task路径，物理目标仍仅解码一次。

Recovery v11的training_phase_metrics仅对formal24第一episode汇总，smoke8只作工程及行为记录；formal组数、成功证书不放宽。Motion与Recovery的执行代码及账本独立，修复原FAILED生成新声明，保留旧冻结源码和实际消耗。

## Motion实际双腿对称专项v3

独立公共bundle standing034_symmetry_engine_v3，仅motion_course v2显式启用joint_mirror reward及motion_standing034_symmetry_v2联合gate；旧reward及gate缺该字段时保持原语义。post-physics/pre-reset实际四腿q按[left_hip+right_hip,left_active-right_active]计算Huber，纯domain不读文件/runtime。evaluator消费具名control schema在固定10–20s窗口计算实际误差MAE/P95，invalid或缺测不通过；几何与目标误差另列诊断。

64zero，高度命令.34，legacy150D/原动作/物理保持。首次新reward Actor/std继承、Critic/Adam/RNG独立；后续同配方续块恢复完整状态。warmup5仅首次。联合站稳与mirror证书独立于旧驾驶、Recovery证书。共享src及活动Recovery冻结代码不因本专项改变。

Motion专项v4修复wheel-envelope转换的optimizer初始化边界：使用state.get检索，新Adam或Critic-only warmup后尚无moment的参数保持无state；已有step/exp_avg/exp_avg_sq按原坐标转换，缺失或shape错误在任何参数修改前拒绝。转换不制造Adam step、不先跑伪更新，来源权重及分布保持。v3已失败冻结副本只读，新声明绑定v4，活动Recovery/shared源码未改。

## Motion关节与轮位对齐v5

motion_standing034_alignment_course_v3/gate alignment_v3独立bundle复用公共MotionCommandEnv、PPO、supervisor。joint_mirror版本native_joint_support_alignment_v2要求runtime给postphysics实际四腿q和measure_posture_geometry；纯alignment模块分别返回hip/active/worst/wheel成本与density。fields动态注册四项，RolloutMetrics实际消费并记录，不仅spec占位。无效heading禁止伪造0。

evaluator同时保存具名native_posture_geometry_v1，fixed1000hold samples计算轮差MAE/P95，原joint_mirror分别计算两个关节MAE/P95；publicabsolute gate增量检查轮位、.36保持峰高、显式zero_mean_abs_vx_max=.05。主gate完整物理+三对齐项；选模先物理/零速可用，再最差归一化偏差。schema未知字段拒绝，sharedsrc与旧v4frozen不改。新reward首块Critic/Adam独立；source/smoke/formal从声明来源分别初始化，不继承smoke末尾。首块完成owner停止复盘，不续下一块。

Motion frame25_distilled_v1为独立离线Actor接口，25/128/64/32/6ELU/linear，legacy25Dframe字段保留、125Dhistory删除。teacherquery使用完整legacy输入，学生只currentframe；数据pre-actionq/dq/previousaction对应实际保存输入，heightcounterfactual显式记录。当前仅CPU训练、TorchScript/ONNXreference输出；未注册公共model/evaluator运行，因此旧legacy150D/31D/1182D路径严格保持，不能按Tensor维度自动猜版本。

Motion25D物理评估接线为独立publicbundle frame25_evaluation_20261013/engine。frame25_probe显式绑定version/studentcheckpoint/manifestSHA/10case矩阵/项目根/资源输出预算；公共checkpoint_input仅对显式绑定25D学生接受严格Sequentialstate及teacher/datasetmetadata，legacy输入检验保持。Frame25Actor只读obs.policy25，不使用obs.history；教师原构造/150D自身分布。evaluate_batch每条件构造对应独立冻结Actor，CaptureActor记录实际preframe25/mean6，不替换行为。两策略每case单独控制，没有student失败后teacher救场。共享CommandEnv/scale/PD/history/物理保持，64simenv/8scoreenv。在线训练请求明确CPU拒绝，未定义reward/critic不放行PPO。

Motion对齐更新诊断采用独立公共bundle（alignment_update_diagnostic_20261013），有效奖励参数显式进入spec.reward.joint_mirror.terms；trainer在选定rollout收集实际成本与reward，在真实PPO更新前后观察同批输入目标，保留原storage/GAE/分布与RNG。成本相关不等于因果或分项梯度。公共supervisor与原owner负责一次有限块，不自动续块；旧v5和共享src保持原样。

Motion运动筛选复测使用strongest034_recheck_20261013独立public bundle，motion_recheck版本严格绑定同一模型七命令、.34m、64/8布局与PPO0，显式project_root分派；未知字段/非零训练拒绝，原Motion物理不变。结果使用具名vx指标，hold_mean_abs_error不能通用视为前向误差。

25D实际0.34教学由frame25_actual034_distillation_20261013/data.py消费具名控制schema与实际pre-action capture，物理目标重新编码学生坐标；distill.py完整episode分割并均衡命令/阶段/episode，不使用历史或teacherquery。旧frame25输入契约保留，新checkpoint角色MotionFrame25Student由独立probe版本识别并校验dataset/manifest/教师SHA，评估共享CommandEnv/PD。

25D学生在线PPO由frame25_ppo_preparation_20261013独立public bundle按frame25_training recipe分派；物理legacy适配保留，但Actor严格只读policy25、Critic真实读取新增frame25_critic34。原reward/CommandEnv/共享train/ControlledPPO/stand_chain不复制成第二trainer。BC权重只映射参数名加载Actor，新Critic/Adam/RNG；计时器只供Critic、不发成功奖，checkpoint绑定新接口/recipe/数据/资产/源码。旧无flag路径保留。

## 共享源码与提交凭证（2026-10-13）

新公共链直接执行src，记录identity.json中的相对路径SHA、Git/dirty及外部PPO身份；阶段引用链身份，仅有变化时保存差异。配置归档目录source_snapshot仅含spec.json，不再含执行代码。未归档dirty内容不能保证字节级复现。

preflight产出进程内Approval；ledger在锁内复核配置、模型、资产、前置证据及预算，持久化submission_receipt_v1。runtime消费该exact attempt的凭证，不重复审查整条祖先链；运行源码变化另行记录。终态报告读取已记录身份，丰富报告失败时保守输出缺失证据摘要，不能补造accepted。历史证据只读；旧validate_frozen_cpu入口已移除。

## 工程精简第二批（2026-10-14）

`tools.model_adapter.ModelAdapter`是checkpoint结构读取/strict state加载边界：describe保留原参数名、显式interface、Critic/Adam/RNG是否存在；load对照实际构造网络检查完整names/shape/finite。actor-only BC不再因health硬编码Critic/update元数据而无法读取，是否允许初始化仍由recipe及前置校验决定。

`domain.execution_limits.ExecutionLimits`从预算声明解析phase updates/samples/wall；null只用于有正更新上限的smoke/formal。学生validate_instance将source SHA、cadence、capture与storage视为实例字段，算法/reward/初始化仍严格匹配版本。历史模板保留原默认值和实际实验语义，不用于隐式扩大新授权。

`tools.artifact_io`统一原子checkpoint/NPZ；`domain.checkpoint_policy`计算保留计划，`tools.checkpoint_lifecycle`在真实owner及ledger锁内执行显式新策略，所有来源、评估与选择引用优先保留。无声明即不清理；已结束历史attempt禁止应用。monitor可按声明轮转子进程日志；报告和数值轨迹继续使用现有摘要/NPZ接口，不新建保存框架。

## 精简复查补丁（2026-10-14）

chain_report通过evidence_summary.ledger_summary保留账本计数与receipt路径/SHA，原始完整凭证仍在ledger；不重复把requested/effective配置写进终态报告。
checkpoint_lifecycle使用inventory的removal_pending跨unlink/原子inventory更新记录中断；只有当前owned attempt可恢复，原始缺证据仍fail closed。
optimizer_capture在两个trainer的真实PPO调用前执行，声明由artifact_policy验证、storage_budget计入；默认不运行。
prepare_student_validation不再固定历史资产模板，显式父spec及source models/manifest经过SHA绑定后构建PPO0声明，教师按case identity匹配。

## 架构精简设计约束（当前有效，2026-10-14 自 plan.md 迁入）

plan.md 的实施清单已完成并归档；本节是其中仍生效的设计正文，与上文「工程精简第二批」「精简复查补丁」按同一主题合并阅读。

**身份记录，不做源码字节归档。** 不保存不可变源码包，不建 CAS 或硬链接物化。每实验只记录 requested/effective 配置、
checkpoint 来源身份、实际模块路径、源码摘要、外部算法与依赖版本、命令；检测到变化时追加一条简短 phase 差异记录。
支持追溯声明与版本差异，**不保证之后逐字节重放**：未提交的 dirty 源码只有 hash 无法重建；正式任务期间避免修改其相关
执行模块，跨版本结果不得自动宣称严格同代码对照，未记录的变化标 UNKNOWN。

**校验按三个时刻收敛。**
1. **准备**：轻量零写 plan —— 配置 schema、未知字段、网络 shape、动作单位/顺序、资源请求与额度语义；需要读
   checkpoint 时一次读取缓存。提交相关字段显式分开：`config_valid` / `resource_ready` / `authorized` / `prerequisites_ready`。
2. **提交/预约**：一个原子边界 —— 创建一次 submission receipt（spec ID、source checkpoint SHA、asset ID、source
   identity ID、协议 ID、GPU UUID/逻辑映射/共享授权、session、预算、exact attempt），锁内再次核对文件未改变且未重复预约。
   trainer 启动后只核验这份 receipt 与实际读回，不重新遍历证书祖先。`reserve` 的锁内 TOCTOU 检查不得因去重取消。
3. **收尾/复盘**：历史只读 —— 终态 + 已结算 ledger + checkpoint inventory + raw evaluation 引用即可生成报告，
   不依赖当前 src、当前全局健康状态或新授权。原证据缺失/损坏标 MISSING/INVALID，仍可出解释性报告但不赋 accepted。

**硬门槛与告警的分界。** 仍拒绝：输入/动作版本不兼容、资产或 checkpoint 拿错、关键输入损坏、非有限值或控制权故障、
重复预算消费、非法资源、评估 window 或模型绑定不完整。降级为告警：当前工作树与旧 run 不同、无关模块变化、报告格式
不同、历史文档链接失效、通知失败（通知故障不改变训练终态，报告故障不阻止终态摘要产生）。

**复用边界。** `supervisor`（公开请求）、`launcher`（创建进程）、`monitor`（owned child 退出/预算）、`stand_chain`
（阶段顺序）职责不同，不为“一个入口”合并成巨型文件。只共享确实跨 Motion/Recovery/学生使用的部分：发布 fresh 目录、
checkpoint 元数据 reader、执行 receipt、预算记账、trace 加载与字段 schema、终态事件写入。允许 task-local
preparer/reviewer，不要求每个辅助动作再套一层公共 CLI。

**数据保存与预算。** raw 数值轨迹一份压缩 NPZ + 具名 schema；JSON 只存逐 env 摘要、协议与轨迹路径/SHA，不重复嵌入
raw 或完整候选对象（legacy 格式 reader 保留）。保留策略：source/accepted/stage passed/best evaluated/latest 保留；
普通中间 checkpoint 按 spec 保留最近 K 及里程碑；optimizer capture 默认关闭且只指定 update；失败尾窗单独上限。
容量估计不是锁；在线默认不自动删除其他 run，清理由显式保护清单 + 用户授权执行，旧物理结果不重评分为新协议通过。

**源码/CPU 验证零复制。** `stand_chain` worker 直接使用共享 src；`validate_cpu` 是普通 CPU 验证入口（默认在当前 src
执行，保存测试名称、源码身份、解释器与结果摘要），旧的“冻结验证”命名与入口已移除，调用统一迁移。

**仍未执行项（边界，不得写成已完成）。** 存量文件迁移/GC 与精确可回收磁盘量未执行（本设计不授权存量删除）；
日期型人工 prepare 变体尚未统一（涉已冻结独立网络，需单独迁移设计，不改原证据）；全部模型格式统一构造仅部分完成
（25D 手工 Actor / 34D Critic 仍独立构造，不开放按 shape 推断）；历史能力集成测试仅部分转为小 fixture
（PORTABLE 入口已隔离历史数据，仍有 22 项历史证书 fixture 行为 SHA 冲突未批准）；旧日期脚本的全调用审计未完成
（只删已迁移调用且已有替代的入口）；手工工作台的独立可编辑引擎不迁回共享 src；旧 Motion 恢复证书涉及的未批准
runtime/configure.py 变化保留严格拒绝；新物理实验、训练配方变量与实际物理能力均未执行或认证。

## 与同事流水线对齐的 PPO 选项契约（自 docs/COLLEAGUE_ALIGNMENT.md 迁入，2026-10-14）

本项目沿用同事已验证流水线的**过程保护**，同时保留 native 闭链物理契约。下列选项均**默认关闭**，
只在新的实验 spec 中显式启用；历史 spec 与 Recovery 行为不受影响（已核对实现：`train.py`、`config.py`）。

| 选项 | 语义 | 记录位置 |
|---|---|---|
| `ppo.critic_warmup_updates: N` | 前 N 次 PPO update 冻结 actor 参数，让 critic 先拟合新的回报分布 | `progress.json` 的 active interval 与 release update |
| `ppo.clear_adam_first_moment: true` | 严格恢复 actor/critic 之后显式清零 Adam `exp_avg`，保留 `exp_avg_sq` | `progress["optimizer_initial"]` 记录被清零张量数 |

命令保留门由既有 `TaskProgression` 与 `task_confirmations.jsonl` 承担：每次完整确认检查零命令站立，
确认到回退即停止该 run。逐命令证据由 `RolloutMetrics.task_metrics` 与 `command_sample_counts` 保留，
不依赖全局 reward 曲线。

**明确不复用**：同事项目的虚拟腿映射、残差动作控制器、轮矩上限、reward 权重与资产相关命令语义。
native 训练继续使用 25D 帧 + 125D 历史、物理六路动作、Plane 场景、1/5/10 ms 时序与 40/5.5 Nm 上限；
同事源码只读。
