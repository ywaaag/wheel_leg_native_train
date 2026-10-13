# 冻结update50完整几何复核

用户明确同意执行PPO0补采；独立根2026_10_7-20_17__recovery_update50_geometry_ppo0。
来源为18_06/formal/model_update_50.pt，严格冻结actor、不建训练更新。
保留原DrawBack初态、当前限位USD、动作/PD、height.36与起身验收，seed104。
一个23秒第一episode请求，8评分环境；full_trace/diagnostics保存全过程
root/height、pitch/roll、腿长、轮心root几何、接触、active q/dq/action和力矩。
不改变奖励、惩罚、制动、Kv或限矩；不随机搜索姿态、不启用R0额外请求。
预算evaluate一次/<=600秒、online/offline optimizer0、sample_limit0。
使用supervisor --evaluation-only，GPU0共享，不停止其他进程，不重试或续训。

原Recovery batch只支持holding10秒；本次仅当显式合法rising_task时要求23秒，
普通Recovery仍10秒，未知/100秒/混用请求拒绝。无需绕过checkpoint身份：
eval spec将冻结50作为严格source，记录其原spec/current asset SHA。
CPU438 passed，plan-only PASS，requested_seconds23。
后台monitor所有者负责退出、exact-ID结算与终态通知；交互不轮询。
提交收据证明预约和启动monitor，不等于评估完成或能力通过。

变更：domain/evaluation_requests.py、tools/recovery_batch.py、tools/evaluate_checkpoint.py；
tests/test_recovery_geometry_request.py；新spec/local预算；本文和STATUS/README/
ARCHITECTURE/TOOL_INDEX/RECOVERY_STANDING_PLAN导航。原run/raw/checkpoint/ledger不改。
