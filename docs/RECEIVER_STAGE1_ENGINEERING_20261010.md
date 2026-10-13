# 多策略第一阶段工程交付（2026-10-10）

本轮仅代码/CPU/已有轨迹离线工作，无新Isaac/GUI/PPO或source optimizer。接线已实施，但真实source_eval/smoke/formal均NOT_RUN，不冒称控制交接训练已通过。两套最终声明UNAUTHORIZED、零used/零attempt、无对应run；旧B50/B250/checkpoint/evaluation/run/ledger保持只读。工作树已有大量其他worker改动，本轮不reset/clean/commit/push。

## 交付与生效边界

docs/MULTI_SKILL_ROADMAP定义Motion/Recovery/Jump/Traverse；只有前两类本轮接线，Jump/Traverse和高速/内倾尚为规划。Recovery计划顶部统一为组合恢复，不要求Recovery先单独站稳；旧顶部归档docs/history/RECOVERY_PLAN_PRE_MULTI_SKILL_20261010.md，下方历史原样保留。新0.5秒本体历史/command/action接口在handoff_ownership.interface_contract声明PLANNED及版本ID，未来须新模型/迁移认证；本轮仍native150D。

### 已接通的评估链

公共supervisor evaluation-only→既有monitor→evaluate_checkpoint→handoff_evaluator→HandoffEnv，共享原物理/PD。dual_frozen_handoff_v1固定22组保持可读；v2显式case_id、Recovery自身冻结spec SHA、checkpoint SHA、family、prefix、seed、组合协议和storage。前缀是合法初始化结束后的真实受控interval，任意0–5秒10ms整倍；未知字段拒绝、case重复ID拒绝。主2秒入口＋.20秒确认＋下一1000interval保持不变。可以另立extended_diagnostic仅延长观察≤5秒，身份不同，不回填main成功。

两套模型history持续更新，previous action从已执行实体目标按自身scale编码，切换不reset/写速度/托举/沉降。控制owner0初始化/1Recovery/2接收策略，scoring phase3为保持但执行者仍2，actor_valid与switch event/三种clock显式记录。新root字段改为实际安装IsaacLab3 xyzw，旧数值/证据不改；randomization纯worldZ yaw，CPU验证重力不变。

### 已接通的训练链

同公共supervisor→stand_chain→train.py→receiver_recipe/ReceiverEnv，不新建trainer/monitor。来源Motion B250 actor/critic/Adam/std，冻结B50及原B250额外只读加载。32Swing冻结B50 .50s＋32原生正常站姿，固定family配额，每rollout记录两组实际receiver有效transition比例。

PPO保存接管候选自己的requested action/logprob，compose_training_action产生真正执行的初始化/冻结前缀动作；不把冻结动作伪装成candidate on-policy样本。pre_action mask仅receiver控制true，初始化/冻结B50false、受控失败末步true。actor surrogate/entropy/valid-global normalization/KL/clip沿ControlledPPO，all-invalid actor gradient=None，原始reward/done/GAE/critic timeline不删步。storage附phase/time/executed action/left-first physical target；actor/critic仍150D且无共享参数。critic不直接读取metadata，有声明的partial-observability/别名风险；这是保持来源架构的首轮基线，不称已解决critic状态识别。

receiver reward对照B250冻结实际combined tracking，零命令linear denominator .04，height target .40、height_width .06、upright2/height2/tracking8/contact.5/effort−.02/action_delta−.01（wheel factor16.6667）/margin−.05，dt.01一次＋terminal−1。假声明separate/independent tracking项不迁入；保留实际cohort宽度规则，源reward源码CPU逐项等价。冻结前缀reward0、actor invalid；不继承support record或DrawBack位置引导。候选只负责接管零速，不称全部Motion替代品。

专用clock覆盖完整2秒收稳＋10秒保持，无旧11.5秒deadline截断。smoke要求真实prefix/handoff/receiver有效optimizer/episode结束/保存和身份；技能0/8不阻断工程smoke。评估重新运行Swing组合及正常站姿，逐env证书与combined gate；额外新episode候选完成同episode10秒后真实切回原Motion±.5m/s各5秒，诊断仅基础运动，不认证高速。原Motion控制归属4/receiver_actor_valid=false，保持history且不reset；phase配置、actor模式与RNG异常/正常都恢复。

## 已有轨迹离线结论

来源run2026_10_10-16_44__recovery_motion_b250_handoff_ppo0全部22组SHA及176逐env重新评分匹配；基线8/8、直接Swing0/8、B50 .50秒组合7/8。机器输出isolated/receiver_stage1_transition_events_20261010/review.json，具名schema和窗口、每trace SHA；入口后的下一1000interval保持、失败env仅首episode，未拼reset。

B50 .50秒条件初始化约.40秒、真实Recovery50interval=.50秒、首Motion是程序第91个policy interval（动作前.90秒），成功入口Motion1.21–1.24秒后，随后10秒。不能把程序.50秒当前缀.50秒。

切换时height约.184m、pitch约−.220rad/roll≈0，腿长左右约.289/.201m，native vx≈+1.19m/s，仍非对称低位；不是先到DrawBack静止再切换。首Motion实体目标与原Recovery目标有四腿约[−.917,+.707,+1.482,+.334]rad跳变，两轮约−7.91/−9.36rad/s，previous action约50%通道超Motion包络。成功也有这些跳变，不据此断言必须blend。

成功env0平面路径：初始化近0；Recovery约.239m；Motion入口前约2.517m（首失双轮接触前.259m、非双轮到首次恢复双轮.393m、首次恢复双轮到入口1.866m）；保持约.759m。native vx积分分别约.249、2.298、.713m，测量轴/姿态导致它与world平面路径不是同一量。主要前进距离来自Motion接管后的收稳段，不自动称轮空转。首次失双轮接触约Motion.16秒，恢复双轮约.32秒；这只是>2N合力事件，不能等同腾空/法向载荷或因果证明。

失败env4前缀几乎相同、动作跳变相近，首Motion到截止平面路径约2.965m。与env0相近的早期角速度峰约4.97 vs5.00rad/s，不能仅凭角速度峰区分成败；截止roll约+.116rad、连续入口最长.09秒，已height约.387m但未满.20秒水平确认。成功环境完整保持roll平均约.018–.024rad，峰约.088–.103rad。早B50 .25秒vx≈.43/晚1秒vx≈2.37/2秒vx≈2.95均倾角失败；构型、速度、接触、history共同变化，未确定唯一因素。

## 最终独立声明与预算

| 项目 | 声明 | 内容 | 上限 |
|---|---|---|---|
| 邻近窗口PPO0 |2026_10_10-22_24__receiver_window_ppo0|正常基线＋B50 .40/.45/.50/.55/.60×seed20261010/11/12，16组×8=128评分episode，64simenv|PPO0/optimizer0，1800s含清理，512MiB|
| receiver短训 |2026_10_10-22_19__receiver_zero_from_b250|Motion B250初始化，冻结B50 .50秒，32/32，64×128|smoke20/formal100，120updates/983040samples，7200s含清理及评估|

每组seed真实用于初始化world-yaw uniform±.01rad，仅Swing扰动、基线原生不扰动；读回保存root全状态，CPU证明不同seed实际不同q且不改变重力，不冒称3training seeds。该合法小扰动仍需runtime初始化证书。训练不加此扰动，保持首轮已测前缀。

训练source_eval900/smoke1500/formal4700合计7100秒＋100秒清理预留=7200。source PPO0含Swing/正常两组和接回原Motion两组；formal25/50/100各相同完整评估，阶段预算已包含评估，不额外加余额。单次source/smoke提交不是formal更新证据，formal从来源初始化不继承smoke。窗口诊断应先运行复盘再进入短训。

同分钟此前22_18窗口draft是缺case独立Recovery spec字段的未授权准备，不能提交；只用最终22_24。未授权draft仍零attempt，无删除旧记录或自动扣用余额。

准确CPU public plan和运行CLI只在TOOL_INDEX维护。本报告不复制命令。两套plan preflight仅报新预算未授权，未核查实时GPU资源，submit_ready=false是正确状态，不是当前GPU可用证明。收到新授权后再核验physicalGPU0/UUID/logicalcuda0共享及完整发布标记，不停止他人、不自动换卡。

## CPU与冻结结果及限制

最终针对性70项通过（含真实public evaluator CPU假环境完整流程、真实optimizer内存副本、masked storage元数据、shared planner/预备器/schema、奖励冻结对照与临时状态/RNG恢复）。内存CPU optimizer更新用于测试独立副本，原checkpoint SHA未变，不计在线PPO。

最终项目全CPU回归762passed/22fixture errors/2warnings。22个错误全部同一tests/test_motion_engineering_recovery_certificate.py fixture：旧冻结Motion将command_v6/runtime/configure.py列为必须SHA不变，当前已有dirty SHA不同，证书拒绝。旧SHA52e99f96a7545ea7ef766fd82ed7b0efb37badf0c36262b5c830fd577ae63a01、当前c6db5373a6371a1c6dec8437c52b24ee8a2b4708b826339c3d4bd2b15f1b76e5；本轮没修改configure.py，本轮开始前artifacts/recovery_motion_handoff_quaternion_cpu_20261010也绑定同当前SHA。其他Motion关键control/reward/network文件SHA与该旧manifest一致。具体证据isolated/receiver_stage1_cpu_validation_20261010/baseline_full_suite_failure.json。未改证书、未将错误全套称通过；该旧Motion恢复证书阻塞不等于新receiver相关CPU失败。

最终冻结验证evaluation17 PORTABLE、training14 PORTABLE通过，必须在最后源码版本再验证（delivery目录）。checkpoint初始化actor/critic/std差异0，Adam preserved，optimizer step0；传感输入仍150D，source_std physical腿约.0276/.0218/.0305/.0278rad、两轮2.289/1.693rad/s不改。冻结验证artifact位于artifacts/receiver_stage1_window_delivery_cpu_20261010及artifacts/receiver_stage1_training_delivery_cpu_20261010，逐module SHA+plan+schema+tests保存。

物理未验证：新yaw扰动初始化、实时切换smoke和actor valid计数、随机训练触限/有效样本份额、receiver学习质量与接回原Motion行为、wall/resource实际吞吐。CPU通过不证明这些物理结果。

## 精确本轮文件

新增：recovery/handoff_ownership.py（owner/clock/版本化接口草稿/yaw）；receiver_contract.py（strict spec）；receiver_runtime.py（共享HandoffEnv训练接收者）；receiver_recipe.py（公共环境与评价）；scripts/prepare_receiver_stage1.py（public publish）；tests/test_receiver_stage1.py（PORTABLE）；tests/test_receiver_public_boundary.py（实际项目边界）；docs/MULTI_SKILL_ROADMAP.md、本报告、历史顶部归档。

增量修改：recovery/handoff_protocol.py（可配置version/时间）；handoff_requests.py（v1/v2兼容和IDs）；handoff_clock.py（专用协议与受限defer）；motion_handoff.py（独立命令/配置score）；handoff_runtime.py（初始化扰动/协议/clock）；handoff_evaluator.py（case自己的model spec/owner记录/版本协议）；recovery/validation.py（receiver显式验证）；command_v6/config.py/domain/recipe.py/train.py/tools/preflight.py/wiring.py（可选receiver公共训练调用）；tools/evaluate_checkpoint.py（receiver版本协议）；tools/evaluation_state.py（恢复receiver临时变量）；tools/play.py（消费同协议/seed）；scripts/prepare_recovery_motion_handoff_scan.py（xyzw注释纠正，无旧spec改变）；scripts/review_recovery_motion_handoff.py（逐阶段和接触事件离线）；STATUS/TOOL_INDEX/ARCHITECTURE/WORKFLOW/RECOVERY_STANDING_PLAN。两套spec/pose/ledger/publication marker/CPU artifacts及isolated机器结果是新路径，旧证据未覆盖。

## 集中待运行请求

请求新授权：physicalGPU0共享但不停止他人、不换卡，先16组/128评分episode PPO0≤1800秒/512MiB；正常基线失败停后续。完成复盘且无接线/初始化/runtime故障后，独立receiver source_eval+smoke20/formal100（共≤120updates、≤983040rawsamples、chain≤7200秒，评估含在预算）。两实验合计wall≤9000秒；失败不自动重试，不追加预算，不自动长训，训练既有owner结算且只做一次启动握手。若用户仅授权其中一项，则只执行该项。

AGENTS.md明确“CPU/文档工作不授予仿真、GUI、采样、PPO、通知或续训权限。PPO0也是仿真，仍需明确授权。”当前此任务无覆盖新声明的运行授权，所以尚未提交。
