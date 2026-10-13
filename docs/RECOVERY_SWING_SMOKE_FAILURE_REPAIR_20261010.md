# Swing-only A工程smoke失败复盘与修复 — 2026-10-10

事件1c82f741fd59682508dcbfe5。14_18 A链FAILED，source_eval及smoke均COMPLETED；smoke10/81920样本，formal0，链145.9885秒。原ledger source_eval1/smoke10/formal0、实际phase墙钟10.0912+129.2734秒保留。不是策略成功或formal训练结束。

唯一证书错误：smoke did not record a complete required-duration training episode。旧配方wiring_smoke required_event_duration_s=11.5未被Swing-only准备重置。短失败episode约.7秒，虽然完成真实有效初始化/受控动作/故障后reset，却不满足这个旧全时域前置。这是本轮准备器遗漏，与用户明确“不要求Swing学会才通过smoke”冲突；不是数值/物理异常。

真实smoke10累计受控35840条（43.75%）、无控制46080，actor optimizer160次；末批mask3086/8192、KL/clip均有读回，未发现储存计数错位。source及smoke末候选Swing0/8、无入口、空retained；双腿<=.34m持续50ms事件0。这些证明受控更新工程路径已跑通，不证明它改善起身或mask完全因果正确。

公共准备器已修：Swing-only smoke覆盖声明覆盖旧duration，required_event=completed_episode、minimum1、duration=policy_dt .01秒、offset=settle_max、必需Swing group真实有效初始化episode。不凭10updates直接PASS；仍必须有真实完成episode、actor更新、非零valid optimizer/reward事件、身份与无故障读回。失败episode可满足工程事件，最终起身+10秒gate未改。

新增swing_smoke_contract纯函数与回归。相关28 tests通过；新14_23 A/B每臂冻结9 PORTABLE通过。旧FAILED证书/历史spec/ledger不改，不把旧证书重新算成通过。原14_18 B已授权未提交，但同样携带11.5s条件，因此不运行已知阻塞配方，不修改其已授权spec。

新configs/experiments/2026_10_10-14_23__recovery_swing_controlled_actor_a及_b仅修smoke契约，来源/奖励/初始化/controlled PPO/seed/budget不变；完整发布、UNAUTHORIZED/零attempt，尚无run。普通CPU修复与准备已在原任务范围内完成，旧授权明确失败不自动重试，因此A新尝试及B新声明运行须用户明确修复后的安排。

若两臂各重新smoke10+formal100，新增220updates1802240样本上限；加上已用A10将达累计230updates1884160样本，比原总220多10次，不能静默重置。新链各5400秒、两链10800秒加既有145.99秒也超原全链总界；需明确新增或累计预算。当前不申请隐含超额、不搬历史余额。也可另设受限formal恢复复用旧smoke实证，但需要现有白名单证书流程是否支持的独立审查，不手工伪造PASS。

本轮新增本报告/isolated review，新14_23声明及冻结CPU证据；修改command_v6/domain/recovery_course.py、tools/prepare_recovery_course.py、tests/test_recovery_swing_only.py，更新STATUS/Recovery plan。没有仿真/PPO/新通知、未commit，原run/checkpoint/evaluation/ledger只读。
