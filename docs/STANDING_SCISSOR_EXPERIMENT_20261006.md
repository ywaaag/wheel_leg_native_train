# Authorized wheel-center alignment probe

## Completion review -- 2026-10-06

Event d5ef508a2c3c881de3e8c86b. Source/smoke/formal all COMPLETED/exit0,
no runtime fault, terminal/ledger agree.53updates/434176samples total,
50formal/409600samples;529.56s(8.83min) chain. All allocated updates consumed;
1140old unused updates remain unspent, no automatic continuation.
Source and final50 all8/8 continuous10s, both0/8 full acceptance.
Raw evidence: source_eval/evaluation_source.json and
formal/evaluation_50_0_0.json under runs/standing_scissor_20261006.

|Metric, mean across8scored envs|Source1500|New50|Prior fixedBC control50|
|---|---:|---:|---:|
|Root height, steady m|0.36120|0.36667|0.36231|
|Wheel-center fore/aft offset, full10s m|0.16685|0.08081|Missing|
|Mean absolute vx m/s|0.06975|0.70411|0.28778|
|Mean absolute yaw rad/s|0.12165|0.11773|0.12979|
|Maximum planar excursion m|0.60005|6.26157|2.52969|
|Joint mirror error rad|0.54709|0.25806|0.46305|
|Mean absolute roll rad|0.000001|0.07234|0.02281|
|Leg-length difference m|0.00339|0.03185|0.00839|
|Dual support, steady|100%|100%|100%|

Wheel offset improves51.6%, joint mirror error52.8%, without height collapse.
Steady2-10s/last2s offset0.07883/0.07869m; still not the4cm diagnostic target.
Full-window fraction offset<=4cm only0.7% (source0.4%). Not a complete alignment
success. Initial minimum height0.36572m versus source0.35575m.
Source fails excursion/vx/yaw/mirror in all8envs. Final50 fails those plus roll
and leg_length in all8envs. Roll mean0.07234>0.05rad gate; leg length31.85mm
>10mm gate. Pitch mean0.02196/peak0.05363rad still passes0.05/0.10 gates.
Closure peak across measured episodes about0.021mm; policy-sampled saturation
0.2%, not every PD substep. No reset/fall/nonfinite/closure fault in full cases.
Thus reduced scissor is accompanied by worse rolling drift and lateral posture,
not a simultaneous stable/symmetric stance. No claim of passive-static mechanism
or physical infeasibility follows from this50-update test.

Formal/smoke initialize independently from source1500, same fixedBC/Adam/seed/
LR3e-5; smoke checkpoint is wiring evidence, not the formal source. Prior A50
is the same-source no-geometry-cost comparison; it lacks actual wheel center
readback, so do not compare its sampled offline geometry as a full-window metric.
New50 has worse drift/roll but improved joint mirror versus that control as well.

### Reward and time evidence

GPU rollout averages1-10 versus41-50:
wheel offset0.16313 ->0.09046m; geometry penalty-.03728 ->-.00778/step;
height reward+.02969 ->+.02884; settling linear penalty-.00336 ->-.03056;
roll penalty-.000112 ->-.01050. Dense sum-.00862 ->-.01874/step.
All reward terms finite. Lower geometry cost did not improve total mean reward;
other costs grew. Negative total reward did not by itself prevent this tradeoff.
This is observed joint evolution, not causal proof of exact network/critic cause.

Formal wall426.83s: rollout363.48/PPO2.56/eval55.50/write0.817s.
Rollout1126.9samples/s; end-to-end959.6samples/s; eval13.0% of formal wall.
Latest model SHA1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71.
Automatic best remains source1500 by drift-prioritized ranking; accepted=null.
That is a conservative comparative choice, not proof the source passes.
HAPI event sent once; this review acknowledges it without new notification.

### Next decision

Do not extend this branch unchanged or further raise the geometry penalty.
The actual runtime measurement and reward coupling are verified; the open
problem is retaining zero-motion/level/leg-length while reducing fore/aft offset.
Next bounded single-variable proposal: same source1500 and recipe with geometry
weight reduced4fold (-.1875 ->-.046875); no changes to BC, yaw, roll, action or
physics. At15cm cost-.0075/step,18cm-.01172, compared with height/support about
+.035. Assess zero-speed/level preservation and alignment jointly, not total
reward positivity or one score. This is a proposal, not a newly submitted run.

Reporting limitation found: geometry trace was not excluded from candidate
registry/report rows, inflating completion_report.md with full arrays. Raw
metrics remain valid; a future narrowly scoped serialization fix should retain
traces in evaluation JSON and put summaries only in registry/Markdown.
No trainer or report generator changed during this completion review.

## Startup evidence -- 2026-10-06

Source COMPLETED/exit0,10s/PPO0/61.67wall seconds.64runtime/FK samples pass;
maximum wheel-center difference0.235mm, tolerance2mm. Source runtime mean
longitudinal offset0.16685m confirms scissor geometry independently of prior
offline reconstruction. Source strict acceptance0/8; other source behavior is
the baseline, not a claim of learned correction.
3smoke COMPLETED/exit0/26.71s. Formal one handshake RUNNING/actual1,
trainer2150267, worker2148333, attempt8e627a44c4d640ae846461564df56e5e.
TensorBoard http://127.0.0.1:6012 HTTP200. No interaction log polling afterward;
background will deliver final report and one current-session HAPI notification.

User agreed the bounded geometry readback ->3smoke ->50formal chain.
Current spec: configs/experiments/standing_scissor_20261006/spec.json.
Current output: runs/standing_scissor_20261006.
Source/teacher remains update1500 SHA
c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82.
Actor/critic/Adam strict load; LR3e-5; fixed all-channel BC0.02. All other
existing yaw recipe, USD, plane, action/control/physics and protocols unchanged.
This is a matched-source reward intervention, not continuation from A/B100.

## Single reward variable

delta = horizontal projection of main-wheel center difference onto native
canonical forward=-bodyZ. Direction is derived using body gravity, not worldX.
Added per-policy-step cost:
`-.1875 * (relu(abs(delta)-.03)/.03)^2 * .01`.
No height gate. At0/3/4/10/15/18cm cost0/0/-.0002083/-.0102083/-.03/-.046875.
Other mirror/height/yaw/effort costs remain unchanged. No wheel lock, extra PD,
hidden action averaging or virtual-leg controller. Lowering height cannot turn
off the cost; preservation is judged by existing height/survival gates.
Current acceptance is unchanged; offset<=4cm is a separate diagnostic target,
not a replacement for drift, height, pitch/roll, yaw, closure or limits.

## Budget and runtime gate

PPO0 source10s capped120wall seconds, includes startup/cleanup;
3smoke updates capped300s;50formal (409600samples), no formal wall cap.
Total53updates/434176samples transferred from unused1193, leaving1140;
no previous actual usage reset. Runtime failures stop, ordinary failures learn.
Before smoke, compare64runtime pre-reset wheel-center samples to current USD
closed-branch FK. Max mismatch<=2mm and offline closure<=0.1mm required.
Missing/nonfinite geometry stops before PPO; summary saved wheel_geometry_readback.json.
Final50checkpoint/full10s evaluation; no100s endurance or automatic extension.
Expected10-15min based on prior measured rollout, shared GPU load dependent.

Train observation remains25/125/150; only physics truth rewards/diagnostics
receive wheel centers.13-column pre-reset geometry trace fields are
left center root xyz,right center root xyz,body gravity xyz,active legs
[left_hip,left_active,right_hip,right_active]. GPU preallocated evaluation
buffers, once-after-eval CPU transfer. Training logs one mean offset/update,
raw/weighted wheel_longitudinal_offset cost using existing rollout accumulator.

## Submit once

```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.command_v6.stand_chain \
  --spec configs/experiments/standing_scissor_20261006/spec.json \
  --output-dir runs/standing_scissor_20261006 \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

Omit--launch for CPU plan-only. Shared chain now executes its frozen source
snapshot; no extra trainer. One formal startup handshake, then no log polling.
Monitor settles exact attempt, emits quantitative report and one HAPI callback.
Read root STATUS and actual manifest/progress/terminal; no re-submit on UNKNOWN.

## Verification before launch

53focused CPU tests pass: deadband/normalization/dt, projection, invalid input,
pre-reset geometry, existing evaluator/reset/RNG behavior, ledger, BC and yaw.
Source phase preflight PASS; no related live trainer at initial identity check.
Runtime geometry agreement is not yet claimed until the source gate completes.
