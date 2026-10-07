# Git 版本控制与工程交接

记录日期：2026-10-07。工程目录：`/home/kellen/wheel_leg_native_train`。

## 首次版本基线

开始本次提交前，`main` 分支没有任何 commit，所有源码和文档均为 untracked。
因此本次首个代码提交保存的是当前现场实现，不代表恢复了某次旧 run 的源码，
也不能凭提交时间推断各算法、配方或修复的历史实现时间。

按职责拆分为三次本地提交：

1. 当前训练内核、接口工程、CPU 测试、声明式配置和 Git 排除规则。
2. 现有准备、诊断、离线审计与共享提交脚本。
3. AGENTS、README、STATUS、ARCHITECTURE、TOOL_INDEX 和相关中文交接文档。

每次提交使用详细中文标题及正文，解释范围、验证和限制。没有执行 push，
没有增加 simulator/PPO 预算，也没有运行旧脚本。

## 纳入版本控制

- `src/`：当前项目唯一 Python 实现，包括 native 运行时、Recovery、协议、gate、
  health、preflight、共享 supervisor/certificate 和默认关闭的选定更新诊断。
- `tests/` 与源码下的 tests：CPU fixture 和回归，包含协议冲突、时长、RNG、
  optimizer 诊断不改变更新、账本及提交保护。
- `scripts/`：准备和诊断工具；保留历史专用脚本以供审计，新公共提交使用 supervisor。
- `configs/`：spec、contract、pose library 和工具配置等声明内容。
- 入口 Markdown、`docs/`、`pyproject.toml` 与 `.gitignore`。

旧 spec 中保存的路径、SHA、seed、HAPI session 和授权字段仅描述历史实验。
它们不会被改写，也不证明当前会话有权继续训练。公共 supervisor 仍需校验
当前 `HAPI_SESSION_ID`、明确物理 GPU、active-phase health、来源和独立 ledger。

## 保持本地的数据

以下内容被 `.gitignore` 排除并原地保留，不删除、不移动、不覆盖：

- `runs/`：checkpoint、原始 evaluation、log、manifest、progress、terminal 和报告。
- `isolated/`：独立审计数据、大型 JSON、隔离实现及工程验证产物。
- `assets/` 与模型二进制：本地冻结 USD、checkpoint、ONNX、数组数据。
- 配置目录中的 `budget*.json`、`ledger*.json`、提交记录、运行候选 review、
  `source_snapshot/` 和 `execution_snapshot/`。
- 缓存、锁、日志、编辑器状态和本地凭据。

排除的是运行数据，不是证据要求。每次运行仍须保存并核对 source/asset/spec/code
身份、exact attempt 和累计预算。不得使用 `git add -f` 绕过边界提交旧账本或资产。

代码 checkout 不能用于回滚预算、账本、运行状态或 checkpoint。Git 不替代本地
数据备份；备份、迁移和存储清理由独立任务处理。

## 提交流程

先读取最近的 AGENTS，检查 `git status` 与 index。按明确路径 stage，
不要使用 `git add .` 将历史数据或无关用户改动混入提交。

```bash
git status --short
git diff --cached --stat
git diff --cached --check
git diff --cached --name-only
```

提交前确认 index 没有 runs、checkpoint、USD、ledger、submission 或旧源码副本。
审查大文件和凭据；凭据检查只报告路径，不输出疑似秘密值。
有同事或用户的 staged changes 时，不清空或撤回它们，先识别所有权并缩小范围。

使用 `git commit -F <正文文件>` 传递完整中文说明，避免 shell 对多行、反引号、
`$()` 的错误解释。完成后检查 `git log`、提交文件和剩余状态。用户请求 commit
不等于请求 push、发布或训练启动。

## 验证与证据

本轮接口工程的全量 CPU 基线：**315 passed**；静态 `py_compile`：75 个文件通过。
正式提交前会再次执行 CPU 回归和 staged diff 检查。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

已有工程交付记录：

- [首次接口交付](NATIVE_INTERFACE_EVIDENCE_20261007.md)。
- [缺口补齐与精确文件清单](NATIVE_INTERFACE_EVIDENCE_FOLLOWUP_20261007.md)。
- 本地 `isolated/interface_evidence_followup_20261007/verification.json`。
- 本地 `isolated/interface_evidence_followup_20261007/change_manifest.json`。

验证产物不加入 Git；源文件之后修改会使旧 change_manifest 的代码 SHA 过时，
它仍是对应工程检查时刻的历史记录，不能自动覆盖更新。本次 commit 的代码身份
以 Git tree 为准；运行身份仍以当次冻结 snapshot/manifest 为准。

CPU fixture 依赖本机的冻结来源、配置和历史账本。全新 checkout 需要另行提供
身份一致的本地依赖，不能默认在任意机器上复现全部物理或历史检查。

## 明确未做

没有启动 Isaac、AppLauncher、在线 PPO 或续训；没有修改 USD、reward、课程目标、
LR、std、网络、advantage normalization、PD、动作尺度或限矩；没有重置账本。
真实 GPU 诊断、detached handshake 和通知投递仍需独立授权验证。
源码提交与 CPU 通过均不代表机器人高速能力或 Recovery 能力改善。
