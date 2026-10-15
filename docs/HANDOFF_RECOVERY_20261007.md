# Recovery 训练交接与当前证据
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


更新时间：2026-10-07，Asia/Shanghai。本文是会话交接记录，不授权仿真或 PPO。
路径以 `/home/kellen/wheel_leg_native_train` 为根；run JSON 优先于 Markdown 历史快照。

## 1. 当前任务与用户意图

长期目标是底盘朝下、腿姿可行的低趴状态自主起身，随后稳定站立。
早期 Recovery 已出现抬升，但存在弹射、倾斜、剪刀腿、滚动、自转及交接困难。
后来改成逆向课程，从近站立的 R0 保持开始，再扩大初态，最终回到低趴起身。

用户最近明确调整目标：不要求定点站稳或控速，先做到不摔和机体水平。
用户 GUI 验收了 `standing_scissor_20261006/formal/model_update_50.pt`。
要求 reward、在线成功条件、完整验收和课程晋级同步修改，旧验收不追溯改写。
因此当前实验取消速度、漂移、yaw 速率、镜像对称等门槛，它们仍作为诊断。
不要因为旧定点控速协议失败而否定新协议通过，也不要把新通过称为定点站立。

本次最新请求是交接上下文。已结束链的完成通知明确不授权自动续训。
下一会话应先分析已有证据；新的物理测试/PPO 必须按授权边界处理，不能重启旧链。

## 2. 工程入口和边界

唯一长期工程：`/home/kellen/wheel_leg_native_train`。
当前共享 kernel 保留 `src/native_stand/command_v6` 名称，不再复制 command_v7 等 trainer。
主流程：preflight -> ledger reserve -> detached launcher -> 一次握手 -> monitor
-> candidate selection -> terminal/accounting -> report -> HAPI 通知。
正式后台启动后，不靠会话轮询日志或 sleep 维持进程。

只允许在此项目内做相关修改，保留 dirty changes 和全部旧 run/checkpoint/账本。
Fudan、同事源项目、原始 USD、独立 MuJoCo 均只读；不停止其他任务。
不增加限矩，不加入外力、LQR、gravity compensation、static trim、硬锁轮或隐藏门控。
新实验用新 spec/run/ledger，不复制整套代码，不覆盖历史结果。

解释器：`/home/kellen/anaconda3/envs/issaclab/bin/python`。
运行 cwd 为项目根，通常 `PYTHONPATH=src CUDA_VISIBLE_DEVICES=0`。
默认 shell 的 `python` 不存在，应使用绝对解释器路径。
当前 Git 工作区大量文件为 untracked；不要清理、reset 或假设这些文件可删除。

最小阅读顺序：AGENTS -> README -> STATUS -> ARCHITECTURE -> 当前 spec -> TOOL_INDEX。
设计 reward/curriculum 前另读 `TRAINING_EXPERIENCE_REUSE.md`、
`docs/RECOVERY_STANDING_PLAN.md`、`参考文献.md`。
当前任务说明：`docs/RECOVERY_SURVIVAL_LEVEL_20261006.md`。

## 3. 策略与物理契约

原生闭链 actual-joint 策略，不是 Gym47250 虚拟腿策略；不能互换权重。
25D frame、5 x 25D oldest -> newest history、actor/critic 共 150D。
frame 切片：

| 切片 | 字段 |
| --- | --- |
| 0:3 | body angular velocity |
| 3:6 | projected gravity |
| 6:9 | command [vx, yaw_rate, height] |
| 9:13 | 四个实际主动腿角偏移 |
| 13:19 | 六个实际主动关节速度 |
| 19:25 | previous clipped action |

动作顺序：left hip、left active、left wheel、right hip、right active、right wheel。
腿是实际关节位置目标，轮是轮速目标；只有一条主动 PD 控制路径。
当前 Recovery 腿尺度 **1.6 rad**，轮尺度 **100 rad/s**，pair projection disabled。
不要误写为早期站立实验的 0.5 rad。actor clip 与真实 USD 关节限位仍保留。
physics 1 ms、PD 5 ms、policy 10 ms；腿 Kp60/Kd2，轮 Kv1。
腿 40 Nm、轮 5.5 Nm；闭链保护 5 mm。
command 当前固定 `[0,0,0.36]`，height 指 root height，不是 COM 或底盘净空。
plane collider，静/动摩擦 0.5/0.5，恢复系数 0；GUI 网格是视觉层，不能改碰撞。

当前 mechanical-stop USD 副本：
`assets/diagnostic/rmuc_robot_closed_loop_knee_stop_0233_v2.usd`
SHA256 `32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7`。
源原始 USD 没被修改。0.233 rad 膝几何止挡来自用户指定姿态限制；不代表已建模气弹簧。
有效碰撞 offset 等未读回的属性仍为 UNKNOWN，不默认等于零。
坐标不是凭 GUI 猜测：按 runtime 的 canonical pitch/roll 和 native forward 定义读取。

## 4. 模型身份：不要混用多个 update500/1500

当前最佳、GUI认可且新协议通过的来源：
`runs/standing_scissor_20261006/formal/model_update_50.pt`
SHA256 `1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。
当前实验直接 strict 加载 150D actor/critic/Adam，并显式应用 LR3e-5。
新环境完整 reset；不声称恢复 PhysX 中间状态。

独立冻结 STAND 历史模型：
`runs/wide_leg_from_scratch_20261002_formal/model_update_500.pt`
SHA256 `fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1`。
其动作腿0.5rad/轮100rad/s；这是早期冻结接管策略，不是本次 source/retention teacher。
当前 autonomous_hold 实验没有让此 STAND 接管，不能宣称 HANDOVER 已验证。

B200、旧低高度 update500、Gym47250 都不是本次来源。
当前最新但退化的模型：
`runs/recovery_survival_level_from50_20261006/formal/model_update_200.pt`
SHA256 `fdd7a140e9b1a3c841dd558347a095384daf81951203e5717a039017be302ddf`。
不要把 latest 自动当成 best，不要未经分析从它继续训练。

## 5. 最新实验与预算结算

run：`runs/recovery_survival_level_from50_20261006`。
event：`f19e69d28f8650f3f6ef342d`。
spec/ledger：`configs/experiments/recovery_survival_level_from50_20261006/{spec.json,budget.json}`。
来源身份、配置及真实执行源码还保存在 run manifest 和各 snapshot 中。
读取共享源码只了解现在实现；复现此 run 必须以 snapshot 为准。

授权总上限 10000 更新 = 3 smoke + 9997 formal；64env x128steps。
总样本上限81920000；本链保守总墙钟上限10小时。
实际 smoke3次/24576样本；formal200次/1638400样本。
总 PPO203次/1662976样本；formal 剩余9797次没有使用，不代表可以自动续训。
source_eval100.72s、smoke35.33s、formal2170.81s、durability759.39s。
整链3075.77s，约51.26分钟。
formal `STOPPED_BOUNDED`、exit0、failure=null；原因是
`standing regressed in two consecutive full evaluations`。
外层 `COMPLETED` 表示有界流程正常收尾，不表示10000更新全部完成或策略学成。
这是行为退化早停，没有确认 nonfinite/closure/control runtime fault。

## 6. R0/R1 课程与当前阶段

R0：现有近站立 nominal70% + 小扰动30%。
R1：扩大的近站立姿态族60% + R0保留40%；不是低趴姿态。
后续 R2：人工捕获低趴；R3：扩大不对称/腿姿。此链 R2/R3 禁用。

每窗口128个完成episode，不重叠；两个连续窗口成功率>=90%、零runtime fault，
还需两次连续完整评估确认，才在下一次 reset 晋级。当前 episode 不改初态。
完整评估 update100/200，之后每500及最终；checkpoint每100，无2秒轻评。
新阶段失败可继续学习；保留R0连续两次完整评估失败触发退化保护。

终态仍是 stage0/R0：46个窗口已记录，连续通过窗口0，完整确认0。
最新窗口尚有102个episode；R1初态采样次数为0，没有晋级。
在线 autonomous_hold 连续2秒条件达到后训练可成功终止；独立评估禁用成功reset，
保持首次连续10秒物理 episode，不能拼接多个 reset 片段。
在线成功要求高度/姿态/接触/底盘净空，不要求控速，也不要求冻结 STAND 接管5秒。

## 7. 本轮 reward 和完整验收

协议 `survival_level_v1`：8/8连续10秒，无fault/reset；2-10秒稳态高度0.34-0.38m，
高度区间采样>=90%，双轮均>2N比例>=95%；mean abs pitch/roll各<=0.10rad，
peak abs pitch/roll各<=0.15rad，peak tilt<=0.18rad，closure<=5mm，
policy采样 saturation<=5%。这不是每PD子步饱和认证。

保留的主要连续 reward（乘policy dt一次）：height Gaussian权重3/宽度.04m；
pitch/roll二次cost各-4、scale.12rad、unconditional；support+.5；
vertical motion/roll-pitch angular motion各-.1；effort/action delta/joint margin，
height overshoot，以及较小低高度wheel-spin cost。
lift/upright权重0；linear/full-angular/yaw settling、mirror、leg-length balance、
wheel difference、support balance及wheel longitudinal offset的贡献为0。
常量 all-channel BC retention coefficient.02，teacher就是source update50，
每rollout最多256个有效近站立输入；这不是teacher接管，也不是行为稳定保证。

update200实际weighted每step均值：pitch-.05048、roll-.13334、height+.02642、
support+.00447，retention独立训练loss约.000224。
这是量级失衡的检查线索，不能仅凭标量就断言梯度主导或唯一根因。
source/checkpoint训练状态分布、episode成功终止和critic也可能参与，尚无因果结论。

## 8. 已验证退化：同协议完整评估

| 模型 | 通过环境 | 稳态高度m | mean abs pitch/roll rad | 平均绝对vx m/s | 10秒净位移m |
| --- | --- | --- | --- | --- | --- |
| source50 | 8/8 | .366665 | .021962/.072339 | .704108 | 6.261570 |
| new100 | 0/8 | .361415 | .026972/.130036 | 1.021925 | 8.598821 |
| new200 | 0/8 | .353141 | .107737/.195606 | 1.353195 | 10.074994 |

new100：8个环境均连续完成10秒，但全部roll gate失败。
new200：5个tilt终止、3个窗口完成；平均连续9.275s，末高度平均.290328m。
失败项：continuous5、tilt8、saturation3、height_fraction8、contact8、pitch8、roll8。
new200全轨迹双轮接触比例平均.848425；不要混同于另一个稳态或rollout窗口。
最新训练rollout接触.894165、饱和.260254、tilt终止13、closure/nonfinite等fault0。
所以来源保持、水平程度、高度和抗跌倒能力都退化，速度变大只是附带诊断。

来源仍通过新协议，旧严格定点/对称协议的失败结果不被改写。
当前能宣称：既定近站立初态下不摔、保持本轮基本水平。
不能宣称：定点控速、完整对称、低趴起身、任意扰动恢复或命令运动通过。

## 9. 100秒结果与报告缺口

`durability_100s.json` 实际测试的是source50，不是new200。
8/8连续100.00295s，无runtime fault、success=true，recovery_gate accepted=true。
但 completion_report.md 写 `100-second gate=None`，因为 stand_chain 只读取
`standing_gate` 而此Recovery评估写的是 `recovery_gate`。这是汇总字段缺口。
当前只完成诊断，尚未修复，旧结果不可覆盖。

更重要：该100秒结果的success_protocol.standing_protocol仍写steady_window[2,10]，
尽管spec evaluation.durability_steady_window_s为[2,100]。
因此能确认100秒连续存活，不能声称高度/水平等摘要验收覆盖全部100秒。
后续应先检查durability协议传递与评分窗口；可优先用已有紧凑轨迹离线重算，
不能直接把当前JSON accepted当作全时段水平认证。
mean abs vx约.704m/s但100秒net drift约5.67m；净位移不能冒充累计行程。

## 10. 关键证据入口

- `runs/recovery_survival_level_from50_20261006/completion_report.md`
- `runs/recovery_survival_level_from50_20261006/formal/terminal_report.json`
- `runs/recovery_survival_level_from50_20261006/formal/progress.json`
- `runs/recovery_survival_level_from50_20261006/formal/candidate_selection.json`
- `runs/recovery_survival_level_from50_20261006/source_eval/evaluation_source.json`
- `runs/recovery_survival_level_from50_20261006/formal/evaluation_100_0_0.json`
- `runs/recovery_survival_level_from50_20261006/formal/evaluation_200_0_0.json`
- `runs/recovery_survival_level_from50_20261006/formal/metrics.jsonl`
- `runs/recovery_survival_level_from50_20261006/durability_100s.json`
- `configs/experiments/recovery_survival_level_from50_20261006/budget.json`

此formal目录没有独立curriculum_windows.jsonl；窗口摘要见progress/metrics，
更详细的课程状态以保存的checkpoint `recovery_curriculum` 为准，不假设日志存在。

TensorBoard当时URL为http://127.0.0.1:6013；本次交接未确认服务仍存活。
JSONL是证据，TensorBoard不是控制进程，不能从浏览器数据推断训练仍运行。
HAPI历史目标6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1；新会话通知目标必须重新明确，
不要把旧ID当新会话ID。完成通知只能触发复盘，不授权续训。

## 11. 历史经验和待检验问题

早期存在Adam恢复覆盖spec LR、inference_mode持久缓存局部reset、SIGTERM收尾、
禁projection后统计仍记占用、timeout读reset后状态、外部YAML SHA导致GUI拒绝等缺陷。
相关实现已经历修复，下一会话应复查对应测试，不用聊天说法代替CPU/runtime证据。
旧BC A/B发现方向冲突但weighted BC梯度贡献很小，未支持BC是唯一主因；
其teacher/recipe不同，不能直接套给本次source50。
轮纵向几何惩罚曾明显减少剪刀腿，但同时增大roll和滚动速度；没有全面改善证据。
不能把剪刀腿直接定性为reward hacking或认为硬对称/硬锁轮是必要修复。

最优先的下一步：
1. 用已有证据修正报告理解，核查100秒评分窗口，保留原结果另写corrected review。
2. 对source/new100/new200做同输入reward、retention与PPO梯度/episode状态分布检查，
   找出水平奖励增强后roll反而变差的原因；不要在未证实时断言唯一原因。
3. 区分本轮离线分析与新训练；一次只调整有证据的主要变量，新spec新预算。
4. 不回退到B200/Gym，不从new200盲续，不放松物理保护，不恢复用户已取消的控速gate。

最近CPU证据：本配方58项focused和80项general检查曾通过、fresh preflight PASS。
这些是启动前记录，不是交接当日重新跑的测试；也不证明未来修改仍通过。
新会话可先查具体测试 `tests/test_standing_survival_level.py` 和TOOL_INDEX公开入口。

## 12. 给新会话的简短任务入口

请先读本文和最近AGENTS，再读取最新run原始JSON；当前训练已停止，未授权自动续训。
用户要解决：已经GUI认可的source50能不摔且基本水平，为何改成survival_level训练后，
100次roll退化、200次开始跌倒？先查reward权衡、来源保持、episode/critic分布与
100秒评分传递，不重新做全项目重构，不用未验证假设开始长训。
当前最佳仍是source50；R0未晋级R1，更没有低趴起身成功认证。
