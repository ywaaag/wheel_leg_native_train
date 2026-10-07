# 底盘朝下 Recovery：实现准备与待授权验证

更新：2026-10-02，Asia/Shanghai。唯一现场入口是 [STATUS](../STATUS.md)。
本轮没有启动 Isaac 或 PPO；没有改变旧模型、旧 run、旧账本或源 USD。

## 固定 STAND 与历史停止

- 模型：[scratch update500](../runs/wide_leg_from_scratch_20261002_formal/model_update_500.pt)。
  SHA256 `fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1`。
- [原始10秒评估](../runs/wide_leg_from_scratch_20261002_formal/evaluation_500_0_0.json)：
  8/8通过，稳态root高度约0.397873m；不代表 Locomotion 或 Recovery 通过。
- 原 run 用户停止后 terminal=FAILED、exit0、实际formal511更新。历史结果保持。
  安装版 AppLauncher 在构造时覆盖 SIGTERM，并直接 close 应用；trainer 原处理器在它之前安装。
  修复为 AppLauncher 后重新安装处理器，正常经过 checkpoint/terminal/ledger 再关闭。
  真正 Isaac SIGTERM 收尾尚未实跑；OS信号假进程与已有账本回归已测。
- projection半径0表示禁用；原统计把任何非零腿向量判作超过0。现在 occupancy为0，并明确标记 enabled=false。

## 初态：发现了真实几何限制

正常根四元数 xyzw=[√0.5,0,0,√0.5]。机身+Y为上轴、−Z为前向，
来自当前物理状态转换和USD坐标，不凭GUI猜测。

当前USD的导轮最低面比robot机身底面低约0.098474m。R1候选：
主动角 `[1.4,-1.2,-1.4,-1.2] rad`，被动角由USD锚点闭链求解；
root初高约0.170474m，理想最近地面间隙2mm，但机身底面净空约0.100474m。
因此它是**导轮支撑的底盘朝下低趴**，不是机身底面贴地。
把机身底面压到地面会令固定导轮严重穿透。需要确认该姿态族符合用户意图；不能改USD掩盖差异。

[姿态库](../configs/experiments/recovery_r1_20261002/poses.json)有42次离线尝试：
R0 train/holdout各4，R1各1，R2各8，R3各8。主动腿扰动R2±0.03rad、R3±0.10rad；
训练姿态seed20261002、holdout20261003。R1是单一容易姿态，两集合的名义姿态相同；
不能以R1成功声称随机姿态泛化。全部离线closure/限位通过，拒绝0/42。
这只证明闭链位置与理想地面几何：**runtime拒绝率=null，沉降、实际接触、自碰撞/穿透未验证**。

### 用户补充：零力矩自然落稳

已纳入独立 INITIALIZING 阶段：从闭链有效低姿态开始，六个主动电机effort=0，
保留重力、闭链、碰撞和被动阻尼，至少0.2s、稳定持续0.2s、最多1s。
只允许初态下落/落稳，不从0.40m制造高冲击跌倒。速度、倾角、低姿态范围、
地面穿透和closure有效才进入Recovery；拒绝计数保留，不能悄悄删难例。
初始化无agent控制和任务reward，采样仍计入实际预算。训练局部reset不会推进其他环境的物理。
机身净空、root高度和COM不是同一量；COM本任务尚未测量，标UNKNOWN。

## 接触、控制与 FSM

robot底部、主轮和导轮为仿真允许支撑候选；腿杆件为限制接触，合力超过200N记任务失败。
USD没有分别命名的云台/雷达/相机碰撞体，弱部件承载检查UNKNOWN，不作硬件安全承诺。
严重理想地面穿透5mm、闭链残差5mm、非有限值和真实USD关节越限属runtime fault；
普通倾倒、限制接触、起身超时、交接不稳属task failure。
当前理想几何地面保护不等于已经测量了PhysX真实接触距离或所有自穿透。

控制保持plane、0.5/0.5摩擦、恢复系数0、1ms物理/5msPD/10ms策略、40/5.5Nm。
Recovery建议独立1.6rad腿尺度覆盖折叠姿态（原STAND仍0.5rad），轮尺度100rad/s，
真实USD目标限位仍裁剪。不得把它称为STAND行为等价适应。
两网络均25D/125D/150D，只见IMU类量、实际主动关节、command与previous action；
root高度和接触真值只用于任务状态、reward、评估，不加入actor。

任务入口 INITIALIZING→RECOVERY→HANDOVER→STAND_VERIFY→STAND。
STAND/FALLEN_CONFIRM部署跌倒触发只是保留的状态名称，目前未实现部署触发。
训练可以直接从低趴开始，不制造先站立再跌倒的过程。

交接候选：root0.385–0.415m、tilt≤0.14rad、角速≤0.3rad/s、线速≤0.05m/s、
主动腿角≤0.15rad、腿速≤0.5rad/s、双轮均>2N、机身净空≥0.25m；
腿目标差≤0.15rad、轮目标差≤2rad/s，Recovery执行腿目标已在STAND归一化域内；持续0.5s。
这些是**待R0验证的候选门槛，不是已测接管域**。
物理腿/轮目标层0.3s混合，不混合归一化action；仅一套PD。
两份history来自真实状态，previous action按各自尺度显式编码/裁剪。
进入区域不算成功：冻结STAND接管后持续5s满足高度、姿态、双轮接触、低速度和≤0.20m偏离才成功。
交接失败立即记失败，不无限重试；成功奖励只发一次。

## 奖励及学习

宽线性抬升 `clip((root_height-initial_height)/(0.40-initial_height),-1,1)` 权重3；
upright权重0.5、归一化effort²均值−0.02、action变化²−0.01、关节幅度成本−0.05，
过程项乘policy dt=0.01；完整成功一次+10，普通失败一次−1。无总奖励裁剪平台。
upright在低趴可能已很高，因此它不是主要起身信号；没有CLF/PBRS或理论稳定声称。
Recovery随机初始化actor/critic、新Adam、LR3e-5；STAND只严格加载冻结actor，不创建其PPO/critic/Adam。
初始化阶段actor输出不控制机构，奖励为0。成功/失败是terminated；Recovery超时是任务失败，
不是站立time-limit截断，不bootstrap失败后的新episode。
R1 formal不自动升级R2/R3；未来升级需128完整episode窗口、连续两窗成功率≥90%，且5s接管成立。

## 实现与验证边界

见 [ARCHITECTURE](../ARCHITECTURE.md)、[工具索引](../TOOL_INDEX.md)。
共用trainer/launcher/ledger/monitor/notification；没有另一套PPO或版本化trainer。
CPU93项测试通过，包括新增19项：SIGTERM处理器覆盖、projection禁用、FSM连续5s与一次性奖励、
局部reset、timeout失败、真实目标混合、history、独立USD rest-transform对照、
source500严格加载/CPU前向一致/文件SHA不变、preflight无run写入、初态拒绝分母及候选误认证。
语法检查通过；未启动Isaac。CPU测试不代替控制权、接触、沉降、PPO接线或后台实跑。

评估使用reset前tensor，逐姿态/seed记录成功率、起身时间、交接失败、5s验证、
接触/closure/姿态/饱和与最差案例。饱和是100Hz采样，不声称捕获每个PD子步。
原始终止tensor同时含q/dq、action、目标、PD请求/裁剪/applied effort和closure；
正常训练仅GPU汇总→每update JSONL，初始化样本及拒绝单独计数。
普通里程碑与最终候选身份精确对应checkpoint，Recovery判定不会拿站立gate替代。

## 准确命令：本轮只能运行 CPU plan

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.recovery.preflight \
  --spec configs/experiments/recovery_r1_20261002/spec.json \
  --output-dir runs/recovery_PLAN_ONLY

/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q
```

以下需要新的一次完整运行授权、独立budget置为AUTHORIZED和几何定义确认；当前不会执行。
每个输出必须全新，不能再次使用相同目录。

```bash
# R0: 冻结STAND近站立10秒。外部300秒上限包含15秒清理宽限。
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src timeout -s TERM -k 15 285s \
 /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.recovery.probe \
 --spec configs/experiments/recovery_r1_20261002/spec.json \
 --output-dir runs/recovery_R0_NEW --mode r0 --run

# R1初始化：零力矩沉降，PPO0；第二个300秒上限。
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src timeout -s TERM -k 15 285s \
 /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.recovery.probe \
 --spec configs/experiments/recovery_r1_20261002/spec.json \
 --output-dir runs/recovery_initial_NEW --mode initial --run

# 经物理证据确认初始化和接管门槛后，复用已有detached入口。
CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python \
 src/native_stand/command_v6/launcher.py \
 --spec configs/experiments/recovery_r1_20261002/spec.json \
 --phase smoke --output-dir runs/recovery_smoke_NEW --launch

CUDA_VISIBLE_DEVICES=0 /home/kellen/anaconda3/envs/issaclab/bin/python \
 src/native_stand/command_v6/launcher.py \
 --spec configs/experiments/recovery_r1_20261002/spec.json \
 --phase formal --output-dir runs/recovery_formal_NEW \
 --hapi-session EXPLICIT_CONFIRMED_SESSION_ID --launch
```

HAPI目标必须在下一次提交时确认，不从历史通知猜测；这里只给真实CLI占位参数，不发送测试通知。

## 建议一次授权范围（尚未批准）

| 阶段 | PPO更新/样本 | 包含启动清理的墙钟上限 |
| --- | ---: | ---: |
| R0接管＋R1初始化物理验证 | 0 | 累计600s（两进程各≤300s） |
| R1接线smoke，64×128 | 5 / 40,960 | 300s |
| R1正式，64×128 | 500 / 4,096,000 | 7200s，包含评估 |

新增总上限505更新、4,136,960样本；三阶段总上限8100s。
formal每100保存，200/400/最终500完整Recovery评估；没有每10次完整评估，终态选优+一次HAPI回调。
不会自动进入R2或开第二链。普通未起身不阻止学习；初态无效、控制错误和runtime fault阻止启动/继续。
约两小时是建议硬上限，不是已测Recovery耗时；原standing511更新总墙钟约91.6分钟只提供量级参考。
初始化和新几何检查可能改变吞吐，实测前不承诺提速/收敛时间。
外部timeout/monitor墙钟是含清理的总成本；trainer内终态wall在close之前，二者不能混用。
