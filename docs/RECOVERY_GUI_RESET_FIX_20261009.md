# Recovery GUI单环境reset修复

用户报告环境setup后立即关闭。源码核查发现tools.play创建1env，RecoveryEnv默认curriculum_training=True，训练spec固定family26/25/13，在显式reset调用fixed_reset_choices时总数64!=1，抛ValueError。其后finally关闭Kit，fast shutdown可能遮蔽Python延迟traceback。用户日志尚未包含实际异常，因此该代码缺陷已确认，但不声称排除所有GUI/renderer问题。

修复tools.play的configure_recovery_preview：创建RecoveryEnv后、显式reset前curriculum_training=False，按spec.preview_family选择holdout；不改训练spec或reset采样实现。异常先stderr flush完整traceback再清理，使后续故障可见。没有增加控制/限矩/RNG干预。

新增tests/test_recovery_gui_preview.py（PORTABLE）覆盖1env预览绕过64slot、选定family、原spec配额不变；与Motion preview回归合计6passed。用户原spec/checkpoint CPU --preview --strict-identities计划通过；本轮未启动GUI/Isaac/PPO，实际视觉效果待用户重新执行同命令核验。

改动：src/native_stand/command_v6/tools/play.py、tests/test_recovery_gui_preview.py、TOOL_INDEX.md、本报告与STATUS。旧run/checkpoint/spec/ledger保持只读，无文件清理/commit。
