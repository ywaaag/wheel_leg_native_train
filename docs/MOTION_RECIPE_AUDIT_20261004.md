# Motion recipe audit, 2026-10-04

## Result and scope

Confirmed experiment/configuration drift precedes any new claim about optimization
dynamics. The warmup and speed1 runs reverted to a different runtime recipe from
the fixed-command run. Their results cannot isolate critic warmup, Adam surgery,
or increased command magnitude. This does not establish the unique cause of the
original mixed/fixed runs' reverse response.

Read-only evidence analysis and CPU reproduction only. No Isaac, simulation,
PPO collection, trainer control, ledger mutation, or runtime source edit.
No current GPU allocation/trainer status is claimed from historical PID fields.

## Verified identities

Compared every `source_snapshot_sha256` entry with its corresponding file:

| Formal run under runs/ | Files verified | Mismatches |
| --- | ---: | ---: |
| motion_gpu1_20261002 | 25 | 0 |
| motion_fixed_20261003 | 26 | 0 |
| motion_warmup_retention_20261003 | 25 | 0 |
| motion_speed1_20261003 | 25 | 0 |

Speed1 update497 checkpoint SHA independently matches the terminal report:
`acc29f8931ac59cb29f508fd829112a8dfde1dc1bd0c2f59647f25295a681eeb`.
Snapshot behavior is corroborated by the reward fields and weighted values
actually recorded in each run's metrics. Historical snapshots are preserved.

## 1. Fixed-command configuration was not implemented in later runs

The warmup and speed1 snapshot specs request L1 `command_mode: fixed`.
Their `runtime_env.py` never reads that key. Reset, pre-physics, and observation
paths unconditionally invoke the ramp scheduler. The speed1 CPU reproduction
at times `[0, 1.5, 3, 6.5, 8]` seconds yields commands `[0, .5, 1, .5, 0]`,
not constant 1m/s. The actual fixed-command run *does* read the key.

Evidence: speed1 `source_snapshot/runtime_env.py:94,114,130` and
`domain_schedule.py`; fixed `source_snapshot/runtime_env.py`.
Thus fixed-command steady-state learning has been tried, but speed1 was not
another instance of that protocol.

## 2. Tracking weights and initial reward width reverted

Warmup/speed1 specs carry separate linear/yaw tracking weights of 4 each.
Their reward snapshots calculate only one combined `velocity_tracking` term,
weighted by 1. The two separate configuration keys are silently ignored.
CPU reproduction changes both ignored weights from 4 to 400: total reward
changes by exactly zero. Recorded raw/weighted tracking values agree with weight1.

Both trainer snapshots also omit the initial stage-width assignment present in
the original motion and fixed trainers. Runtime receives base linear denominator
`.01`, rather than the configured L1 `.04`. `change_stage` can apply stage widths,
but both new runs have no task progression and no promotion path to call it.

Evidence: speed1 `source_snapshot/domain_reward.py:9-21`,
`train.py:201-216`, `runtime_env.py:144-153`; compare fixed `train.py:210`.
Warmup has the same omissions and the same recorded reward field set.

For speed1's actual reward, with vy=yaw=0:

| Command vx | Actual vx | Raw combined tracking |
| ---: | ---: | ---: |
| 1 | 0 | 3.7201e-44 |
| 1 | .4 | 2.3195e-16 |

This is an almost absent tracking reward over those error ranges, independently
of upright weight. Combined tracking multiplies the linear and yaw Gaussians:
large linear error also attenuates the incentive to correct yaw, and vice versa.
This is a concrete signal-quality concern, not a proof that it caused all
historical reversal. PPO uses sampled returns, not direct differentiation
through this reward with respect to physical velocity.

## 3. Reported speed1 improvement omits substantial yaw/contact regression

Recomputed speed1 command-group metrics with sample-count weighting:

| Updates | vx m/s | yaw rad/s | mean absolute yaw rad/s | Dual contact |
| --- | ---: | ---: | ---: | ---: |
| 1-50 | .08294 | -.14060 | .14624 | .99338 |
| 100-200 | -.02698 | -.29075 | .29388 | .98674 |
| 300-400 | .06550 | -1.22073 | 1.22128 | .99995 |
| 448-497 | .26610 | -1.73549 | 1.74092 | .92060 |
| 497 only | .41261 | -2.19045 | 2.19392 | .83903 |

These groups use episode-assigned target labels and include entry/ramp/hold/exit/
parking samples: `runtime_env.py:187-197` applies no hold-window filter.
Therefore `.30540m/s` at update497 is error against the effective ramp command
over the grouped samples, not independently measured steady-state error to 1m/s.
The zero-command `.00393m/s` figure is signed mean velocity, not net drift;
its mean absolute velocity is `.01444m/s` for that update. Opposite motions
can cancel in signed means. Neither statistic replaces independent standing.
Speed1 terminal has zero evaluations and no accepted candidate.

## 4. Retention protection is still absent in these later recipes

The fixed run's removed task progression already disabled retention stopping.
Warmup and speed1 specs likewise have no task progression; terminal reports
show null task curriculum and no evaluations. A name containing `retention`
does not establish that an independent retention gate ran.
CPU actor freezing can be real while behavioral retention remains unverified.
Source standing regression certifies the source, not the updated policy.

## 5. Existing PPO evidence is stronger than the handoff states

`isolated/motion_fixed_20261003/diagnostics/ppo_replay_evidence.json` already
records 16 actual offline optimizer steps on 8192 real samples. Installed versus
minimal-reference final actor/critic parameter differences are both zero;
minibatch alignment error is zero. The accompanying audit reports three shuffle
seeds and historical early-update clipped-objective changes. Thus a blanket
claim that only PPO0 or pre-update probability ratios were checked is outdated.
It does not certify unrecorded late updates or identify their failure mechanism.

The full capture GAE report says timeout augmentation uses pre-action V(obs_t),
not post-physics terminal value. Calling that the terminal-state bootstrap is
inaccurate. The report quantifies the difference without proving it caused reversal.
The quoted wheel std `.0433/.0354` comes from indices2/5; the four leg std values
in the replay JSON are approximately `.0802/.0781/.0900/.0799`.

## Next engineering step

Prepare one explicit, versioned effective recipe before new experiments. CPU
preflight must check that requested command mode, reward keys, initial stage
width, retention owner, and evaluation protocol are actually implemented by the
selected execution tree. Persist those effective values at the CLI/runtime
boundary. Do not silently fix or reinterpret historical specs/artifacts.

After that preparation, a separately authorized small physical check can verify
the effective command/terms and zero/positive/negative/yaw behavior. No new
budget or training is implied by this audit. Further normalization or optimizer
comparisons should use one identical effective recipe and the existing frozen
data wherever feasible. Repeating already completed PPO0 checks or changing
several recipe variables cannot resolve the current attribution problem.

## Reproduce

`/home/kellen/anaconda3/envs/issaclab/bin/python scripts/audit_motion_recipe_20261004.py`

The script reads immutable manifests/snapshots/metrics, executes only snapshot
pure Torch reward/schedule functions on CPU, checks SHA and assertions, and
prints structured results. Exit0 verified on 2026-10-04. All source/hash and
CPU reproduction checks passed; no simulator behavior is claimed by this run.
