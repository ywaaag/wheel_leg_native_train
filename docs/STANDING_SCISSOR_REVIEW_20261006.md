# Scissor posture offline review

## Confirmed evidence

No new physics or PPO. Current USD SHA32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7.
Tool: scripts/audit_standing_scissor.py; four CPU fixtures pass (forward axis,
translation/swap invariance, horizontal projection, missing gravity rejection).
Raw artifact: [scissor_geometry_review.json](../runs/standing_bc_ab_20261006/scissor_geometry_review.json).

Decoded saved pre-action25D observations: actual four active positions=channels
9:13 /2 + zero reference. Reused AssetPoses joint frames and bounded closure
solver, initialized passive branch from saved R0 pose. Native forward=-root Z,
up=+root Y; measured forward projected onto gravity-horizontal plane, not USD X.
Computed wheel centers, hip-wheel sagittal angles and closure for16uniformly
selected inputs from each of6payloads. All96reconstructions satisfy closure
<=0.1mm. Authored offline kinematics is not PhysX body-position readback.

|Saved rollout update|A wheel offset m|B wheel offset m|A sagittal angle difference rad|B difference rad|
|---|---:|---:|---:|---:|
|1|0.04853|0.04853|0.14383|0.14383|
|50|0.14273|0.13833|0.46411|0.44842|
|100|0.17549|0.17377|0.57208|0.56659|

Inputs are captured before PPO updates1/50/100 (actor source/49/99); they are
256eligible training observations/payload, with16sampled for this review.
They are not a full holdout trajectory or an unbiased comparison over identical
episode ages. Values support real fore/aft scissor geometry in these saved
states, but not a claim of monotonic whole-run scissor worsening. Joint mirror
error0.56rad alone was insufficient to infer19cm; independent USD reconstruction
now supports roughly17-18cm for sampled states. It does not prove this is passive
static stabilization or that precise wheel control is unnecessary.

R0 base reset offset0.022mm, sagittal difference0.000065rad. Other R0 train and
holdout active joint perturbations are only about0.005rad; reset_idx loads those
explicit pose entries and zeroes velocities, without large reverse-leg random
offset injection. No reset fix is justified by the proposed explanation.
Prior holdout JSON lacks actual wheel-center/passive-q time series; full
runtime reconstruction/branch agreement remains an explicit measurement gap.

## Actual reward scale

Last formal rollout GPU mean contributions per10ms policy step:

|Term|A100|B100|
|---|---:|---:|
|Standing height|+0.029887|+0.029874|
|Dual support|+0.005000|+0.005000|
|Joint mirror|-0.001476|-0.001446|
|Dense contributions summed|+0.031616|+0.031424|

These are same-rollout aggregate statistics, not an exact per-state counterfactual.
Mirror has deadband0.03rad, scale0.2rad, weight-0.02, unconditional gate and
one dt multiplication. It remains active at lower heights, but its sampled
cost is small relative to height/support. This supports a reward tradeoff
investigation; it does not prove a unique causal mechanism or PPO convergence.

The suggested expression -lambda*(d/.03)^2 has no3cm deadband: at3cm it already
penalizes by-lambda. At dt=.01, pre-dt lambda=.12 gives-.030 at15cm and-.0432
at18cm; lambda=.14 gives-.035 at15cm and-.0504 at18cm. A desired3cm deadband
would instead require an explicit max(d-.03,0), and different calibration.
Neither making total reward negative nor high first50-update weight guarantees
recovery; it can favor earlier termination and abrupt loss of source behavior.

## Recommended next single variable

Prefer wheel-center longitudinal alignment over raw action equality or replacing
physical control by a virtual-leg controller. Keep25/125/150D, action semantics,
PD/limits, USD/material, source choice, optimizer and acceptance unchanged.
First add a separate diagnostic tensor for actual pre-reset wheel positions,
gravity-projected forward offset and hip-wheel sagittal angles; cross-check
against this offline tool on a bounded no-PPO window. Wheel centers are not
contact patches and must be labeled accordingly.

Then one explicit fresh recipe may add a smooth, finite geometry cost with a
documented tolerance/normalization, raw/weighted/dt plots and actual safety
checks. Do not simultaneously add virtual-pitch cost, change reset, raise yaw
cost and alter BC. Evaluate alignment together with height, drift, self-rotation,
contact, pitch/roll and effort; low offset obtained by collapsing is not success.
BC schedule must be held constant in this new comparison; the prior BC test
did not establish a symmetry cure.

Proposed bounded validation, not launched here: PPO0 geometry readback capped
120s,3smoke capped300s,50formal updates (409,600formal samples), source/final10s
comparison. New updates total53/434,176samples, transferred from unused1193
only after explicit experiment authorization; estimate10-15min shared GPU,
strict runtime fault stops and exact ledger. Source/teacher/BC decision belongs
in that new spec, not an in-place change to the completed A/B.

## Reproduce

From project root, no Isaac/AppLauncher/GPU simulation:

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  scripts/audit_standing_scissor.py \
  --pair runs/standing_bc_ab_20261006 \
  --output runs/standing_bc_ab_20261006/scissor_geometry_review_new.json \
  --samples-per-payload 16
```

Output must be new. Input checkpoint/spec/pose/USD identities are checked or
recorded; no old evaluations, checkpoint, budget or completion report is changed.
