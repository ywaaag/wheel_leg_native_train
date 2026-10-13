# Recovery冻结随机rollout诊断：失败、修复与有界重试准备

2026-10-09用户同意冻结随机rollout联合诊断，并提出25次更新可能不足。该可能性成立：25更新无明显改善不证明长期不可学习。本任务只为判断探索/回报是否值得延长，未授权新PPO。

## 本次真实结果

首次run `runs/2026_10_9-09_33__recovery_b25_frozen_rollout_probe`，attempt `a4b0095afa084dc68320806fdd9b88ec`，已FAILED并结算。环境创建后共享evaluate_batch先读取标准Recovery diagnostic_profile，但新rollout请求diagnostic_storage=None，触发TypeError。失败在随机采样前，无完成rollout、无NPZ、新checkpoint或PPO/optimizer更新。ledger墙钟5.328720秒，terminal5.000851秒，退出清理另计。

本轮应先隔离诊断adapter配置读取，这是可避免的新增分支接线错误；CPU collector真实RSL测试通过不能替代adapter生命周期覆盖。已用recovery_batch_arguments将普通Recovery参数与rollout分支隔离，补None storage与原普通分支回归。旧失败run/spec/ledger只读保留，不重置实际消耗、不自动重新运行。

## 准备的接口与范围

纯domain.rollout_probe严格声明2×64×128、optimizer_updates=0、详细数组上限64MiB；保留认证RecoveryB25、fixed26/25/13、当前beta=.3奖励、150D与原控制/新USD。

tools.frozen_rollout_probe复用真实RSL PPO.act/process_env_step/compute_returns，不调用PPO.update/optimizer.step；完整加载actor/critic/Adam，结束比较state_dict不变并恢复RNG/actor模式。保存pre150D/family/episode/control mask、原ppo样本mean/std、postpre-reset geometry/control/reward/record、values/returns/raw与globalnormalized advantages以及timeoutbootstrap后的storage reward。原始reward和storage reward分开，不能将timeoutbootstrap当新奖励。

共享supervisor --evaluation-only→monitor→evaluate_batch提交，独立evaluate ledger；engineering_diagnostic_only、gate NOT_RUN，不冒充23秒完整能力评估。计算returns不计PPO更新；16384是采集transition而非训练样本。后台并不新增watcher；明确前台有界诊断可等待自身退出。

## 已完成CPU和未授权重试

- 最终全回归683 passed，冻结PORTABLE5 passed、schema/plan/来源完整初始化通过；fixture调用真实RSL两个rollout验证无权重/Adam变化、数组尺寸与GAE有限，另测setup异常RNG恢复和普通/诊断分支分离。
- 全回归一次共享源码execution_dependencies接口暂缺导致失败，该文件随后已存在，单项与全回归重跑通过；没有改动同事该接口，保留初次失败记录。
- 重试声明：`configs/experiments/2026_10_9-09_40__recovery_b25_frozen_rollout_guardfix/spec.json`；新budget/poses/publication/preparation保持UNAUTHORIZED、attempts空，尚无run/reserve。
- 总诊断墙钟仍600秒，前次5.328720已用，重试最多594.671280秒；PPO0、2×128×64、NPZ≤64MiB不变，sharedGPU0同UUID，禁止停止他人进程或自动换卡。
- 重试冻结CPU报告：`artifacts/recovery_frozen_rollout_guardfix_cpu_20261009/validation_result.json`。
- `scripts/review_recovery_frozen_rollout.py`已准备离线identity/reward/globalGAE/固定trajectory扣bonus审核，尚无真实数据，不能输出模拟结论。

## 下一判断

若动作已有有效收腿探索、回报/advantage也支持这些动作且旧组保住，可准备从认证来源独立更长块（如100更新、早期25/50/100筛选），才能检验“次数太少”；该更长训练必须新批准。若clip后控制几乎无差异或advantage明显错配，先解决相应单变量，不先耗长训预算。两rollout跨度2.56秒含初始化，不覆盖完整10秒保持、不测收敛，也不能唯一确诊critic record别名。

## 改动文件

新增`src/native_stand/command_v6/domain/rollout_probe.py`、`tools/frozen_rollout_probe.py`、`scripts/prepare_recovery_rollout_probe.py`、`scripts/review_recovery_frozen_rollout.py`、`tests/test_recovery_rollout_probe.py`；修改`tools/evaluate_checkpoint.py`、`tools/storage_budget.py`、`config.py`。更新TOOL_INDEX、ARCHITECTURE、STATUS和RECOVERY_STANDING_PLAN及本报告；独立spec/CPU产物为审计证据。没有改物理/actor/critic/reward/旧run，没有新PPO或文件清理。
