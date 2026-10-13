# Level2 update50事件对齐与弱轮心对齐短训练

## 新授权重提：2026_10_7-20_55__recovery_level2_alignment_from50

用户在20_42来源接口失败后明确重新批准同一四步方案；新独立spec/预算，旧账本使用保留。
复用已完成SHA绑定的事件/窗口复盘，不重复仿真补采；来源、物理、reward、PPO、
DrawBack/R0和评估与20_42声明逐项相同，只有执行接口修复、新身份与授权。
新spec：configs/experiments/2026_10_7-20_55__recovery_level2_alignment_from50/spec.json；run同名。
source600s/PPO0、smoke10/600s、formal<=100/3600s，总<=110/901120样本，25/50/100评估。
485 CPU passed（18.94s）；supervisor plan PASS、health OK、零写入及旧ledger/terminal SHA保持已验证。
新链已提交，submission_verified=true，握手SOURCE_EVAL，formal_first_update_verified=false。
worker3673383、exact attempt30710f982235429290d336d933414aa3，进程/session/GPU身份匹配。
此次仅新增20_55配置/spec、poses、preparation_manifest、verification与本地独立预算，
更新README、STATUS、RECOVERY_STANDING_PLAN和本文；未再改训练源码或历史证据。

## 最新终态更正：FAILED，零PPO

原始chain_terminal_report与source_eval/terminal_report优先于下方提交握手记录。
source_eval在评分协议校验时退出：ValueError unknown or malformed standing_protocol fields；
新增evaluation.full_trace_updates被train作为standing_protocol传入，PROTOCOL_FIELDS遗漏它。
source_eval已使用1次，smoke/formal均0，actual_updates0；不是模型行为失败。
当前共享代码已补显式白名单，并增加真实训练evaluation声明的边界回归；未知字段仍拒绝。
冻结失败副本、历史spec/ledger不改写，不自动重提；新运行需新声明/独立路径与明确授权。

用户明确批准：先离线复盘，再单变量配方，smoke10/formal最多100，25/50/100筛选。
新声明根`2026_10_7-20_42__recovery_level2_alignment_from50`，不继续旧链。
来源18_06/formal/model_update_50.pt SHA de06b39d2a88c44250309b4ae0509188b532cc5c51a681d456a545c307243694。
资产SHA32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7。

## 离线事件复盘

脚本`scripts/review_recovery_geometry.py`；证据
`isolated/recovery_update50_geometry_event_review_20261007/review.json`，逐输入SHA。
原始23秒×8env数据只读，无仿真或optimizer更新。

|阶段|8env的实测恢复时间范围|几何/高度|
|---|---|---|
|首次满足站立入口条件|7.760–7.910s|轮心水平纵向错位约33.2cm|
|入口后错位首次超过40cm|9.220–9.380s|高度约0.343m，仍双轮接触|
|入口后高度首次低于0.34m|9.290–9.440s|错位约40.7–40.9cm|
|入口后首次双轮失触|10.100–10.260s|错位约50.1–50.5cm，高度约0.277m|

这是先后顺序而非因果证明；同seed/同初态的8env也不是8个独立训练随机流。
保持段错位均值24–28cm、峰值约70cm，腿长差均值约2cm；不能互相替代。
8env完整观察但起身后10秒保持0/8，fault0；此前肉眼抬升不等于完整起身认证。

## 评分窗口核准

实际使用slice[start:start+1000]，恰好1000个100Hz样本，首次满足入口后不重选窗口。
post_rise_window_s是[start*dt,(start+1000)*dt]的轨迹索引边界，env0为[8.14,18.14]。
recovery_s是series[start,0]的恢复计时，env0为7.76008s；初始化期间此计时不推进。
二者不能直接相减解释策略事件。逐环境复算入口、完整窗口、failed_checks、
高度比例、接触比例、高度均值均与原始评估一致，不改历史评分。
此前交互按(arange+1)*dt筛选窗口会混入入口前一帧，错误显示入口即高度不合格；
本报告按精确索引切片纠正：env0首次高度离带为恢复9.290s。

## 单变量配方与量级

仅增加连续成本：
`-0.1 * clamp((h-.32)/.04,0,1) * (relu(abs(horizontal_wheel_offset)-.04)/.20)^2`。
单位为每秒奖励；在process_reward中乘policy dt=.01一次，初始化步原有逻辑归零。
不是硬锁、动作投影、对称网络、制动、轮速平滑或腿长惩罚。

8env已有轨迹的保持段平均成本约-.069至-.101/s，峰值约-.374至-.392/s；
保持段lift平均约+1.886至+1.890/s，standing_height约+.881至+1.058/s。
低于.32m成本严格为0；尺度分析不证明PPO梯度大小或训练收益。

保留原DrawBack+40%R0、source50 actor/critic/Adam、LR3e-5、64×128、height.36、
原抬升/姿态/接触奖励与起身验收、限位USD、动作和PD/40/5.5Nm控制。
smoke与formal分别由source50启动，不以smoke末尾或退化100作为下一阶段默认来源。
明确full_trace_updates25/50/100保存完整几何/姿态/接触/控制；不新增评估次数。

## 独立授权与执行

source_eval最多600s/PPO0；smoke10最多600s；formal最多100/3600s；
总在线更新<=110、样本<=901120；链墙钟4860s含原有结算余量；不跑100秒durability。
GPU0 shared，当前session由CLI核验，不停止其他进程、不自动重试或扩大课程。
新source评估同协议起身和R0；普通能力失败可训练，初始化/闭链/证书故障阻断。
完整gate和R0回归共同选模；未全通过仍报告未认证，奖励或几何改善不冒充能力。
后台supervisor负责source→smoke→formal和终态通知，交互只一次启动握手，不轮询。

## 本次文件

新增scripts/review_recovery_geometry.py、scripts/prepare_recovery_alignment.py、
tests/test_recovery_alignment_probe.py、新spec/poses与本报告（budget/证据本地保存）。
修改recovery/domain.py（显式可选高度门控）、recovery/validation.py（仅rising有门控允许该成本）、
command_v6/config.py与train.py（选定完整评估保存全过程）。
更新README、STATUS、ARCHITECTURE、TOOL_INDEX与RECOVERY_STANDING_PLAN导航。
旧配方无新增gate字段时成本语义保持；holding仍拒绝添加此对齐成本。

## 验证与提交回执

完整CPU474 passed（18.47s），git diff --check通过；plan-only PASS，spec/ledger SHA未变，无run创建。
2026-10-07通过supervisor提交，submission_verified=true，当前握手SOURCE_EVAL；
formal_first_update_verified=false，不能宣称formal PPO已经开始。
worker3658116，exact chain attempt9236c584719e44198cdfda2a0bae570f；
argv/start/spec/output/GPU0/current session全部核验，shared/preemption=false。
一次资源检查与启动握手后结束交互，不轮询或自动续训。

失败后工程修复验证：完整CPU485 passed（18.44s），git diff --check通过。
新增修改command_v6/domain/evidence.py；扩展tests/test_recovery_alignment_probe.py。
本次只修共享源码和交接文档，未新建运行、未预约预算、未启动模拟/PPO。
