# Recovery动态过渡：短时序与测量接口CPU准备

2026-10-09用户同意继续准备。新增明确实体关节目标时序、有限候选与测量字段契约，不启动仿真/GUI/PPO，不暗写常规CommandEnv。

## 六条时序

从保存合法Swing fulljoint出发，同一目标终点由收缩偏移a=.30rad、转动偏移b=.20rad组合为四主动轴[a−b,a+b,−a+b,a+b]。采用quintic smoothstep连续目标，起止一阶二阶导数为0；收缩与转动各持续120或240ms，收缩开始相对转动延迟0/40/80ms，形成六候选，允许过程重叠。

纯CPU按100Hz实际命令时间重新解被动闭链；六条全部通过closure≤1e-4m、USD jointlimits、当前reference0/legscale1.6/action±1包络。target函数越界明确拒绝，不靠clamp掩盖声明无效。端点双腿约.297m且朝向仍非完整DrawBack；诊断覆盖局部支撑/收腿前段，不保证完整起身。

1ms目标曲线数值速度峰值约3.13–7.81rad/s、加速度约39–200rad/s²（按各通道/候选报告）；这是命令导数，不是实际电机速度/加速度或已验证的可执行能力。当前40Nm限矩不增，不能将目标速度直接当碰地冲量。每条固定root路径均有理想planegap为负，需真实机体运动；不能当合法静态reset/无需支撑的自由运动。

## 显式动作边界

诊断起始时钟从合法初始化结束后的首次受控transition开始，不能用启动wallclock。四腿在声明区间由显式diagnostic target覆盖，两个轮继续同一冻结boundedmeanactor，避免同时加轮制动或置零；未实际执行。记录actionorigin与6Doverride_mask，不能称这些动作是RL输出。时序结束最后target最多保持100ms后停止trial，不自动跳回actor或切LQR，避免未验证目标突变/接管掩盖失败。

初始姿态、所有动作尺度、physics1ms/PD5ms/policy10ms、40/5.5Nm保持。fault/closure>.005/原tilt终止/非法initial/target越界/预算触顶退出。不能把站立level .18rad直接新增为本诊断早停阈值。拟议首块6候选、每trial含init最多3s、总wall900s、详细128MiB，均是未授权草案，不是可直接reserve的budget。

## 具名测量契约

新增pureCPU validate_sample接显式joint_names/body_names，核对全jointq/dq、rootstate13、target6、requested/clipped/appliedPD6、override6、episode与时钟/actionorigin。PD rate5ms、physics rate需具名body的world3Dcontactforce和明确dt=.001；缺字段/错误尺寸/非有限/伪5ms当1ms拒绝。不从文件/Isaac/env读取，字段生产属于runtime适配层。

不能用已有100Hz wheelcontactforce替代1ms接触冲量或全部连杆支撑力。真正physics contact生产者、force方向/单位/filter/body匹配、与engine更新时序对齐、fault保存和清理均未完成，当前runnable=false。接触积分只在确认为力且时间支持正确时按F*dt定义，不用传感器平均值假装瞬时峰。

## 下一工程步骤

实现隔离诊断adapter：显式动作来源、命令调度、substep测量与pre-reset保存，沿用共享CommandEnv物理控制与supervisor预算监控，默认关闭且不得影响训练RNG或optimizer。需CPU假engine/异常清理测试和真实字段可用性检查，再准备独立可审查run spec/ledger以及授权。现有六条候选只研究局部动态可达性，不提供完整Swing到DrawBack轨迹；后续完整路径需根据物理结果修改，不盲目追加速度或幅度。

本次不要求用户现在批准未完成的runtime接口，也没有用同意CPU准备作为物理运行许可。没有新成功轨迹、保持策略仍认证B25。

## 产物和验证

新增src/native_stand/recovery/dynamic_diagnostic.py（纯CPU target/encode/measurementcontract）、scripts/prepare_recovery_dynamic_timing.py、tests/test_recovery_dynamic_diagnostic.py（PORTABLE）。2tests通过：quintic端点/重叠/包络拒绝，以及具名measurement字段/缺接触/错误dt拒绝。六条真实USD命令采样点闭链审核完成，输出isolated/recovery_dynamic_timing_draft_20261009/timing_plan.json绑定spec/pose/USD SHA。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX、ARCHITECTURE与本报告。未改runtime/旧run/raw/specledger/checkpoint/资产，无仿真/PPO/通知/清理/Git提交。
