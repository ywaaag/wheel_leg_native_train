# Swing轮mean辅助loss：接线与短块提交

## 授权与唯一变量

用户明确批准执行RECOVERY_STANDING_PLAN第8.6节，实验2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25，公开supervisor提交成功。一次有界握手SOURCE_EVAL，worker身份核验True，formal首更新未验证；不轮询/守候后台。

来源Recovery认证B25：runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt；SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。严格继承actor/critic/全部17Adam状态/实际std，冻结CPU参数差异0；腿/轮目标1.6rad/100rad/s，150D/6D/新USD/原reward/gate/终止/40与5.5Nm保持。固定训练family26/25/13复用已运行课，不从失败new75继续。

只新增Swing/pre_entry/raw wheel mean loss：lambda.001、margin.9、channels2/5。不是环境reward，不乘dt，不执行mean bias/制动/teacher或方案B。旧组样本auxloss0但共同网络可能受更新影响，不保证无损。

## 真实接线、分母与clip

RSL-RL公开optimizer hook没有minibatch索引，本轮使用当前真实on-policy rollout所有eligible输入，固定batch在每次optimizer.step复用，不伪称当前minibatch。分母是该rollout全部受控transition（初始化有效且FSM RECOVERY），eligible再要求实际pose familySwing和rise_hold.entry<0；metadata与obs在ppo.act前复制，episode reset不串接，初始化/旧组/入口后排除。

PPO epochs4×minibatches4＝正常每rollout16个optimizer step；hook每次只做确定性actor前向与autograd.grad，不调用distribution.update/sample，保留std无直接aux梯度。进入hook的PPO+entropy actor梯度已经由RSL-RL裁剪；加入aux后再次按原max_grad_norm裁剪actor合成梯度，critic不加辅助项。incoming clipped norm、weighted aux norm、before/after reclip norm与应用次数/eligible/分母逐更新读回；不声称重构原始未裁剪PPO gradient。

实际随机ppo.act的mean/std/sample只读聚合，记录eligible六通道mean越界比例、真实sample clip比例和std均值；这些是训练实测，不是上轮PPO0 Gaussian解析概率。

smoke wiring certificate新增实际eligible+nonempty hook+nonzero gradient证据；缺证据阻止formal。source_eval无optimizer/aux应用。formal任一同checkpoint三组完整accepted即保存并停止本块；旧组连续两次完整失败保护保留。

## CPU量级与验证

真实B25在保存的240条Swing输入上，lambda.001 raw excess mean.89975，weighted loss.00089975，actor weighted aux norm.013418；没有传入PPO梯度/没有optimizer.step，参数/RNG不变。该CPU审核分母仅240Swing控制输入，不冒充runtime全受控分母；runtime按实际Swing占比稀释，真实incoming/aux norm另记录，不因此声称系数已最优。

全量共享CPU633 passed；随后新增随机读回边界测试及完整接受提前停止接线，最终PORTABLE冻结schema/plan/严格初始化及6项测试通过。针对性实际Adam hook测试验证输出更新方向、空eligible与无hook优化完全一致、RNG保持、合成梯度二次裁剪、mask/分母/读回。AST和diff检查通过。

最初准备因公共checkpoint频率不接受10失败，未发布/未模拟；采用checkpoint_every25与明确full unlock10/25/50，完整评估点恰好10/25/50（full_every50），10由full评估触发保存。没有改公共频率限制。

## 独立预算、提交与通知

source_eval≤900秒/PPO0；smoke10≤900秒（81920样本）；formal≤50≤5400秒（409600样本）；合计最大60更新/491520样本、phase墙钟7200秒、chain7260秒含60秒清理。新spec/poses/budget/manifest完整publication SHA，register_authorization记录当前明确批准，不借旧额度/不重置旧账本。

物理GPU0 shared，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda:0，不停止其他进程、不切GPU。source/smoke未通过工程证书不提交formal；已通过工程不代表行为接受。

spec/ledger/回执：configs/experiments/2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25/；run：runs/2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25/；CPU审核artifacts/recovery_mean_auxiliary_cpu_audit_20261008/audit.json；最终冻结验证artifacts/recovery_wheel_mean_aux_frozen_final_cpu_20261008/validation_result.json。

本次外部通知仍禁用：运行审批未显式指定发送完成消息，不能暗自启用。后台会写completion_report/report_ready，人工请求时一次只读核验；不增加watcher。剩余预算不自动续训/重试/做耐久。

## 本轮改动文件

- src/native_stand/recovery/mean_auxiliary.py：显式schema、当前rolloutbatch、public optimizer hook与读回。
- src/native_stand/recovery/validation.py：辅助项冲突/版本校验。
- src/native_stand/command_v6/train.py：pre-action mask/capture、真实采样只读、hook、日志与完整通过提前停止。
- src/native_stand/command_v6/wiring.py：smoke非零梯度证书要求。
- src/native_stand/command_v6/domain/recovery_course.py、tools/prepare_recovery_course.py：可选aux请求，公共准备发布及10/25/50调度。
- tests/test_recovery_mean_auxiliary.py：PORTABLE接线边界测试。
- 新实验声明与本报告、RECOVERY_STANDING_PLAN、STATUS、TOOL_INDEX、ARCHITECTURE。

## 终态决策

优先真实Swing高度/入口/保持进步且旧DrawBack/R0保留，不能只看loss或clip改善。mean改善但仍早倾倒则另准备reward或观测单变量；eligible0或mean无变化先查接线/实际梯度，不自动增lambda；旧组退化回退B25。来源/latest/best_new/accepted分别记录，新接受须三组同checkpoint完整通过。
