# Status

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
