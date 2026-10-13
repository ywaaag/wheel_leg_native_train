# Recovery 50/100起跳对齐与P2轮探索A/B准备

## 后续运行批准与提交 — 2026-10-08

用户明确批准“按你的方案行动”，两臂独立账本已登记AUTHORIZED并绑定当前owner session；原UNAUTHORIZED段落是准备时历史。
每臂source900秒/PPO0、smoke20/900秒、formal100/7200秒、chain9060秒，总240更新/1966080样本。
A/B分别通过唯一supervisor提交，同一GPU0共享并发，不停止其他进程，不新建配对watcher或trainer。
一次握手两臂均SOURCE_EVAL、submitted=true、submission_verified=true；formal_first_update_verified=false、started=false。不声称formal已更新。
授权后共享CPU536 passed，实际冻结副本各12 passed；spec/模块SHA与提交前身份核对一致。
GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，逻辑CUDA0，preemption=false；快照仅为各臂提交时刻。
[A回执](../artifacts/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/A_submission_stdout.json)、[B回执](../artifacts/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B_submission_stdout.json)。
后台各owner负责自己source→smoke→formal、预算/保护/结算并通知当前会话；交互worker不轮询，不自动增加块或重试。

依据：最新AGENTS、README/STATUS、WORKFLOW/TOOL_INDEX、训练经验指南与RECOVERY_STANDING_PLAN第7节；用户明确批准离线对齐及准备同源P2。
本轮无AppLauncher、PhysX、GUI、GPU资源检查、PPO、提交或通知发送。新A/B均UNAUTHORIZED，运行额度为待批准建议，旧ledger和raw不改。

## 来源身份与离线对齐

优先候选是23_29链本次new50，不能混称18_06 S50。
checkpoint：runs/2026_10_7-23_29__recovery_min_height_p1_guardfix_from_s50/formal/model_update_50.pt。
SHA256：8507dd7e157f0d1f27908056a51ddef6afcee08047dbf2c26d7758f6cd598d8e。
来源冻结spec SHA和USD SHA、完整评估/checkpoint分别核验，见[输入清单及逐事件数据](../isolated/recovery_takeoff_alignment_20261008/review.json)。
[轨迹图](../isolated/recovery_takeoff_alignment_20261008/comparison.png)分列50/100的高度、左右合力、roll、轮心纵向错位和轮目标。

保留原始trace索引、post-step时钟和实测recovery时钟，分别分析入口前、首入口确认及随后1000保持样本。
轮心是root-frame位置，纵向投影为水平native forward=-root Z，利用重力去除竖直分量；不是把gravity误当forward。
接触仍是记录的合力>2N；低读数不独立认证真实腾空，力矩是100Hz latest-held PD结果，不是每5ms/1ms审计。
没有完整150D pre-action历史，不能伪称actor均值回放或逐帧历史接线认证。

| 八环境DrawBack指标 | new50 | new100 |
| --- | --- | --- |
| 前2秒峰高 | .4397–.4402m | .4659–.4662m |
| 前2秒最大abs roll | .0700–.0708rad | .1036–.1042rad |
| 入口前两轮均低合力累计时间 | .08–.10秒 | .25–.28秒 |
| 入口前最大左右轮竖直位置差 | .0253–.0259m | .0560–.0564m |
| 保持窗平均轮心纵向绝对错位 | .1595–.1606m | .0320–.0326m |

env0时序：两模型约.04秒超过4cm纵向错位、.17秒超过5mm左右竖直差、.19秒abs roll超过.03rad；.23秒出现两轮均低合力。
这些阈值仅作固定离线时序诊断，不是新gate。它们支持不对称在落地前已出现，不能将其全部归因于落地颠簸；两模型早期事件时间相近，不能据此证明不对称是唯一原因。
第一次两轮低合力段，new50 env0约.08秒、new100约.15秒；恢复>2N时左轮先于右轮约.16/.12秒。
new100后续交替左右先接触，env0入口前共6段两轮低合力；new50为1段。首段“左先”与GUI后来左轮弹跳不矛盾，不能用它判定哪一边一直离地。
new100峰高时四腿施加力矩约[-29.3,-28.4,+22.5,-22.0]Nm，new50约[-23.2,-13.5,+8.6,-16.6]Nm；这是不同状态/时刻的动作证据，不是配对因果实验。

保持阶段，new50 env0高度.4238–.4264m、mean abs轮心错位.1605m、wheel target半差绝对均值6.41rad/s、接触99.9%。
new100高度.4284–.4335m、错位.0321m、wheel target半差绝对均值5.59rad/s、接触94.1%。
即new100更齐、roll更小，但接触更差，不能将剪刀腿/差速单独当完整稳定性的根因，也不据此立刻加更强对称惩罚。
R0按同一协议单独对齐：new50保持错位.1386–.1399m，new100 .0257–.0260m，仍不能以几何更齐替代完整保持验收。

## 为什么选择P2而不是同时改多项reward

P1实际采到入口后2–10秒，new50保持高度/水平明显优于来源，确定性保持窗采样触限为0；随机训练各family/phase逐轮触限却约45–56%。
这满足第7节“有可用确定性动作、训练持续大量轮触限”的对照触发方向，不证明低std一定会解决确定性跳跃。
确定性new100跳得更高也有腿部施力/构型变化，现有证据不支持把所有跳跃直接归因于轮std。
因此保留new50作同源，两臂仅比较后续探索初值；不同时加对称、轮心成本、制动、vertical成本或改接触协议。
若B触限降低却抬升丢失或保持退化，B失败；若两臂无净收益，再按实际证据选择腿发力/落地构型的独立变量。

## A/B完整准备声明

根：configs/experiments/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50。
[A spec](../configs/experiments/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/A/spec.json)、[B spec](../configs/experiments/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/spec.json)。
A/B各自独立budget.json，UNAUTHORIZED、used全0、attempts空、session=null；不复用耗尽的P1额度。
机器differences仅一个字段：recovery.exploration_initialization.wheel_std_multiplier，A=1，B=.5。

本次new50归一化std：[.05820535,.11699411,.09482490,.05808646,.06057710,.07567806]。
腿物理std约[.09313,.18719,.09294,.09692]rad；轮物理std A=[9.48249,7.56781]rad/s，B=[4.74125,3.78390]rad/s，均为输出裁剪前尺度。
固定positive scalar参数化，无wheel output factor；B只改2/5通道初值，不冻结、不加std schedule、不改action scale。
训练中std仍由PPO学习，旧std的Adam矩也保留；可能再次增长，应从初始化回读与检查点检查，不能只看声明。
两臂smoke/formal各自从同一个new50初始化，不继承smoke末权重。严格恢复actor/critic全部参数和17个Adam状态，LR3e-5、gamma/lambda等不变。
parent restore_source_rng=false：两臂按相同seed20260930重新开始，保持该设置，不宣称恢复来源RNG或独立training seeds。
source_eval保持原始std，干预只在smoke/formal的Adam恢复后、首次act前发生，因此它不直接改善冻结source的确定性起跳。
DrawBack/R0、40%R0抽样、新USD、1.6/100动作尺度、40/5.5Nm限矩及minimum-height协议保留。
旧pose文件按原SHA只读复用；未重新序列化其中合法的无限passive limits。

建议每臂source≤900秒/PPO0、smoke20/900秒、formal100/7200秒、chain9060秒含清理。
总240更新/1966080样本、总chain上限18120秒。这是新建议，不自动借用P1余额或用户对准备工作的同意。
保存25/50/75/100；完整评估25/50/100，同时评DrawBack/R0，保留抬升、接触、倾角、10秒完整保持和逐轮phase触限。
本轮不跑100秒耐久、不升级Swing/随机倒地。
运行时继续共享GPU0且不得停止别人；当前session/UUID在另获运行授权后由supervisor提交检查核验。

## CPU及计划验证

共享全量536 passed。两臂实际冻结副本各12 passed，schema/plan通过，未创建run。
共享source_eval plan均READY_NEEDS_AUTH/cpu_valid=true，budget SHA未变。
通过项目现有tools.validate_frozen_cpu完成验证，不增加第二套验证/监督程序。
[实际checkpoint初始化](../isolated/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50_initialization/verification.json)验证A/B各actor均值和critic保持、干预不改Adam/RNG、只有B两轮std变更；PPO/optimizer step=0。
冻结测试验证不依赖真实资产数据的独立fixture；实际模型身份加载在原项目另行核验。
这些是CPU实现证据，尚无新PhysX、训练或A/B收益结论。

## 本轮文件

新增scripts/review_recovery_takeoff.py、scripts/prepare_recovery_wheel_std_ab.py、src/native_stand/recovery/exploration.py、tests/test_recovery_exploration.py、tests/test_recovery_exploration_wiring.py及本文。
修改command_v6/train.py（仅训练初始化调用）、recovery/validation.py（显式声明检查）、tools/entrypoints.py、TOOL_INDEX/ARCHITECTURE/STATUS和RECOVERY_STANDING_PLAN当前进展说明。
新增本次A/B未授权声明、独立budget/preparation_manifest和离线/CPU验证产物。
保留其他worker dirty changes，未删除脚本、未改历史模型/评估/账本、未提交Git或推送。
