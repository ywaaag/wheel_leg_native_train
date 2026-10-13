# Swing-only A/B smoke修复后的明确授权提交 — 2026-10-10

用户在14_18 A失败报告之后重新发送完整任务及明确运行授权。本次使用已准备的14_23修复声明，两臂新账最多220updates/1802240原始transition/全链10800秒，每臂source≤900、smoke10≤900、formal100≤3500、清理100，chain5400秒。原14_18 source_eval1/smoke10、81920样本/145.99秒原账保留，不清零、不搬formal余额；两次批准历史累计最多230在线更新1884160样本、墙钟10945.99秒，不能把新批准当原总额仍未变化。

新experiment configs/experiments/2026_10_10-14_23__recovery_swing_controlled_actor_a及_b：Swing-only64、actor_valid PPO、原21_58奖励/10_58谱系、相同seed20261010且restore_source_rng=false/restore_recovery_curriculum=false。唯一A/B学习变量仍为B四腿output-layer一次性校准，candidate SHA d074488410257e02b44704f8b2119612617cf44267c50d6e4561f72d39a9ab51，校准最大.029990rad、anchor RMS.049990rad，留出.030043超过校准门槛并已披露。目标方向覆盖44.3%不是技能证据。

修复仅Swing-only smoke旧11.5s持续episode条件：要求真实completed episode至少一个policy interval及有效初始化group事件、非零valid optimizer、真实reward/wiring身份和无mask违规。没有要求已学会Swing、不改最终同episode完整10s gate。旧FAILED证书不改写。

本次授权前核验单臂完整publication、来源/候选SHA、无重复submission/fresh output/零used账本，两个已完成冻结验证的每个inputs SHA与当前文件逐一匹配（各9PORTABLE通过）。相关28tests为上一修复验证，本轮无源码变更、不重复扩大测试。A/B有效spec差异限experiment/artifacts/pose库路径及Bsource/candidate身份，reward/control/std/seed/采样一致。

公共register_authorization两臂登记，A check-submission PASS/READY后唯一supervisor提交，一次默认5秒握手SOURCE_EVAL/worker身份OK、formal首更新未核验。run runs/2026_10_10-14_23__recovery_swing_controlled_actor_a。B已AUTHORIZED但尚无attempt/run，按本条授权A终态事件唤醒后只读复盘，再核验GPU/identity/session/ledger/output首次提交；不需重复用户确认。本次再失败不自动重试，不自动长训。

physicalGPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→logicalcuda0共享，不停止其他任务、不换卡。提交前快照127/32760MiB、盘约19GiB；仅瞬时核查。既有owner终态at-most-once通知当前session7bbabd67-183d-4185-b686-1aefcd55781b。没有个人轮询/watchers/等待长训。评估sourcePPO0、formal25/50/100，formal受控25万为目标不是追加额度。

本轮只授权登记14_23 spec/budget及receipt，新增isolated提交记录、本报告，更新STATUS与Recovery计划；新run和冻结代码由supervisor生成，无其他源码/旧run/checkpoint/evaluation/ledger改写，无commit/push。
