# Reuse decisions

Checked 2026-10-01. Source projects are read-only. "Reuse" below means a
specific physical/configuration element or engineering pattern, not another
team's policy or reward table.

| Source and location | Useful part | Decision / side effect |
| --- | --- | --- |
| Colleague `wheeled-legged_RL/source/agent_world/agent_world/assets/rmuc_wheel_leg.py`, `configs/rmuc_wheel_leg.yaml` | Immutable closed-loop USD path, articulation root/solver setup, active leg/wheel and passive/guide actuator groups. | Import the SHA-pinned `RMUC_WHEEL_LEG_CFG` at the CLI boundary, copy it per environment, zero only active gains for one explicit effort path, and read back all active bindings/limits. The module reads YAML at import; preflight hashes both before Isaac. Do not mutate the shared cfg or import the colleague task env. |
| Colleague closed-loop USD `.../assets/usd_files/rmuc_wheel_leg/rmuc_robot_closed_loop.usd` | Closed-loop constraints, bodies, collision assets and inertia. | Use the immutable SHA-pinned source. `native_stand/env.py` resolves six motor joints by name and four closure endpoints; no USD edit or Jacobian lookup. Authored properties are distinct from runtime effective values. |
| Colleague `source/agent_tasks/agent_tasks/direct/rmuc_wheel_leg/env.py` | Scene cloning, body-name contact binding, passive/guide separation, closure-consistent reset ideas. | Reuse only these physical-interface principles. Do **not** inherit right-first action order, wheel-effort action, its 8 ms policy, radial spring, extra feedback, motor-response compensation, reward, curriculum or PPO. |
| Local [ground A/B report](/home/kellen/wheel_leg_migration_audit/sim2sim_47250_bridge_20261001/GROUND_AB_REPORT_20261001.md) and `ground_env.py` | On fixed 0.5/0.5 friction, zero restitution, the USD Plane reduced left-wheel separation and force spikes relative to the mesh. | Implement only the physical Plane and explicit material in this project; verify composed binding at runtime. This was 47250 diagnostic evidence, **not** native-training acceptance. PhysX contact/rest offsets remain UNKNOWN until readback. |
| Local `native_stand/command_v6/domain`, `ledger.py`, `train.py`, `tools/preflight.py` | 25D/125D native contract, B200 warmstart by named columns, exact attempt ledger, GPU rollout aggregation, independent terminal snapshot. | Carry one audited kernel into this long-term project. Old v6 runs and their consumed ledger stay at the audit path; the new project has one code tree and new spec/budget. Remove unreachable benchmark phase. |
| Local `native_stand/contract.py`, `env.py` | Physical-joint targets/PD, named joints, reset/closure/body motion. | Carry only these needed source modules and change ground to Plane as an explicit new physics experiment. `native_stand/train.py`/`probe.py` are **not** runtime imports. |
| Fudan Gym `ARCHITECTURE.md`, `CODEX_WORKFLOW.md`, `TRAINING_METHODOLOGY.md` | Clear layer ownership, true command/observation/reward/PPO wiring checks, retained baseline tasks, independent candidate selection. | Reuse process and tests. Do not import its tree asset, virtual joint map, 47.294118 Nm wheel limit or actor weights into the native physical-joint policy. |
| Third-party `/home/kellen/wheeled-legged_RL/README.md`, `scripts/rsl_rl/play.py`, `source/agent_tasks/agent_tasks/direct/wheelbipe/wheelbipe_V14/env_cfg.py`, `.../agents/rsl_rl_ppo_cfg.py` | Separate task config/runner config, a play CLI with keyboard and bounded steps, per-run velocity/reward traces and explicit multiple RL recipes. | Reference architecture and operator UX only. Its Wheelbipe V14 topology, older documented Isaac Lab version, domain randomization, action/reward definitions and PPO numbers are not this RMUC closed-chain contract. Existing dirty files remain untouched. No code was copied from it. |

The V14 action implementation in `wheelbipe25_v3/env.py:_apply_action`
sets leg position targets, but its wheel branch is **conditional**: configured
velocity control uses velocity targets, otherwise the default branch uses
effort targets. It does not prove our RMUC wheel control without our own
readback. Its `_apply_spring` models forces on V14 prismatic spring joints;
the current RMUC native environment has passive-link damping and no copied
V14 spring force. Adding one would change the frozen physical experiment and
requires mechanism/force-curve evidence and a new spec. V14's 35D/78D saved
run and delay/randomization settings remain references, not our 25D/125D
interface or a reason to inject new delay now.

The current project therefore owns the observation, six-channel physical
action, reward, standing recipe and independent gate. The colleague provides
the closed-loop asset and validated physical organization; the third-party
project and Fudan provide design experience.
