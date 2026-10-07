# Recovery: Stable, Level, Symmetric Standing

## 当前交接决定：转向自主起身 — 2026-10-07

用户现在的优先目标是**尽快学会自主起身，并在起身后不摔、基本水平**。

执行更新：用户随后明确批准实行本计划。现行配方与独立预算见
[首次低位起身](RECOVERY_RISE_LOW_20261007.md)，当前根为
`2026_10_7-16_18__recovery_rise_formal_from50`（正式阶段）；已完成的来源/smoke
证据在`2026_10_7-15_58__recovery_rise_low_from50`。PPO0定位已证明两个新中间姿态
被动沉降后初始化无效，暂不训练；已有低姿态8/8有效，故首轮直接采用此低位组。
训练期限定为11.5秒，独立观测23秒含初始化与起身后完整10秒保持；
下文15秒仍为历史提案，不是当前运行值。首个15_51提交在AppLauncher前失败，
消耗0；修复冻结身份接线后使用新根，旧证据保留。运行事实以新run优先。
15_58的10次smoke完成后又被completed字段接线误报阻止formal；仅在新目录
更正证书、导入已有使用和身份记录后执行formal-only，未重复smoke或增加总预算。

本节取代下文历史段落的“下一步”、入口和预算建议；历史内容保留以追溯来源。
最初计划编辑阶段不授权 AppLauncher、PPO或额外评估；后续用户执行授权
仅限上方新声明与独立预算，仍不允许旧链续训。
执行时仍按 AGENTS → STATUS → 新 spec → 实际 manifest/ledger/raw evaluation 核验。

### 已有证据与默认来源

默认起点仍是 `runs/standing_scissor_20261006/formal/model_update_50.pt`，SHA256
`1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。
这是当前 survival/level 协议下保留的来源，不是已认证的任意倒地起身策略。

| 原始证据 | 当前可作出的判断 |
| --- | --- |
| [source_capability 终态](../runs/recovery_coverage_ab_20261007/source_capability/terminal_report.json)：R0、R0_perturbed，各 seed104/205，各8环境×10秒，总32/32，PPO0 | 来源已覆盖本组近站立扰动；不再为已通过的这组初态单独安排 R1 PPO。不能外推到更大扰动或低姿态。 |
| [A_first 正式结果](../runs/recovery_coverage_ab_20261007/A_first/formal/analysis.json)：100更新/819200样本；25、50各8/8，100为0/8 | update100 全部因 roll 超限失败，均完成10秒且无 runtime fault；这是水平退化，不是本轮跌倒。 |
| [B_uniform 正式结果](../runs/recovery_coverage_ab_20261007/B_uniform/formal/analysis.json)：同预算；25、50、100各8/8 | 全 rollout 有效样本均匀选择支持减轻 roll 退化；只有一组训练随机流，不能保证长期无遗忘。 |
| 两组 candidate_selection：best_new=update25，best_overall/accepted=source50 | 不从最新100继续训练；B 的通过不等于净收益，mean abs vx由来源约0.704升至1.105m/s。漂移仍仅为诊断。 |
| 本轮两组 durability=NOT_RUN | 本轮没有100秒新认证。已有历史100秒评估/重评分需按其模型与协议身份单独引用，不能套给本轮候选。 |

课程名与 pose family 必须区分：课程 R1 是 `R0_perturbed`；family `R1`
是历史低位姿态，属于课程 R2。不按字符串“R1”直接判定难度。
两组完成事件分别为 A `250b545a9918a358c91f6cf0`、B `f865405426068218aa206370`。
通知中的 accepted=True 指来源回退，不代表最新模型通过。

### 最短推进路线

1. **先做 CPU 证据整理与起身接线检查。** 定位已有低位自主 Recovery 的 checkpoint、
   原始逐环境轨迹与 pose 身份，确认是否有可复用的自主抬升片段。旧模型只进入候选清单；
   旧2秒、teacher handover 或不同高度协议不等于当前自主起身认证。已有
   [manual0001](RECOVERY_MANUAL0001_START.md)记录约0.168m低位姿态，但历史几何检查
   不替代下一轮的初始化回读。
2. **准备一次有界 PPO0 能力定位。** 在新声明中明确一组闭链一致、可实际落地的
   中间低姿态和 captured0001，比较 source50 与有证据的历史自主 Recovery 候选；
   数量、seed、起身期限和墙钟先冻结，不做无限 checkpoint sweep。
   测初始高度、最大抬升、首次到达站立区、连续保持、倾角、接触及失败原因。
   普通起身失败是能力边界，不是训练前必须通过的 gate；非法初态/闭链故障才阻断。
3. **从最近的能力边界训练。** 如果来源在某组低姿态已经能起身，保留该能力并向
   更低一级扩展；如果完全不能抬升，先选择更近的中间姿态。按实测 root height、
   腿构型、方向和接触分组，不凭空指定0.15/0.20m为可行 reset。
   本轮只启用一个新难度组；不重新花主要预算训练已通过的近站立扰动。
4. **固定任务配方，分段保留候选。** 建议首轮 smoke10+formal最多100更新，
   formal评估25/50/100；64×128下总110更新/901120样本。这是待定预算提案，
   尚未创建 spec/账本或分配墙钟；PPO0基线与评估/清理须各有有限墙钟。
   smoke必须覆盖实际起身/超时事件及真实参数更新，不能仅证明程序启动。
   不能覆盖完整事件时报告证据不足，不静默增加更新额度。
5. **按新增起身成功与旧能力保持选模。** 保留来源和早期 checkpoint；失败分支
   不成为下一阶段默认起点。当前新组获得独立多seed起身结果且旧R0无回归后，
   才另行考虑下一难度。100秒耐久是所选候选的后续独立验收，不把它当作
   首轮低位探索的前置条件，也不宣称10秒通过已经耐久。

### 起身奖励、终止与成功必须重新对齐

当前 coverage 配方是近站立保持：`lift=0`、`upright=0`，height正项3，
pitch/roll平方成本各-4且 unconditional，failure_once=-1；连续项乘dt一次。
不能原样用于低位起身，也不能先凭感觉提高惩罚权重。

- **恢复阶段信号：** 恢复显式、有限的抬升与直立信号；检查低高度下的有效量级。
  现有 lift 是相对初高的高度进度，不是相邻状态势差，不称为有最优策略不变保证的 PBRS。
  精细水平和减速成本在接近站立时平滑增强；记录 gate 覆盖，避免低位必要运动
  被终态成本压制。具体权重/高度门槛在新 spec 冻结前以实测状态离线对比。
- **保留项：** uniform_rollout 作为优先候选，coefficient先保留0.02；仅约束
  来源已认证的近站立有效输入，不对低位输入强行模仿未知来源行为。
  reset 初始建议旧任务40%、新组60%，属待检验提案；另测实际样本占比，
  episode 长短不同会使 reset 比例与 rollout 占比不同。记录 family/pose/episode/
  时间覆盖；不同时改变环境数、LR、网络或 advantage normalization。
- **快速失败 reset：** 当前 `minimum_up_cos=0.5` 即总倾角约60°以上可立即终止
  对应环境 episode；不是停止整个 trainer。当前代码还检测禁止接触、初始化拒绝
  和 runtime fault。站立 gate 的均值0.10rad/峰值0.15rad不是当前全程立即终止门槛。
  低姿态需要独立核验60°是否排除了合法初态/恢复路径；不要把站立的小角门槛
  直接施加于恢复全程。接近站立后可以另声明带连续超限时间的倾角失败规则，
  但不能在本轮历史 run 中追溯应用。
- **接触规则：** 起身允许已确认的支撑接触。当前允许模式包括 robot、轮和多种连杆；
  因此不能声称“任意机身触地就失败”。逐个核对实际 body 分类与传感器，
  弱组件未建模仍为UNKNOWN。不为了易通过而禁用闭链、穿透、非有限或关节安全保护。
- **成功事件：** Recovery actor 自主从声明低位到达0.34–0.38m站立区，
  以现 survival/level 高度、水平、接触标准连续保持2秒作为拟议训练成功；
  期间无 teacher 接管。建议最多15秒起身期限，超时失败仍属任务数据。
  在线事件奖励只发一次；成功 episode 的bootstrap/终止语义在新 spec明确。
  独立验收记录完整恢复过程，随后同一episode连续保持10秒，保持指标窗口从
  达到站立条件起计算，不能把固定[2,10]直接当作低位起身后的稳态窗口。
  总时长必须足以容纳起身期限与10秒保持，早终不能缩短要求；所有初始环境
  进入分母，禁止只评分已成功的子集。这是拟议新协议，尚无运行认证。

最少诊断：每pose有效初始化数/尝试数/成功数、起身耗时、峰值抬升、
连续保持时间、首次失败原因、姿态/高度/接触/力矩限幅/闭链，分阶段reward
raw与dt后量级、return/value/advantage，以及retention eligible/selected覆盖。
runtime fault、物理失败、超时和保持证书失败分开统计；未知历史梯度不补零。
新 evaluator 若尚不支持事件对齐保持窗口，应先补纯CPU fixtures与plan-only，
不能用错误窗口启动训练。

### 两份参考材料如何使用

[TRAINING_EXPERIENCE_REUSE](../TRAINING_EXPERIENCE_REUSE.md)提供证据优先级、
真实事件接线、奖励单位/量级、旧能力回归、同源对照和候选筛选规则；其历史
“当前未运行/固定站立”描述不代表今天状态。
[参考文献](../参考文献.md)可借鉴逆向初态课程、支撑几何排查和分阶段奖励，
但没有可追溯论文来源或本项目干预证据。短腿一定更容易起身、两腿必须完全同步、
门控消除局部最优等只是假说；先核对原生机构与轨迹，不将其写成根因。

不引入硬状态机代替策略起身、残差轨迹控制、虚拟腿映射、WBC/LQR、重力补偿、
限矩增加或无限力矩“解冻”；不硬锁轮/左右动作，不修改USD。
合法滚动不等于滑移，不因轮转就盲目加入强轮速/对称惩罚。
本任务不训练速度跟踪，不能把“趴地偷速度reward”当作已确认机制。

### 实施边界与下一位执行者

只通过 `native_stand.command_v6.supervisor` 提交；下文旧 launcher/train_stages
命令仅历史说明。新配置/run根使用Asia/Shanghai的
`YYYY_M_D-HH_MM__purpose`，独立ledger，记录来源/资产/代码/协议SHA。
先CPU回归和零写入plan-only，再按明确授权预留exact attempt。
用户此前允许共享GPU0且禁止停止其他进程；资源同意不等于新的PPO或评估预算。
当前两组已COMPLETED，不重启、合并账本或使用剩余额度；当前会话身份需重新记录。

最初计划编辑阶段仅改本文，未新增spec、预算、模拟、训练或历史重评分；
后续执行阶段的新增声明与实际使用见本节顶部执行更新及对应run。

---

以下为历史决策，所有“当前/下一步/授权”仅属于所注明日期和run。

## Current Decision: User-Approved Survival and Level Posture -- 2026-10-06

New authorized implementation supersedes the preparation paragraphs below:
[survival/level R0 -> R1](RECOVERY_SURVIVAL_LEVEL_20261006.md), fresh10000total
updates3smoke+9997formal. Read STATUS for actual detached startup and runtime.
New frozen protocol removes motion/symmetry gates consistently across reward,
online success, curriculum, evaluation and selection. Old experiments stay intact.

The user accepts `runs/standing_scissor_20261006/formal/model_update_50.pt`
by GUI and changes the current objective to **avoid falling and keep the body
level**. Zero-speed regulation, bounded planar drift and strict leg symmetry
are no longer promotion requirements for this next task; retain them as
diagnostics. This is a changed task, not an improvement of the old acceptance
score. Original specs, evaluations, ledgers and automated selections stay intact.

Next source SHA256:
`1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`.
Its existing full evaluation records 8/8 continuous10s, no runtime fault,
mean root height0.36667m, dual support100%, mean absolute pitch1.26deg and
roll4.15deg. Mean absolute vx0.70411m/s is a diagnostic, not a rejection under
the user's new goal. The model is GUI-approved for this goal; it is not certified
under a new machine-readable protocol or the old stationary-standing protocol.

Proceed next to **R1 enlarged near-standing perturbations**, keeping R0 samples.
R1 does not mean the captured bottom-down pose: that is curriculum stage R2.
In code, R1 uses pose family `R0_perturbed`; pose family `R1` is the low-pose
family and must not be selected by confusing family names with stage IDs.
Do not require the newly harder R1 cases to succeed before starting R1 learning.
Validate their initialization, closure and control path first.

Before submission, create a new spec with matching reward, success/FSM,
curriculum and evaluation semantics. Do not leave old speed/drift/symmetry
conditions silently active after removing them from the report. Retain height,
support, pitch/roll, continuous survival and all physical runtime protections.
A proposed level tolerance consistent with the accepted GUI is mean absolute
pitch/roll<=0.10rad each and peak<=0.15rad; these are proposed new values,
not retroactive thresholds or a completed new acceptance test. Promotion to
R2 should still require two non-overlapping128-episode windows and two full
evaluations under the frozen new protocol. Only subsequent resets change stage.

This update records task intent and the next source. It starts no simulation/PPO,
allocates no budget and does not enable stages in a historical spec.

## Previous Decision -- 2026-10-06

Wheel alignment probe is COMPLETED/reviewed:53updates, offset16.69->8.08cm,
but vx0.704m/s and roll/leg-length gates fail. Not a stable/symmetric solution.
No continuation; lower-weight same-source comparison is the next proposal.
See root STATUS and STANDING_SCISSOR_EXPERIMENT_20261006 completion review.

Current task supersedes BC test: [wheel alignment probe](STANDING_SCISSOR_EXPERIMENT_20261006.md).
Source1500 unchanged, fixedBC0.02, only wheel-center geometry reward added;
53updates transferred,1140old remaining unspent. Runtime/FK64samples passed,
3smoke complete, formal startup actual1. No automatic extension. Read STATUS.

Current authorized next experiment: [BC gradient / annealing A/B](STANDING_BC_AB_20261006.md).
Yaw-only chain is completed at103updates,0/8 strict acceptance. Two new arms
transfer206updates (3smoke+100formal each), leaving1193 old updates unspent.
Same source1500, seed/Adam/LR/reward/physics; only full-channel BC schedule differs.
No automatic wheel-only/mirror experiment or long continuation. Read root STATUS
and pair run manifest/terminal for actual state; paragraphs below are history.

Superseding entry: [yaw-only review](STANDING_YAW_REVIEW_20261006.md).
The separately authorized2000-update v2 long run stopped at498updates;103remaining
updates are transferred to source1500 yaw-only smoke3/formal100. Remaining1399
old updates are not automatically resumed. Original metadata below is historical.

Bounded v2 source10s/smoke3/candidate10s verification is now complete;
[report](../runs/standing_level_v2_check_20261006_151025/completion_report.md).
3updates/24,576samples,216.52s. Both models survive10s but fail drift/vx/yaw/mirror;
source remains best observed, accepted=null. No long continuation authorized;
the new ledger's formal limit is0. Earlier UNAUTHORIZED statements below describe
preparation history, not permission to restart or reset usage.

The user stopped the chain after1189formal+3smoke updates. Do not resume it or
reuse its remaining8808updates automatically. Formal STOPPED_BOUNDED and
wrapper COMPLETED conflict is preserved in original evidence.
See [height-gate review](STANDING_HEIGHT_GATE_REVIEW_20261006.md) and the
[new CPU-only v2 spec](../configs/experiments/recovery_standing_level_v2_20261006/spec.json).
The ledger was UNAUTHORIZED during preparation; its bounded verification is now
consumed and formal remains0. R0 settling, pitch/roll and geometry costs are
unconditional; upright weight0; source retention0.30-0.40m, same coefficient.
Original source1500, physics and acceptance stay fixed. These are mechanism
repairs, not demonstrated convergence improvements. The short physical verification
above is complete; no long run was launched.

## Historical Authorization — 2026-10-06

The user has now authorized this complete detached chain: at most10000
actual PPO updates,10h cumulative wall,3smoke+9997formal,81920000samples.
Baseline300s,smoke300s,formal34740s,durability600s and60s cleanup reserve.
Ledger is AUTHORIZED and starts with zero usage. The execution uses the
experiment's independent `execution_snapshot/src/native_stand` so a concurrent
motion trainer keeps its own code/config. Snapshot CPU/fake-process checks:
81 passed. The older500-update budget proposal below is superseded.
Run: `runs/recovery_standing_balance_20261006_chain_1140`.
HAPI target: `6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1`.
One startup handshake; no conversational log polling after submission.
No other control, reward, protocol or enabled-stage changes accompany the
budget increase. R0 remains the only enabled stage.

Updated: 2026-10-06. This is the handoff and context-recovery entry, not a new
simulation/PPO authorization. Start from AGENTS -> STATUS -> this document ->
the current spec -> the actual run manifest. Check the ledger and process
identity before submission; never resume from a historical PID.

## Current Evidence

- Frozen source: `runs/recovery_stage0_stand_from1000_20261005_chain/formal/model_update_1500.pt`.
  SHA256: `c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82`.
- It passed 8/8 autonomous **2-second** hold. It has no continuous10s/100s
  standing certificate and no bottom-down Recovery certificate.
- The subsequent symmetry-only500 run survived15s but achieved0/8 holds;
  last2s mean abs vx0.416m/s exceeded0.30m/s. Height/contact/tilt remained good.
  Stronger symmetry penalty is not a demonstrated improvement.
- Source, latest, accepted and GUI-approved models are separate identities.
  Do not substitute B200, old500 or Gym47250.

## Historical v1 Recipe

[spec](../configs/experiments/recovery_standing_balance_20261006/spec.json),
[budget](../configs/experiments/recovery_standing_balance_20261006/budget.json).
This recipe was authorized and subsequently stopped by the user. Its original
spec, ledger and source snapshot are historical evidence; do not edit them.

Target: command `[0,0,0.36]`, autonomous stable standing by Recovery itself.
No handover/teacher control is used to obtain success. Physical configuration
remains the knee-stop USD copy, plane0.5/0.5/0, physics1ms, PD5ms, policy10ms,
leg40Nm/wheel5.5Nm, action leg1.6rad/wheel100rad/s and no pair projection.
25D physical-joint frame +125D oldest-to-newest history =150D actor/critic.

This is a multi-term standing adaptation, not a single-variable reward ablation:

| Term | Definition / Frozen Value |
| --- | --- |
| Height | Gaussian around0.36m, width0.04m, weight3; saturated lift weight becomes0 for this R0 recipe |
| Pitch/roll | Existing canonical squared costs, weight-4 each, scale0.12rad; full gate now0.36m |
| Linear settling | Existing full-speed Pseudo-Huber, scale0.1m/s, weight-0.6 |
| Angular settling | Existing Pseudo-Huber, scale0.35rad/s, weight-0.4 |
| Vertical motion | Squared vz/0.1, weight-0.1 |
| Level angular motion | Body x/z angular speed squared, scale0.3rad/s, weight-0.1 |
| Mirror posture | Hip sum and active-link difference, deadband0.03rad, scale0.2rad, weight-0.02 |
| Leg-length balance | Hip-anchor to main-wheel-center length difference, scale0.02m, weight-0.02 |
| Wheel differential | Left/right wheel-speed difference, scale10rad/s, weight-0.01; same authored wheel-axis signs |
| Source retention | Auxiliary actor-mean MSE, coefficient0.02, <=256 real pre-action inputs/rollout; only zero command and height0.34–0.38m |

The six new costs use a0.30–0.36m height gate except Gaussian height.
Continuous terms are multiplied by policy dt exactly once; success/failure
bonuses remain once-only. Existing effort/action/contact penalties are retained.
Retention teacher is frozen **source1500**, with the same1.6/100 action semantics;
it is not the older0.5rad STAND network. Retention adds an explicit gradient
through PyTorch's public optimizer pre-step hook; no optimizer method replacement.
It may inhibit necessary adaptation, so log its loss and selected input count.
Coefficient0.02 is a proposed recipe value, not a proven optimum.
Real pre-action observations/masks are copied in fixed-size batches; eligible
inputs are selected once at the first optimizer step, not by per-policy-step
GPU boolean indexing. At64x128x150 this cache is about4.7MiB plus masks.

## Course and Promotion

1. R0: nominal near-standing pose70%, small closure-consistent leg perturbations30%.
2. R1: enlarged near-standing leg and orientation perturbations.
3. R2: captured bottom-down low pose.
4. R3: enlarged asymmetric low-pose distribution.

Only R0 is enabled in this500-update recipe (`max_enabled_stage=0`). No motion
commands or automatic jump to low poses. The other stages are explicit future
interfaces, with offline candidates that still require runtime validation.
Before enabling each stage, validate its initialization and retain >=40% of
previously mastered tasks in a separately versioned recipe; the present recipe
does not claim that future rehearsal mix has been tested or enabled.

The curriculum manager requires two non-overlapping128-completed-episode windows,
each success rate>=90% and runtime faults0, **plus two consecutive full10s
evaluations**. Success includes low-speed/height/tilt/contact and geometry gates,
not reward alone. A short2s screen cannot promote a stage. Failed full evaluation
resets its confirmation streak. Stage changes affect subsequent resets only.

## Independent Acceptance

Training may end a successful episode after2s. Independent standing evaluation
suppresses that success-only reset and continues the **same episode**; true faults
and falls still end it. All terminal data come from pre-reset snapshots.

| Criterion | Required Value |
| --- | --- |
| Continuity | 8/8 complete10s, no reset/fault; final selected candidate100s separately |
| Height | 2–10s mean0.34–0.38m; >=90% samples in range; initial minimum reported |
| Speed | Mean abs vx/vy<=0.03m/s; yaw<=0.03rad/s |
| Drift | Whole-episode maximum planar excursion<=0.20m from pre-physics origin |
| Level | Mean abs pitch/roll<=0.05rad each; peak<=0.10rad; peak tilt<=0.12rad |
| Symmetry | Mean mirrored joint error<=0.10rad; mean leg-length difference<=0.01m |
| Support | Dual contact>2N in >=95% steady samples; mean normalized force difference<=0.30 |
| Safety | Closure<=5mm; sampled saturation<=5%; existing fault protections intact |

These symmetry/support values are proposed v1 thresholds pending physical
feasibility checks. Contact force is sensor resultant magnitude, not verified
normal load. Policy-sampled saturation is not every-PD saturation certification.
Body COM offsets may require a small persistent load difference. Never lower
thresholds in a running experiment; record infeasibility and create a new spec.
Never require raw left/right actions to be identical or lock the wheels.

## Execution and Budget Proposal

New baseline<=300s/PPO0 -> smoke3updates/300s -> formal<=500updates/7200s ->
selected candidate100s/600s. Total proposed actual PPO<=503updates,
samples<=4,120,576; formal alone4,096,000samples. No old budget is reused.
Source10s may fail the new behavioral gates; that is not a runtime fault.
Before PPO, require8 continuous source episodes, valid initialization and no
runtime fault under this exact spec. If the source cannot survive10s, diagnose
the reset/control path first.

Formal checkpoint every100;2s screening every100;full10s every250/final.
For500updates this means6 checkpoint identities (including evaluated250),
4 light screens and2 full evaluations. Light screens never certify standing.
Final100s uses only an already10s-accepted candidate; otherwise report no accepted
candidate. The durability phase must remain independently budgeted.
Ordinary full milestones retain summaries and bounded failure windows; source,
final and selected durability evaluations retain compact trajectories. Candidate
registries exclude these arrays so repeated summaries do not rewrite trajectories.

CPU-only plan (no Isaac/output/ledger mutation):

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/preflight.py \
  --spec configs/experiments/recovery_standing_balance_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_balance_source_NEW
```

After explicit runtime budget approval, use the existing launcher for source_eval,
then the existing sequential Recovery train_stages for smoke/formal; supply the
confirmed HAPI target explicitly. Do not call the older Recovery chain: its
autonomous baseline validator targets the historical2s protocol.
The source-only trainer builds actor only, writes evaluation_source and a source
candidate registry; smoke preflight checks exact baseline spec/checkpoint identity.

Actual runtime CLI (verified against `--help`; **not executed**):

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/launcher.py \
  --spec configs/experiments/recovery_standing_balance_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_balance_source_NEW --launch
```

After that exact baseline completes and is validated, the existing detached
smoke/formal supervisor can be submitted with the confirmed HAPI ID. Do not
submit both commands concurrently or manually turn the ledger into AUTHORIZED
without an explicit runtime budget. The `train_stages` CLI takes `--spec`,
`--output-dir`, `--hapi-session`, and optional `--tensorboard-logdir`.

## CPU Verification (2026-10-06)

Focused regression: **78 passed**. Full suite: **159 passed, 7 failed**;
the seven failures concern historical configs referencing an outdated colleague
YAML SHA. The capture CLI's actual error is `colleague_config identity differs`.
Historical configs and evidence were not rewritten to hide the drift. The new
recipe freezes the current dependency identity and records the old/new hashes.

Coverage includes the actual source1500 actor/critic and all17 Adam states,
strict150D loading, exact parameter/moment equality and effective LR3e-5;
inference-mode inputs followed by real Adam retention backward; CPU fake
environments that reset their live state after falling; complete10s scoring,
0.4m final drift, sign-alternating velocity, missing/nonfinite diagnostics;
stage caps,128-episode windows, two full confirmations and regression stops.
The new source-only plan returns `READY_NEEDS_AUTH`, CPU-valid, zero files
written. Smoke preflight accepts a physically valid10s source baseline even
when it fails the new behavioral gates, but rejects a2s or mismatched baseline.

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q \
  tests/test_recovery_standing_balance.py tests/test_recovery_autonomous.py \
  tests/test_recovery_dense_reward.py tests/test_recovery_settling.py \
  tests/test_completion.py src/native_stand/command_v6/tests/test_domain.py
```

CPU evidence does not establish that R0 can pass these thresholds in PhysX.
No new runtime baseline, smoke, formal, or100s durability result exists.

## Required Review / Do Not Drift

- First decide whether source1500 retains standing for10s; don't silently call2s10s.
- Compare matched-duration source/candidate windows and all checkpoint identities.
- Track retention cost, level angles, mirror/leg lengths, vx/yaw, dual contact,
  saturation, closure, per-pose acceptance and complete success counts.
- Rank full acceptance, survival, passed-env count, drift, level and symmetry;
  never rank early-death/low-drift or reward-only as best.
- If two consecutive full zero-command evaluations regress, stop escalation and
  preserve earlier candidates. Do not automatically add updates or change STAND.
- R0 success is standing from near-standing reset, not successful low-pose recovery.
- The next low-pose recipe must restore explicit lift progress and verify that
  the near-standing Gaussian doesn't eliminate the low-height learning signal.
- No external force, gravity compensation, hard wheel lock, hidden action gate,
  USD edits or effort-limit increase.
- Completion notifications request review and never authorize continuation.
