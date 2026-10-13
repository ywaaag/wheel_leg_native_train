# Recovery P1 reset修复后的独立重试

终态更新：事件53acf4f6cdbc0c19ec7fd48c，链FAILED；source评估完成，smoke保护器误读compact候选摘要，在AppLauncher前失败，PPO仍0更新。[复盘与接线修复](RECOVERY_MIN_HEIGHT_P1_GUARD_TERMINAL_REVIEW_20261007.md)。下方握手为历史记录，未自动续训。

用户在事件0809b5e45005c37591bb8494失败复盘后明确请求“继续”，本次按原P1范围执行一次独立修复重试。
新config/run根：2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50。
旧22_10账本、失败报告、源码快照保持原样，不重置source used=1；旧smoke/formal均0更新。
来源仍为S50，SHA de06b39d2a88c44250309b4ae0509188b532cc5c51a681d456a545c307243694。
reward、PPO、control、action、USD、termination和评估配置逐项与前次声明相等；共享源码只修复RiseHold持久dwell的inference生命周期。

本次source≤820秒、smoke≤20更新/900秒、formal≤100更新/7200秒、chain≤8980秒。
旧链已耗73.2669秒，本次与旧链累计墙钟上限9053.2669秒，小于原批准9060秒；累计PPO上限120更新/983040样本。
独立授权与账本见[声明目录](../configs/experiments/2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50/spec.json)。
不追加配方、课程、耐久或自动再重试。

验证：共享CPU510 passed；实际冻结副本专项54 passed，包含真实RiseHold推理后reset及训练step；plan PASS，budget SHA未变、plan output未创建。
[冻结验证](../isolated/2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50_cpu/verification.json)。

已通过唯一supervisor提交。一次握手：submitted=true、submission_verified=true、current_stage=source_eval、run_state=SOURCE_EVAL。
formal_first_update_verified=false、started=false；不声称formal已经更新或修复已经取得新物理验证。
共享GPU0，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，preemption=false；未停止其他进程。
[一次提交回执](../artifacts/2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50/submission_stdout.json)。
后台owner负责source→smoke→formal、预算、评估、结算与终态通知。交互worker不轮询，不从剩余额度推断自动延长。
本轮新增独立config/预算/授权/准备清单、CPU冻结验证、提交记录及本文；根README和STATUS新增本次提交说明。
