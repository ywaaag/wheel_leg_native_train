# wide_leg_from2000_20261002

Status: **BLOCKED_BEFORE_D1/PPO** (2026-10-02 Asia/Shanghai)

Source is update 2000 with SHA `d0091d369b45b1bd758ce93e129416775ebcb92c0a3d7e6de51e9729735a29a6`.
The new contract is `leg_scale=0.5 rad`, pair projection disabled, with the legacy
wheel scale retained by the selected spec. CPU tests: 23 passed.

D0 was attempted twice. The first used an incorrect wheel-scale comparison and is
kept as `runs/wide_leg_from2000_20261002_d0.json`. The corrected historical-source
D0 is `runs/wide_leg_from2000_20261002_d0_source.json`; it failed 8/8 tilt within
0.26 s. This conflicts with the saved historical update-2000 10-second evaluation,
so current runtime equivalence is not established.

No D1, PPO smoke, or formal training was started. Do not resume until the saved
formal source snapshot and current runtime are compared and the D0 regression passes.
See `DIAGNOSTIC_REPORT.md`.
