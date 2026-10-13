# 轮mean辅助系数独立量级审核

## 范围

用户同意上一轮“先独立系数量级审核，再决定是否验证更强固定系数”。本轮CPU读取B25 checkpoint、已授权完成的真实输入采集和上一formal50 metrics。没有仿真/在线PPO，没有修改/导出checkpoint，没有运行新spec或通知。5个候选各做一次CPU反事实Adam步骤（包含lambda0控制），不是PPO更新/历史minibatch重放。

脚本scripts/audit_recovery_mean_coefficient.py；身份/全部数字isolated/recovery_mean_coefficient_audit_20261008/audit.json。actor/critic/17Adam名映射严格匹配，各候选从相同B25及Adam状态重新加载；所有critic梯度None、actor传入梯度显式0。lambda0用于扣除来源Adam历史矩在零梯度时的参数移动。原始state_dict仅内存复制，没有写模型。程序恢复CPU RNG。

输入为各组首.30秒实际pre-action150D，Swing240样本；梯度分母使用上一真实formal整体eligible质量23.501%的代理值，不冒称重建了当前rollout。真实PPO梯度向量未知，不能进行PPO/aux方向相加的历史重放。

## 梯度与单步读回

| lambda | CPU辅助actor norm | 根据上一实际读回线性估算aux/incoming clipped norm |
|---|---:|---:|
| .001 | .003154 | .316% |
| .01 | .031542 | 3.157% |
| .03 | .094626 | 9.470% |
| .1 | .315419 | 31.566% |

不是不同lambda实际PPO训练结果；输入/网络变化、Adam和梯度组合改变后比例会变化。

lambda=.03相对lambda0 Adam单步控制，Swing左右轮mean平均变化+.000503/+.000460（负mean向边界内移动）；最大任一输出变化.000580。DrawBack最大输出变化.000197、R0 .000109。旧组mask为0但共享特征导致输出仍变化；不能称旧组无损。各候选单步后Swing轮仍100%mean越界，不能保证25更新能解除裁剪或起身。

lambda.1旧组变化约为.03的3.3倍，预计辅助占比约31.6%；没有真实合成方向/物理结果，不选它作为首个固定候选。选择.03为可审核中间量级，仅比原弱项增加系数，不加std/奖励/网络改动。

## 下一具体候选与建议预算

建议版本化新声明（原v1严格lambda.001不改）：lambda=.03、margin=.9、同固定当前rolloutbatch/全部受控分母/每optimizer step应用/PPOclip→aux→actorreclip。从认证B25严格继承全部actor/critic/Adam/std；保留Swing/DrawBack/R0固定26/25/13，旧reward/150D/新USD/control/termination/gates。只改辅助系数，不叠B、不清Adam、不继续失败latest。

新块建议source≤900秒/PPO0、smoke10≤900秒、formal≤25≤3600秒；formal10/25完整三组，最大35实际更新/286720样本、phase墙钟5400秒、chain5460秒含60秒清理。独立spec/ledger及完整发布SHA，原账本不复用。smoke仍需实际eligible非零梯度；读回真实aux/incoming/combined norms、mean/std/sample clip、三组高度/入口/保持。

原DrawBack/R0保持和Swing进展共同选模；不能仅clip下降通过。实际合成异常或连续两次旧组退化停止，不自动加lambda/预算；完整三组通过及时保存复验。若有非零且足够量级aux仍不移动mean，优先核查实际更新方向和Adam影响；若解除clip而无起身进展，再转向独立reward/观测候选。

该runtime预算/系数尚未获本次明确运行范围批准；当前仅有CPU审计JSON和设计，不发布伪造可提交spec。后续已有用户自动通知并唤醒本会话授权，新的运行spec应冻结当前负责人session为通知目标并启用，不能再次默认为禁用；不改旧run通知记录。

## 验证

脚本实际执行成功；输入SHA核验、参数名映射、相同初始化控制、零系数Adam对照均实际运行；5次CPU反事实step、在线PPO0、导出模型0。结论为局部输出和量级证据，不是收敛/安全认证。AST/diff验证通过。
