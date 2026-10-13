# DrawBack奖励分解及仅接触退化不停止候选 — 2026-10-09

CPU工作完成，无仿真/PPO/新checkpoint。组件证据isolated/recovery_guidance_components_20261009/audit.json绑定原始source/10/25/50评估和冻结spec SHA。

同一前300ms env0位置质量均值.08018→.08704，对称质量.35581→.43039，乘积.02273→.03067；乘积保留位置质量信号约28.35%→35.23%。目标平均距离.39283→.38971m。位置几何局部斜率代理非零，不能说没有任何引导，但对称项明显压低位置奖励；该代理不是PPO策略梯度或动力学可达性证据。此前更对称却不收腿的判断仍成立。

为避免同时改奖励和停止条件，本次新实验只改变旧保持接触退化处理，保持原DrawBack镜像reward、来源10_58new25、std/Adam、USD/physics/control和初始化。不是从退化new50续训，也不加新reward/强制对称动作。允许Swing起步腾空仍按原当前协议，不要求必须腾空，静态DrawBack轮心作为机体下方支点近似，非精确COM跟踪。

## 显式停止契约

retention_regression_policy版本recovery_retention_contact_diagnostic_v1：仅retained families失败且所有失败env都完成要求hold窗口、无runtime_fault、standing_failed_checks包含continuous_contact且只含continuous_contact/terminal_certificate时，将连续退化触发stop改record_only。进度仍记录stop_requested/stop_effective/policy和原consecutive_failures。倾角/缺测/窗口不完整/其他证书失败或runtime fault仍停止；数值异常、物理故障、预算保护、原Recovery其他progress guard全部保持。

该规则不更改评估accepted、连续接触评分或最终晋级。旧组失触仍标失败、不接受为保旧成功，不能拼模型。用户要求取消失触停训由这一窄范围版本落实，不取消所有退化/安全停止。源码默认没有该字段时保持原行为；历史run冻结代码不变。

## 独立候选

新声明configs/experiments/2026_10_9-21_49__recovery_drawback_contact_diagnostic_total100/spec.json，smoke10＋formal90总≤100更新819200样本，formal10/25/50/90三组完整评估，source900/smoke900/formal7200秒、chain9060秒。当前UNAUTHORIZED/零used/空attempt，尚无run。来源checkpoint SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c。原18_39剩余40不搬用、不重置历史额度。

相关16 CPU tests通过；Recovery全组233 passed/2既有JIT warnings，独立冻结5 PORTABLE通过，actor/critic/Adam严格初始化保持、出版SHA通过。真实runtime计数、停止条件消费与更长训练行为尚未认证；CPU工程通过不证明起身。权重和目标不变，驻留/低位空中部分reward风险仍保留。

下一需明确批准这个新独立总100预算后才能公共授权登记、sharedGPU0核验与supervisor一次提交；终态自动通知按明确已有currentowner权限冻结，失败不重试、不追加。若长一点仍不移动轮子，不自动提高奖励系数。

## 文件

新增scripts/audit_recovery_guidance_components.py、recovery/regression_policy.py、tests/test_recovery_regression_policy.py、本报告、上述独立config目录和CPU证据；修改recovery/validation.py、command_v6/domain/recovery_course.py、tools/prepare_recovery_course.py、train.py及STATUS/RECOVERY_STANDING_PLAN/TOOL_INDEX/ARCHITECTURE。无旧run/spec/ledger/checkpoint/资产变更，无commit。
