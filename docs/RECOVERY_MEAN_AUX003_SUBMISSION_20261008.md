# λ=.03独立短块准备与提交

实验2026_10_8-20_39__recovery_swing_mean_aux003_from_b25。用户同意上一审核报告建议：认证B25、固定26/25/13、只将轮mean辅助系数改为.03，新版本swing_wheel_mean_excess_rollout_v2；旧v1仍.001。std/actor/critic/全部Adam严格继承，来源SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44；reward/观测/物理/控制/终止/gate/辅助batch/分母/clip顺序保持，B奖励关闭，不从latest继续。

## 预算及通知

新完整publication绑定spec/budget/manifest/poses，独立授权receipt；source≤900秒/PPO0，smoke10≤900秒，formal≤25≤3600秒、10/25完整三组验收。最多35实际更新/286720样本，phase5400秒、chain5460秒含60秒清理，不借旧额度或自动延长。

用户已明确允许自动通知并唤醒当前会话；本块notifications.enabled=true，target/session7bbabd67-183d-4185-b686-1aefcd55781b，后台按现有report_ready/hash及at-most-once流程投递，不额外watcher，不改旧禁通知记录。通知不授权续训。

物理GPU0共享，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda:0；不停止其他进程、不换GPU。public supervisor零写plan/check-submission READY，实际启动状态见本报告后附回执及STATUS；formal先须实际smoke梯度证书。

## 验证与改动

修改mean_auxiliary.declaration/validate：v1.001/v2.03各自严格版本；日志读回实际version。公共recovery_course请求解析支持v2；新测试验证版本仅version/coefficient区别，旧版错用.03拒绝。公共准备器编译原sampling/assessment并完整发布新声明；本轮显式通知覆盖只在新发布前完成，未修改旧或已授权spec。

针对性22项CPU通过（1.63秒），PORTABLE冻结schema/plan/5测试通过（1.30秒），严格初始化parameter/std差异0、Adam不变；没有CPU optimizer audit重复、模拟或PPO更新证据。版本接线/通知配置工程通过不保证行为通过。

改动文件src/native_stand/recovery/mean_auxiliary.py、src/native_stand/command_v6/domain/recovery_course.py、tests/test_recovery_mean_auxiliary.py、新experiment目录、本报告及STATUS/RECOVERY_STANDING_PLAN/TOOL_INDEX。未commit、未删除旧脚本、未覆盖checkpoint。

## 后续规则

读真实aux/incoming/combined gradient、eligible分母/采样clip/std及三组entry/保持，不因mean改善便accepted。旧组两次完整失败停止，全部三组完整接受及时保存停止；否则在有界终态复盘，不在线改lambda/自动续训。来源B25为fallback。

## 一次启动回执

submitted=True，worker身份核验=True；阶段SOURCE_EVAL，formal首更新未验证；worker 472697。回执configs/experiments/2026_10_8-20_39__recovery_swing_mean_aux003_from_b25/submission_review.json。不轮询后台。
