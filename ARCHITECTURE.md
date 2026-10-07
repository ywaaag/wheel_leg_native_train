# Execution chain

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
