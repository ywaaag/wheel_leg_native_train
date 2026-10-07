# U50 physical A/B diagnostic on GPU0

## Execution and supervision

The v2 Kit evidence was preserved by reference: its py-spy stack shows the main thread in `AppLauncher -> SimulationApp._create_app -> _start_app`, before `CommandEnv` or `agent_world` import. The new evaluator now follows the successful `source_snapshot/train.py` order: create `AppLauncher({headless: true, device: cuda:0, multi_gpu: false})`, then add `asset_module_root`, then import `isaaclab_rl` and the native environment. CPU plan-only verified the actual supervisor entry, source hashes, four model SHA values, asset resolution, fixed command mode, and L1 denominators `.04/.09`; the 37-test CPU suite passed.

New attempt: `u50evalgpu020261004`, spec `configs/experiments/motion_recipe_u50_eval_20261004_gpu0/spec.json`, output `runs/motion_recipe_u50_eval_20261004_gpu0/`. The GPU0 preflight saw only the existing NX display process, not another trainer. Kit startup succeeded on RTX 4080 and logged `Environment device: cuda:0`; 64 environments were created. Recovery was not touched and online PPO was zero.

Four complete command groups were saved atomically, each with A/update50 and B1/B2/B3, 8 scored environments per model:

- `0.0 m/s`, 10 s
- `+0.1 m/s`, 9 s
- `-0.1 m/s`, 9 s
- `+0.2 m/s`, 9 s

The fifth `-0.2 m/s` group began its A item before the time guard and was therefore excluded as incomplete; its raw A file remains for audit. The attempt ended `STOPPED_BOUNDED` with 17 item files. Isaac cleanup after interruption made the measured wall time `908.809 s`, exceeding the 900 s bound by `8.809 s`; no extra work was performed after settlement. The exact ledger was charged once and agrees with the terminal and supervisor records.

## Paired physical results

The complete per-environment records and paired deltas are in `runs/motion_recipe_u50_eval_20261004_gpu0/comparison_summary.json`. All models retained dual-wheel contact near 1.0, low tilt (about `.009–.013 rad`), closure around `3e-5 m`, and zero saturation. All four commands failed their motion/standing acceptance gates because the policy did not track the requested positive speeds; this is a capability result, not a runtime fault.

Mean values over the eight scored environments:

| command | model | mean vx | abs vx error | direction fraction | mean drift |
|---:|---|---:|---:|---:|---:|
| 0 | A | -0.0297 | 0.0297 | n/a | 0.278 |
| 0 | B1 | -0.0340 | 0.0340 | n/a | 0.319 |
| 0 | B2 | -0.0308 | 0.0308 | n/a | 0.289 |
| 0 | B3 | -0.0330 | 0.0330 | n/a | 0.310 |
| +0.1 | A | -0.0203 | 0.1203 | 0.00 | 0.169 |
| +0.1 | B1 | -0.0249 | 0.1249 | 0.00 | 0.208 |
| +0.1 | B2 | -0.0221 | 0.1221 | 0.00 | 0.184 |
| +0.1 | B3 | -0.0242 | 0.1242 | 0.00 | 0.203 |
| -0.1 | A | -0.0387 | 0.0613 | 1.00 | 0.325 |
| -0.1 | B1 | -0.0428 | 0.0572 | 1.00 | 0.359 |
| -0.1 | B2 | -0.0393 | 0.0607 | 1.00 | 0.330 |
| -0.1 | B3 | -0.0416 | 0.0584 | 1.00 | 0.350 |
| +0.2 | A | -0.0110 | 0.2110 | 0.00 | 0.091 |
| +0.2 | B1 | -0.0160 | 0.2160 | 0.00 | 0.132 |
| +0.2 | B2 | -0.0136 | 0.2136 | 0.00 | 0.112 |
| +0.2 | B3 | -0.0155 | 0.2155 | 0.00 | 0.129 |

Relative to A, all three replay seeds shift mean vx in the negative direction for every complete command:

- zero: B1/B2/B3 `-0.00435/-0.00113/-0.00337 m/s`
- +0.1: `-0.00462/-0.00181/-0.00390 m/s`
- -0.1: `-0.00412/-0.00059/-0.00289 m/s`
- +0.2: `-0.00495/-0.00255/-0.00451 m/s`

The signs are consistent across all seeds. The negative-command direction fraction remains 1.0, while positive-command direction remains 0.0 for both A and B. This supports a small common negative velocity bias after one update, with seed-dependent magnitude; it does not show command-response reversal. The positive commands were already moving backward under A, so the update worsened that existing bias rather than flipping a correct response. The zero-command drift and error also worsen for all three seeds.

These results are a repeatable single-update physical effect under this protocol, but they do not prove the historical update50→100 degradation mechanism. The incomplete `-0.2` group prevents a full five-command conclusion, and the 8.8 s cleanup overrun is recorded rather than hidden.

The next useful experiment is a fresh, separately authorized multi-batch fixed-command comparison that preserves the same four-model identity but samples several independent reset/rollout batches before one update. It can test whether the common negative shift survives batch variation; continuing long training would not distinguish that from a one-batch optimization artifact.
