# GUI 模式、模型分布与证据接口修复（2026-10-09）

本轮CPU工程修复，不启动GUI/Isaac/采样/PPO，不读后台训练进度，不修改活动冻结代码、历史run/账本或checkpoint。

## 已修复

1. 公共environment_mode明确training/evaluation/preview；configure在构造前设置，Recovery初始化采用对应split/training，play使用1env holdout而非训练64slot，evaluator切换后恢复。spec采样配方未改变。
2. Motion与Recovery所有GUI路径共用gui_device；显式physical-gpu覆盖或读取spec设备，CUDA_VISIBLE_DEVICES冲突拒绝；device=cuda:0、multi_gpu=false、renderer物理GPU明确。
3. preview_plan严格加载actor并恢复CPU RNG，绑定checkpoint/spec/资产/姿态库、family、分布版本/class/实现SHA、保存std与单env合法holdout，生成CPU/GUI命令。不存在的family在CPU拒绝，不凭名字猜。
4. runtime_cleanup尝试全部清理步骤，原异常保留，cleanup异常附note并即时stderr打印；先持久化主错误再Kit.close。真实Kit行为未知，不能称GUI已验证。
5. Recovery bounded-mean迁到recovery.learning/learning_distribution；tools.model_factory统一task-aware构造，保持state_dict/Adam参数名称和概率语义；Motion learning及learning_distribution与原Motion冻结源码字节完全一致。共享调用方SHA仍真实变化，不自动豁免旧证书。
6. 补齐bounded-mean、腿执行和相关audit工具注册；audit_entrypoints自动对照TOOL_INDEX，新增强制CPU测试。当前目录覆盖PASS。
7. 可选数值存储evaluation_numeric_npz_v1接入train、单项/批量evaluator；新JSON只保留summary及具名数组引用/SHA，NPZ压缩数值轨迹、exclusive原子发布。evaluation_loader验证并还原；公共terminal/events审计复用，不新建平行报告系统。
8. candidate_registry统一递归去轨迹，补齐原手写删字段漏掉的几何/控制数组，raw内容不变。历史JSON不自动迁移。

## 验证与未通过项

- 专项85 passed / 7.44秒（最终日志为准），包含真实安装PPO fixture、strict state/Adam/JIT、模式/reset/异常恢复、NPZ roundtrip/None/SHA/path escape、registry compact、目录同步。JIT出现2条已安装PyTorch弃用warning。
- 全量：680 passed, 2 warnings, 22 errors in 29.14s。22个错误均来自历史Motion恢复测试fixture要求当前critical runtime/configure与原SHA完全相同；本轮公共模式修复已改变此文件，严格拒绝是预期的身份边界。没有删除/跳过测试、放宽断言或修改旧fixture/证书来制造全绿。
- 修复了此次首次全量发现的play直接脚本执行relative import错误，后续实际脚本CPU plan回归通过。
- 真实共享play入口两案：Recovery GPU0、Motion GPU1 CPU计划均PASS；audit hook拒绝任何Isaac/omni/pxr导入，实际未触发。spec/checkpoint/相关ledger前后SHA一致，simulation/files_written/PPO_updates均0。
- 把展示名称Swing当实际family的一次CPU尝试被正确拒绝；改用姿态库真实family后通过，不改姿态库。
- 原2026_10_9-10_14恢复声明保持原证书/未授权账本。它只能说明当时工程READY；当前共享调用方变化需要新的逐文件审核，不可以自动提交。

## 存储与消费者边界

编码仅对新spec显式artifacts.evaluation_trace_encoding生效，默认历史行为不变；NPZ保留shape/dtype/axes/字段位置，缺失None往返仍None，SHA冲突拒绝。
公共evidence loader、audit_terminal、review_recovery_events已支持。仍有专用脚本直接json.loads，需迁移loader后才能消费压缩轨迹；因此本轮不默认全局开启，不删除原始JSON。
新存储真实仿真写入/GUI渲染/Kit fast exit均未执行；CPU工程证据不证明训练能力改善或完整执行量审计。

## CPU命令与产物

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q tests/test_preview_and_storage_contract.py tests/test_recovery_gui_preview.py tests/test_motion_keyboard_preview.py tests/test_recovery_bounded_mean_distribution.py tests/test_entrypoint_catalog.py tests/test_protocol_followup.py tests/test_evidence_interfaces.py tests/test_stand_plane_contract.py
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q tests
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python artifacts/gui_mode_distribution_storage_20261009/check_cpu_previews.py
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.audit_entrypoints
```

结果：artifacts/gui_mode_distribution_storage_20261009/result.json、两份plan、tests_targeted/full、entrypoint_audit与Motion共享模块SHA对照。准确公共用法只维护TOOL_INDEX，流程WORKFLOW，架构ARCHITECTURE，状态STATUS。

## 精确改动文件

- `src/native_stand/command_v6/domain/environment_mode.py`
- `src/native_stand/command_v6/runtime/execution_mode.py`
- `src/native_stand/command_v6/runtime/configure.py`
- `src/native_stand/command_v6/tools/runtime_cleanup.py`
- `src/native_stand/command_v6/tools/play.py`
- `src/native_stand/command_v6/tools/preview_plan.py`
- `src/native_stand/command_v6/tools/model_factory.py`
- `src/native_stand/recovery/learning.py`
- `src/native_stand/recovery/learning_distribution.py`
- `src/native_stand/command_v6/learning.py`
- `src/native_stand/command_v6/learning_distribution.py`
- `src/native_stand/recovery/recipe.py`
- `src/native_stand/recovery/runtime.py`
- `src/native_stand/recovery/probe.py`
- `src/native_stand/command_v6/tools/evaluation_state.py`
- `src/native_stand/command_v6/tools/evaluate_checkpoint.py`
- `src/native_stand/command_v6/tools/frozen_rollout_probe.py`
- `src/native_stand/command_v6/tools/checkpoint_initialization.py`
- `src/native_stand/command_v6/tools/prepare_motion_experiment.py`
- `src/native_stand/command_v6/train.py`
- `src/native_stand/command_v6/tools/evaluation_storage.py`
- `src/native_stand/command_v6/tools/evaluation_loader.py`
- `src/native_stand/command_v6/tools/audit_terminal.py`
- `src/native_stand/command_v6/tools/review_recovery_events.py`
- `src/native_stand/command_v6/config.py`
- `src/native_stand/command_v6/tools/entrypoints.py`
- `src/native_stand/command_v6/tools/audit_entrypoints.py`
- `scripts/review_recovery_bounded_mean_probe.py`
- `scripts/audit_recovery_mean_coefficient.py`
- `scripts/review_recovery_input_capture.py`
- `scripts/review_recovery_coverage.py`
- `tests/test_preview_and_storage_contract.py`
- `tests/test_recovery_gui_preview.py`
- `tests/test_recovery_bounded_mean_distribution.py`
- `tests/test_entrypoint_catalog.py`
- `README.md`
- `TOOL_INDEX.md`
- `WORKFLOW.md`
- `ARCHITECTURE.md`
- `STATUS.md`
