# Motion recipe wiring fix

Prepared an isolated execution version at `isolated/motion_recipe_20261004/src`.
It is based on the previously working fixed-command snapshot, not the shared
source tree used by Recovery.

Command mode is explicit (`fixed` or `ramp`) at the stage and evaluation
boundary. Fixed mode returns the sampled target at reset and every
observation/pre-physics update; ramp mode retains entry/ramp/hold/exit.
Unknown modes fail schema validation or environment construction.

Reward tracking mode is explicit. `combined` emits one `velocity_tracking`
term. `separate` computes and records independent linear and yaw terms and
requires both weights. Active-stage denominators are applied before environment
creation without mutating the requested spec. They are recorded as `(m/s)^2`
and `(rad/s)^2`; `dt=0.01` is applied once.

Retention is independent of promotion. `RetentionGuard` checks accepted zero command
at each retention evaluation and stops after configured
consecutive failures even when task progression is disabled. Confirmations are
written to `retention_confirmations.jsonl`; effective configuration is recorded
separately from the requested spec.

The prepared spec and ledger are intentionally **UNAUTHORIZED**:

```text
configs/experiments/motion_recipe_20261004/spec.json
configs/experiments/motion_recipe_20261004/budget.json
```

The second repair pass fixes trainer STOP scope, makes retention cadence
independent of normal evaluation (`50,100,150,200` for the prepared 200-update
budget), snapshots the command already prepared for the current evaluation
transition, and distinguishes fixed steady-state gates from ramp stop gates.
Missing gate metrics are failures/unknowns rather than implicit passes.

CPU tests passed 10/10 and the isolated source compiled. Source-eval plan-only
returned `READY_NEEDS_AUTH` with zero simulation, zero PPO and zero files
written. Formal plan-only correctly reports the missing preceding source phase.
No AppLauncher, simulation, physical sampling or PPO was started.

## Final CPU pass (2026-10-04)

Changed files in this pass (all relative to the project):

- `isolated/motion_recipe_20261004/src/native_stand/command_v6/train.py`: retention uses the real global STOP also used by the signal handler; terminal stop_kind distinguishes retention from user signals; explicit motion evaluation commands remain in the evaluation list.
- `isolated/motion_recipe_20261004/src/native_stand/command_v6/tools/evaluate_checkpoint.py`: the evaluation_state context wraps target changes, reset and buffer setup as well as rollout. It restores command_mode, forced_target, capture_terminal, episode duration, actor mode and CPU/CUDA RNG. Cleanup attempts all restorations; cleanup errors are attached to the original exception instead of replacing it.
- `isolated/motion_recipe_20261004/src/native_stand/command_v6/domain/task_curriculum.py`: zero alone is the accepted retention baseline; missing zero is incomplete and counts as a failed confirmation. Motion results retain their own acceptance gates.
- `isolated/motion_recipe_20261004/src/native_stand/command_v6/tools/preflight.py`: displayed evaluation plan includes the actual independent retention checks at 50/100/150/200.
- `isolated/motion_recipe_20261004/test_recipe_cpu.py`: 16 CPU tests pass, including real trainer STOP/signal state, zero-only retention, missing zero, fixed/ramp gates, and evaluation-state normal/exception restoration.
- Deleted unused `domain/stop_state.py`; there is no second stop state.
- `configs/experiments/motion_recipe_20261004/spec.json`: retention commands are only [0,0]; motion progress endpoints remain; wall limits enabled. The independent budget remains UNAUTHORIZED and was not edited.

Effective prepared recipe: active L1, fixed training and fixed evaluation, separate linear/yaw weights 4/4, squared denominators .04/.09, 64x128 rollout, LR 3e-5, 200 formal updates. Retention every 50 updates stops after two zero failures; passing resets the counter. No reward/PPO tuning was performed.

Executed CPU command:

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q isolated/motion_recipe_20261004/test_recipe_cpu.py
```

Result: 16 passed. State-restoration tests exercise the context used by evaluate_actor with fake settings and injected reset/rollout-labelled exceptions; they do not exercise Isaac reset or the full physical evaluator. Trainer tests exercise its actual STOP helper and signal handler; real checkpoint serialization and terminal accounting still require the short physical validation.

Exact plan-only entry (omit --run):

```bash
PYTHONPATH=/home/kellen/wheel_leg_native_train/isolated/motion_recipe_20261004/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.train \
  --spec /home/kellen/wheel_leg_native_train/configs/experiments/motion_recipe_20261004/spec.json \
  --phase source_eval --output-dir /home/kellen/wheel_leg_native_train/runs/motion_recipe_20261004/source
```

Repeat with phase/output suffix smoke and formal. Source reports READY_NEEDS_AUTH; smoke/formal report missing authorization and preceding phase. These are intended blocks, not permission to bypass the ledger. All report simulation=0, ppo=0, files_written=0. Formal plan shows retention/full=true at 50/100/150/200.

## Proposed short physical validation — UNAUTHORIZED

Suggestion: total 900 seconds wall clock, at most 3 actual PPO updates; source_eval <=450 seconds, smoke <=450 seconds. Do not run formal 200 as part of this short validation. No retry or automatic long training.

Before authorization/run, read `nvidia-smi` GPU/process identities and `ps -eo pid,args`; verify physical GPU1 availability and that Recovery source/output are untouched. Use CUDA_VISIBLE_DEVICES=1 with logical cuda:0 and verify actual process GPU ownership in runtime logs/nvidia-smi. Stop this validation on identity mismatch, failed source standing regression or physical runtime fault. Ordinary source motion failure is task data, not a wiring failure.

Future entry is the exact plan-only command above with `CUDA_VISIBLE_DEVICES=1` and `--run`, first source_eval/source, then smoke/smoke only after source passes and a fresh exact-ID ledger authorization/reservation exists. It is currently blocked by UNAUTHORIZED. source_eval evaluates the frozen source; smoke initializes from that same frozen source, not an evaluated copy. Current formal would also initialize from source (not smoke); formal is outside this short proposal and remains blocked.

Source checks zero standing. Smoke checks fixed commands, separate raw/weighted tracking, initial effective widths, finite updates/actual LR and independent zero/positive/negative evaluation. Record yaw, contact, tilt/height, six-channel actions/torques and saturation. Freeze checkpoint SHA before evaluation. Motion acceptance failure is recorded accepted=false without claiming retention regression; zero retention failures follow the declared counter. Runtime fault ends the attempt. Verify final checkpoint, completed updates/samples, STOPPED_BOUNDED versus normal completion, and one terminal settlement. Never deliberately introduce physical faults to test early stopping.

CPU success is not behavior acceptance and does not establish the unique cause of reverse learning. Waiting for short physical validation authorization.
