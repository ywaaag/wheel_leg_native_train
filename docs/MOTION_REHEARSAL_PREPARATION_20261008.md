# Motion B250 同协议复盘与旧端点 rehearsal 准备

日期2026-10-08；用户授权本轮离线比较、准备与CPU检查，未授权仿真/采样/PPO。
来源B250保持为回退；不从formal25/50续训，不升±3，不加入yaw。

## 证据与更正

比较目录：`isolated/2026_10_8-14_53__motion_old_endpoint_rehearsal_audit/`。
comparison.md精简结果，comparison.json含33个model×command项目、264个逐环境结果，
输入raw/checkpoint/spec/manifest/certificate绑定SHA，additional冻结代码SHA见
raw_recalculation_corrected.json；旧ledger身份记录在raw_recalculation.json。
verification_final.json是独立复算结论：232个非零、完整窗口gate MAE与原结果完全一致。
初始naive切片及zero轴试算不是正式评分，保留试算文件并在verification_final明确更正；
历史原gate未改写。summary float32窗口与gate float64窗口不混同。

旧端点来源与formal25/50 effective protocol完全一致；来源±2各8/8。
±2.5独立来源probe的调度/diagnostics元数据与训练评估不同，原SHA分别保留；
评分门槛、请求时长、保持及停车窗口一致，不宣称原协议SHA全部相同。

|模型|zero mean vx|±2增益g|±2不对称a|±2.5增益g|±2.5不对称a|
|---|---:|---:|---:|---:|---:|
|B250|.008057|1.083046|-.004420|1.148954|.021182|
|formal25|.044181|1.199914|.012245|1.265592|.098328|
|formal50|.024478|1.287685|-.017817|1.294240*|.214089*|

g=(v(+c)-v(-c))/(2c)，a=(v(+c)+v(-c))/2-v(0)。zero mean(abs(vx))与上表mean vx数值相同。
*formal50 -2.5于10.29–10.31s joint_safety提前终止，保持窗口不完整；其双向统计
只是部分窗口诊断，不作为完整速度能力或标准对称性比较。此前只说超速的摘要不完整。

formal25的±2及±2.5各0/8，失败均为hold_absolute_error；formal50的±2、+2.5、
-1.5因误差失败，-2.5因连续时长/缺完整保持失败。零/±.5/±1仍通过。
已完成项目方向和双轮接触检查通过，不等于姿态对称或轮心对齐通过。
formal50 +2.5最大tilt约.3624rad，-2.5接触仍1.0但joint_safety终止；闭链误差
约数十微米。逐环境高度、限矩、停车、位移和failed_checks全保存在JSON。
力矩仅100Hz policy采样，不证明每5ms PD子步无持续饱和。

**运行证据支持**：较高端点的响应增益扩大、双向超速及旧端点退化；不是整体增益收缩。
**待验证机制**：较高新端点采样占比是否导致旧能力保持不足。
**UNKNOWN**：独立训练seed重复性、roll方向及幅度、真实轮心纵向错位及其因果。

## 用户GUI观察

用户报告机体roll歪斜、剪刀腿及约5cm轮心前后错位，但没有指定模型、命令和时窗。
记录为USER_REPORTED，不当作本轮独立量测。现有Motion轨迹包含root/速度/contact/
effort/closure/aggregate tilt，没有roll/pitch、完整root quaternion、轮心位置或关节
几何轨迹，不能由tilt推算roll，也不能用镜像腿关节误差代替轮心错位。
如需量化，后续另准备明确checkpoint/command/window的PPO0诊断：同步root姿态与
双轮中心，计算水平root-heading-frame前后偏差和roll；本轮不补采、不加对齐惩罚。

## 新的唯一准备声明

`configs/experiments/2026_10_8-14_56__motion_old_endpoint_rehearsal/spec.json`

spec SHA：`08e5f7492b3cf58f49c25cd805a5680866b4be4b590354fd576a2e1a72ba2024`。
由现有tools.prepare_motion_experiment生成，parent为上一短链冻结formal spec；
来源B250 SHA：`5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。
严格审核150D actor/critic、std、Adam参数名/shape/状态与CPU/CUDA RNG，不构造或步进optimizer。
来源LR保持3e-5，reward/PPO/物理/action/obs/termination逐字典相等。
0/±.5 tracking分母.04，其余1.0；时相/episode长度保持，不改advantage normalization。

名义64槽权重：zero16；旧八端点各4；新±2.5各8。
实际实现仍为原reset随机类别采样（weights=.25、旧各.0625、新各.125）；
不新增固定sampling_slots，不保证单rollout恰好16/4/8。
这是为了保持“只改比例”：若另要求严格固定环境槽位，应另作机制变更决定，不能偷偷混入。

独立book UNAUTHORIZED、attempts空、used全零；smoke1、formal最多50，51总更新、
417792总samples（formal409600）。拟议phase墙钟source2500s/smoke600s/formal9000s。
formal25/50完整11命令评估；旧能力两次确认退化停止；不解锁下一档。
smoke与formal各自恢复B250，formal不接smoke末尾；环境新reset，不恢复历史PhysX状态。
父spec中的旧blocked_reason含历史100预算说明，机器额度以新budget/formal50为准；
这是preparer文案继承限制，不扩大预算。新run路径尚未创建。

## 本轮验证与边界

- 新审计及准备器针对性18 passed（6.78s）；全量CPU559 passed（26.39s）。
- preflight为READY_NEEDS_AUTH/AUTHORIZATION_MISSING，仅缺新的运行授权。
- plan simulation0/ppo0/files_written0，spec/ledger SHA前后不变、run不存在。
- 审计输出及prepared配置为新目录独占创建，拒绝覆盖；旧证据未写入。
- 未启动GUI/Isaac/PPO、未检查GPU/进程、未发送通知、未提交Git。

本轮新增scripts/audit_motion_response.py、tests/test_motion_response_audit.py、
本报告；更新STATUS和TOOL_INDEX；新增上述独立配置声明及本地审计输出。
后续首先审核GUI几何担忧的证据缺口及采样语义，再决定是否另行授权此51-update试验。

## 后续明确授权与提交回执

用户已明确批准上述下一实验。使用register_authorization先零写核验，再登记新独立
spec/ledger，receipt保留授权前SHA；没有重置旧消耗或改训练配方。
approval_id为motion_rehearsal_89e527cb032c4299be2956fa98c829a2。
拟议phase墙钟2500/600/9000共12100秒与51更新上限登记一致。
授权后preflight PASS、默认supervisor plan PASS、health OK，仍零写输出。
43项针对性CPU回归通过（6.69秒）；测试读取未授权准备快照，避免依赖合法变化的活动ledger。

supervisor --launch提交GPU1 exclusive，CUDA_VISIBLE_DEVICES=1映射cuda:0，
UUID GPU-dfc076b6-b082-3065-512a-e21064067db1；未抢占GPU0或停止其他任务。
一次5秒握手：worker145263、attempt4f1cfbdbbfd3438fabebbdd107f8595f；
argv/start/output/spec/GPU/current session全部核验，submission_verified=true。
当前握手阶段SOURCE_EVAL，formal_first_update_verified=false、started=false；
提交不是正式PPO开始或能力通过证明。
终态通知目标冻结为本执行会话191bacc3-e5c7-4b8f-ae3d-5677eada837b。
run为runs/2026_10_8-14_56__motion_old_endpoint_rehearsal，入口chain.log、
chain_progress.json、completion_report.md；spec同名config目录，账本budget.json。
后台owner完成source→smoke→formal、25/50完整评估、预算与结算；本worker停止等待，不轮询。
