# R0 yaw-only controlled continuation

## Completion Review

Reviewed2026-10-06, eventa9a468f94c2254234fa81ea8.
[Original automatic report](../runs/recovery_standing_yaw_20261006/completion_report.md)
and original evaluation/selection/ledger are unchanged. Source/smoke/formal
COMPLETED/exit0, no accounting/exit conflict, no metrics JSONL issues.
103actual updates/843,776samples:3smoke(24,576)+100formal(819,200).
Chain971.83s(16.20min); formal872.53s. No automatic continuation authorized.

Same64-env layout,8scored envs,seed104,continuous10s protocol,2-10s steady window:

| Metric (8env mean) | Source1500 | New50 | New100 |
| --- | ---: | ---: | ---: |
| Steady root height m |0.36120|0.36231|0.35803|
| Mean abs vx m/s |0.06975|0.28778|0.07369|
| Mean abs vy m/s |0.00793|0.00867|0.00614|
| Mean abs yaw rad/s |0.12165|0.12979|0.08020|
| Maximum planar excursion m |0.60005|2.52969|0.65689|
| Mirror posture error rad |0.54709|0.46305|0.56877|
| Mean abs pitch rad |0.00308|0.00720|0.00219|
| Mean abs roll rad |0.000001|0.02281|0.000002|
| Dual wheel support |100%|100%|100%|
| Policy-sampled any-channel saturation |0.1%|0.1%|0.1%|
| Continuous completed |8/8|8/8|8/8|
| Fully accepted |0/8|0/8|0/8|

All8env in all3evaluations fail excursion,vx,yaw,mirror. No runtime faults or
falls in these10s evaluations. Height,level,contact,closure and sampled saturation
pass. New100 yaw improves34.1% relative to source, pitch improves28.7%; excursion
worsens9.5%, vx worsens5.6%, mirror worsens4.0%, height drops3.18mm but stays within
the frozen height gate. New50's better mirror comes with substantially greater
translation. Lower yaw is a partial observed gain, not stable/symmetric standing.

New100 latest SHA:
`be0dc90b235e8ae95c8d37de8a42295b9ca8aef4818d195c764724dded6e53f4`.
Accepted=null. Existing continuous-standing sorter selects source because all
have equal survival/pass counts and it prioritizes drift before level/mirror.
It does not demonstrate source is uniformly best; new100 has better yaw/pitch.
The generic Recovery ranking-description string in the automatic report omits
the continuous-standing branch; actual code uses drift/level/mirror after survival.
This wording mismatch does not change the raw acceptance results.

Compared with old250(250updates,10s), new100 has less yaw(0.0802 vs0.3184) and
better height/mirror, but more excursion(0.6569 vs0.1637). Different update budgets
prevent treating this as an equal-budget causal A/B. Old100 had only2s evidence;
do not compare its aggregate metrics directly against the new10s evaluation.

Formal time: rollout748.20s, PPO4.88s, evaluation114.10s, serialization0.78s.
Evaluation13.1% of formal wall meets the10-15% planning target. Rollout1094.9
samples/s; end-to-end938.9samples/s. No time evidence suggests JSON writes dominate.
New transferred103-update allowance fully used. Old ledger1399unused updates stay
unspent; this callback does not grant any continuation.

Next priority: offline compare symmetry reward gradients/objective with frozen
asymmetric source-retention actions on actual near-standing observations. The
source's mirror error0.547rad versus required<=0.1rad makes competing objectives
a plausible hypothesis; coefficients, state distribution and physical target
response must be checked before calling it causal or removing retention.
No optimizer/action remapping, threshold change, additional reward or new PPO was
performed during this review.

Updated2026-10-06. User agreed to channel-level saturation diagnosis and a
single-variable yaw intervention; no automatic additional training is authorized.

## Stopped run

`runs/recovery_standing_level_v2_long_20261006/formal` received SIGTERM at recorded
update497 and finalized498updates/4,079,616samples/4729.52s, STOPPED_BOUNDED,
exit0. Independent evaluation acceptance is distinct from graceful process exit.
No checkpoint, evaluation or historical attempt was rewritten.

## Measured channel evidence

PPO0, update400, same64-env layout/seed,8scored envs,2s continuous episode.
Raw: [evaluation](../runs/standing_saturation_review_20261006/evaluation_400_control_2s.json).
Summary: [channels](../runs/standing_saturation_review_20261006/saturation_channels.json).
Wall16.52s, no runtime fault. Existing plane/PD/limits/asset/action retained.

| Channel | Request peak Nm | Applied peak Nm | Saturation samples |
| --- | ---: | ---: | ---: |
| Left hip |14.21|14.21|0%|
| Left active |14.69|14.69|0%|
| Left wheel |10.49|5.5|0.5%|
| Right hip |20.02|20.02|0%|
| Right active |16.08|16.08|0%|
| Right wheel |33.15|5.5|35.5%|

This window does not support leg torque saturation as the explanation of the
aggregate35.5%. It confirms right-wheel clipping, not its unique cause.
Right-wheel clipping persists in the second second(30.25%); the longest streak
is4consecutive100Hz samples(0.04s sampling window), not a sustained whole-episode
stall. Left-wheel clipping is restricted to the first sample in each scored env.
Mean absolute wheel target/actual speeds: left3.28/2.40rad/s, right4.64/1.76rad/s.
See [wheel details](../runs/standing_saturation_review_20261006/wheel_detail.json).
Sampling is100Hz policy end, latest held5ms PD torque; no claim about every PD
substep or continuous force between samples. Geometry/asymmetry/yaw causal order
remains unproven. Original any-channel statistic is retained and correctly labeled.

## Intervention

[Spec](../configs/experiments/recovery_standing_yaw_20261006/spec.json): source
native update1500, strict actor/critic/Adam load, actual LR3e-5. Source250's old
full10s evidence is a separate comparison; it is not the new initialization.
Only task change is extra canonical-Y yaw Pseudo-Huber cost:

```text
-0.8 * (sqrt(1 + (yaw/0.35)^2) - 1) * 0.01
```

No hard yaw reset, no height reset, no optimizer clearing, no action remapping,
no symmetry-weight increase, no PD/asset/material/limit/acceptance change.
Cost is sign-symmetric, unbounded and unconditional in height. Existing overall
angular cost remains. At0.36rad/s the added per-step cost is approximately-0.00348;
zero yaw costs0. This is a controlled test, not a convergence guarantee.

Fresh source10s baseline (PPO0,<=300s) ->3smoke (<=300s) ->100formal, no formal
wall-clock limit inherited from the user authorization. Full10s confirmations
at50/100; no extra final100s endurance in this test. Behavioral failure does not
block formal; runtime faults or finite actor-update failure do.

103updates/843,776samples transferred atomically from the stopped2000-update
ledger; old formal limit1897, used498, unused1399 remains unspent. New ledger
smoke3/formal100. No double budget, no old attempt modification, no automatic
continuation of unused quota.

55focused CPU checks passed including yaw axis/sign/gate/dt, schema, exact quota
transfer and existing recovery/source/reset/chain checks. Runtime improvement
is judged by full evaluations, not by CPU tests or a successful launch.

## Monitoring

TensorBoard http://127.0.0.1:6010 compares previous and yaw_only runs; source
evaluation has no PPO metrics, first new events are expected during smoke.

New reward tags `rollout/raw_mean/settling_yaw` and
`rollout/weighted_mean/settling_yaw` distinguish this extra cost from overall
`settling_angular`. Track actual yaw, pitch/roll, height, mirror errors, contact,
saturation and source-retention cost together. A lower weighted yaw cost alone
does not certify symmetric stable standing. Full results must preserve height,
level and contact while reducing yaw; ordinary short-window survival is not10s
acceptance. Source/update250 comparison uses identical10s protocol and seed.
