# Recovery腿执行事件对齐：右腿不收短与首步发力

2026-10-09用户同意继续离线分析。依据10_58 boundedmean短训来源/new10/new25三份完整raw（各Swing/DrawBack/R0、8env），只读原证据；无仿真/采样/optimizer、新reward或控制修改。

## 已核验的序列

三候选Swing全部8env：首个受控policy-step之后，tilt在recoveryclock .05s首次超过.18rad，.06s首次出现任一轮接触力≤2N。tilt先于该接触门槛事件，但时间顺序不是因果；.18是站立水平指标，此处不是把实际terminal阈值改成.18。最终terminal tilt约1rad、.30–.33s结束。

source env0第一受控snapshot，实际post-step腿q [1.134,−1.384,−1.131,−1.398]，目标[−.393,−.254,+.452,−1.600]rad；三通道误差约1.53/1.13/1.58rad。最新heldPD request [−90.51,+66.51,+93.20,−14.80]Nm，实际limit后[−40,+40,+40,−14.80]Nm。new25仍[−88.16,+65.05,+94.12,−14.87]→[−40,+40,+40,−14.87]。首步冲击模式并未被25更新消除。

## 右腿不是不动，而是保持长腿整体摆动

source env0右主动q从[−1.1306,−1.3983]到约[−.1599,−.4273]rad，两个通道均显著运动。右q0−q1范围仅.26738–.26851rad，left相应差值1.74180–2.51851rad。new25右差仍.26751–.26883rad，左1.66713–2.51852rad。右腿hip→wheel距离最小约.37599m，左约.36308m，说明两个右关节运动没有形成明显相对构型收缩，几何上主要保持伸长摆动。

这是实体主动关节与原生wheelcenter实测关系，不把sum/difference改成虚拟腿控制或认定某通道失效。右两个关节在closure作用下同向运动可能涉及支撑/约束/力矩，尚无子步/完整passive状态以唯一解释。不能仅从右active2目标负值与实际正向运动断言PD接线反号，因为闭链约束耦合、当前heldPD与endstate时间不同。

## 三种限幅必须区分

- **动作裁剪**：source env0四腿raw越界比例[0,70%,0,10%]；new25[0,39.39%,0,15.15%]。这是Gaussian动作[-1,1]裁剪，尚不等于机械限位。
- **关节目标限位裁剪**：三候选Swing各8env的target_before_joint_limit与target_after均无差异，比例0。不支持“新增USD主动关节目标被限位挡住”这一解释；不能据此排除所有被动branch/物理接触限制。
- **PD力矩限制**：new25 env0四腿policy-held40Nm占比[12.12%,3.03%,30.30%,0]，右第一主动通道约30%，第二没触40Nm。右腿并非两个电机都满矩；不授权加力矩或补偿。

原applied torque与latestheldclip已保留，但100Hz末状态不能核准所有5ms PD/1msphysics子步，不能从postq直接宣称exactprecontrol误差或force因果。

## 与成功旧任务比较

DrawBack起步也存在大目标误差：source env0第二通道约−1.52rad、request≈−89.86Nm并限到−40Nm，仍可成功进入并完整保持。故“首步饱和”并非单独充分失败原因；区别是初态构型和闭链作用下实际运动方向/收腿程度。DrawBack实际起点长度约.1526/.15米，Swing约.376米；不能复制其腿目标并认定可在Swing起点恢复。

DrawBack/R0入口前短暂失触也不等于旧任务完整保持失败。本次旧任务保持窗口通过，分析不混用入口事件和入口后1000样本证书。

## 下一最小工作

先做CPU原生闭链构型可达性与目标方向审核：以保存Swing全关节/真实USDbranch为起点，在现有实体主动关节范围内小幅扫描左右active q，解闭链、核对wheelcenter/长度与closure、机械限位/理想碰撞，判断哪些实体目标确实可收短右腿，以及当前目标偏向哪里。对照DrawBack合法构型，明确仅几何可达而非动力学可恢复；不生成隐藏控制轨迹/施加力/改变初态，不做runtime。

如果当前可行范围里有收短方向而policy与实际受力未利用，再准备最小有界子步诊断，记录pre/post全关节及constraint/contact/PD；若仅静态扫描无可行路径，不将其视为完整不可能性证明。之后选择腿探索/奖励或有证据的课程单变量，不能盲目同时加对称、actionbias与制动。当前无新仿真/PPO授权。

## 产物与验证

新增`scripts/audit_recovery_leg_execution.py`和`tests/test_recovery_leg_execution.py`（PROJECT_DATA），2tests passed，验证trace对齐拒绝以及action/jointtarget/PD三类限幅和事件先后独立统计。审核输出`isolated/recovery_leg_execution_complete_audit_20261009/audit.json`，含输入SHA、三候选三组24env摘要及首100ms必要事件，checkpoint SHA核验。初版输出保留，无覆盖旧证据。
更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX和本报告。未改源码控制/旧raw/spec/ledger/checkpoint/USD，无仿真/训练/通知/清理或Git提交。
