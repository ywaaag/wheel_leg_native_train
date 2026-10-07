# Recovery自主站稳配方

2026-10-03。用户已明确授权基线300秒→smoke3次/300秒→formal1000次/4小时。
此文件为配方说明，实时执行状态以根STATUS和当前run原始JSON为准。

## 任务与来源

从Recovery update1500严格恢复actor、critic、Adam，实际LR仍为3e-5。
来源SHA：`cb5ccd4307a3b9c799bd8543b9c7b9f56eb239c1637534b81852f70b82fb06f5`。
新环境完整reset，不恢复PhysX中间状态；新任务下critic仅作初始化。
初态仍是manual0001低趴姿态，不扩大随机腿姿族。

Recovery自行完成抬升、减速、保持；成功前没有HANDOVER或STAND_VERIFY。
冻结STAND文件保持不变，当前环境仍可计算其诊断输出，但不执行其目标。
保持25D/125D/150D原生接口、1.6rad腿尺度/100rad/s轮尺度、1/5/10ms时序、
plane0.5/0.5/0材质、40/5.5Nm限矩及全部闭链/非有限/关节安全保护。
不增加完美高度或世界速度actor输入；仿真真值仅用于reward与成功判定。

## 新成功协议

同时满足以下条件并连续保持2.00秒：

- root高度0.38–0.42m；不是COM高度。
- 倾角<=0.20rad。
- 三维机身线速度模长<=0.05m/s。
- 三维机身角速度模长<=0.30rad/s。
- 双轮合力模长各>2N，机身理想几何净空>=0.25m。
- 无运行故障、禁止接触或任务失败。

任一稳定条件中断就重计2秒；不是拼接片段。达到条件时发一次+10，
以Recovery自主完成结束episode；15秒起身超时仍是普通任务失败。
STAND接管所用的0.15rad角度、两策略目标差不限制自主成功。
两秒是训练成功定义，不等于10秒/100秒站立、扰动鲁棒性或已完成STAND交接。
旧协议仍要求冻结STAND接管后5秒，旧模型结果不追溯重判。

## 奖励修改

保留原低位线性lift、upright、effort、action_delta、joint_margin与事件权重。
只替换旧收稳成本：

```text
g(h) = clip((h-0.32)/0.06,0,1)
linear_cost  = g(h) * (sqrt(1 + ||v/0.10||²) - 1)
angular_cost = g(h) * (sqrt(1 + ||ω/0.50||²) - 1)
reward += dt * (-0.10*linear_cost - 0.20*angular_cost)
```

不对成本设置硬封顶；高速区近似线性增长、低速区为二次型，零速附近斜率趋零。
低趴0.168m时g=0，不压制早期抬升。以0.21m/s、2.45rad/s仅单轴运动估算，
完全激活时每秒成本约-0.933，单policy步约-0.00933；这些是公式fixture值，
不是从新模型实测。原稳定抬升/upright最多约3.5/秒，没有假定新权重必然收敛。
一并改变任务成功语义和成本形状，因此不是单变量消融。

本版不同时加入轮速平方成本或标称姿态项。实际轮速不是滑移，零轮速目标不是锁轮；
STAND也没有唯一已验证“完美默认关节角”。必要滚动与差动要保留。
本版未改变lift的高度封顶；如果出现高位静止但高度过冲的局部最优，再独立研究
高位目标高度项，不隐瞒这一局限，也不声称保证形成稳态吸引子。

## 实现与验证

- domain.py：自主连续保持FSM、full-body稳定条件、Pseudo-Huber成本。
- runtime.py：新spec选择自主成功；旧spec行为路径保持。
- train.py：GPU统计包含settling_linear/settling_angular，每update搬运。
- recipe.py/selection.py：显式自主2秒协议，避免把它认证为旧5秒STAND接管。
- validation.py：成功模式与冻结协议验证；play.py显示正确任务名称。
- tests/test_recovery_autonomous.py：中断重计、局部reset、故障/timeout优先、
  成功只发一次、竖直速度/自转拒绝、无封顶/正负对称、新旧候选协议区分。

31CPU tests通过，1项历史preflight排除；新CPU plan通过。CPU不代替物理验证。

## 命令（项目根目录，Conda解释器）

CPU诊断计划，安全且已验证，不写run、不导入Isaac：

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.recovery.probe \
  --spec configs/experiments/recovery_self_stand_from1500_20261003/spec.json \
  --output-dir runs/recovery_self_stand_from1500_BASELINE \
  --mode checkpoint --seconds 18 \
  --checkpoint runs/recovery_settle_from433_formal_20261002b/model_update_1500.pt
```

获批后以相同参数加`--run`，外部275秒TERM/15秒kill预留清理。
随后smoke/正式使用唯一launcher；无`--run`为plan：

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/launcher.py \
  --spec configs/experiments/recovery_self_stand_from1500_20261003/spec.json \
  --phase smoke --output-dir runs/recovery_self_stand_from1500_SMOKE
```

推荐新预算：基线300秒/PPO0；smoke3次/300秒；formal最多1000次/14400秒，
64×128，正式8,192,000样本；总墙钟上限15000秒。每100次checkpoint、每500次完整
评估，最后一次评估计入formal墙钟。新账本已有明确授权，旧额度不自动转入。
获批后detached流程连续推进，只在故障或预算条件停止，报告/HAPI通知不授权续训。
