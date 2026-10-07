# Fixed433 gate-first diagnosis

2026-10-02. No physical budget reused. New ledger UNAUTHORIZED, PPO budget0.
Source433 SHA `a8b189d3bb9b46edd25b7a7c06c3c096dc2d18ce99b4f1b6ddb6f3046b1150d5`;
source checkpoint's original spec identity is checked separately from diagnostic spec.
STAND remains frozen SHA `fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1`.
Original reward,1.6rad Recovery legs/100rad/s wheels,plane,40/5.5Nm,1/5/10ms retained.
No settling_reward enabled. No STAND retraining. No gate relaxation.

## Preparation evidence

CPU plan passes model/asset/spec identities;26CPU regressions pass,1historical
preflight excluded. Actor forward default stochastic_output=False verified from
installed RSL-RL. No Isaac imported or run created by plan.

## Proposed one-time scope and budget

64env layout,8scored holdout manual0001 first episodes,same evaluation seed.
Max18sim seconds covers passive initialization plus15s Recovery/FSM timeout.
Stop recording each scored env at its first done; no concatenation after reset.
New physical cumulative wall300s including startup,execution,cleanup; use external
TERM275s then kill grace15s, leaving10s supervisor margin. One attempt,no retry,
PPO0. Based on earlier329s for two full evaluations,one case may fit300s but
throughput/shared GPU can vary. Timeout means INCOMPLETE, not policy fall.

## Exact commands (cwd project root)

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.recovery.probe \
  --spec configs/experiments/recovery_diagnostic433_20261002/spec.json \
  --output-dir runs/recovery_diagnostic433_20261002 \
  --mode checkpoint \
  --checkpoint runs/recovery_r1_manual0001_retry_20261002/formal/model_update_433.pt \
  --seconds 18
```

CPU command verified. Physical command below may be executed only after new
ledger authorization; do not infer authorization from this document:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
timeout --signal=TERM --kill-after=15s 275s \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.recovery.probe \
  --spec configs/experiments/recovery_diagnostic433_20261002/spec.json \
  --output-dir runs/recovery_diagnostic433_20261002 \
  --mode checkpoint \
  --checkpoint runs/recovery_r1_manual0001_retry_20261002/formal/model_update_433.pt \
  --seconds 18 --run
```

## Evidence and decision

Existing result.json per_env records retain root/pose/state,gate_diagnostics_100hz
(11predicate masks,full world linear/angular velocity,leg/wheel target jump,dwell),
control_diagnostics_100hz (q/dq/raw/clipped action,target pre/post limit,request/
clipped/applied effort,closure). All copied in _get_dones before auto-reset.
Sample frequency100Hz; per-channel sampled effort clipping can be recomputed,
continuous5ms-PD saturation cannot be certified from these rows.
Runtime faults,task failures,incomplete remain separate. SIGTERM partial evidence
uses pre-reset snapshot when available; full trace may not be written on interruption.

When height is in gate,compare per-condition failure fractions and longest
simultaneous passing window against0.5s. If speed/yaw still violates the gate,
prioritize Recovery settling. If physical state is calm but only leg/target predicates
block,propose bounded frozen STAND takeover-domain test. Existing0.15rad is a
provisional gate,not proof that more bent poses are impossible to accept. If actual
STAND_VERIFY fails,consider STAND robustness next. No threshold changes based on
GUI alone. This diagnostic does not itself validate a broader STAND takeover domain.
