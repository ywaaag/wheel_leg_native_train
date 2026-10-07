# Native closed-chain training

Current engineering entry: [入口、资源与episode语义修复](docs/ENTRY_SEMANTICS_FIX_20261007.md)。
exclusive/shared、source/best_new/best_overall、提交阶段和formal首更新分别记录。
工程代码更新不授权运行；现有训练冻结快照与历史证据保持不变。

Motion工程复核入口（2026-10-07）：[新协议、模型身份和PPO0复核](docs/MOTION_ENGINEERING_RECHECK_20261007.md)。
独立motion授权不改变Recovery；当前物理终态以该新run/ledger为准。

Recovery R0 holding experiment: [冻结配方](docs/RECOVERY_R0_HOLD10_20261007.md)与
[已完成复盘](docs/RECOVERY_R0_HOLD10_REVIEW_20261007.md)。历史授权已执行，
不代表当前续训许可；source50和历史结果保持不变，运行状态以run终态为准。

Engineering entry (2026-10-07): [interface/evidence changes](docs/NATIVE_INTERFACE_EVIDENCE_20261007.md).
Followup: [verified gap closure](docs/NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md).
Read-only health/preflight and offline correction tools are available; this change
does not authorize simulation or continuation. Historical launch text below must
be resolved against immutable terminal evidence and STATUS.

**Current entry:** [STATUS.md](STATUS.md). Current engineering validation and
remaining runtime limits are recorded in the followup above. Git versioning
rules and commit scope are in [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md).
Versioned specs do not carry active training permission; local ledger and fresh
explicit authorization still govern any runtime action.

The following task descriptions are dated history. The
[survival/level R0 -> R1](docs/RECOVERY_SURVIVAL_LEVEL_20261006.md) chain started
from GUI-approved scissor update50 and subsequently stopped within its bound;
actual terminal evidence overrides its earlier startup description.

Historical task:
autonomous R0 standing from native Recovery update1500; its implementation,
thresholds and handoff are in [RECOVERY_STANDING_PLAN.md](docs/RECOVERY_STANDING_PLAN.md).
Completed controlled probe: [wheel-center alignment](docs/STANDING_SCISSOR_EXPERIMENT_20261006.md),
3smoke+50formal; offset reduced but drift/roll degraded,0/8 acceptance.
No continuation launched. Action/physical contract unchanged.
The height-independent2000-update continuation stopped at498updates; the
yaw-only test improved yaw but achieved0/8 full acceptance. Current task is
[BC gradient / annealing A/B](docs/STANDING_BC_AB_20261006.md) completed206transferred
updates: less yaw with annealing, more drift,0/8 acceptance. See STATUS/review.
No automatic follow-up.

The separate frozen STAND model is scratch update500 (8/8 independent10s
standing acceptance), not B200 or Gym47250. It is not the current training
source or the source-retention teacher. Later bottom-down Recovery/handover
work must independently verify the low-pose initialization and5s STAND
takeover; R0 near-standing success does not certify that task.

## Historical project setup

The paragraphs below describe earlier setup/authorization. Resolve current
model, task and permissions from STATUS and the corresponding immutable run evidence.

Current authorized standing chain uses
[stand_long_20261001/spec.json](configs/experiments/stand_long_20261001/spec.json).
Follow [STATUS](STATUS.md) to its independent ledger and real run. Shared code
handles adaptive6/10/20/30s episodes; no command_v7 code tree was copied.
The remaining preparation descriptions refer to the original project setup.

This is the **one current native closed-chain training project**. It uses the
colleague's immutable closed-loop USD and a physical `Plane` ground collider.
The current task is zero-command standing at `[vx, yaw, height] =
[0, 0, 0.363]`. The source is native B200, expanded from 22D/110D/132D to
25D/125D/150D without replacing its learned actor or critic weights. This is
not the Gym 47250 virtual-leg migration and not a resumption of `command_v6`
formal training.

Read [AGENTS.md](AGENTS.md), [STATUS.md](STATUS.md),
[ARCHITECTURE.md](ARCHITECTURE.md), the
[current spec](configs/experiments/stand_plane.json), then
[TOOL_INDEX.md](TOOL_INDEX.md). [Reuse decisions](docs/REUSE_DECISIONS.md)
identify what comes from the colleague project; [experiment plan](docs/EXPERIMENT_PLAN.md)
separates source regression, the new plane/height standing recipe, and later
motion stages. The [source B200 recipe](configs/contracts/source_B200.json)
keeps the old mesh/0.35 m identity separate from the new experiment. The only writable current budget is
[budget.json](configs/experiments/budget.json), presently unapproved.
[Changed files and provenance](docs/CHANGED_FILES.md) identify the carried
kernel and every new project file.

Before designing or changing rewards, curricula, training experiments,
candidate selection, or acceptance, read [TRAINING_EXPERIENCE_REUSE.md](TRAINING_EXPERIENCE_REUSE.md).
Actual runs are governed by their spec, manifest, and raw evaluations.

Code is under `src/native_stand/`: the small source physical environment,
the audited v6 pure domain/ledger/trainer kernel, and an explicit plane scene.
The retained `command_v6` package name identifies the reused kernel, not a
new `command_v7` experiment. A new experiment changes a spec, not another
copy of the Python tree. Run artifacts go only under `runs/`; none have been
created by this preparation.

The [historical audit](/home/kellen/wheel_leg_migration_audit/) still contains
v1-v6 runs, the separate Gym-to-Lab migration, and 47250 sim2sim evidence.
Their old Markdown pages are historical snapshots; do not treat their budgets
or model labels as this project's current state.
