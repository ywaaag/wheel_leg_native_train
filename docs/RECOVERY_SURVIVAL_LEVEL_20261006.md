# Survival and Level R0 -> R1

Updated: 2026-10-06. User authorized headless detached training, at most10000
actual PPO updates. The fresh budget does not transfer or reset any old allowance.
Entry: [STATUS](../STATUS.md); [spec](../configs/experiments/recovery_survival_level_from50_20261006/spec.json).

## Source and Physical Contract

GUI-approved `runs/standing_scissor_20261006/formal/model_update_50.pt`.
SHA256 `1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`.
Strict150D actor/critic/Adam load, applied LR3e-5, fresh physical reset and
curriculum counters. Frozen retention teacher is this same source, coefficient.02;
the older STAND500 network never takes control in this autonomous task.

Mechanical knee-stop USD/plane0.5/0.5/0,25D+125D,leg1.6rad/wheel100rad/s,
physics1ms/PD5ms/policy10ms,40/5.5Nm and all runtime guards unchanged.
Command remains `[0,0,0.36]`; zero command does not imply speed certification.

## Revised Objective

Avoid falling and keep the body level. Speed, drift, yaw, mirrored joints,
leg-length/load imbalance and wheel offset remain measurements, not gates.
Old stationary acceptance results and rankings are historical and unchanged.

Rewards retained: Gaussian height(weight3,width.04m), pitch/roll quadratic
costs(weight-4 each,scale.12rad,unconditional), dual support(.5), vertical
motion(-.1), roll/pitch angular motion(-.1), effort/action-rate/joint-margin
and height-overshoot costs. All continuous terms multiply policy dt once.
Removed contributions: linear/full-angular/yaw settling, mirror posture,
leg-length balance, wheel difference, support balance and wheel offset.
No reward clipping, wheel locking, added physical compensation or new actor input.

Online success: height.34-.38m, tilt<=.18rad, each abs pitch/roll<=.15rad,
dual forces>2N and chassis clearance>=.25m, continuous2s. Success_once remains10;
training episodes may end at success. Independent evaluation continues the same
episode10s and disables success-only reset.

Full acceptance:8/8continuous10s, no fault/reset;2-10s mean height.34-.38m,
>=90% height samples in range, dual support>=95%, mean abs pitch/roll<=.10rad
each, peak<=.15rad each, peak tilt<=.18rad, closure<=5mm and policy-sampled
saturation<=5%. Saturation is not an every-PD substep certificate.

## Curriculum

R0 uses the existing nominal/small-perturbation library. Two non-overlapping
128-completed-episode windows with >=90% success and0faults, plus two consecutive
full confirmations, unlock R1 on subsequent resets only. Full confirmations
at100/200 updates and every500 thereafter. No promotion by reward alone.

R1:60% existing enlarged near-standing family `R0_perturbed`,40% R0. Within
the R1 family, nominal10%/three perturbed poses90%; both splits have four
closure-resolved poses, distinct training/holdout seeds. Initialization remains
zero-velocity direct reset, no warmup stabilizer. Pose identities and actual
rejection/sample counts are logged. This is bounded library generalization,
not arbitrary-pose or disturbance certification. R2 low-pose and R3 disabled.

Full R1 evaluations independently measure R1 and retained R0. A retained R0
failure prevents a candidate certificate; persistent R0 regression stops training.
Failure on a new R1 task alone continues learning. Final durability restores
the selected checkpoint's curriculum stage and independently rechecks retained R0.
Ranking:acceptance, passed envs, continuous survival, accepted stage, pitch+roll,
contact, closure,SHA. Drift/reward/symmetry do not rank this task.

## Budget and Submission

Source10s/PPO0<=300s -> smoke3updates<=300s -> formal9997updates<=34140s ->
selected candidate100s/PPO0<=1200s;60s reserve. Conservative total cap10h.
64env x128steps, total10000updates/81,920,000samples. No automatic new chain.
Checkpoint every100updates plus final; full evaluations100/200/every500/final;
no2s lightweight simulation. Formal plan has22 full milestones; each R1
milestone also has one retained R0 case. Runtime timing remains measured evidence.

```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.stand_chain \
  --spec configs/experiments/recovery_survival_level_from50_20261006/spec.json \
  --output-dir runs/recovery_survival_level_from50_20261006 \
  --hapi-session 6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1 --launch
```

Submission is deduplicated; never rerun an existing output. One formal startup
handshake, then background ledger/monitor/selection/report/HAPI callback. Notification
does not authorize continuation. TensorBoard reads update-end JSONL through the
existing viewer, separately from control/PPO. Live URL is in STATUS after launch.

## CPU Evidence

58focused tests pass: new/legacy gates, strict actor/critic/Adam/LR, motion-only
diagnostics, preserved physical failures,128-episode windows, R1 cap,40% rehearsal,
retained R0 failure, source trace reclassification, selection and evaluation frequency.
Three historical broader tests depend on old external-YAML identity/authorization/
execution-snapshot import path; failures are recorded, not rewritten into passes.
Fresh source preflight PASS;80additional general checks pass after excluding the
known historical-YAML test and historical submission-only fixtures.

## Startup Evidence

Source phase COMPLETED/PPO0 in100.72s:8/8continuous10s accepted under the new
protocol, height~.36667m/contact100%, no fault; vx~.704m/s remains measured.
Smoke COMPLETED3actualupdates/24,576samples/35.33s, actor parameters changed.
One formal handshake RUNNING/actual1:trainer2210972, worker2208166,
attempt700a9368fe7b4a90885bd978b476d7ce. No further training-log polling.
TensorBoard http://127.0.0.1:6013 HTTP200, detached smoke/formal viewers.
Actual manifests/ledger/terminal override this startup snapshot. This proves
runtime wiring and source behavior, not learned R1 or final long-duration success.

Changed shared modules:recovery/{domain,standing,runtime,validation,recipe,selection},
command_v6/{config,completion,train,tools/evaluate_checkpoint}, existing
scripts/prepare_standing_balance.py. Added tests/test_standing_survival_level.py,
fresh config/spec/ledger/pose/probe artifacts and this document. Navigation and
architecture/change log updated. No original model/spec/run/asset/ledger modified.
