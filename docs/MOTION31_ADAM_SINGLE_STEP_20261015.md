# Motion31固定batch离线Adam单步对照（2026-10-15）

## 本轮结论

单步结果**不支持“去掉−1.5梯度即可保护旧能力”**。A完整batch对旧五命令的固定样本surrogate总体改善；B消融−1.5 Actor贡献后，旧任务总体反而微小下降。−1.5确实改变了更新方向和裁剪强度，但“主导”不等于“有害”。本轮没有新仿真或online PPO，不导出训练模型，不从750/1000续训，不直接修改归一化/Adam/奖励或重开长训。

这不是运动验收：固定输入上的动作或surrogate变化，不能推断实际vx、pitch、roll、接触或腿几何会改善。

## 输入与唯一对照变量

- 数据：`runs/2026_10_15-16_00__motion31_u1600_frozen_advantage_probe/rollout.npz`，SHA256 `b92f0bf22fcac50147c07641ff5e0d1863531a918b033c2b85ff2314d889cfde`。
- 来源：`runs/2026_10_14-21_23__motion31_posture_quality512_v3/formal/model_update_1600.pt`，SHA256 `83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`。
- 每臂从同一Actor/Critic/Adam/std独立恢复；LR3e−5、Adam β(.9,.999)、全batch65536、相同returns和global normalized advantage、Actor/Critic分别裁剪maxnorm1。
- A：全部七cohort参与Actor surrogate。
- B：只将−1.5 Actor surrogate贡献乘0；不重填样本、不重新归一化、不改变65536分母；Critic仍使用全部样本。
- 每臂仅1次CPU Adam step；Critic参数改变量逐项完全一致，std未变。全局CPU old log-prob由来源在精确记录输入重新前向，初始ratio严格为1，避免CPU/GPU浮点差伪装更新；不声称bit-exact历史重放。
- 熵项保留，但固定Gaussian std使其无Actor均值梯度；无BC/retention，Actor/Critic无共享参数。

## 结果

`clipped_surrogate_gain`越大表示当前固定样本Actor目标改善；不是机器人运动奖励或能力通过。

|指标|A完整batch|B消融−1.5|
|---|---:|---:|
|Actor梯度范数，裁剪前|2.671526|.288576|
|Actor裁剪比例|.374318|1|
|Actor参数变化L2|.00088517|.00033465|
|旧五命令surrogate gain|+.000010710|−.000001732|
|旧五命令KL均值|.00023431|.00012739|
|全七命令surrogate gain|+.00033548|−.00005373|
|当前臂Actor梯度点乘Adam参数变化|−.00033467|−.000001713|

两臂参数更新cosine约.339885。两臂各自的gradient·delta都为负，符合本次局部下降方向；不证明未来多步PPO更新或物理响应一定正确。

|目标vx|A surrogate gain|B surrogate gain|
|---|---:|---:|
|0|+.000006744|−.000010540|
|+.5|+.000014136|+.000005500|
|−.5|+.000032933|+.000006057|
|+1|+.000010441|+.000009616|
|−1|−.000004095|−.000004613|
|+1.5|−.000011597|+.000015124|
|−1.5|+.001765133|−.000295930|

A改善五旧命令中的四组，但−1略差；A的+1.5略差而−1.5明显改善。B降低整体分布变化，并改善+1.5，但zero和−1略差。没有一臂逐命令全胜，不能据此宣称“减少新任务就一定防遗忘”。

## 证据等级和下一优先

- 已确认：单batch下−1.5贡献明显改变梯度裁剪及Adam更新方向；CPU单步目标结果如上。
- 本批不支持：global centering把旧正A翻负；去除−1.5即可改善所有旧任务；单步surrogate符号错误。
- 待验证：多minibatch/多epoch后发生累积漂移、Critic对新失败状态适应不足、任务相对权重随训练演化。
- UNKNOWN：历史update250–1000实际梯度分布、Adam继承是否是因果根因、这两种离线更新的真实运动效果。

下一优先仍在固定数据上检查完整一次PPO update的16个optimizer step，冻结同一minibatch排列，区分单步结果与多步累积；不是直接启动新长训。本轮只执行已同意的单步对照，未执行完整16步重放。原formal有5次Critic适应，本次没有重现；一批1.28秒数据也不能覆盖全部episode或远期信用分配。

## 可复用工具、验证与消耗

新增`scripts/audit_motion31_adam_step.py`和`tests/test_motion_adam_step.py`。只读原run/checkpoint，拒绝覆盖新输出；完整六通道动作变化、KL、ratio和输入SHA写入新审计目录。不修改训练实现或物理/奖励配方。

CPU命令：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/test_portable_cpu.py`，**481 passed、8 skipped、4 warnings**；定向8 passed。测试覆盖同分母消融、Critic完全一致、Adam缺失拒绝、来源/RNG不变、已有输出拒绝和NumPy RNG元数据比较。

第一次两臂计算完成后，报告校验复用的tree_equal不支持checkpoint NumPy RNG数组，报ValueError；新增局部source_equal及回归后重算。来源文件从未写入，失败记录保留：`artifacts/2026_10_15-16_21__motion31_fixed_batch_adam_ablation/failed_attempt.json`。

最终证据：`artifacts/2026_10_15-16_22__motion31_fixed_batch_adam_ablation_retry/`：

- `audit.json` / `audit.md`：成功的2臂单步结果；
- `execution_manifest.json`：累计真实batch CPU optimizer **4 step**（失败报告前2＋成功2）；
- `cpu_tests.txt`：全CPU回归输出。

成功对照本身约1.60秒CPU。新增Isaac/GPU墙钟0，online PPO0，checkpoint导出0，不占用/重置任何在线账本，没有新运行授权或Git提交。改动清单为上述两个Python文件、本报告、STATUS、TOOL_INDEX。
