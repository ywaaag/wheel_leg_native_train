# Files created for the long-term project

## 2026-10-06 survival/level R0 -> R1 authorized implementation

Changed recovery/{domain.py,standing.py,runtime.py,validation.py,recipe.py,selection.py},
command_v6/{config.py,completion.py,train.py,tools/evaluate_checkpoint.py},
scripts/prepare_standing_balance.py. Added tests/test_standing_survival_level.py,
configs/experiments/recovery_survival_level_from50_20261006/{spec,budget,poses,reward_probe}.json,
docs/RECOVERY_SURVIVAL_LEVEL_20261006.md; updated STATUS/README/ARCHITECTURE/
TOOL_INDEX/RECOVERY_STANDING_PLAN and this log. Explicit new goal with legacy defaults,
40% R0 rehearsal, independent retention evaluation and matching ranking.
58focused and80general checks pass; fresh preflight PASS. Historical models/specs/results/ledgers
and USD unchanged. User authorized10000totalupdates; source8/8physical10s,
3smokeactual actor update, one formal RUNNING/actual1 handshake. New run logs,
source snapshots and TensorBoard6013 process metadata are runtime artifacts.

## 2026-10-06 user-approved survival/level objective

Updated STATUS.md and docs/RECOVERY_STANDING_PLAN.md to record GUI-approved
scissor update50 identity and the revised goal. Next stage is near-standing R1,
not captured low-pose R2. New gate values remain proposals for a fresh spec.
Historical evaluations/selection/specs/ledgers unchanged; no simulation or PPO.
Source checkpoint SHA recalculated; changed files are these two documents and
this change log.

## 2026-10-06 wheel-center alignment probe

Changed recovery/{domain.py,standing.py,runtime.py,recipe.py,validation.py,
asset_poses.py}, command_v6/{train.py,stand_chain.py},
scripts/prepare_standing_yaw.py and tests/test_standing_scissor_audit.py.
Added configs/experiments/standing_scissor_20261006/{spec.json,budget.json},
docs/STANDING_SCISSOR_EXPERIMENT_20261006.md; updated STATUS/ARCHITECTURE/TOOL_INDEX.
53focused CPU checks pass, preflight PASS; runtime remains separately gated.
Only53unused updates debited in old ledger; original run/attempt/model retained.

## 2026-10-06 scissor geometry offline diagnostic

Added scripts/audit_standing_scissor.py, tests/test_standing_scissor_audit.py,
docs/STANDING_SCISSOR_REVIEW_20261006.md and new pair scissor_geometry_review.json.
Updated STATUS/TOOL_INDEX.4CPUfixtures pass;96saved observation reconstructions
closure-valid. No trainer/runtime/reward/spec/physics/PPO/budget change.

## 2026-10-06 BC gradient and annealing comparison

Changed src/native_stand/recovery/{standing.py,validation.py} and
src/native_stand/command_v6/train.py for BC schedule/channel scope, gradient
evidence and compact selected-update payloads. Added command_v6/retention_ab.py,
scripts/prepare_standing_bc_ab.py, tests/test_standing_bc_diagnostics.py,
tests/test_standing_bc_ab_workflow.py, docs/STANDING_BC_AB_20261006.md and two
independent config/ledger arms. Updated STATUS/README/ARCHITECTURE/TOOL_INDEX.
RECOVERY_STANDING_PLAN navigation also points to the new pair.
63focused tests pass; source preflights PASS. Old ledger only debits206unused
updates through existing locked transfer; old run/attempt/evaluation preserved.

## 2026-10-06 yaw-only intervention

Changed recovery `domain.py`, `validation.py`, `recipe.py` and shared `train.py`
for optional canonical-Y yaw reward/schema/GPU field and pre-reset CLI diagnostics.
Changed `ledger.py` for explicit smoke count in existing atomic transfer;
`stand_chain.py` for explicit controlled-test durability opt-out (default unchanged).
Added `scripts/prepare_standing_yaw.py`, `tests/test_standing_yaw_intervention.py`,
two independent experiment directories, diagnostic result and
`docs/STANDING_YAW_REVIEW_20261006.md`. Updated STATUS, TOOL_INDEX, ARCHITECTURE,
RECOVERY_STANDING_PLAN.55focused CPU tests pass. Old run/attempt/evaluation unchanged;
only unused formal allowance is explicitly debited in its ledger.
Runtime: update400 PPO0 channel diagnostic completed in16.52s. New source and
3smoke completed; detached formal handshake confirmed1actual update. This proves
runtime wiring, not behavioral improvement. README navigation and comparison
TensorBoard6010 were also updated.

## 2026-10-06 height-independent formal continuation

User authorized2000formal updates with no wall-clock limit,16,384,000samples.
New `configs/experiments/recovery_standing_level_v2_long_20261006/{spec.json,budget.json}`
references original completed source/smoke evidence; no old run/ledger is rewritten.
Added `scripts/prepare_standing_long.py` and `tests/test_standing_evidence_reuse.py`.
Changed `src/native_stand/command_v6/tools/preflight.py` to verify immutable
prior spec identity and allow only submission metadata differences for evidence reuse.
Changed `src/native_stand/command_v6/tools/metrics_tensorboard.py` to support
background `--wait-for-metrics`. Updated STATUS, README, ARCHITECTURE and TOOL_INDEX.
38focused CPU checks pass, formal preflight PASS. Existing launcher/monitor/train
started detached; handshake confirmed1actual update. No post-start training polling.
No additional reward/control/observation/asset change in this submission.

## 2026-10-06 bounded v2 runtime verification

Updated only v2 `spec.json` authorization scope/chain bound and `budget.json`
to source1/evaluate1/smoke3/formal0,900s cumulative physical wall,24,576samples.
Executed existing shared `stand_chain.run_phase`/monitor/trainer for source/smoke,
and existing independent checkpoint evaluator for the candidate; no new trainer.
New artifacts under `runs/standing_level_v2_check_20261006_151025/`: immutable
code/spec snapshots, exact phase attempts/logs, smoke checkpoint, full evaluations,
selection, metrics, terminal/progress, verification_summary and completion report.
Updated STATUS, README, TOOL_INDEX and RECOVERY_STANDING_PLAN navigation.
81 CPU/fake-process checks passed before physics. Actual runtime completed
3PPO updates/24,576samples; source and smoke3 both0/8 strict acceptance.
No runtime implementation, reward coefficient, USD, old ledger or old run changed.

## 2026-10-06 stopped chain and height-independent repair

Changed `src/native_stand/recovery/{domain.py,standing.py,validation.py}` for
explicit validated reward gates; defaults preserve old height-gated formulas.
Changed `scripts/prepare_standing_balance.py` to create a separate corrected
recipe and synthetic raw/weighted/dt probes. Added
`configs/experiments/recovery_standing_level_v2_20261006/{spec.json,budget.json,reward_probe.json}`.
Changed shared `src/native_stand/command_v6/stand_chain.py`: exact smoke count,
user-stop chain finalization, no next phase/durability after stop, exit conflict preserved.
Added `tests/test_standing_height_independent.py`; made existing
`tests/test_recovery_standing_balance.py` ledger fixtures independent of mutable
run usage; updated `tests/test_stand_chain.py` fixture with explicit smoke budget.
Updated STATUS, ARCHITECTURE, TOOL_INDEX, RECOVERY_STANDING_PLAN and
added `docs/STANDING_HEIGHT_GATE_REVIEW_20261006.md`.

The existing user-stop request artifact and normal monitor settlement belong
to the old run. Old terminal reports, checkpoints, execution snapshot/spec and
charged ledger usage are not rewritten. New recipe is CPU only/UNAUTHORIZED.

## Authorized standing submission 2026-10-06

Updated the unsubmitted standing-balance spec/ledger to3smoke+9997formal
updates,81920000samples and36000s total. Added an isolated
`configs/experiments/recovery_standing_balance_20261006/execution_snapshot/src/native_stand`
for this run; its only extra changes are the chain's total wall supervision,
strict smoke-count gate, waiting TensorBoard bridge and100s certificate label.
The active motion trainer retains its original shared source. Added
`tests/test_standing_balance_submission.py`: immutable-snapshot suite81passes.
Run `recovery_standing_balance_20261006_chain_1140` is detached; its one startup
handshake is UNKNOWN while source baseline runs. No interactive log polling.

## 2026-10-06 autonomous standing preparation (CPU only)

Added `docs/RECOVERY_STANDING_PLAN.md`,
`configs/experiments/recovery_standing_balance_20261006/{spec.json,poses.json,budget.json}`,
and `scripts/prepare_standing_balance.py`. Added pure standing geometry/gates
and retention in `src/native_stand/recovery/standing.py`; extended the Recovery
domain, runtime snapshots, evaluator, selection, trainer plan, and preflight
for continuous ten-second evidence. Added
`tests/test_recovery_standing_balance.py` with reset-corruption fixtures. No
Isaac/PPO was launched and no old run, checkpoint, USD, or ledger was overwritten;
the new ledger remains `UNAUTHORIZED`.

Changed implementation files:
`src/native_stand/recovery/{domain.py,runtime.py,recipe.py,selection.py,validation.py,preflight.py}`,
`src/native_stand/command_v6/{train.py,config.py,completion.py,tools/preflight.py}`.
Navigation changes: `AGENTS.md`, `README.md`, `STATUS.md`, `ARCHITECTURE.md`,
`TOOL_INDEX.md`, and this file. Verification:78 focused CPU passes; full suite
159 passes/7 historical external-YAML identity failures. The new recipe's
source-only preflight is CPU-valid and `READY_NEEDS_AUTH`. No runtime claim.

Offline settling review2026-10-04: added `scripts/review_recovery_settling.py`,
`tests/test_recovery_offline_settling.py`; added `SETTLING_REVIEW_20261004.md`
and `review_settling_offline_20261004{,_v2}.json` in corrected formal run.
Updated STATUS and TOOL_INDEX only; no trainer/reward/spec/asset/ledger change.
10CPUtests passed; no new simulation/PPO or HAPI test notification.

## Recovery correction 2026-10-04

Modified implementation:
- `src/native_stand/recovery/domain.py`: normalized wheel cost; complete-episode stage windows.
- `src/native_stand/recovery/runtime.py`: actual reset-stage wiring, GPU event buffers, per-pose initialization, height summaries.
- `src/native_stand/recovery/recipe.py`: evaluation suspends curriculum collection.
- `src/native_stand/recovery/preflight.py`: reject missing stage families/bounds.
- `src/native_stand/recovery/probe.py`: explicit budget phase; all-family initialization diagnostics.
- `src/native_stand/recovery/train_stages.py`: TensorBoard bridge per phase.
- `src/native_stand/command_v6/tools/preflight.py`: validate reverse families; remove unsafe bounded-smoke fallback.
- `src/native_stand/command_v6/ledger.py`: remove unsafe bounded-smoke fallback.
- `src/native_stand/command_v6/tools/metrics_tensorboard.py`: SIGTERM flush/close.
- `tests/test_recovery_dense_reward.py`: full-window, stage-isolation, normalized-cost regressions.

Added `scripts/prepare_reverse_recovery.py`, and immutable corrected recipes/pose
libraries in `configs/experiments/recovery_dense_curriculum_20261004/`:
`spec_corrected.json`, `poses_corrected.json`, `spec_corrected_direct.json`,
`spec_corrected_direct_poses.json`. The first recipe failed runtime initialization;
the direct-reset recipe passed initialization and is the submitted recipe.
Updated `STATUS.md`, `ARCHITECTURE.md`, `TOOL_INDEX.md`, and this index.
Existing budget.json receives normal exact-attempt charges only; old attempts,
source checkpoint, USD and historical evaluations remain untouched.

Evidence:39focusedCPUtests passed; one historical YAML-identity test excluded.
Four runtime families x train/holdout initialization passed. Corrected smoke
handshake confirmed trainer3063424 with real PPO updates. Initialization evidence
does not certify recovery success; formal remains conditional on completed smoke.

## Read-only TensorBoard viewer

Added `src/native_stand/command_v6/tools/metrics_tensorboard.py`; updated this
file and TOOL_INDEX. This is not imported by running training and only reads
metrics JSONL; event output goes to a separate viewer directory. No runtime
training file/config or budget changed.

## 2026-10-01 authorized adaptive standing

Added `configs/experiments/stand_long_20261001/spec.json` and independent
`budget.json`; `src/native_stand/command_v6/stand_chain.py`,
`domain/episode_curriculum.py`; `tests/test_episode_curriculum.py`,
`tests/test_stand_chain.py`. Changed shared kernel `config.py`, `runtime/env.py`,
`runtime/configure.py`, `train.py`, `monitor.py`, `domain/metrics.py`,
`tools/evaluate_checkpoint.py`. Navigation changes: AGENTS/README/STATUS/
ARCHITECTURE/TOOL_INDEX/this file. Spec schema version stays6, experiment identity
is new; no new command-version source directory. Old budgets/runs/assets/models
and reference repositories are unchanged. All executable edits/tests finished
before submission; while running, only non-runtime documentation was updated.

## 2026-10-01 automation increment

Added `src/native_stand/command_v6/completion.py`,
`src/native_stand/command_v6/tools/completion.py`, `tests/test_completion.py`,
and `docs/automation_example/{README.md,analysis.json,candidate_selection.json,completion_report.md}`.

Changed `src/native_stand/command_v6/train.py`, `launcher.py`, `monitor.py`,
`domain/metrics.py`, `tools/preflight.py`, `tools/summarize_run.py`,
`tests/test_preflight_ledger.py`, plus `STATUS.md`, `ARCHITECTURE.md`,
`TOOL_INDEX.md` and this file. All code paths here are under the same kernel
directory; no new version tree was copied.

Notification lock/transport is a minimal adaptation of read-only Fudan
`plane/wheel_legged_gym/adapters/notifications/hapi.py`; workflow candidate
screening/completion and app completion supplied identity/readiness concepts.
Gym imports, turning metrics, job schema and old ack paths are not reused.
No reward/physics/observation/curriculum/spec values or real budgets changed.
Examples are synthetic CPU fixtures, not trained model evidence.

No source or artifact outside `/home/kellen/wheel_leg_native_train` was edited.
The new Git repository has no commit yet. Historical audit runs remain at
their original paths. `src/native_stand/command_v6` carries **one** selected
v6 implementation kernel; it is not a fresh experiment-version copy.

## Navigation and configuration

- `.gitignore`, `pyproject.toml`, `runs/.gitkeep`
- `AGENTS.md`, `README.md`, `STATUS.md`, `ARCHITECTURE.md`, `TOOL_INDEX.md`
- `configs/contracts/source_B200.json`
- `configs/experiments/stand_plane.json`, `configs/experiments/budget.json`
- `docs/EXPERIMENT_PLAN.md`, `docs/REUSE_DECISIONS.md`, `docs/CHANGED_FILES.md`

## Native physical scene

- `src/native_stand/__init__.py`, `src/native_stand/contract.py`: copied from
  the native experiment source for the single physical-joint control path.
- `src/native_stand/env.py`: copied source with the mesh collider replaced by
  a spec-configured physical USD Plane and explicit material. It no longer
  injects the colleague module path at import.
- `src/native_stand/control_readback.py`: active/passive actuator readback
  extracted from the old native trainer so runtime no longer imports a CLI.

## Audited v6 kernel retained in one package

- `src/native_stand/command_v6/__init__.py`, `config.py`, `learning.py`,
  `ledger.py`, `launcher.py`, `monitor.py`, `train.py`
- `src/native_stand/command_v6/domain/__init__.py`, `command_schedule.py`,
  `contract.py`, `metrics.py`, `protocol.py`, `reward.py`, `warmstart.py`
- `src/native_stand/command_v6/runtime/__init__.py`, `configure.py`,
  `control_readback.py`, `env.py`
- `src/native_stand/command_v6/tools/__init__.py`, `preflight.py`,
  `summarize_run.py`, `validate_ledger.py`, `checkpoint_input.py`,
  `evaluate_checkpoint.py`, `play.py`

New project changes relative to old v6 include the plane/material identity,
spec-owned control/reward/schedule wiring, zero-command active stage, a new
unspent ledger, source-only behavior reporting, evaluator standing window,
and separately budgeted evaluate/play phases. `domain/command_schedule.py`,
`domain/metrics.py`, `domain/protocol.py`, and `domain/warmstart.py` retain the
audited pure calculation logic; no third-party Wheelbipe code was copied.

## CPU tests

- `src/native_stand/command_v6/tests/test_domain.py`
- `src/native_stand/command_v6/tests/test_preflight_ledger.py`
- `tests/test_stand_plane_contract.py`

All are CPU-only. They cover 25D/125D reset/history, B200 actor/critic/Adam
expansion, reward, terminal snapshot, ledger isolation, authorization gate,
fixed standing spec, candidate identity and plan-only CLI side effects. They do not establish
plane runtime physics equivalence.

The 2026-10-01 review fixed only existing project files:
`src/native_stand/command_v6/domain/warmstart.py`, `domain/protocol.py`,
`train.py`, `tools/evaluate_checkpoint.py`, the two kernel CPU test files,
and `STATUS.md`, `ARCHITECTURE.md`, `TOOL_INDEX.md`,
`docs/EXPERIMENT_PLAN.md`, `docs/CHANGED_FILES.md`. No source model,
physics asset, reward weight, gate threshold, old run or budget was changed.
# 2026-10-01: formal update 500 evaluation reset repair

- `domain/episode_curriculum.py`: retain the normal persistent peaks tensor with `copy_`; inference-mode temporary values must not replace mutable episode buffers.
- `train.py`: record terminal/ledger exit code and pass it to installed `SimulationApp.close(exit_code=...)`; fast shutdown can bypass Python's subsequent raise.
- `tests/test_episode_curriculum.py`: inference collection followed by normal local reset, unchanged non-reset environment, and fake-app failure/success exit-code tests.
- CPU suite: 65 passed. Original failed run/ledger records unchanged. Independent update-500 10s evaluation is a separate PPO=0 attempt; it does not resume training.
# 2026-10-02: Recovery preparation and stop/statistics repairs

- Shared kernel: `command_v6/train.py`, `config.py`, `completion.py`,
  `tools/preflight.py`, `domain/contract.py`, `runtime/env.py`.
  Fix post-AppLauncher signal ownership and disabled-projection occupancy;
  explicit Recovery task dispatch, immutable snapshots, task-specific selection.
- New task modules in `src/native_stand/recovery/`: `__init__.py`, `domain.py`,
  `asset_poses.py`, `prepare.py`, `runtime.py`, `recipe.py`, `validation.py`,
  `selection.py`, `preflight.py`, `probe.py`.
- New pending experiment: `configs/experiments/recovery_r1_20261002/spec.json`,
  `budget.json`, `poses.json`. Budget remains UNAUTHORIZED/used0.
- CPU fixtures: `tests/test_recovery.py`;93 tests passed. Independent evaluator dispatches the Recovery recipe; GUI rejects unsupported Recovery playback before Isaac initialization.
- Navigation: README, STATUS, ARCHITECTURE, TOOL_INDEX and this index;
  `docs/RECOVERY_PREPARATION_20261002.md` records measured geometry limitations,
  unverified runtime gates, commands and proposed budget.
- No source repository/USD/checkpoint/historical run or ledger was changed.

## Manual pose GUI, 2026-10-02

- Added `src/native_stand/recovery/capture.py`, `capture_controls.py`, `capture_runtime.py`:
  one-env keyboard/slider manual targets, zero-effort settling, timeline pause/reset,
  exclusive candidate records, source/config snapshots and terminal cleanup. No policy/PPO.
- Added `configs/tools/recovery_capture.json`: explicit current YAML identity, historical base-spec unchanged.
- Added `tests/test_pose_capture.py`: five CPU tests (controls/limits, nonfinite input,
  tilted/scaled support geometry, CLI no side effects, exclusive save).
- Added `docs/RECOVERY_POSE_CAPTURE.md`; updated STATUS, ARCHITECTURE and TOOL_INDEX.
- No runtime GUI was launched. Shared training code, assets, old specs, models, ledgers unchanged in this task.

## User-confirmed linkage support and captured R1 pose

- `recovery/domain.py`, `runtime.py`, `validation.py`: contact patterns are explicit
  configuration; linkage expansion requires user confirmation; unmatched bodies stay
  restricted and empty restricted groups are supported. Physical protection unchanged.
- New `configs/experiments/recovery_r1_manual0001_20261002/{spec,budget,poses}.json`:
  measured manual0001 posture, independent pending budget, frozen STAND identity,
  current external YAML pinned; old recipes and records unchanged.
- `tests/test_recovery_manual_support.py`: weak-part classification and authorization tests.
- `docs/RECOVERY_MANUAL0001_START.md` and STATUS: actual readiness/evidence/budget pending.
-25 related CPU regressions and new CPU preflight pass; no runtime test or PPO executed.

## Authorized Recovery chain submission

- Added `recovery/chain.py` and `tests/test_recovery_chain.py`: thin sequential
  bounded workflow, actual gate validation, smoke actor-change gate, exact reconciliation,
  report and single final HAPI notification. Existing trainer/monitor reused.
- `recovery/probe.py`: optional actual physical-progress handshake; initial acceptance
  checks all64environments, not just8scored. Evaluator optional progress callback.
- Manual0001 spec/ledger: explicit user authorization recorded, all counters initially0;
  no validated physical gate fabricated. Immutable probe snapshots precede later gate publication.
-27relatedCPU tests pass; one real R0 handshake verifies first physical step, not PPO.
-STATUS/ARCHITECTURE/TOOL_INDEX link real chain, limits and terminal evidence.
# 2026-10-05 Recovery training audit

- `src/native_stand/command_v6/domain/warmstart.py`: explicit training RNG seed and
  evaluation RNG preservation helpers.
- `src/native_stand/command_v6/train.py`: opt-in source RNG restore, preserve RNG around
  milestones, restore/save Recovery curriculum state, report actual Recovery stage.
- `src/native_stand/recovery/domain.py`: serialize/restore pending and completed reverse
  curriculum windows.
- `src/native_stand/recovery/runtime.py`: checkpoint state adapter and stage restoration.
- `src/native_stand/recovery/recipe.py`: standalone evaluator restores RNG state.
- `configs/experiments/recovery_dense_curriculum_20261004/spec_corrected_direct.json`:
  explicit `restore_source_rng=false` and `restore_recovery_curriculum=true`.
- `tests/test_recovery_dense_reward.py`: CPU tests for seed isolation, evaluator RNG and
  curriculum checkpoint continuation.
- `docs/RECOVERY_TRAINING_AUDIT_20261005.md`, `STATUS.md`, `ARCHITECTURE.md`,
  `TOOL_INDEX.md`: evidence and entry-point updates.
