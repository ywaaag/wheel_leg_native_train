# Standing Height-Gate Review

Updated:2026-10-06. User ordered stopping the existing chain and repairing the
height escape mechanism before considering further training. New simulation/PPO0.
Unique navigation: root STATUS -> this review -> corrected spec -> future manifest.

## Stop and Evidence

[Formal terminal](../runs/recovery_standing_balance_20261006_chain_1140/formal/terminal_report.json)
and [ledger](../configs/experiments/recovery_standing_balance_20261006/budget.json)
agree: formal1189updates/9,740,288samples, smoke3/24,576; total1192updates.
STOPPED_BOUNDED,exit0,user_signal; chain elapsed11348.03s. Old wrapper incorrectly
reports administrative COMPLETED after stop; original report is not overwritten.
No accepted continuous10s candidate. Remaining8808formal updates are preserved,
not automatically assigned to the new recipe.

Saved full evaluations0/250/500/750/1000 each0/8. Mean steady height decreases
from source~0.3612m to update1000~0.3390m; yaw/error/saturation worsen as well.
This is degradation across checkpoints, not proof of perpetual mechanical collapse
in a fixed-checkpoint episode. Source1500 remains the explicit initialization:
`c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82`.
Latest1189 is unreviewed and is not selected merely because it is last.

Example env0, same full evaluation layout/protocol:

| Metric | Source1500 | New update1000 |
| --- | ---: | ---: |
|Steady height,m|0.36120|0.33899|
|Mean abs vx,m/s|0.06983|0.23128|
|Mean abs yaw,rad/s|0.12161|0.80721|
|Mean abs pitch,rad|0.00308|0.00995|
|Mean abs roll,rad|0.000001|0.03904|
|Mirrored joint error,rad|0.54709|0.59013|
|Sampled saturation fraction|0.001|0.797|

Both source pitch/roll and update1000 pitch/roll pass the existing level gates.
The dominant observed failures are drift/spin, mirrored posture, height and
saturation; explicit pitch/roll reward alone is not a complete remedy.
Source already fails mirror/vx/yaw/excursion under the new strict protocol.

## Confirmed Mechanism

v1 pitch/roll, vertical/angular settling, mirrored posture, leg-length and wheel
differential costs are multiplied by increasing height gates. Lowering height
reduces their negative contribution. Source retention separately disappears below
0.34m, removing that auxiliary gradient when degradation crosses the boundary.
`upright=clamp(up,0,1)` is already close to1 in these mostly upright episodes;
it gives little discrimination for small pitch/roll differences and remains
positive despite height/drift failure. This is not evidence of a coordinate bug.

The controlled CPU probe fixes pitch/roll0.04rad, vx0.23m/s, yaw0.8rad/s,
mirrored errors0.59rad, support50N/wheel, zero effort/action differences. Only
height changes. These synthetic inputs are not a replay of a real trajectory.

| Height | Old total per10ms | Corrected total per10ms |
| --- | ---: | ---: |
|0.334m|0.033445|-0.000822|
|0.340m|0.033847|0.002880|
|0.360m|0.029484|0.009516|

Old formula rewards the lower state more in this probe. Corrected formula
retains the same stability costs at each height; Gaussian height favors0.36m.
Full raw/weighted/dt tables: [reward_probe.json](../configs/experiments/recovery_standing_level_v2_20261006/reward_probe.json).
This identifies an incentive mechanism, not its unique causal share in PPO failure.

## Corrected Recipe and Reward Tradeoffs

[Spec](../configs/experiments/recovery_standing_level_v2_20261006/spec.json),
[ledger](../configs/experiments/recovery_standing_level_v2_20261006/budget.json).
UNAUTHORIZED/all counters0. Source, USD, plane, control, action, PPO, reward
coefficients and independent acceptance remain fixed except:

- Upright weight2 ->0; retain raw diagnostic. Existing pitch/roll terms remain
  weight-4, scale0.12rad each and become unconditional.
- Standing geometry/vertical/angular costs and Pseudo-Huber settling costs use
  explicit unconditional gates. Legacy default is still height-gated.
- Frozen-source actor retention covers valid zero-command R0 observations at
 0.30-0.40m instead of0.34-0.38m, coefficient0.02 unchanged.

At0.36m in the synthetic moving state, height contributes+0.030/step, contact
+0.005, pitch and roll each-0.004444, linear settling-0.009048, angular
settling-0.005980, mirror-0.001568. Hence stronger level constraints are already
present; do not blindly multiply all weights. Term count alone does not measure
influence: inspect weighted contributions, state distributions, gates and PPO
advantages. PPO uses sampled returns, not direct differentiation through physics.

Retention is an actor-mean MSE auxiliary optimizer loss, not reward and not
multiplied bydt; its magnitude is not directly comparable to per-step reward.
The source was observed near0.36m. Its action targets at0.30m are not certified
as safe or appropriate; broadening coverage could inhibit necessary adaptation.
Moreover, teacher preservation can preserve the source's asymmetry and velocity
bias, which conflict with the new acceptance. Do not increase retention strength
merely because selected sample count increased.
Before training, compare source/current actions on real inputs and log retained
samples/loss. Selection is bounded256 samples/rollout and biased toward earliest
eligible inputs; it is not a complete uniform replay of the source's state domain.

This standing-only repair must not be used unchanged for low-pose Recovery:
unconditional posture/velocity penalties could inhibit a necessary lift. R0
only remains enabled. No symmetry hard action constraint, wheel lock, teacher
control, compensation, force-limit increase or claimed CLF/PBRS guarantee.

## Reading Applied

[TRAINING_EXPERIENCE_REUSE](../TRAINING_EXPERIENCE_REUSE.md) requires actual
formula/unit/dt/clip/gate checks and source-identity comparisons; that is applied
here. Its2026-10-01 current-state paragraphs are historical, not current facts.
[Reference text](../参考文献.md) motivates dense task feedback and reverse
curricula, but its broad convergence claims lack project evidence. We do not
adopt infinite actuator limits, hidden gates, external stabilizers or an invented
reference trajectory. The previous reward already was dense; sparse success
alone is not an adequate explanation of this degradation.

## Verification and Next Gate

CPU regression covers legacy/new gate behavior, low-height fixed-error probes,
signed pitch/roll and single dt multiplication, source/physics identity, fresh
unauthorized budgets, preflight no side effects, source actor/critic/Adam,
inference-mode retention, pre-reset scoring and fake-process user-stop paths.
Verification:81 focused CPU/fake-process tests pass. Full sweep183pass/10fail:
one active motion-ledger test, seven historical external-YAML/capture/preflight
identity tests, and two consumed-budget/snapshot-entry tests. These are not
silently skipped or counted as passing; old assets/configs/budgets stay unchanged.
Relevant exact regression command:

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q \
  tests/test_standing_height_independent.py tests/test_recovery_standing_balance.py \
  tests/test_recovery_dense_reward.py tests/test_recovery_autonomous.py \
  tests/test_recovery_settling.py tests/test_completion.py tests/test_stand_chain.py \
  tests/test_standing_balance_submission.py::test_incomplete_smoke_never_starts_formal \
  tests/test_standing_balance_submission.py::test_fake_chain_runs_once_notifies_once
```

Plan-only:

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/preflight.py \
  --spec configs/experiments/recovery_standing_level_v2_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_level_v2_SOURCE_PLAN_ONLY
```

Returns READY_NEEDS_AUTH/cpu_valid, no Isaac/PPO/output/ledger writes.
Proposed first runtime scope: source-only10s (300s wall/PPO0), then at most3
smoke updates (300s wall), real actor/teacher coverage and finite/control/reset
checks, independent10s candidate (300s wall/PPO0). Total proposed900s and
24,576 PPO samples. A candidate need not pass behavior gates to establish wiring,
but early height loss/saturation must be investigated before spending long-run
budget. New budget requires authorization; no submission or allowance transfer.
The config's500formal-update allowance is a proposal, not a granted continuation.
