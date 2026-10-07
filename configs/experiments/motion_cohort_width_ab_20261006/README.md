# Frozen cohort tracking-width A/B

User authorization: 2026-10-06, compare only all-cohort wide tracking against
old-target-cohort source-width preservation. No high-speed progression or
automatic continuation beyond this comparison.

Source B: `/home/kellen/wheel_leg_native_train/runs/motion_forward_cohort_20261006/formal/model_update_25.pt`.
SHA256: `bacd31f34a1e3917afa8e5dd9648bb5985c023dd0bc9ffd6a96ad1e1eed6fbad`.
Restore actor, critic, Adam, std and Torch RNG; LR remains 3e-5.
Each physical environment starts from a new reset, not a recovered historical simulation state.

A uses d_v=1 for all targets. B uses d_v=.04 for episode target zero/+-.5,
and d_v=1 for new +/-1 targets, including their entry/ramp/exit/parking phases.
Instantaneous ramp command crossing +-.5 does not select the old cohort.
Same Gaussian formula, weight8, yaw denominator .09, and policy dt .01.
Both arms retain the identical current PPO/physical/network contract.
No retention, critic warmup, Adam surgery, LR/std adjustment or advantage normalization change.

Each arm has its own source_eval/smoke/formal ledger. One source baseline per arm
evaluates 0,+-.5,+-1 for30s under the same evaluation seed104; all three old cohorts
must pass before online updates. Baseline failure blocks the comparison rather
than relabeling a missing source capability as retention.
Each arm independently restarts from B for one smoke update and <=250 formal updates.
Allocated total online updates <=502, samples <=4,112,384, chain wall<=14,400s,
including startup and evaluation. Source<=1500s, smoke<=180s, formal<=6000s each.
No automatic retries or budget extensions; all phases use physical GPU1 only.

Targets 0,+.5,-.5,+1,-1, weights20/10/10/30/30% and31s training episodes
with1/2/24/2s entry/ramp/hold/exit match the previous L1 run.
Episode ages remain synchronized in both arms to isolate the width variable.
New diagnostics record actual hold fraction and selected denominator per target cohort.
Evaluation uses30s and2/8/8/8s scheduling, hold10-18s, parking26-30s.
Full evaluation at125/250, checkpoints125/250, no stage promotion.
Ordinary new-command failure consumes the allocated stage budget; two consecutive
old-cohort failures stop that arm; nonfinite/closure/control faults block the chain.

The gate is frozen from capability_v2 for comparability, including tilt .5rad,
contact .95 and mean height .34-.46m. These inherited thresholds are experimental
choices, not proof of stricter .2rad posture acceptance or centimeter station keeping.
Zero gate: horizontal p95<=.3m/s and mean abs yaw<=.3rad/s.
Parking residual and displacement are reported separately, not fine-stop gates.
Eight evaluation environments / one evaluation seed / one training source are not
multi-seed training evidence. Equal allocated budgets do not imply equal actual
updates if an arm is stopped for a predeclared guard.

CPU: focused cohort-width, reward, selection, exact-ledger, fake-supervisor and
shared completion/domain regression. Historical stand_plane preflight fixtures
have an external YAML SHA mismatch; they are retained and separately identified.
Actual A/B specs pass identity/schema plan-only without creating runs or changing ledgers.

Plan-only:
```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.command_v6.motion_width_ab \
  --config configs/experiments/motion_cohort_width_ab_20261006/ab_spec.json \
  --output-dir runs/motion_cohort_width_ab_20261006
```
The same command with `--launch` submits exactly one detached snapshot-owned chain.
Background phase monitors handle checkpoints/terminal/exact settlement. The chain
sends a single final HAPI notification to the current worker session frozen in ab_spec.json.
Read `chain_progress.json`, then `chain_terminal_report.json`, `analysis.json`
and `completion_report.md`; notification does not authorize further training.
