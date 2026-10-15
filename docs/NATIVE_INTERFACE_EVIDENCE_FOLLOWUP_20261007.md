# Native interface gap closure
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


2026-10-07. This document supersedes completion claims in the first interface
engineering report; all earlier artifacts remain immutable. Scope: CPU fixtures,
static checks and offline evidence only. No AppLauncher, Isaac process, online PPO,
new authorization, reservation, continuation, or physics/learning recipe change.

## Implemented and CPU Verified

| Requirement | Result |
| --- | --- |
| Actual evaluation duration | Requested scoring duration/windows remain frozen; actual duration and each environment's observed duration are recorded separately. Early failure cannot shorten acceptance. |
| One effective scoring protocol | Recovery/native reject unknown/conflicting fields, validate duration/rate/count and SHA, use the effective record for gates. Standing100s durability produces a gate and honors the configured durability window. |
| Evaluation state isolation | Runtime switches, actor mode and Torch RNG restore even if setup/reset/cleanup fails. RNG restores after reset. Runtime faults/interruption carry partial duration and sanitized pre-reset evidence into terminal reports. |
| Gate adapter | All five states, malformed/empty rows, env-count/decision/failed-check contradictions, protocol SHA/contract and termination semantics are checked. Conflicting full evidence cannot drive curriculum promotion or candidate acceptance. Light cases remain ineligible for full certification. |
| Diagnostics validity | CLI OR runtime flag, explicit merge rule, per-field requested/enabled/valid/count/reason/scope; finite zeros are valid measurements, disabled or nonfinite fields are null/invalid. Aggregation happens after collection. |
| Generic offline audit | Automatic phase/checkpoint/evaluation discovery, terminal sidecars excluded, correct chain/arm ledger discovery, snapshot/source/asset/spec/evaluator identities, actor/critic/std/Adam hashes and checkpoint internals. Missing evidence UNKNOWN; conflicts INVALID. |
| Reward audit | Continuous, success, failure and timeout events are separate; unrecorded timeout data remains null. Generic summary does not fabricate historical PPO gradients. Specialized frozen100s rescore remains explicitly selectable. |
| Health check | Docs/current spec, exact ledger/attempt/run accounting, raw evaluations/report hash/status, all model roles/stage command coverage, internal checkpoint identities, exact process argv/start/spec/output/attempt and GPU UUID mapping. Read-only. |
| Submission | Public supervisor launch uses active-phase health, current HAPI session, physical GPU mapping/occupancy and preflight as hard prerequisites. UNKNOWN handshake sets started=false. Two former high-speed PID/hardcoded submitters now use the shared explicit CLI. |
| Smoke certificate | Shared validator for preflight/ledger/phase owners; source/spec/checkpoint/asset/effective protocol and scored episodes verified. A persisted matching certificate is required. Smoke adds a single end-of-budget light evaluation, not an additional PPO budget or ability acceptance. |
| Preflight | Compatible status plus distinct reason/action for OK, configuration, identity, budget, authorization, unsettled attempt, process identity, missing evidence and behavior gate failure. Plan-only remains zero-write. |
| P2 | Default off; configured update list only. Actual reward/event counts/duration distribution, raw and normalized storage advantage summaries, value/return/log-prob, full-rollout before/after ratio/KL/clip/entropy/mean/std, actual optimizer-input actor/critic/std norms, both retention paths' eligible/selected/ages/commands/channel errors and first actual-step BC/PPO probes. |

P2 full-rollout policy comparison is explicitly **not** a minibatch KL history or
the scheduler's input. BC/PPO comparisons describe the actual first optimizer
step, PPO+entropy after clipping and BC before addition; they are not a reward-term
causal decomposition. Observer fixtures verify exact parameter updates, cached
distribution and RNG invariance. CPU toy SGD/Adam fixtures are not online PPO.

The fixed-reference diagnostic path only observes the existing retention objective;
lambda, sample selection, action parameterization and gradient addition/clipping
are unchanged. Native/recovery reward, curriculum goals, LR/std/normalization,
network, USD, physical parameters, action scaling and limits were not changed.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.supervisor \
 --spec configs/experiments/recovery_survival_level_from50_20261006/spec.json \
 --output-dir isolated/interface_evidence_followup_20261007/PLAN_ONLY_FINAL_UNCREATED

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.tools.health_check \
 --project-root /home/kellen/wheel_leg_native_train \
 --spec configs/experiments/recovery_survival_level_from50_20261006/spec.json
```

Final test count, exact file SHA and verification output are in
`isolated/interface_evidence_followup_20261007/change_manifest.json` and
`verification.json`. Plan-only correctly reports BUDGET_EXHAUSTED. Health also
identifies existing historical source/new-candidate registration inconsistencies;
those reports are preserved, not edited to clear warnings. Unused old allowance
is not current authorization.

## Offline Evidence

All output directories are fresh, exclusive-create. Each contains audit.json,
audit.md and audit_manifest.json; generic correction also supplies corrected aliases.

- `isolated/interface_evidence_followup_20261007/final_recovery/`: four evaluations;
  historical missing effective protocol remains UNKNOWN.
- `final_high_speed/`: 24 source/smoke/formal evaluations, not just formal milestones.
- `final_width_ab_v2/`: 30 evaluations, both arms' actual ledgers resolved from frozen
  manifest/config identity. Earlier followup outputs retained.
- `final_reference/`: bundle identity/tensor hashes; 57408x150 observations, commands
  balanced19136each, age6.00–8.98s. SHA251840a97275811d6b343e72a07ff885b8b110de5a6559f61bc42286c130ff25.
  Metadata rows897 counts collection rows, not observation samples. This bundle-only
  directory lacks manifest/terminal evidence; it is not a training run certificate.
- `frozen_recovery_rescore/`: independent frozen100s rescore with effective [2,100],
  8/8 passed, no saved metric mismatch outside explicitly limited drift reconstruction.
  Continuous/event rewards remain separate, unavailable historical gradients null.

Generic reports intentionally do not infer actual historical windows from inaccurate
serialized prose. The frozen rescore supplies the separate100s window evidence.
Input paths/SHA are recorded and rechecked after output generation. Historical
checkpoint, raw evaluation, spec, ledger, report and frozen code were not overwritten.

## Exact Incremental Files

```text
README.md
STATUS.md
TOOL_INDEX.md
docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md
scripts/audit_recovery_survival.py
scripts/submit_motion_high_speed_formal.py
src/native_stand/command_v6/domain/evidence.py
src/native_stand/command_v6/domain/selected_diagnostics.py
src/native_stand/command_v6/domain/retention.py
src/native_stand/command_v6/tools/evaluate_checkpoint.py
src/native_stand/command_v6/tools/evaluation_state.py
src/native_stand/command_v6/tools/health_check.py
src/native_stand/command_v6/tools/correct_evidence.py
src/native_stand/command_v6/tools/preflight.py
src/native_stand/command_v6/completion.py
src/native_stand/command_v6/train.py
src/native_stand/command_v6/stand_chain.py
src/native_stand/command_v6/ledger.py
src/native_stand/command_v6/launcher.py
src/native_stand/command_v6/submission.py
src/native_stand/command_v6/supervisor.py
src/native_stand/command_v6/wiring.py
src/native_stand/command_v6/motion_width_ab.py
src/native_stand/recovery/recipe.py
src/native_stand/recovery/selection.py
tests/conftest.py
tests/test_completion.py
tests/test_evidence_interfaces.py
tests/test_protocol_followup.py
tests/test_selected_diagnostics_followup.py
tests/test_health_submission_followup.py
tests/test_offline_evidence_followup.py
tests/test_recovery_autonomous.py
tests/test_standing_balance_submission.py
tests/test_standing_height_independent.py
tests/test_motion_high_speed_course.py
tests/test_motion_cohort_width_ab.py
```

Generated evidence/report manifests are additional new files listed by output path.
Existing dirty/untracked project changes were preserved. Current code describes
future execution; historical source snapshots remain the implementation of old runs.

## Remaining Physical Evidence

Engineering gaps above have CPU/offline evidence. No fresh Isaac smoke, real GPU
diagnostic collection, live detached startup or HAPI terminal delivery was executed.
Those require a separately authorized bounded runtime check. CPU mock evidence does
not certify physics or learned capability. Other historical experiment-specific
orchestrators remain for reproducibility; new common submissions use supervisor.
Incomplete old smoke evidence will be rejected by the new certificate rather than
silently reused. No historical output is upgraded to accepted on that basis.

Success thresholds0.15rad/0.10rad, +10event reward, short success reset and learned
motion regression remain separate training design questions. No such recipe changed.
