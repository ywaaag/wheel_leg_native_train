# Recovery manual pose capture

One environment, plane0.5/0.5/0, original USD,1ms physics/5ms PD/10ms command updates,
40/5.5Nm. No actor, optimizer, PPO, or training ledger. Four actual leg position targets;
ADJUST mode has zero wheel **velocity target**, not wheel locking. PASSIVE has zero effort
on all six active joints; passive linkage damping remains. Default PASSIVE from the
offline-valid guide-wheel-supported low pose. This is manual candidate collection,
not Recovery training or standing/recovery acceptance.

## Run from desktop terminal

```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 PYTHONPATH="$PWD/src" \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.recovery.capture \
  --spec configs/tools/recovery_capture.json \
  --output-dir "runs/recovery_pose_capture_$(date +%Y%m%d_%H%M%S)" \
  --max-wall-seconds 1800 --run
```

Remove `--run` for CPU plan: no AppLauncher, output creation or ledger mutation.
`--help` is also CPU only. Every manual session requires a new output directory.
GUI loop wall bound defaults30minutes, including initialization; cleanup can take additional
time. This is not an external hard-timeout supervisor or an allocated training budget.

## Operation

- Click viewport for keyboard focus.1/2/3/4 select left hip/left active/right hip/right active.
- Up/Down changes selected target by0.02rad (configurable `--step-rad`, maximum0.1).
- Four sliders show actual joint target radians, clamped to USD bounds; no direct q teleport.
- Space toggles ADJUST/PASSIVE; buttons do the same. ADJUST can have a large error relative
  to fallen q: start with small changes and inspect torque. No pair projection is used.
- P or Pause stops the simulation timeline; camera remains usable. Resume continues the same episode.
- S or Save writes one new pose JSON. R resets to the same closure-consistent low pose,
  zero velocity and PASSIVE. Esc/Ctrl-C/window close exits.

For useful passive initial states: adjust, switch PASSIVE, wait until motion settles,
then pause and save. Requested vs executed mode/targets are separately recorded, so UI
changes during rendering cannot be mislabeled as already applied control.

## Evidence and limitations

Each `pose_*.json` includes all joint q/dq (active and passive), root pose/velocities,
actual body transforms, contact sensor world force vectors, authored ideal collider
clearances, PD request/clipped/applied effort, targets, closure and episode identity.
`manifest.json`, `control_readback.json`, source/config/YAML snapshots and
`terminal_report.json` keep the session identity. No per-step JSON or policy trajectory.
Screenshot is not automated in this first version (`NOT_CAPTURED`); optional manual
screen capture can accompany the numeric JSON.

Ordinary low height/body support do not auto-reset. Nonfinite, closure>5mm,
ideal floor penetration>5mm or actual joint-limit violation stop and save a fault record.
Interbody penetration remains UNKNOWN; ideal gap is not PhysX contact distance.
Instantaneous low velocities are a candidate flag, not evidence of sustained settling.
No manual record is automatically admitted to training. Weak-part support safety is not certified.

Current external colleague YAML differs from the historical Recovery spec SHA.
The independent [capture config](../configs/tools/recovery_capture.json) explicitly pins
the current YAML SHA and original base-spec SHA. Historical specs/ledgers remain unchanged;
this does not establish dynamic equivalence to older runs. Further dependency drift fails preflight.

CPU controls/rotated collision support/CLI side effects/exclusive output tests pass.
No Isaac GUI was launched during implementation; UI integration and real passive settling
remain runtime-unverified. Send the saved **directory path**, not manually transcribed angles.
