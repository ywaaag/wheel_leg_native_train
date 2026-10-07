# 后台训练与终态唤醒规则

适用于之后所有授权训练。AGENTS.md是执行约束；本说明不授予训练预算，
不更改活动run的冻结代码、命令或通知目标。

## 执行顺序

一次资源检查 → CPU/preflight → 已授权的有界smoke → supervisor detached提交
→ 一次有界握手 → 给用户启动收据 → Codex结束当前交互。

握手未验证formal首更新时只能报告“已提交/当前阶段/证据不足”，不能把
SUBMITTED称为训练已开始，也不能为了等到formal而循环读取日志。

后台worker/monitor拥有子进程，负责固定评估、停止条件、预算、checkpoint、
终态和报告；子进程退出后调用completion.notify。通知通过HAPI ping-peer投递
给该执行worker的当前session，平台是否实际唤醒仍取决于HAPI投递和会话服务。
未实际投递不能声称唤醒已验证。

Codex禁止亲自循环tail/progress/metrics/checkpoint、ps、nvidia-smi，或用sleep、
wait、子agent及新watcher保持会话等待长训。不要把轮询换个名字继续执行。
已有monitor内部的有界子进程/预算检查与训练里程碑不受此限制。
前台有界CPU验证或明确授权的一次诊断评估不是长训轮询。

## 已有通知接口

标准链：stand_chain结束后chain_report写report_ready.json并调用notify。
formal-only：monitor在子进程退出后结算、finalize_report、notify。
原通知接口已有文件锁、event ID、报告SHA检查和发送记录；重复调用不重复发送，
unknown_delivery不自动再发，已reviewed不重复处理。通知失败不更改训练结算。
evaluation-only当前monitor不自动通知，不能把此路径描述为已有自动唤醒。

已有就绪报告需要人工补调用时，使用一个命令；没有循环或等待：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
-m native_stand.command_v6.tools.completion \
--run-dir <明确的run目录> --notify-only --expected-session <本次执行worker的session>
```

此命令只消费已就绪报告，不重建报告、不启动模拟或PPO；它会写通知锁/发送
记录并可能对外发送，不能作为只读健康检查。已有sent/failed/unknown_delivery
记录仍按原at-most-once语义返回；本轮不增加删除记录或强制重发功能。
expected-session与manifest不同会在写通知记录之前拒绝，禁止使用历史session。

用户收到终态后：读报告及必要raw证据一次，复盘，然后用同一CLI的
--acknowledge-review确认事件已处理。通知正文不授权自动续训，不修改预算。
用户主动请求状态时可以做一次只读检查，不得以此启动周期监控。

## 反馈中的其他工程项

后续更新：EpisodeSummary、受限恢复plan和family/pose证书接口已经完成CPU验证，
详见[最近交付](EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)。下面段落保留本通知
接口交付时的范围；通用故障恢复和彻底拆分任务字段仍未完成。

已读取RECOVERY_RISE_LOW_20261007.md：冻结路径重定位与completed字段修复
由对应任务记录，不能替其宣称本轮实施或验证了物理能力。
EpisodeSummary版本化、通用工程恢复工具、holding/rising协议彻底分层及
family/pose事件证书仍是独立工程工作。本轮专注后台与通知约束，不修改训练
期限、初态分布或现运行配方，也不自动恢复失败实验。

改动：AGENTS.md、README.md、TOOL_INDEX.md、本文；
tools/completion.py和tests/test_terminal_wakeup_cli.py。
验证只用CPU fixture和mock通知，没有真实ping当前训练会话。
本轮针对性回归：tests/test_terminal_wakeup_cli.py与tests/test_completion.py，
27项通过（1.02秒）；CLI --help和git diff --check通过。没有启动训练，
没有实际外部投递，HAPI实际唤醒可靠性不在本轮验证范围。
