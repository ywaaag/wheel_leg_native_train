# Recovery P1原始证据接线修复重试

终态更新：事件a3ad42500f31c87c5166606a，COMPLETED；smoke20/formal100、983040样本，完整接受0/8，自动best100。[量化复盘](RECOVERY_MIN_HEIGHT_P1_COMPLETED_REVIEW_20261008.md)。下面SOURCE_EVAL是历史握手；未自动追加训练。

用户在53acf4f6cdbc0c19ec7fd48c失败复盘后明确请求“继续”，并要求核对AGENTS中的工具说明。
已重读AGENTS、TOOL_INDEX、ENGINEERING_STATUS，核对entrypoints及engineering_recovery的实际CLI/白名单。
现有engineering_recovery仅支持completed_episode旧证书reader错误，本次控制轨迹消费者错误不适用；未扩大白名单、未调用execute或修改旧证书。
准备使用集中experiment_naming，CPU验证使用既有preflight/supervisor plan，实际提交仍仅用supervisor。

新根：2026_10_7-23_29__recovery_min_height_p1_guardfix_from_s50。
[声明](../configs/experiments/2026_10_7-23_29__recovery_min_height_p1_guardfix_from_s50/spec.json)、独立账本/authorization_receipt/preparation_manifest均在同目录。
S50及reward/PPO/USD/action/control/termination/evaluation与上一声明逐项相等。
原始来源诊断由tools/recovery_progress_baseline校验身份后读取，不从compact candidate summary补零。

提交前CPU检查另复现了PhaseCoverage懒分配inference tensor、第二个rollout普通reset失败的同类问题。
新增统计项分配现在在torch.inference_mode(False)中创建持久正常tensor，仍在原推理rollout统计；不影响动作采样、奖励或优化器。
新增真实“两次推理rollout→普通reset”测试。共享全量516 passed；实际冻结副本60 passed。
[最终冻结验证](../isolated/2026_10_7-23_29__recovery_min_height_p1_guardfix_from_s50_cpu_verified/verification.json)。
较早cpu目录保留为修复前的准备检查，不作为本次提交代码身份。

前两链实际墙钟232.9681秒、source204.8366秒、smoke0.2345秒、PPO0更新。
本次source≤660秒、smoke≤20更新/899秒、formal≤100更新/7200秒、chain≤8819秒。
累计chain上限9051.9681秒≤原9060秒，source上限864.8366秒≤900秒，smoke上限899.2345秒≤900秒；累计PPO上限120更新/983040样本。
旧预算/失败报告/模型/评估/冻结代码不重置或覆盖，本次不增加课程、耐久或自动重试。

一次supervisor握手SOURCE_EVAL；submitted=true、submission_verified=true；formal_first_update_verified=false、started=false。
共享物理GPU0，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，preemption=false，未停止其他进程。
[提交回执](../artifacts/2026_10_7-23_29__recovery_min_height_p1_guardfix_from_s50/submission_stdout.json)。
这些是提交时证据，不证明formal已更新、smoke已通过或新物理能力已学会。后台owner负责预算、评估、结算和当前会话终态通知；交互worker不轮询。

本轮代码修改仅src/native_stand/recovery/min_height.py与tests/test_recovery_min_height.py的统计张量生命周期修复。
其余新增为本次配置/独立账本/授权/准备清单、CPU冻结验证、回执和本文；README/STATUS追加本次提交说明。
