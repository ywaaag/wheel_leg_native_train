# Recovery轮均值有界单变量短训：验证与提交

2026-10-09用户同意执行迁移PPO0之后的短训。本轮已通过supervisor提交独立source_eval→smoke→formal链，没有轮询。一次握手SOURCE_EVAL，formal首更新尚未核验，不能说正式PPO已经更新。

## 配方、预算与身份

声明`configs/experiments/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25/`包含spec/budget/poses/preparation/publication/approval/authorization_receipt。新run同名，worker1032925、链attempt9e45423ad684483da873db37862d73dd；submitted=true、submission_verified=true，5秒有界握手。source/smoke/formal目录保留。通知enabled=true，负责人session7bbabd67-183d-4185-b686-1aefcd55781b，后台终态at-most-once。

来源认证RecoveryB25：`runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt`，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。smoke与formal各自严格加载同源actor/critic/Adam，初始化std不再乘旧倍率，参数坐标保持、行为分布公开变化。来源按新分布重新评估，不冒用原Gaussian来源证书或10_50PPO0的spec身份。

单变量相对支撑纪录baseline是action_distribution recovery_wheel_bounded_mean_gaussian_v1，仅2/5 mean=tanh(rawMLPmean)，原Gaussian std/sample/logprob/entropy/KL语义；四腿目标映射、beta=.3纪录及原reward、fixed26/25/13、DrawBack/R0、newUSD、150D、原PD/限矩与评分不改。不是sampletanh/制动/轮置零。meanaux和std初始化干预关闭，Swing腿首步偏差未叠加修复。

smoke10/formal≤25，合计35更新/286720训练samples。source≤900s/smoke≤900s/formal≤3600s，链≤5460s含60秒收尾（91分钟上限，非耗时预测）。full10/25同时评分Swing/DrawBack/R0，source/early/latest/bestnew/accepted分开；旧两组连续两次full失败停止，缺字段UNKNOWN不能通过。无自动重试/延长/调beta/std，无100秒耐久。物理GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda0 shared CLI授权，未停止其他任务或自动换卡。

## 新增验证与smoke证据

真实RSL-RL测试通过：PPO.act/proces_env_step/storage/compute_returns及实际PPO.update；更新前同distribution logprob的ratio=1，更新后actor参数变化且有限。概率更新在bounded mean Gaussian坐标，不能对物理clipped action替换storage未裁剪sample。

smoke证书新增实际support_record_policy证据：eligibleSwing样本存在、两轮mean平均幅度≤1且finite，每轮至少一次rollout有未裁剪样本；否则formal阻断。该最小事件只证明不再全部clip，并不保证有效探索幅度或支撑动作成功；终态仍比较实际std/clip、抬升/入口、完整接触、tilt与两旧组。沿用现已加强的reward基准/reset/失败/ineligible/episodebudget违规审核与真实episode/group事件，不用旧smoke直接放行。

source迁移三组PPO0先前DrawBack/R0各8/8完整10秒、新std重放正确，但Swing0/8；当前新source独立复核仍必要。PPO0不代表学习改善。

## CPU与提交核验

全回归694 passed、22 errors、2warning；22errors均Motion受限恢复证书对共享learning.py/learning_distribution.py的历史源码身份保护，与上轮相同已知阻断。没有改其历史证书或测试冒充通过，当前外任务冻结代码不变，但其未来新源码恢复仍需审查，不声称全套通过。2warnings为torch.jit.script现有RSL导出API弃用提示。

本轮最终冻结PORTABLE14 passed，schema/零写plan/sourceactorcriticAdam完整初始化通过：`artifacts/recovery_bounded_mean_train_frozen_cpu_20261009/validation_result.json`。supervisor一次check-submission READY、配置PASS、当前session/UUID/output/独立unusedbudget/存储核验；submit再次核验resource。结束交互后由后台owner负责采样、保存、评估、退出和预算结算及通知，不再查progress/PID/GPU。

## 本轮文件变更

修改`src/native_stand/command_v6/domain/recovery_course.py`支持严格action_distribution request，`tools/prepare_recovery_course.py`编译该声明，`wiring.py`新增实际policy证据要求；新增`scripts/prepare_recovery_bounded_mean_train.py`（薄request包装，公共course负责发布），扩展`tests/test_recovery_bounded_mean_distribution.py`真实PPOupdate及smoke反例。更新TOOL_INDEX、ARCHITECTURE、STATUS、RECOVERY_STANDING_PLAN和本报告。旧run/raw/spec/ledger/checkpoint、资产和其他dirty changes保留，未清理文件/commit/push。

## 剩余不确定性

若有效轮探索改善但Swing仍不收腿，下一依据真实腿动作与回报选独立干预；不同时叠制动、对称或改变观测。若旧能力退化，不接latest、回退认证B25。此实验尚无训练结果，不能保证有界mean可以解决起身。
