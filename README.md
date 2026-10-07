# Native closed-chain training

新 Codex 会话先读：[入口、用法与授权边界](docs/CODEX_START_HERE.md)。历史“当前”记录不代表实时进程状态。

当前工程总入口：[工程状态与剩余缺口](docs/ENGINEERING_STATUS.md)。
近期验证435项CPU通过；工程接口与历史训练事实分别记录，提交不授予运行权限。

最新证据工程：[冻结身份、episode schema与受限恢复](docs/EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)。
工程恢复只生成未授权新配置，不自动恢复训练；历史证据和活动快照保持不变。

训练执行遵守[后台与终态唤醒规则](docs/DETACHED_TRAINING_POLICY.md)：一次握手后
结束交互，后台owner结算并通知当前HAPI会话；Codex不得亲自轮询日志等待长训。

当前Recovery转入[低位自主起身](docs/RECOVERY_RISE_LOW_20261007.md)，
使用独立日期时间spec/ledger；coverage A/B已完成，保留source50。
起身后保持采用事件对齐窗口，不将近站立或2秒成功称为完整起身认证。
准确提交/首更新/终态见STATUS与新run证据，旧段落仅日期任务记录。

最新工程接口：[状态机、任务请求与历史工具保护](docs/STATE_REQUEST_FIX_20261007.md)。
共享链状态和formal首更新证据分开；Motion/Recovery请求不混用。
这些接口修复不授权新的仿真或训练，也不替换活动run的冻结副本。

已完成Recovery任务：[source50能力复核与BC覆盖对照](docs/RECOVERY_COVERAGE_AB_20261007.md)。
保留其独立账本和原始证据；旧hold10已结算，不代表续训许可。

公共入口只见[当前工具清单](TOOL_INDEX.md)；旧日期命令集中在
[历史工具清单](TOOL_INDEX_HISTORY.md)。新提交仅使用supervisor。
新实验使用[日期时间前缀命名](docs/EXPERIMENT_NAMING.md)，例如
`2026_10_7-14_27__motion_width_ab`；已有实验不重命名。
当前Motion推荐来源为B250，早期new250推荐已被后续物理复核替代；
Recovery hold10已结束，不授予续训权限。

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
