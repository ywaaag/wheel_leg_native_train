# Motion 历史 run 清理（2026-10-08）

用户明确授权删除不再使用的 Motion 实验记录，例外是当前任务及其来源传承链。本次没有仿真、PPO、续训或修改 Recovery。

删除50个退役 Motion run目录及对应零散日志，2860个文件，约4.025 GiB。此前两次中间记录清理释放约3.708 GiB。历史文档和配置仍保留，但指向已删除 run 的链接不再表示证据可用；不能据此重新核验原始轨迹或冒充完整证据。

保留B250来源链：`motion_cohort_width_ab_20261006` → `motion_forward_cohort_20261006` → `motion_retention_ab_20261006` → `motion_overnight_20261005_retry2` → `motion_recipe_per_command_norm_online_seed20261001_20261004_retry1` → 非Motion原始standing run。保留来源PPO0复核、相关reference、2026-10-07/08近期Motion短训、姿态故障和sim2sim记录。

B250删除前后SHA均为 `5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。一次进程快照未发现Motion trainer；没有停止进程。配置目录中的spec、授权及ledger未删除，非Motion目录未修改。

记录目录：`artifacts/2026_10_08-21_50_42__motion_retired_runs_cleanup/`。

- `plan.json`：逐文件路径/大小、保留目录、删除目录及来源链。
- `deleted_directories.jsonl`：实际删除事件。
- `retired_headers.json`：可保存的小型manifest、terminal、progress及预算原文与SHA；不替代已删除的原始评估。
- `result.json`：完成状态与实际数量。

删除是用户授权的存储清理，不代表历史实验通过或失败结论改变。没有可恢复的完整备份。
