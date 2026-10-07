# wide_leg_from2000_20261002 D0/D1 diagnostic status

Date: 2026-10-02 (Asia/Shanghai)

## Source identity

- Checkpoint: `runs/height40_from500_20261002_night/formal/model_update_2000.pt`
- SHA256: `d0091d369b45b1bd758ce93e129416775ebcb92c0a3d7e6de51e9729735a29a6`
- Checkpoint update: 2000
- Asset SHA256: `6bf6ce7f64f8d46cdc759bdf48dba0def85f6e9e6915acca27c543dbcf031a27`

## CPU work

23 domain/preflight/ledger tests passed. The action contract now supports the explicit
wide-leg case (`leg_scale_rad=0.5`, `leg_pair_radius_rad=0.0`) while preserving the
legacy (`0.1`, `0.12`) case. No PPO update was executed.

## D0 attempts

The first attempt used `0.1/0.12` but `wheel_scale=6`, which is not the historical
formal snapshot. It is retained as `runs/wide_leg_from2000_20261002_d0.json` and is
not treated as a valid D0 regression: 8/8 tilt at 0.64 s.

The corrected attempt used the historical source snapshot action values:
`leg_scale=0.1`, `pair_projection=0.12`, `wheel_scale=100`, height command `0.40`,
64 environments and the fixed seed. It is retained as
`runs/wide_leg_from2000_20261002_d0_source.json`.

Result: 8/8 task failures by `tilt`; first failure was approximately 0.26 s.
There was no nonfinite, closure or mapping runtime fault in the report, but the
observed behavior does not reproduce the existing historical update-2000 evaluation:
`runs/height40_from500_20261002_night/formal/evaluation_2000_0_0.json`.

## Decision

D0 source regression has not passed. D1 wide-contract behavior and PPO smoke/formal
training are blocked until the runtime snapshot/configuration used by evaluation is
made behaviorally identical to the source run. This prevents training on an
unverified control path.

The likely issue is implementation/config drift between the saved source snapshot and
current `command_v6` runtime, not evidence that the 0.5 rad contract itself is bad.
The exact first differing control/reset/observation field is still UNKNOWN. Compare
`formal/source_snapshot/native_env.py`, `domain_contract.py`, `runtime/env.py`, and
`runtime/configure.py` before any new physics run.
