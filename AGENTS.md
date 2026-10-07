# Native closed-chain project rules

This project is `/home/kellen/wheel_leg_native_train`. Read `README.md`,
`STATUS.md`, `ARCHITECTURE.md`, the current spec linked by STATUS, then
`TOOL_INDEX.md` before running a command. A run's manifest, progress, terminal
report and evaluation JSON override a Markdown status snapshot.

Before designing or changing rewards, curricula, training experiments,
candidate selection, or acceptance, read `TRAINING_EXPERIENCE_REUSE.md`;
actual runs follow their spec, manifest, and raw evaluations.
For the prepared autonomous-standing task, also read
`docs/RECOVERY_STANDING_PLAN.md`; it is a handoff contract and does not grant
a runtime or PPO budget.

Only this project may be edited for its experiments. Keep the colleague USD and
source project, `/home/kellen/fudan_train`, `/home/kellen/wheel_leg_sim2sim`,
`/home/kellen/wheel_leg_training`, and all old audit runs read-only. Do not
move or overwrite checkpoints, raw evaluations, or ledgers. Record source and
asset SHA in every run. Current code describes the next run, not an old run.

The frozen native interface is in the experiment spec and `ARCHITECTURE.md`:
25D physical-joint frame, five oldest-to-newest frames, 150D actor/critic
input, six left-first position/velocity targets, 1 ms physics, 5 ms PD, 10 ms
policy, 40/5.5 Nm physical limits. Training, independent evaluation and GUI
playback use the same `CommandEnv` and plane scene. No Gym virtual-leg mapping,
Jacobian lookup, LQR, gravity compensation, static trim, hidden gating, or
effort-limit increase.

Run CPU tests and plan-only preflight before any AppLauncher. Plan mode writes
nothing. Each experiment spec directory owns an independent budget.json.
Only explicit user authorization permits simulation/PPO; follow STATUS to the
corresponding ledger, preserve all previous usage and reject duplicate chains. An
authorized attempt needs a fresh output path, exact-ID ledger reservation and
terminal accounting. Never infer an active trainer from an old PID. Do not
stop or change another task. A new reward, physical contract, command stage,
or acceptance gate requires a new experiment spec and run directory, while
the shared code stays in this one project.

Use `/home/kellen/anaconda3/envs/issaclab/bin/python`. The package is imported
from this project's `src/`; the colleague asset module root is supplied at
the CLI boundary after identity checks. Pure domain modules must not read
files, environment variables or Isaac runtime state.

## Evidence and Interface Changes

Read `docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md` before changing
evaluation, gate aggregation, diagnostics, preflight or submission interfaces.
These engineering changes do not authorize simulator use or a training budget.
Keep requested scoring windows separate from observed per-environment duration;
early termination must never shorten the acceptance requirement. Reject unknown
protocol fields, invalid SHA, contradictory gate decisions and missing scored
environments. Normalize gates by task; UNKNOWN or missing evidence cannot pass
or unlock a curriculum stage. Never treat uncollected diagnostics as measured zero.

Evaluation must restore actor mode, runtime switches and Torch RNG even after
setup, reset or cleanup failure. Restore RNG after all cleanup resets. Optional
diagnostics default to disabled, run only at explicitly selected updates and
must not change action sampling, gradients, optimizer updates or the recipe.
Label full-rollout probes, actual optimizer-step probes and offline replay
separately; unavailable historical gradients remain UNKNOWN.

Use the shared supervisor for new source -> smoke -> formal submissions. Formal
requires a persisted, identity-matched `wiring_certificate.json`, source identity,
active-phase health and exact ledger prerequisites. Require an explicit physical
GPU and the current HAPI session; never reuse a historical session ID. Verify
process command, start time, spec, output and attempt ID rather than PID alone.
An UNKNOWN handshake must report `started=false`. A commit, old quota, historical
AUTHORIZED field or terminal notification never grants new simulation permission.

## Git and Documentation

For every newly created experiment, prefix its root directory and experiment
name with the creation date/time in Asia/Shanghai: YYYY_M_D-HH_MM__<purpose>,
for example 2026_10_7-14_27__motion_width_ab. Use the same name for the config
root, run root, spec.experiment and artifacts.run_name where present. If the
minute/name already exists, append a collision suffix or use seconds; never
overwrite. Phase/arm children (source_eval/smoke/formal/A/B) keep their semantic
names. Do not rename existing/prepared/frozen experiments or historical evidence.
See docs/EXPERIMENT_NAMING.md; naming never grants runtime authorization.

Use TOOL_INDEX.md for current public entries and TOOL_INDEX_HISTORY.md only for
historical reproduction. Only supervisor is the public submission CLI; launcher,
monitor and stand_chain remain internal components. Recipe-specific preparers are
not generic configuration tools. Historical replay acknowledgment never grants
simulation authorization; retired fixed-GPU/run/session drivers cannot launch.

New submission interfaces are documented in `docs/ENTRY_SEMANTICS_FIX_20261007.md`.
Default GPU ownership is exclusive; shared mode requires a recorded explicit user
authorization note. Never exempt owners merely by process name or treat sharing as
training authorization. Distinguish submitted/current stage from verified formal
first update. Certificate readers validate only; the phase owner writes evidence.
Use canonical model roles; a source may be best overall but never best new.
Episode certificate failure, physical termination, time-limit truncation and
runtime fault are separate facts. Required smoke duration comes from the frozen
event declaration; insufficient sampling cannot be fixed by silently raising budget.

Follow `docs/GIT_WORKFLOW.md`. Version current source, tests, scripts, declaration
configs and documentation. Keep `runs/`, `isolated/`, USD/assets, checkpoint
binaries, mutable ledgers/budgets, submission records and frozen execution copies
local and read-only; do not force-add ignored evidence. Stage explicit paths,
review staged contents and preserve unrelated dirty changes. Do not reconstruct
an imaginary historical baseline from current files. Use detailed Chinese commit
messages when requested; do not push without an explicit request.

Update README, STATUS, ARCHITECTURE and TOOL_INDEX when public interfaces change.
Preserve dated historical statements and add explicit corrections/current entry
notes. List exact changed files, CPU checks, missing runtime evidence and known
compatibility limits. Do not describe a test or report repair as learned capability.

CPU regression, without AppLauncher:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```
