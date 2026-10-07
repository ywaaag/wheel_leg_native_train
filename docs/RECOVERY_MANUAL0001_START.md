# R1 manual0001 launch readiness — 2026-10-02, Asia/Shanghai

User confirmed linkage support safety and requested Recovery training. This recipe
uses the captured0001 low pose, not old high-standing training or a new trainer.
[Spec](../configs/experiments/recovery_r1_manual0001_20261002/spec.json),
[budget](../configs/experiments/recovery_r1_manual0001_20261002/budget.json).

Frozen STAND: scratch update500 SHA
`fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1`.
Recovery is a new random150D actor/critic/freshAdam, 64env×128steps, LR3e-5;
STAND network is separate, frozen, and never part of its optimizer.
Recovery leg targets use1.6rad, wheel normalization100rad/s; frozenSTAND retains
0.5rad/100rad/s. One original PD path and40/5.5Nm limits remain.

Initial source: `runs/recovery_pose_capture_20261002_145814/pose_0001_73d09dbe.json`.
Preserve all measured q and root orientation; new reset zeroes velocity.
Authored offline closure recomputation: maximum2.71835e-7m, actual joint limits valid.
Root≈0.168474m; guide-supported chassis gap≈0.098474m. This geometry interpretation
and linkage support are user confirmed. No side/back/falling-impact poses included.
Train and holdout R1 use the same easy posture with separate seed; do not claim
random-pose generalization. R2/R3 do not auto-unlock.

Contact classification now reads explicit patterns from the recipe. Confirmed
active/long/node/parallel/upper/lower linkage bodies may support the robot;
unmatched modeled bodies remain restricted. Unmodeled weak components remain UNKNOWN.
Finite, closure5mm, penetration5mm and true joint-limit protections are unchanged.

## Remaining physical gates

1. FrozenSTAND10s near-standing takeover probe on the current plane/config.
2. Replay0001 with bounded passive settling:64env layout,8scored, noPPO.
3. Only actual passing evidence may set initialization/handover validated flags.
4. Smoke checks control/reset/loss/update; ordinary unsuccessful recovery is learning data.
5. Success requires physical-target handover and frozenSTAND continuous5s verification.

## Quantitative authorization pending

Existing budget remains UNAUTHORIZED, used0. No physics/PPO launched this turn.
The latest pasted task explicitly requires a confirmed runtime/update budget;
20smoke/10000formal from AI material are not accepted as authorization.

Proposed single conditional chain: R0+initialization cumulative600s/PPO0;
smoke5updates/40,960samples/300s; formal500updates/4,096,000samples/7200s including
evaluations/cleanup. Total505updates,4,136,960samples,8100s. No automatic retries,
additional chain, R2 upgrade or budget reuse. Final notification target must be
the explicitly configured current HAPI session, not a guessed historical ID.

## CPU command already executed

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.recovery.probe \
 --spec configs/experiments/recovery_r1_manual0001_20261002/spec.json \
 --output-dir runs/recovery_r1_manual0001_R0_PLAN --mode r0
```

CPU valid; two physical gates pending; no output/run/ledger mutation.
25 relevant CPU tests passed; the historical preflight test against the externally
changed YAML was deselected. The new spec independently passed CPU preflight.
Historical YAML/spec/pose/run/checkpoint records remain unchanged.
