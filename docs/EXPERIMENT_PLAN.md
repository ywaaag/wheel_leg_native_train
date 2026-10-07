# Plane standing experiment

This is a **conditional plan**, not authority to start simulation. The new
[ledger](../configs/experiments/budget.json) is all zero. Every output path
below must be new and every attempt must remain in that ledger.

## Source versus new recipe

| Item | Native B200 source | New standing spec |
| --- | --- | --- |
| Weight identity | `model_adapt_200.pt`, SHA `f440ef...b05698` | Same actor/critic and named Adam moments, explicit per-frame input expansion. Source Adam LR `1e-4` is intentionally replaced by spec LR `3e-5`, and the effective group is recorded. No Gym 47250 weight. |
| Observation | 22D + 110D = 132D, no command input | 25D + 125D = 150D, command `[0,0,0.363]` in every current/history frame. New first-layer command columns zero at initialization. |
| Ground | Native v2 inherited the mesh collider | One physical USD Plane at z=0, explicit friction 0.5/0.5 and restitution 0. |
| Height reward center | v2 B group `0.35 m` | `0.363 m` per user-accepted posture. This is a **new reward variable**, not behavior-equivalent refactoring. |
| Zero velocity reward | v2 B denominator `0.01 (m/s)^2`, yaw denominator `0.09` | Same widths and weights. Raw upright/height/zero-velocity/contact/effort/action-delta/joint-margin, weighted sum x0.01 s then terminal penalty. No per-term clip. |
| Control | Four physical leg position targets, two wheel velocity targets | Same six channels, action clip +/-1, scale/projection, 200 Hz PD, physical 40/5.5 Nm. Other colleague physical settings are not tuned. |

The source-only plane evaluation is the first physical gate. It records
composed Plane/material, six-joint control readback, first input/history,
continuous 10-second survival, drift, contact, closure, height, tilt and
saturation. If B200 already satisfies the new stand gate, do not run PPO just
to exhaust a budget. If it fails as an ordinary task outcome with valid
control/physics, first compare its per-env trace and then decide whether
standing adaptation is warranted. Nonfinite, closure and control-ownership
faults block training.

The old v2 B200 review had 8/8 continuous 10-second episodes but failed its
**old** 0.34-0.36 m steady-height gate; one example was 0.36309 m. That
historical gate is retained in its original evaluation JSON. The user now
accepts about 0.36 m, so this project freezes 0.34-0.38 m and does not claim
that 0.35 m was mechanically unreachable. If the new plane baseline fails
for an unexpected height or contact reason, a separate no-PPO probe should
capture raw/clipped action, paired leg-target projection before/after, actual
q/dq, PD request/applied effort, contact and root height. Do not insert a V14
spring force or retune reward based on the old height gate alone.

## Proposed one-time budget request

1. `source_eval`: one 64-env layout / 8 scored-env continuous 10-second run,
   total process wall cap **600 s**, no PPO.
2. Only if adaptation is justified: `smoke`: at most **3 actual PPO updates**,
   64 env x128 steps = **24,576 samples**, process cap **300 s**. Verify reset,
   command/history, current reward, finite loss, changed actor and retained
   B200-initialized critic/Adam. Ordinary falls are task data.
3. Conditional `formal`: at most **200 actual PPO updates**,
   **1,638,400 samples**, process cap **3600 s**. Checkpoint/2-second light
   evaluation every 100 updates; independent 10-second evaluation at 200 and
   final. No motion command is sampled. Candidate selection compares source,
   milestones and final under the same plane/seed/standing protocol.
4. Optional separate `evaluate` allowance after training: up to two bounded
   10-second source/candidate comparisons, each external process cap 300 s.
   GUI `play` remains unapproved and is not an acceptance result.

Old v6 500 updates took 5274.83 s including its evaluations, about 10.55 s
per update overall; its measured rollout was around 6.46 s per update in
four-update benchmarks. Thus 200 updates might need roughly 35 minutes plus
evaluation/initialization, but the new plane scene and shared GPU can change
throughput. The 3600 s cap is a hard stop, not a speed promise. Source mesh
evaluation completed in about 54 s; 600 s leaves substantial startup and
scene-change margin. No old budget is transferred.

Use [TOOL_INDEX.md](../TOOL_INDEX.md) for exact interpreter and commands.
After authorization, update only the new ledger's `authorization` and phase
limits to the approved values, then rerun plan-only preflight. The background
monitor owns updates, timeout, snapshots and final ledger settlement. A failed
attempt consumes its actual updates; never erase it or reset the counters.
Future command stages require new experiment specs and independent budget,
following stand -> bidirectional line -> bidirectional yaw -> low-speed
combined -> expanded speed -> dynamic starts/stops and turns.
