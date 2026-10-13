# Motion旧端点rehearsal终态复盘

事件8cb50f802e7871b821859052。一次只读复盘已完成，未续训、未模拟、未改历史证据。
run：runs/2026_10_8-14_56__motion_old_endpoint_rehearsal。
新比较输出：isolated/2026_10_8-17_29__motion_rehearsal_terminal_review。
优先读comparison_corrected.json/md与sampling_budget_review.json。
审计器旧版遗留了上一短链-2.5早终止的固定文字，本次移除硬编码并另存corrected输出；
原比较数值和原run报告没有覆盖。本次所有25/50逐环境均完整30秒。

## 终态与预算

链COMPLETED，formal STOPPED_BOUNDED，accepted_candidate=null。
实际smoke1/8192samples、formal50/409600samples，合计51/417792；无剩余formal额度。
整链7200.957s（约2h00m01s），formal4946.948s（约1h22m27s）。
ledger source_eval1/smoke1/formal50全部结算，无RUNNING attempt，无重复提交/额外预算。
formal early_stop_reason=stage update budget exhausted；task learned_failures=2也同时存在。
准确表述是“达到50-update上限，并且连续检查仍有旧能力失败”，不是提前中断。
report标题Native standing/10-second accepted是通用旧文本，实际Motion11命令各30秒；
不能拿报告标题解释实际协议。没有100秒durability或三seed认证。

## 身份与唯一变量

来源B250 SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。
新formal25 SHA24cde085f2f23d08162bdeeae88460e9bb9ee758eaa3e4ed5a7b395c3a7d92c5。
新formal50 SHA36421729b9cfbeb48f2ab00d09fd8e4a925321f827c45a414b99c552005109ce。
勿与上一短链formal25/50、历史new250/500混称。
冻结reward/PPO/action/control/ground/observation/history/termination与上一短链逐字典相等，
schedule仍1/2/24/2s，实际optimizer LR3e-5。不启retention、不改advantage normalization。
训练变量是reset类别权重：zero25%、旧八端点各6.25%、新±2.5各12.5%。
scoring窗口/阈值与来源一致，调度/diagnostics元数据不同保留原SHA，不伪称完整协议SHA相同。

## 逐命令结果

每格MAE为8env均值，通过数按原始逐环境gate计算；全部direction/contact检查通过。

|command|B250 MAE|new25 MAE/通过|new50 MAE/通过|
|---|---:|---|---|
|0|.0081|.0119 /8|.0188 /8|
|+.5|.0331|.0132 /8|.0402 /8|
|-.5|.0448|.0201 /8|.0145 /8|
|+1|.0400|.0346 /8|.0238 /8|
|-1|.0710|.0412 /8|.0286 /8|
|+1.5|.0366|.1489 /8|.0670 /8|
|-1.5|.0599|.2255 /8|.1742 /8|
|+2|.1743|.3752 /0|.2315 /8|
|-2|.1684|.4124 /0|.3608 /0|
|+2.5|.4016|.7201 /0|.5052 /0|
|-2.5|.3434|.6107 /0|.5770 /0|

new25为56/88，new50为64/88；两次均没有完整11命令通过。
new50实际+2=2.2295/-2=-2.3608，+2.5=3.0052/-2.5=-3.0770m/s。
对应失败都是hold_absolute_error，没有独立验收runtime fault/提前终止。
new25/50最小接触率1.0，最大tilt约.3472/.3427rad，closure最大约46.24/45.31微米，
policy采样最高饱和比例.000333。训练期间另有15次joint_safety episode终止，
不能把评估安全结果扩展成训练从未失败。训练termination归因到具体cohort缺完整证据。
roll及轮心几何仍未被Isaac原始轨迹记录，MuJoCo量测不能替代此运行。

## 与上一短链的同预算观察

在相同formal50处，新rehearsal相比上一短链：

- +2 MAE .5820→.2315，0/8→8/8。
- -2 MAE .5687→.3608，仍0/8。
- +2.5 MAE .9742→.5052，仍0/8。
- -1.5 MAE .3149→.1742，0/8→8/8。
- -2.5本次完整30秒；上一短链约10.3秒joint_safety结束，两者MAE不能当等窗口终点直接比较。

这支持“本次比例调整后有部分保持改善”的现象，但不是多训练seed重复验证；
采样随机流与状态访问也随概率改变，不能宣称唯一因果或根因修复。
±2增益B250/new25/new50=1.0830/1.1969/1.1476，new50有所回落，仍高于来源；
±2.5增益1.1490/1.2662/1.2164。zero bias .0081/-.0119/-.0188m/s。
每环境速度/MAE/姿态/接触/停车/位移与failed_checks在corrected JSON，不能拼不同模型的成功点。

## 实际采样与吞吐

409600真实formal样本的cohort占比：zero28.98%；旧合计55.88%；新合计15.14%。
新+2.5=10.97%、-2.5=4.17%；旧+.5=3.88%、-.5=10.51%，不是严格正负均衡。
原因机制是reset随机类别采样和不同episode终止/持续时间，本轮未证明各因素的贡献。
实际保持段占比75.52%，没有“主要只有准备段”的证据。
formal耗时rollout444.43s、PPO1.80s、评估4484.51s、保存11.75s，
评估占formal墙钟约90.6%。慢主要是独立评估，不是optimizer更新耗时。
不能为了吞吐把完整评估缩短或只看reward；可后续研究并行不同命令而保持8env/完整窗口。

## 决策

本次不成功获得±2.5阶段候选，不做三seed，不升±3，不从new50续训。
继续保留完整B250为来源/回退；new50仅为诊断候选，不是“最强已认证模型”。
**下一项优先建议**：先把同一16/旧各4/新各8配比做成明确固定64env槽位的
单变量采样机制对照，保留B250/reward/width/PPO/时相/物理，验证实际正负样本覆盖。
这是随机→固定槽位的新机制试验，不是本次配比已严格执行，也不保证改善；
CPU先测配额、reset、保持段计数和早终止语义，再提独立预算/授权。
暂不同时缩tracking核、改归一化或增加几何惩罚。本通知不授权新实验准备或运行。

## 本轮工程及边界

更新scripts/audit_motion_response.py以兼容scoring/schedule拆分的只读元数据，
并去掉上一run专属终止文字；新增本报告与只读审计输出，更新STATUS。
不改原run/report/spec/ledger/checkpoint，不启动Isaac/MuJoCo/PPO，不检查进程/GPU，不提交Git。
