# 姿态smoke轻评估窗口故障复盘

事件`3bb21a4b40e4f8cbdeeca999`。run `runs/2026_10_8-22_51__motion_b250_posture_storage_retry`。通知只授权复盘，本轮不改代码、不重试、不启动仿真/PPO。

## 实际结果

链FAILED。source_eval COMPLETED，0、±.5、±1、±1.5、±2全部8/8，每环境连续30秒，九份raw的posture_geometry窗口均完整。来源阶段1865.370803秒。smoke已执行1次真实PPO更新、8192 samples，随后milestone_evaluation异常，68.230369秒。formal未启动，接受候选为空。

新checkpoint仅用于诊断：`smoke/model_update_1.pt`，SHA256 `51444ce99f439f046157ba0313d0715731680c9c6f6286dfb195109a7a8727c0`。没有完整独立候选评估，不能称姿态改善或已通过，也不作为正式续训来源。

两个exact attempt已结算：来源`116ee8e25195492f9d35fbc559ad897b` COMPLETED/0更新；smoke `512262ff7a404f54a7babf67f36e59e4` FAILED/1更新，无未结算attempt。链1939.752001秒，结合旧两链3806.672207秒，累计5746.424208秒（95.77分钟），原10800秒剩5053.575792秒（84.23分钟）。累计smoke1已用完，formal50尚未用；余额不授权新运行，不可自动追加smoke。

## 已确认实现错误

冻结train.py 738–745调用evaluate_actor：轻评估`standing_protocol=None`、`target_window=light_window_s`。冻结evaluate_checkpoint.py 70–76生成有效协议，此时motion_window_s为None。第175行对非零target直接选择motion_window_s，第176行下标访问window[0]，触发`TypeError: 'NoneType' object is not subscriptable`。

确定缺口是“可选轻评估motion窗口”与“姿态统计要求窗口”接线不一致。完整来源评估成功，不意味着轻评估路径正确。应在协议解析阶段显式提供轻评估姿态窗口，或在缺窗口时报告不可用；不能将短窗口升级为完整保持证据，不能将缺失几何数据记作零值。

## 存储与证据

本次没有ENOSPC。chain_terminal_report约3.25MiB、source analysis约3.24MiB、smoke analysis约3.32MiB，摘要去掉完整轨迹已生效，但候选/逐环境摘要仍可能重复；不把这次异常归因于磁盘。

证据：completion_report.md、chain_terminal_report.json、source_eval原始evaluation_source*.json、smoke/terminal_report.json、smoke/progress.json、冻结source_snapshot、配置budget.json。旧记录保持原样。

## 唯一优先下一步

先修轻评估姿态窗口并补CPU回归：零/非零target、无motion窗口、短窗口与完整窗口、早终止均应覆盖；证明不误授完整通过。随后核验本次完整source与保存smoke能否形成合法工程恢复证据，不再默认重新做30分钟来源采集。formal仍从B250恢复，而非smoke模型。新尝试须用户明确授权、累计墙钟扣除、smoke额度不重置；当前不启动或准备绕过证书的formal-only。
