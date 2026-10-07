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

Version-control entry: [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md). Commit source,
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
