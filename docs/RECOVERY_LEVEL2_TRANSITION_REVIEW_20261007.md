# Level2抬升到收稳复盘与下一配方

执行更新：用户随后明确批准此prepared spec的来源评估600秒、smoke10/600秒、
formal最多100/3600秒，总110/901120samples，并沿用GPU0共享。独立账本已AUTHORIZED，
授权后plan-only PASS/health无finding；下文UNAUTHORIZED是准备阶段历史状态。
后台执行与一次启动握手见STATUS，不能从授权推断formal已经运行或模型已通过。
批准后全量437项CPU通过（17.68s）、source plan-only PASS/health无finding。
公共supervisor一次5秒握手已验证提交与worker身份，state=SOURCE_EVAL；
exact chain attempt803c92b92d4349d7b42d176225ffcd83，worker3490652。
formal首更新未核验；不轮询等待，由后台owner完成有界流程、结算和通知。

本轮用户同意推进复盘中的诊断及工程修复。只CPU/离线；没有AppLauncher、PPO、
旧链续训、停止其他进程或改写历史证据。当前训练已结束，不能引用旧PID作实时状态。

## 原始证据与结果

来源：runs/2026_10_7-17_21__recovery_level2_drawback_from1000/source_eval/evaluation_source.json。
候选：同run/formal/evaluation_100_0_0.json。脚本scripts/review_recovery_transition.py，
可信离线输出isolated/recovery_level2_transition_20261007_verified/review.json及review.md。
逐环境原始路径/SHA绑定且执行后重查。第一轮offline输出目录保留，verified版修正
lift参考为初始化接受后的实测高度（此run没有reverse curriculum），不得引用旧目录
lift重放值作为精确运行reward。两版均未修改原始输入。

分组为低于0.34m、0.34–0.38m、超过0.38m；每组样本可能不连续，不把分组时长
当作已站稳时长。全部指标为policy100Hz，非完整PD子步力矩认证。

| 记录/阶段 | 平均记录时长 | mean abs pitch | 任意通道限矩采样比例 |
| --- | --- | --- | --- |
| source，高度区间内 | 0.040s | 0.010rad | 0.750 |
| source，高于0.38m | 22.410s | 0.312rad | 0.000 |
| new100，高度区间内 | 2.599s | 0.029rad | 0.996 |
| new100，高于0.38m | 4.491s | 0.054rad | 0.795 |

source穿过目标高度时双轮接触比例为0，vertical_motion成本约-13.26/s，
不能把短暂穿越高度区当作站立入口。source高位段pitch成本约-27.31/s、
roll成本-4.45/s，而lift+2、upright约+.47、height约+.82、support约+.49/s；
height_overshoot约-1.39/s。水平成本是显著负项，但这只是记录状态的公式重放，
不是因果梯度或完整return/advantage分解，不能据此宣布唯一根因。

new100改善了pitch并短暂进入完整入口，随后维持不住高度/接触、倾角终止。
其高度区间内roll成本约-2.74/s，pitch约-.60/s；任意通道饱和接近全程。
候选未保存完整control trace，不能将其归因于某个电机。source抬升期可见轮通道
饱和，但source后段不饱和；不能据此推断candidate也只是轮饱和。
6通道control不含被动膝角；“全过程不触新膝限位”仍未由这些轨迹认证。
25/50只保存有限失败尾窗，无完整transition，不用尾窗重建全过程。

R0本来就在旧1000新USD基线下0/8，因此没有经过认证的旧R0能力可称被本轮保持；
40%rehearsal占比不能替代原能力基线。失败的new100不成为默认下一起点。

## 报告与选模工程修复

新score_rise增加post_rise_metrics、standing_metrics_scope、post_rise_evidence_status。
没有入口时post_rise_metrics=null、status=NOT_ENTERED；有入口但缺完整保持时
status=INCOMPLETE；完整窗口为COMPLETE，是否通过仍取全部gate，不以完整代替成功。
旧standing_metrics保留兼容但明确标pre_entry_diagnostic_only，不能冒充保持成绩。
recipe传播这些字段。未更改任何时间/姿态阈值或旧raw结果。

classify_recovery识别autonomous_rise，独立ranking优先full acceptance、当前通过数、
retained通过数、完整有效保持、较少物理终止、入口数、SHA；不奖励失败前观测更久
或最高高度更大。只有full gate通过才accepted，失败候选best不代表可部署。
新ranking仅用于未来run，旧candidate_selection不覆写。

## 下一实验的可审查声明（未授权运行）

configs/experiments/2026_10_7-18_06__recovery_level2_settle_cost_probe/spec.json。
同旧1000、实测DrawBack、当前USD、60%低位/40%R0、actor/critic/Adam、LR、
环境量和时相、控制、安全保护、起身协议；只同时降低pitch/roll成本幅度-4→-1，
不动归一化尺度/height gate，也不同时改高度目标、立起奖励、轮制动或动作。
这是二维水平成本幅度的联合干预，不称为单独pitch或roll因果消融。
evaluation gate_diagnostics=true补控制轨迹，仅观察评估，不修改PPO；记录此差异。
新report/ranking不改变gate；判定仍需起身后同episode完整10秒。

拟议source<=600s/PPO0、smoke10/600s、formal<=100/3600s，110updates/901120samples；
ledger UNAUTHORIZED。这是对显著水平成本的受控假说检验，不是盲目更大惩罚或
保证解决饱和。比较初态有效率、入口、完整保持、fall、接触、各通道饱和和
source收益；无净收益则保留来源，不自动续训。

本轮文件：scripts/review_recovery_transition.py；recovery/{rising.py,recipe.py,selection.py}；
command_v6/completion.py；tests/test_recovery_rising.py；本spec及独立local budget；
本文、STATUS、README、ARCHITECTURE、TOOL_INDEX、RECOVERY_STANDING_PLAN。
已有dirty改动保留，未编辑旧资产/checkpoint/ledger/report。

验证：437 CPU passed（17.73s）、git diff --check通过；新spec完整plan-only
READY_NEEDS_AUTH，仅AUTHORIZATION_MISSING，新run目录未创建。
