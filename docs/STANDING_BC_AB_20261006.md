# Standing BC gradient and annealing comparison

## Completion review -- 2026-10-06

Event74c16b14abeaebf3e9155986. Pair and all six phases COMPLETED/exit0;
206actual updates (6smoke+200formal),1,687,552samples,1890.95s/31.52min.
Both exact ledgers used source1/smoke3/formal100;1193old updates remain unspent.
Callback sent to the configured session; no automatic continuation.
Raw report: [completion_report](../runs/standing_bc_ab_20261006/completion_report.md).
Full evaluations: each arm's formal/evaluation_{50,100}_0_0.json; source
source_eval/evaluation_source.json. Old reports and checkpoints are preserved.

|Metric (mean across8scored envs)|Source1500|A_fixed100|B_annealed100|Gate|
|---|---:|---:|---:|---:|
|Continuous10s completion|8/8|8/8|8/8|8/8|
|Full acceptance|0/8|0/8|0/8|8/8|
|Steady root height m|0.36120|0.35803|0.35821|0.34-0.38|
|Mean absolute vx m/s|0.06975|0.07369|0.08638|<=0.03|
|Mean absolute yaw rad/s|0.12165|0.08020|0.04288|<=0.03|
|Maximum excursion m|0.60005|0.65689|0.78844|<=0.20|
|Joint mirror error rad|0.54709|0.56877|0.55992|<=0.10|

All8envs fail excursion/vx/yaw/mirror at both50/100 in both arms. No missing
or runtime-fault cases; height, pitch/roll, contact, closure and sampled
saturation gates pass. Final contact100%; closure about0.021mm; policy-sampled
saturation0.1%, not a claim about every PD substep. B100 mean absolute
pitch0.00106rad versus A0.00219rad; both already meet the level gate.
Leg-length differences A/B3.31/2.84mm pass despite large joint mirror errors.
This discrepancy merits geometry/normalization/objective inspection, not a claim
that joint asymmetry is physically harmless or that its metric is wrong.

B100 versus A100: yaw improves46.5%, mirror improves only1.6%, vx worsens17.2%
and excursion worsens20.0%. Against source, both mirror errors are worse.
At50, mirror improves to A0.463/B0.444 but drift grows to2.53/2.93m; that is
a tradeoff, not simultaneous progress. Neither source nor either final is fully
accepted; no overall best candidate is established by this controlled pair.
These are near-standing R0 evaluations, not completed low-pose Recovery.

## Gradient and effective configuration checks

Formal A:99defined first-minibatch cosines,53.5% negative, mean-0.0467;
weighted BC/PPO norm average0.154%, maximum0.317%. Leg contribution average
0.0254%, wheel0.1523%; norms of contributions do not add as scalars.
Formal B:51fromexactzero BC, average weighted ratio0.0395% across100updates.
Its direction may still oppose when BC is disabled, but no actual BC update then
occurs. Both formal1teacher=student has zero BC gradient/null cosine.
Actual B coefficients: update1 .02,26 .01,50 .00001973,51/100 exactly0.
Gradient comparisons include PPO entropy and clipping, use different minibatch/
captured-state distributions, and inspect one optimizer step per update. Adam
preconditioning and later minibatches are not captured by this norm ratio.
Measured opposition does not establish a dominant BC anchoring mechanism.

Formal A/B rollout729.30/732.22s; PPO5.15/4.76s; evaluations111.57/112.01s;
serialization0.754/0.756s. Rollout throughput1123.3/1118.8samples/s; end-to-end
formal962.3/958.9samples/s. Evaluation about13.1% of each formal phase.

## Decision

Do not extend either branch unchanged or immediately prioritize wheel-only BC:
removing all BC did not solve mirror/drift, and the observed leg BC contribution
is small. Next most useful offline work: verify mirrored USD geometry/signs and
the per-state mirror penalty/weighted signal on saved pre-action/posture data,
then specify full observation/history/action equivariance tests before any mirror
BC physical experiment. Never average left/right actions at the same state as
though that were verified physical mirroring. No new PPO/physics is launched
by this completion review; remaining quota is not reset or automatically spent.

Final A100 SHA008e11af36c2310ecc1fd3945d3df0e60994d2b780598fdcf32871842f5edc18;
B100 SHA08aec50d89f065b5ccbd364107160f9335dd1eefd04969a75a36b6443da0d51f.

Authorized2026-10-06: gradient inspection, then full-channel BC annealing A/B.
Wheel-only and full observation/action mirror BC are not automatically launched.
Source/teacher native Recovery update1500 SHA:
`c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82`.
Same actor/critic/Adam, seed, LR3e-5, yaw recipe, mechanical-stop USD, plane,
actions, control and protocol in both arms. No optimizer reset or reward change.

Each arm: PPO0 source10s/300s cap,3smoke/300s cap,100formal updates.
Total206updates/1,687,552samples transferred from stopped allowance;1193remain.
Formal has no wall cap; exact update/sample caps still apply. Source behavioral
failure does not block learning; runtime faults do. Smoke requires3finite
updates, actor change and3gradient probes before formal. Full10s at50/100,
no100s durability. Estimated32-40min based on prior chain, shared GPU dependent.

A_fixed: BC0.02 throughout. B_annealed: same smoke BC; cosine0.02 to0 over
formal1-51, exactly0 from51. Zero BC skips backward and extra gradient clipping.
Each arm independently starts from the same source, not from the other arm.

First optimizer minibatch/update records actor PPO+entropy gradients after
installed PPO clipping, BC norms, cosine and weighted norm ratio. Leg/wheel
contributions share the full6-channel denominator and sum to full BC gradient.
These compare actual batches, not isolated reward-term gradients. Negative
cosine is opposition, not causal proof; zero norm gives null. Compact inputs/
gradients saved at1,3,10,50,51,100, never the full rollout.

Report compares continuous survival/pass count, height, vx/yaw, excursion and
mirror error. No overall winner when neither passes. Completion notification
requests review without authorizing continuation. Shared source is snapshotted.

## Entry

Cwd `/home/kellen/wheel_leg_native_train`; interpreter `issaclab`.

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.command_v6.retention_ab \
  --config-dir configs/experiments/standing_bc_ab_20261006 \
  --output-dir runs/standing_bc_ab_20261006 \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

Removing `--launch` is CPU plan-only. Do not repeat a submitted pair.
One formal startup handshake; background owns reports/accounting/HAPI.
No interaction polling. Per-arm gradient_smoke_review.json, metrics.jsonl,
bc_gradient_update_*.pt, full evaluations and selection; pair analysis.json,
completion_report.md, terminal and notification state. TensorBoard reads only
update-end JSONL. Source/smoke behavioral results are not convergence claims.

## Startup evidence — 2026-10-06 20:02 CST

63focused CPU/fake-process tests pass. A source and3smoke completed exit0;
one formal handshake RUNNING/actual1, trainer2046440, worker2044513.
TensorBoard http://127.0.0.1:6011 responds HTTP200. First-minibatch smoke
probes2/3 have cosine-0.106/-0.302 but weightedBC/PPO norm only0.0108%/0.0229%.
There is directional opposition with small magnitude in these early probes;
BC anchoring is not established as the main failure mechanism.
CPU/startup success does not establish behavioral improvement.
