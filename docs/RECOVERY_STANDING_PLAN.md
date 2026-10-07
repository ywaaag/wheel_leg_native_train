# Recovery: Stable, Level, Symmetric Standing

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
