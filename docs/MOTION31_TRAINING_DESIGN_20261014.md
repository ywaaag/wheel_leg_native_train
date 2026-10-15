# 31D Motion：独立训练版本与 CPU 交付

状态：CPU 实现与未授权声明；没有启动 Isaac、PPO0、online PPO 或通知。工程回归不等于运动通过。

## 来源与目标

阅读依据：`PROJECT_MASTER_PLAN.md`、`参考文献.md`、`TRAINING_EXPERIENCE_REUSE.md`，以及迁移和五命令原始评估。来源为 `isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt`，SHA256 `a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`。

该文件只有迁移 Actor/std，没有 Motion Critic、Adam 或可恢复训练 RNG。原五命令 PPO0 的40/40连续生存不等于站立质量或运动通过：零偏置约 +0.346 m/s，负命令响应方向错误。不能恢复不存在的优化器。第一块保持 Actor/std、建立新 Motion49 Critic/Adam；后续同配方块严格恢复 Actor/Critic/Adam/std/RNG，环境重新 reset。

路线为 L1 `0/±0.5/±1` → L2 `±2` → L3 `±3` → L4 `±4 m/s` → Y1 `±1` → Y2 `±2` → Y4 `±4 rad/s`。这是一条新的粗档课程选择，与旧0.5增量课程不同。每档保留已学端点，块间人工审批，不在运行中换 reward 或自动扩预算。

## 明确版本和接口

| 部分 | 新版本 | 行为 |
|---|---|---|
| 训练 | `student_motion31_training_v1` | 独立 Motion 角色、命令与分块预算 |
| reward | `student_motion31_tracking_reward_v1` | 独立 tracking 分项、模式相关误差尺度、Huber 远场 |
| Critic | `motion_privileged49_v1` | 31D Actor +18D Motion 特权；不能混用站立49D |
| 验收 | `motion31_training_assessment_v1` | 同一模型完整矩阵、保持/停车分开、与来源逐环境姿态比较 |

Actor 拓扑仍为31→128→64→32→6，Critic49→256→128→64→1。Actor前22D物理字段不变；22–24为 vx/4、yaw/4、height/.5，25 Motion=1、26 Recovery=0。Critic新增18D：高度误差1、native速度3、接触合力2、effective命令2、tracking误差2、受控时间1、保持标记1、实际六通道力矩6。全部具名并声明单位/尺度。

Actor仍没有直接机身线速度；轮速、IMU和当前关节状态提供间接信息，但接触滑移时可能存在状态混淆。Critic特权有助价值估计，不能将缺失的信息自动传给Actor，也不能证明31D足以在所有状态下完成速度控制。

沿用来源学生契约：腿尺度 **1.5 rad**，轮100 rad/s，实体关节 left-first，physics/PD/policy=1/5/10ms、40/5.5Nm、Plane及来源资产。不能拿旧150D Motion的0.5rad腿尺度套用。retention关闭；std固定；没有改变现有版本的 reward、物理或网络。

`CommandEnv`仍提供 target_xy/固定槽位，Motion调度使用受控 episode age。学生 observation 的 legacy getter曾可能重写 command；新显式分支在编码前恢复同一调度结果，reward使用该次动作之前保存的命令，evaluator核对 Actor22–26列。终止bootstrap使用reset前Motion49输入。

## Reward：冻结的首轮选择

不是把线速度和yaw分数互乘。每项分别计算后加权，防止原地转向因为vx=0而奖励归零。误差定义为真实 native 速度减同一effective command；零命令没有进度奖励。

| 项 | 权重 | raw |
|---|---:|---|
| 支撑 | 0.5 | 接触力及高度连续支撑分数 |
| linear tracking | 4 | exp(-e_vx²/d_lin) |
| yaw tracking | 2 | exp(-e_yaw²/d_yaw) |
| lateral tracking | 1 | exp(-vy²/0.09) |
| height | 2 | 1/(1+((h−0.34)/0.04)²) |
| upright | 2 | 1/(1+sum((pitch,roll)/0.20)²) |
| linear/yaw/lateral Huber | −1/−0.5/−0.5 | 大误差仍有区分、尾部导数有界 |
| 镜像/轮心差/腿长差 | −0.2/−0.3/−0.15 | bounded_cost；尺度0.10rad、0.03m及0.02m |
| effort/target change | −0.02/−0.002 | 实際力矩归一化平方、实际执行目标变化 |

所有density最后乘 **dt=0.01一次**；无总clip，成功/失败/timeout事件奖励为0。非受控、无效或物理失败样本无dense reward。

episode目标决定模式，不根据ramp经过的瞬时小命令改标签：直线active轴 d_lin=1、yaw抑制d_yaw=0.09；自转d_yaw=1、平移抑制d_lin=0.09；零命令两者均0.09。非active轴Huber尺度0.3，active轴1。不是以 `clamp_min(command,.1)` 稀释零速误差。

例如误差1m/s时，d=0.04的exp分数约1.39e−11，d=1约0.368；误差1.9时d=1约0.027，Huber尾部仍提供区分。CPU reward曲线/导数是对**状态误差**的数学审计，不能当成仿真可微梯度、历史Actor梯度或快速收敛保证。权重/宽度尚无新在线因果证据，不能称作根因修复。

参考文献中的指数势阱、物理量归一化和对称约束仅作为设计思路；没有照搬WBC/LQR、补偿、无限力矩或动力学解冻。其“保证收敛/封死漏洞”等描述不是本项目已验证事实。

## 采样、验收和预算

64env×128steps=8192样本/update，LR3e−5、epochs/minibatches=4/4及现有global advantage normalization不变。首块固定槽位zero16、±0.5各12、±1各12；后续zero16、当前两端各12，其余24按旧正反配对确定性分配。首块smoke和formal分别从原始迁移Actor/std初始化，各自新Critic/Adam、前5次只更新Critic；smoke模型不作为formal来源。后续块完整恢复，不重复warmup。

训练controlled30秒：准备0.5、升速1、保持25.5、回零1、停车2；理想保持占85%，实际计数另报。无额外错峰、reset随机化或未来命令采样。首次smoke预算50更新，允许普通能力失败，但必须有真实episode结束/reset、非零reward、实际Actor更新、checkpoint读回和有效完整评估接线。不会因随机策略不能生存30秒就拒绝进入学习。

独立验收每命令8env：准备2、升速8、保持8、回零8、停车4，共controlled30秒；初始化计入请求31.52秒。保持MAE≤0.3、方向≥0.95、平均增益0.8–1.2、80%样本达到70%目标。停车world XY均速≤0.3、yaw绝对均速≤0.3；zero稳态world XY p95≤0.3。高度均值0.30–0.38、双轮接触≥0.95、饱和≤0.05、closure≤0.005、离地安全和连续生存均检查。

倾角peak≤0.50是本**新实验显式门槛选择**，不是沿用旧站立0.18，也不把它称作已有高质量站姿。pitch/roll保持均值须逐命令逐env不劣于同协议来源（容差0），完整记录几何；不拿tracking通过称为“站稳通过”。±4还要求均速3.6–4.4、连续3秒的一秒滑动均速≥3.8。

默认formal100/200/300评估全部**五命令**，不是三命令；每块最多300formal，全块4小时/2GiB，先到即停。相邻完整检查点间至少100真实更新、连续两次全矩阵通过才登记accepted；已被来源认证的能力连续两次退化有界停止。缺失来源姿态/完整窗口不放行。

任务formal累计上限2000（16,384,000 formal样本）；首块smoke50另计409,600样本，source_eval为PPO0。稳定task manifest配合exclusive append-only块登记，后续实验使用实际创建时间，不改旧账本；准备及reserve前读取各块实际formal用量，禁止并发消费同任务。达到额度、墙钟或存储上限仍未通过，报告能力边界/NEEDS_DESIGN，不换配方或放宽gate。

每块stage固定；下一级准备器必须消费已结算、SHA绑定的上一块accepted，新块重新授权。没有accepted时仅可同级从完整已评估best_new准备，不能晋级。已通过接线的同配方续块不重复smoke或Critic warmup。最终三评估seed声明为20261014/15/16；**尚未运行三seed认证**，单seed阶段accepted不能称为全高速能力通过，相关PPO0须独立审批。

## 本轮产物与验证入口

最终未授权spec：`configs/experiments/2026_10_14-16_42__motion31_tracking_block01/spec.json`；同目录budget/task_manifest/publication_complete。更早16_08/16_15/16_35是CPU准备中间声明，不作为运行推荐，不覆盖它。

公开命令只在TOOL_INDEX维护。运行仍由supervisor/launcher/monitor负责；新增motion_runner是既有trainer内的版本适配器，没有第二个公开launcher。准备器默认零写，`--write`只发布UNAUTHORIZED文件，不reserve、不创建run、不通知。

CPU发现并修复两处明确接线问题：legacy observation可能用另一时钟重写Motion command；链剩余时间大于单阶段预算时，run_phase将其误判成扩大预算。前者仅在新Motion分支恢复受控时钟，后者严格取chain/phase两项上限较小值。两者均有CPU失败样例；没有将它们解释为历史运动退化的唯一根因。

未完成的物理证据：受控Motion31 command→physics真实readback、smoke50、source同ramp协议基线、formal能力变化、三seed认证、sim2sim。不得用CPU fixtures替代。后续唯一优先步骤：在新明确运行授权下执行该首块来源评估→接线smoke→最多300formal；块结算后根据零偏置、双向gain、各gate和几何变化决定同级续块还是重新设计。
