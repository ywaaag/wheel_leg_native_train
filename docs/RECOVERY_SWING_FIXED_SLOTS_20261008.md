# Swing固定训练环境首块：离线复盘、配方与提交

## 旧块终态与结论

`2026_10_8-14_51__recovery_level3_swing_from_b25`已COMPLETED：smoke10/formal100，901120样本、2918.76秒；Swing来源/25/50/100均0/8。来源B25、new25/new50的DrawBack/R0各8/8；new100两个旧组各0/8，保持窗continuous_contact失败。新50是诊断排序，不是新增完整能力；继续采用来源B25。

正式100更新有效任务transition785076：Swing12305（1.567%）、DrawBack538450（68.586%）、R0234321（29.847%）。Swing无入口后保持样本，401个完成episode平均.707秒；该时长包含初始化，不和恢复计时混用。40%reset抽样不等于40%实际transition。

离线env0共同事件（来源/25/50/100）：首控制约.01秒，pitch超过.10rad约.04秒，首次单轮失触.06–.07秒，tilt超过.5rad约.13–.14秒，峰高约.231–.232米，约.30–.35秒恢复控制后tilt终止。pitch偏离早于失触，不能把失触当唯一先因。首控制主动腿目标与Swing初态差较大，三腿PD请求约±67–100Nm被裁至40Nm、两轮请求约−97/−99Nm被裁至−5.5Nm；100Hz held-PD证据，不是完整5ms力矩认证。动作适用性是后备诊断，本块不同时改动作/reward。

原始身份与逐环境事件：`isolated/recovery_swing_fixed_coverage_audit_20261008/review.json`；可复用离线脚本`review_recovery_swing_failure.py`，无模拟/optimizer。

## 新块单变量

实验`2026_10_8-16_08__recovery_level3_swing_fixed_slots_from_b25`，公共prepare_recovery_course准备，新spec/poses/budget/manifest完整发布SHA及独立授权receipt。

- 来源P2 B/formal/model_update_25.pt，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44；严格加载actor/critic/Adam与实际std，两轮4.88557/3.88416rad/s，不重复减半。
- 仅将随机跨family reset改为固定训练environment family：64环境，Swing26、DrawBack25、R013（40.625%/39.0625%/20.3125%，近似原40/40/20的整数分配）。env0–25 Swing，26–50 DrawBack，51–63 R0。每次只在本family内抽pose，部分reset不改变归属。
- 未延长失败存活，不改终止/奖励/USD/动作/PD/限矩/评分；因此大量Swing初始化仍消耗预算，实际有效transition占比仍须读回，不能宣称已达到40%。
- 明确`sampling.version=fixed_environment_families_v1`；counts之和必须等于64且weights等于counts/64；assessment独立覆盖Swing及两个旧组，不把槽位分配用于评估。
- 独立source≤900秒/PPO0、smoke10≤900秒、formal≤100≤7200秒，完整25/50/100三组评估；chain≤9060秒含清理，110总更新/901120样本。
- 保留来源/早期候选；旧组连续两次完整失败停止，新Swing未成功不作为工程拒绝条件。全部三组同checkpoint完整通过才accepted。
- GPU0共享，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda:0，不停止其他任务。外部通知禁用；不自动续训/重试/耐久或随机倒地。

## 验证

共享CPU596 passed（26.01秒）。首次冻结测试因测试硬编码项目src/历史配置路径失败，未模拟；原报告保留在artifacts/recovery_swing_fixed_slots_cpu_20261008。修正本轮runtime调用测试的源码定位，从实际导入sampling模块查找runtime；历史配置依赖测试在原项目全量已验证，冻结副本只运行独立fixture。

第二次冻结schema/plan/28测试通过，严格初始化所有参数差异0、Adam不变；报告artifacts/recovery_swing_fixed_slots_cpu_v2_20261008/validation_result.json。公开supervisor零写plan与check-submission READY；最终握手见本实验submission_review.json及STATUS，不轮询后台。

## 后续决策

终态一次复盘先比较实际Swing有效transition提升、初始化占比、入口/峰高/存活前缀及旧组完整保持。覆盖提升但动作/倾倒时序不变时，才准备对应合法中间状态/单变量动作学习调查；不直接加制动、对称或更多奖励，也不从退化latest接棒。

## 启动回执

公开supervisor一次提交成功，submission_verified=True，握手阶段SOURCE_EVAL，worker 210269；formal首更新未验证。回执：configs/experiments/2026_10_8-16_08__recovery_level3_swing_fixed_slots_from_b25/submission_review.json。
