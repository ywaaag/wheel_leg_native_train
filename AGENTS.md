# Codex 执行约束

本项目 `/home/kellen/wheel_leg_native_train`。以正确性、可追溯性和最小变更为先；中文简洁交付。

## 最短阅读链

1. 本文件：授权和不可变边界。
2. `README.md`：导航；`STATUS.md`：选择本次 Motion 或 Recovery 的证据入口。
3. 当前任务的 spec、ledger、manifest、冻结代码、terminal、原始 evaluation。
4. 按任务需要读 `TOOL_INDEX.md`（命令）、`WORKFLOW.md`（步骤）或 `ARCHITECTURE.md`（接线）。

设计/改变 reward、课程、选模或验收前读 `TRAINING_EXPERIENCE_REUSE.md`。
只有自主起身任务需要读 `docs/RECOVERY_STANDING_PLAN.md`。日期报告按证据需要读取，不作为必读链。
Markdown状态是导航快照；run原始证据优先。当前源码描述下一次执行，不解释旧run行为。

## 授权与文件边界

- 仅编辑本项目；保留dirty changes，不reset/clean。外部同事项目、Fudan、sim2sim、wheel_leg_training只读。
- 旧run/checkpoint/raw evaluation/spec/ledger和活动任务的冻结代码只读；不停止或改动其他任务。
- CPU/文档工作不授予仿真、GUI、采样、PPO、通知或续训权限。PPO0也是仿真，仍需明确授权。
- 新配方/课程/gate使用新spec、新run、独立ledger；exact-ID预留和结算，保留历史实际消耗。
- 旧授权、余额、已通过smoke、commit和终态通知均不能授权新运行。状态不明先核验，不重复提交。
- 物理GPU、UUID、逻辑CUDA映射和共享授权显式记录；不自动换GPU或抢占其他任务。
- 通知须有明确授权和实际负责人目标。接收事件不表示任务归属或接管授权。

## 冻结接口与代码规则

legacy150D保持25D frame＋5帧oldest-to-newest history；新版学生仅按显式版本 `multiskill_student_v1`／`multiskill_mcu_v2` 的固定字段/维数/尺度分派，不接受任意接口漂移。6D left-first实体腿位置/轮速目标；
`multiskill_mcu_v2`的`standing_privileged49_v1`仅由v13/v14显式声明启用：Actor仍31D，Critic49D；旧默认40D不变，不凭输入shape推断版本。
迁移Motion的`student_motion31_validation_v1`只读PPO0诊断可显式复用同一49D输入布局；不加载/训练Critic、不凭shape推断版本，不改变旧默认。新Motion训练仅由 `student_motion31_training_v1` + `motion_privileged49_v1` 启用非零命令，不能混用站立49D语义；旧Recovery及诊断接线保持。CPU准备不授权仿真或PPO，分块续训仍需新审批；仅新显式 `motion31_parallel512_2000_v1` 按用户2026-10-14新授权允许512env首级最多2000formal、smoke50另计、18h/2GiB，不自动升档/续链，不改变旧64env限制。
Plane；physics/PD/policy为1/5/10ms；腿/轮40/5.5Nm。各实验动作尺度等以冻结spec为准。
训练、评估、播放共享CommandEnv；不加虚拟腿映射、LQR、补偿、static trim、隐藏控制或限矩增量。
纯domain只接收显式数据，不读文件/env/Isaac状态；CLI负责身份与文件读写。
AppLauncher先于Isaac runtime导入；资产模块根在依赖导入前核验并设置。

评估配置拆成scoring/schedule/storage；requested/effective/runtime读回分开。
缺字段或UNKNOWN不能通过gate/晋级；提前失败不缩短要求窗口。完整窗口与证书通过分别记录。
评估setup/reset/清理异常仍恢复actor模式、临时状态和RNG；清理错误不覆盖原始错误。
诊断默认关闭，只在显式更新启用，不改变采样RNG、分布缓存、梯度或optimizer。
Motion31准备及每次runtime启动须在AppLauncher前保存小型`reward_snapshot.json`：实际公式源码SHA、spec/source身份、权重、dt、误差曲线/导数与饱和风险；不复制整个源码树。TensorBoard保留具名raw、weighted density、dt contribution及分命令物理指标。宽核到窄核属于新配方设计，须以同协议误差/保留证据决定切换并冻结于新spec，不按更新数盲切，不承诺快速收敛；旧run不补写或重评分为新能力。
2026-10-14新授权宽窄核Motion31实验总online上限2000（smoke50+formal1950），显式reward_refinement_v2仅非零直线按完整证据渐进混合，宽核至少25%且Huber/几何/权重/PPO/物理不变；不沿用旧余额、不自动解锁。具体状态入口见STATUS，不将来源/接线通过当作Motion能力通过。
用户随后授权停止旧Motion并开姿态质量v3：仅显式`student_motion31_quality_reward_v3`/`motion31_quality_termination_v1`启用非饱和几何/姿态成本和持续严重坏姿态task termination，失败transition保留、terminated不bootstrap，不以差姿态长存活授予通过。历史50次包含于原2000上限，新smoke50+formal1900，不重置墙钟/新增配方额度；物理接口不变，新协议不能回写旧结果。具体门槛与身份见STATUS所索引声明。
用户随后明确允许smoke最多5次：仅新显式`motion31_quality_short_wiring5_v1`将smoke设为4critic+1actor更新，formal仍5次critic warmup；短证书只授予有限接线验证，不要求或冒称完整training episode/reset/timeout，覆盖实际单独报告，完整验收不变。正式上限1900、历史50次及失败评估墙钟保留，不将省下额度自动用于formal。
来源/latest/best_new/best_overall/accepted分开；同一模型完整能力，不拼成功点。

2026-10-15用户新授权一次2000在线更新课程，显式`motion31_straight_yaw_progression_v1`从v3/u1600三评估seed120/120来源完整恢复，顺序直线±1.5→±2→原地yaw±1→±1.5；保留zero及全部已学端点，不提前采样未解锁档。512env/GPU0共享，smoke≤5＋formal≤1995合计≤2000、18h/2GiB，单stage≤1500，预算不随晋级重置；不自动重试/第三链。保持v3原pitch/reward权重与停车时相、PPO/网络/物理不变，沿用绝对姿态与宽容保护；每250全评8env/command、连续两次完整通过才晋级，阶段通过模型与最终全课程accepted分开。CPU准备不授予其他运行，当前owner通知与TensorBoard显式开启。声明与证据入口见STATUS。

2026-10-15用户同意恢复v3奖励权重和停车训练路线，先修宽容早停并做1600三seed PPO0确认。仅新显式`motion31_absolute_posture_assessment_v4`采用保持段最大pitch≤.1/roll≤.05，来源相对姿态仅诊断；`motion31_absolute_posture_retention_v1`适应300、固定250检查、同一已学命令3次明显退化才停，UNKNOWN不晋级、不冒称能力退化。训练episode严重姿态终止仍原阈值，不放松runtime故障保护。三seed确认新evaluate1账本/PPO0/3h/2GiB/GPU0共享，不据此自动新PPO/升档或域随机化；细节见STATUS索引。

2026-10-14末用户另行明确授权当前链终态后一次新2000更新实验，见STATUS及`docs/MOTION31_SUCCESSOR_AUTHORIZATION_20261014.md`。显式`student_motion31_hold_level_reward_v4`/`motion31_hold_level_successor_v1`可从已结算父链同协议最佳运动checkpoint完整恢复Actor/Critic/Adam/std/RNG/refinement；保留zero，取消非零训练回零/停车，增强水平姿态权重。新增online总额2000含smoke≤5＋formal≤1995，512env/GPU0共享、18h/2GiB，不升速、不自动重试/第三链。新评分停车仅诊断，原物理/姿态/跟踪证据仍必需；缺accepted不阻止学习，不能称已能力认证。通用终态通知旧“未授权续训”措辞不撤销这次独立授权。

2026-10-15用户另行授权前进优先2000更新晋级课程：仅显式`motion31_forward_progression_v1`/`motion31_forward_capability_v1`，原v3/u1600完整恢复，来源+1.5完整通过后新档+2→+3→+4；保留zero及已学前进端点，不采样后退/yaw。512env/GPU0共享，smoke5+formal≤1995总2000、18h/2GiB、stage≤1500，不追加/重试。原reward/PPO/物理/训练时相不变；parking单独诊断，不以精确停车gate挡升级；绝对姿态/物理/跟踪与zero.3标准保留。每250全评8env、两次通过升级、原宽容旧能力保护，来源原始证据只读复用并记录derived protocol。当前owner通知和TensorBoard沿用授权，后台一次握手后结束；详见STATUS和新课程报告。

## 提交与后台

解释器固定 `/home/kellen/anaconda3/envs/issaclab/bin/python`，共享源码为项目 `src/`。
先CPU测试、零写plan；公开提交只用supervisor。配置PASS不等于submit_ready；
当前session、GPU资源、身份、输出、账本和前置证书在reserve前再次核验。
新链使用共享src和ledger-owned提交凭证；不复制源码/测试树，阶段记录身份引用或差异。
旧命令无需兼容，迁移当前调用；历史运行证据仍只读。
formal须身份匹配的wiring_certificate，或经公共校验消费的版本化受限工程恢复证书。
恢复流程见WORKFLOW；证书不授予运行权限或新能力通过，不重置smoke额度或修改原FAILED。
事件型smoke必须覆盖真实事件，不能仅凭更新数。
站立smoke检查工程接线，不要求随机探索策略已学会长期站立；真实Actor更新、结束/reset、非零奖励和保存读回仍必需。normal timeout是否被观察单独报告，未观察不冒称bootstrap已物理验证；生存与姿态质量仍由独立完整窗口验收。
source/smoke阶段提交不等于formal首更新；UNKNOWN握手报告started=false。

长训detached只做一次有界启动握手，然后结束交互。Codex不得循环查log/progress/metrics/PID/GPU，
也不得用sleep/wait、新watcher或子agent守候长训。既有monitor管预算、保存、评估、退出和结算。
明确授权的前台有界CPU验证/物理诊断评估可等待其自身完成，不属于长训轮询。
后台owner写hash匹配报告、report_ready并按at-most-once通知冻结负责人；未知投递不自动重发。
终态复盘只读一次；续训须新用户授权。旧PID或一次资源快照不证明当前存活/持续可用。

## 版本与交付

新实验名由domain.experiment_naming生成 `YYYY_M_D-HH_MM__purpose`（Asia/Shanghai），
config/run/spec名称一致，阶段子目录保留source_eval/smoke/formal；旧实验不重命名。
Git只处理明确本轮源码/测试/声明/文档；不force-add运行数据、资产、checkpoint或mutable ledger。
按明确路径stage，不git add .；commit/push仅按用户指令，提交不能重置预算或冒充历史源码。
公共工具命令只维护TOOL_INDEX，流程只维护WORKFLOW，结构只维护ARCHITECTURE，任务状态只维护STATUS。
新Recovery课程复用公共准备器；sampling/assessment与评分协议分开，新旧采样字段混用拒绝。
多文件声明含姿态库时核验完整发布标记和逐文件SHA后再授权。
固定family配额在config/preflight核验；冻结CPU仅执行PORTABLE测试，源码定位从实际导入模块出发。
sim2sim必须绑定actor坐标与COM测量语义；轨迹消费具名轴/schema，尺寸相同不能替代语义验证。
交付具体改动、验证、剩余证据与副作用；工程通过不代表行为通过。
