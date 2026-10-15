# Codex入口整合前原文归档
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


仅用于历史追溯。现行阅读入口是根AGENTS/README/STATUS，工具/流程/架构各有唯一正文。
原文以代码块保存，旧“当前”和相对链接仅代表归档时内容。

## AGENTS.md

````markdown
# Native closed-chain project rules

Before submission-interface changes, read `docs/SUBMISSION_CONTRACT_FIX_20261007.md`. A preflight PASS is not submission readiness; current-session/GPU/authorization checks are separate. That documentation-only commit leaves its implementation in the working tree, so verify the local CLI before use.

New Codex sessions must also read `docs/CODEX_START_HERE.md` for current entrypoints, command usage, authorization boundaries, and the no-polling policy. This handoff does not grant simulation or training authorization.

This project is `/home/kellen/wheel_leg_native_train`. Read `README.md`,
`STATUS.md`, `ARCHITECTURE.md`, the current spec linked by STATUS, then
`TOOL_INDEX.md` before running a command. A run's manifest, progress, terminal
report and evaluation JSON override a Markdown status snapshot.

Before designing or changing rewards, curricula, training experiments,
candidate selection, or acceptance, read `TRAINING_EXPERIENCE_REUSE.md`;
actual runs follow their spec, manifest, and raw evaluations.
For the prepared autonomous-standing task, also read
`docs/RECOVERY_STANDING_PLAN.md`; it is a handoff contract and does not grant
a runtime or PPO budget.

Only this project may be edited for its experiments. Keep the colleague USD and
source project, `/home/kellen/fudan_train`, `/home/kellen/wheel_leg_sim2sim`,
`/home/kellen/wheel_leg_training`, and all old audit runs read-only. Do not
move or overwrite checkpoints, raw evaluations, or ledgers. Record source and
asset SHA in every run. Current code describes the next run, not an old run.

The frozen native interface is in the experiment spec and `ARCHITECTURE.md`:
25D physical-joint frame, five oldest-to-newest frames, 150D actor/critic
input, six left-first position/velocity targets, 1 ms physics, 5 ms PD, 10 ms
policy, 40/5.5 Nm physical limits. Training, independent evaluation and GUI
playback use the same `CommandEnv` and plane scene. No Gym virtual-leg mapping,
Jacobian lookup, LQR, gravity compensation, static trim, hidden gating, or
effort-limit increase.

Run CPU tests and plan-only preflight before any AppLauncher. Plan mode writes
nothing. Each experiment spec directory owns an independent budget.json.
Only explicit user authorization permits simulation/PPO; follow STATUS to the
corresponding ledger, preserve all previous usage and reject duplicate chains. An
authorized attempt needs a fresh output path, exact-ID ledger reservation and
terminal accounting. Never infer an active trainer from an old PID. Do not
stop or change another task. A new reward, physical contract, command stage,
or acceptance gate requires a new experiment spec and run directory, while
the shared code stays in this one project.

Use `/home/kellen/anaconda3/envs/issaclab/bin/python`. The package is imported
from this project's `src/`; the colleague asset module root is supplied at
the CLI boundary after identity checks. Pure domain modules must not read
files, environment variables or Isaac runtime state.

## Detached Training and Terminal Wake-up

Submit authorized training through the detached supervisor/monitor chain. The
interactive Codex worker may perform one resource snapshot and one bounded startup
handshake, then must end the interaction. A submission receipt alone does not prove
formal training started; report the exact verified stage and missing evidence.

Do not personally poll training logs, progress.json, metrics, checkpoint files,
processes or GPU state to wait for training. No repeated tail/ps/nvidia-smi, shell
while loops, periodic sleep/wait, or repeated tool calls that keep the conversation
alive. Do not move that polling into a newly created watcher or sub-agent. Existing
owned monitors may enforce process/budget deadlines and evaluate frozen milestones.
Foreground bounded CPU tests or diagnostic evaluations are separate from long training.

The background owner waits for its own child exit, reconciles the exact attempt,
writes a compact terminal report and report_ready event, then invokes the existing
completion.notify hook to wake the execution worker's current HAPI session. Validate
the current session before submission; never inherit a session from a historical
spec or example. Notification requires a hash-matched ready report, event-ID dedup,
and no automatic continuation. A failed/unknown delivery is not a training failure
and must not trigger restart, duplicate submission or an unlimited send retry.

On terminal wake-up, read the report once, review immutable evidence and acknowledge
the event. Do not automatically resume training from a notification. Only explicit
new user input permits a one-shot status inspection or diagnosed engineering repair;
do not use that exception to resume polling. See docs/DETACHED_TRAINING_POLICY.md.

## Evidence and Interface Changes

Recovery batch duration comes from recovery.task_protocol.batch_seconds; do not
hardcode a second duration in schema, planner or evaluator. For new transition
diagnostics declare diagnostic_profile and required_diagnostic_fields; summary,
failure_tail and full_transition have distinct scopes. Missing historical fields
cannot be reconstructed as measurement. tools.prepare_checkpoint_diagnostic only
creates UNAUTHORIZED PPO0 declarations, never launch or reuse parent permission.

Use docs/ENGINEERING_STATUS.md as the current engineering index. Dated test counts,
startup PIDs and protocol statements remain historical; verify exact frozen run
evidence before claiming current process state or learned capability. A documentation
or Git task never authorizes simulation, polling, notification sending or resumption.

Use domain.episode_summary for completed-episode producer/reader contracts.
Conflicting legacy aliases must fail. Read docs/EPISODE_IDENTITY_RECOVERY_FIX_20261007.md
before correcting an engineering certificate. Never use aggregate episode counts
to prove a new family/pose path was observed. Declared source identity and actual
frozen location are separate; relocation still needs the submission receipt and
exact module hashes. Engineering recovery defaults to a zero-write plan and never
grants budget/launch authorization, even when publication is explicitly requested.

Read `docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md` before changing
evaluation, gate aggregation, diagnostics, preflight or submission interfaces.
These engineering changes do not authorize simulator use or a training budget.
Keep requested scoring windows separate from observed per-environment duration;
early termination must never shorten the acceptance requirement. Reject unknown
protocol fields, invalid SHA, contradictory gate decisions and missing scored
environments. Normalize gates by task; UNKNOWN or missing evidence cannot pass
or unlock a curriculum stage. Never treat uncollected diagnostics as measured zero.

Evaluation must restore actor mode, runtime switches and Torch RNG even after
setup, reset or cleanup failure. Restore RNG after all cleanup resets. Optional
diagnostics default to disabled, run only at explicitly selected updates and
must not change action sampling, gradients, optimizer updates or the recipe.
Label full-rollout probes, actual optimizer-step probes and offline replay
separately; unavailable historical gradients remain UNKNOWN.

Use the shared supervisor for new source -> smoke -> formal submissions. Formal
requires a persisted, identity-matched `wiring_certificate.json`, source identity,
active-phase health and exact ledger prerequisites. Require an explicit physical
GPU and the current HAPI session; never reuse a historical session ID. Verify
process command, start time, spec, output and attempt ID rather than PID alone.
An UNKNOWN handshake must report `started=false`. A commit, old quota, historical
AUTHORIZED field or terminal notification never grants new simulation permission.

## Git and Documentation

For every newly created experiment, prefix its root directory and experiment
name with the creation date/time in Asia/Shanghai: YYYY_M_D-HH_MM__<purpose>,
for example 2026_10_7-14_27__motion_width_ab. Use the same name for the config
root, run root, spec.experiment and artifacts.run_name where present. If the
minute/name already exists, append a collision suffix or use seconds; never
overwrite. Phase/arm children (source_eval/smoke/formal/A/B) keep their semantic
names. Do not rename existing/prepared/frozen experiments or historical evidence.
See docs/EXPERIMENT_NAMING.md; naming never grants runtime authorization.
New public preparers must use domain.experiment_naming rather than hardcoded names.
Read docs/STATE_REQUEST_FIX_20261007.md for canonical chain RunState and distinct
Motion/Recovery batch request schemas. Legacy handshake fields are evidence, not
a second lifecycle. Do not migrate or edit an active task's frozen execution code.

Use TOOL_INDEX.md for current public entries and TOOL_INDEX_HISTORY.md only for
historical reproduction. Only supervisor is the public submission CLI; launcher,
monitor and stand_chain remain internal components. Recipe-specific preparers are
not generic configuration tools. Historical replay acknowledgment never grants
simulation authorization; retired fixed-GPU/run/session drivers cannot launch.

New submission interfaces are documented in `docs/ENTRY_SEMANTICS_FIX_20261007.md`.
Default GPU ownership is exclusive; shared mode requires a recorded explicit user
authorization note. Never exempt owners merely by process name or treat sharing as
training authorization. Distinguish submitted/current stage from verified formal
first update. Certificate readers validate only; the phase owner writes evidence.
Use canonical model roles; a source may be best overall but never best new.
Episode certificate failure, physical termination, time-limit truncation and
runtime fault are separate facts. Required smoke duration comes from the frozen
event declaration; insufficient sampling cannot be fixed by silently raising budget.

Follow `docs/GIT_WORKFLOW.md`. Version current source, tests, scripts, declaration
configs and documentation. Keep `runs/`, `isolated/`, USD/assets, checkpoint
binaries, mutable ledgers/budgets, submission records and frozen execution copies
local and read-only; do not force-add ignored evidence. Stage explicit paths,
review staged contents and preserve unrelated dirty changes. Do not reconstruct
an imaginary historical baseline from current files. Use detailed Chinese commit
messages when requested; do not push without an explicit request.

Update README, STATUS, ARCHITECTURE and TOOL_INDEX when public interfaces change.
Preserve dated historical statements and add explicit corrections/current entry
notes. List exact changed files, CPU checks, missing runtime evidence and known
compatibility limits. Do not describe a test or report repair as learned capability.

CPU regression, without AppLauncher:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

````

## README.md

````markdown
# Native closed-chain training

工程流程补齐：[冻结CPU验证与公共证据接口](docs/ENGINEERING_WORKFLOW_COMPLETION_20261008.md)。

Codex新工具操作：[参数、固定流程与写入边界](docs/NEW_TOOLS_USAGE_20261008.md)。

最新工程：[通知路由与证据生命周期修复](docs/NOTIFICATION_EVIDENCE_FIX_20261008.md)。
CPU验证，不发送通知或重提任务；完整修复与仍待完成项分别列明。

Recovery P1已COMPLETED：smoke20+formal100，new50/100保持高度与水平改善，连续双轮接触未过；自动best100未认证。见[终态复盘](docs/RECOVERY_MIN_HEIGHT_P1_COMPLETED_REVIEW_20261008.md)。未自动续训。

Recovery P1原始诊断接线修复重试已提交：23_29链，握手SOURCE_EVAL，formal首更新未验证；遵循AGENTS工具入口，共享GPU0、扣除已耗墙钟。见[记录](docs/RECOVERY_MIN_HEIGHT_P1_GUARDFIX_RETRY_20261007.md)。

Recovery P1第二次链FAILED：source评估完成，smoke保护器误读候选摘要，PPO0更新。共享接线已修复、CPU515 passed，未重试；[复盘](docs/RECOVERY_MIN_HEIGHT_P1_GUARD_TERMINAL_REVIEW_20261007.md)。

Recovery P1 reset修复后的独立重试已提交，握手SOURCE_EVAL；formal首更新尚未验证。原额度扣除已耗墙钟，共享GPU0。见[重试记录](docs/RECOVERY_MIN_HEIGHT_P1_RESETFIX_RETRY_20261007.md)。

Recovery P1终态FAILED：来源评估reset工程错误，PPO0更新。共享代码已最小修复并通过CPU510项；无自动重试。见[复盘](docs/RECOVERY_MIN_HEIGHT_P1_TERMINAL_REVIEW_20261007.md)。

Recovery P1新链已批准并提交，首次握手SOURCE_EVAL，formal首更新尚未验证；共享GPU0、不自动续训。见[执行记录](docs/RECOVERY_MIN_HEIGHT_P1_PREPARATION_20261007.md)。

Recovery P0/P1最新准备：[新高度目标迁移](docs/RECOVERY_MIN_HEIGHT_P1_PREPARATION_20261007.md)。来源S50；UNAUTHORIZED，未启动仿真/PPO。旧0.34–0.38协议与终态保留。

Recovery最新终态：[对齐短训复盘](docs/RECOVERY_LEVEL2_ALIGNMENT_TERMINAL_REVIEW_20261007.md)。20_55完成110更新，0/8认证；新100高度/接触保持改善，轮振荡与roll仍失败，无续训。

Motion 通用准备入口：[提交契约与准备器](docs/MOTION_PREPARER_CONTRACT_20261007.md)。
显式来源/请求/身份，默认零写计划，`--write`仅创建未授权声明；提交仍只用supervisor。

当前Recovery获新授权重提：[20_55 spec](configs/experiments/2026_10_7-20_55__recovery_level2_alignment_from50/spec.json)，同配方新独立账本；20_42历史失败保留。状态见STATUS。

当前Recovery：[Level2弱轮心对齐短训练](docs/RECOVERY_LEVEL2_ALIGNMENT_20261007.md)。已完成8env离线事件/窗口核查；20_42链来源阶段接口失败，PPO0。共享接口已修，未自动重启，实际状态看STATUS与run。

提交接口修复：[authorization/session 契约与可提交检查](docs/SUBMISSION_CONTRACT_FIX_20261007.md)。默认 plan PASS 不等于可提交；本轮仅文档入 Git，修复代码保留工作树。

新 Codex 会话先读：[入口、用法与授权边界](docs/CODEX_START_HERE.md)。历史“当前”记录不代表实时进程状态。

最新诊断接口：[任务时长、保存profile与checkpoint准备](docs/DIAGNOSTIC_PROFILE_FIX_20261007.md)。
显式规划保存字段，默认未授权PPO0准备，不触碰后台冻结评估。

当前执行[冻结update50完整几何PPO0复核](docs/RECOVERY_UPDATE50_GEOMETRY_PPO0_20261007.md)，
仅补采诊断，不新增PPO或改变控制。结果看独立run终态。

最新Level2已经结束，下一步为[收稳诊断与准备](docs/RECOVERY_LEVEL2_TRANSITION_REVIEW_20261007.md)。
新report区分入口前诊断与保持成绩；下一cost probe未获运行预算，不续训旧链。

最新Recovery任务：[Level2原收腿姿态与旧抬升模型迁移](docs/RECOVERY_LEVEL2_DRAWBACK_20261007.md)。
用户GUI确认manual0001；source旧update1000、当前限位USD、新独立预算，状态见STATUS。

当前工程总入口：[工程状态与剩余缺口](docs/ENGINEERING_STATUS.md)。
近期验证435项CPU通过；工程接口与历史训练事实分别记录，提交不授予运行权限。

最新证据工程：[冻结身份、episode schema与受限恢复](docs/EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)。
工程恢复只生成未授权新配置，不自动恢复训练；历史证据和活动快照保持不变。

训练执行遵守[后台与终态唤醒规则](docs/DETACHED_TRAINING_POLICY.md)：一次握手后
结束交互，后台owner结算并通知当前HAPI会话；Codex不得亲自轮询日志等待长训。

当前Recovery转入[低位自主起身](docs/RECOVERY_RISE_LOW_20261007.md)，
使用独立日期时间spec/ledger；coverage A/B已完成，保留source50。
起身后保持采用事件对齐窗口，不将近站立或2秒成功称为完整起身认证。
准确提交/首更新/终态见STATUS与新run证据，旧段落仅日期任务记录。

最新工程接口：[状态机、任务请求与历史工具保护](docs/STATE_REQUEST_FIX_20261007.md)。
共享链状态和formal首更新证据分开；Motion/Recovery请求不混用。
这些接口修复不授权新的仿真或训练，也不替换活动run的冻结副本。

已完成Recovery任务：[source50能力复核与BC覆盖对照](docs/RECOVERY_COVERAGE_AB_20261007.md)。
保留其独立账本和原始证据；旧hold10已结算，不代表续训许可。

公共入口只见[当前工具清单](TOOL_INDEX.md)；旧日期命令集中在
[历史工具清单](TOOL_INDEX_HISTORY.md)。新提交仅使用supervisor。
新实验使用[日期时间前缀命名](docs/EXPERIMENT_NAMING.md)，例如
`2026_10_7-14_27__motion_width_ab`；已有实验不重命名。
当前Motion推荐来源为B250，早期new250推荐已被后续物理复核替代；
Recovery hold10已结束，不授予续训权限。

Current engineering entry: [入口、资源与episode语义修复](docs/ENTRY_SEMANTICS_FIX_20261007.md)。
exclusive/shared、source/best_new/best_overall、提交阶段和formal首更新分别记录。
工程代码更新不授权运行；现有训练冻结快照与历史证据保持不变。

Motion工程复核入口（2026-10-07）：[新协议、模型身份和PPO0复核](docs/MOTION_ENGINEERING_RECHECK_20261007.md)。
独立motion授权不改变Recovery；当前物理终态以该新run/ledger为准。

Recovery R0 holding experiment: [冻结配方](docs/RECOVERY_R0_HOLD10_20261007.md)与
[已完成复盘](docs/RECOVERY_R0_HOLD10_REVIEW_20261007.md)。历史授权已执行，
不代表当前续训许可；source50和历史结果保持不变，运行状态以run终态为准。

Engineering entry (2026-10-07): [interface/evidence changes](docs/NATIVE_INTERFACE_EVIDENCE_20261007.md).
Followup: [verified gap closure](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md).
Read-only health/preflight and offline correction tools are available; this change
does not authorize simulation or continuation. Historical launch text below must
be resolved against immutable terminal evidence and STATUS.

**Current entry:** [STATUS.md](STATUS.md). Current engineering validation and
remaining runtime limits are recorded in the followup above. Git versioning
rules and commit scope are in [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md).
Versioned specs do not carry active training permission; local ledger and fresh
explicit authorization still govern any runtime action.

The following task descriptions are dated history. The
[survival/level R0 -> R1](docs/RECOVERY_SURVIVAL_LEVEL_20261006.md) chain started
from GUI-approved scissor update50 and subsequently stopped within its bound;
actual terminal evidence overrides its earlier startup description.

Historical task:
autonomous R0 standing from native Recovery update1500; its implementation,
thresholds and handoff are in [RECOVERY_STANDING_PLAN.md](docs/RECOVERY_STANDING_PLAN.md).
Completed controlled probe: [wheel-center alignment](docs/STANDING_SCISSOR_EXPERIMENT_20261006.md),
3smoke+50formal; offset reduced but drift/roll degraded,0/8 acceptance.
No continuation launched. Action/physical contract unchanged.
The height-independent2000-update continuation stopped at498updates; the
yaw-only test improved yaw but achieved0/8 full acceptance. Current task is
[BC gradient / annealing A/B](docs/STANDING_BC_AB_20261006.md) completed206transferred
updates: less yaw with annealing, more drift,0/8 acceptance. See STATUS/review.
No automatic follow-up.

The separate frozen STAND model is scratch update500 (8/8 independent10s
standing acceptance), not B200 or Gym47250. It is not the current training
source or the source-retention teacher. Later bottom-down Recovery/handover
work must independently verify the low-pose initialization and5s STAND
takeover; R0 near-standing success does not certify that task.

## Historical project setup

The paragraphs below describe earlier setup/authorization. Resolve current
model, task and permissions from STATUS and the corresponding immutable run evidence.

Current authorized standing chain uses
[stand_long_20261001/spec.json](configs/experiments/stand_long_20261001/spec.json).
Follow [STATUS](STATUS.md) to its independent ledger and real run. Shared code
handles adaptive6/10/20/30s episodes; no command_v7 code tree was copied.
The remaining preparation descriptions refer to the original project setup.

This is the **one current native closed-chain training project**. It uses the
colleague's immutable closed-loop USD and a physical `Plane` ground collider.
The current task is zero-command standing at `[vx, yaw, height] =
[0, 0, 0.363]`. The source is native B200, expanded from 22D/110D/132D to
25D/125D/150D without replacing its learned actor or critic weights. This is
not the Gym 47250 virtual-leg migration and not a resumption of `command_v6`
formal training.

Read [AGENTS.md](AGENTS.md), [STATUS.md](STATUS.md),
[ARCHITECTURE.md](ARCHITECTURE.md), the
[current spec](configs/experiments/stand_plane.json), then
[TOOL_INDEX.md](TOOL_INDEX.md). [Reuse decisions](docs/REUSE_DECISIONS.md)
identify what comes from the colleague project; [experiment plan](docs/EXPERIMENT_PLAN.md)
separates source regression, the new plane/height standing recipe, and later
motion stages. The [source B200 recipe](configs/contracts/source_B200.json)
keeps the old mesh/0.35 m identity separate from the new experiment. The only writable current budget is
[budget.json](configs/experiments/budget.json), presently unapproved.
[Changed files and provenance](docs/CHANGED_FILES.md) identify the carried
kernel and every new project file.

Before designing or changing rewards, curricula, training experiments,
candidate selection, or acceptance, read [TRAINING_EXPERIENCE_REUSE.md](TRAINING_EXPERIENCE_REUSE.md).
Actual runs are governed by their spec, manifest, and raw evaluations.

Code is under `src/native_stand/`: the small source physical environment,
the audited v6 pure domain/ledger/trainer kernel, and an explicit plane scene.
The retained `command_v6` package name identifies the reused kernel, not a
new `command_v7` experiment. A new experiment changes a spec, not another
copy of the Python tree. Run artifacts go only under `runs/`; none have been
created by this preparation.

The [historical audit](/home/kellen/wheel_leg_migration_audit/) still contains
v1-v6 runs, the separate Gym-to-Lab migration, and 47250 sim2sim evidence.
Their old Markdown pages are historical snapshots; do not treat their budgets
or model labels as this project's current state.

````

## STATUS.md

````markdown
# Status

## 公共工程流程补齐 — 2026-10-08

[实现/用法/证据](docs/ENGINEERING_WORKFLOW_COMPLETION_20261008.md)：统一冻结CPU副本验证、
终态事件审计、时间轴、source/milestone/final/CLI/batch保存计划、三类计数摘要及
Recovery/reward205叶子effective披露；未核验消费者明确列出，不伪称运行生效。
全量CPU528 passed，冻结验证25项通过、零写plan；P1旧formal只读事件审计/账本一致。
旧18入口引用/guard全部审计，保留历史复现；无删除、仿真/PPO、通知或活动快照变更。

## 通知与证据接口修复 — 2026-10-08

[核查与修复](docs/NOTIFICATION_EVIDENCE_FIX_20261008.md)：049380...通知按历史manifest目标
投递到967b73ed...，不是已证明的随机路由错误。新增route一致性拒绝，未转发/重发。
评分与调度/保存调用边界分开；完整hold失败语义、持久tensor、raw loader、并列诊断候选、
entrypoints与未授权Recovery重试计划补齐。CPU522 passed；历史retry零写plan通过。
未仿真/PPO、未改活动冻结副本/旧账本；公共时间轴/统一保存计划/三类计数摘要仍未完整。

## Recovery P1完整执行完成 — 2026-10-08

事件a3ad42500f31c87c5166606a已去重复盘。23_29链COMPLETED，smoke20+formal100，总983040样本、31.41分钟；工程链路通过。new50/new100高度/姿态/限矩改善但连续双轮接触仍失败，完整0/8；自动best100，accepted=null。new50接触约99.9%，new100约94%，应保留并列候选。实际2–10秒训练覆盖已确认；未续训。见[完整复盘](docs/RECOVERY_MIN_HEIGHT_P1_COMPLETED_REVIEW_20261008.md)。

## Recovery P1原始诊断接线修复重试已提交 — 2026-10-07

用户“继续”授权独立23_29链；S50与原P1配方保留，source660秒、smoke20/899秒、formal100/7200秒，前三链累计上限9051.97秒。另在提交前修复统计张量跨inference rollout/reset生命周期风险。CPU516、冻结60 passed，plan PASS；共享GPU0，唯一supervisor一次握手SOURCE_EVAL，formal首更新未验证。见[执行记录](docs/RECOVERY_MIN_HEIGHT_P1_GUARDFIX_RETRY_20261007.md)。不轮询，不自动追加。

## Recovery P1第二次终态FAILED，来源评估已完成 — 2026-10-07

事件53acf4f6cdbc0c19ec7fd48c：23_04 source_eval完成134.57秒，DrawBack/R0均8/8有效初始化与入口、0/8完整接受；smoke在AppLauncher前因保护器误读删去控制轨迹的candidate摘要失败，PPO仍0更新。共享接线已改读身份核验的原始source JSON，CPU515 passed；未重试。见[复盘](docs/RECOVERY_MIN_HEIGHT_P1_GUARD_TERMINAL_REVIEW_20261007.md)。下方SOURCE_EVAL为历史启动握手。

## Recovery P1 reset修复重试已提交 — 2026-10-07

用户“继续”授权同配方独立重试，根2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50；source820秒、smoke20/900秒、formal100/7200秒，扣除旧链墙钟后累计≤9053.27秒。共享GPU0，未停止其他进程。CPU510、冻结54 passed，plan PASS；一次握手SOURCE_EVAL，后台提交身份核验通过，formal首更新尚未验证。见[重试记录](docs/RECOVERY_MIN_HEIGHT_P1_RESETFIX_RETRY_20261007.md)。不轮询，不自动追加。

## Recovery P1终态FAILED，已复盘 — 2026-10-07

事件0809b5e45005c37591bb8494：22_10链在source_eval切换R0 reset时发生inference tensor原地更新错误；source一次/70.26秒，smoke/formal均0更新，无新候选。共享RiseHold持久dwell存储已最小修复，CPU510 passed；旧冻结代码/账本不改，未重试。详见[终态复盘](docs/RECOVERY_MIN_HEIGHT_P1_TERMINAL_REVIEW_20261007.md)。下方SOURCE_EVAL为历史启动握手。

## P1新链已获批准并提交 — 2026-10-07

用户本轮明确批准source≤900秒、smoke≤20更新/900秒、formal≤100更新/7200秒，总120更新/983040样本；当前会话已绑定。独立根`runs/2026_10_7-22_10__recovery_min_height_p1_from_s50`。一次提交握手为`SOURCE_EVAL`，submitted=true、submission_verified=true；formal_first_update_verified=false，不声称formal已更新。共享物理GPU0，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，未抢占其他进程。授权后CPU509 passed、冻结副本53 passed、plan PASS。后台owner按预算执行并终态通知，交互worker不轮询、不自动延长。

[提交回执](artifacts/2026_10_7-22_10__recovery_min_height_p1/authorized_submission_stdout.json)及[授权记录](configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/authorization_receipt.json)。后文UNAUTHORIZED是准备时历史状态，实际状态以独立账本/manifest/终态为准。

## Recovery新高度P1准备，未授权 — 2026-10-07

已按最终RECOVERY_STANDING_PLAN第0–13节完成P0离线重评分；DrawBack全候选0/8、R0全组缺完整trace为UNKNOWN。默认S50无对齐成本。新v2有限10秒任务与平台高度reward已实现CPU验证，独立声明2026_10_7-22_10__recovery_min_height_p1_from_s50仍UNAUTHORIZED；未运行。详见[准备报告](docs/RECOVERY_MIN_HEIGHT_P1_PREPARATION_20261007.md)。以下旧运行结果保持原协议。

## Recovery弱轮心对齐已完成并复盘 — 2026-10-07

20_55链COMPLETED：smoke10+formal100，总110/901120samples，39.55分钟。
source/25/50/100均0of8，R0亦0of8；未跑durability。新100保持高度/接触100%，
仍roll.1092>.10、饱和83.81%；25/50/100均出现末5秒约50Hz轮力矩交替。
自动best50为失败排序并列后的SHA选项，不代表行为最优。无自动续训。
[终态复盘](docs/RECOVERY_LEVEL2_ALIGNMENT_TERMINAL_REVIEW_20261007.md)。下方启动状态为历史。

## Motion通用准备器工程验证 — 2026-10-07

[实现与用法](docs/MOTION_PREPARER_CONTRACT_20261007.md)。复用工作树已有authorization/session
契约及--check-submission；health共用规范化。新增通用Motion evaluation/单阶段course准备器，
显式parent/model/request/audit/GPU/session，默认零写，发布仅UNAUTHORIZED/零used/空attempts。
实际B250两模式CPU准备与supervisor plan正确拒绝未授权运行，对应run不存在。
本轮无AppLauncher、采样、optimizer或训练提交，未检查/迁移活动训练；其冻结代码不变。
独立fixture覆盖身份/差异/预算/失败清理/真实CLI无Isaac，最终验证见报告。

## Recovery对齐新授权重提 — 2026-10-07

新spec：[20_55](configs/experiments/2026_10_7-20_55__recovery_level2_alignment_from50/spec.json)。复盘和配方不变，协议字段接线已修。
新独立source600s、smoke10/600s、formal<=100/3600s；旧20_42失败/零PPO账本保持。
GPU0 shared；485 CPU passed、supervisor plan PASS/health OK/零写入。
已提交并核验一次握手：submission_verified=true，SOURCE_EVAL，formal_first_update_verified=false。
worker3673383、exact attempt30710f982235429290d336d933414aa3，argv/start/spec/output/GPU/session匹配。
提交时资源核验shared/preemption=false；后台owner执行后续阶段，交互不轮询。

## Recovery对齐短训终态更正 — 2026-10-07

2026_10_7-20_42__recovery_level2_alignment_from50已FAILED；source_eval1，smoke0，formal0，PPO0。
失败为full_trace_updates新增保存字段未纳入评分协议白名单，不是行为验收失败。
共享代码修复及CPU回归另记，不重写冻结证据、不自动重提。
下方SOURCE_EVAL/已提交是历史握手记录，不能当当前运行状态。见[失败复盘](docs/RECOVERY_LEVEL2_ALIGNMENT_20261007.md)。

## Recovery Level2弱轮心对齐已准备 — 2026-10-07

[事件/配方复盘](docs/RECOVERY_LEVEL2_ALIGNMENT_20261007.md)，[新spec](configs/experiments/2026_10_7-20_42__recovery_level2_alignment_from50/spec.json)。
用户批准source50单变量高度门控轮心成本：-.1、deadband.04、scale.20、gate.32–.36。
8env先错位>40cm，随后高度出下限，再失触；评分窗口复算一致，因果仍待干预。
独立source600s/PPO0、smoke10/600s、formal<=100/3600s、总110/901120samples。
25/50/100全评估保存全轨迹；GPU0 shared，不停止其他任务、不自动扩展或重试。
已通过supervisor提交：submission_verified=true，SOURCE_EVAL，formal_first_update_verified=false。
一次握手核验worker3658116、exact attempt9236c584719e44198cdfda2a0bae570f，argv/start/spec/output/GPU/session匹配。
474 CPU passed，plan-only PASS且零写入；后台owner负责后续阶段，交互不轮询。
下方20_17提交已COMPLETED/PPO0/0of8保持，无fault。

提交契约工程复验：[authorization/session 修复](docs/SUBMISSION_CONTRACT_FIX_20261007.md)，CPU 466 passed；未启动仿真、未查训练进度。本轮只提交文档，代码修复尚未提交。

新会话操作入口：[CODEX_START_HERE](docs/CODEX_START_HERE.md)。本页各条运行状态属于记录时刻，最新事实以对应 run 的原始证据为准。

## Motion B250 ±2.5有界课程扩展 — 2026-10-07

[来源复核与启动报告](docs/2026_10_7-20_29__motion_b250_2p5_short_REPORT.md)。
PPO0来源双向完整评估COMPLETED/417.317s：+2.5实际+2.9016、MAE.4016；
-2.5实际-2.8431、MAE.3434，各0/8，仅hold_absolute_error失败，方向/接触/物理检查通过。
来源B250 SHA5d3389d5...未变；原始逐环境证据在runs/2026_10_7-20_18__motion_b250_endpoint2p5/baseline。
用户授权的条件短训已提交GPU1独占、冻结执行副本；[spec](configs/experiments/2026_10_7-20_29__motion_b250_2p5_short/spec.json)。
总新增在线上限100=smoke1+formal99，检查25/50/75/99全11命令；不解锁±3或yaw，不进入长训。
一次5s握手submission_verified=true，worker3641776，chain exact attempt983eb74c8c3c4e66ad6540dda423f35f；
启动阶段SOURCE_EVAL，formal_first_update_verified=false。此为启动事实，后续进度/终态以run/ledger为准。
后台owner自动执行旧端点前置回归、smoke、formal、retention和结算通知；worker不轮询。
CPU438通过、实际spec回归和plan-only PASS；历史motion账本去重已用5293，保守剩余4707，新链未重置旧余额。
本轮未修改共享训练代码/Recovery/旧证据；零/±.5宽度.04，其余1.0，原PPO/reward/物理保持。

## Diagnostic Profile Engineering — 2026-10-07

[时长/profile/诊断准备器](docs/DIAGNOSTIC_PROFILE_FIX_20261007.md)：Recovery batch
统一任务时长，summary/failure_tail/full_transition显式保存scope，冻结checkpoint
诊断准备默认UNAUTHORIZED/PPO0。CPU441项、语法133文件通过。
update50原spec只读plan解析23秒/100Hz及四类字段，BUDGET_EXHAUSTED仍拒绝运行，
无新output、spec/ledger SHA未变；未补采、未改后台冻结评估或控制/PPO。

## 冻结update50完整几何PPO0已提交 — 2026-10-07

[补采声明](docs/RECOVERY_UPDATE50_GEOMETRY_PPO0_20261007.md)，
[当前spec](configs/experiments/2026_10_7-20_17__recovery_update50_geometry_ppo0/spec.json)。
用户同意，固定18_06 update50/DrawBack/currentUSD/seed104，8env×23秒一个请求，
完整geometry/posture/contact/control；单次<=600秒、PPO0，不训练/加惩罚/制动。
438 CPU passed、plan-only PASS；通过supervisor --evaluation-only提交，
提交预约不代表已完成，后台owner结算/终态通知，交互不轮询等待。

## 剪刀腿材料/轮delta离线核查 — 2026-10-07

[复盘](docs/RECOVERY_SCISSOR_REFERENCE_REVIEW_20261007.md)：已读取参考文献2，
区分轮心纵向偏置与腿长/关节镜像。env0离线USD采样new50末段约20.7cm、
new100约17.5cm（root-local/branch假设，非runtime水平支撑认证）。
wheel delta每步17.65/11.53rad/s却贡献约-.0000741/s，history源码顺序未见错误；
没有完整actor输入，runtime history仍未认证。不直接加惩罚/软制动/改Kv。
下一步冻结update50 PPO0补完整geometry的提案待预算；本项无模拟/PPO。

## update50/100轮控制离线诊断 — 2026-10-07

[时序复盘](docs/RECOVERY_WHEEL_TIMELINE_REVIEW_20261007.md)：用户批准离线核查，
新目录isolated/recovery_wheel_timeline_20261007/audit.json绑定原始SHA，未模拟/PPO。
new100末5秒8env两轮每policy步反转，499次/轮，约50Hz；各轮50%触限，any100%，
applied=physical_clipped，raw wheel action无归一化裁剪。不是恒定单向轮饱和。
new50末5秒无轮饱和/反转、接触gate100%；评分窗口中镜像偏差与失触相关，
但完整height/腿长trace缺失，事件因果UNKNOWN，不能先决定加腿长惩罚。
GUI认可new50保留候选；不从100续训、不加制动/改限矩，无新训练预算。

## Level2水平成本对照已获授权 — 2026-10-07

用户明确批准[prepared spec](configs/experiments/2026_10_7-18_06__recovery_level2_settle_cost_probe/spec.json)。
独立账本AUTHORIZED、使用0，来源旧update1000/原DrawBack/当前限位USD；
pitch/roll成本-4→-1、评估control轨迹开启，其他训练参数与验收门槛保持。
source_eval<=600s/PPO0、smoke10/<=600s、formal<=100/<=3600s；累计110/901120samples。
当前session匹配、GPU0共享；不停止其他进程，不续用旧额度，不自动重试或扩展课程。
授权后plan-only PASS、health无finding；实际提交阶段以一次握手为准，不轮询等待。
437 CPU passed；一次5秒启动握手submitted/submission_verified=true、SOURCE_EVAL。
worker3490652身份argv/start/spec/output/GPU/session匹配；chain exact attempt
803c92b92d4349d7b42d176225ffcd83。formal_first_update_verified=false，
started=false：只是来源评估阶段已提交，不能宣称正式PPO开始或能力通过。
后台owner负责后续证书/评估/终态和当前session通知，不在交互中轮询或自动续训。

## Level2收稳诊断与准备 — 2026-10-07

[复盘与修复](docs/RECOVERY_LEVEL2_TRANSITION_REVIEW_20261007.md)。Level2已COMPLETED，
未续训。offline source/new100阶段分析显示source快速越过高度区后过高前倾，
new100更水平但高度区间任意通道限矩比例约99.6%，最后倾角终止；因候选无完整
控制轨迹，逐通道原因UNKNOWN，不把大reward成本当已证明的因果梯度。
报告字段明确无入口/保持不完整，未来起身排名不以失败前存活/最高高度主导。
下一[准备spec](configs/experiments/2026_10_7-18_06__recovery_level2_settle_cost_probe/spec.json)
同旧1000/DrawBack/newUSD，水平成本幅度-4→-1，评估补控制轨迹；ledger UNAUTHORIZED。
CPU/plan另记；本轮未AppLauncher/PPO、未覆盖历史证据或停止其他进程。
验证：437 CPU passed、git diff --check通过；新supervisor plan-only为
READY_NEEDS_AUTH，仅缺新预算授权，新run目录不存在。未运行模拟或PPO。

## Recovery Level2 DrawBack迁移 — 2026-10-07

用户GUI确认原manual0001收腿姿态，并授权旧update1000迁移到当前限位USD后开启Level2。
[配方](docs/RECOVERY_LEVEL2_DRAWBACK_20261007.md)，
[当前spec](configs/experiments/2026_10_7-17_21__recovery_level2_drawback_from1000/spec.json)。
新family drawback_manual0001 60%+R0 40%，不是上一轮Swing family R1。
strict恢复旧actor/critic/Adam，source_asset/current_asset分别记录；height目标.40→.36。
新USD组合后属性仅两个knee限位差异，初态全部在界内/闭链2.72e-7m。
436 CPU passed，source plan-only PASS、health无finding；一次5秒握手已完成：
submitted/submission_verified=true、state=SOURCE_EVAL、formal_first_update_verified=false。
chain attempt466326fc210242bb8abfbbc080672e49、worker3438448；argv/start/spec/output/
session/GPU身份匹配。只是来源评估阶段的启动证据，不是formal启动或抬升认证。
遵守新版detached规则，交互不再轮询等待；后台owner负责证书、后续阶段和终态通知。
不使用上一轮update100，不继承初始化已验证标记，不复用旧预算；关闭未认证旧actor BC。
预算source600s/PPO0、smoke10/600s、formal<=100/3600s，累计110/901120samples。
source→smoke→formal受独立证据与两family事件证书约束；准备不代表formal已启动。
上一轮16_18 formal已COMPLETED100更新，低位0/8、R0在100次为0/8因roll；不续训。

工程摘要入口：[ENGINEERING_STATUS](docs/ENGINEERING_STATUS.md)。最近完整CPU验证为
435项通过；下面415/423等数值属于对应阶段历史检查，不相互替代。
本次仅文档/版本整理，未查看进程或轮询训练日志；下方启动记录不证明当前存活。

## Episode / Identity / Recovery Engineering — 2026-10-07

[本轮接口修复](docs/EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)：EpisodeSummary v1、
声明/执行源码身份分离、per-pose事件摘要、holding/rising身份及受限零写恢复plan。
CPU435项通过，127个Python文件语法通过；真实冻结preflight子进程未导入Isaac。
原15_58失败证书仅做一次离线plan，15项输入绑定、历史SHA未变，未发布新配置、
未恢复PPO或追加预算。下方运行记录原样保留，本工程验证不判断当前任务存活。

## Recovery自主低位起身 — 2026-10-07

现行正式阶段根：`2026_10_7-16_18__recovery_rise_formal_from50`，
[spec](configs/experiments/2026_10_7-16_18__recovery_rise_formal_from50/spec.json)。
15_58链source与smoke均COMPLETED，smoke实际10更新，无runtime fault，R0回归8/8；
但冻结证书读取completed_episodes而实际producer写completed，误报事件缺失并阻止formal。
550个已完成episode、最长2.18秒的原始证据均保留；修复读取后phase owner在新目录
生成corrected_smoke_certificate.json/PASSED，原FAILED证书不改写。
新ledger完整导入source1/smoke10使用与原exact-ID记录，formal仍0/<=100，累计110不变；
导入attempt按ID去重，不能跨账本重复累计。original failed证书仍阻止旧链再次formal。
423 CPU passed；formal-only plan PASS，来源/smoke预算已耗尽与未起身属于既有事实，
不是formal身份阻塞。已通过公共supervisor提交formal-only，首更新证据另记。

formal单次握手已验证：RUNNING/actual_updates1、identity_verified=true、started=true；
exact attempt `b6ae54f673d7480f93988c6511a79345`，trainer3359946、monitor3359944。
握手文件runs/2026_10_7-16_18__recovery_rise_formal_from50/formal/handshake.json；
此为当前argv/start/spec/output/attempt匹配的首更新证据，不能凭PID推断后续存活。
后台monitor负责后续评估/结算/通知；不再会话轮询训练日志，不自动续训。

当前提交根改为`2026_10_7-15_58__recovery_rise_low_from50`：原15_51链在AppLauncher
之前被strict源码根检查拦住，原attempts空/used全0，保留FAILED证据，不修改旧链。
合法冻结worker现在通过提交receipt逐文件SHA验证，未关闭strict身份检查。
422 CPU passed，新source plan-only PASS/health无finding；新spec记录原失败证据SHA，
原定总110更新上限不变。已通过supervisor提交，首更新证据另记；本段不代表已训练。

新15_58链来源阶段已COMPLETED/PPO0/failure=null：低位8/8有效初始化、fault0，
新起身证书0/8；retained R0在事件协议下8/8。smoke阶段已观察实际3更新、
actor_parameters_changed=true。正式首更新与smoke持久证书仍待后台owner验证，
不能据此称已学会起身或formal已经开始。

用户批准[新起身方案](docs/RECOVERY_RISE_LOW_20261007.md)。新独立spec：
configs/experiments/2026_10_7-15_51__recovery_rise_low_from50/spec.json；
run根runs/2026_10_7-15_51__recovery_rise_low_from50。
source50、低位family R1 60%+R0 40%，不自动晋级；10smoke+<=100formal，
总<=110updates/901120samples。source<=600s、smoke<=600s、formal<=3600s。
23秒事件对齐评估，起身<=11.5秒后完整保持10秒；不启用100秒durability。
PPO0定位已COMPLETED：runs/2026_10_7-15_46__recovery_rise_source_locator，
三个请求完成，零PPO；两个新中间姿态初始化被拒绝，未纳入训练；
已有低位8/8有效，source约0.23m后倾角失败。未将定位standing gate当起身认证。
CPU420项通过（后续增量检查与启动状态另记），source plan-only PASS/health无finding。
运行事实以新run终态为准；本段准备状态不表示formal首更新已验证。

Coverage A/B两组均COMPLETED：A100为0/8因roll；B100为8/8。
两组best_new25、best_overall source50，durability NOT_RUN；不续训旧链。

## State / Request Engineering -- 2026-10-07

[本轮接口修复](docs/STATE_REQUEST_FIX_20261007.md)：共享链RunState、Motion/Recovery
独立请求schema、历史CLI保护、集中命名及选定update覆盖诊断。
CPU415项通过，Python语法121文件通过，plan-only零输出、输入spec/ledger SHA不变。
未启动仿真/PPO，未改活动run冻结副本；旧独立A/B及Recovery历史链未追溯迁移。
以下coverage任务状态属于另一任务，原记录保留，不从工程验证推断其终态。

## Recovery Coverage A/B authorized -- 2026-10-07

source_capability COMPLETED/exit0/PPO0/329.2028s，R0与R1(family R0_perturbed)
seed104/205四项均8/8，总32/32、fault0。来源已具备本组R1初态能力。
A_first/B_uniform detached提交已核验，submitted/submission_verified=true，
current_stage=source_eval；formal首更新尚未在本启动记录中验证。
worker3225689/3225690，独立冻结run与账本，后台owner负责后续训练/终态，
不重复提交或自动追加系数实验。局部同输入离线报告：
isolated/recovery_coverage_ab_20261007/source_completed/review.json。

[新方案](docs/RECOVERY_COVERAGE_AB_20261007.md)：用户批准source50的R0/R1
PPO0双seed平衡初态复核与BC样本覆盖A_first/B_uniform受控对照。
配置根configs/experiments/recovery_coverage_ab_20261007，各独立spec/budget。
各组10smoke+<=100formal，合计<=220updates/1802240samples，仅BC选择方式不同。
CPU403passed、三项plan-only PASS；运行事实以新run终态为准。
GPU0共享已获明确授权，不停止任何其他进程，不重启旧hold10、不启用R1 PPO。

## Public Entry Consolidation -- 2026-10-07

当前工具与历史命令已拆分：TOOL_INDEX.md / TOOL_INDEX_HISTORY.md。
旧固定GPU/run/session的高速preparation runtime入口退役；三旧Motion
声明生成器默认拒绝，显式历史复现仍不得覆盖已有目录。新提交只走supervisor。
本轮仅工程修改与CPU核验，不生成新实验配方、不启动仿真或续训。
当前Motion来源建议仍是B250；旧报告早期new250建议已被最终复核替代。
全量CPU回归399项通过；详见docs/ENTRYPOINT_CONSOLIDATION_20261007.md。

## Entry Semantics Engineering -- 2026-10-07

[本轮局部修复与验证](docs/ENTRY_SEMANTICS_FIX_20261007.md)：明确资源共享授权、
模型角色、episode结果、event-sized smoke和单一certificate owner；默认首阶段
握手与formal首更新验证分开。只CPU检查，不启动/恢复/停止训练，不修改当前
Recovery冻结执行副本、ledger或历史raw评估。下方任务状态以各run终态为准。
CPU回归387项通过，113个Python文件语法检查通过；历史572项输入SHA未变化。
plan-only正确拒绝已耗尽预算（BUDGET_EXHAUSTED），输出目录未创建。

## Motion engineering/capability recheck -- 2026-10-07

[Motion独立任务](docs/MOTION_ENGINEERING_RECHECK_20261007.md)：新absolute_v3协议及工程接线修复。
本轮online/offline optimizer=0。GPU0被其他任务占用，未预留attempt；用户追加GPU1授权，
一次PPO0评估COMPLETED：9项各8/8通过，1942.31s含清理，在线/离线更新0。
来源B250的0/±1/±1.5/±2通过；new250的±1.5通过，B250误差更低。
CPU387 passed。来源B250与new250/new500路径/SHA分别绑定。
[机器结果](isolated/motion_recheck_20261007/final_gpu1/result.json)及逐项raw/terminal/ledger保留。
建议B250起点、待学±2.5；prepared v4账本UNAUTHORIZED，plan READY_NEEDS_AUTH。
不将旧trace重评分当作新训练收益，不续训；本任务评估已退出，未启动PPO。

## Authorized Recovery R0 Holding Experiment -- 2026-10-07

当前已完成复盘见[R0 hold10完成报告](docs/RECOVERY_R0_HOLD10_REVIEW_20261007.md)。
该复盘记录source/smoke/formal均COMPLETED，formal100更新；新100为0/8，
source仍优于新候选，不授权续训。以下RUNNING、PID与首更新内容仅为历史启动记录，
不能用于判断当前进程存活或模型能力；原始run证据优先。

Detached startup verified: source10s COMPLETED/PPO0/71.23455s,8/8 accepted,
no runtime fault. Smoke COMPLETED10updates/81920samples/136.21032s,
actor changed, wiring_certificate PASSED/errors[]. Smoke update8 recorded64
normal10.0s timeouts,0physical failures;64window certificates failed separately.
Formal single handshake RUNNING/actual1, identity_verified=true/started=true,
trainer3168977, worker3164611, attempt43e96c5cc5d846779640bbc3edefd3c2.
These are startup facts, not a completed100-update result. Shared GPU0 explicitly
allowed by current user; no other process stopped. Background monitor owns full
evaluations, terminal/accounting/report/current-session notification.
CPU351passed; plan-only PASS/health OK before AppLauncher. Runtime source/spec/asset
and frozen execution identities are in the new run. No conversational log polling
after the formal handshake, no extra PPO/automatic continuation.

Current user approved execution of [R0 continuous10s experiment](docs/RECOVERY_R0_HOLD10_20261007.md).
[Spec](configs/experiments/recovery_r0_hold10_from50_20261007/spec.json), independent
local budget.json; output runs/recovery_r0_hold10_from50_20261007.
Source scissor50 unchanged; success_once0, no early success reset, normal10s
time limit bootstraps via installed PPO. Full-window online certification,
R0 cap0, all continuous rewards/physics/PPO/BC unchanged.
source10s/PPO0 + smoke10 + formal<=100, total<=110updates/901120samples;
full evaluation25/50/100, no final100s or R1. CPU/preflight/runtime startup
are reported separately below or in the immutable run evidence. No automatic continuation.

## Version Control Handoff -- 2026-10-07

[Git workflow and submission scope](docs/GIT_WORKFLOW.md): the repository had no
prior commit; the first versioned baseline captures current files, not a restored
historical implementation. Source/tests/declaration configs, scripts and docs are
committed separately. Dynamic budgets, submissions, runs, binary assets and isolated
evidence stay local and unchanged. This handoff grants no simulator/PPO budget.
Current CPU engineering evidence:315tests passed;75files passed py_compile.
Actual runtime and capability still require the immutable run evidence below.

## Interface/evidence engineering update -- 2026-10-07

Followup [gap closure](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md): protocol
duration/gate identity, read-only health, strict certificate/submission prerequisites,
generic offline audit and default-off selected diagnostics completed CPU verification.
No simulation/PPO or historical authorization changes. Runtime verification remains
explicitly separate; current health findings do not authorize continuation.

[Changes and CPU/offline validation](docs/NATIVE_INTERFACE_EVIDENCE_20261007.md).
No simulation, online PPO, continuation or budget change. Historical run evidence
remains unchanged. Frozen offline Recovery100s rescore confirms actual [2,100]
posture scoring and8/8; its old serialized [2,10] description was incorrect.
New effective protocol/gate/diagnostics interfaces disclose actual scopes and
missing evidence. Old protocol results are not rewritten or newly authorized.

## Survival/level chain reviewed and stopped -- 2026-10-07

Current handoff: [Recovery context and evidence](docs/HANDOFF_RECOVERY_20261007.md).
Event `f19e69d28f8650f3f6ef342d`; chain completed its bounded workflow.
Formal stopped at200updates after two failed full evaluations, not10000updates.
Smoke3/formal200, total203PPOupdates; chain3075.77s. R0 remains active, R1 not sampled.
Source scissor update50 remains best:8/8 new survival/level10s acceptance.
New100 fails roll8/8; new200 has5tilt terminations and0/8 full acceptance.
Source100s result has8/8continuous survival; its posture gate still scores2-10s,
so it is not a full100s posture certificate. Report shows `gate=None` because
Recovery stores `recovery_gate`, while chain summary reads `standing_gate`.
These report/protocol issues are diagnosed, not yet repaired; raw results unchanged.
No new simulation/PPO authorized or started by this handoff. Historical startup below
is superseded by terminal evidence in `runs/recovery_survival_level_from50_20261006`.

## Survival/level R0 -> R1 running detached -- 2026-10-06

[Task](docs/RECOVERY_SURVIVAL_LEVEL_20261006.md),
[spec](configs/experiments/recovery_survival_level_from50_20261006/spec.json),
[ledger](configs/experiments/recovery_survival_level_from50_20261006/budget.json).
Source is GUI-approved scissor update50 SHA1fa4255a...; strict150D actor/critic/Adam,
LR3e-5, same mechanical-stop USD/plane/PD/action/effort limits.
10000totalupdates =3smoke+9997formal,81,920,000samples, conservative10h cap.
Objective:survival and level posture; motion/drift/symmetry diagnostic-only.
R0 confirmations then R1 near-standing with40% R0 retention; R2/R3 disabled.
58focused CPU checks plus80general regression checks pass, fresh preflight PASS.
Historical fixture failures are recorded in the task document, old outputs unchanged.
Source10s physically completed8/8 new-protocol acceptance,0PPO,100.72s,
height0.36667m/contact100%, no runtime fault; moving vx~0.704m/s remains diagnostic.
Smoke3actualupdates/24,576samples COMPLETED35.33s, actor parameters changed.
One formal startup handshake RUNNING/actual1, trainer2210972, worker2208166,
attempt700a9368fe7b4a90885bd978b476d7ce. Manifest SHA/spec/asset/source agree.
No post-handshake training-log polling or automatic new chain.
TensorBoard http://127.0.0.1:6013 HTTP200; smoke/formal JSONL viewers detached.
Process metadata: runs/recovery_survival_level_from50_20261006/tensorboard_processes.json.
Output: `runs/recovery_survival_level_from50_20261006`.
HAPI target6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1. See actual manifests/terminals.

## User-approved next source and revised goal -- 2026-10-06

User GUI accepts [scissor update50](runs/standing_scissor_20261006/formal/model_update_50.pt)
for **survival and level body posture**, without zero-speed/drift requirements.
SHA256 `1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`.
Existing evidence:8/8continuous10s, no runtime fault, mean height0.36667m,
dual support100%, mean abs pitch1.26deg/roll4.15deg. GUI approval is separate
from the old automated0/8 strict result, which remains unchanged.
Next: R1 enlarged near-standing perturbations with R0 retention; R2 is the
captured low pose. [Current plan](docs/RECOVERY_STANDING_PLAN.md) supersedes
the lower-weight comparison proposal below. New reward/success/promotion gates
must share the revised objective in a fresh spec before submission. No run,
spec, budget or physical configuration changed by this documentation update.

## Wheel alignment probe completed and reviewed -- 2026-10-06

Eventd5ef508a2c3c881de3e8c86b; [review](docs/STANDING_SCISSOR_EXPERIMENT_20261006.md#completion-review----2026-10-06).
All phases COMPLETED/exit0,53updates/434176samples,529.56s(8.83min), ledger agrees.
Source/final50 all8/8 continuous10s,0/8strict acceptance, no runtime fault.
Wheel fore/aft offset0.16685->0.08081m(-51.6%); mirror0.54709->0.25806rad.
Height0.36120->0.36667m, but abs vx0.06975->0.70411m/s,
excursion0.60005->6.26157m, roll0.000001->0.07234rad,
leg-length difference3.39->31.85mm. Final fails excursion/vx/yaw/roll/mirror/
leg_length in all8. Dual support100%, pitch/height/closure/sampled saturation pass.
Alignment improved at the expense of zero-motion and lateral posture; not accepted.
Best-by-existing-ranking remains source1500, accepted=null; latest is new50.
1140old unused updates remain unspent. No automatic continuation after review.
Next proposal: lower only geometry weight4fold on same-source controlled test;
do not raise it further or extend this branch unchanged. TensorBoard6012 history.
Observed report serialization bloat noted in review; raw evaluations preserved.

## Wheel-center alignment probe running -- 2026-10-06

Historical startup only; completed terminal above supersedes RUNNING.

User authorized [scissor probe](docs/STANDING_SCISSOR_EXPERIMENT_20261006.md).
Source1500 strict actor/critic/Adam, LR3e-5, fixedBC0.02, same yaw recipe.
Only added longitudinal wheel-center cost,3cm deadband;15cm ->-.03/step.
PPO0 source10s/120s cap ->64runtime/FK samples<=2mm ->3smoke/300s ->50formal.
53updates/434176samples transferred;1140unused old updates remain unspent.
No extra actual budget; no100s durability in this controlled50-update probe.
53focused CPU tests pass; source preflight PASS. Output runs/standing_scissor_20261006.
Runtime geometry gate PASSED64samples, peak center mismatch0.235mm<=2mm.
Source10s COMPLETED/exit0/PPO0/61.67s; actual source wheel offset mean0.16685m.
Source0/8strict acceptance is a behavior baseline, not wiring failure.
3smoke COMPLETED/exit0/26.71s. One formal handshake RUNNING/actual1,
worker2148333, trainer2150267, attempt8e627a44c4d640ae846461564df56e5e.
TensorBoard http://127.0.0.1:6012 HTTP200. No post-handshake log polling;
background monitors settle/report/notify current confirmed HAPI session once.
These are startup/readback facts, not learned alignment or acceptance claims.

## Scissor geometry offline check -- 2026-10-06

[Review](docs/STANDING_SCISSOR_REVIEW_20261006.md) and
[raw reconstruction](runs/standing_bc_ab_20261006/scissor_geometry_review.json).
96saved training input reconstructions using current USD closure all valid.
Sampled A/B rollout100 wheel longitudinal offset means0.17549/0.17377m;
sagittal leg-angle differences0.57208/0.56659rad. This supports observed
scissor geometry; not a full holdout measurement or proof of static stability.
R0 reset is near-symmetric; no large opposing-leg randomization found.
Actual A100height/support/mirror weighted means +0.02989/+0.005/-0.00148.
Next best single-variable candidate is wheel-center longitudinal geometry cost,
after actual pre-reset runtime readback agrees with offline reconstruction.
New standalone offline tool and4CPUfixtures pass; no new PPO or physics,
no reward/spec/asset/budget changes. Existing1193unused allowance stays unspent.

## BC A/B completed and reviewed -- 2026-10-06

Event74c16b14abeaebf3e9155986; [review](docs/STANDING_BC_AB_20261006.md#completion-review----2026-10-06).
Pair/all six phases COMPLETED/exit0,206updates/1,687,552samples,1890.95s(31.52min).
Both arms source1/smoke3/formal100 charged exactly;1193old updates remain unused.
Source,A50/A100,B50/B100 all8/8 continuous10s,0/8 full acceptance, no runtime fault.
A100/B100: root0.35803/0.35821m, abs vx0.07369/0.08638m/s,
abs yaw0.08020/0.04288rad/s, excursion0.65689/0.78844m,
mirror0.56877/0.55992rad. All8fail excursion/vx/yaw/mirror; other gates pass.
BC annealing improves yaw but worsens drift, not a symmetry/stability solution.
A weighted BC/PPO first-minibatch norm average0.154%, leg contribution0.0254%;
directional conflict observed but BC dominance unsupported. B51+actualBC=0.
Next priority: offline mirror geometry/sign and reward-signal audit on saved
states before full mirrored BC. Wheel-only BC is not automatically submitted.
Callback sent once; this review starts no simulation/PPO, changes no recipe,
and resets no budget. TensorBoard6011 retains A/B evidence.

## BC gradient / annealing A/B running -- 2026-10-06 20:02 CST

Historical startup facts; completed terminal above supersedes RUNNING.

Current task: [BC A/B plan](docs/STANDING_BC_AB_20261006.md).
Source/teacher update1500; same seed/Adam/LR3e-5 and yaw-only recipe.
A_fixed BC0.02; B_annealed cosine to zero from formal51. Each arm source10s,
3smoke+100formal;206updates/1,687,552samples transferred, no added allowance.
Old ledger has1193unused updates.63focused CPU/fake-process checks pass;
both source preflights PASS. Output `runs/standing_bc_ab_20261006`;
manifest/handshake/terminal govern state. No automatic wheel-only/mirror BC.
Source0/8 strict acceptance; gradient conflict awaits actual measurements.
Estimated32-40min; formal strict update/sample cap, no wall cap.
Detached one startup handshake confirmed A_fixed formal RUNNING/1actual update,
trainer2046440, worker2044513, attempt8fb5cdf7891c4b30a6516e0708e384dc.
A source10s/61.03s and3smoke/26.68s completed before formal, exit0.
[Smoke gradient evidence](runs/standing_bc_ab_20261006/A_fixed/gradient_smoke_review.json):
update1teacher=student gives zero BC gradient; update2/3 cosine-0.106/-0.302,
but weighted BC norm is only0.0108%/0.0229% of clipped PPO actor norm.
Leg/wheel directions both oppose in these probes; BC is not established as
the principal cause. Scope is first minibatch, PPO+entropy composite.
TensorBoard http://127.0.0.1:6011 HTTP200, readonly A/B smoke/formal viewers.
No log polling after handshake. Background finishes both arms and notifies
session6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 once.

## Yaw-only100-update test completed and reviewed -- 2026-10-06

Eventa9a468f94c2254234fa81ea8; [report](runs/recovery_standing_yaw_20261006/completion_report.md)
and [review](docs/STANDING_YAW_REVIEW_20261006.md#completion-review).
Source/smoke/formal all COMPLETED/exit0, no terminal/accounting conflict.
3smoke+100formal=103updates/843,776samples; chain971.83s(16.20min).
Formal819,200samples,872.53s; no automatic continuation authorized.
Source/yaw50/yaw100 all8/8 continuous10s,0/8 accepted, no runtime faults.
Source->yaw100: abs yaw0.12165->0.08020rad/s(-34.1%), height0.36120->0.35803m,
abs vx0.06975->0.07369m/s, excursion0.60005->0.65689m,
mirror0.54709->0.56877rad. All8fail excursion/vx/yaw/mirror; level/contact/height/
closure/saturation pass. Accepted=null; source1500 is automated best by existing
drift-prioritized ranking, not uniformly best; yaw100 has better yaw/pitch.
Latest yaw100 SHAbe0dc90b235e8ae95c8d37de8a42295b9ca8aef4818d195c764724dded6e53f4.
Formal rollout748.20s/PPO4.88s/eval114.10s/write0.78s; eval13.1% of phase wall.
Rollout1094.9samples/s, end-to-end938.9samples/s.
New103-update quota consumed; old1399unused updates remain unspent, no resume.
Next diagnostic priority: inspect symmetry objective versus frozen-source action
retention on identical actual inputs; potential conflict is not a confirmed cause.
No new simulation/PPO/model/reward changes during this completion review.

## R0 yaw-only controlled continuation -- 2026-10-06

Historical submission details; now completed, see reviewed terminal above.

User agreed stopping the deteriorating branch, channel-level diagnosis and one
yaw-only intervention. [Review](docs/STANDING_YAW_REVIEW_20261006.md),
[new spec](configs/experiments/recovery_standing_yaw_20261006/spec.json),
[new ledger](configs/experiments/recovery_standing_yaw_20261006/budget.json).
Previous long run finalized STOPPED_BOUNDED/exit0 at498updates/4,079,616samples.
Update400 PPO0 two-second diagnostic confirms right-wheel35.5% saturation,
left-wheel0.5%, four leg channels0% in100Hz samples; no runtime fault.
New task adds only canonical-Y yaw Pseudo-Huber(-0.8,scale0.35) to existing costs.
Source remains update1500 with strict Adam/LR3e-5; update250 is comparison evidence.
103remaining updates transferred:3smoke+100formal,843,776samples, no formal wall
limit. Full10s at50/100, no100s durability or automatic extra training in this test.
Output `runs/recovery_standing_yaw_20261006/`; manifest/progress/terminal govern
actual state.55focused CPU checks pass; source preflight PASS before submission.
Detached formal handshake confirmed RUNNING/1actual update, trainer1888487,
worker1886759, formal attempt49452a90371940f1bae7c6509bf909e6. Source and3smoke
completed before formal. Startup facts only; no post-start training polling.
TensorBoard comparison: http://127.0.0.1:6010 (previous versus yaw_only).
Old6009 retains stopped-run history; new events arrive after the first smoke update.

## R0 height-independent long training authorized -- 2026-10-06

Historical authorization: this run is now stopped at498updates; see above.

User explicitly authorized2000formal updates, no wall-clock limit.
[Current spec](configs/experiments/recovery_standing_level_v2_long_20261006/spec.json)
and [exact ledger](configs/experiments/recovery_standing_level_v2_long_20261006/budget.json)
permit16,384,000new samples (64env x128steps). Output:
`runs/recovery_standing_level_v2_long_20261006/formal/`.
Read that run's manifest/progress/terminal for actual runtime state.
Source remains native update1500; target0.36m, R0 only. Height-independent
pitch/roll/settling constraints and source-retention scope were verified in the
completed bounded run below. Its immutable source/smoke evidence is referenced,
not rewritten or charged a second time. Ordinary behavioral failure is not a
formal-start blocker; runtime faults and frozen regression stops remain active.
CPU:38focused tests passed; formal plan-only preflight PASS.
Detached startup handshake confirmed RUNNING with1actual update,
trainer PID1797484, monitor PID1797483, attempt48e363397d8a4728b67b9afd139f42ed.
These are startup facts, not a continuously polled runtime status.
Checkpoint every100; light evaluation every100; full10s every250 and final.
TensorBoard for this run: http://127.0.0.1:6009 . Reports and one completion
notification target current HAPI session6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1.
No interaction polling or automatic continuation after completion.

## Height-independent bounded verification completed — 2026-10-06

Current report: [standing_level_v2_check_20261006_151025](runs/standing_level_v2_check_20261006_151025/completion_report.md).
Authorized source10s +3smoke + candidate10s completed;3actual PPO updates,
24,576samples,216.52s physical wall including cleanup of900s maximum.
Source/candidate both8/8 continuous10s, no runtime fault, both0/8 strict acceptance.
Source versus smoke3: height0.36120->0.36247m, mean abs vx0.06975->0.10333m/s,
yaw0.12165->0.11361rad/s, mirror0.54709->0.53024rad,
mean maximum excursion0.60005->0.90763m. Contact100%; sampled deterministic
saturation0.1%. Both fail excursion/vx/yaw/mirror; pitch/roll and height pass.

Finite loss, actor changed, actual LR3e-5,256retention samples/update verified.
Training stochastic saturation33-35% is not the same statistic as deterministic
evaluation saturation. No completed PPO episodes or128-episode curriculum window
in3updates; no convergence claim. Source1500 remains best observed; accepted=null.
[Ledger](configs/experiments/recovery_standing_level_v2_20261006/budget.json)
used source1/evaluate1/smoke3/formal0; formal allowance0 blocks long training.
The historical spec's500formal updates were a proposal at verification time.
The separate authorization/spec above supersedes that pending decision.
Next recommendation: separately authorized100-update controlled test with50/100
independent comparisons, rather than immediately using thousands of updates.
HAPI completion event4159bd535923366cb9939eee was sent once to the confirmed
current session; notification does not authorize continuation.

## Standing chain stopped; height-gate repair prepared — 2026-10-06

User requested stopping [recovery_standing_balance_20261006_chain_1140](runs/recovery_standing_balance_20261006_chain_1140/).
Formal terminal and exact ledger agree:1189updates/9,740,288samples,
STOPPED_BOUNDED,exit0,stop_kind=user_signal. Smoke adds3updates/24,576samples;
total1192updates/9,764,864samples. Chain wall11348.03s (~189.1min).
8808formal updates remain in the old ledger; user stop is not authorization to reuse them.
The historical wrapper labels its chain COMPLETED despite user stop; preserved
as evidence, not a training/behavior success. No accepted continuous10s candidate.

Current entry: [height-gate review](docs/STANDING_HEIGHT_GATE_REVIEW_20261006.md).
Prepared [v2 spec](configs/experiments/recovery_standing_level_v2_20261006/spec.json)
and [new ledger](configs/experiments/recovery_standing_level_v2_20261006/budget.json)
were initially UNAUTHORIZED; the bounded verification authorization and final
usage are recorded above. The new R0 recipe makes standing/settling/pitch/roll
costs independent of height, zeros upright contribution, and widens source
retention inputs to0.30-0.40m. Source remains update1500, not latest1189.
Other weights, USD, plane, PD, limits, action, PPO and acceptance are unchanged.
Preparation preflight was READY_NEEDS_AUTH/cpu_valid; bounded runtime is now complete.
Detailed CPU results, reward probes and remaining runtime checks are in the review.
Verification:81 focused CPU/fake-process tests pass; full suite183pass/10fail.
Remaining failures depend on historical external YAML identities, a live occupied
motion ledger, or snapshot-specific test entry/consumed authorization. They are
listed in the review; full-suite green and runtime success are not claimed.

TensorBoard6008 retains this stopped chain's history. Read terminal/ledger for
state; neither old PIDs nor an open TensorBoard implies active training.

## Symmetry continuation completed -- reviewed 2026-10-06

[Review](runs/recovery_symmetry_from1500_20261006/REVIEW_20261006.md): formal
COMPLETED, exit0, 500updates/4,096,000samples/61.96min; smoke3 additional
updates. Independent new500 evaluation is0/8: all8env survive15s then
recovery_timeout, no runtime fault. Last2s mean abs vx0.416m/s exceeds the
0.30m/s gate; height0.3576m, contact99.90%, tilt~0.020rad remain good.
Gated symmetry error improves temporarily then regresses. Do not replace
the old accepted2s update1500 with new500; updates100-400 remain unreviewed.
No automatic continuation authorized. The original run contains a preparation
accounting discrepancy: requested500updates, submitted smoke3+formal500;
total usage503updates/4,120,576samples is preserved and documented.

Detached run `runs/recovery_symmetry_from1500_20261006` used
`model_update_1500.pt` (SHA256
`c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82`) and
changes only the high-height-gated `leg_symmetry` reward from `-0.08` to
`-0.20`. The USD, Plane, controller, action contract, limits, curriculum and
learning rate were unchanged. The submitted ledger allocated3smoke and500formal
updates; both completed. TensorBoard bridge output is under the run's
`tensorboard/` directory. Old startup PIDs are historical identities only.

## R0 standing at 0.36 m completed -- 2026-10-06 02:14 CST

Latest review: [REVIEW_20261006.md](runs/recovery_stage0_stand_from1000_20261005_chain/REVIEW_20261006.md).
Formal is STOPPED_BOUNDED, exit0:1954updates/16,007,168samples/~239.1min;
smoke3updates. [Ledger](configs/experiments/recovery_stage0_stand_from1000_20261005/budget.json)
settled exactly;46formalupdates remain, no automatic continuation authorized.
[Frozen spec](runs/recovery_stage0_stand_from1000_20261005_chain/formal/source_snapshot/spec.json)
uses command[0,0,0.36], R0 near-standing only, automatic promotion disabled.

Offline checkpoint selection is recorded in
[checkpoint_selection_20261006.json](runs/recovery_stage0_stand_from1000_20261005_chain/formal/checkpoint_selection_20261006.json).
Among the independently evaluated checkpoints, update1500 is now the selected
candidate: 8/8 pass the **autonomous2s hold protocol**, with approximately
0.361 m final height, 0.022 rad peak tilt and 99.13% dual contact. The GUI
preview command is documented in [TOOL_INDEX.md](TOOL_INDEX.md).
Full saved evaluations1000 and1500 both8/8 pass the **autonomous2s hold protocol**;
episodes end at~2.2-2.3s. They do NOT certify continuous10s/100s standing,
low-pose Recovery or STAND handover. Update1500 has lower translation/tilt and
update1000 lower yaw; a new authorized PPO0 continuous10s test is still needed
before claiming long-duration standing. Latest1954 is unreviewed.
Selected update1500 SHA:c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82.

The horizontal-from900 run below is historical: ended1381updates at the3h bound;
its best-reviewed1000 had0/8 successes, not an accepted standing model.

## Horizontal stability continuation from update900 — 2026-10-05

本轮已按用户授权启动独立长训：
[`spec.json`](configs/experiments/recovery_horizontal_from900_20261005/spec.json)
和独立账本
[`budget.json`](configs/experiments/recovery_horizontal_from900_20261005/budget.json)。
来源为 `recovery_dense_corrected_chain_20261004/formal/model_update_900.pt`，
SHA256 `e61866d19946c10faaeff49fa6c457f2708f2e79400b425c9845b19faea51983`。

变量：自主成功速度门改为 `0.30 m/s`；增加高度门控 pitch/roll 水平奖励（权重
`-2`、scale `0.12 rad`）；settling linear/angular cost 加强为 `-0.15/-0.4`；
倾角成功门为 `0.12 rad`。plane、USD、1 ms physics、5 ms PD、10 ms policy、
40/5.5 Nm limits、25D/125D/150D 接口均保持不变。课程仍从 R0 零命令开始，
两次不重叠的128 episode窗口、每窗成功率≥90%、无 runtime fault 后才升级。

执行链：smoke 已完成 `3/3` 更新、`24,576` samples、finite loss、actor changed、
无 runtime fault；formal 已 detached 启动，最多 `1,997` 更新，合计上限 `2,000`
次 PPO 更新（总样本上限 `16,384,000`）。当前 formal 进程身份和账本以
[`runs/recovery_horizontal_from900_20261005/`](runs/recovery_horizontal_from900_20261005/)
为准。TensorBoard bridge 输出在该 run 的 `tensorboard/smoke` 与 `tensorboard/formal`。

## update900 PPO0 physical evaluation — 2026-10-05

独立评估已完成：
[`failure_summary.md`](runs/recovery_eval_update900_20261005_170935/failure_summary.md)
和逐环境原始结果
[`update900_eval.json`](runs/recovery_eval_update900_20261005_170935/update900_eval.json)。
原始 checkpoint
`recovery_dense_corrected_chain_20261004/formal/model_update_900.pt` 的 SHA256 为
`e61866d19946c10faaeff49fa6c457f2708f2e79400b425c9845b19faea51983`；PPO 更新为 0，
8/8 scored env 均完整运行到 15 s 后 `recovery_timeout`，0 runtime fault，accepted=false。
高度、倾角、双轮接触、闭链和底盘净空均通过对应安全门；已确认的主要失败项是末段
`|vx|≈0.305 m/s`，无法满足自主成功的三维线速度 `≤0.05 m/s`，因此稳定保持计时为 0。
旧快照未保存完整三维角速度范数，角速度门的独立判定仍为缺测。

## Recovery checkpoint review — 2026-10-05

离线筛选报告：[checkpoint_review.md](runs/recovery_checkpoint_review_20261005/checkpoint_review.md)。
按每个 checkpoint 前 100 次更新的训练统计，诊断候选为
`recovery_dense_corrected_chain_20261004/formal/model_update_900.pt`
（SHA256 `e61866d...51983`）；它只出现过 3 次完整成功，仍不是验收通过模型。
现有物理评估只有 update500/1000，均 0/8，故 `accepted_candidate=null`。旧产物没有
128 个 episode 的逐条终止字段，本轮没有新增 PPO0 物理评估。

## Recovery 训练链审计 — 2026-10-05

针对其他运动训练的退化复盘，已完成 Recovery 代码对照和 CPU 修复；详见
[RECOVERY_TRAINING_AUDIT_20261005.md](docs/RECOVERY_TRAINING_AUDIT_20261005.md)。
修复了 warm-start RNG 被无条件覆盖、评估 RNG 污染 PPO、Recovery reverse
curriculum checkpoint 不完整和 stage 指标静态报告四项问题。未启动新的仿真或 PPO，
历史 `recovery_dense_corrected_chain_20261004` 不变。

## Current outcome and offline review — 2026-10-04

Corrected formal is STOPPED_BOUNDED, exit0,1418updates/11,616,256samples,
10741.21s. It remained R0; no lower pose family was trained. Evaluated500/1000
both0/8success,15s recovery_timeout,no runtime fault. Ledger totals remain
smoke30/formal1692, remaining formal1308; no automatic resume authorized.

[Offline gate/control/reward review](runs/recovery_dense_corrected_chain_20261004/formal/SETTLING_REVIEW_20261004.md)
and its linked per-env JSON are the current diagnosis entry.1000 improves
height/tilt but rolls at~0.81m/s and yaws~0.36rad/s in the last2s. Known gates
coincide for at most0.01s, not2s. Terminal wheel targets remain15.07/10.88rad/s.
Handover leg-angle gates are inactive in autonomous_hold and do not block success.
Full velocity vectors/control sequences are missing: exact full-gate/reward
offline recomputation remains UNKNOWN.10CPUregressions pass; this review used
PPO0/simulation0. Proposed next single variable: multiplier on existing high
height settling weights, not a granted new run or modification of current recipe.

## Recovery correction in progress -- 2026-10-04

Latest corrected continuation is submitted at
`runs/recovery_dense_corrected_chain_20261004` using
`configs/experiments/recovery_dense_curriculum_20261004/spec_corrected_direct.json`.
39focusedCPUtests passed; one historical external-YAML identity test excluded.
Runtime initialization passed all4families x2splits,64env layout. R0/R1 are
direct zero-velocity resets, NOT passive stationary certificates; R2/R3 pass
settling checks. The earlier static-hold diagnostic failed as task initialization
and remains preserved. Source stays update1500, not the degrading274checkpoint.
Remaining smoke7; formal2726 maximum, formal wall10800s; existing ledger shared.
The corrected supervisor must complete smoke before formal; see phase progress
and terminal JSON for actual state, not this submission snapshot.
TensorBoard6007 run prefix: `recovery_dense_corrected_20261004/{smoke,formal}`.
New scalars: `task_metrics/motion/mean_height_m`, `mean_abs_height_error_m`,
`mean_linear_speed_mps`, and `task_metrics/reverse_curriculum/stage`.

User requested stopping the degrading dense run and correcting the curriculum
and reward scale before continuing. The stopped formal attempt completed274
updates (2,244,608samples), STOPPED_BOUNDED, exit0, no runtime failure.
Original smoke23 and formal274 charges remain in the same ledger; remaining
allowances are smoke7 and formal2726. No completed attempt is rewritten.

Corrected recipe: `configs/experiments/recovery_dense_curriculum_20261004/spec_corrected.json`.
Its pose library has24 closure-consistent candidates and2 explicitly rejected
candidates. These are offline candidates, NOT runtime-certified poses.
Actual reverse curriculum is now wired to per-episode stage IDs, GPU terminal
buffers and update-end statistics. Only128 completed episodes of the current
stage form a window; two successful non-overlapping windows are required.
Promotion affects subsequent resets only; evaluation cannot promote stages.

Wheel-spin cost is normalized by100rad/s, retaining weight-0.02; a100rad/s
state costs0.0002 per policy step rather than2. Unverified raw joint symmetry,
nominal-target "support region", and unverified-sign slip rewards are removed
from this corrected recipe, not retrospectively changed in old evidence.

The first corrected candidate attempted static initial-target PD hold and failed
R0 initialization. It is historical failed preparation, not the launched recipe.
The launched direct-reset recipe removes that hold: R0/R1 start from valid zero
velocity geometry; R2/R3 retain passive settling. See the latest entry above.
36focusedCPU regressions passed; one historical external-YAML identity test
is excluded and its original failure is preserved. Corrected CPU preflight passes.

New initialization diagnostic: `runs/recovery_dense_corrected_initial_20261004`.
PPO0, charged to the existing formal attempt budget rather than inventing a
source-evaluation allowance. Formal training is not resumed before validation.

## Dense reverse-curriculum Recovery — current submission

Authorized source is the independently evaluated `model_update_1500.pt` from the
knee-stop run. Budget is smoke30 plus formal3000 updates, with TensorBoard monitoring.
The first submission failed before PPO because the supervisor output directory had
already been created; evidence is retained in
`runs/recovery_dense_curriculum_20261004_chain/` and charged updates remain zero.
Fresh retry is `runs/recovery_dense_curriculum_20261004_chain_retry1/`; startup
handshake confirmed smoke update1 (trainer PID2975014). The smoke TensorBoard bridge
writes under `runs/recovery_r1_manual0001_retry_20261002/tensorboard/recovery_dense_curriculum_20261004_retry1/smoke`.
Formal will start only after all30 smoke updates pass finite-loss and actor-change checks.

## Current Recovery continuation — 2026-10-04

User authorized at most10000 total PPO updates, no formal wall-clock cap, sharedGPU0.
[Current spec](configs/experiments/recovery_knee_stop_pitch_20261004/spec.json),
[independent ledger](configs/experiments/recovery_knee_stop_pitch_20261004/budget.json),
[candidate comparison](configs/experiments/recovery_knee_stop_pitch_20261004/candidate_review_corrected.json).
Historical20checkpoints compared over a common0–9.60s Recovery window;
late7.60–9.60s elevated/contact states precede pitch ranking. Recommended1400 is
an initialization candidate, not accepted standing: lateheight0.4079m, abs pitch
0.3212rad, abs vx0.7079m/s. Old sweep16results used ORIGINAL asset/manual0001;
they do not certify the new stop USD or captured pose.

New isolatedUSD `assets/diagnostic/rmuc_robot_closed_loop_knee_stop_0233_v2.usd`
preserves opposite-end2.5rad limits, left knee lower=-0.233rad/right upper=0.233rad.
Old copy's untouched far limit had erroneous8207degrees; kept as historical evidence.
Stops have finite solver compliance and are not a gas-spring force model.
Captured224308pose was closure-resolved within the stops, initialvelocities zeroed.
[New initial probe](runs/recovery_knee_stop_pitch_20261004_initial_retry/result.json)
accepted64/64 after short passive settling and second velocity zero; residual
about1.6e-6m and ideal ground gap about-1.6e-6m in env0 at acceptance.
Initial attempt failed on missinglibrarygeometry; retained,4.07s/PPO0, fixed before retry.
16focusedCPUtests passed. New reward adds only height-gated canonical pitch cost;
existing upright/overshoot/settling, PD, action and limits retained.

Execution: smoke3updates/300s then formal9997updates/no wall cap, one sequential
chain `runs/recovery_knee_stop_pitch_20261004_chain_retry1`. Total samples≤81,920,000.
Checkpoint100/full evaluation500; no motion curriculum or auto retry.
Read phaseprogress/terminal for current facts; this is a submission snapshot.
HAPI formal completion target6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1.
Notifications request review and do not authorize another chain.
First smoke attempt stopped before PPO because pitch reward was absent from rollout
metric registration; retained in `runs/recovery_knee_stop_pitch_20261004_chain`.
Corrected retry uses the SAME ledger with0previous PPO consumed, not a reset budget.
Startup handshake confirmed retry smoke1actual update,trainerPID2653963.
Smoke completed3/3updates; formal startup handshake confirmed1actual PPO update,
trainerPID2654580,monitorPID2654579. This is a point-in-time startup snapshot.
TensorBoard summaries bridge into existing dashboard logdir under
`recovery_knee_stop_pitch_20261004/smoke` and `/formal`.
17focusedCPUregressions passed. Background guard covers pre-formal supervisor failures;
normal formal notifications remain owned by the existing monitor.

## Dense Recovery follow-up — preparation only

The knee-stop run was stopped after2315updates: all four independent evaluations
(500/1000/1500/2000) had0/8 autonomous successes. A new preparation spec is at
`configs/experiments/recovery_dense_curriculum_20261004/spec.json`; its ledger is
explicitly `UNAUTHORIZED`, so no PPO has been submitted. It keeps the same isolated
USD, captured pose, 150D policy and physical limits. The only reward additions are
continuous allowed-support contact credit and a low-height wheel-spin cost gated
out between0.20 and0.32m. This targets the observed low-lying wheel-scrubbing mode;
it does not add hidden control, wheel locking, external forces or a new actor input.
CPU dense-reward regressions pass6/6. Separate budget authorization is required
before a smoke or formal run.
The prepared spec now also records reverse levels R0 near-standing, R1 symmetric
DrawBack approximation, R2 captured low pose and R3 expanded asymmetric poses;
two clean128-episode windows at >=90% success are required before each next reset
level. Dense diagnostics/rewards include leg-pair coordination, support imbalance,
target support-region proxy and wheel/body slip proxy. These are explicit metrics,
not left/right action equality or a hidden controller.
Below are historical snapshots, not current status.

## Level and overshoot Recovery training — 2026-10-03 startup snapshot

User authorized2000updates from autonomous Recovery1000.
[Current run](runs/recovery_level_from1000_20261003/),
[spec](configs/experiments/recovery_level_from1000_20261003/spec.json),
[ledger](configs/experiments/recovery_level_from1000_20261003/budget.json).
Source SHA408e108ed54d31454470726a90a1dde469d7185397716271ea0790f91d941525,
strict actor/critic/Adam,LR3e-5,new reset. Changes: upright weight0.5->2,
one-sided height overshoot cost -((root_height-command_height)+/0.04)^2 per second.
No PD/action/limit/asset/success2s changes.12focusedCPU tests passed and unified
smoke preflight PASS. Startup confirmed2real smoke updates,PID2077117; no formal
completion implied. Background sequential supervisor runs smoke3/300s then
formal2000/28800s,stops on fault,no automatic retries. Same-source formal startup,
smoke is wiring validation rather than a source checkpoint replacement.
Check current phase progress,monitor_exit and terminal reports for live facts.
TensorBoard6007 bridges configured under recovery_level_from1000_20261003/smoke
and /formal. Formal completion sends report to explicit currentHAPI session.
Old runs/ledgers unchanged.

## Autonomous Recovery formal launch confirmed — 2026-10-03 startup snapshot

[Current chain](runs/recovery_self_stand_from1500_20261003_chain/),
[real PPO handshake](runs/recovery_self_stand_from1500_20261003_chain.submission.json),
[baseline](runs/recovery_self_stand_from1500_20261003_baseline/result.json).
Baseline completed92.09s,8valid initial episodes,0runtime faults,0successes and
8ordinary Recovery timeouts; this allows learning under the approved protocol.
Smoke completed3/3 updates,finite losses,actor changed; source/spec/effective LR3e-5,
Adam state_count17. Chain advanced to formal and formal metrics/event file exists.
This is a startup snapshot; read chain/phase progress and terminal JSON for current status.

Budget caps: baseline300s,smoke3/300s,formal1000/14400s;64x128,formal8,192,000samples,
smoke24,576samples. Outer supervisor14690s plus15s cleanup excludes already-completed
baseline; combined total stays within15000s. FrozenSTAND remains unused for control;
success requires Recovery autonomous2s hold. No domain randomization or wheel lock.

TensorBoard HTTP200 and both event files verified at `http://127.0.0.1:6007`.
Runs: `recovery_self_stand_from1500_20261003/smoke` and `/formal` under existing
dashboard logdir. Read-only bridge logs/identities are in chain tensorboard files.
Final chain report and one HAPI completion notification target the explicitly verified
current session6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1; notification never authorizes continuation.
Other isolated motion trainer was neither changed nor stopped.

## Authorized autonomous Recovery chain — 2026-10-03

User explicitly authorized baseline300s/PPO0 -> smoke3updates/300s -> formal
1000updates/14400s. [Spec](configs/experiments/recovery_self_stand_from1500_20261003/spec.json)
and [independent live ledger](configs/experiments/recovery_self_stand_from1500_20261003/budget.json).
Source is Recovery1500 SHA cb5ccd4307a3b9c799bd8543b9c7b9f56eb239c1637534b81852f70b82fb06f5;
no old quota was reset or transferred.32CPU tests passed,one historical preflight excluded.
[Baseline output](runs/recovery_self_stand_from1500_20261003_baseline/) uses new
autonomous2s success protocol,not legacy frozen-STAND5s handover. Ordinary baseline
task failure permits learning; faults/invalid initialization/incomplete baseline stop.
Startup progress here is a snapshot; read phase/chain terminal reports for later facts.
Other isolated motion task is untouched and may affect sharedGPU0 throughput.

## Recovery autonomous standing preparation — 2026-10-03 11:02 CST

User requests Recovery itself to stand steadily. New [spec](configs/experiments/recovery_self_stand_from1500_20261003/spec.json)
and [UNAUTHORIZED budget](configs/experiments/recovery_self_stand_from1500_20261003/budget.json)
start strictly from best evaluated Recovery1500. [Design and commands](docs/RECOVERY_SELF_STAND_20261003.md).
No new simulation/PPO submitted. CPU plan passes; smoke plan correctly requires budget authorization.
Task changes: continuous2s autonomous hold vs old frozen-STAND5s takeover;
height-gated uncapped pseudo-Huber linear/angular settling costs vs old saturated cost.
Legacy handover remains default for all existing specs. No wheel lock, extra damping,
raw symmetry/nominal-angle reward, PD/effort/asset change.31CPU regression tests passed,
one historical preflight excluded. Runtime behavior remains unverified.

## Update1500 wider handover request — 2026-10-03

[Offline gate review](runs/recovery_settle_from433_formal_20261002b/HANDOVER_1500_REVIEW_20261003.md),
[per-env evidence](runs/recovery_settle_from433_formal_20261002b/handover_1500_review_20261003.json).
User requests STAND to finish balancing/straightening from a less-perfect Recovery
state. Recorded1500 late state is upright(tilt≈0.015rad),but vx≈0.21m/s,yaw≈2.45rad/s;
in original height band planar speed fails100%,yaw98.9–99.2%. Terminal right active
angle≈-0.160rad is only≈0.010rad outside provisional gate; all8 terminal leg speeds
pass. Per-step target jumps UNKNOWN. No handover occurred; no evidence of failed STAND
takeover. Broader trigger is proposed for fixed-policy testing only,not activated.
No new simulation/PPO or run/ledger mutation during review.

## Fixed433 takeover-gate diagnostic prepared — 2026-10-02

User confirmed gate-first priority; no reward-enabled/PPO run submitted.
[Execution scope](docs/RECOVERY_433_GATE_DIAGNOSTIC.md),
[diagnostic spec](configs/experiments/recovery_diagnostic433_20261002/spec.json),
[new UNAUTHORIZED ledger](configs/experiments/recovery_diagnostic433_20261002/budget.json).
Existing probe now supports checkpoint mode; same frozen STAND/Recovery433 and
original reward/control,64env layout/8scored,first episodes only,max18s simulation.
All11 gate masks/full root velocities/target jumps and54D physical control snapshot
are captured before reset at100Hz; allocated tensor buffers transfer after evaluation.
Plan-only checkpoint identity check passes,26CPU regressions pass,1historical
preflight deselected. Installed actor default inference is deterministic.
Proposed new physics wall300s includes initialization/cleanup,PPO0; awaiting explicit
budget authorization (old wall exhausted). No STAND robustness or lowered gate.

## Update433 offline analysis — 2026-10-02

User selected433 for analysis. [Identity and training-window evidence](runs/recovery_r1_manual0001_retry_20261002/ANALYSIS_UPDATE433_20261002.json).
433 remains UNREVIEWED by independent physical evaluation; no simulation/PPO here.
401–433 aggregate lift0.9280,upright0.9397,tilt3/update,zero handover/success.
Any-channel policy-sample saturation0.9030; not per-motor or PD-substep fraction.
These are changing stochastic training policies, not a deterministic433 trace.
Next priority is bounded fixed433 gate/velocity/effort diagnostic before further training.

Prepared settling-reward draft at configs/experiments/recovery_r1_settle_from433_20261002
is UNAUTHORIZED and NOT LAUNCH READY: existing Recovery schema rejects warmstart,
and runtime settling reward has CPU fixtures only.26CPU tests passed,1historical
preflight deselected. Do not use this draft to launch until schema distinguishes
Recovery continuation from immutable STAND and physical433 evidence is available.

## Recovery terminal review — 2026-10-02

Current Recovery chain ended STOPPED_BOUNDED at formal wall limit, exit0, no
reported runtime fault. Actual formal433updates/3,547,136samples plus smoke5/
40,960samples. Formal child including cleanup7151.66s; corrected chain7250.57s.
1000-update continuation is NOT_SUBMITTED; predecessor bounded stop prevented
launch, and remaining formal wall is only48.34s. Do not automatically restart.

[Quantitative review](runs/recovery_r1_manual0001_retry_20261002/TERMINAL_REVIEW_20261002.md)
and [per-env compact analysis](runs/recovery_r1_manual0001_retry_20261002/review_quantitative_20261002.json).
Best evaluated Recovery update400 accepted=false,0/8success,0handover frames;
latest update433 is UNREVIEWED. Both differ from frozen accepted STAND update500.
Ledger formal cap1000,used433: unused567updates (no wall allowance for another run).
Old chain report remaining_updates67 uses obsolete505 total; preserve original,
use live ledger for quota. No simulation/PPO was launched by this review.

## Recovery 1000-update authorization and live TensorBoard — 2026-10-02

User authorized1000 formal updates total (not1000 additional), plus existing5smoke.
Current formal trainer retains its immutable500-update startup spec. Exact ledger
cap extended1000 without resetting usage. A detached conditional continuation
PID516959 waits for normal prior-chain completion, then strict-loads Recovery
actor/critic/Adam into a fresh environment for the remaining500 updates; original
7200s formal wall is shared, previous wall deducted. Failure does not trigger retry.
CPU continuation fixture passed. No running source/spec was edited.

TensorBoard HTTP200 verified at `http://127.0.0.1:6007`, event file exists under
`runs/recovery_r1_manual0001_retry_20261002/tensorboard/formal_1_500`.
Read-only metrics bridge PID516960, TensorBoard PID516961; existing6006 service untouched.
Continuation output: `runs/recovery_r1_manual0001_extend_to1000_20261002`;
its `.continuation.json` records WAITING/SUBMITTED/NOT_SUBMITTED, followed by
normal progress, ledger and HAPI terminal callback if submitted.

## Recovery corrected initialization retry — 2026-10-02 startup snapshot

User authorized validation followed by training if wiring passes.
[New chain](runs/recovery_r1_manual0001_retry_20261002/),
[submission and one real handshake](runs/recovery_r1_manual0001_retry_20261002.submission.json).
Handshake confirmed initial probe PID505923, one physical policy step/0.01s.
Initial probe subsequently exited0/passed=true with64 validated envs and advanced
to smoke (monitorPID506207). This is not yet formal training evidence.
Read this chain's `chain_progress.json` / `chain_terminal_report.json` for subsequent state.

Passed prior R0 is explicitly reused; previous child cleanup wall102.21s is deducted
from600s diagnostics. Same ledger preserves all consumption and permits one corrected
initial attempt (source_eval slot3), then smoke5/300s and formal500/7200s.
No new PPO allowance.7CPU regressions and plan-only preflight passed.
Background gates and final HAPI callback remain active; no automatic second retry.
New probe stores all64 pre-reset state/control/cause snapshots for failure review.
The shared chain/probe code and ledger authorization were updated before submission;
no running trainer was modified. Frozen STAND SHA and physical protection unchanged.

## Recovery initialization correction — 2026-10-02

User requested a one-time second velocity zero after passive settle minimum,
before static validation. Shared Recovery runtime now zeros root 6D velocity
and all joint velocities only for initializing envs once per episode, then
requires the full existing static dwell after that operation. Static joint-speed
validation excludes only named `guide_wheel_*_spin` joints; passive linkage,
main wheels and all-joint nonfinite/safety protection remain checked.
This changes initialization semantics and is not spontaneous passive-settle evidence.
CPU/fake-API regression passed; no new physics/PPO or chain restart performed.
Next physical run must preserve this source snapshot and report this explicit
initialization intervention; existing failed-chain evidence and ledger are unchanged.

## Recovery chain terminal review — 2026-10-02 15:41 CST

Current chain has **ended FAILED before PPO**; no automatic continuation is authorized
by the completion notification. [Review](runs/recovery_r1_manual0001_chain_20261002_153110/FAILURE_REVIEW_20261002.md)
and [terminal evidence](runs/recovery_r1_manual0001_chain_20261002_153110/chain_terminal_report.json)
override the startup snapshots below.

Frozen STAND R0 passed 8/8 continuous 10 s. R1 passive initialization accepted
41/64 and rejected 23/64; smoke/formal were not reached, actual updates/samples=0/0.
The 23 replacement allocations after auto-reset were pending, not another completed test.
Whole chain wall=102.33 s, physical child wall including cleanup=102.21 s;
ledger pre-cleanup wall=99.71 s. Both diagnostic attempt slots were consumed.

Rejection causes and rejected env IDs are UNKNOWN: only the 8 passing scored envs
have step records. Executed snapshot applies the settlement velocity threshold to
all joints, including passive guide-wheel rotation; whether this caused rejection
is a hypothesis. Next priority is reset-before evidence for all 64 envs: per-condition
settlement/rejection masks, dwell and separate active/passive/guide joint velocities.
Do not loosen protection or start PPO to bypass this gate. No new simulation was
performed during this review; historical results and ledger remain unchanged.

## Authorized Recovery R1 chain — 2026-10-02 15:31 CST startup snapshot

[Real chain directory](runs/recovery_r1_manual0001_chain_20261002_153110/),
[startup handshake](runs/recovery_r1_manual0001_chain_20261002_153110.startup_handshake.json),
[submission command](runs/recovery_r1_manual0001_chain_20261002_153110.submission.json).
One real handshake confirmed R0 physical progress:1policy step/0.01sim seconds,
probePID482428 matched its command and output; outer supervisorPID482352.
**PPO0 at handshake; this is R0 validation, not a claim that formal training started.**
This is a timestamped snapshot; read `chain_progress.json` and terminal evidence for later state.

User explicitly authorized diagnostics600s→smoke5updates/300s→formal500updates/7200s,
total505updates/4,136,960samples. [Exact ledger](configs/experiments/recovery_r1_manual0001_20261002/budget.json)
is now AUTHORIZED. SharedGPU0,64env×128, fixed STAND update500, only R1 manual0001.
No R2 upgrade, retry, second chain or budget reset. Physical protection unchanged.

Backend gates: complete10s R0 scored8 acceptance→all64initialization acceptance→
5finite smoke updates with actor change→formal, save100/evaluate200,400,500.
Only actual passing probe evidence publishes validated flags; no control/config
changes occur while a child is running. Source/phase snapshots preserve identities.
Outer timeout is8080s plus15s kill allowance (≤8095s), inside8100s authorization.
Child limits independently include termination/cleanup margins. Background owns
exact-attempt reconciliation, candidate report and **one final chain notification**
to current explicit HAPI target `6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1`.

Final entries: `chain_terminal_report.json`, `completion_report.md`,
`formal/candidate_selection.json`, `formal/completion_report.md` when reached.
No extra simulation is launched to fill missing results.27relatedCPU tests passed;
historical external-YAML preflight intentionally not reused as new-spec evidence.

## Recovery R1 manual0001 — 2026-10-02 current preparation snapshot

User confirmed linkage support and requested training. [Launch readiness](docs/RECOVERY_MANUAL0001_START.md)
uses [new manual0001 spec](configs/experiments/recovery_r1_manual0001_20261002/spec.json).
Frozen STAND remains scratch update500. Manual low-pose closure/limits and new
CPU preflight pass;25 relevant CPU tests pass. Source/old specs remain unchanged.
No simulation/PPO launched. [Independent ledger](configs/experiments/recovery_r1_manual0001_20261002/budget.json)
is UNAUTHORIZED/used0 pending explicit quantitative budget confirmation.
Runtime initialization and measured takeover domain are not yet validated.
Proposed conditional600s diagnostics→5smoke/300s→500formal/7200s; no R2 auto-upgrade.

## Manual pose collection GUI — 2026-10-02 preparation snapshot

[GUI instructions](docs/RECOVERY_POSE_CAPTURE.md), [capture config](configs/tools/recovery_capture.json).
Implemented keyboard/sliders, explicit passive/PD modes, pause/reset and complete candidate JSON.
CPU verified only; no simulation/PPO started. User requested this manual collection tool;
Recovery training budget remains unauthorized. External YAML identity drift was detected:
manual capture pins its current SHA separately; historical Recovery spec remains unchanged.

## Current task — Recovery preparation (2026-10-02 13:55 CST snapshot)

The fixed **STAND** policy is [native scratch model update500](runs/wide_leg_from_scratch_20261002_formal/model_update_500.pt),
SHA `fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1`.
[Raw 10s evaluation](runs/wide_leg_from_scratch_20261002_formal/evaluation_500_0_0.json)
passed 8/8, steady root height about0.397873m. It is not certified locomotion or recovery.
[Model handover report](runs/wide_leg_from_scratch_20261002_formal/MODEL_500_HANDOVER_20261002.md).

The prior trainer is stopped (one command-identity check this session found no project trainer).
[Original terminal](runs/wide_leg_from_scratch_20261002_formal/terminal_report.json)
remains **FAILED**, exit0,511 actual formal updates: missing trainer terminal after user SIGTERM.
The new handler fix does not rewrite that historical outcome or deny its independent model evaluation.

Current work is [Recovery preparation](docs/RECOVERY_PREPARATION_20261002.md), with
[task spec](configs/experiments/recovery_r1_20261002/spec.json),
[pending independent budget](configs/experiments/recovery_r1_20261002/budget.json), and
[explicit closed-chain pose candidates](configs/experiments/recovery_r1_20261002/poses.json).
**No new simulation/PPO is authorized or running.** All current usage is0.

Confirmed geometry limitation: chassis `robot` bottom is about0.10m above floor in
guide-wheel-supported low poses. Do not initialize that body bottom onto the plane:
the fixed undercarriage guides would penetrate it. The proposed passive-settle
initialization is bounded and cannot remove that geometric difference.
Pending: agreement on that low-pose definition, runtime initialization/penetration
checks, and frozen-STAND takeover-domain verification. The current handover gate
is a candidate, not a measured acceptance region. CPU validation alone cannot unlock PPO.

All subsequent sections are historical snapshots, including their “current/running” wording.

## Current authorized chain — height40 from update500

Confirmed at 2026-10-02 00:49 CST: formal PPO RUNNING, trainer PID3703684,
chain worker PID3701268, command/output identity checked after a real update.
The single startup handshake confirmed update1; one follow-up identity check
observed update6/49,152 formal samples. This is a snapshot, not permanent state.
Authoritative live state:
[chain progress](runs/height40_from500_20261002_night/chain_progress.json),
[handshake](runs/height40_from500_20261002_night/startup_handshake.json),
[formal progress](runs/height40_from500_20261002_night/formal/progress.json),
[terminal report](runs/height40_from500_20261002_night/chain_terminal_report.json).

- [Frozen spec](configs/experiments/height40_from500_20261002/spec.json),
  [ledger](configs/experiments/height40_from500_20261002/budget.json).
- Source is native update500, SHA `b3c04a08900644fd54faef2d45a5d8bbc64a73dc14b0292f5ae56b7834543473`;
  strict150D loading, restored Adam and explicit actual LR3e-5. No B200 input expansion.
- Wheel target scale100rad/s uses explicit output calibration6/100 and corresponding
  previous-action input/Adam coordinate conversion. CPU regression preserves source
  physical wheel targets in the old unsaturated action domain. Runtime regression is pending.
  Physical torque limits remain40/5.5Nm; physics/PD/policy remain1/5/10ms.
- First task is root height0.40m; height reward weight2, width0.06m.
  Motion stages are gated by two full confirmations and retain40% zero samples.
  High wheel target capability does not certify high-speed behavior.
- Old unused2500 updates were transferred, not duplicated: smoke5 + formal2495,
  total20,480,000 samples, whole chain maximum8h. Old formal500 usage remains recorded.
- 73 CPU tests passed before submission. Source diagnostic completed8/8 continuous10s,
  no runtime fault, contact1.0, saturation0, steady height≈0.35256m. It fails
  only the new height checks, so no new0.40m acceptance is claimed.
  [Raw source](runs/height40_from500_20261002_night/source_eval/evaluation_source.json),
  [compact control analysis](runs/height40_from500_20261002_night/source_eval/control_diagnostic_summary.json).
  Two leg normalized actions frequently reach clipping bounds; combination projection
  occupancy0, sampled applied-vs-clipped effort difference0. This does not yet establish
  a mechanical inability to reach0.40m. Smoke completed5 updates/40,960 samples,
  finite loss and actual actor update. Formal actual LR3e-5 read back.
- Background owns sequential source diagnostic, smoke, formal, candidate evaluation,
  budget settlement and one completion notification to the captured HAPI target.
  Ordinary failure to reach0.40m is task data, not an infrastructure stop.

All sections below describe prior experiments and are historical snapshots.

## Fixed height scan — 2026-10-02

PPO=0. Frozen `update_2000` was evaluated at command heights 0.34, 0.355,
0.363, 0.38, 0.40 and 0.42 m; `update_500` was evaluated at 0.40 m. All
cases completed 8/8 ten-second episodes without runtime faults. `update_2000`
settled at 0.35533–0.35552 m across the six commands; raw leg action channels
were at their clip boundary about99.9%/100%. Target projection occupancy rose
from about0.8% at0.34 to78.8% at0.42. This supports a height-input/native
action-contract bottleneck, not a proof that the closed-chain plant cannot
reach0.40 m. See [scan report](runs/height_scan_20261002/DIAGNOSTIC_REPORT.md)
and [raw summary](runs/height_scan_20261002/diagnostic_summary.json).

## Latest review — 2026-10-01 CST

Formal chain FAILED after500 actual updates due to inference tensor reset at first evaluation. Training is not resumed. Minimal buffer and exit-code fixes passed66 CPU tests. Independent update500 evaluation completed8/8 continuous10s and passed8/8 frozen standing gates; steady height≈0.35270m, no continuing height decline within2–10s.100s durability is NOT_RUN.

- [Review](runs/review_500_20261001_REPORT.md), [raw full trace](runs/review_500_20261001_eval10.json), [per-env comparison](runs/review_500_20261001_summary.json).
- Latest model: `runs/stand_long_20261001_205100/formal/model_update_500.pt`; this is now independently10s accepted, but has larger yaw error and deeper initial dip than B200. The original chain candidate-selection/FAILED reports remain historical and unchanged.
- Ledger: formal500, smoke3, evaluate1. No automatic continuation or extra evaluation budget.
- Source snapshot: `runs/review_500_20261001_source_snapshot/`.

The RUNNING text below is a historical snapshot, superseded by this review.

## Current standing chain — 2026-10-01 20:54 CST

**Formal PPO is RUNNING at this snapshot**, verified through a first-actual-update
handshake and one evidence check. Trainer PID3444486, detached chain worker3441508.
Do not launch a duplicate or treat this timestamped state as permanently current.

- Current [spec](configs/experiments/stand_long_20261001/spec.json) and
  [authorized independent ledger](configs/experiments/stand_long_20261001/budget.json).
  Original stand_plane/old migration ledgers are unchanged.
- Active [chain](runs/stand_long_20261001_205100/),
  [handshake](runs/stand_long_20261001_205100/startup_handshake.json),
  [formal progress](runs/stand_long_20261001_205100/formal/progress.json).
- Source plane baseline COMPLETED in80.14s: 8/8 passed continuous10s;
  drift0.0887–0.0908m, dual-contact1.0, steady height≈0.36309m,
  mean abs vx0.00983–0.00994m/s, saturation0,
  closure maximum≈0.0000251m. [Raw result](runs/stand_long_20261001_205100/source_eval/evaluation_source.json).
- Smoke COMPLETED: 3updates/24,576samples,41.43s, finite loss and actor changed.
  Effective optimizerLR3e-5 and17 restored states verified.
- Formal snapshot: 4updates/32,768samples; 2,996 updates remain at this instant.
  Current episode level0/6s; no128-episode complete window yet.
- Native B200 warmstart, command[0,0,.363],25D+125D→150D, plane0.5/0.5/0,
  1ms physics/5ms PD/10ms policy, legs40Nm/wheels5.5Nm remain fixed.
- Adaptive episode6→10→20→30s: deadline assigned per-env only at reset.
  Two consecutive non-overlapping128-completed-episode windows are required;
  normal timeout fraction≥95% and per-episode metric-pass fraction≥95%.
  Frozen per-episode gates: abs vx/yaw≤.03, excursion≤.20m, tilt≤.20rad,
  dual contact≥.80, mean height[.34,.38], saturation≤.10, closure≤.005m.
- Formal≤3000updates/24,576,000samples or36,000s; checkpoint100/full10s500,
  no light evaluation. Final selected100s assessment has a separate600s/PPO0
  budget; 10s candidate acceptance does not certify100s durability.
- 63 CPU tests passed before launch, including reset isolation, exact window
  boundaries, survival-only rejection and actual installed PPO timeout bootstrap.

Current accepted **10s source baseline** is B200 on this plane. No trained formal
candidate or100s result exists yet at this snapshot. Backend will select source,
best/full-accepted/latest separately; ordinary falls are task results, faults
stop the chain. No automatic new chain or additional budget.

Backend writes chain_terminal_report/analysis/candidate_selection/completion_report,
then sends one HAPI event to`6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1`.
Per-phase monitors keep local reports and do not send duplicate notifications.
The notification never authorizes continuation. Current chain was already
submitted; see TOOL_INDEX for the exact command, not a resubmission instruction.

The older preparation snapshots below are historical, not current authorization.

## Automation snapshot — 2026-10-01 20:15 CST

No simulation/PPO started. One process check found no trainer/monitor using this
project. The budget is still `NOT_AUTHORIZED`, every counter zero. Original 28
tests plus new coverage: **53 CPU tests pass**. Fake subprocess/transport tests
do not prove actual Isaac or HAPI delivery.

Pipeline: detached monitor → exact-attempt settlement → `analysis.json`,
`candidate_selection.json`, `completion_report.md` → `report_ready.json` → one
HAPI send. Reviewed requires explicit acknowledgement. See
[tools](TOOL_INDEX.md) and [synthetic example](docs/automation_example/completion_report.md).
The example contains invented fixture data, not a model result.

Formal plan is unchanged: 200 updates/1,638,400 samples, 2 checkpoints, one
2-second light evaluation at100 and one 10-second full evaluation at200.
Plane runtime estimates are UNKNOWN. Formal wall limit3600s includes60s terminal
reserve. Evaluation10–15% is a planning target, not permission to skip protocol.

Current CLI session target verified from `HAPI_SESSION_ID`:
`6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1`. Future submissions capture the explicit
target once; background does not guess. No test message was sent. A fresh source
baseline authorization is still required before runtime verification.

Checked 2026-10-01 19:41 CST. This is a snapshot; recheck process command,
run progress and terminal before claiming a live run. One process check found
no native_stand/command_v6 trainer. An unrelated RMUC GUI playback was active
and was not touched.

**Current objective:** prepare a maintainable plane-ground, complete-command
native standing project. The only active task command is `[0,0,0.363]`.
Straight motion, yaw, combined motion, rise-from-fall and high-speed are not
current training targets. The user accepts approximately 0.36 m posture.

- Current experiment: [stand_plane.json](configs/experiments/stand_plane.json).
  Plane z=0, Z up, explicit static/dynamic friction 0.5/0.5 and restitution 0.
  Native 25D/125D/150D and 40/5.5 Nm limits are frozen there.
- New run: **none**. New [budget](configs/experiments/budget.json) is
  `NOT_AUTHORIZED`, all phase limits and usage zero. No current candidate has
  passed a plane-ground evaluation. No simulation or PPO was run for this
  preparation.
- Source: [native B200](/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/B_formal/model_adapt_200.pt),
  SHA `f440ef1999fd10886b74bf64bdff03bbdbe6c7e85c4a226e9d9428e5d4b05698`.
  Actor, critic and Adam expansion are covered by CPU tests. A prior v6
  source-only 8/8 10 s result is on its **mesh** scene, not evidence that
  this new plane scene has passed: [evaluation](/home/kellen/wheel_leg_migration_audit/native_stand/command_v6/runs/source_eval_20261001_1210_retry2/evaluation_source.json).
- Historical v6 Stage 1 [terminal](/home/kellen/wheel_leg_migration_audit/native_stand/command_v6/runs/formal_stage1_20261001_1300/terminal_report.json)
  completed 500 updates/4,096,000 samples on its old scene. Its consumed
  [ledger](/home/kellen/wheel_leg_migration_audit/native_stand/command_v6/budget.json)
  stays separate and does not authorize this project.
- Latest saved here: **none**. Best observed here: **none**. Accepted here:
  **none**. A new B200 plane baseline is the first required physical check.

**CPU status:** 28 CPU tests pass, source/asset/module/YAML SHA match, and
preflight reports `READY_NEEDS_AUTH` without creating an output. See
[TOOL_INDEX.md](TOOL_INDEX.md) for safe commands. No runtime scene/readback or
GUI check has occurred in this new project. Its authored plane binding and
runtime control ownership must be read back in the proposed source-only run.

Review fixes now in code: B200 Adam moments are retained but the actual
optimizer learning rate is checked against spec `3e-5`; a normal 2-second
light evaluation is `evaluation_window` completed without pretending to be
a full standing pass; source and formal 10-second results use one standing
gate with per-env failed checks; formal terminal/progress include latest and
best evaluated checkpoint plus `candidate_selection.json`. A closed startup
handshake pipe cannot interrupt the trainer or exact-attempt settlement.
These are CPU-proven wiring changes, not plane runtime verification.

**Next permitted work:** review this spec and propose one explicit new budget
for the conditional chain in [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md).
Do not start AppLauncher or PPO until that budget is authorized and the CPU
preflight becomes `PASS`. A source baseline that already passes standing does
not require PPO merely to spend an allowance.

## Fixed433 gate diagnostic result — 2026-10-02

[Report](runs/recovery_diagnostic433_20261002/DIAGNOSTIC_REPORT.md) and [summary](runs/recovery_diagnostic433_20261002/gate_summary.json) are complete. PPO0; eight first episodes,18s each,all task failures,zero runtime faults. At target height band all environments had0s simultaneous gate pass: linear speed0.30–2.34m/s vs limit0.05, angular speed0.45–3.67rad/s vs0.3, net displacement1.17–1.50m. Active leg angle reached0.54–1.08rad, leg target jump0.54–1.00rad and wheel target jump89–133rad/s; these are secondary after the speed failure. Height overshot to≈0.611m. No handover/STAND_VERIFY occurred, so no evidence of STAND instability. Next change should target height-gated Recovery deceleration/target-rate settling; do not widen the0.15rad gate or add STAND robustness yet. Diagnostic ledger consumed one source_eval slot; no training budget consumed.

## Settling chain preflight failure — 2026-10-02

The settling chain ended FAILED before PPO. R0 and64/64 low-pose initialization passed;
PPO0. Exact cause was source identity metadata: model_update_433.pt embeds spec SHA
`799bf673b35feecb9421001f342695181af91ce98978ce2571510476b47bbb6b`, while the new spec
retained stale `source_spec_sha256=c1b6...`. Corrected in
`configs/experiments/recovery_r1_settle_from433_20261002/spec.json` for a future run.
No restart was made after terminal notification; ledger records source_eval2, smoke0,
formal0. See run `FAILURE_REVIEW_20261002.md`.

## Retry2 smoke automation review — 2026-10-02

Retry2 notification corresponds to automation failures, not Recovery behavior. First attempt failed before PPO due stale source_eval prerequisite. Second attempt completed the configured 3/3 smoke updates (24,576 samples, finite losses, actor changed), but stale chain logic required5 updates and incorrectly blocked formal. Live ledger: source_eval0, smoke3, formal0, formal limit10,000. No formal training process remains. See `runs/recovery_settle_from433_retry2_chain_20261002/RETRY2_FAILURE_REVIEW_20261002.md`. No continuation launched after the notification.

## Settling formal terminal review — 2026-10-03

Formal settling run stopped at the10h wall bound:3395 formal updates/27,811,840 samples, plus3 smoke updates; zero runtime faults. Six full evaluations all had0/8 Recovery successes. Best observed update1500 reached15s timeout, mean final height0.416m and mean peak tilt0.211rad, but no handover/5s STAND verification. Updates2000–3000 regressed in height/tilt; latest3395 is unreviewed. See `runs/recovery_settle_from433_formal_20261002b/TERMINAL_REVIEW_20261003.md`. No continuation authorized or started.

````

## ARCHITECTURE.md

````markdown
# Execution chain

公共工程证据：domain.time_axis统一索引/时间，diagnostic_profiles.storage_plan统一保存解析，
domain.accounting统一limit/actual/settled，Recovery effective包含全声明叶子及兼容用途。
工具validate_frozen_cpu/audit_terminal/audit_entrypoints不构造新的监督执行链，
见docs/ENGINEERING_WORKFLOW_COMPLETION_20261008.md。

评分声明通过domain.evaluation_config与schedule/storage分开；train各评估调用与独立evaluator
采用相同适配。registry保留摘要和raw引用，ProgressGuard经tools.evaluation_loader读身份核验诊断。
notification_route记录owner/target，notify冲突拒绝；旧manifest兼容，历史证据不迁移。
min-height完整window与certificate结果分开；见docs/NOTIFICATION_EVIDENCE_FIX_20261008.md。

Recovery进度保护器的baseline消费者通过CLI边界tools/recovery_progress_baseline从原始evaluation_source.json取完整控制证据、核验spec/source/asset身份并记录SHA；不从删去大数组的candidate摘要推断诊断。纯域ProgressGuard仍不读文件。详见[终态修复](docs/RECOVERY_MIN_HEIGHT_P1_GUARD_TERMINAL_REVIEW_20261007.md)。

Recovery最小高度v2新增纯域recovery/min_height.py；task_protocol统一deadline/hold/batch时长，runtime首入口锁存及1000样本有限任务终止，rising/recipe同窗评分、selection进度排序。旧v1分支保留；不增加控制层。共享代码与冻结CPU检查只支持下一轮准备，实际运行仍需独立spec/授权。见[迁移报告](docs/RECOVERY_MIN_HEIGHT_P1_PREPARATION_20261007.md)。

Motion声明准备见docs/MOTION_PREPARER_CONTRACT_20261007.md：tools.prepare_motion_experiment
默认零写，CLI文件边界共用tools.experiment_preparation的SHA/差异/独占发布；
严格CPU加载共享learning.model并审计完整Adam映射，但不执行更新。
新spec统一authorization字典，budget仍UNAUTHORIZED。prepare→config/recipe→supervisor
plan/submission_contract→已有链；不会新建trainer/monitor或绕过当前session/资源校验。

## Level2单变量对齐 — 2026-10-07

[冻结声明与事件复盘](docs/RECOVERY_LEVEL2_ALIGNMENT_20261007.md)。wheel_longitudinal_start_m/full_m显式配置时，现有轮心水平错位平方成本乘高度gate；未配置保持历史公式。survival_level验收不改，只有rising且显式gate允许新增cost；holding仍拒绝。evaluation.full_trace_updates只能选合法full milestones，增加保存而非评估/控制/PPO。

Recovery task_protocol owns batch duration. Explicit diagnostic profiles define
saved fields/scope/rate before runtime; frozen checkpoint preparation emits an
unauthorized evaluation-only spec and ledger. See docs/DIAGNOSTIC_PROFILE_FIX_20261007.md.

Recovery batch request duration remains10s for holding; explicit validated rising_task
requires23s to retain the full recovery/hold observation horizon. Cross-mode durations
and unknown fields fail. Full batch diagnostics preserve geometry/posture/control
without optimizer updates; source identity is the explicitly selected frozen actor.

Future rising reports explicitly label pre-entry diagnostic metrics and incomplete
hold evidence; post_rise_metrics is null if no entry. Autonomous-rise candidate rank
uses full acceptance/retained evidence and terminations, not failed pre-entry survival
or higher peak height. Frozen historical reports/rankings remain unchanged.

Level2 migration uses measured manual0001 joint_pos and original root orientation,
strict old150D actor/critic/Adam with separate source_asset/current_asset identities.
No policy remapping: action/observation/history and PD timing/limits match; current
height target0.36 replaces old0.40. DrawBack and R0 have separate smoke group evidence;
historical initialization flags are not reused. See docs/RECOVERY_LEVEL2_DRAWBACK_20261007.md.

当前工程能力与验证范围见docs/ENGINEERING_STATUS.md。源码描述下一次执行，
已运行实验始终按自身冻结实现解释；本次文档更新不更新训练阶段或行为结论。

EpisodeSummary v1 joins device rollout producers and certificate readers.
Recovery task_protocol preserves legacy behavior while recording holding/rising
identity; pose episode metrics keep geometry, initialization and capability distinct.
Execution identity records declaration and actual copy location separately.
Read docs/EPISODE_IDENTITY_RECOVERY_FIX_20261007.md for the restricted offline
certificate/usage publication tool and its authorization boundary.

Completed-episode smoke receipts consume the actual RolloutMetrics field completed,
with completed_episodes only as a legacy fallback. A phase owner may issue a fresh
offline corrected receipt for that exact reader failure; historical receipts stay
unchanged. Reused source/smoke attempts carry explicit evidence-spec SHA and external
certificate SHA; current recipe equivalence and all original inputs remain strict.
Formal-only resumes preserve imported usage/exact IDs, do not rerun smoke, and do
not grant a second budget. Health validates the declared matching evidence spec.

Strict execution identity accepts a relocated shared-chain worker only against
its submission receipt: unchanged frozen spec SHA, declared source root, and exact
Python module hashes. It does not accept arbitrary alternate roots or bypass source
identity. Existing frozen workers/receipts are not modified retroactively.

Opt-in recovery.rising_task uses pure recovery/rising.py to score the first
standing-entry sample followed by a complete10s same-episode hold, within a23s
observation horizon and11.5s active recovery deadline. Per-env windows are explicit;
no episode stitching or shortened early-failure acceptance. Static reset rehearsal
keeps40%R0, no automatic stage upgrade. Rising stays on student targets without
STAND forward/control. A validated ordinary source recovery failure may permit
wiring smoke; missing initialization/runtime fault/protocol mismatch cannot.
Historical baseline and fixed-horizon scoring remain unchanged. See
docs/RECOVERY_RISE_LOW_20261007.md and its independent spec/ledger.

New shared chain uses tools.run_state for canonical lifecycle records and
startup/terminal projections; IO stays outside pure domain. Motion and Recovery
requests validate independently via tools.motion_batch/recovery_batch and pure
domain.evaluation_requests before shared runtime creation. Existing frozen runs
retain their old implementations. See docs/STATE_REQUEST_FIX_20261007.md.

Recovery retention explicitly selects first(default) or uniform_rollout eligible
indices once per rollout without RNG consumption. Coefficient and optimizer hook
are unchanged. Explicit balanced_pose_cycle provides evaluation-only initial pose
coverage; weighted training reset remains intact. Shared batch evaluator dispatches
Recovery family/seed requests through the same environment and scoring implementation.

Public entry inventory: TOOL_INDEX.md; dated commands: TOOL_INDEX_HISTORY.md.
tools.entrypoints supplies a read-only catalog and historical CLI guards.
This catalog does not parse recipes, authorize runs or replace supervisor health,
preflight, identity and ledger checks. No new submission wrapper is introduced.

Current engineering contract: [entry/episode semantics](docs/ENTRY_SEMANTICS_FIX_20261007.md).
Pure resource policy, candidate roles, episode result and execution plan live in
domain; file/process/GPU reads stay at CLI boundaries. Shared supervisor records
exclusive/shared authorization and owner snapshot without process-name whitelist.
Owned phase events distinguish submission/current-stage/formal-update evidence.
run_phase generates certificate once; all other chain readers validate it.
Samples derive from frozen PPO dimensions, smoke requirements from event timing.
Holding window diagnostics are device reductions serialized at update end.

Recovery explicitly opt-in `standing_task.training_episode` uses `recovery/holding.py`
for streaming full10s gates: steady sums and whole-episode peaks match independent
scoring. Normal horizon produces timeout/bootstrap; failed posture certification
does not become a physical fall. Success neither resets early nor selects teacher
control. Historical specs retain their FSM path. Current authorized R0 contract:
docs/RECOVERY_R0_HOLD10_20261007.md; no R1 promotion or final100s phase.

## Current Evidence Interfaces

The current interface contract and CPU/runtime limits are in
[NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md).
`domain/evidence.py` validates effective scoring protocol and task-specific gates;
requested windows remain frozen while observed per-env duration is recorded.
`tools/evaluation_state.py` isolates evaluation switches, actor mode and RNG,
including setup/cleanup faults. Missing/contradictory full evidence cannot promote
a course; light evaluation never certifies full ability.

The shared `supervisor` defaults to plan-only. Authorized submission runs health,
source identity and exact-attempt checks before the existing owned-child chain.
`wiring.py` supplies the same persisted certificate validation to phase owners,
preflight and ledger; formal depends on verified evidence, not a hardcoded PID or
evaluation filename. Runtime completion remains monitor-owned and at-most-once.

Selected-update diagnostics default to off. Device aggregates and read-only
full-rollout/optimizer-step probes preserve the training objective and RNG.
Offline audit reads frozen implementation and recorded identities; it writes only
fresh corrected directories. Unknown history is not reconstructed as measurement.

Git tracks current source and declaration configs; immutable local inputs/evidence
are a separate data boundary. See [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md). The
historical task descriptions below identify prior recipes, not new permissions.

Explicit `survival_level_v1` objective selects motion-independent online success,
full scoring and candidate ranking. Old stationary recipes keep prior semantics.
Pure standing_success_mask/pose_sampling unify level gates and weighted rehearsal.
R1 uses60% near-standing perturbations/40% R0; holdout evaluates each separately.
Retention regression observes retained R0 rather than unlearned R1; promotion
uses current-family full result plus retained checks. Final evaluator restores
checkpoint curriculum stage. No actor/control/physics path changes.
Shared schedule honors explicit unlock_full_updates; new recipe100/200/500 then
every500, no light simulations. Current spec/source/budget:STATUS and
docs/RECOVERY_SURVIVAL_LEVEL_20261006.md.

Optional wheel_longitudinal_offset reward receives pre-reset runtime main-wheel
body centers, converted to root coordinates and gravity-horizontal native-forward
projection. Reward uses explicit deadband/scale/negative weight, dt once, no
height gate. Actor/control and frozen protocol unchanged. Recovery evaluator
preallocates13-column geometry tensor and emits summary/full selected traces.
Shared stand_chain optionally verifies source wheel readback against existing
AssetPoses bounded closure solver before any PPO; it executes frozen source.

`command_v6.retention_ab` sequences two independently initialized arms through
shared stand_chain phases/monitor/trainer/ledger. Source retention adds explicit
constant/cosine schedules and optional first-minibatch actor PPO+entropy versus
BC gradient diagnostics, with leg/wheel contributions sharing one denominator.
Default remains constant/all6; zero BC skips backward/reclip. Trainer writes
compact selected-update evidence and once-per-update summaries. Pair submission
freezes execution source, deduplicates launch and sends one completion callback.

Optional standing-only `settling_yaw_weight` and `yaw_scale_rad_s` add canonical-Y
Pseudo-Huber cost; explicit config validation rejects other tasks/nonfinite values.
Default recipes have unchanged reward fields; enabled recipes aggregate the new
GPU field once per update. Recovery evaluation honors CLI diagnostics and emits
pre-reset control groups/sampling identity. Quota transfer accepts an explicit
smoke count(default5), preserving locked/idempotent exact-budget publication.
Controlled tests may set `evaluation.run_final_durability=false`; default chains
retain their previous final-candidate durability behavior.

Completed source/smoke evidence can be referenced by a fresh formal ledger via
`evidence_spec_path`. Preflight validates the original manifest SHA and compares
all spec fields except submission metadata (experiment/budget/artifacts/
authorization/phase description). Changed rewards/actions/physics/protocol deny
reuse. Original attempts and evidence remain immutable; reused rows charge zero
new updates/wall and retain original ledger/attempt/consumption identity.
Formal still uses the existing launcher, monitor, trainer and notification flow.

## Recovery run boundaries

`command_v6.domain.warmstart.seed_training` 默认只使用当前 spec seed；恢复来源
checkpoint 的 RNG 必须显式设置 `restore_source_rng=true`。评估通过
`preserve_rng_state` 和 Recovery evaluator 的同等保护，不改变后续 PPO 采样。
Recovery checkpoint 还保存 `recovery_curriculum`，包含 stage、通过窗口、未完成窗口
和历史窗口；恢复只影响后续 reset，不重写当前 episode。

## Corrected reverse Recovery

Each episode owns a reset-stage ID. Runtime captures pre-reset success/fault in
a128-step GPU buffer; update-end collection forms128-episode non-overlapping
windows. Two >=90% success windows with no runtime fault advance subsequent
resets only. Old-stage completions are excluded; holdout evaluation suspends
promotion. Per-pose initialization uses direct closure-valid zero-velocity
reset for near-standing R0/low-support R1, and passive settling plus validation
for captured R2/perturbed R3. No initialization stabilizer controls PPO steps.
Wheel cost normalization is explicit in the corrected recipe; legacy recipes
retain their original unnormalized semantics. Unverified geometry rewards are
excluded from the corrected recipe rather than mislabeled as physical metrics.

## Knee-stop Recovery continuation

Current entry and identities are in root STATUS, not the historical workflow below.
`prepare_knee_recovery.py` reviews old evidence and generates an isolated USD/spec/
closure-resolved pose library. `recovery.probe` validates passive initial settling;
`recovery.train_stages` sequences shared smoke/formal launcher and exact ledger.
`runtime.configure` copies asset config before selecting the isolated USD.
Source asset SHA and new asset SHA are explicit distinct manifest fields.
Optional pure-domain high-position pitch cost receives canonical pitch from runtime;
no new actor input, physical compensation, or control path is introduced.
Formal monitor owns reports/notifications. Independent submission guard covers
pre-formal supervisor failure without relaunching, changing budget, or double-notifying.

## Authorized Recovery workflow

`recovery/chain.py` is a thin sequential supervisor of the existing `probe.py` and
`command_v6/monitor.py`/trainer/ledger. It owns cumulative diagnostic wall budget,
publishes measured initialization/takeover gate evidence only between exited children,
and requires5completed smoke updates plus actual actor change before formal.
It reuses completion notification locks/transport for a single final chain report;
phase monitors retain local quantitative reports and send no separate HAPI callbacks.
Probe progress callback is optional; it supplies one true physical-step handshake.
No new trainer, algorithm or control path is introduced.

## Manual Recovery pose collection (no policy/PPO)

`configs/tools/recovery_capture.json` pins the original Recovery base-spec and current
external YAML identity. `recovery/capture.py` is the CLI/UI/file boundary; CPU-only
`capture_controls.py` handles four bounded joint targets and ideal shape support math.
`capture_runtime.py` explicitly subclasses the shared native scene, uses the same PD
and plane, disables ordinary task resets, and stops on physical faults. Passive mode
zeros six active efforts. No actor/critic/optimizer, no training-ledger reservation.
Only user-triggered saves transfer full state to CPU; no per-step recording.
See [capture guide](docs/RECOVERY_POSE_CAPTURE.md) for limitations and launch command.

## Recovery task (preparation, no runtime evidence yet)

One shared trainer is retained. `spec.task=recovery` selects
`native_stand/recovery/recipe.py`; no new trainer tree is created.

- `recovery/asset_poses.py`, `prepare.py`: CPU USD joint-frame closure and
  primitive support geometry; explicit active+passive pose artifacts. No virtual
  Gym leg state, torque Jacobian or MuJoCo controller dependency.
- `recovery/domain.py`: pure Torch FSM/reward/physical-target blend. Entry is
  INITIALIZING→RECOVERY→HANDOVER→STAND_VERIFY→STAND; failure/fault are separate.
  STAND/FALLEN_CONFIRM deployment triggers are reserved, not implemented/certified.
- `recovery/runtime.py`: subclass of shared CommandEnv; same plane/asset/PD,
  explicit zero-active-effort passive settling, local reset, all-joint USD limits,
  ideal-ground-penetration guard, chassis/support geometry, pre-reset tensor evidence.
- `recovery/recipe.py`: CLI assembly loads frozen STAND actor strictly (no standing
  critic/Adam object). New Recovery actor/critic/Adam learn separately through the
  installed RSL-RL library; no teacher loss. Batched holdout first-episode evaluation.
- `recovery/preflight.py`, `probe.py`: CPU plan and separately budgeted R0/settling
  probes. Runtime imports happen only after explicit `--run`/ledger authorization.
- Existing `train.py`, ledger, launcher, monitor and completion components are
  reused; Recovery-specific classification lives in `recovery/selection.py`.

Actor remains25D plus125D history,150D total, no root/contact truth. STAND uses its
unchanged0.5rad/100rad/s action normalization. Proposed Recovery uses1.6rad/100rad/s
to cover folded initial joints; actual USD target limits and40/5.5Nm remain.
Both histories use real state; previous execution is explicitly normalized and
clipped separately. Handover blends physical position/velocity targets over0.3s,
through one PD path; only5s continuous frozen-STAND verification completes a trial.

Passive settling is explicit (0.2s minimum,0.2s stable dwell,1s maximum). There is
no agent control/reward during it; these samples still count against PPO budget.
Rejected initial states, ordinary failures and runtime faults have separate counts.
Ground penetration here is an ideal-geometry proxy; inter-body penetration and
actual contact envelopes remain runtime validation gaps. No physical result is claimed.

See [current Recovery preparation and commands](docs/RECOVERY_PREPARATION_20261002.md).

## Autonomous standing adaptation (CPU implementation, 2026-10-06)

`recovery/standing.py` contains pure Torch posture geometry, continuous
pre-reset standing gates, and a frozen-source Adam pre-step retention hook.
`recovery/runtime.py` computes posture snapshots before reset and adds six
height-gated settling/geometry costs without changing the actor observation
contract. `recovery/recipe.py` evaluates one uninterrupted ten-second episode;
`recovery/selection.py` rejects incomplete or inconsistent certificates.
`scripts/prepare_standing_balance.py` creates the immutable R0 spec, pose
library, and independent budget. This path is CPU-tested only and does not
change USD, PPO, control limits, or old run outputs.

The height-independent v2 recipe explicitly chooses `unconditional` reward
gate mode for pitch/roll, Pseudo-Huber settling and standing geometry costs.
`recovery.domain.reward_height_gate` is pure Torch; absent mode preserves old
height gates. `standing.py` reuses it. Validation rejects unknown modes.
Upright remains a logged raw diagnostic with zero weight in v2; canonical
pitch/roll squared errors provide level feedback. Retention range is explicit
0.30-0.40m, not a certified source recovery domain. No actor/controller change.
The shared standing supervisor now requires the exact smoke update count and
ends the whole chain on user_signal before another phase or durability test.
Conflicting exit/terminal states remain failures. Historical snapshots are unchanged.

## Adaptive standing orchestration

`stand_chain.py` snapshots the shared tree/spec and refuses a duplicate submission
for the same authorization. It runs source_eval→smoke→formal monitors sequentially,
uses one formal first-update handshake, then evaluates the best full-observed
checkpoint for100s under separate600s/PPO0 budget. Only the chain sends a final
HAPI event; each phase has its own attempt, progress, terminal and local analysis.

`domain/episode_curriculum.py` contains pure explicit-input episode statistics
and128-completed-episode non-overlapping windows. Runtime assigns each env's
6/10/20/30s deadline only when that env resets. Active episodes keep their old
level/deadline after global promotion; records are grouped by assigned level.
Two passing windows require both normal timeout≥95% and metric-pass episodes≥95%.
Rollout128 steps does not reset episodes. Milestone evaluations interrupt/reset
unfinished training episodes; those interruptions are not completed-window data.

Training timeout is deadline reached AND NOT task/fault termination. Explicit
is_finite_horizon=False makes RSL wrapper pass time_outs; installed PPO5.0.1
bootstraps timeout rewards using gamma×transition.values, not ordinary falls.
The CPU fixture exercises its real process_env_step method. This preserves the
installed algorithm and does not claim a new terminal-next-value implementation.

Smoke and formal independently warm-start B200/mapped Adam at spec3e-5; smoke is
wiring validation, not formal-resume progress. Ordinary task failures do not
block the next learning phase. Nonfinite/closure/ownership faults stop the chain.
Per-update GPU summaries include motion and pre-reset completed episode metrics;
no full rollout trajectory is persisted. A bounded stop saves the last completed
update as UNREVIEWED if it lacks full screening. Final100s uses identical physical
control and gates with100s duration/2–100s steady window; it is not inferred from10s.

## Completion automation

Launcher CPU-preflights and shows `completion.plan`, captures the CLI HAPI
target, reserves an exact attempt and writes a submission sidecar before
detaching monitor. It does not precreate the trainer output. Reserved preflight
accepts only the same phase/path/attempt. Manifest and immutable snapshots precede
AppLauncher. One bounded handshake never turns a closed pipe into trainer failure.

Rollout tensor aggregates are transferred at update end and appended to
`metrics.jsonl`; progress remains small. Command counts are episode-target
assignments, not per-step effective-command counts. Episode durations use the
pre-step counter/done mask. Existing saturation is policy-state sampling, not
new every-PD-step certification. No full PPO rollout is saved.

Checkpoint inventory and candidate registry are separate. Evaluations always
bind exact current checkpoint weights, evaluator/protocol/physical/source SHA,
seed/layout/scored count. Light2s cannot certify full10s. Full results are ranked
by acceptance, survival, passed envs, drift, contact, SHA tie-break; reward is not
used. A short-lived low-drift case cannot beat a longer survivor. Current-plane
source evidence participates only with identical identities. Unreviewed saved
weights remain UNREVIEWED; absent accepted evidence means accepted_candidate=null.

After trainer exit the monitor reconciles ledger and exit conflicts before
`completion.finalize_report`, then `completion.notify`. Analysis reads saved
evidence only, reports per-env failures/source deltas/time/missing data, and does
not resimulate. Notification adapts minimal Fudan lock/at-most-once transport via
`hapi ping-peer --message-file -`; no Gym imports, tokens or old ack paths.
Readiness, sending and actual review are separate files. Unknown delivery is not
retried. Analysis/notification errors preserve ledger and write completion_error.
New native `tools/completion.py --acknowledge-review` is the only review entry.

Timing is host elapsed without per-step GPU synchronization. Serialization covers
checkpoint/registry/progress IO; JSONL append is outside its own stored duration.
Startup and remaining unattributed wall are separate. Report/callback work follows
the bounded trainer child; HAPI transport has an independent90s timeout.

```text
configs/experiments/stand_plane.json
  -> CPU schema, source and asset identity, ledger preflight
  -> colleague ArticulationCfg copied into local env instance
  -> local USD Plane + explicit material + body/joint/contact sensor binding
  -> native physical state -> 25D frame -> 5-frame oldest-to-newest history
  -> B200 expanded actor or later native actor -> six normalized actions
  -> physical leg position / wheel speed targets -> 200 Hz explicit PD
  -> 40/5.5 Nm limits -> 1 kHz PhysX closed-loop step
  -> current-state reward and termination -> RSL-RL PPO (training only)
  -> independent continuous-episode evaluation / GUI playback
```

| Responsibility | Actual file and contract |
| --- | --- |
| Identity, schema, phase, budget | `command_v6/config.py`, `tools/preflight.py`, `ledger.py`, `launcher.py`, `monitor.py`; the only next-run spec and ledger live under `configs/experiments/`. |
| Colleague asset adaptation | `native_stand/env.py` imports the SHA-pinned colleague `RMUC_WHEEL_LEG_CFG` after the CLI supplies its verified module path. The config is copied per env; active motor gains are zeroed for exclusive explicit effort control. Passive linkage and guide-wheel parameters remain from the colleague configuration. |
| Scene | `native_stand/env.py:_setup_scene` creates one collision-enabled USD `Plane`, binds the spec material, and refuses an existing `/World/ground`. `runtime/control_readback.py` checks composed Plane/material plus active backend/actuator gains and limits. Effective PhysX contact/rest offsets remain UNKNOWN until runtime readback. |
| Observation | `command_v6/domain/contract.py:frame/history` and `runtime/env.py`. 25D: body angular 3; gravity 3; `[vx,yaw,height]` 3; four physical leg offsets; six physical qdot; previous clipped action 6. Scales are in the spec and frozen by preflight. Five frames oldest to newest; local reset repeats the new frame. No Gym virtual leg state or world position enters actor. |
| Action and physical feedback | `domain/contract.py:targets`, `native_stand/env.py:_apply_action`. Left hip, active, wheel, right hip, active, wheel. Legs: reference 0 + clipped action x0.1 rad, each pair projected to 0.12 rad; wheels: clipped action x6 rad/s. Fresh joint q/dq every 5 physics steps, leg `60*(target-q)-2*dq`, wheel `1*(speed_target-dq)`, clip to 40/5.5 Nm. |
| Reward/termination | `domain/reward.py` takes explicit current tensors and spec weights/widths; `runtime/env.py` owns current contact and terminal state. Raw terms, weights, 10 ms scale, then terminal penalty. Ordinary fall is task data; nonfinite or closure >5 mm is runtime fault. Root height is not COM height. |
| PPO and warmstart | `command_v6/train.py`, `domain/warmstart.py`, `learning.py`; installed RSL-RL 5.0.1, not a local PPO copy. Actor and critic each read 25D+125D=150D. B200 first-layer old columns map per frame and command columns start at zero; Adam moments map by verified name/order. New PhysX episodes reset rather than resuming source PhysX state. |
| Evaluation/play | `tools/evaluate_checkpoint.py`, `tools/play.py` use the same `CommandEnv`, shared actor builder and plane/control readback. `domain/protocol.py` uses reset-before snapshots and does not splice episodes. A full 10 s source/formal/independent result uses one standing gate with per-env failed checks; 2 s light evaluation can finish its requested window but has no standing gate. Source baseline and final selected candidate may retain full compact traces; normal rollout writes aggregated progress once per update. |

Adam transfers named first/second moments and source optimizer settings other
than `lr`; spec `ppo.learning_rate=3e-5` is explicitly applied and actual
param-group LR recorded before rollout. Formal progress/terminal identify
latest saved checkpoint separately from best fully evaluated standing
candidate; `candidate_selection.json` preserves that distinction. Startup
handshake is advisory: a closed pipe returns UNKNOWN to the launcher without
breaking trainer completion or ledger settlement.

The old `native_stand/command_v6` source was a proven kernel but inherited a
mesh-ground `native_stand.env`. This project carries only that kernel and the
needed native environment/contract, replaces the ground with an explicit
plane, and keeps historical runs at their original paths. `command_v3-v5`,
Gym 47250, the Jacobian lookup, and the MuJoCo controller are not runtime
dependencies. A new spec, not a new Python copy, versions later tasks.
# Height40/update500 recipe

The authorized `configs/experiments/height40_from500_20261002/spec.json`
uses the existing shared implementation, not another version directory.
`domain/warmstart.py` strictly restores150D actor/critic/Adam, overrides LR,
and explicitly converts previous-action coordinates for wheel scale100.
`learning_distribution.py` calibrates wheel output by6/100 to retain source
physical targets initially; it does not change40/5.5Nm effort limits.
`domain/task_curriculum.py` requires two full confirmations before task upgrade.
`runtime/env.py` aggregates per-command rollout statistics on device and shares
the same plane, observation/history, PD and reset path with evaluation/play.
`train.py` couples that task curriculum to the existing6/10/20/30s episode
curriculum. Task advancement resets episodes explicitly; normal timeout versus
failure remains separate. Shared `stand_chain.py` runs source/smoke/formal and
final accepted-candidate durability, with exact-attempt ledger settlement and
one completion callback. Source evaluation includes100Hz control diagnostics;
those are not a claim of every-PD-substep force measurement.
# Recovery Autonomous Success (2026-10-03)

New optional `recovery.fsm.success_mode=autonomous_hold` keeps the Recovery actor
in control until the current physical state satisfies
`recovery.autonomous_stability` continuously for2s. Instability resets the hold
counter. The success pulse terminates that episode; STAND is never executed before
success. Legacy handover remains default, with frozen-STAND5s verification.
Reward adds configurable height-gated pseudo-Huber linear/angular costs in pure
domain functions. Recipe output carries the success protocol; candidate selection
distinguishes autonomous2s from legacy5s. See [task design](docs/RECOVERY_SELF_STAND_20261003.md).
Current verification is CPU only; new physical/PPO budget is not authorized.
# Colleague-aligned training protections

The opt-in warm-start protections and their provenance are documented in
[docs/COLLEAGUE_ALIGNMENT.md](docs/COLLEAGUE_ALIGNMENT.md). They are disabled
unless a new experiment spec explicitly sets the PPO fields, so the native
Recovery and historical runs keep their recorded behavior.
# Motion absolute-error recheck -- 2026-10-07

严格effective_recipe_version=1通过domain.recipe解析，旧冲突声明作为legacy ignored记录。
本轮只实现来源实际combined/ramp/global normalization等价表达；不启用split/fixed算法。
motion_absolute_v3共用score、capability_gate、resolve_gate、completion，保持10–18s/停车26–30s。
共享supervisor --evaluation-only → monitor → evaluate_checkpoint --batch复用一次AppLauncher，
每model×command原子保存，monitor在child关闭后结算独立PPO0账本；未启动任何训练。
详见docs/MOTION_ENGINEERING_RECHECK_20261007.md。

````

## TOOL_INDEX.md

````markdown
# Current Tool Index

新增`tools.validate_frozen_cpu`、`tools.audit_terminal`、`tools.audit_entrypoints`；
分别负责CPU验证副本、一次终态事件核验和静态引用/guard审计。默认零写，
显式--write或--output-dir才写新工程目录，不提交训练；[精确用法](docs/ENGINEERING_WORKFLOW_COMPLETION_20261008.md)。

`tools.prepare_recovery_retry`：显式失败run/ledger/current session，默认零写；--write只发布
UNAUTHORIZED零额度声明，不转移预算或自动重提。共享前缀native_stand.command_v6。
`tools.evaluation_loader`为内部身份校验raw读取接口；min-height prepare/review已同步机器入口表。
见[本轮工程记录](docs/NOTIFICATION_EVIDENCE_FIX_20261008.md)。

`scripts/review_recovery_min_height.py --run <completed_chain> --output-dir <fresh_dir>`：旧轨迹新协议离线评分，独立NumPy交叉核验、输入SHA；不仿真。
`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_recovery_min_height.py`：仅本轮S50配方准备器，创建新UNAUTHORIZED声明，不能launch或复用历史授权。后续仍只走supervisor；见[报告](docs/RECOVERY_MIN_HEIGHT_P1_PREPARATION_20261007.md)。

`native_stand.command_v6.tools.prepare_motion_experiment`：通用Motion PPO0评估/单阶段课程声明，
显式parent/checkpoint/request/SHA/GPU/session，默认零写；`--write`仅发布未授权新目录。
用法、schema和验证见[准备器契约](docs/MOTION_PREPARER_CONTRACT_20261007.md)。
不启动训练，后续提交继续使用唯一supervisor。

当前Level2对齐：[说明](docs/RECOVERY_LEVEL2_ALIGNMENT_20261007.md)。scripts/review_recovery_geometry.py --run/--output-dir只读输入、写新离线报告；scripts/prepare_recovery_alignment.py --hapi-session为本次获批配方专用准备器，会创建新spec/授权账本，不能当通用或历史授权入口。提交仍只用supervisor。

supervisor 新增只读 `--check-submission`，区分配置检查与提交就绪，见[提交契约用法](docs/SUBMISSION_CONTRACT_FIX_20261007.md)。相关代码本轮不提交；使用前先核对工作树与 `--help`。

首次使用请读：[新 Codex 会话入口与命令用法](docs/CODEX_START_HERE.md)。公开提交只用 supervisor；旧 preparer 不作通用入口。

Recovery起身PPO0 batch仅显式合法rising_task支持23秒；holding仍10秒。
当前补采见docs/RECOVERY_UPDATE50_GEOMETRY_PPO0_20261007.md，仍只通过supervisor提交。

scripts/review_recovery_transition.py：既有Level2全过程离线分段/公式量级审计，
显式--run/--output-dir，新目录独占创建，不启动模拟/PPO；缺完整轨迹标UNKNOWN。

最新Recovery：docs/RECOVERY_LEVEL2_DRAWBACK_20261007.md；
scripts/prepare_recovery_level2.py仅准备身份核验后的Level2声明，公共supervisor提交。
新family drawback_manual0001不与历史Swing family R1混用。

[当前工程能力、验证边界和剩余缺口](docs/ENGINEERING_STATUS.md)。工具可调用
不代表已授权；准备器、恢复发布和通知命令均有写入/发送边界，不能泛称只读。

[后台执行规则](docs/DETACHED_TRAINING_POLICY.md)：只一次启动握手，之后结束交互；
后台monitor负责终态通知，禁止Codex循环tail/progress/ps/GPU或新增watcher。
tools.completion --notify-only只消费现有就绪报告；--expected-session校验当前目标，
不重算报告、不等待训练。该通知命令有发送/记录副作用，不是只读检查。

当前Recovery起身入口：docs/RECOVERY_RISE_LOW_20261007.md，独立日期时间spec；
scripts/prepare_recovery_rise.py准备PPO0定位或依据定位结果准备起身训练声明。
只通过supervisor提交，--locator-run明确已完成证据，不重启旧coverage链。

已完成Recovery coverage复现记录：docs/RECOVERY_COVERAGE_AB_20261007.md；准备工具
scripts/prepare_recovery_coverage.py。source_capability使用supervisor --evaluation-only，
A_first/B_uniform使用同一supervisor的source/smoke/formal链。一次性独立预算，
历史明确GPU0/shared和当时session；不可重用旧授权或自动增强系数/扩展R1训练。

本页仅列当前公共入口。历史命令、旧会话/PID、日期配方和旧推荐保留在
[历史工具清单](TOOL_INDEX_HISTORY.md)，不能作为当前运行许可。
新实验根目录和spec名称必须以创建日期时间开头，例如
`2026_10_7-14_27__motion_width_ab`；详见[命名规则](docs/EXPERIMENT_NAMING.md)。
完整机器可读分类：`python -m native_stand.command_v6.tools.entrypoints --include-historical`。

## 唯一公开提交入口

`native_stand.command_v6.supervisor`，默认 plan-only。必须显式提供 spec/output；
运行还需当前授权、GPU、会话、独立账本和身份匹配的证据。
`launcher`、`monitor`、`stand_chain` 是内部组件，不是另一条公开提交路线。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
-m native_stand.command_v6.supervisor \
--spec <明确选择的spec.json> --output-dir <新的output目录>
```

此示例没有 `--launch`；plan 不创建 run、账本或报告。
资源默认 exclusive；shared 需要本次明确批准说明。提交确认、当前阶段与
formal 首更新验证分开，UNKNOWN 不能宣称训练已启动。
新共享chain的state/status统一为RunState；started及首更新确认只描述证据。
详见[状态与请求边界修复](docs/STATE_REQUEST_FIX_20261007.md)。

## 当前检查与报告入口

| 入口 | 职责 |
| --- | --- |
| `tools.entrypoints` | 只读公共/内部/历史工具分类，默认只显示当前入口 |
| `tools.health_check` | 只读文档、身份、账本和进程核验 |
| `tools.preflight` | CPU 前置检查与明确 reason code |
| `tools.completion` | 通用终态报告 CLI，底层实现仍在 completion.py |
| `tools.correct_evidence` | 新目录离线更正报告，不覆盖历史原始评估 |
| `tools.engineering_recovery` | 仅已确认completed reader错误的零写恢复计划；发布仍UNAUTHORIZED，不启动训练 |
| `tools.prepare_checkpoint_diagnostic` | 冻结模型PPO0诊断准备，profile/身份/独立账本，默认UNAUTHORIZED |
| `tools.prepare_motion_experiment` | Motion评估/单阶段课程准备；默认零写，--write仅发布未授权声明 |
| `tools.prepare_recovery_retry` | FAILED/TERMINATED exact attempt准备；默认零写，发布仍零额度，旧消耗单列 |
| `tools.validate_frozen_cpu` | 默认零写冻结验证计划；--write生成CPU验证副本及专项结果 |
| `tools.audit_terminal` | 一次raw事件/更新/身份审计，可选新输出，不重写run |
| `tools.audit_entrypoints` | 静态引用与historical guard审计，不自动删除 |
| `scripts/prepare_recovery_min_height.py` | min-height专用配方准备，不是通用重试或提交入口 |
| `scripts/review_recovery_min_height.py` | min-height已有轨迹离线重评分，写新报告，不采集/PPO |
| `scripts/audit_recovery_survival.py` | 冻结输入、身份及指标离线审计 |
| `scripts/prepare_recovery_coverage.py` | 显式新目录、日期时间名称的coverage配方准备器；仍需独立授权 |
| `scripts/review_recovery_coverage.py` | 既有coverage证据的离线复盘，不运行optimizer |

表中 tools 模块前缀均为 `native_stand.command_v6.`。
精确参数以各入口 `--help` 为准；只读核验不授权仿真。
独立物理评估由 supervisor `--evaluation-only` 提交；评估执行器是内部组件。

## 当前证据与决策入口

- Motion 最终复核：[工程报告](docs/MOTION_ENGINEERING_RECHECK_20261007.md)的最终结论优先；
  B250 为推荐来源，new250 的早期推荐已被后续同协议物理证据替代。
- Recovery R0 hold10 已完成：[复盘](docs/RECOVERY_R0_HOLD10_REVIEW_20261007.md)。
  source50 仍优于已评估新模型，旧授权不允许再次提交。
- 当前 spec/候选/授权状态看 [STATUS](STATUS.md)，不从工具名或版本号猜测。
- [本次入口收敛与边界](docs/ENTRYPOINT_CONSOLIDATION_20261007.md)。
- [接口语义](docs/ENTRY_SEMANTICS_FIX_20261007.md)、[Git边界](docs/GIT_WORKFLOW.md)。

## 准备器边界

2026-10-08更正：已有`tools.prepare_motion_experiment`，支持明确父配方的评估/单阶段课程。
参数与示例见[新工具操作手册](docs/NEW_TOOLS_USAGE_20261008.md)。以下旧准备器说明仅作历史定位。现有
`prepare_motion_course_plan.py`、`prepare_recovery_hold.py`、
`prepare_motion_recheck_20261007.py` 是特定配方/复现实验工具；
生成配置不能代替设计决策、校验或授权。本轮没有把它们包装成通用准备器。

旧高速 runtime 准备入口已禁止执行。三个固定旧路径的 Motion 准备器默认拒绝，
历史声明复现需显式 `--historical-replay`，且仍不能覆盖已有目录。
两旧submit/continue包装器仅输出弃用提示并退出2，不再转发任何提交。
其他已列历史准备/报告工具要求--historical-replay；旧watch入口禁用。
新提交直接使用supervisor。

````

## docs/CODEX_START_HERE.md

````markdown
# 新 Codex 会话：入口与用法

新公共工程流程：[冻结CPU验证、终态审计、时间轴和保存计划](ENGINEERING_WORKFLOW_COMPLETION_20261008.md)。
默认只读计划；--write和--output-dir有CPU副本/新审计写入副作用，无仿真/PPO权限。

更新日期：2026-10-08。本页是操作交接，不是训练授权，也不是实时进程状态。
只 checkout 已提交版本时，先检查 `git status`：工作树可能包含尚未提交的新接口，
不能把工作树测试结果当成 HEAD 的验证结果。

## 先读什么

1. 最近的 `AGENTS.md`。
2. 根 `README.md`、`STATUS.md`、`ARCHITECTURE.md`。
3. STATUS 指向的任务 spec，以及对应 run 的 manifest、progress、terminal、原始评估和 ledger。
4. `TOOL_INDEX.md` 与本页。
5. 涉及训练设计、选优或验收时，读 `TRAINING_EXPERIENCE_REUSE.md`。

根 STATUS 同时可能记录 Motion 与 Recovery。先确定本次用户请求的任务，
不要用 Recovery 的状态推断 Motion，也不要用文档中的旧 PID 判断现在存活。
运行事实以对应 run 的冻结实现、配置和原始证据为准；共享源码描述下一次运行。
缺失证据标 UNKNOWN，不能从聊天摘要补造。

## 固定工作环境

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONPATH=src
PYTHON=/home/kellen/anaconda3/envs/issaclab/bin/python
git status --short
```

只修改本项目；保留已有 dirty changes。历史 run、checkpoint、evaluation、ledger、
source_snapshot 和外部仓库只读。不得停止、重启或修改其他任务。
物理 GPU 编号、shared/exclusive 模式和共享授权必须显式核对，不自动切换 GPU。

## 当前入口与安全命令

提交契约修复与 `--check-submission` 用法见
[authorization/session 提交检查](SUBMISSION_CONTRACT_FIX_20261007.md)。
该轮按要求仅提交文档，相关代码仍在工作树；只 checkout HEAD 时先核对接口是否存在。

唯一公开提交入口是 `native_stand.command_v6.supervisor`。
launcher、monitor、stand_chain 是内部组件，不是另一条供用户选择的提交路线。

以下命令只显示用法或执行只读检查，不启动 AppLauncher/PPO：

```bash
"$PYTHON" -m native_stand.command_v6.supervisor --help
"$PYTHON" -m native_stand.command_v6.tools.preflight --help
"$PYTHON" -m native_stand.command_v6.tools.health_check --project-root "$PWD"
"$PYTHON" -m native_stand.command_v6.tools.completion --help
```

使用实际 spec 和新的输出路径设置 `SPEC_PATH`、`RUN_PATH` 后，再做计划检查：

```bash
"$PYTHON" -m native_stand.command_v6.supervisor --spec "$SPEC_PATH" --output-dir "$RUN_PATH"
"$PYTHON" -m native_stand.command_v6.tools.preflight --spec "$SPEC_PATH" --output-dir "$RUN_PATH" --phase formal
```

supervisor 默认 plan-only；运行必须额外显式选择 `--launch`。
不要把本页示例、旧 ledger 剩余额度、已通过 smoke 或终态通知当成新运行授权。
`--formal-only` 仅复用同一链内已经核验的前置证据，不绕过预算和身份检查。
`--evaluation-only` 是 PPO0，但仍是物理仿真，需要用户授权。

| 工具/操作 | 写入与运行边界 |
| --- | --- |
| health_check、preflight、supervisor 默认计划 | 只读；不创建 run、不 reserve ledger、不启动仿真 |
| 准备器 | 创建新 spec/独立预算及来源清单；不等于授权运行 |
| correct_evidence、离线 audit | 仅在新输出目录写更正报告；不覆盖原证据 |
| supervisor --launch | 需要明确授权、exact attempt、身份与预算前置检查 |
| completion/通知 | 使用现有终态证据；外部通知需授权，目标是本次会话 |

详细 CLI 以本工作树的 `--help` 和 `TOOL_INDEX.md` 为准。
按日期命名的旧 preparer 只用于该实验复现，不是通用准备入口。
不得移除 historical guard；弃用包装器不能被当作续训入口。

## 一次提交的固定流程

新工具的参数、写入边界和错误处理见[新工具操作手册](NEW_TOOLS_USAGE_20261008.md)。
Motion用prepare_motion_experiment；Recovery失败重试用prepare_recovery_retry。
两者默认零写，--write只发布UNAUTHORIZED声明。准备完成后继续使用supervisor，
--check-submission与默认plan区分；通知目标需核对实际负责人，不凭收到事件自动接管任务。

1. 核对任务、授权、来源 checkpoint SHA、资产、spec、执行依赖与冻结副本。
2. 做一次必要资源检查；检查 ledger 未结算 attempt，不抢占其他任务。
3. CPU tests 与零写入 preflight/plan-only。
4. 有授权时才执行有界 smoke；验证真实 episode 事件，不以固定更新数代替覆盖。
5. 由 supervisor detached 提交，后台 owner 管训练、评估、预算、结算与终态通知。
6. 只做一次启动握手；反馈当前阶段与证据，然后结束交互。

SUBMITTED 仅表示提交，SOURCE_EVAL/SMOKE 不表示 formal 已开始。
只有 formal 首个真实更新、进程身份、attempt、输出路径及 progress 证据齐全，
才能报告 formal 已启动；UNKNOWN 握手不能冒充启动成功。
CPU 测试、有限 loss 和 reward 上升都不证明机器人能力通过。

## 后台训练与唤醒规则

Codex 不得循环读 progress/log，不得周期性执行 ps/nvidia-smi/tail，
不得用 sleep、反复 wait 或代理 watcher 等待整场训练。
后台 monitor 可以履行其预算与结算职责，worker 不代替它。
终态由既有 hook 通知当前 HAPI 会话；不要复制旧 session ID。
通知失败与训练失败分开记录，不因此重跑训练。
终态通知只授权读取复盘，不自动授权续训，也不重复处理已 reviewed 的事件。
规则详见 [后台执行政策](DETACHED_TRAINING_POLICY.md)。

## 新实验、协议与证据

新实验统一使用 `YYYY_M_D-HH_MM__purpose`，由集中命名函数生成。
spec.experiment、配置目录、run 与报告应对应；旧实验不重命名。
来源、latest、best_new、best_overall、accepted 和 fallback 分开登记。
未评估 checkpoint 不能 accepted，来源不能冒充新训练结果。

评估时长、窗口、终止语义和保存字段应从有效任务协议解析。
Recovery holding 与 rising 不混用时长；Motion 保持段与停车段分别评分。
诊断未采集字段必须是 null/invalid，不能伪装真实零。
summary、failure_tail、full_transition 的字段和采样率先在 plan 中核对。
若当前工作树有新的诊断准备器，先读其 `--help` 与对应工程报告；
不能因它创建了预算文件就直接运行。

冻结源码可以重定位，但声明身份与实际副本位置要分别记录并逐文件核验。
报告更正写新目录，输入路径与 SHA 留清单；不能凭“更正”追溯宣布旧能力通过。
reward、课程、网络、PPO、物理契约的改变另建实验，不能混入普通接口修复。

## 文档导航与交付

- [工具索引](../TOOL_INDEX.md)：当前工具与历史工具分类。
- [工程交接](ENGINEERING_STATUS.md)：已有接口与验证范围；其中日期是历史检查时刻。
- [命名规则](EXPERIMENT_NAMING.md)。
- [Git 工作边界](GIT_WORKFLOW.md)。

结束时列出精确修改文件、实际验证命令/结果、仍缺证据及 commit SHA。
只暂存本次授权改动，不使用 `git add .` 混入其他 worker 的训练配置或代码。
文档更新不能声称新的物理验证；没有运行就明确写“未启动仿真/PPO/续训”。

````

## docs/ENGINEERING_STATUS.md

````markdown
# 当前工程状态与交接入口

更新日期：2026-10-08。本页汇总当前共享源码的工程能力，不替代run的
manifest、冻结源码、原始评估、terminal或ledger，也不判断进程当前是否存活。

## 当前公共入口

后续[公共流程补齐](ENGINEERING_WORKFLOW_COMPLETION_20261008.md)：冻结CPU验证、终态事件审计、
公共时间轴、保存计划、三类计数摘要和Recovery全字段披露均已实现并CPU验证。
全量528 passed；真实已结束run只读审计，未模拟/PPO或更改活动快照。
完整声明枚举与实际消费者认证分开；旧18入口已有guard/引用审计，未删除。

新工具参数及副作用：[操作手册](NEW_TOOLS_USAGE_20261008.md)。
Motion通用准备、Recovery失败重试均默认零写，发布未授权声明；
评分/调度/storage边界、raw loader和通知路由见[工程修复](NOTIFICATION_EVIDENCE_FIX_20261008.md)。
当前新增接口最近全量CPU记录522 passed；以下435项是旧阶段历史记录。

- 新提交：`native_stand.command_v6.supervisor`，默认零写入plan-only。
- 只读核查：health_check、preflight、entrypoints。
- 离线证据：correct_evidence、audit_recovery_survival.py。
- 受限工程恢复：engineering_recovery，默认零写入；显式发布仍UNAUTHORIZED。
- 终态报告/通知：tools.completion；notify-only只消费已有就绪报告。

精确CLI和历史工具分类见[TOOL_INDEX](../TOOL_INDEX.md)。launcher、monitor、
stand_chain保留内部职责；已退役watch不替代后台owner。

## 已实现与验证范围

| 工程项 | 当前状态 | 限制 |
| --- | --- | --- |
| shared/exclusive资源与模型角色 | CPU验证；来源与best_new分开 | 不自动授权共享，不以PID猜测任务 |
| RunState | 共享标准chain统一记录，握手为证据投影 | 独立旧A/B及历史链不追溯迁移 |
| Motion/Recovery请求schema | 独立validator，拒绝跨task字段 | 标准Recovery batch仍固定10秒；rising按显式独立协议路径 |
| 冻结源码重定位 | 声明根/实际根分开，receipt/逐文件SHA严格核验 | 真实冻结preflight为CPU证据，无新GPU执行认证 |
| EpisodeSummary | 版本1，兼容completed/旧alias，冲突拒绝 | 不重写历史metrics |
| per-family/pose smoke | GPU张量汇总，声明组分别核验 | 新真实runtime覆盖与吞吐尚未验证 |
| holding/rising | 明确任务身份与窗口对齐，legacy adapter保留行为 | standing_task共享字段尚未彻底拆除 |
| 受限证书恢复 | 指定completed reader错误白名单、SHA计划、exact-ID去重 | 仅发布未授权新配置；非通用预算转移或自动恢复 |
| 后台通知 | 现有owner终态hook、报告SHA、事件去重与当前session校验 | 本轮mock验证，未实际发送HAPI通知 |
| 报告 | Markdown压缩数组，链接原始证据 | JSON/原始轨迹不删减，旧报告不覆盖 |
| 新实验命名 | 集中Asia/Shanghai日期时间前缀 | 旧/已冻结实验不重命名 |

## 最近验证

最近全量CPU：435 passed（18.61秒），127个Python文件AST语法通过。
后续冻结schema记录的针对性回归：43 passed（2.18秒）。
一次历史起身smoke只读恢复plan绑定15项输入，source_eval1/smoke10/formal0
及原limits保留，未创建目标目录或publication receipt；检查输入SHA未变化。
Git提交前的再次验证另记于提交说明，不覆盖上述历史检查。

没有启动Isaac/AppLauncher、PPO、续训或新预算；没有修改活动run冻结副本。
CPU/mock成功不能证明运动、起身或高速度能力改善。

## 任务事实的阅读边界

Motion当前推荐来源为B250，依据[最终同协议复核](MOTION_ENGINEERING_RECHECK_20261007.md)。
Recovery coverage A/B已完成，起身链的准确运行状态读
[起身实施记录](RECOVERY_RISE_LOW_20261007.md)及其run终态。
STATUS中的PID、RUNNING和首更新是对应握手时刻事实，不作为现在存活证明。
本次文档整理没有轮询任务，不更新或推断其最新训练结果。

## 下一步工程优先项

1. 在另有授权的新运行中验证per-pose摘要、分组smoke与通知投递；仅一次握手。
2. 准备器的共享身份/exclusive-create/账本事务封装，防止中途留下可误用配置。
3. 逐步拆除holding/rising的legacy字段，先有兼容证据再退役旧接口。

不扩大工程恢复白名单，不因旧额度或终态通知自动续训。长训detached后结束交互，
后台owner负责终态通知；Codex禁止亲自周期性查日志、进程或GPU。

详细交付：[状态接口](STATE_REQUEST_FIX_20261007.md)、
[episode/身份/恢复](EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)、
[后台唤醒规则](DETACHED_TRAINING_POLICY.md)、[命名](EXPERIMENT_NAMING.md)、
[Git边界](GIT_WORKFLOW.md)。

````

## docs/NEW_TOOLS_USAGE_20261008.md

````markdown
# Codex新工具操作手册

新增公共时间轴、保存计划、计数摘要、legacy清单及三个工程工具用法见
[公共流程补齐](ENGINEERING_WORKFLOW_COMPLETION_20261008.md)。

本页说明当前工作树接口，不提供仿真/训练/重试/通知授权。先读AGENTS、根文档、
任务spec与原始证据。历史run、checkpoint、raw evaluation、ledger和冻结代码只读。
只修改文档不会启动任务；实际可调用接口以本机--help为准。

## 共同环境和入口

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
PYTHON=/home/kellen/anaconda3/envs/issaclab/bin/python
"$PYTHON" -m native_stand.command_v6.tools.entrypoints
```

默认目录只列当前工具；加--include-historical可查历史/内部/退役分类。
提交统一用supervisor，launcher/monitor/stand_chain保留内部职责。
下面的变量均须替换为核验过的实际值；示例不含--launch，也不自动获授权。

## Motion评估或单阶段课程准备

输入：有效parent spec、150D native完整checkpoint及预期SHA、request JSON、
新config目录、当前session、明确GPU index/UUID。父配方需effective_recipe_version=1，
旧spec声明与实际执行不一致时先做独立迁移审查。

```bash
"$PYTHON" -m native_stand.command_v6.tools.prepare_motion_experiment \
 --parent-spec "$PARENT_SPEC" --checkpoint "$CHECKPOINT" \
 --checkpoint-sha256 "$CHECKPOINT_SHA" \
 --request docs/examples/motion_evaluation_request.json \
 --output-dir "$NEW_CONFIG_DIR" --hapi-session "$HAPI_SESSION_ID" \
 --physical-gpu "$PHYSICAL_GPU" --gpu-uuid "$GPU_UUID"
```

- 默认只输出spec/budget/preparation_manifest计划，files_written=0。
- evaluation示例包含±2.5、30s父协议、1200s墙钟，PPO预算0。
- course用`docs/examples/motion_course_request.json`：明确retained/current/weights、
  inclusive在线100=smoke1+formal99、每25完整评估及各phase墙钟。
- course只包含当前0.5增量，不解锁更高级；父reward/PPO/物理/gate保持。
- 可选`--audit "$AUDIT_JSON" --audit-sha256 "$AUDIT_SHA"`仅引用身份，不导入通过证书或额度。
- 加--write才在本项目configs/experiments下新建三个文件：spec.json、budget.json、preparation_manifest.json。
  名称必须符合日期时间规范，重复路径拒绝；账本UNAUTHORIZED、used0、空attempts。
- 参数名/Adam shape、来源资产、输入SHA、未知请求字段或允许差异冲突会在发布前失败。

CONFIG_DIR名称推荐用集中函数生成，手册不硬编码某个旧日期目录：

```bash
"$PYTHON" -c 'from native_stand.command_v6.domain.experiment_naming import new_experiment_name; print(new_experiment_name("motion_endpoint_review"))'
```

完整schema与验证限制见[MOTION_PREPARER_CONTRACT](MOTION_PREPARER_CONTRACT_20261007.md)。
准备器校验声明完整性，不把retained列表当已认证能力，后续来源gate仍需证据。

## Recovery失败重试准备

使用**phase run**（如失败source_eval/smoke/formal），配对应旧ledger，不使用只含链摘要的根目录。
terminal和ledger必须为同一已结算FAILED/TERMINATED exact attempt，实际更新数一致。

```bash
"$PYTHON" -m native_stand.command_v6.tools.prepare_recovery_retry \
 --run "$FAILED_PHASE_RUN" --ledger "$OLD_LEDGER" \
 --output-dir "$NEW_CONFIG_DIR" --hapi-session "$HAPI_SESSION_ID"
```

默认零写，核验manifest/frozen spec/source/asset/library SHA，输出历史actual updates、
wall和声明差异。加--write发布未授权零phase额度的新准备文件，不自动修reward或换模型。
COMPLETED任务、RUNNING attempt、terminal/ledger不一致或错误SHA会拒绝。
后续先完成工程修复证据和新预算登记，提交仍用supervisor；旧消耗不清零、不搬账本余额。

## Plan与提交就绪检查

```bash
"$PYTHON" -m native_stand.command_v6.supervisor \
 --spec "$NEW_CONFIG_DIR/spec.json" --output-dir "$NEW_RUN"
```

评估任务加--evaluation-only。默认plan零写，不读GPU；preflight PASS只代表当前phase
配置/身份/账本条件通过。完整元数据可呈READY_METADATA，但submit_ready仍false。
未授权准备返回AUTHORIZATION_MISSING是正确状态。

明确授权并登记新账本后，可做一次只读资源与session检查：

```bash
"$PYTHON" -m native_stand.command_v6.supervisor \
 --spec "$NEW_CONFIG_DIR/spec.json" --output-dir "$NEW_RUN" \
 --physical-gpu "$PHYSICAL_GPU" --hapi-session "$HAPI_SESSION_ID" --check-submission
```

评估任务仍加--evaluation-only。READY/submit_ready=true仅指该时刻就绪；
缺session、错误GPU/UUID、重复output、资源冲突或未授权返回NOT_READY/exit2。
--check-submission与--launch互斥；一次检查后不循环等资源。
实际提交需要额外显式--launch及用户运行授权，一次握手后交付路径，后台owner执行结算。

## 原始证据与报告读取

```bash
"$PYTHON" -m native_stand.command_v6.tools.summarize_run --run-dir "$PHASE_RUN" --ledger "$LEDGER_PATH"
```

这是一次只读小文件摘要，actual_updates优先terminal，其次progress；不是进程存活证明。
ledger用于核对exact attempt和预算，used不可单独代替实际完成更新。
通用raw读取接口为`tools.evaluation_loader.load`，内部Python API而非提交CLI：
传入folder、registry entry、spec/checkpoint/asset SHA和required_fields。
它读取entry.evaluation，校验身份与可选raw SHA，缺字段拒绝。ProgressGuard用该loader，
registry删去trace后的摘要不能充当完整诊断轨迹。

候选读candidate_selection.json：accepted_candidate表达完整认证；
diagnostic_comparison提供contact/posture/prefix并列候选，其通过身份独立保留。
1000样本完整保持但contact失败时，窗口完整不等于证书通过。
新结果hold_window_complete与hold_certificate_passed分开；旧raw不改写。

## 通知与复盘归属

通知目标来自提交时manifest/authorization/receipt，不来自后来读报告的会话。
新manifest.notification_route保存owner/target；冲突记录notification_route_conflict并不发送。
收到未知任务事件时先核对run和负责人，不能据此接管、续训或猜测新接收者。
本页不授权任何真实通知。获明确通知授权后才使用下面命令：

```bash
"$PYTHON" -m native_stand.command_v6.tools.completion \
 --run-dir "$RUN_WITH_READY_REPORT" --notify-only --expected-session "$HAPI_SESSION_ID"
```

此命令有外部发送及锁/发送记录写入副作用，消费已有hash匹配report_ready，
不会重新生成报告或训练；重复event按at-most-once处理，未知投递不自动重试。
`--acknowledge-review`会写completion_review，也不是只读检查；仅处理明确属于该任务的事件。
默认completion CLI会重写报告，不用于本轮要求历史run只读的审查；使用summarize_run或直接读JSON。

## 工程修改时用的内部接口

- `domain.evaluation_config.split`输出scoring/schedule/storage；训练与evaluator用scoring适配。
- `domain.diagnostic_profiles.resolve`仅定义保存范围；完整统一训练保存计划仍未完成。
- `tools.experiment_preparation.checked_input/differences/publish`集中SHA/差异/独占发布，纯domain不读文件。
- min-height专用prepare/review的参数以各脚本--help为准，适用范围不同，不代替通用重试器。

回归命令：

```bash
"$PYTHON" -m pytest -q --tb=short
```

最近本轮工程记录为522项CPU通过，非新的物理/PPO认证。
2026-10-08后续已接入公共时间轴、共享保存解析和三类计数摘要；
legacy字段叶子已完整列出，未证实消费者明确标UNKNOWN/待核验。
使用时以[公共流程补齐](ENGINEERING_WORKFLOW_COMPLETION_20261008.md)所列覆盖范围为准。

````

## docs/DETACHED_TRAINING_POLICY.md

````markdown
# 后台训练与终态唤醒规则

适用于之后所有授权训练。AGENTS.md是执行约束；本说明不授予训练预算，
不更改活动run的冻结代码、命令或通知目标。

## 执行顺序

一次资源检查 → CPU/preflight → 已授权的有界smoke → supervisor detached提交
→ 一次有界握手 → 给用户启动收据 → Codex结束当前交互。

握手未验证formal首更新时只能报告“已提交/当前阶段/证据不足”，不能把
SUBMITTED称为训练已开始，也不能为了等到formal而循环读取日志。

后台worker/monitor拥有子进程，负责固定评估、停止条件、预算、checkpoint、
终态和报告；子进程退出后调用completion.notify。通知通过HAPI ping-peer投递
给该执行worker的当前session，平台是否实际唤醒仍取决于HAPI投递和会话服务。
未实际投递不能声称唤醒已验证。

Codex禁止亲自循环tail/progress/metrics/checkpoint、ps、nvidia-smi，或用sleep、
wait、子agent及新watcher保持会话等待长训。不要把轮询换个名字继续执行。
已有monitor内部的有界子进程/预算检查与训练里程碑不受此限制。
前台有界CPU验证或明确授权的一次诊断评估不是长训轮询。

## 已有通知接口

标准链：stand_chain结束后chain_report写report_ready.json并调用notify。
formal-only：monitor在子进程退出后结算、finalize_report、notify。
原通知接口已有文件锁、event ID、报告SHA检查和发送记录；重复调用不重复发送，
unknown_delivery不自动再发，已reviewed不重复处理。通知失败不更改训练结算。
evaluation-only当前monitor不自动通知，不能把此路径描述为已有自动唤醒。

已有就绪报告需要人工补调用时，使用一个命令；没有循环或等待：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
-m native_stand.command_v6.tools.completion \
--run-dir <明确的run目录> --notify-only --expected-session <本次执行worker的session>
```

此命令只消费已就绪报告，不重建报告、不启动模拟或PPO；它会写通知锁/发送
记录并可能对外发送，不能作为只读健康检查。已有sent/failed/unknown_delivery
记录仍按原at-most-once语义返回；本轮不增加删除记录或强制重发功能。
expected-session与manifest不同会在写通知记录之前拒绝，禁止使用历史session。

用户收到终态后：读报告及必要raw证据一次，复盘，然后用同一CLI的
--acknowledge-review确认事件已处理。通知正文不授权自动续训，不修改预算。
用户主动请求状态时可以做一次只读检查，不得以此启动周期监控。

## 反馈中的其他工程项

后续更新：EpisodeSummary、受限恢复plan和family/pose证书接口已经完成CPU验证，
详见[最近交付](EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)。下面段落保留本通知
接口交付时的范围；通用故障恢复和彻底拆分任务字段仍未完成。

已读取RECOVERY_RISE_LOW_20261007.md：冻结路径重定位与completed字段修复
由对应任务记录，不能替其宣称本轮实施或验证了物理能力。
EpisodeSummary版本化、通用工程恢复工具、holding/rising协议彻底分层及
family/pose事件证书仍是独立工程工作。本轮专注后台与通知约束，不修改训练
期限、初态分布或现运行配方，也不自动恢复失败实验。

改动：AGENTS.md、README.md、TOOL_INDEX.md、本文；
tools/completion.py和tests/test_terminal_wakeup_cli.py。
验证只用CPU fixture和mock通知，没有真实ping当前训练会话。
本轮针对性回归：tests/test_terminal_wakeup_cli.py与tests/test_completion.py，
27项通过（1.02秒）；CLI --help和git diff --check通过。没有启动训练，
没有实际外部投递，HAPI实际唤醒可靠性不在本轮验证范围。

````

## docs/EXPERIMENT_NAMING.md

````markdown
# 新实验命名规则

适用范围：此规则加入后新建的实验和实验根目录。创建时间采用Asia/Shanghai。
已有、已准备或已冻结的实验保持原名，禁止为满足命名规范搬移历史证据。

格式：`YYYY_M_D-HH_MM__用途`，例如：

```text
2026_10_7-14_27__motion_width_ab
2026_10_7-15_08__recovery_coverage
```

日期不强制补零，小时和分钟使用两位数字。名称应简短表达任务与唯一实验变量；
不要只用test、new、latest等无法区分用途的名称。

同一实验使用同一个完整名称：

- 配置根目录：`configs/experiments/2026_10_7-14_27__motion_width_ab/`。
- 运行根目录：`runs/2026_10_7-14_27__motion_width_ab/`。
- `spec.experiment`及存在时的`artifacts.run_name`与根目录名一致。

source_eval、smoke、formal以及A/B等阶段或对照臂子目录保留职责名称，
不逐个添加时间。跨日运行也不改名：前缀表示创建时间，不表示当前更新时间。
同一分钟重名时追加`_01`、`_02`，或追加秒数；仍必须使用fresh/exclusive-create，
不得覆盖旧目录、spec、checkpoint、evaluation或ledger。

Linux shell可以只读生成时间前缀：

```bash
date '+%Y_%-m_%-d-%H_%M'
```

旧日期准备器是历史复现工具，不得直接改路径后当作通用新实验入口。
新实验准备时应明确冻结目标名称，再完成身份核验、spec和独立账本。
命名规范不授权创建预算、启动仿真/PPO或复用历史授权。

本轮将规则写入AGENTS和当前入口文档，未对历史spec实施追溯schema校验。
共享命名接口为domain.experiment_naming；公开coverage准备器的CLI及prepare
函数均校验新根目录名称。历史复现工具保持冻结名称，不做追溯修改。
新增公开准备器必须复用new_experiment_name/validate_new_experiment_name，
不能自行硬编码日期。未迁移的历史工具仍由执行者遵守其复现边界；
避免仅因目录名合法就推断其配置、证据或权限有效。

````

## docs/GIT_WORKFLOW.md

````markdown
# Git 版本控制与工程交接

记录日期：2026-10-07。工程目录：`/home/kellen/wheel_leg_native_train`。

## 首次版本基线

开始本次提交前，`main` 分支没有任何 commit，所有源码和文档均为 untracked。
因此本次首个代码提交保存的是当前现场实现，不代表恢复了某次旧 run 的源码，
也不能凭提交时间推断各算法、配方或修复的历史实现时间。

按职责拆分为三次本地提交：

1. 当前训练内核、接口工程、CPU 测试、声明式配置和 Git 排除规则。
2. 现有准备、诊断、离线审计与共享提交脚本。
3. AGENTS、README、STATUS、ARCHITECTURE、TOOL_INDEX 和相关中文交接文档。

每次提交使用详细中文标题及正文，解释范围、验证和限制。没有执行 push，
没有增加 simulator/PPO 预算，也没有运行旧脚本。

## 纳入版本控制

### 本次增量提交

后续工程提交包含状态机/请求schema、后台唤醒约束、EpisodeSummary与受限恢复，
以及现场已存在的coverage/起身实现、工具和声明配置。不同任务的改动按当前
相互依赖实现保存，不把所有变化归因于同一实验。最新交接和验证范围见
[ENGINEERING_STATUS](ENGINEERING_STATUS.md)；下述387项属于前一次接口提交。
publication receipts与budget同属本地运行数据，保持Git排除。

本次保存当前工作树中相互依赖的接口修复和已存在的Motion/Recovery实现，
不是把所有改动归为同一作者或同一次实验。按代码与CPU回归、工具与声明配置、
文档拆分提交；详细文件清单由各commit提供。现有声明spec保存其原身份和
授权状态，PREPARED/UNAUTHORIZED不因进入Git而获得执行权限。

新增工程入口见[入口语义修复](ENTRY_SEMANTICS_FIX_20261007.md)。最新CPU回归
387项通过；此前315项是首次基线的历史结果。113个Python文件语法通过，
572项历史输入SHA未变化。plan-only正确拒绝已耗尽预算并保持零写入。
本次只整理文档、验证和本地提交，没有启动任何仿真、PPO或续训。

- `src/`：当前项目唯一 Python 实现，包括 native 运行时、Recovery、协议、gate、
  health、preflight、共享 supervisor/certificate 和默认关闭的选定更新诊断。
- `tests/` 与源码下的 tests：CPU fixture 和回归，包含协议冲突、时长、RNG、
  optimizer 诊断不改变更新、账本及提交保护。
- `scripts/`：准备和诊断工具；保留历史专用脚本以供审计，新公共提交使用 supervisor。
- `configs/`：spec、contract、pose library 和工具配置等声明内容。
- 入口 Markdown、`docs/`、`pyproject.toml` 与 `.gitignore`。

旧 spec 中保存的路径、SHA、seed、HAPI session 和授权字段仅描述历史实验。
它们不会被改写，也不证明当前会话有权继续训练。公共 supervisor 仍需校验
当前 `HAPI_SESSION_ID`、明确物理 GPU、active-phase health、来源和独立 ledger。

## 保持本地的数据

以下内容被 `.gitignore` 排除并原地保留，不删除、不移动、不覆盖：

- `runs/`：checkpoint、原始 evaluation、log、manifest、progress、terminal 和报告。
- `isolated/`：独立审计数据、大型 JSON、隔离实现及工程验证产物。
- `assets/` 与模型二进制：本地冻结 USD、checkpoint、ONNX、数组数据。
- 配置目录中的 `budget*.json`、`ledger*.json`、提交记录、运行候选 review、
  `source_snapshot/` 和 `execution_snapshot/`。
- 缓存、锁、日志、编辑器状态和本地凭据。

排除的是运行数据，不是证据要求。每次运行仍须保存并核对 source/asset/spec/code
身份、exact attempt 和累计预算。不得使用 `git add -f` 绕过边界提交旧账本或资产。

代码 checkout 不能用于回滚预算、账本、运行状态或 checkpoint。Git 不替代本地
数据备份；备份、迁移和存储清理由独立任务处理。

## 提交流程

新实验目录和声明名称遵守[EXPERIMENT_NAMING.md](EXPERIMENT_NAMING.md)，
使用创建日期时间前缀；历史路径不因文档规范或Git提交被移动、重命名。

先读取最近的 AGENTS，检查 `git status` 与 index。按明确路径 stage，
不要使用 `git add .` 将历史数据或无关用户改动混入提交。

```bash
git status --short
git diff --cached --stat
git diff --cached --check
git diff --cached --name-only
```

提交前确认 index 没有 runs、checkpoint、USD、ledger、submission 或旧源码副本。
审查大文件和凭据；凭据检查只报告路径，不输出疑似秘密值。
有同事或用户的 staged changes 时，不清空或撤回它们，先识别所有权并缩小范围。

使用 `git commit -F <正文文件>` 传递完整中文说明，避免 shell 对多行、反引号、
`$()` 的错误解释。完成后检查 `git log`、提交文件和剩余状态。用户请求 commit
不等于请求 push、发布或训练启动。

## 验证与证据

本轮接口工程的全量 CPU 基线：**315 passed**；静态 `py_compile`：75 个文件通过。
正式提交前会再次执行 CPU 回归和 staged diff 检查。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

已有工程交付记录：

- [首次接口交付](NATIVE_INTERFACE_EVIDENCE_20261007.md)。
- [缺口补齐与精确文件清单](NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md)。
- 本地 `isolated/interface_evidence_followup_20261007/verification.json`。
- 本地 `isolated/interface_evidence_followup_20261007/change_manifest.json`。

验证产物不加入 Git；源文件之后修改会使旧 change_manifest 的代码 SHA 过时，
它仍是对应工程检查时刻的历史记录，不能自动覆盖更新。本次 commit 的代码身份
以 Git tree 为准；运行身份仍以当次冻结 snapshot/manifest 为准。

CPU fixture 依赖本机的冻结来源、配置和历史账本。全新 checkout 需要另行提供
身份一致的本地依赖，不能默认在任意机器上复现全部物理或历史检查。

## 明确未做

没有启动 Isaac、AppLauncher、在线 PPO 或续训；没有修改 USD、reward、课程目标、
LR、std、网络、advantage normalization、PD、动作尺度或限矩；没有重置账本。
真实 GPU 诊断、detached handshake 和通知投递仍需独立授权验证。
源码提交与 CPU 通过均不代表机器人高速能力或 Recovery 能力改善。

````

## TOOL_INDEX_HISTORY.md

````markdown
# Historical Tool Index

2026-10-07归档：以下内容按原文保留，其中current、RUNNING、授权、PID、URL及
命令均为对应记录时刻的历史陈述。当前入口仅见[TOOL_INDEX](TOOL_INDEX.md)。
不得使用旧session、旧剩余额度或历史推荐直接提交新实验。

# Tool index

## Shared Public Entry

[局部入口修复](docs/ENTRY_SEMANTICS_FIX_20261007.md)。新提交使用
`native_stand.command_v6.supervisor`，默认plan-only。资源默认exclusive，
shared必须记录明确批准；可选有界握手报告提交/current stage，不能冒充formal通过。
两个highspeed wrapper仅兼容旧调用并输出DEPRECATED，不推荐作为新入口。

Current task preparation and read-only engineering entries are listed first.
All date-specific tools below the historical separator are archived references,
not independent current permissions or recommended new launchers.

## Motion PPO0 capability recheck

[精确命令及协议](docs/MOTION_ENGINEERING_RECHECK_20261007.md)。
supervisor --evaluation-only默认零写plan；明确授权后--launch才预留独立evaluate attempt，
共享monitor调用evaluate_checkpoint --batch一次AppLauncher逐项原子保存。
tools.correct_evidence --protocol-spec消费同一score/gate重新评分历史trace，只写新的审计目录。
旧capability_v2不改写；新absolute_v3无隐藏80%响应条件，zero使用mean(abs(vx))≤.5。
后续prepared版本及身份以STATUS和对应spec为准；未授权账本不能提交PPO。

## Current Recovery R0 Holding

docs/RECOVERY_R0_HOLD10_20261007.md records the frozen contract and single submission.
That experiment has completed; docs/RECOVERY_R0_HOLD10_REVIEW_20261007.md records
the review. Its old authorization does not permit resubmission or continuation.
scripts/prepare_recovery_hold.py prepares a fresh identity-checked spec/pose copy/
independent ledger; --authorize requires the current user's explicit scope.
Shared supervisor only, CPU tests/plan first; source -> smoke10 -> formal<=100.
tests/test_recovery_holding.py verifies window scoring/time-limit semantics.
No repeat of the named submission, no automatic R1 or reuse of old remaining quota.

Version-control entry: [GIT_WORKFLOW.md](WORKFLOW.md). Commit source,
tests, declaration configs and docs using explicit paths; ignored run data,
ledgers and execution snapshots are not submitted. All commands below retain
their runtime authorization requirements after checkout or commit.

## Current read-only engineering entries

Latest [gap closure and exact CLI](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md).
The public supervisor requires explicit spec/output and is plan-only by default;
`--formal-only` still requires identity-matched persisted smoke certificate and
active-phase health. New corrected audits reject pre-existing output directories.

See [interface/evidence changes](docs/NATIVE_INTERFACE_EVIDENCE_20261007.md) for
commands, compatibility, exact changed files and corrected offline reports.
`native_stand.command_v6.tools.health_check` is read-only; `supervisor` defaults
to plan-only and owns the existing source/smoke/formal chain only when explicitly
launched under applicable authorization. `tools.correct_evidence` and
`scripts/audit_recovery_survival.py` exclusively create new offline reports.
All launch descriptions below are historical; terminal evidence overrides them.

## Historical Experiment Tools

The following old preparation/launch records remain for reproduction and tests.
In particular prepare_standing_yaw.py and prepare_standing_long.py are historical
recipe generators; do not choose them as a new public submission entry.

## Historical survival/level R0 -> R1 chain

Exact headless detached command, frozen gates/budget and source identity:
docs/RECOVERY_SURVIVAL_LEVEL_20261006.md. Existing stand_chain/preflight/monitor
only. Preparation uses scripts/prepare_standing_balance.py --recipe survival-level
with --source-spec/--source-checkpoint/--output-dir; --authorize only under explicit
user authorization, refuses existing directory. No physics/PPO in preparation.
Live TensorBoard: http://127.0.0.1:6013, source/smoke completed, formal single
handshake RUNNING. Viewer metadata in the new run's tensorboard_processes.json.
CPU regression: tests/test_standing_survival_level.py. Source50 and all historical
results remain untouched. No duplicate launch; live TensorBoard URL/identity STATUS.

## Wheel-center alignment controlled training

docs/STANDING_SCISSOR_EXPERIMENT_20261006.md is the current budget/formula/command.
Shared stand_chain source/smoke/formal entry only; no duplicate trainer.
Source runtime geometry readback must agree with offline USD FK before smoke.
Actual reward geometry is a wheel-center quantity, not contact-patch displacement.
TensorBoard tags: task_metrics/mean_wheel_longitudinal_offset_m,
rollout/raw_mean/wheel_longitudinal_offset and rollout/weighted_mean/wheel_longitudinal_offset.
Keep existing height/vx/yaw/contact/level/mirror/saturation metrics visible.
Viewer http://127.0.0.1:6012; process metadata runs/standing_scissor_20261006/tensorboard_processes.json.

## Scissor posture offline geometry audit

See docs/STANDING_SCISSOR_REVIEW_20261006.md for exact command/limitations.
scripts/audit_standing_scissor.py consumes saved BC pre-action observations,
uses existing offline AssetPoses solver, checks USD/spec/pose identities and
writes a fresh compact JSON. CPU-only, no Isaac/AppLauncher/physics/PPO/ledger.
Coordinates: native forward=-rootZ; gravity-horizontal projection is explicit.
It reconstructs a passive branch, not the runtime body pose. Output collision
or SHA mismatch stops; never silently zero-fill unavailable actual geometry.
tests/test_standing_scissor_audit.py contains4geometry/missing-data fixtures.

## BC gradient / full-channel annealing A/B

Current command/budget: `docs/STANDING_BC_AB_20261006.md`.
Public `python -m native_stand.command_v6.retention_ab` without `--launch`
checks both source phases on CPU without creating output. With `--launch`,
freezes source, sequences shared phases, gives one formal handshake and leaves
report/accounting/HAPI to detached worker. Do not repeat submitted output.
Tests: test_standing_bc_diagnostics.py and test_standing_bc_ab_workflow.py.
scripts/prepare_standing_bc_ab.py creates fresh configs and explicitly transfers
unused quota; must not rerun on the existing experiment directory.
TensorBoard http://127.0.0.1:6011 shows A_fixed/B_annealed smoke/formal;
process identity in runs/standing_bc_ab_20261006/tensorboard_processes.json.
Tags under task_metrics/standing_retention: coefficient,
gradient_comparison/cosine and weighted_norm_ratio, plus legs/wheels subfields.
Judge behavior with full evaluations, not gradient signs alone.

## R0 yaw-only controlled test

Current evidence and authorization: `docs/STANDING_YAW_REVIEW_20261006.md`.
Shared `stand_chain` sequences source/smoke/formal; ordinary source behavior
failure does not block finite/physically valid training. One formal handshake;
background monitor/report/HAPI dedup remain unchanged. Do not duplicate a submitted
chain or reset its103-update transferred allowance.

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.stand_chain \
  --spec configs/experiments/recovery_standing_yaw_20261006/spec.json \
  --output-dir runs/recovery_standing_yaw_20261006 \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

Removing `--launch` is CPU plan-only. Independent checkpoint evaluator's
`--diagnostics` now also records Recovery pre-reset54-column controls; group
offsets/sampling semantics are stored in result JSON. Existing summary/full
paths and previous gates are unchanged.
TensorBoard http://127.0.0.1:6010 compares the previous run and new yaw_only
smoke/formal logs. Viewer uses update-end JSONL only; no Isaac or PPO side effects.
Process metadata is `runs/recovery_standing_yaw_20261006/tensorboard_processes.json`.

## Current R0 height-independent formal submission

Spec: `configs/experiments/recovery_standing_level_v2_long_20261006/spec.json`.
Budget:2000new formal updates, no wall-clock limit; immutable prior source/smoke
evidence is referenced in its exact ledger. Do not submit again if the output
or a running attempt exists. Cwd is this project, interpreter is issaclab:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
src/native_stand/command_v6/launcher.py \
  --spec configs/experiments/recovery_standing_level_v2_long_20261006/spec.json \
  --phase formal --output-dir runs/recovery_standing_level_v2_long_20261006/formal \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

Removing `--launch` is CPU plan-only (no output/Isaac/reservation). Launch performs
exact reservation, detached monitor and one handshake. Monitor owns terminal
accounting, report and notification. TensorBoard6009 reads this run's
`tensorboard/`; JSONL viewer `--wait-for-metrics --follow` waits in a separate
background process, does not synchronize training or read full trajectories.
`scripts/prepare_standing_long.py` generates a fresh ledger referencing exact
completed verification attempts; refuses existing config paths.


## Stopped standing-balance chain (2026-10-06)

`runs/recovery_standing_balance_20261006_chain_1140` is stopped by the user;
do not resubmit its authorization. It uses the experiment's immutable
`execution_snapshot/src/native_stand/command_v6/stand_chain.py` public entry,
the existing phase monitors/ledger and one startup handshake. See root STATUS
for the exact HAPI target and actual stage evidence. Per-phase TensorBoard
events are under the chain's `tensorboard/`; current server is
http://127.0.0.1:6008. No events are expected before the first smoke update.
The older6007 server retains its old logdir. Source/cleanup are PPO0;
full behavior acceptance is distinct from successful process completion.

## Height-independent R0 bounded verification completed

Review `docs/STANDING_HEIGHT_GATE_REVIEW_20261006.md`. Current prepared spec is
`configs/experiments/recovery_standing_level_v2_20261006/spec.json`. Its authorized
source1/evaluate1/smoke3 have been consumed; formal limit0. Do not resubmit.
Report: `runs/standing_level_v2_check_20261006_151025/completion_report.md`.
Interpreter below is the Conda issaclab Python; cwd is this project root.
Plan-only command reads identities/schema/budget without Isaac/GPU/output writes:

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/preflight.py \
  --spec configs/experiments/recovery_standing_level_v2_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_level_v2_SOURCE_PLAN_ONLY
```

Current source preflight reports phase budget exhausted; formal is unauthorized.
Do not treat the historical plan-only example as a resubmission instruction.
`scripts/prepare_standing_balance.py --recipe height-independent --source-spec ...
--output-dir NEW` creates a new spec/UNAUTHORIZED ledger/synthetic reward probe;
refuses existing output, reads source SHA, preserves old ledger and pose library.
Run with PYTHONPATH=src. CLI help and CPU tests do not start Isaac.

## Autonomous standing preparation (CPU only)

Read `docs/RECOVERY_STANDING_PLAN.md` and
`configs/experiments/recovery_standing_balance_20261006/spec.json` before any
submission. The pure tests are run from the project root with
`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q
tests/test_recovery_standing_balance.py`; they do not import Isaac or
reserve a ledger attempt. Plan-only preflight is:

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/preflight.py \
  --spec configs/experiments/recovery_standing_balance_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_balance_SOURCE_PLAN_ONLY
```

It reports `READY_NEEDS_AUTH` for the unapproved ledger, writes no output,
and reports the required source-only continuous10s runtime baseline. No old
Recovery chain is a substitute: its validator uses a historical short hold.
Only after explicit authorization should the existing launcher/train chain be
used with a fresh output directory and exact HAPI target.

## Recovery training audit (CPU only)

`docs/RECOVERY_TRAINING_AUDIT_20261005.md` records the current Recovery run and the
RNG/curriculum fixes. The changes are covered by
`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q
tests/test_recovery_dense_reward.py tests/test_recovery.py` (27 passed when the
historical stale-YAML identity test is excluded). No Isaac, PPO, ledger reservation,
or output directory is created by these tests.

`/home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_recovery_settling.py
--run runs/recovery_dense_corrected_chain_20261004/formal --output <new.json>`:
cwd project root; reads saved39-column evaluation traces and snapshotted spec;
exclusive-create JSON output only. No Isaac/GPU/PPO/ledger changes. Missing full
velocity/control sequences stay UNKNOWN; checks necessary gates and terminal
wheel targets. Existing selection tool does not compute these gate intervals.

## Corrected Recovery continuation

Current recipe: `configs/experiments/recovery_dense_curriculum_20261004/spec_corrected_direct.json`.
Uses the original experiment ledger (smoke23/formal274 already consumed).
`scripts/prepare_reverse_recovery.py --source-spec ... --output-spec ...` is
offline-only closure/geometry candidate generation, exclusive output creation.
`python -m native_stand.recovery.probe --mode initial --budget-phase formal
--seconds 1.05 --spec ... --output-dir ... --run` starts Isaac/PPO0 and checks
all reverse families using the explicitly charged phase; no new update allowance.
Use `--seconds 1.05` as two CLI arguments. Interpreter is the issaclab Conda
Python; cwd is project root; set `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=0`.
The existing `recovery.train_stages` entry now accepts `--tensorboard-logdir`;
its background supervisor starts/stops a read-only metrics bridge per phase.
Formal begins only after a COMPLETED, finite/changed-actor smoke and exit0.
Current chain: `runs/recovery_dense_corrected_chain_20261004`.

## Current knee-stop Recovery (already submitted)

Evidence and launch identity: [STATUS](STATUS.md),
[experiment details](docs/RECOVERY_KNEE_CONTINUATION_20261004.md).
`scripts/prepare_knee_recovery.py` is a one-time CPU preparation tool that refuses
existing outputs. Do not rerun it over the current experiment.
`recovery.train_stages` uses shared launcher/monitor/ledger to run smoke then formal.
Formal null wall cap is explicit; finite PPO cap remains enforced.
`scripts/watch_recovery_submission.py --output-dir <chain> --hapi-session <id>`
is a background report guard, not a training launcher. It reads exact supervisor
PID/command/output, leaves ledgers unchanged, and notifies only if the formal monitor
has not already done so. Existing HAPI notifier provides locks and event deduplication.
TensorBoard bridge is read-only and uses existing `tools/metrics_tensorboard.py`.

## Reusable motion keyboard GUI

Fixed entry: `scripts/play_motion_keyboard.py`.
See [parameters, model selection and WASD controls](docs/MOTION_KEYBOARD_PLAY.md).
`/home/kellen/anaconda3/envs/issaclab/bin/python scripts/play_motion_keyboard.py --checkpoint /absolute/model.pt --spec /absolute/matching/spec.json --run`
Without `--run`: CPU identity plan only. With it: bounded one-env GUI, no PPO
or checkpoint/ledger writes. GPU0 desktop rendering, GPU1 physics/policy;
supports native150D STAND/motion models, not Recovery or Gym policies.

## Recovery complete chain (already submitted; do not duplicate)

`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.recovery.chain --spec configs/experiments/recovery_r1_manual0001_20261002/spec.json --output-dir runs/NEW --hapi-session CONFIRMED_ID`

Without `--run`: CPU-only plan, no output/ledger mutation. With `--run`: authorized
sequential probes→smoke→formal, actual ledger charges, snapshots/reports and one
final HAPI callback. It refuses occupied/used ledger or existing output. Current
detached submission includes external8095s maximum timeout; exact command and
current output are linked in STATUS. Do not launch another copy while it owns the ledger.

## Manual Recovery pose GUI

Fixed Recovery433 gate diagnosis: see [exact CPU/physical commands](docs/RECOVERY_433_GATE_DIAGNOSTIC.md).
`python -m native_stand.recovery.probe --mode checkpoint` requires explicit
checkpoint and recorded SHA/source spec. Without `--run`: CPU identity plan,
no Isaac/files/ledger. With `--run`: requires new diagnostic budget authorization,
reserves source_eval only,loads actor only,no PPO; original first episodes retained.
Gate/effort records are100Hz,not every5ms PD substep. Safety fault stops evaluation.

Recovery checkpoint preview (no project output/ledger writes, no PPO; default GUI ground is a dark
colored, reflective visual layer with a 1 m grid; it has no collision and does not change the
physical Plane):
`CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python src/native_stand/command_v6/tools/play.py --spec runs/recovery_r1_manual0001_retry_20261002/formal/source_snapshot/spec.json --checkpoint runs/recovery_r1_manual0001_retry_20261002/formal/model_update_200.pt --preview --max-policy-steps 0 --run`

Use `--ground-style solid|none`, `--ground-extent-m M`, or
`--ground-grid-spacing-m M` to change only the GUI appearance.

Current R0 acceptance preview (selected checkpoint, 2026-10-06):

```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/play.py \
  --spec runs/recovery_stage0_stand_from1000_20261005_chain/formal/source_snapshot/spec.json \
  --checkpoint runs/recovery_stage0_stand_from1000_20261005_chain/formal/model_update_1500.pt \
  --preview --ground-style grid --ground-grid-spacing-m 1 \
  --max-policy-steps 0 --run
```

This is a GUI-only preview: PPO updates are zero, no output or ledger entry is
written, and `--max-policy-steps 0` keeps the window running until it is closed
or interrupted with Ctrl-C. The checkpoint SHA is
`c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82`.
The current selection passed the independent `autonomous_hold` 2-second
protocol; this preview is not a 10-second or 100-second acceptance test.

All project GUI paths use the same dark grid visual layer: `play.py`, manual
Recovery pose capture, and the isolated keyboard motion GUI. The layer is
render-only and has no collision or physics material.
Run from project root. Uses the Recovery `preview_family` from the spec, falling
back to `active_family` (R0 for the current corrected run), with the shared FSM
and frozen STAND takeover; ordinary ended episodes reset and repeat.
Close GUI/Ctrl-C to stop. Without `--run`, CPU identity plan only.
Shared GPU0 playback may reduce training throughput. Runtime GUI not yet verified;
CPU preview identity plan passed. Historical stand_plane tests have two external
YAML-identity failures; do not change old specs to bypass those checks.

`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.recovery.capture --spec configs/tools/recovery_capture.json --output-dir runs/NEW_CAPTURE [--run]`

Cwd: project root. Without `--run`: CPU identity/limits/plan, no Isaac/output/ledger.
With `--run`: one-env GUI, actual leg PD or explicit zero-active-effort, no policy/PPO,
new pose JSONs/source snapshots/readback/terminal; refuses existing output.
Keys/slider instructions and exact launch command: [pose capture](docs/RECOVERY_POSE_CAPTURE.md).
Common failures: dependency SHA drift requires an explicit new manual config identity;
runtime closure/nonfinite/ground penetration stops collection and preserves a fault candidate.
Do not weaken protection or automatically admit saved poses to training.

## Current Recovery preparation

Interpreter `/home/kellen/anaconda3/envs/issaclab/bin/python`; cwd
`/home/kellen/wheel_leg_native_train`; use `PYTHONPATH=src` for module CLIs.
Read [STATUS](STATUS.md) and [task instructions/commands](docs/RECOVERY_PREPARATION_20261002.md).

| Entry | Purpose and effects |
| --- | --- |
| `python -m native_stand.recovery.preflight --spec ... --output-dir ...` | CPU source/asset/pose/schema plan; no Isaac/GPU/run/ledger writes. Lists pending geometry/initialization/takeover gates. |
| `python -m native_stand.recovery.prepare --spec ... [--output NEW.json]` | CPU USD closure/collider geometry. Without output prints summary; with output writes new file only and refuses existing file. Not runtime pose certification. |
| `python -m native_stand.recovery.probe --spec ... --output-dir NEW --mode r0` | Plan only by default; `--run` needs new authorized ledger, starts Isaac, frozen-STAND10s takeover near standing, PPO0; source snapshot/result/terminal written. |
| same probe `--mode initial` | Explicit bounded zero-active-effort settling; `--run` additionally requires accepted low-pose geometry definition. PPO0. Partial geometry/self-contact evidence is not automatic training authorization. |
| existing `command_v6/launcher.py --phase smoke/formal --spec Recovery.json` | CPU preflight then detached common trainer/monitor; requires authorized independent budget and runtime prerequisite records. New Recovery PPO only; STAND immutable. Not authorized this session. |

Common failures: SHA/schema/output conflict→fix exact CPU input; pending physical
gate→inspect R0/initial probe evidence; task fall→record failure; nonfinite/closure/
control mismatch→stop and preserve pre-reset evidence. Do not restart or spend old budgets.

## TensorBoard read-only viewer

Current trainer writes JSONL, not event files. `tools/metrics_tensorboard.py`
converts existing numeric summaries to a separate event directory. `--follow`
is a user-launched viewer that reads new lines every5s; it does not modify trainer,
spec, ledger or source metrics, and imports neither Isaac nor PPO. Ctrl-C stops
only the converter. Without follow it exports a snapshot and exits. Re-running
into the same event directory can duplicate scalar steps; use a fresh view
directory when restarting. Partial trailing lines are left unread until complete.

## Current authorized standing chain — already submitted

Do not repeat this exact submission:

```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/stand_chain.py \
  --spec configs/experiments/stand_long_20261001/spec.json \
  --output-dir runs/stand_long_20261001_205100 \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

Help/omitted launch is CPU-only and creates no run/reservation. Actual launch
snapshots the shared code, checks the authorized target, creates a detached chain,
and waits once up to240s for a formal actual-update/PID identity handshake.
UNKNOWN never permits resubmission. The current handshake confirmed RUNNING.

Current paths: chain_progress.json/startup_handshake.json plus active phase
progress; final chain_terminal_report.json/analysis.json/candidate_selection.json/
completion_report.md/notification marker. Each phase directory retains its own
log and terminal. Checkpoints100, full screening500, no light screening.
Final100s uses public evaluate_checkpoint,64-env layout/8 scored/reset-first,
PPO0 and a separate600s wall allowance. Ordinary behavior failure is reported,
not used to auto-append a training chain. No interactive polling is required.

## Completion and submission

Interpreter `/home/kellen/anaconda3/envs/issaclab/bin/python`, cwd this project's
root. Help/plan parse before Isaac import, no run/ledger write. Actual launches
remain blocked by the unapproved ledger.

```bash
cd /home/kellen/wheel_leg_native_train
/home/kellen/anaconda3/envs/issaclab/bin/python src/native_stand/command_v6/launcher.py \
  --spec configs/experiments/stand_plane.json --phase formal --output-dir runs/PLAN_ONLY \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1
```

After fresh source-only authorization, submit to this confirmed session:

```bash
CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/launcher.py --spec configs/experiments/stand_plane.json \
  --phase source_eval --output-dir "runs/source_plane_$(date +%Y%m%d_%H%M%S)" \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

This starts simulation, PPO0, reserves source allowance and writes a fresh run
and sidecars. Smoke/formal use the same entry, start PPO and need their own
authorized budget/prerequisites. A PID alone is not success: one handshake
checks actual progress or returns UNKNOWN without relaunch. Explicit target
overrides CLI `HAPI_SESSION_ID`; missing target keeps local reports only.

Read-only summary (no sim/PPO):

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python src/native_stand/command_v6/tools/summarize_run.py --run-dir /absolute/run
```

Local report generation (writes reports/readiness only; no sim/PPO/notification):

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python src/native_stand/command_v6/tools/completion.py --run-dir /absolute/run
```

`--notify` explicitly sends at most once to the captured manifest target after
readiness. `--acknowledge-review` records reviewed only after actual review; no
send/training. Ready reports return unchanged. Missing snapshots/report errors
are saved as completion_error by monitor. JSONL truncated tail is reported while
earlier records remain readable. No notification test was sent in this task.

Interpreter: `/home/kellen/anaconda3/envs/issaclab/bin/python` (Python 3.12,
Torch 2.10.0+cu128, Isaac Sim 6.0.1.0, Isaac Lab 6.1.14, RSL-RL 5.0.1).
Working directory for all commands: `/home/kellen/wheel_leg_native_train`.
Commands were checked against their safe `--help` and code; `--help` and
plan-only exit before AppLauncher. Keep every output path new. The ledger is
`configs/experiments/budget.json`; currently no phase is authorized.

| Entry | Input and exact command | Side effects and failure evidence |
| --- | --- | --- |
| CPU tests | `P=/home/kellen/anaconda3/envs/issaclab/bin/python; "$P" -m pytest -q` | No Isaac/PPO/run output. Failure identifies pure contract, warmstart, ledger or preflight drift. |
| CPU preflight | `P=/home/kellen/anaconda3/envs/issaclab/bin/python; "$P" src/native_stand/command_v6/tools/preflight.py --spec configs/experiments/stand_plane.json --phase source_eval --output-dir runs/PLAN_ONLY` | Reads source and asset SHA, actor/critic/Adam, spec and ledger; no Isaac, GPU, PPO or output creation. `READY_NEEDS_AUTH` is the expected current result. Only `PASS` permits `--launch`. |
| Ledger audit | `P=/home/kellen/anaconda3/envs/issaclab/bin/python; "$P" src/native_stand/command_v6/tools/validate_ledger.py --ledger configs/experiments/budget.json` | Read-only; mismatch of exact attempts or counts is a stop condition. |
| Run summary | `P=/home/kellen/anaconda3/envs/issaclab/bin/python; "$P" src/native_stand/command_v6/tools/summarize_run.py --run-dir runs/RUN_ID` | Read-only; terminal absence remains explicit. |
| Source-only standing | `CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python src/native_stand/command_v6/launcher.py --spec configs/experiments/stand_plane.json --phase source_eval --output-dir "runs/source_plane_$(date +%Y%m%d_%H%M%S)" --launch` | **Not yet authorized.** After approval: one Isaac process, no PPO, background monitor; new manifest/source snapshot/progress/evaluation/terminal and exact ledger attempt. First read terminal and evaluation per env. |
| PPO wiring smoke | Same launcher shape with `--phase smoke` and fresh `runs/smoke_*` | **Not yet authorized.** After source evaluation and separate approval: up to 3 updates/24,576 samples; source actor/critic/Adam, reset and finite reward/loss. Ordinary fall is task data. |
| Formal standing | Same launcher shape with `--phase formal` and fresh `runs/formal_*` | **Not yet authorized.** Up to 200 updates/1,638,400 samples or 3600 s, whichever first; checkpoint/light evaluation every 100, full 10 s at 200. Read `candidate_selection.json` alongside terminal and per-env evaluation; latest saved, best observed and accepted are distinct. A 2 s light-window completion is not a standing pass. |
| Independent evaluation | `P=/home/kellen/anaconda3/envs/issaclab/bin/python; "$P" src/native_stand/command_v6/tools/evaluate_checkpoint.py --spec configs/experiments/stand_plane.json --checkpoint /absolute/model.pt --output runs/evaluation_NEW.json --vx 0 --yaw 0 --seconds 10` | Without `--run`: no Isaac/write. With `--run`: needs separately authorized `evaluate` allowance; uses the same env and deterministic actor, no PPO; writes fresh result/terminal sidecar and exact ledger attempt. External hard timeout must bound process. Missing terminal/result is not behavior failure. |
| GUI play | `P=/home/kellen/anaconda3/envs/issaclab/bin/python; "$P" src/native_stand/command_v6/tools/play.py --spec configs/experiments/stand_plane.json --checkpoint /absolute/model.pt --output runs/play_NEW.json --max-policy-steps 0` | Without `--run`: no Isaac/write. With `--run`: requires a separately approved `play` attempt and opens the Kit GUI with the same zero-command plane environment, no PPO. Close the window or Ctrl-C. GUI is not independent acceptance. |

For source-only, smoke and formal, launcher reserves the exact attempt, starts
one detached monitor with an external hard timeout including 30 s kill grace,
and performs one bounded startup handshake. `UNKNOWN` handshake status means
read the background terminal later; it is not permission to submit again.
The runtime scene verifies the composed Plane/material and active control
readback before policy sampling. Historical runs remain outside this project.

After a separate `evaluate` allowance is granted, one complete bounded
source/candidate check uses the current spec and an unused output filename:

```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 timeout -s TERM -k 15 285s \
  /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/evaluate_checkpoint.py \
  --spec configs/experiments/stand_plane.json \
  --checkpoint /absolute/model.pt --output "runs/evaluation_$(date +%Y%m%d_%H%M%S).json" \
  --vx 0 --yaw 0 --seconds 10 --full-trace --run
```

This command is **not authorized now**. The direct evaluator reserves an
`evaluate` attempt before AppLauncher and writes a result plus terminal
sidecar; the 285+15 s bound includes SIGTERM cleanup. A timed-out or missing
result is incomplete, not a strategy fall.
# Height40 chain entry

Interpreter: `/home/kellen/anaconda3/envs/issaclab/bin/python`.
Working directory: `/home/kellen/wheel_leg_native_train`.
Current submission: `runs/height40_from500_20261002_night`; **do not resubmit**.
Read STATUS, the chain progress/startup handshake, then phase progress/terminal
and the exact experiment ledger. Read-only inspection does not launch Isaac/PPO.

The public submitted command is:
```bash
CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/stand_chain.py \
  --spec configs/experiments/height40_from500_20261002/spec.json \
  --output-dir runs/height40_from500_20261002_night \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```
This creates immutable snapshots and new phase outputs, reserves/charges the
transferred budget, starts Isaac/PPO and captures one formal-start handshake.
It is documented for provenance, not authorization to start another chain.
UNKNOWN handshake means consult the eventual terminal report; do not retry.
# Recovery Self-Standing Preparation (2026-10-03)

[Design, CPU plans and proposed budget](docs/RECOVERY_SELF_STAND_20261003.md).
Existing Recovery probe checkpoint mode uses fixed1500 and new autonomous2s
criteria; no optimizer/PPO. Existing launcher is the sole smoke/formal entry.
Plans are read-only. `--run` starts simulation and writes an exact attempt;
new ledger is UNAUTHORIZED. Old completed run budgets are not used.
No new trainer or version package was introduced.

````
