# Recovery P1来源评估失败复盘

事件0809b5e45005c37591bb8494已核对报告SHA并通过既有CLI确认reviewed。
run：runs/2026_10_7-22_10__recovery_min_height_p1_from_s50，终态FAILED。
依据为链completion_report、chain_terminal_report、source_eval报告、独立账本及冻结min_height.py。
[输入SHA和CPU复现记录](../isolated/recovery_min_height_p1_inference_reset_review_20261007/review.json)。

## 结论和消耗

这是source_evaluation阶段的状态生命周期错误；没有进入PPO，不构成P1训练退化或新目标学习失败的证据。
source_eval attempt `8bd836c2c252435fad4c73fd73440d19`，exit1，70.2648秒；整链73.2669秒。
账本source_eval used=1，smoke/formal used=0，PPO updates/samples=0。
来源S50没有被这次运行更新；accepted/best/latest均无新的候选。
原formal限额100未使用，但旧chain不可重复提交、source尝试已消耗，不能据此自动重试。

## 失败机制与CPU复现

评估在torch.inference_mode下调用真实RiseHold.observe。
原代码`self.dwell=torch.where(...)`重新绑定持久成员，结果为新inference tensor。
评估随后切换retained R0，在推理上下文外env.reset→RiseHold.reset执行原地索引赋值，PyTorch拒绝修改inference tensor。
异常清理reset遇到同一个错误；cleanup并不是第二个独立物理失败。

对实际冻结文件独立CPU加载后证实：dwell storage被替换、is_inference=True，退出inference_mode后reset报完全相同错误。
此前假环境评估测试没有使用真实RiseHold成员，因此未覆盖这种生命周期；这是本轮新增实现的缺陷。
source_eval没有产出完整持久化evaluation_source/候选结果，不能从执行到了R0 reset推断DrawBack通过。
不将丢失的临时轨迹重建为测量，也不把best=None解释为来源原本不会抬升。

## 最小修复与验证

仅共享源码将赋值改为`self.dwell.copy_(torch.where(...))`，保留创建于正常上下文的持久存储。
不在reset临时开inference_mode掩盖问题，不改变动作、奖励、时钟、PPO或物理配方。
新增回归使用真实RiseHold，连续验证两轮推理评估后的普通reset、所有持久tensor身份和is_inference、随后普通训练step。

CPU全量：510 passed，20.89秒；无AppLauncher或GPU模拟。历史冻结文件、模型、原始报告和账本不修改。
修改文件：src/native_stand/recovery/min_height.py、tests/test_recovery_min_height.py；新增本文，更新STATUS/README/准备报告的终态说明。
该CPU修复尚无新的PhysX验证；本通知不授权续训，本轮未提交新链、未重试、未启动仿真/PPO。

下一运行必须先核实新授权、创建独立路径/账本及冻结副本、完成CPU和plan检查，再走同一supervisor。
原任务目标仍按最终RECOVERY_STANDING_PLAN第0–13节，当前无需改变reward/std/USD或新增课程。
