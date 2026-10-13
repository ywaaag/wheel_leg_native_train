# Motion 姿态轻评估窗口修复

用户同意先修接口、CPU验证及核验工程恢复证据。本轮未仿真、PPO、通知、续训、reserve或改历史文件。

## 修复范围

- `src/native_stand/command_v6/domain/posture_geometry.py`：新增纯函数diagnostic_window，非零命令有motion_window_s时选该窗口，否则选协议明确声明的steady_window_s。返回scope、是否声明运动窗口及具名时间轴。
- `src/native_stand/command_v6/tools/evaluate_checkpoint.py`：姿态统计调用共享解析；完整性使用closed post-step时间轴要求样本数及valid mask，不再用round(时长/dt)少算端点。短窗口仅证明短窗口完整，不替代完整运动gate。
- `tests/test_posture_geometry.py`：覆盖zero/positive/negative轻评估、显式完整运动窗口、早终止与实际runtime调用接线。

未修改reward、课程、网络、PPO、动作或物理参数。旧冻结evaluator保持不变。

## CPU验证

`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q`：662 passed，26.57秒。专项15 passed。三个本轮文件py_compile及diff检查通过。证据在`artifacts/motion_posture_light_window_fix_20261009/cpu_tests.txt`。

## 恢复资格核验

原run `2026_10_8-22_51__motion_b250_posture_storage_retry`的source九命令完整；当前source_evidence仅因执行源码SHA变化返回CONFLICTING，不是缺轨迹。

smoke_certificate为FAILED：actor update unproven、smoke terminal failure、no recorded smoke evaluation。progress中的actor_parameters_changed为None。虽有evaluation_1_0_0.json文件，但终态未登记完整smoke评估集；不能以文件存在猜测证书通过。离线比较原B250与smoke actor最大参数变化0.000236175954，证明权重确有变化，但不自动补齐运行证书。

完整核验与SHA证据分别在recovery_evidence_check.json、actor_delta.json。旧ledger/terminal/certificate不更正、不覆盖。累计5746.424208秒、smoke1已用完、formal0，剩5053.575792秒/最多50 formal更新；余额不产生新运行授权。

## 下一步

不能直接formal-only，也不能重新做smoke PPO。合法下一步是独立PPO0工程验证：对已保存smoke checkpoint补齐修复后评估路径，同时建立明确的源码变更审核与更正证据引用，保留原FAILED终态。来源复用仍须通过严格身份接口，不能用CPU测试替代证书。PPO0仿真需要明确授权及新的独立评估账本，耗时计入剩余84.23分钟；formal仍从B250恢复。当前没有准备或提交该物理验证。
