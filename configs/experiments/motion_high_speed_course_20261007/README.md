# B250 straight high-speed course

Authorized source: B/formal/model_update_250.pt, SHA256
5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e.

Training uses inherited global 1/2/24/2-second command schedule and 31-second
episodes (24/31 nominal holding). Evaluation uses 2/8/8/8 plus 4 seconds zero,
30 seconds total; hold window is 10-18 seconds. Per-stage schedule metadata in
the initial preparation is evaluation metadata; actual training uses the global
curriculum.schedule_s. Reset timing and physical reset remain unchanged.

L2/L3/L4 retain old tasks and use fixed 64 slots: zero16, old24, new24.
Each current direction owns12 slots. Old directions own6/4/3 slots at L2/L3/L4.
Episode-target cohort width: zero and +/-0.5 use0.04; +/-1 and all new speeds use1.
No retention, yaw tasks, optimizer surgery or advantage-normalization change.
Actor/critic/Adam/std and recoverable RNG load from B250; actual LR3e-5.
The simulator starts from a new reset, not a restored physical state.

Raw linear tracking examples exp(-error^2/denominator), with vy=yaw=0:

| error | denominator0.04 | denominator1 |
|---|---:|---:|
|0|1|1|
|0.2|0.367879|0.960789|
|0.5|0.00193045|0.778801|
|1|1.38879e-11|0.367879|
|2|3.72008e-44|0.0183156|
|4|1.91517e-174|1.12535e-7|

Tracking weight8 and policy dt0.01 multiply these by0.08, once. Float32
underflow of extremely small narrow-kernel values is expected, not clipping.

Limits: smoke10 updates; formal4500; each stage1500; full chain18 hours.
Formal evaluates every250 updates, checkpoints every100. All learned commands
are evaluated at each checkpoint; two consecutive old-ability failures stop.
Final L4 certification uses seeds104/137/173 and eight scored environments each.
Stage acceptance and final multi-seed certificate are separate records.

CPU:60 passed,1 historical exhausted-ledger fixture excluded. Source plan-only
PASS, no writes. New fixture checks SHA/network/Adam/LR, cohort widths, exact
slots, budget and separate source/new/per-stage registration. Run source and
smoke through scripts/run_motion_high_speed_preparation.py, then submit formal
through the existing detached launcher on physical GPU1. Notification target:
191bacc3-e5c7-4b8f-ae3d-5677eada837b (current worker session).

Bounded smoke handling: the10-update smoke includes full evaluation switching.
If its1200-second phase wall interrupts later command evaluations, formal may
proceed only if all10actual updates are recorded, actor changed, holding samples
exist, zero full evaluation was saved without runtime fault and terminal has no
exception. STOPPED_BOUNDED remains unchanged; this is wiring evidence, not
capability acceptance. No extra smoke updates or simulator restart is performed.

Changed implementation files: command_v6/config.py, completion.py, ledger.py,
monitor.py, train.py, runtime/env.py, tools/preflight.py. Added scripts:
prepare_motion_high_speed_course.py, run_motion_high_speed_preparation.py,
continue_motion_high_speed_submission.py, submit_motion_high_speed_formal.py.
Added test: tests/test_motion_high_speed_course.py. Configuration and this entry
belong to the fresh20261007directory; historical runs/specs/ledgers unchanged.
