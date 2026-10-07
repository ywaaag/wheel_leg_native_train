# Motion 工程修复与能力复核

## 范围与真实执行链

本轮授权仅工程修改、CPU/离线重评分和累计3600s物理评估；online PPO=0、offline optimizer=0。
GPU0启动前被另一项目占用，未预留attempt；用户随后明确授权GPU1。
旧run、checkpoint、spec、evaluation、ledger、外部仓库均只读。

实际调用链：supervisor CLI → preflight/config.validate → domain.recipe.resolve →
execution_identity → monitor exact attempt → evaluate_checkpoint.batch → AppLauncher →
CommandEnv/configure → ramp command/combined reward → evaluator → score →
capability_gate(motion_absolute_v3) → resolve_gate/completion selector → terminal/ledger。
训练仍使用安装版RSL-RL PPO；本轮没有构建optimizer、没有更新权重。

## 问题分类和修复

|分类|事实及处理|
|---|---|
|A 已有修复|effective protocol、requested/observed时长分离、早终止不缩短gate、默认关闭P2、评估actor/RNG恢复。保留现有实现。|
|B 当前缺陷|独立CLI使用stage0基础reward；改为active_stage和统一recipe解析。|
|B 当前缺陷|声明separate/fixed/per_command但执行combined/ramp/global；新严格spec拒绝冲突，旧spec保留并显式列legacy ignored声明。|
|B 当前缺陷|execution_source_root声明旧isolated但加载共享src；严格spec核对真实src并保存模块SHA和外部PPO文件SHA。|
|B 当前缺陷|source baseline命令集硬编码；改从source_required_commands读取。|
|B 当前缺陷|字符串authorization导致health_check AttributeError；兼容字符串及字典。|
|B 当前缺陷|native评估恢复无条件清除进入前forced_target；恢复原值，cleanup错误不覆盖原始错误。|
|B 当前缺陷|新协议没有共用训练/候选路径；v3接通evaluator、trainer、completion。|
|C 协议变更|旧capability_v2的80%均速/70%持续及±4的3.8条件保留历史；新增absolute_v3体现用户目标，不回填历史通过。|
|C 采样选择|同步episode/固定env槽位是现有设计，本轮不修改。|
|D 证据缺口|B250 ±1.5/±2、new250 ±1.5、yaw、每5ms PD完整限矩尚缺当前版本物理证据。|

## Requested → effective → 实现

新复核spec显式使用ramp、combined、global_adv_norm。训练时序1/2/24/2s、31s episode；
评估2/8/8/8s和4s停车、30s episode。active-stage linear=1.0、yaw=.09；
cohort zero/±.5 linear=.04。velocity_tracking权重8，其余来源权重/动作/物理不变。

- command：domain/command_schedule.py 和 runtime/env.py。
- combined tracking：domain/reward.py，不新增split项。
- width：domain/recipe.py 和 domain/tracking_width.py。
- normalization：安装版PPO.compute_returns默认全rollout标准化；非per-command。
- identity：tools/execution_identity.py记录模块实际路径、SHA、Python、依赖及PPO实现SHA。
- plan/manifest/runtime_readback各自保存requested、effective及实际env reward/schedule。

## 新协议

motion_absolute_v3：保持10–18s，停车26–30s。逐环境mean(abs(vx-command))≤.3；
yaw目标mean(abs(yaw-command))≤.3。方向率≥.95，无80%–120%或隐藏最小速度附加条件。
±.5不動时error=.5，因此失败；yaw静止同样失败，不依赖reward。
zero使用mean(abs(vx))≤.5，位移仅记录及60m场地边界保护，不使用旧.2m定点条件。
横向mean abs vy≤.02、zero/直线yaw≤.3；原地yaw平移≤.3、净漂移≤.3、最大偏移≤.5。
保持物理阈值：tilt≤.5rad、双轮接触≥.95、高度均值.34–.46、closure≤.005m、
policy采样任一通道限矩占比≤.5。不能宣称是每5ms限矩审计；滑移未测。
完整30s和完整保持窗口不可缩减。缺失字段MISSING_EVIDENCE，不能补零通过。
停车残速单列，不加入本轮稳态gate；缓变过程完成不代表急停认证。

## 模型身份与离线能力矩阵

三个250/500不能混淆：

- B250：runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt
  SHA 5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。
- new250：runs/motion_high_speed_course_20261007/formal/model_update_250.pt
  SHA 5edcd3fb78bed39b131a12e56552674a62c8993d03a57e01cfe9b32770a799c4。
- new500：runs/motion_high_speed_course_20261007/formal/model_update_500.pt
  SHA 95ec1c0bc4786684ee63d20e5c582d8ef73653d5b9657dd2d14adbed67adc270。

同轨迹新协议重评分，不是新训练收益：

|command|B250 vx/MAE|new250 vx/MAE|new500 vx/MAE|
|---|---|---|---|
|0|.0081/.0081|-.0057/.0057|.0013/.0013|
|+.5|.4669/.0331|.3913/.1087|.3846/.1154|
|-.5|-.4552/.0448|-.4181/.0819|-.3864/.1136|
|+1|.9600/.0400|.7914/.2086|.7838/.2162|
|-1|-.9290/.0710|-.8507/.1493|-.7766/.2234|
|±1.5|UNKNOWN|UNKNOWN|UNKNOWN|
|+2|UNKNOWN|1.7998/.2002|1.6993/.3007|
|-2|UNKNOWN|-1.8239/.1761|-1.6179/.3821|

上述B250和new250已测命令新评分均8/8；new500 ±2为0/8。逐环境、旧gate、新gate及
原始文件SHA在isolated/motion_recheck_20261007/high_speed_rescore/rescore.json，
cohort_rescore/rescore.json。来源original±2缺失，不能宣称new250新学会±2。
当时的暂定判断：new250最符合已有更广命令覆盖；B250低速误差更小，是回退来源。
此早期来源推荐已被本文最后的GPU1同协议复核替代：当前推荐B250。
不能拼不同模型点，也不能把这条暂定判断作为当前提交依据。
下一次先补±1.5，再决定起点和最高完整0.5步长能力。yaw均UNKNOWN。

## CPU/plan-only与物理入口

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/motion_recheck_20261007_gpu1/spec.json \
 --output-dir runs/motion_recheck_20261007_gpu1/attempt1 \
 --physical-gpu 1 --evaluation-only
```

启动前针对性49tests通过，GPU1 plan PASS。一次提交使用同命令加--launch --wait，
monitor PID3158545、attempt fd5a5cf644b545fd82f28af0e52873f1。
独立账本configs/experiments/motion_recheck_20261007_gpu1/budget.json。
所有后续状态以该新run的manifest、progress、terminal_report、monitor_exit和ledger为准。
worker不轮询日志；后台monitor是超时、child退出和结算的唯一owner。没有通知发送。

## 后续训练准备，未执行

configs/experiments/motion_absolute_halfstep_PREPARED_20261007_v2/spec.json 和其UNAUTHORIZED账本。
包含L0、直线±.5到±4、之后yaw±.5到±4，初始待学习±1.5、保留zero/±.5/±1。
三次完整确认才一次晋一级，在reset边界生效；required_commands缺失或单方向不能晋级。
每25update零命令、每50完整；失败→通过→失败计数1→0→1，motion未学会不算旧能力遗忘。
实际目标端点whitelist reset断言；默认ramp只连接已允许端点，不能采未来端点。
训练计划仅建议200updates/7200s，无quota transfer；本轮不授权任何PPO。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/motion_absolute_halfstep_PREPARED_20261007_v2/spec.json \
 --output-dir runs/motion_absolute_halfstep_PLAN_ONLY --physical-gpu 0
```

CPU plan应READY_NEEDS_AUTH，不能加--launch。本轮只授权PPO0。
最值得下一轮隔离验证的变量：新增端点组成，只加入±1.5并保留已验收端点；
不同时改reward/LR/std/normalization。固定cohort和状态分布仍为候选机制，不是已证实根因。

## 参考材料勘误

参考文献2把不同run的update250身份混称B250；按上述完整路径/SHA区分。
全局advantage或PCGrad根因/保证没有本项目因果证据。Fudan成功是树模型、不同接口/限矩、
特定协议；复用命令rehearsal、同模型完整命令选优、退化回退，不能证明native ±4可达。
只读实现：fudan_train/plane/wheel_legged_gym/experiments/recipes/motion_goal.py:stage_bank/apply。
不加入PCGrad/WBC/MPC/LQR/新网络/privileged critic。

## 精确修改范围

本轮修改：README.md、STATUS.md、ARCHITECTURE.md、TOOL_INDEX.md；
command_v6/config.py、train.py、completion.py、monitor.py、supervisor.py；
domain/evidence.py、protocol.py、task_curriculum.py、selected_diagnostics.py；
runtime/env.py；tools/preflight.py、evaluate_checkpoint.py、evaluation_state.py、health_check.py、correct_evidence.py。
新增domain/recipe.py、tools/execution_identity.py、tests/test_motion_absolute_recheck.py；
scripts/prepare_motion_recheck_20261007.py、prepare_motion_course_plan.py、report_motion_recheck_20261007.py；
本报告及四个新声明目录。Recovery runtime/validation/wiring等并发修改不是本轮所作，保留不动。

最终全量CPU回归351 passed in16.79s，75source files原地compile通过（无pycache）。
新增用例覆盖实际resolver、protocol_for_spec、score/gate、调度、命令覆盖、P2分组、
真实CPU子进程退出与exact reconciliation；不是物理能力证明。
首次halfstep PREPARED版本的stage0非zero导致plan CONFIG_ERROR，修正生成v2后
plan仅AUTHORIZATION_MISSING；v1不作为执行入口，保留失败准备事实。

已执行GPU0提交在资源检查阶段拒绝，无reservation、无Isaac、无PPO、无attempt消耗。
GPU1用户补充授权后独立spec通过plan，CUDA_VISIBLE_DEVICES=1，逻辑cuda:0；
真实进程显存归属GPU-dfc076b6-b082-3065-512a-e21064067db1确认，RTX3060。
GPU0另一个trainer未停止或修改。物理actual结果会写入独立final_gpu1报告；
此处启动描述不替代终态证据。

## GPU1实际复核与后续准备

最终CPU命令 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short`：387 passed in17.70s。
GPU1已完成全部9项，均8/8通过；child退出0，monitor和独立账本均COMPLETED。
包含初始化、保存和清理墙钟1942.309946s，小于3600s，缺失项0、运行故障0。
在线PPO=0、离线optimizer=0。完整评估全64env政策步样本1,728,000；
其中8个scored env样本216,000，均为评估样本，不计作训练或PPO0 rollout采集。
模型SHA未改变、实际执行快照SHA全部核验匹配。

|模型|命令m/s|保持段mean vx|保持段mean absolute error|
|---|---:|---:|---:|
|来源B250|0|.008057|.008057|
|来源B250|+1|.960034|.039965|
|来源B250|-1|-.929039|.070960|
|来源B250|+1.5|1.521571|.036631|
|来源B250|-1.5|-1.536903|.059934|
|来源B250|+2|2.169730|.174264|
|来源B250|-2|-2.162456|.168429|
|new250|+1.5|1.255212|.244786|
|new250|-1.5|-1.316300|.183697|

这是冻结模型PPO0复核，不是新增学习。B250本来具备已测±2能力；
建议下一轮以B250为起点，学习±2.5，保留低档端点。当前版本±.5未重新采集，
其历史原始轨迹与新版本认证区别仍须记录。±4及yaw无证据，不宣称通过。

新准备spec：`configs/experiments/motion_absolute_halfstep_PREPARED_20261007_v4/spec.json`，
SHA `e2b2d135dfb5f484c69d468421526def956dec5679065ea089d112fc5c76ed92`。
active_stage=5，对应待学习直线±2.5；账本UNAUTHORIZED、零使用、空attempts。
实际supervisor plan-only返回READY_NEEDS_AUTH/AUTHORIZATION_MISSING，CPU有效、写入0；
本轮没有PPO授权，因此此状态正确，不能挪用物理复核授权。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/motion_absolute_halfstep_PREPARED_20261007_v4/spec.json \
 --output-dir runs/motion_absolute_halfstep_PLAN_ONLY_v4 --physical-gpu 1
```

终态集中报告：`isolated/motion_recheck_20261007/final_gpu1/result.json`及`report.md`。
首次报告等待进程PID3195628因Conda Python未暴露os.pidfd_open退出；
该报告交付错误不影响评估child或monitor。修复为Linux pidfd syscall兼容路径，
CPU live/exited pidfd测试通过后，直接读取已完成终态生成报告，无重跑物理attempt。
报告核验child terminal、monitor_exit、ledger、checkpoint及快照SHA，
记录完整项逐环境指标和包含清理的墙钟。旧模型、旧账本未写入。

最终建议来源B250：同协议0/±1/±1.5/±2全部通过，保持段误差明显小于new250；
旧±.5原始trace新评分亦通过，但它与本轮新评估的执行身份分别记录。
后续最值得验证的一个变量是命令端点组成：保留旧能力，只加入±2.5。
工程配置/协议/结算未发现剩余阻断，但完整训练启动仍须新授权和所需来源证据校验。
prepared v4仅plan有效，不是已获得训练预算。当前无本任务训练/评估进程。
本轮不证明PPO退化唯一机制、不宣称±4或yaw/急停通过。
