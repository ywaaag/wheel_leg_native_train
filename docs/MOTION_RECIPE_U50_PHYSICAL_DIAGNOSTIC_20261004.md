# U50 single-update diagnostic: 2026-10-04

## Scope and identity

This diagnostic used the frozen `model_update_50.pt` checkpoint, its own actor/critic/Adam state, and the existing eight rollout blocks from `runs/motion_recipe_u50_capture_20261004`. The offline replay used seeds `81023`, `81024`, and `81025`, one complete PPO update per seed, 16 optimizer steps per path. Actual and reference PPO parameters matched within the configured check (`max abs diff = 0` for actor and critic for all three seeds). Replay models were written only under `isolated/motion_recipe_20261004/diagnostics/u50_replay_20261004e/models/` and are marked diagnostic-only.

The fresh physical comparison identity is in `configs/experiments/motion_recipe_u50_eval_20261004/spec.json`; it binds update50 and the three replay models, fixed command mode, the L1 recipe, 64 environments, 8 scored environments, seed 104, 10 s zero-command and 9 s nonzero-command evaluations, and the same target windows. Online PPO is zero. Its independent ledger is `configs/experiments/motion_recipe_u50_eval_20261004/budget.json`.

## Supervision gate

The isolated monitor now waits briefly for a child terminal report, writes a missing-terminal fallback atomically, and finalizes an exact attempt only once. CPU tests cover normal child exit, exception exit, timeout, missing terminal, an existing terminal, and repeated reconciliation. The suite passed **37 tests**.

The one authorized physical comparison attempt was `u50eval20261004`. It failed before simulation because the child imported `CommandEnv` before inserting the colleague asset module root, producing `ModuleNotFoundError: agent_world`. The parent preserved this as `FAILED` and charged exactly one physical-evaluation attempt; it did not retry. The failed child entered its imports before its `try/finally`, so its terminal was synthesized by the supervisor. The evaluator has since been corrected so asset-root insertion and imports are inside the terminal-protected block, but that correction was not physically retried under this authorization. There are no physical A/B results from this attempt.

## Frozen rollout analysis

The eight blocks contain 65,536 transitions. Rollouts 0–6 each contain 8,192 samples and no timeout. Rollout 7 contains 64 timeout transitions (one per environment), with no true terminations. Thus the observed timeout boundary is present; true-termination behavior remains CPU-fixture-only. Per-command counts over all blocks are: `-0.2`: 10,115; `-0.1`: 10,240; `0`: 23,669; `+0.1`: 10,559; `+0.2`: 10,953.

The independent reward/storage/GAE checks from the capture remain within their recorded tolerances. The last-block timeout uses the runtime's `V(obs_t)` bootstrap semantics; a pre-reset-terminal-value alternative is retained only as a counterfactual. The full per-rollout and per-command value, return, raw/normalized advantage, tracking and saturation statistics are in `isolated/motion_recipe_20261004/diagnostics/u50_replay_20261004e/rollout_analysis.json`.

For the frozen PPO objective, sample-count-weighted mean total surrogate improvement across the three seeds was:

| command | mean total improvement | seed population SD |
|---:|---:|---:|
| +0.2 m/s | 200.945 | 29.190 |
| -0.2 m/s | 62.840 | 18.764 |
| 0 m/s | 42.088 | 11.999 |
| +0.1 m/s | 12.997 | 8.307 |
| -0.1 m/s | 11.541 | 5.028 |

Therefore `+0.2 m/s` dominates the actual full-batch contribution. This conclusion uses `per-sample objective change × sample count`; it is not inferred from a group mean. The 64 timeout samples are only 0.0977% of the batch, so the timeout window cannot dominate the total objective contribution. The three overall surrogate improvements were `0.003402`, `0.005410`, and `0.004244`; post-update sample KL estimates were about `0.0041–0.0059`, with clip fractions `0.042–0.063`.

## Physical conclusion

The requested A (unmodified update50) versus B1/B2/B3 same-protocol physical comparison did not run because of the pre-simulation asset import failure. Consequently this run provides **no evidence** that one PPO update reproducibly causes backward motion in physics. The frozen batch does show a positive surrogate objective dominated by the `+0.2 m/s` group, but that is an optimization-batch fact and cannot be converted into a physical motion claim.

The only next experiment with information value is one fresh, explicitly authorized physical comparison using the corrected evaluator and the already frozen four models, with no PPO updates: verify asset import before AppLauncher-dependent environment construction, then evaluate all five commands for A/B1/B2/B3 under the bound in the new spec. A repeated physical decline across all three replay seeds would support objective/physics mismatch for a single update; mixed or unchanged results would weaken that hypothesis and require a multi-update or distribution-shift experiment later. No such experiment is automatically submitted here.
