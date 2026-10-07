# Recovery survival/level 离线复盘

核查日期：2026-10-07。只读取已有 run、checkpoint 和源码快照；没有启动
Isaac、物理步进或 PPO，没有修改历史评估、模型、spec、预算或共享训练代码。
本记录修正交接文档的部分判断，不追溯改写旧结果。

可复核产物：
`runs/reviews/recovery_survival_20261007/offline_audit.json`。
生成工具：`scripts/audit_recovery_survival.py`；所有输入记录 SHA256。

## 1. 结论及证据强度

已确认的主要问题是 **短 episode 成功目标与长期水平验收不一致**，同时发生了
reward/terminal 分布变化和来源行为漂移。这支持优先检查成功奖励与终止语义，
不支持把“roll 惩罚太强”或“BC 主导梯度”当作已证实的唯一根因。

source50、新100、新200的相同 seed104/R0 holdout 新协议结果分别为8/8、0/8、0/8。
新100全部完成10s，只失败roll；新200有5个tilt终止、3个完成10s。
无nonfinite/closure runtime fault；课程始终stage0，R1未采样。
formal terminal为STOPPED_BOUNDED/exit0、实际200更新；外层COMPLETED是流程完成。
source50仍为最佳已观察/已接受模型；latest200不能替代它。

| 模型 | 10s完成 | mean abs pitch/roll rad | 稳态高度m | 通过 |
| --- | --- | --- | --- | --- |
| source50 | 8/8 | .021962/.072339 | .366665 | 8/8 |
| 新100 | 8/8 | .026972/.130036 | .361415 | 0/8 |
| 新200 | 3/8 | .107737/.195606 | .353141 | 0/8 |

来源checkpoint、当前spec和USD的SHA与formal manifest一致。USD为
`32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7`；
source50为`1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。
脚本按实际运行的`formal/source_snapshot`加载纯reward实现；所需standing模块亦核对SHA。

## 2. 并不是增强水平惩罚后的单变量退化

与source50自己的`standing_scissor_20261006/formal/source_snapshot/spec.json`
比较，pitch/roll都是原有的`-4*(angle/.12)^2*.01`、unconditional，**未增强**。
height权重3、width.04m、support.5、success_once10也未改变。
本轮取消了linear/angular/yaw settling、轮纵向几何、support balance、mirror、
leg-length balance、wheel difference成本，同时放宽在线成功条件，并将teacher
从来源链的update1500换成source50。因此不是只改roll权重的对照实验。

在source50的同一组已保存物理输入上，去掉每env第一步（缺少上一动作）、
不计成功/失败事件，原配方平均连续reward为 **-.022331/step**，新配方为
**+.019127/step**。差值+.041458主要来自取消linear settling成本-.034325，
其次取消轮纵向几何成本-.005545。pitch/roll成本在这次同输入计算中完全相同。
该计算覆盖8env的999步/个，采用已保存实际q/dq/action/effort/posture/geometry；
角速度方向只按成本所需的norm、canonical yaw及x/z norm等价构造。
这是reward符号/量级变化的证据，不是PPO梯度或行为因果分解。

## 3. 成功奖励、episode与验收存在具体缺口

在线`standing_success_mask`只检查当前pitch/roll各不超过 **.15rad**，
再结合height、tilt、contact、chassis条件，连续2s成功并立即终止。
它不检查完整评估中的 **mean abs pitch/roll<=.10rad**。
因此roll稳定在.13rad的episode可在线成功，却必然失败完整roll验收。
新100正是8/8稳态roll约.13rad、训练当次64个成功的实例。

| 更新区间 | 成功/失败episode | 完成episode均长s | 连续reward均值/step | 事件reward/step | value loss均值 |
| --- | --- | --- | --- | --- | --- |
| 1–50 | 1856/0 | 2.160878 | +.021557 | +.045313 | 1.116715 |
| 51–100 | 1920/0 | 2.161818 | +.016116 | +.046875 | .287083 |
| 101–150 | 1609/7 | 2.394350 | +.006080 | +.039265 | .527560 |
| 151–200 | 216/382 | 6.928896 | -.097957 | +.004341 | 7.807794 |

事件reward按`(10*successes-failures)/samples`算，原`weighted_mean`日志只含连续项，
**不含**这些事件。前100次完成3776个episode，全成功、无失败，几乎都在2.16s终止。
其成功事件贡献超过连续reward；训练很少经历长期自主保持，10s评估主动禁用成功reset。
这构成明确的目标和采样时间范围不一致；不能由此声称策略有意规避任务。

新100当次连续reward+.006784，成功事件64*10/8192=+.078125，总量约+.084909。
新200当次连续reward-.157412；pitch-.050479、roll-.133336、height+.026419、
support+.004471，且完成13个失败、0成功。roll cost是平方误差，均值不能用
mean(abs(roll))直接平方替代。其大幅负值与后期跌倒/长episode并存，不能证明梯度主导。

## 4. 来源保持及critic

formal严格加载source50 actor/critic/Adam，有效LR3e-5；optimizer初始state_count17，
没有清除first moments。来源之前的50次scissor训练是0成功、256失败，而新配方
前100次是3776成功、0失败。critic和Adam继承自不同reward/terminal分布，且没有
critic warmup；这是具体的分布迁移风险，尚未证实它是退化原因。

新100/200的BC raw MSE分别为.002198/.011199，normalized RMS约.04688/.10583；
weighted分别.00004396/.00022399。两者是不同的on-policy输入分布，不能当作
同输入跨模型误差比；不能把BC标量loss直接与reward均值或surrogate loss比较以断言梯度强弱。

retention只对actor均值生效；不保留critic、Adam或动作方差。它从8192个pre-action
样本中按step-major顺序取前256个eligible输入，在16个optimizer step中重复使用，
不是全rollout均匀采样，更不是冻结接管。eligibility为零命令、有效初始化、height.30–.40m。
在64env大量有效时只覆盖rollout前约4步。分布漂移到teacher不熟悉的状态时，
teacher在这些新输入上的输出也不具有已验证的稳定性保证。

value loss从新100的.446320到新200的10.438107；这是预测目标拟合变差的标量证据。
本轮`gradient_diagnostics=false`、未保存gradient payload；没有完整PPO
obs/value/return/advantage/log_prob/minibatch。**实际critic值分布、解释方差、
GAE/return分布及PPO-vs-BC梯度无法从现存日志精确恢复**，不能补造。
checkpoint权重变化和参数norm仅供身份/变化检查，不等于这些分布。

## 5. 100秒交接判断的修正

`durability_100s.json`绑定的确实是source50，8env各10000个保存样本。
调用链中的`evaluate_checkpoint`生成duration100协议，但Recovery入口通过`**unused`
忽略传入的`standing_protocol`。不过Recovery自己的评分调用明确覆盖
`steady_window_s=[window_start, seconds]`，本次就是 **[2,100]**。
最终`success_protocol.standing_protocol`却写回原spec对象，仍显示seconds10/[2,10]。
所以这是 **协议描述不实**，并非本次姿态实际只评分2–10s。

用冻结评分器离线重算[2,100]：**8/8通过**；除未保存原始pre-physics xy导致
无法精确重算的两个诊断位移字段外，全部保存评分指标与重算误差<=2e-6。
100秒稳态平均height .366650m，mean abs pitch/roll .022146/.072598rad，
height-in-range和dual-contact均100%。[2,10]重算指标与原JSON有差异，
进一步支持原结果实际使用[2,100]。

因此已有证据可确认：在本次R0 holdout、同物理契约、100Hz策略采样条件下，
source50连续100秒存活且通过全时段稳态水平协议。不是所有扰动、低趴恢复、
定点控速或每5ms限幅认证。100s净位移约5.67m，不是累计行程。

汇总`100-second gate=None`来自`stand_chain.reconcile_durability`只取
`standing_gate`，而结果提供`recovery_gate`。formal terminal的evaluation cases
也只有`standing_gate=None`；真实0/8结果应从原评估Recovery字段读取。
候选选择和退化早停实际使用Recovery accepted，没有证据说明此报告字段缺口改变了选模/早停。

另发现：source_eval中`gate_diagnostics_100hz`虽有字段名/数组，却全部填零；
CLI `--diagnostics`开启采集，但runtime只有`recovery.gate_diagnostics=true`才填充。
本spec为false。不能将该数组的零当作真实速度/角速度，control和posture证据分别核查。

## 6. 验证、范围与后续约束

40项CPU检查通过：`test_standing_survival_level.py`、
`test_standing_height_independent.py`、`test_standing_bc_diagnostics.py`、`test_stand_chain.py`。
plan-only source_eval结果cpu_valid=true、READY_NEEDS_AUTH、phase budget exhausted；
simulation0、ppo0、files_written0。未恢复任何旧链。

复现离线报告必须选择新的output，工具拒绝覆盖：

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  scripts/audit_recovery_survival.py \
  --run runs/recovery_survival_level_from50_20261006 \
  --output runs/reviews/recovery_survival_20261007_NEW/offline_audit.json
```

优先待处理的是成功奖励/短期reset与长期均值协议的缺口；新的recipe需要独立spec，
不能通过改旧gate恢复成绩。其次是同输入的teacher保持、critic及真实PPO梯度诊断。
源码报告可后续小范围修正为序列化effective protocol并按task取gate，另补诊断validity；
本次只完成核查与corrected review，没有改变下一次runtime行为。
任何物理测试或PPO都仍需新的明确授权；不从new200自动续训。
