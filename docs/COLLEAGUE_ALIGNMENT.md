# Native training alignment with the validated colleague pipeline

This project now exposes the same **process protections** used by
`/home/kellen/桌面/11 (1)/11/wheeled-legged_RL`, while retaining the native
closed-chain physical contract.

## Reused ideas

- `ppo.critic_warmup_updates`: freeze actor parameters for the first N PPO
  updates while the critic fits the new return distribution. The run records
  the active interval and release update in `progress.json`.
- `ppo.clear_adam_first_moment`: explicitly clear Adam `exp_avg` after strict
  actor/critic restoration, preserving `exp_avg_sq`. The count of cleared
  tensors is recorded under `optimizer_initial`.
- Existing `TaskProgression` and `task_confirmations.jsonl` provide the native
  equivalent of command retention gates: zero-command standing is checked on
  every full confirmation, and a confirmed regression stops the run.
- Existing `RolloutMetrics.task_metrics` and `command_sample_counts` retain
  per-command evidence instead of relying on a global reward curve.

Both new PPO options default to disabled, so historical specs and Recovery
behavior are unchanged. Enable them only in a new experiment spec, for
example:

```json
"ppo": {
  "critic_warmup_updates": 10,
  "clear_adam_first_moment": true
}
```

## Deliberate non-reuse

The colleague project’s virtual-leg mappings, residual action controller,
wheel limits, reward weights, and asset-specific command semantics are not
copied. Native training continues to use the 25D frame plus 125D history,
physical six-target action, Plane scene, 1/5/10 ms timing, and 40/5.5 Nm
limits. The colleague source remains read-only.

## Verification

The warm-start unit test verifies that first moments become zero while second
moments are unchanged. Existing preflight tests still exercise the unchanged
spec path; a current `stand_plane.json` fixture reports its pre-existing
colleague-config SHA mismatch and is not evidence of a runtime regression.
