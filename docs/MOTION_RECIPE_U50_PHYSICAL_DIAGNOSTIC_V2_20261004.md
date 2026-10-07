# U50 single-update physical A/B diagnostic v2

## Outcome

The new exact attempt was `u50evalb20261004`, using the fresh spec and ledger in `configs/experiments/motion_recipe_u50_eval_20261004b/` and output `runs/motion_recipe_u50_eval_20261004b/`. GPU1 was selected with `CUDA_VISIBLE_DEVICES=1`; GPU0 and Recovery were not modified.

CPU preparation passed: the existing 37-test regression suite passed, the actual evaluator entry resolved `agent_world` from the configured asset root before importing `CommandEnv`, and plan-only reported the four model identities, five targets, 64 environments, 8 scored environments and zero online PPO updates. L1 effective reward resolution was checked in the entry preparation: linear denominator `.04`, yaw denominator `.09`, fixed command mode, zero-command 10 s, nonzero 9 s, windows `[2,10]` and `[2,6]`.

The child reached Isaac initialization but produced an Omniverse/Kit crash dump. GPU1 never showed an evaluation compute process and no model-command result was written. The supervisor was stopped after the runtime fault; a one-time settlement verified that no evaluator child remained, wrote a terminal report, and charged the exact attempt once. Final status is `STOPPED_BOUNDED`, wall time `340.282 s`, online PPO `0`, completed physical evaluations `0`, missing evaluations `20`.

## Evidence retained

The four model SHA identities were verified before submission:

- A update50: `af990e413b636b218b4fe35eae2a8a0b32c2c985975b0707dc8d9cbda6b3e4a8`
- B1 seed81023: `412610ab22781885096f4cf1a6639b951aa514c0aa131f31682f945b06a9d0ff`
- B2 seed81024: `260bfd243be892d0f3c2db3fcef11a30690b2512eada3bd7004956911dc381ab`
- B3 seed81025: `984a016588d36aa44679a1c82efec04c0936d57c10d3f6faa5988d98109258ac`

All actor tensors had the expected 150D input network shapes and finite values. B1/B2/B3 each carry `diagnostic_only=true`, source A SHA, and replay seeds 81023/81024/81025.

The terminal and ledger agree on the exact attempt. There are no physical metrics to compare and no candidate model was registered. The prior failed attempt remains unchanged.

## Answers

1. The asset import ordering fix was verified by the actual evaluator's CPU path and the new process command. The previous `agent_world` import error did not recur. Terminal ordering is protected in the child source, but this run crashed during Isaac startup before the child could commit its terminal; the supervisor settlement preserved the final terminal and charged once. Thus the evidence path is settled correctly, while successful child terminal delivery after a normal physical run remains unverified.

2. A single frozen-batch PPO update cannot be judged physically in this run. No A/B model-command evaluation completed, so there is no evidence for or against repeatable loss of standing or forward/backward motion.

3. Common action offset, command-response reversal and seed sensitivity cannot be separated physically. The prior offline evidence remains only optimization evidence: the `+0.2 m/s` group dominated sample-weighted surrogate improvement, but that does not substitute for physics.

The next informative experiment remains a fresh, separately authorized physical attempt after the Isaac GPU1 startup fault is diagnosed (driver/Kit/runtime initialization), using the same four frozen models and no PPO updates. Reusing this stopped attempt or its balance would violate the exact-attempt boundary; no retry was submitted.
