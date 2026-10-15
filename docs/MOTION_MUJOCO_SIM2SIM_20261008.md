# B250 native → MuJoCo 首轮迁移诊断
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


**后续更正**：首轮actor观测坐标基接错，0.18秒失败不能用于判断B250迁移能力。
修正后11命令各完成30秒。最终解释与证据见
坐标修复与配对复盘（该报告已按文档整理删除，长期结论见 TRAINING_EXPERIENCE_REUSE.md §12），以下保留首次事实。

2026-10-08。用户明确要求MuJoCo sim2sim验证，参考wheel_leg_sim2sim；
只编辑native项目，参考仓库与历史模型只读。没有启动Isaac/PPO/GUI，没有查询或改动后台训练。

## 实际结果

run：`runs/2026_10_8-16_58__motion_b250_mujoco/`。
manifest.json保存输入文件/mesh SHA、坐标变换、关节绑定、传动、物理差异；
command_00–10.json保存每policy10ms的控制/姿态/轮心/接触/几何轨迹。
terminal_report.json、budget.json、post_validation.json及report.md记录终态与消耗。

流程COMPLETED，但all_passed=false，不是运动能力通过。
0/±.5/±1/±1.5/±2/±2.5共11个目标，每个请求30秒、实际0.18秒：
主动腿位置超过native .5rad安全阈值，JOINT_SAFETY停止。
所有案例都在2秒零命令准备段内，轨迹相同；这是重复的同一起点失败，
不是11个独立命令验证，也没有保持段速度/MAE/停车结果。缺值均null。

|指标|实际值|
|---|---:|
|每项physics steps|180（请求30000）|
|累计physics steps|1980|
|累计policy samples|198|
|测试主体墙钟|0.267317秒（不含外层进程初始化/CPU plan）|
|末端roll|−0.019062rad|
|末端pitch|−0.521851rad|
|峰值tilt|0.522167rad|
|末端水平轮心前后错位|−0.198543m（native body heading轴）|
|闭链最大残差|0.00126433m|
|两轮PD饱和比例|各1.0|
|实际执行器关节输出与clipped PD请求最大误差|0Nm|

没有nonfinite或超过.005m闭链阈值。末端偏斜主要是pitch，不能把这个MuJoCo
结果当成用户在Isaac GUI观察的roll/5cm现象，更不能替代其量测。
关节限矩严格40/5.5Nm；轮motor控制值除以传动15.7647058824，
5.5Nm输出对应motor ctrl约.348880597，不使用原runner的更高轮输出限矩。

## 模型与来源

B250：`runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`
SHA：`5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。
使用其冻结source_snapshot/spec.json，严格150D actor权重，CPU确定性推理，
不修改checkpoint，不恢复/构造optimizer。critic无需推理，不进行训练。

参考MJCF：`/home/kellen/wheel_leg_sim2sim/assets/wheeled_infantry.xml`
SHA：`663e121ef9aed4bfab09ff0d3d98321b7ce77d80b63584235e4da691bd3aebf3`。
完整模型nq45/nv44/nu6/neq4；不修改XML、compiled model参数或外部源码。
7个主要刚体零位位置对应USD（浮点误差约1e-16m），质量接近一致；
四connect连接点对应native，初始closure约1.18e-16m。

原参考runner是Fudan虚拟腿/ONNX路径，动作尺度、clip、控制和native不同，
没有直接使用或复制它的虚拟状态/雅可比扭矩映射、equilibrium、qfrc补偿或LQR。
新工具复用几何命名与固定CAD→native坐标基，直接读取实际主动joint q/qdot。
零位XML root roll90，经基变换后得到native reset yaw90，初始gravity=[0,0,-1]。
这只是静态基核验；运行中与PhysX的关节符号、root状态/观测等价性尚未用配对状态认证。

## 契约与模型差异

适配器保持：25D physical frame＋125D history、oldest→newest、reset重复5帧、
6D left-first实体动作、clip[-1,1]、leg .5rad/wheel100rad/s、
physics1ms/PD5ms/policy10ms、reference joint0、同一PD公式、40/5.5Nm限矩。
命令按2/8/8/8s平滑时序，保持10–18、停车26–30，height command.4。
无补偿、无外力稳定、无隐藏zero gate。

保持原MJCF意味着仍有明确差异：

- 地面friction=[1.1,.05,.01]，native配置为static/dynamic .5/.5、restitution0；
  MuJoCo的三个friction分量语义不同，不能逐项等同。
- MJ主动腿阻尼.08、轮.01；各主动DOF armature .01；native对应运行值尚未完整认证。
- MuJoCo软connect/contact与PhysX求解不同；碰撞proxy、惯量全量、guide轮接触未做严格parity认证。
- 相同零位位置/质量不证明动力学完全一致；此结果不能判定native B250无能力或物理不可达。

本轮没有为了通过修改这些参数，也不把失败归为已经证实的策略根因。

## CPU与身份验证

- 新适配器2项CPU测试通过；含键盘相关回归共7项通过（时间见实际命令输出）。
- plan-only真实加载checkpoint/MJCF，逐输入SHA核验，simulation0/files_written0。
- 实际MuJoCo已运行；post_validation确认所有输入SHA仍一致、执行器力矩转换误差0。
- 在线/离线PPO更新0。没有GPU依赖、训练额度转移、通知发送或Git提交。

新增`scripts/validate_native_mujoco.py`、`tests/test_native_mujoco_adapter.py`及本报告；
更新TOOL_INDEX、ARCHITECTURE、STATUS。已授权的Motion训练链未读取进度或修改。

## 下一步唯一优先项

先做**PhysX/MuJoCo配对状态的观测与执行器响应parity**，从零命令首个policy窗口开始，
核对root坐标基、四腿joint方向/零位、轮轴符号、history和确定性actor输出，
再核对相同PD请求下的响应差异。已有MuJoCo轨迹够定位失败窗口，不能先追加高速测试。
若需新增Isaac采集或修改诊断模型，单独声明范围/身份；不改训练USD或放宽安全gate。
暂不宣称sim2sim通过，不进入MuJoCo高速/yaw认证。
