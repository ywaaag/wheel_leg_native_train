# Native interface and evidence changes

2026-10-07. Engineering-only change: no Isaac/AppLauncher, online PPO, continuation,
new budget, reward/physics/optimizer recipe modification, or historical evidence overwrite.

## Delivered interfaces

- `domain/evidence.py`: explicit effective protocol validation and deterministic SHA;
  timing, frequency, first-episode semantics and metric scopes; unknown fields rejected.
  Recovery owns its thresholds, while evaluator timing is explicit. Short evaluation
  does not relax the original minimum full acceptance duration.
- `resolve_gate`: task-specific gate normalization with PASSED, FAILED, NOT_RUN,
  MISSING_EVIDENCE, CONFLICTING_EVIDENCE; raw gate, missing fields, conflicts and
  candidate eligibility remain visible. Missing and conflicting evidence cannot pass.
- Recovery diagnostics: CLI request OR runtime spec; runtime switch restored after
  evaluation; absent arrays are null with validity metadata. Pre-reset controls and
  terminal snapshots retain their existing provenance. Policy-end sampling is not
  a complete 5ms PD-substep saturation audit.
- Generic evaluator: height/velocity metrics use the explicit scored window and stop
  metrics use the explicit parking window. Legacy direct `score` calls retain legacy
  behavior when no effective protocol is passed. New evaluations therefore disclose
  their corrected scopes; they must not be mixed silently with old evaluations.
- `health_check`: document links, current spec identities, source checkpoint metadata,
  budgets, unsettled attempts, run accounting and candidate SHA; optional one-shot
  process/GPU snapshot. No process is stopped and no ledger is reserved. A process
  list without matched attempt/output/start identity remains UNKNOWN.
- Preflight retains PASS/FAIL/READY_NEEDS_AUTH and adds reason_code/action. Codes:
  OK, CONFIG_ERROR, IDENTITY_ERROR, BUDGET_EXHAUSTED, AUTHORIZATION_MISSING,
  UNSETTLED_ATTEMPT, MISSING_EVIDENCE. Process identity checking additionally emits
  PROCESS_IDENTITY_MISMATCH. Behavior failure is distinct from an infrastructure error.
- `wiring.py`: one shared smoke certificate validator, tied to frozen spec/source,
  actual updates, actor changes, terminal and recorded evaluation paths. No hardcoded
  10-update count or evaluation filename. High-speed preflight and ledger both use it.
- `supervisor`: read-only default; explicitly launched chains use the existing owned
  monitor-child workflow. Source -> smoke certificate -> formal -> reconciliation.
  External-PID/pidfd continuation is removed. Submission requires an explicit GPU.
  Handshake checks manifest/spec/attempt/output, actual first PPO update and both
  trainer/monitor identities; uncertainty stays UNKNOWN.
- `play.py`: fixed confirmed UnboundLocalError in non-preview plan-only path.
- P2 `domain/selected_diagnostics.py`: default disabled; only configured update IDs.
  Actual reward total, completed-duration summaries, available storage values/returns/
  normalized advantages, real optimizer-input gradient norms, optional reward/task
  summaries, eligible/selected retention counts, captured ages/commands/channel error.
  No PPO distribution or loss is changed. Existing BC/PPO probes are reported only
  when actually available; absent probes remain null. Optimizer gradients are sampled
  after existing clipping/retention hooks, aggregated over minibatches, not per-sample
  or a reward-specific causal decomposition.

## CPU validation

Use the project interpreter, without importing Isaac:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

All source modules and both changed scripts also passed in-memory `compile()`;
73 files, no pycache writes. Full CPU suite: **268 passed**. Protocol fixtures cover 1/10/100 seconds, duration/windows,
unknown fields, timeout/task failure/runtime fault/early termination, gate states,
zero-versus-missing diagnostics, real gradient observer invariance, certificate,
exclusive report output and UNKNOWN handshake. Existing notification/chain/ledger
fixtures are included. Live GPU execution and detached handshakes were not tested.

Old tests assumed consumed budgets were still available or imported code had to be
inside a historical snapshot. They now test consumed-budget classification and the
actual snapshot launch contract. Dependency identity tests use fresh temporary CPU
fixture specs; no historical SHA, spec or budget was rebased on the current YAML.

Plan-only source evaluation reports READY_NEEDS_AUTH / BUDGET_EXHAUSTED,
cpu_valid=true; simulation=0, ppo=0, files_written=0. Output remains absent.
Health snapshot found no matching native trainer/monitor commands; GPU compute
processes were recorded read-only. This is not permission to use either GPU.

## Corrected offline outputs

All outputs are new, exclusive-created files under `isolated/interface_evidence_20261007/`:

- `recovery_corrected_v2/audit.json`, `audit.md`, `audit_manifest.json`: frozen
  Recovery implementation and input SHA; source100s is 8/8 using [2,100], no saved
  metric mismatch. Continuous and success/failure event rewards are separate;
  unrecorded timeout event contribution remains null. Legacy gate arrays from a
  disabled runtime are invalid, not measured zeros. Missing historical gradients
  remain UNKNOWN.
- `high_speed_corrected/corrected_analysis.json`, `corrected_report.md`,
  `audit_manifest.json`: 14 historical evaluations, identities preserved.
- `cohort_width_corrected/`: same three files, 10 B evaluations.
- `reference_corrected_v2/`: same three files, actual reference bundle SHA, shape,
  command counts and age span. Manifest/progress/terminal/selection are absent in
  this bundle-only directory and remain UNKNOWN.

Earlier corrected/v1 outputs are retained rather than overwritten. Motion reports
do not assign new acceptance or invent missing effective protocol identity.

Read-only commands:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.tools.health_check \
 --project-root /home/kellen/wheel_leg_native_train \
 --spec configs/experiments/recovery_survival_level_from50_20261006/spec.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.supervisor \
 --spec configs/experiments/recovery_survival_level_from50_20261006/spec.json \
 --output-dir isolated/interface_evidence_20261007/PLAN_ONLY_UNCREATED
```

The second command is plan-only. Adding `--launch` is a new simulation action and
requires explicit applicable authorization; unused historical quota is insufficient.

## Exact changed files

```text
README.md
STATUS.md
TOOL_INDEX.md
docs/NATIVE_INTERFACE_EVIDENCE_20261007.md
scripts/audit_recovery_survival.py
scripts/continue_motion_high_speed_submission.py
src/native_stand/command_v6/domain/evidence.py
src/native_stand/command_v6/domain/protocol.py
src/native_stand/command_v6/domain/selected_diagnostics.py
src/native_stand/command_v6/tools/evaluate_checkpoint.py
src/native_stand/command_v6/tools/health_check.py
src/native_stand/command_v6/tools/correct_evidence.py
src/native_stand/command_v6/tools/preflight.py
src/native_stand/command_v6/tools/play.py
src/native_stand/command_v6/completion.py
src/native_stand/command_v6/config.py
src/native_stand/command_v6/train.py
src/native_stand/command_v6/stand_chain.py
src/native_stand/command_v6/ledger.py
src/native_stand/command_v6/submission.py
src/native_stand/command_v6/supervisor.py
src/native_stand/command_v6/wiring.py
src/native_stand/recovery/recipe.py
src/native_stand/recovery/selection.py
src/native_stand/recovery/standing.py
src/native_stand/command_v6/tests/test_preflight_ledger.py
tests/test_evidence_interfaces.py
tests/test_stand_chain.py
tests/test_standing_height_independent.py
tests/test_standing_balance_submission.py
tests/test_motion_high_speed_course.py
tests/test_motion_cohort_width_ab.py
tests/test_recovery_autonomous.py
tests/test_pose_capture.py
tests/test_recovery.py
tests/test_stand_plane_contract.py
```

Generated corrected evidence paths above are additional new files. This checkout
was entirely untracked before work; no existing dirty artifacts were removed.

## Remaining evidence and compatibility limits

Engineering checks do not improve or certify robot capability. No new physical
measurements exist. Historical unrecorded PPO ratio/KL/BC gradients and absent
metadata cannot be recovered; selected diagnostics report only exposed actual data.
Real GPU diagnostics and detached launch must be checked in a separately authorized
smoke. The public supervisor reuses stand_chain; historical task-specific launchers
are retained, not all rewritten. Its new certificate is stricter than old smoke
evidence, so incomplete old evidence may block a new submission as intended.

Reward +10, short success resets, online0.15rad versus full0.10rad, reward/episode
curriculum design and motion retention degradation remain separate experiment
decisions. No implicit simulation/continuation authorization is created here.
