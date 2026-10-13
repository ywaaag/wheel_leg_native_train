

# 以下为历史章节，可以不用看
## 0. 当前有效决策 — 2026-10-12 持续Swing课程

11_42 B1.80课程已FAILED：smoke12＋formal185；update100三组24/24入口与完整观察窗口，但0/24验收，接触/触限/速度仍失败。用户本次批准无限累计预算并要求惩罚约束：新v10从已保存B100 Actor继续，只加首次入口后弱失触成本，起身过渡仍允许腾空。新Critic/Adam、warmup5、smoke12，再按原动态课程自动推进；历史509更新消耗继承，未保存的85次不声称恢复。原故障具体类型UNKNOWN，补全64环境pre-reset证据、保留所有物理保护；再次工程故障不自动重试。见[新配方与恢复](RECOVERY_CONTACT_SUFFIX_RESTART_20261012.md)。

用户已持续授权同一个31D Recovery学生按计划自动学习，不设累计PPO更新上限；每个子run仍formal≤300、全块≤4小时、≤2GiB、独立账本。来源为00_12 update300（normal候选未accepted）。先A只加入口后弱轮目标平滑，formal最多600，随后B真实冻结B50/B250前缀1.80→0秒、学生学习后缀；32/16/8/8，最终无教师56/8巩固和两次32环境认证。辅助后缀、normal与无教师Swing严格分开；最终目标仍学生自主Swing＋10秒，不回到长期站立专项或反复蒸馏。

同配方保留Actor/Critic/Adam/RNG与课程，新reward只首次初始化/warmup；受控mask同时用于Actor与Critic但保留GAE时间轴。三块停滞有限回退/细分，仍无进展NEEDS_DESIGN；工程故障/用户停止停链。持续授权已覆盖计划内续训，不每300更新重新申请；超出任务的接口/物理/控制变更仍另立决策。具体工程和执行证据见[持续课程](RECOVERY_CONTINUOUS_SWING_COURSE_20261012.md)。

### 历史决策快照（2026-10-11，不代表仍在运行）

当时已按用户明确要求从站立专项update50继续：22_43 motion_mirror_from50_v6继承该Actor，Critic/PPO Adam重新建；原站姿reward保留，新增Motion祖先联合零速tracking（最大+4分/秒）及weak actual-q mirror（最大−.2分/秒），不平均执行目标、不锁左右、不加Progress/32D。固定31D/64normal、小yaw/物理/验收不变；首段smoke12＋formal300（25/50/100/200/300），312updates2555904samples/12600秒/2GiB，站姿能力与Swing回归分开，source和早期候选保留。来源和新联合配方差异、离线量级及实际提交见[update50继续学习](RECOVERY_STANDING_MOTION_MIRROR_FROM50_20261011.md)。

最新GUI后续实验：Motion原站姿label非严格镜像；离线mirror-targets候选BC5000＋22_28 PPO0已完成。新学生腿更齐，但normal约.56秒即倒、完整保持0/8，较未mirror BC1.17秒退化；不替换站立专项PPO50、不续此mirror模型。不能把“更对称”当“更稳定”，下一保留成功Motion真实反馈，对称仅独立辅助要求，不直接把teacher标签平均当成功动作。Progress已给出可部署受控计时0~1纯CPU提案，未来需独立32D/41D显式版本；当前仍31D，不靠timer称起身进展/成功，不混合本轮mirror与新接口。详见[镜像/Progress复盘](RECOVERY_STATIONARY_MIRROR_PROGRESS_20261011.md)。

当前已获新授权推进基本站立专项PPO：20_46 v5从站立关键帧蒸馏学生SHA06c33c…e365开始，64normal训练、小yaw±.01，单Actor全程Recovery、BC0、新Critic/Adam、31D/物理不变，Swing仅回归。首段smoke12＋formal300（25/50/100/200/300检查），总312updates2555904samples/12600秒/2GiB；站立专项通过与Swing完整起身分别认证，不混为accepted能力。完成验证后公共supervisor sharedGPU0提交，实际单次握手见[提交报告](RECOVERY_STANDING_PPO_SUBMISSION_20261011.md)。

最新站立补教终态：同一Recovery学生完成两版BC，第二版提高normal首20步采样；normal入口8/8但约1.17秒后倒、完整10秒0/8，原BC约.37秒倒，B250基线8/8。Swing回归仍0/8，不能宣布基本站立已学会。接下来聚焦normal闭环最早偏离与教师状态覆盖/有界站立学习，不再凭整体BC误差放行；新模型是站姿实验候选而非完整起身accepted。完整证据见[站立补教](RECOVERY_STANDING_DISTILLATION_20261011.md)。设备按用户偏好先测速选快者，此次小网络共享GPU下CPU梯度batch较快；网络/接口不变。

第一交付仍是同一个Recovery学生独立Swing起身并完整保持10秒，然后验证Motion交接。31D/40D、物理参数和验收不变。

15_25角速度成本实验已formal100完成，仍无入口0/32；它降低剧烈倾倒但没有建立持续支撑。离线按第一次抬升峰值对齐，教师也腾空和短暂低于.30m。学生回落时腿更长、支点构型偏离，下一先测该真实动态状态是否在B250的局部教学范围内，不直接加强接触奖励/制动/对称或继续长训。

16_21原attempt因评估family接线工程FAILED，5.3704秒独立保留。修复后16_43已获明确新授权并COMPLETED：9组72评分episode/203.3126秒/PPO0；B250正常基线和原B50 .50秒组合均8/8，学生new100 .30–.65秒七个接管时刻均0/8，无入口，全部真实切换后倾角终止。逐环境重评分、31D输入、previous-action/物理缓存和连续Motion历史核验一致。

用户明确授权后续训练，并提出站立鲁棒性辅助落地收稳。下一已落实17_12 v4混合课程：同一个31D学生从原BC开始，32Swing继续完整起身＋32B250原生正常站姿学习小角速度扰动收稳；单Actor全程Recovery、BC0、无教师救场、物理和PPO参数不变。Swing沿用v3奖励，normal补齐已站立状态的高度参考语义，不叠加腿长/对称/制动。首轮smoke12/formal100，25/50/100检查；Swing四组主选模、normal单独报告，不以站姿通过冒充自主起身。112更新/917504samples/7200秒/2GiB是执行worker选定的首个决策段，不代表无限自动续训。工程验证和提交证据见[站立辅助课程](STUDENT_STANDING_REHEARSAL_SUBMISSION_20261011.md)。

此前七个接管时刻均失败，仍不能在这些失败状态直接补B250教师标签；没有启用新BC、blend、短历史或GRU。当前完整自主起身尚未通过，抬升后支撑衔接仍是主要瓶颈。本阶段结束按Swing入口与完整保持实测决定下一变量。

以下13_35/14_32预算与“未授权”描述为各自当时记录，不代表当前再授权或仍在训练。

目标：合法Swing及既有小yaw扰动→同一个Recovery学生全程收腿、转腿、抬升、收稳→同episode完整10秒保持。B50和B250的成功组合是该学生已有教学来源，运行时不执行教师前缀/切换/救场。暂停MotionZero，Jump/高速/量化/真机不在本轮。

当前接口multiskill_mcu_v2，31D Actor当前帧、40D privileged Critic，Actor31→128→64→32→6、ELU/tanh；无历史、GRU或新增阶段输入。保留1.5rad/100rad/s目标、USD/Plane/PD/1/5/10ms及40/5.5Nm。1182D multiskill_student_v1仅属下面历史蒸馏/首次评估范围，legacy150D不变。

接口、控制归属、有效reward、终止与预算验证后，允许未成功学生进入有界PPO；完整恢复是学习目标，不是source、smoke或formal能力前置条件。当前固定BC学生SHA 7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470；本轮不新增BC、不选其他起点，lambda_BC=0。Critic和PPO Adam新建、每阶段前5次更新仅Critic、std固定腿.05rad/轮2rad/s。

recipe student_recovery_ppo_bc_v1与输入版本分别绑定；初始化false mask保留真实GAE，post-physics/pre-reset计算任务reward。首次入口≤2.5s确认.20s，下一固定1000interval完整证书，窗口完成不等于成功；真实失败/工程故障/预算截断单列。source行为0/32可继续，只须工程有效及教师对照正常。没有DrawBack/R0保留或旧retention。

本轮独立授权source40评分episode/900s、smoke12/98304/900s、formal100/819200/5400s，全链112更新/917504/7200s、产物≤2GiB。完整评估25/50/100，同四组选模，再选定单模型原生＋三新小yaw复核32。普通跌倒/没起身不取消formal；工程错误不自动重试。公共supervisor一次握手，既有owner结算，不轮询守候。

### 2026-10-11：PPO100之后的有效下一决策

13_35已完成100次formal且664895有效Actor样本，完整入口仍0/32。离线分析显示双侧收短保留，但BC的抬升失败被更新为低位拖至2.5秒deadline；31D输入重建/dt/事件/mask未发现对应错误。gamma=.99使晚发生的−1失败事件折扣更小，固定轨迹回报优于BC，构成优先检验的奖励偏好。此为机制假说，不是唯一根因证明。

下一准备14_32独立failure_zero：同一31D学生从原BC重新开始，唯一主要变量failure_once −1→0；失败事件、真实终止、物理保护、入口deadline、固定10秒窗口与验收不变。BC0、std/网络/LR/GAE/物理不变，无教师运行救场。预算source40/900s＋smoke12/900s＋formal100/5400s，总112更新917504samples/7200s/2GiB；UNAUTHORIZED零attempt。若仅早倾倒增多但仍无入口，明确未跨瓶颈，不自动续训。具体数据/限制见[复盘](STUDENT_RECOVERY_PPO100_REVIEW_20261011.md)。短历史暂作为后续独立候选，当前不加。

### 历史：1182D学生蒸馏契约（2026-10-11较早批次）



当前目标：新RecoveryStudent从合法Swing（首版含小yaw扰动）开始，初始化结束后全程独立控制收腿、转腿、抬升、落地与10秒保持。旧B50→B250组合只作教师和冻结对照；不在学生0.50秒时切任务标识或调用教师救场。实际关键转腿和抬升由旧Motion B250完成，教师历史名称不限制教学职责。

当时接口固定为 `multiskill_student_v1`：51×(22本体字段＋1有效标记)＋9任务输入＝1182D Actor；1191D Critic另外读声明的高度、真实native线速度、接触与阶段计时。Actor仅IMU与关节反馈/实际执行目标历史，无教师ID、未来成功或仿真特权量。学生任务标识整条示教始终Recovery。legacy150D严格保留。

新独立协议 `student_autonomous_swing_v1`：首个学生受控动作开始≤2.5秒确认连续.20秒入口，之后同episode连续1000个10ms interval保持；高度≥.30（允许.42）、既有水平/接触/闭链/采样触限与主零速标准不放宽。过渡期允许失触，不套保持约束。旧组合协议和历史结果不改。

本轮CPU示教：旧7条成功＋最新24条小yaw成功，按15/8/8完整episode训练/验证/测试；四阶段均衡，重复采样不当新经验。Recovery BC 5000步，Motion仅零命令BC 2400步；动作拟合达标不代表闭环能力。旧receiver终态首次检查时尚未存在，由原owner继续负责；不作为新版前置，也不默认升级其checkpoint。

当时下一决策依据新学生独立闭环证据：拟合差先修编码/标签/拟合；拟合好但早偏离，定位最早偏离准备有界补采；该批次曾限制完整恢复后才准备PPO；此能力前置现已撤销，按顶部工程条件允许有界PPO。Actor来自学生BC，Critic与PPO Adam重新初始化，不继承教师或BC optimizer；示教loss单独计算，初始化mask与完整GAE时间轴保留。

本轮未运行Isaac/GUI/采样/GPU训练/PPO。10组80评分episode/1800秒/512MiB独立物理验证声明未授权，正式文件、SHA及误差见[学生交付](STUDENT_DISTILLATION_DELIVERY_20261011.md)，命令只维护TOOL_INDEX。Jump、Traverse、压弯仅预留任务接口，不登记已实现能力。

## 0.1 学生首次独立闭环结果 — 2026-10-11

新学生PPO0已完成：Recovery原Swing＋三小yaw组0/32，教师组合32/32；学生峰高约.385m，31/32倾角终止、1/32入口deadline，不能把拟合达标当恢复通过。Motion零命令学生入口8/8但保持0/8，原B250正常8/8。下一先离线定位受控.7–1.2秒抬升后偏离及正常平衡反馈；暂不追加PPO/BC或新采样。原始结果、逐env/阶段指标与最小后续范围见[独立验证复盘](STUDENT_PPO0_COMPLETED_REVIEW_20261011.md)。此前00_55未授权描述仅对应发布时快照，现已按本轮新授权执行并exact-ID结算，授权不提供续训。

## 历史执行进展与阶段性建议 — 2026-10-08至2026-10-09

以下“当前/下一步”属于各记录当时语义；后续执行以第0节的2026-10-10 Swing-only任务契约为准。

**2026-10-09最新终态：500预算并未跑满，smoke10＋formal100后腿触限退化保护停止。** 25/50旧组contact-only已正常放行，100 DrawBack触限失败非接触失败，R0恢复8/8；Swing仍无入口0/8，镜像明显改善但轮子未进DrawBack。901120样本/36.1分钟，余额390不自动继续。下一CPU审核更有辨别力的双侧收腿位置进展及旧腿预载，不取消触限或增矩，不续new100。[完整复盘](RECOVERY_CONTACT_DIAGNOSTIC500_COMPLETED_REVIEW_20261009.md)。

**2026-10-09当前运行：用户批准总500在线更新的新独立contact-only记录实验已提交。** 21_58声明smoke10/formal490、4096000样本、chain≤23460秒；来源10_58new25，奖励不改，旧组完整hold且仅contact失败不提前stop，其余保护/gate不变。冻结5/check READY，一次握手SOURCE_EVAL/worker身份OK、formal首更新未核验。formal10/25/50/100/200/300/400/490完整三组筛选，等终态通知，不轮询不追加；此前未授权文字为准备历史。[预算与握手](RECOVERY_CONTACT_DIAGNOSTIC500_SUBMISSION_20261009.md)。

**2026-10-09最新CPU交付：奖励组件分解＋仅旧保持连续失触不提前停训的独立候选已准备。** 不同时改reward，来源仍10_58new25；旧组完整hold且仅contact证书失败时记录退化，其余失败/数值物理预算保护保留，评分gate不变。总100在线候选2026_10_9-21_49__recovery_drawback_contact_diagnostic_total100未授权，Recovery233/冻结5通过，无runtime。需针对新预算批准，不搬旧剩余40。[配方与停止条件](RECOVERY_CONTACT_DIAGNOSTIC_PREPARATION_20261009.md)。

**2026-10-09最新终态：DrawBack镜像reward完成收尾、formal因旧组连续退化停在50。** smoke10+formal50/491520样本/45.8分钟，未用40不继续。奖励真实生效、镜像改善（相同前300ms .329→.231rad），但轮心目标只接近约3.2mm、右腿仍.376m，Swing全无入口；旧组25/50连续失触失败。下一先CPU分解位置/对称质量及构型方向，再决定独立双侧进展候选，不接受new25/50，不增权续latest。[完整复盘](RECOVERY_DRAWBACK_GUIDANCE100_COMPLETED_REVIEW_20261009.md)。

**2026-10-09当前执行：用户批准新奖励总100次，按smoke10＋formal≤90限制总额。** `2026_10_9-18_39__recovery_drawback_mirror_guidance_total100`已supervisor提交，SOURCE_EVAL握手/worker身份OK，formal首更新未核验。819200样本/chain≤9060秒，10/25/50/90三组完整评估，旧退化保护保留，不追加/不轮询。旧25候选仍未授权；行为等待终态原始证据。[具体预算与握手](RECOVERY_DRAWBACK_GUIDANCE100_SUBMISSION_20261009.md)。

**2026-10-09最新准备：DrawBack轮心位置×镜像质量稠密reward正式接线CPU完成。** 每秒1分/.22–.30m平滑退场，原奖励及控制保持，纯额外reward、不切actor、不加观测记忆；低位腾空/驻留收益仍存在，需短块证伪。独立`2026_10_9-18_34__recovery_drawback_mirror_guidance_from_new25`已发布UNAUTHORIZED，Recovery238/冻结5通过，无runtime。下一明确批准35更新286720样本/chain5460秒预算后才登记并提交。[具体配方、验证和风险](RECOVERY_DRAWBACK_GUIDANCE_PREPARATION_20261009.md)。

**2026-10-09最新设计：用户选择朝DrawBack轮心位置推进并要求镜像对称的奖励实验，不用固定秒数角度轨迹或严格动作投影。** CPU耦合质量原型与真实反事实已完成，软奖励不能保证完全对称；下一明确动态目标衔接起身、驻留/腾空/终止与原reward量级，再接真实读回和独立声明。保留旧技能原协议，禁止将CPU候选当已接线/已提交实验。[设计与准备边界](RECOVERY_DRAWBACK_MIRROR_GUIDANCE_PROPOSAL_20261009.md)。

**2026-10-09当前结论：已完成A/B固定输入与旧保持失触离线诊断。** B25中心loss真实下降6.63%，但起步两hip仍偏离局部收短路径，右腿仍.37599m；旧组失触不是env0明显剪刀腿/roll增大事件，而是在持续腿目标误差、轮差速及接触波动后出现。未确诊唯一原因，不接受B/不续latest。下一候选须明确改变关键动态收腿/转腿学习信号并核查旧输出迁移，不再把仅拉近当前q当成功桥接；先CPU设计，新runtime/PPO另授权。[诊断交付](RECOVERY_LEG_CENTER_TRANSFER_REVIEW_20261009.md)。

**2026-10-09最新：腿中心A/B默认关闭工程接线与正式声明准备完成。** 两臂同源10_58new25，B仅加lambda=.1/preclock前100ms腿中心辅助loss，保留奖励/std/控制；失败step排除、PPOclip→aux→actor reclip、真实smoke事件证书均已接线。各冻结9项CPU通过；全仓库720pass/22 Motion历史configure身份ERROR。各smoke10/formal25，总70更新573440样本；UNAUTHORIZED/零消耗、无新runtime。下一须明确批准这两个新短块预算，再核验并经supervisor提交；不扩展手写动态adapter。[本轮完整交付](RECOVERY_LEG_CENTER_AB_PREPARATION_20261009.md)。

**2026-10-09目标reward审核完成：** 负距离成本在冲高越gate后可减免，且带新增累计负cost的早终止权衡；硬双侧质量bonus在真实Swing8env全为0（一腿始终长导致乘积截断），还有短腿驻留激励。暂不把两候选接训练。下一CPU应改为真实Swing区域有辨别力的平滑几何项，并显式审核驻留/阶段语义，单公式不叠加，先完成信号要求再发布spec。[反事实与场景审核](RECOVERY_GEOMETRY_TARGET_AUDIT_20261009.md)。

**2026-10-09最新CPU审核：** 低位收腿/向下支点几何已核算，Swing八env确实几乎不收短；严格PBRS吸收terminal归0时，固定初态完整折扣回报为常量，失败末步释放正项，不提供新增收腿目标。因此不把PBRS直接接入短训。下一准备明确改变目标偏好的bounded几何项，先审核早死/冲高gate/必要转姿/回报量级，再决定新reward声明；不叠meanaux，不运行PPO。[审核与下一步骤](RECOVERY_SUPPORT_GEOMETRY_AUDIT_20261009.md)。

**最新优先方向：浙江大学原PDFRecovery知识已核验，转向低位“收腿＋形成向下支点”的几何进展奖励CPU设计，暂停继续增lambda。** Swing原轨迹腿长约.375米始终不收短；成功DrawBack起点约.15米，保持时允许伸长。首候选为具名hip→wheel真实几何的有界势能进展，先核准终止/timeout与系数量级；不硬接状态机/LQR/零轮矩，不永久短腿。不叠mean辅助或轮矩成本，未授权新训练。[原资料与新方法](RECOVERY_ZJU_GEOMETRY_METHOD_20261008.md)。

lambda.03块已完成并复盘：smoke10/formal25，旧组全保留、Swing无入口；aux梯度实际约9.46%但轮clip仍近100%，不继续单凭norm增lambda。收尾因ENOSPC未写链报告/通知，现另写isolated/recovery_aux003_completion_recovery_20261008/completion_report.md并按授权补发；原run不改。下一先实际更新方向/Adam证据或独立reward机制准备，未授权续训。

用户已批准lambda.03独立短块并提交`2026_10_8-20_39__recovery_swing_mean_aux003_from_b25`，握手SOURCE_EVAL、formal首更新未验证；v2与旧v1系数语义分开，B25/std/Adam/reward/control保持。smoke10/formal≤25、full10/25，35更新/286720样本、chain5460秒；当前会话终态自动通知启用。下方“预算未授权”属审核阶段历史。[提交交付](RECOVERY_MEAN_AUX003_SUBMISSION_20261008.md)。

独立系数量级CPU审核完成：lambda.03候选按旧训练估算aux/incoming clipped actor norm约9.47%，CPU单步较零系数Adam控制使Swing轮mean向边界移动但仍越界，旧组输出小幅变化；非PPO重放/起身证据。建议新版本固定.03、smoke10/formal≤25、10/25完整评估，总35更新/286720样本、chain≤5460秒；尚未发布/授权runtime。自动通知权限已有，下一新spec冻结启用当前负责人目标。[审核](RECOVERY_MEAN_COEFFICIENT_AUDIT_20261008.md)。

方案A已COMPLETED并复盘（smoke10/formal50）：旧DrawBack/R0全保留，Swing10/25/50均无入口；aux hook800次有效、平均norm约传入已裁剪actor梯度的.316%，轮mean仍越界，未解除裁剪。微小峰高.231→.233不算成功。下一不继续latest或原预算，先准备独立mean系数CPU量级审核；B仍独立后备，未授权新运行。[复盘](RECOVERY_WHEEL_MEAN_AUX_REVIEW_20261008.md)。

第8.6节方案A用户已批准，真实接线/CPU审核完成并提交`2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25`，握手SOURCE_EVAL、formal首更新未验证。当前rollout固定辅助batch/全部受控分母，每optimizer step复用，PPOclip→aux→actor reclip；reward/std不改，B关闭，smoke10/formal≤50、10/25/50完整验收。通知仍禁用，后续结果以原始run为准。[本块交付](RECOVERY_WHEEL_MEAN_AUX_SUBMISSION_20261008.md)。下方“尚未接线/未授权”属准备阶段历史。

**当前下一步：先完成方案A的工程接线和CPU量级审核，再准备一个smoke10＋formal最多50更新的新短块。方案B只保留为独立后备，不叠加。完整步骤、预算和转向条件见第8.6节。** 本次用户要求更新计划，不授权新runtime/PPO或通知；现有候选函数尚未接入训练。

用户批准参考奖励工程及传统Recovery摘要准备独立候选，已CPU核算：优先A仅Swing/pre-entry轮rawmean越界辅助loss（lambda=.001、margin=.9，std/奖励不改）；B独立后备为低位physical clipped wheel-effort弱cost（−.1/秒，.20–.32米gate），Swing每env反事实约−.0198，R00。两方案未runtime接线/未生成可提交spec/未运行，不叠加。开源文档缺原仓库/版本，浙江大学实机身份尚未独立确认；不复制LQR/虚拟腿/零轮矩控制。[候选与量级](RECOVERY_CONTROL_PRIOR_PROPOSALS_20261008.md)。

真实150D输入—动作—奖励PPO0已完成：`2026_10_8-17_39__recovery_b25_input_action_reward_probe_ppo0`，147.458秒/PPO0，Swing0/8、DrawBack/R0各8/8。Frame重算误差<5e-7、history一致、actor前向可重放；Swing动态观测有响应但不能证明观测充分。两轮mean全程超出−1、解析裁剪概率100%/98.63%；低位pitch/roll/vertical gate激活0。下一优先准备mean越界动作覆盖与低位reward辨别力的分别单变量，不默认再减std，未授权新PPO。[诊断报告](RECOVERY_INPUT_ACTION_REWARD_PROBE_20261008.md)。

最新支撑PPO0已COMPLETED（结算171.884秒/PPO0）：原DrawBack/R0各8/8，.194米候选沉降回原Swing后才初始化有效，.228/.259/.289米初始化拒绝且趋原Swing。没有据此自动开启PPO；这不是要求先找到成功Swing轨迹或动态中间态才能学习。原Swing已合法且用户GUI确认。动作范围未见硬不可达证据，但观测适用性、奖励信号、探索/裁剪及优化迁移仍均未排除。下一优先准备Swing/DrawBack/R0同源输入—动作—奖励联合诊断；动态restore仅是可选手段，不能称已找到Swing桥接路径。保留B25，不延长静态沉降或加托举。见[完整复盘](RECOVERY_SWING_SUPPORT_PROBE_20261008.md)。下方“已提交”是此前阶段记录。

固定分组块`2026_10_8-16_08__recovery_level3_swing_fixed_slots_from_b25`已完成（smoke10/formal75，旧组连续两次退化保护停止）。Swing有效transition占比23.58%，峰高仍约.232米、0/8入口，故增加覆盖不足以解决当前学习。来源B25保留；用户批准先做动作范围/路径离线检查及六项有界PPO0：原DrawBack/R0＋Swing当前闭链分支四个合法中间支撑候选（约.194/.228/.259/.289米）。`2026_10_8-16_53__recovery_b25_swing_support_probe_ppo0`已提交，PPO0总墙钟≤1800秒；初始化实际构型保留及能力以终态raw为准，不自动开新训练。

Level3首块已COMPLETED但Swing全部未入口，峰高约.231米；new25/new50保住DrawBack/R0，new100因失触退化。Swing有效transition仅1.57%，不是reset声明40%。用户批准从B25实施固定训练family首块，26/25/13槽位、奖励/控制/终止不变；配方及离线对齐见[本轮交付](RECOVERY_SWING_FIXED_SLOTS_20261008.md)。下方旧“已提交、尚无formal证明”是首块历史摘要，当前提交回执以STATUS为准。

用户已GUI确认Swing候选及DrawBack起身，并批准Level3首块。`2026_10_8-14_51__recovery_level3_swing_from_b25`已提交，握手SOURCE_EVAL，尚无formal首更新证明。三组40/40/20，B25实际std不重复减半，smoke10/formal≤100，25/50/100完整联合筛选。独立预算/工程验证/回执见[首块交付](RECOVERY_LEVEL3_SWING_PREPARATION_20261008.md)；以下“需GUI确认/需新授权”是此前阶段记录。

最新Swing定位：五项PPO0完成，原DrawBack/R0保持通过；5%插值沉降回原构型，10%初始化拒绝，不作为新桥接技能。历史Swing候选初始化8/8有效且保留关节构型，但当前B25未起身、tilt终止。下一可从B25准备有界Level3学习并保留原组；需GUI确认目标初态、独立新训练授权，不重复轮std减半。[实测复盘](RECOVERY_B25_SWING_BRIDGE_20261008.md)。

最新小扰动验证完成：B25在原DrawBack/R0＋6个±.01rad合法候选八项全部8/8通过，PPO0。按逆向课程准备更靠近Swing的5%/10%静态桥接及历史Swing候选冻结验证；尚未授权新运行。[结果与下一spec](RECOVERY_B25_SMALL_PERTURBATION_20261008.md)。

最新：P2 B25完整候选已完成三个seed双初态冻结复验，六项8/8全通过。按第9节准备DrawBack附近±.01rad小扰动，runtime初始化尚需新授权PPO0验证；然后推进Swing可达支撑组。见[复验及小扰动准备](RECOVERY_B25_REVALIDATION_20261008.md)。R0三seed是相同初态重复性，未称任意倒地泛化。

后续用户已明确批准P2 A/B预算并提交，两臂首次握手SOURCE_EVAL，formal首更新未验证。运行事实和授权见[提交记录](RECOVERY_P2_WHEEL_STD_AB_PREPARATION_20261008.md)，下面“仅准备/UNAUTHORIZED”保留为准备时阶段记录，不覆盖新独立账本。

23_29 P1链已COMPLETED，smoke20+formal100；新平台高度/完整10秒训练覆盖已实际接通，尚无完整accepted。
用户GUI认为本次new50起跳和收稳优于new100；身份为23_29/formal/model_update_50.pt，SHA8507dd7e157f0d1f27908056a51ddef6afcee08047dbf2c26d7758f6cd598d8e，不能混称18_06 S50。
已完成50/100入口前起跳/左右落地/入口后弹跳的离线对齐；不对称先于落地出现，100更齐但接触更差，仍非唯一因果结论。
按第7节准备同源new50轮std初值A1/B.5，两臂其余配方相同；实际轮std9.482/7.568→4.741/3.784rad/s，保留全部Adam、腿std、mean/critic、原pose/USD/gate。
[离线事件与P2准备](RECOVERY_P2_WHEEL_STD_AB_PREPARATION_20261008.md)。本轮仅准备，A/B均UNAUTHORIZED，未仿真/PPO/提交；预算建议仍需明确运行授权。
下方2026-10-07第0–13节保留最终讨论原文：其中“最新20_55”“P1尚未实现/验证”属于该日规划背景，不覆盖23_29原始终态与本节执行进展。目标、单变量及授权边界继续适用。

最新20_55终态已COMPLETED，总110更新，全部候选完整认证0/8。
新100已实现入口后10秒高度/接触保持，但roll和轮振荡/饱和失败；新50几何改善但接触退化。
先按[终态复盘](RECOVERY_LEVEL2_ALIGNMENT_TERMINAL_REVIEW_20261007.md)诊断轮振荡/训练覆盖，
不默认采用自动best50，不自动续训或开启新课程。

## 早期目标与效力记录（2026-10-07阶段，当前以第0节为准）

更新：2026-10-07。本节至第13节是当前规划；后面的折叠区保留历史原文，
其中旧的“当前来源”“下一步”“授权”和高度要求不作为新实验指令。

**用户最新明确要求：允许站在0.42m；最终高度不要低于0.30m；能站稳、姿态平稳水平即可。**
因此不再要求回到0.36m，也不把0.42m变成另一个必须精确跟踪的目标。
当前任务仍是从实测 DrawBack 低位自主起身并连续保持10秒；不要求原地零速、
厘米级位置保持或严格腿部对称，不新增运动命令。不摔和水平是能力目标，
轮心错位、速度、位移、腿长差是重要诊断，但不能只因某项看起来漂亮便接受模型。

本轮用户授权的是**制定计划并编辑本文**，以及明确新的高度目标；本次未改代码、
spec、资产或模型，未启动仿真/PPO。下面的新实验额度是建议上限，不是新运行授权。
20_55链已按其冻结授权结束，不能追溯替换成新目标。后续执行者若已获得
覆盖某阶段的明确授权，应完成该阶段，不为每个常规步骤重复确认；没有覆盖时，
先完成代码、CPU测试、离线评分、新spec和plan，最后集中核实缺少的运行范围。
用户暂不能对话时，不臆造授权、不花Motion预算；完成一切已授权的准备和分析后交付。

### 阅读与行动顺序

1. [AGENTS](../AGENTS.md) → [新会话入口](../README.md) → 根README/STATUS/ARCHITECTURE/TOOL_INDEX。
2. 本文 → [训练经验复用](../TRAINING_EXPERIENCE_REUSE.md) → 所选run的spec、manifest、冻结实现和原始评估。
3. 已授权旧链的终态复盘 → P0新目标离线复评 → P1统一目标与保持训练 → 依据结果选择P2/P3。
4. 不复刻旧代码树，不启动第二套trainer/monitor；新提交只走共享supervisor。
5. 不靠本文的历史运行描述推断进程仍活跃。本次计划编辑没有检查或等待活动训练进度。

## 1. 模型、姿态与资产身份

| 对象 | 当前角色与证据 |
| --- | --- |
| 起身来源S50 | `runs/2026_10_7-18_06__recovery_level2_settle_cost_probe/formal/model_update_50.pt`；SHA256 `de06b39d2a88c44250309b4ae0509188b532cc5c51a681d456a545c307243694`；有自主抬升动作，旧完整起身保持0/8 |
| 早期站立source50 | `runs/standing_scissor_20261006/formal/model_update_50.pt`；SHA256 `1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`；另一谱系，不能和S50混称，不能直接当当前资产下已认证teacher |
| DrawBack姿态 | `runs/recovery_pose_capture_20261002_145814/pose_0001_73d09dbe.json`；SHA256 `1ebaf39d3c07283c01cb519f3ab8e5b3acd7c5d5ded4a08faa88f29ac41b699c`；使用保存的实际joint_pos，不能用UI requested angles代替 |
| 当前Recovery USD | `assets/diagnostic/rmuc_robot_closed_loop_knee_stop_0233_v2.usd`；SHA256 `32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7` |
| 弱轮心对齐链 | `runs/2026_10_7-20_55__recovery_level2_alignment_from50`；已COMPLETED，smoke10+formal100；所有候选完整认证0/8。new100高度/接触改善但roll和饱和失败，new50几何改善但接触退化；不自动选择或续训 |
| 不作默认续训源 | 18_06的update100，已有50Hz轮目标/力矩交替及限矩证据；除非是明确的故障诊断，不从它继续 |

Source/current asset、pose、actor、critic、Adam、RNG和协议各自绑定身份。
新目标需要严格加载S50，但旧critic/Adam只是初始化，不是新目标价值估计已正确的证明。
新评估与训练使用同一个原生闭链环境及物理接口，Recovery腿动作尺度仍为**1.6rad**，
不能误用Motion的0.5rad；轮100rad/s，40/5.5Nm，physics/PD/policy为1/5/10ms。
初态约0.168474m；已有初始化和几何有效性不能替代新run的实际初始化readback。

## 2. 已查明的事实：后续决策必须据此区分问题

### 2.1 首次抬升很快，旧7.8秒是回落时首次进入窄高度带

从20_55已完成的[来源评估](../runs/2026_10_7-20_55__recovery_level2_alignment_from50/source_eval/evaluation_source.json)
重算，八环境首次超过0.34m均在恢复计时约0.18秒，峰高均在约0.32秒。
下面为env0代表轨迹，不把同seed八环境冒称八次独立训练：

| 恢复计时 | 高度m | vx m/s | 实测事件 |
| --- | --- | --- | --- |
| 0.18s | 0.3494 | -0.729 | vz约+1.285m/s，只有一轮接触读数>2N |
| 0.32s | 0.4407 | -0.834 | 两轮接触读数均低于阈值，已发生冲高 |
| 0.50s | 0.4033 | -1.070 | 双轮接触恢复，在高位滑行 |
| 7.76s | 0.3799 | -1.866 | 从上方回落，首次满足旧入口；轮心纵向错位约0.332m |
| 9.29s | 0.3394 | -2.659 | 旧高度下限失守，错位约0.409m，roll约0.152rad |
| 10.10s | 0.2772 | -3.701 | 失去双轮接触，错位约0.504m |

完整轨迹还出现后续重新抬升，不能描述成不可逆趴地。瓶颈是**冲高后的动态收稳和保持**，
不是尚未探索到抬升动作。速度持续增加与失稳相关，但本任务尚未增加静止/速度验收。
两轮位置不是接触斑块；接触是传感器合力>2N，不能据此认证法向负载或支撑多边形。

可复查[离线轨迹图](../artifacts/2026_10_7-21_19_17__recovery_source50_offline_review/trajectory.png)
和[输入SHA及八环境事件](../artifacts/2026_10_7-21_19_17__recovery_source50_offline_review/evidence.json)。
图中阴影为**旧协议**首次入口保持窗，不是本文新目标的评分窗。

### 2.2 高度奖励与最新用户目标明确冲突

旧配方的两个高度项为：

```text
standing_height = +3 * exp(-((h - 0.36) / 0.04)^2)
height_overshoot = -1 * (max(h - 0.36, 0) / 0.04)^2
```

仅这两项，在h=0.36时合计+3/秒，在h=0.42时约-1.934/秒，差约4.934/秒。
连续项另乘policy dt=0.01一次。因此只放宽报告，而保留这套奖励，仍会鼓励降高。
这是已确认的**新目标与旧配方冲突**，不是已经证明所有历史降高均由这两项造成。
旧lift在目标高度以上已截断，并非越高奖励越大；不能把它解释成无限鼓励冲高。

### 2.3 训练只要求2秒短稳定，验收却要求10秒

20_55冻结实现沿用`autonomous_hold`：`verify_s=2`，成功+10并terminated/reset；
恢复计时11.5秒仍未成功则task failure/terminated。评估设置continuous_evaluation，
延长观察到23秒、屏蔽成功reset，首次入口后另算10秒。
依据是冻结的`recovery/domain.py::RecoveryFSM.step`、`runtime.py::_get_dones`及`recipe.py`。
spec中的“10s/no success reset or bonus”注释与实际执行不符，应在新声明中消除。

18_06的100更新原始metrics共有578个完成episode：R0=222、DrawBack=356，
成功0、task failure578、normal timeout0、runtime fault0。
**2秒成功重置没有实际截短这次已记录的成功轨迹，因为根本没有成功事件。**
当前来源在旧高度协议内最长连续stable约1.46–1.48秒，初次失稳已在训练可见区间。
不过一旦将来稳定2秒就提前结束，将无法学习同次成功episode后续2–10秒；
训练时域与完整目标的缺口必须处理，不能宣称只延长时长必定解决动力学问题。

### 2.4 R0失败不能等同于不会平衡

20_55来源R0完整23秒，姿态/接触/闭链/采样饱和检查通过；高度约0.423m且全程高于0.401m，
旧失败项仅height_mean、height_fraction、standing_entry。
当前新高度目标可能改变结论，但必须从完整trace重新找入口和重算窗口，不能直接改成8/8。
40%R0是reset抽样权重，不是40%有效transition，也不自动代表已认证的旧技能。

### 2.5 随机探索与确定性行为差距值得单独检验

S50标准差按实际动作尺度换算：四腿约0.097/0.196/0.098/0.100rad，
两轮约9.53/7.64rad/s（输出裁剪前）。Kv=1时，同一瞬间实际轮速不变，
如此大的目标扰动对应的请求力矩变化容易超过5.5Nm物理限矩。
18_06四个25-update窗口中，任意通道policy采样触限比例约0.765/0.753/0.756/0.778。
确定性S50 env0在恢复0.5–9.29秒没有采样触限，几何/高度仍逐步退化。
所以不能仅靠“限矩饱和”解释确定性失稳，也不能用GUI平滑推断训练探索足够温和。
上述训练聚合混合初态和阶段，尚无充分的逐通道、逐阶段因果证据。

## 3. 新目标必须一次明确：版本化协议与训练目标

下面是待实现的新版本设计，**不是现行schema或已发布spec**。
建议语义名`autonomous_rise_min_height_v2`；执行者可以按当前架构选等价名称，
但必须有新协议身份和SHA，历史`autonomous_rise_v1`保持原语义。

### 3.1 验收要求

| 项目 | 下一版本默认规则 |
| --- | --- |
| 起身高度 | root height至少0.30m；0.36、0.40、0.42m均可；不设人为精确目标上限，实际关节/几何/穿透保护仍生效 |
| 首次入口 | 初始化有效；高度>=0.30m；真实机体正净空；双轮接触>2N；abs(pitch/roll)<=0.10rad；tilt<=0.18rad；以上条件连续满足0.20秒后首次确认，不把冲高时一帧穿越当站稳 |
| 起身期限 | 从初始化完成计时，首次入口确认不晚于11.5秒；不是从AppLauncher或trace起点计时 |
| 保持 | 第一次入口开始，同一episode连续10秒；不重选后面好看的窗口、不拼接episode |
| 高度保持 | 保持窗中每个有效样本高度>=0.30m；不保留旧0.34–0.38上限或旧height_mean范围 |
| 水平 | 沿用mean abs pitch/roll各<=0.10rad、peak abs各<=0.15rad、peak tilt<=0.18rad |
| 接触 | 本版暂沿用旧起身证书的连续双轮接触要求；同时报告contact fraction。旧95%汇总与连续100%证书不能混称；若以后认为过严，必须另开协议，不在本轮临时放宽 |
| 执行/物理 | 闭链<=5mm、采样饱和<=5%，保留非有限、关节、穿透和已确认接触安全保护；限矩统计注明100Hz范围 |
| 不作为新硬门槛 | 平面零速、厘米漂移、轮心4cm对齐、原始关节严格镜像、固定腿长差；继续记录 |
| 通过单位 | 逐环境结果；所有声明初态进入分母，初始化拒绝、提前终止、缺数据不能被删除 |

必须审查旧`chassis_clearance_min_m=0.25`是否只是旧高度偏好：它可能造成有效高度下限
高于用户的0.30m。新成功判据要求真实机体正净空并保留runtime穿透/禁止接触保护，
不直接继承0.25m作为姿态偏好；用同资产几何readback解释根高度与净空的关系。
不得为改变高度目标而放宽物理限位、接触合法性或穿透阈值。

0.20秒是本计划为新版本提出的入口确认时长，不是历史协议已经采用的值。
它只确认事件，不接管动作；确认前不足0.20秒的短穿越可以清零候选计数，
确认后锁存第一个入口，不能因为后续失败再次选择窗口。100Hz下确认需20个连续有效样本，
完整10秒保持从确认后开始，另取1000个policy区间，在线/离线使用相同的索引边界。
这项与高度目标迁移一并明确记录，不能宣称只改了旧高度上限。

新高度没有上限，**新入口可能明显早于旧7.8秒**。必须重新扫描整条trajectory；
不能在旧[8.14,18.14]索引窗口上仅替换height阈值，也不能将旧9.29秒跌破0.34
当成跌破0.30。R0按声明的近站立保持协议单独评分，窗口/初始化清晰记录，
不能用低位“没进入旧高度带”的诊断代替它的实际保持行为。

### 3.2 高度相关reward的默认迁移方案

为了快速贴近用户目标，推荐采用**高度足够后的平台满足项**，不再追精确0.36。
下面给出可执行的初始配方提案，必须离线画曲线、CPU验证、新spec冻结后才可训练：

```text
lift_reference = 0.168m  # 显式任务参考，不再由高位R0初高产生负向lift定义
lift_raw = clamp((h - lift_reference) / (0.30 - lift_reference), 0, 1)
height_sufficient_raw = clamp((h - 0.30) / (0.34 - 0.30), 0, 1)
continuous_height_reward = 2 * lift_raw + 3 * height_sufficient_raw
```

0.34m仅是软奖励达到平台的裕量，**不是新的0.34m验收下限**。
在0.34m以上，此两项不再偏好降到0.36或升到0.42；低位仍有有限密集抬升信号。
停用“超过0.36就惩罚”的任务高度overshoot项；若有独立物理上界，仍由冻结安全保护执行，
不能凭空创造新的0.42硬上限。保留现有水平、接触、effort、vertical motion等项的有效系数，
不同时增加yaw/速度/轮平滑或对称性成本。低于0.30时，保持奖不能取代抬升奖。

actor observation中历史height command暂保留来源的0.36常量以免同时改变输入分布，
但新版本必须显式说明它是兼容输入；reward和gate从新任务高度下界/平台配置读取，
不得再从该兼容常量隐式推回Gaussian、overshoot或成功高度。
旧语义仍由旧版本分支执行，不以删字段方式使旧checkpoint解释失真。

高度目标、奖励形状、终止和完整成功事件同步迁移属于**任务目标迁移**，不是
“只改一个系数”的因果消融。它优先解决实现目标错误，之后才比较单变量优化。
对齐成本由P0候选决策冻结一次：确有完整保持收益才保留；否则默认回到S50无对齐项，
不是因为轮心错位更小就默认保留。不得一边更换来源一边声称对齐单独有效。

## 4. P0：当前旧链结束后的复盘与新目标离线评分

20_55链已按冻结授权结束；不重启、不复用账本、不从其latest或自动best继续。
P0从其terminal、ledger、25/50/100 checkpoints和原始评估开始，所有新结论写独立输出。

完成以下交付，不必等待新的物理预算：

1. 建立S50、20_55各已评估候选、latest、best_new、best_overall、accepted、fallback清单。
2. 旧协议结果保持原样；按第3节新协议，在新输出中重新找首次入口和完整10秒窗口。
3. DrawBack与R0分别列出：初始化有效数、首次高度穿越、首次入口、保持前缀、完整通过数、
   最小高度、pitch/roll均值/峰值、失触时刻、采样限矩、闭链、轮心错位及其变化。
4. 全窗口缺失则标证据不足，不能从末1秒、聚合均值或GUI补出10秒通过。
5. 只有新协议身份、模型/资产、同一episode完整窗口均可核验时才给离线新协议分数；
   明确这是旧轨迹重评分，不是新训练收益。
6. 对新的评分器做独立CPU交叉核验，尤其恰好1000个policy样本、初始化时钟、首入口及
   提前终止；不要只调用两遍同一个helper就称独立验证。

### P0候选决策

| 结果 | 决策 |
| --- | --- |
| 某候选DrawBack/R0完整新协议都通过 | 优先进入同模型独立PPO0复验，可能无需继续PPO；保留来源 |
| 对齐候选显著延长保持且R0无回归，无新振荡 | 可作为下一轮来源候选；保存与S50的并列证据，冻结其已用reward |
| 仅轮心更齐，保持不改善或新出现振荡/失去抬升 | 不采用该候选，回退S50；下一步不继续提高对齐权重 |
| 全部未通过 | 不停止在笼统NO-GO；使用最好的有限行为候选，进入P1目标迁移与有界学习 |
| 接线/初始化/物理契约异常 | 先修并验证这些异常，不能将其作为策略能力结果 |

## 5. P1：将完整起身—保持真正放入训练

### 5.1 任务状态和时钟

下列FSM只描述环境任务事件和评分，**不增加控制器、不替换actor动作**：

```text
初始化有效
  → 起身搜索（恢复计时≤11.5s）
  → 新入口条件连续0.20s首次确认：锁存entry_time和episode_id
  → 同一actor继续控制10s
  → 完整成功或完整保持失败
```

- 首入口以前，11.5秒还未完成入口确认属于有限任务失败，按新任务声明终止。
- 首入口以后，终点是`entry_time+10s`，不能被旧全局11.5秒deadline截掉。
- 2秒/5秒只作诊断里程碑，不发完整成功证书、不触发reset。
- 入口后若高度、连续接触或姿态峰值硬条件越界，完整首窗证书记失败；在物理安全范围内仍可
  采到本次约定终点，学习失稳后的控制。不能重新锁存第二次入口把前次失败擦掉。
- 保持期间不能把入口的abs角度<=0.10逐帧套成失败门槛：0.10是保持全窗均值要求，
  短暂0.11rad且peak<=0.15、全窗均值合格仍可通过。均值角度与饱和比例在窗末汇总，
  不以中途前缀均值暂时超限永久否决整窗；真正峰值越界则锁存失败。
- runtime fault、真实安全终止优先；不为了收满10秒继续非法闭链/非有限状态。
- 最晚11.5秒入口应允许到恢复21.5秒，加初始化上限和离散余量后，23秒观察上限足够；
  各时钟必须由共享任务协议推导，不在schema、runtime、evaluator复制常数。
- 128步rollout只是1.28秒采样块，不是episode。跨rollout的entry/hold状态不得丢失。
- 近站立R0单独声明10秒保持任务；初始化完成、episode起点和评分起点必须可追踪。
  若采用统一入口流程，明确其最大时长和首入口规则，不能在日志中仍冒充固定10秒R0。

**禁止两个伪修复：**只改`curriculum.episode_length_s=23`而保留旧FSM；
只改`verify_s=10`而仍在恢复11.5秒无条件终止。

### 5.2 奖励事件和bootstrap

新任务默认将原+10成功奖励移到**完整10秒证书通过**时一次发放，2秒只记录；
失败事件仍为一次-1。明确这是奖励时序改变，不宣称纯时长A/B。
保持过程中持续发放第3节密集高度满足项和既有水平/接触等反馈，不能只靠最后+10。
每个episode事件最多一次，reset不能漏发、重发或把成功与失败同时计算。

| 事件 | 推荐新任务语义 |
| --- | --- |
| 初始化拒绝、真实安全失败、无入口且deadline耗尽 | task terminal；原因分开，无虚假成功，无terminal后的bootstrap |
| 首入口后轻微证书条件失败 | 锁存certificate_failed；若未触发安全终止，继续采样至约定终点 |
| 完整保持任务结束 | 本计划按有限任务终点处理，成功/失败一次记账，不使用reset后value补回报 |
| 128步rollout切边 | 非episode终点，正常使用对应末状态value计算GAE |
| 外部人为截断继续任务 | 只有显式定义为continuing truncation时才对pre-reset末状态bootstrap；运行中断的半个batch不能伪装完整更新 |

新任务在完整1000个保持样本后正常成功终止，必须标明`task_success`和实际完成时长。
它可以`terminated=true`且证书通过；不能让旧评分器的通用`not terminated`将其当成提前死亡。
只有提前结束、故障或证据不足才拒绝完整窗口；不能反过来忽略所有done。
这一兼容处理限于新版本，旧运行仍按自己的终止/评分协议解释。

不要把所有名为timeout的字段一律改成bootstrap，也不要把普通采样截断一律当跌倒。
当前gamma=.99、100Hz下，1/2/10秒后的折扣约.366/.134/.0000432；
这不等于网络只能记住一秒，但说明延迟终末奖不能独自承担长期学习。
P1保留gamma/lambda，不同时调折扣、LR、网络或Critic输入。

### 5.3 当前架构下要检查的实现落点

优先复用现行模块，路径变更时以实际import链为准：

- `recovery/task_protocol.py`：唯一任务类型、deadline、hold与batch时长解释。
- `recovery/validation.py`：新版本合法字段；旧固定`height_m=[.34,.38]`约束不能误套新版本。
- `recovery/rising.py`、`standing.py`：纯域入口、窗口和逐环境判据，在线/离线共用。
- `recovery/domain.py`、`runtime.py`：事件FSM、奖励、reset、pre-reset证据、episode状态。
- `recovery/recipe.py`：实际评估调用、R0结果、时钟、first episode及异常恢复。
- `command_v6/domain/episode_summary.py`及`episode_result.py`：生产/消费统一。
- `command_v6/domain/evidence.py`：协议SHA和gate缺证/冲突分类。
- `command_v6/domain/selected_diagnostics.py`：复用现有P2观察器，不另建旁路PPO。
- `command_v6/supervisor.py`、`wiring.py`、preflight：冻结实现的真实入口与证书。

评分、保存profile、评估频率、预算、授权、session/GPU各自解析；
不把整块evaluation字典作为standing评分协议传入，也不允许所有未知字段以绕过校验。
legacy schema仅在明确版本分支解释，新的requested/effective/runtime必须一致。
新reward连续项仍乘dt一次；高频控制与动作尺度保持原契约。

### 5.4 必须通过的CPU回归

1. 高度0.30/0.36/0.42均不因旧上限拒绝，0.2999正确失败；无隐藏0.25m净空偏好。
2. 新高度满足项在0.36和0.42一致，低位有限，超过平台不额外奖励冲高。
3. 新入口必须从完整trace寻找；短于0.20秒的冲高穿越不锁存入口；不复用旧7.8秒或旧索引窗。
4. 入口在7.8秒时，不会9.8秒短成功reset，也不会11.5秒被截断。
5. 入口在11.5秒边界时，允许完成后续10秒；无入口则按deadline失败。
6. 中间跌出条件不能重新选择窗口；真正跌倒/闭链/非有限优先终止。
7. exactly1000有效policy样本、首尾边界、初始化时间与跨rollout状态正确。
8. 成功/失败事件最多一次，GAE/bootstrap使用正确末状态，不能读取reset后observation；
   完整1000保持样本后的task_success终止可通过，提前999样本的终止不能冒充完整通过。
9. R0和DrawBack分别记录，不用总episode数证明任一family路径覆盖。
10. 正常/异常评估退出都恢复actor模式、RNG和runtime配置。
11. 现有Motion、旧Recovery版本保持原行为；真实冻结worker也通过CPU配置/计划检查。
12. 保持中短暂0.11rad但全窗mean<=0.10、peak<=0.15可通过对应角度项，真正peak>0.15失败；
    入口与保持判据各有独立fixture，正净空同时进入online/offline规则。
13. plan-only零写入；配置冲突在AppLauncher前拒绝；新目标声明不重写历史SHA。

## 6. P1有界运行建议、检查点与放行

以下是**申请或核对授权时的具体建议**，本文件不创建额度，不替代已有账本。

| 阶段 | 建议额度/检查 |
| --- | --- |
| 新协议PPO0来源复核 | DrawBack与R0，同一S50/资产，8 scored env/组；总墙钟<=900秒，含初始化和清理；若成本估计超限，启动前修正预算而不是运行中超支 |
| wiring smoke | 最多20更新；64×128下163840样本、每env25.6秒采样；墙钟<=900秒；最少需求由事件时长计划推导 |
| 第一块formal | 最多100更新、819200样本；墙钟<=7200秒；checkpoint25/50/75/100，完整评估25/50/100 |
| 第一块总PPO上限 | smoke20+formal100=120更新、983040样本，smoke与formal独立计费 |
| 同配方延长 | 有进步且保护通过时，另在适用授权内追加最多200更新一块；不是直接10000更新 |
| 未通过前的耐久评估 | 不跑100秒；23秒完整起身窗足以指导首轮 |

formal从明确冻结来源初始化；默认不继承smoke末尾权重，保持与现行流程一致。
20更新smoke提供足够的时间跨度，不意味着所有环境必须已学会完整成功。
必须证明实际参数更新、初始化/终止/历史接线、样本预算和物理有限性；
普通能力失败不阻断训练。未进入保持的行为样本如实记0覆盖，不假造“保持事件已验证”。

每次完整评估默认只对当前一个checkpoint评DrawBack/R0；保存逐环境摘要与失败原因。
来源、首个完整通过、最终候选和明确故障窗口保存完整轨迹，其他点使用声明的summary/failure_tail。
不同时对大量候选跑100秒，不循环重复来源基线。只有模型/物理/协议/执行身份兼容且
当前证书允许，才复用旧PPO0证据；“都叫source50”不构成复用依据。
根据本机实测rollout、评估、保存和清理耗时安排预算，不能把Motion/Gym速度照搬。

### 进度指标与暂停规则

必须同时报告full certificate和**诊断保持前缀**：首次新入口后，连续满足高度、接触、
瞬时姿态/安全条件的前缀秒数；均值角度、饱和比例等完整窗口条件仍单独评分。
2秒/5秒前缀是学习进度，不能替代10秒完整验收。

- 来源和候选都没完整通过时：先看有效入口率、最差环境保持前缀、完整通过环境数，
  再看姿态/接触；不会仅因“0/8 accepted”就禁止继续这一个有限学习块。
- 已认证R0若在两次固定完整检查点失败，停止本分支并保留最后通过候选。
  从未认证的R0应记为尚未掌握，不以它两次失败冒称遗忘而机械停训。
- 已有抬升/入口在两次检查中明显丢失，或出现已确认的新持续轮振荡，停止该分支；
  “明显”在spec中用逐环境入口数和固定窗口振荡指标定义，不运行后临时改标准。
- 100更新后若所有候选仍无完整成功，且保持前缀、接触、姿态均无可复核改善，
  不自动增加同配方预算，进入P2诊断分支。
- 有改善但未完整通过，可在已授权范围继续一个200更新块；禁止用总reward改善替代行为进步。
- 非有限、闭链、资产/控制身份异常立即按工程故障停止；普通任务失败只终止相应episode。
- 失败→通过→失败的连续失败计数必须1→0→1；同一任务不维护两套停止计数器。

## 7. P2：仅在证据支持时进行探索尺度对照

触发条件：P1目标已接通且CPU/物理证据正确，确定性来源仍有可用动作，
随机训练按阶段统计却明显更差或持续大量触限。先确认触限发生在哪个通道/阶段，
不能只凭全episode的75%直接改所有std。

建议同源两臂，唯一变量为**初始轮探索标准差**：

- A：P1配方和所选来源自身std。
- B：只将两个轮std初值乘0.5；四腿std、actor mean、critic、LR、reward、初态与物理保持。
- 如果来源仍是S50，两个轮的裁剪前物理std由约9.53/7.64降至4.77/3.82rad/s；
  若来源变了，重新读实值，不复用这组数字。
- 两臂各建议smoke20+formal100，25/50/100同协议评估；总240更新、1966080样本，独立授权与账本。
- 这是探索初始化干预，不是等价参数迁移。显式确认当前scalar/log std参数化、output factor、
  正数约束及clip，保存初始化前后分布。不要通过改wheel action scale达到相同效果。
- 不冻结std、不另加下限/上限schedule、不清所有Adam矩、不改entropy/Kv；
  如要处理std参数的Adam历史，必须明确成为另一个变量，不能暗中进行。
- 分支同seed和初始化流便于比较；不同std会自然改变轨迹，不要求后续状态相同。
  若再验证独立训练seed，不得恢复同一来源RNG后声称独立随机流。

选择标准：完整保持与R0保留优先，分阶段/逐轮饱和率是机制证据；
若只是饱和率下降而起身能力丢失，B失败，不继续把std越调越小。
若两臂相近，无证据支持该改法，回到更好行为候选，检查P3过渡状态覆盖。

## 8. P3及后备分支：只解决已定位的缺口

### 8.1 静态R0会保持，实际起身落点仍收不住：过渡状态覆盖

从真实轨迹选择**入口附近且尚未失稳**的状态分层，先学这些状态后的保持，
再回到原DrawBack端到端复验。不能只按root height选点：需同时保存几何、速度、姿态和接触。

动态reset所需：root pose/linear-angular velocity、全主/被动joint pos/vel、闭链分支、
执行中的PD目标、previous action、五帧history及一致的时钟/episode状态。
当前100Hz姿态/控制trace不一定包含所有被动关节与仿真接触内部状态，
不能凭部分数据宣称恢复了原PhysX状态。若建立近似reset，单独认证其闭链和短时readback，
明确与原轨迹不完全等价；不把静态passive settle当动态状态复现。

不能可靠恢复时，优先利用当前policy的自然rollout延长/统计过渡覆盖；
若未来另授权使用source前缀生成状态，它只是显式训练初始化，不是部署控制器，
source前缀样本不得伪装当前policy on-policy PPO数据，最终仍从原DrawBack完整验收。

初始分配仅作可申请的方案：R0 40%、原DrawBack 40%、真实过渡组20%；
比例变化单列实验，保留原DrawBack评估，不同时改变reward/std/物理。
按实际transition而非reset次数报告覆盖，桥接组成功不能代替端到端起身通过。

### 8.2 再次出现50Hz轮目标交替

20_55的新25/50/100在确定性评估中已经出现交替；不能把它仅解释成采样噪声，
也不能声称降低探索std就能消除已经学入actor的确定性振荡。
先复核policy raw mean、sampled/clip action、previous action/history、PD时相和applied effort；
从同一原始窗口确认是actor输出、随机探索还是控制响应的交替，避免时相错读。
若随机探索已控制而确定性振荡仍存在，再单变量研究轮action_delta的物理尺度：
先把每步rad/s变化、现有cost和其他项量级画出来，按固定来源和实测分布冻结一个系数。
只改变轮通道成本，不同时改Kv、限矩、low-pass或policy频率；不得把Motion的尺度因子
直接移植到Recovery。低cost只是候选线索，不证明把cost加大一定有收益。

### 8.3 保持样本充足、探索合理，仍无进步

利用已有P2/selected_diagnostics查看family×phase的value/return、原始/归一化advantage、
真实优化前后ratio/KL、std和梯度；区分rollout探针、minibatch统计和真实optimizer step。
不从梯度norm或reward大小推断某个奖励因果占主导。必要时用一个身份完整的新batch
独立复算GAE/timeout，禁止伪称复现没有storage的历史更新。
gamma、critic warmup、per-command/group normalization属于后备单变量，不一起开启。
不因网络建议就加入PCGrad、privileged critic、对称网络或另一控制层。

### 8.4 三份参考材料中可借鉴的部分：只作诊断与实验约束

[参考文献](../参考文献.md)和[参考文献2](../参考文献2.md)没有作者、DOI或论文链接，
是AI生成的思路材料，不是本项目根因证据。它们可作为待证伪的诊断清单。
[训练经验复用指南](../TRAINING_EXPERIENCE_REUSE.md)含项目与同事仓库的可追溯历史证据，
但其旧“当前任务/预算/高度”段落不覆盖本计划的新高度目标。采用下列做法：

| 可借鉴点 | 触发与实际测量 | 决策边界 |
| --- | --- | --- |
| 门控奖励先验证真实覆盖 | 每个完整on-policy rollout按`family × phase`记录transition数、每项reward gate激活比例、raw/weighted/dt贡献；phase互斥划分为入口前、入口后0–2、2–5、5–10秒；零必须区分条件未发生、正确为零、字段失接 | 高度gate在冲高时就可能激活，不能称只在稳态工作；门控不保证消除reward hacking。覆盖为零先查未到达、提前终止、任务时钟和记录口径，再决定修复，不先加新奖励 |
| 逆向课程只从可达状态扩展 | 每个新pose先检查初态、闭链、接触和短时readback；起点难度由完整几何/速度/接触定义，不按root height插值 | R0静态通过不能证明动态起身落点可控；不采用无限力矩解冻、硬控制权切换或用静态passive settle冒充动态状态恢复 |
| 轮振荡按同一时相审计 | 用实际USD轴符号统一前进方向；同一policy时刻同时保存actor raw mean、sampled/clip action、轮目标、实际轮速、requested/clipped/applied torque及接触 | 100Hz逐策略步交替可以报告；latest-held PD记录不是完整5ms/1ms认证。合法滚动、轮速或轮心前进不是滑移，不能直接施加静止足滑移惩罚 |
| 对照必须同时回答两类收益 | 每个A/B分别与共同source同协议比较，并互相比较；候选完整DrawBack/R0/安全结果并列 | 一个arm比另一个好但两者都退化，不构成继续训练收益。评估seed重复性不等于独立training seed，不能拼接不同checkpoint通过项 |
| 多任务冲突先诊断再动算法 | 仅在P1已有真实2–10秒保持覆盖、且R0/DrawBack出现重复此消彼长时，基于同一on-policy batch按family和互斥phase记录样本数、raw/normalized advantage、组均值actor梯度与实际加权贡献；PPO/entropy/辅助项分开 | 负cosine、global advantage normalization或镜像残差都不是根因结论；不直接启用PCGrad。均值梯度不含Adam历史、多步clipping和闭环状态变化，不能保证物理能力 |

左右不对称若仍是稳定现象，先做**只读镜像残差**：定义USD物理镜像的observation/action置换及符号，
确认`T(T(x))=x`，同时变换五帧history、previous action与command，再计算
`||pi(T_obs(o))-T_action(pi(o))||`。资产、初态或接触不满足镜像条件，或残差很小却仍失稳时，
不支持“网络缺少对称性”是充分解释。非对称状态可以合理需要非对称动作，不以raw左右动作必须相等构造惩罚。

若几何成本改善错位却伴随roll、平移或饱和恶化，可复用已有轨迹检验“共同分量/差分分量代偿”假说：
在USD轴符号统一后，比较左右轮目标、实速和实际力矩的半和、半差，按入口和首次失稳时刻对齐。
缺少可重复的控制变化，或失稳先于该变化时，不支持这条解释；相关性仍不证明能量必然转移。
这属于已有轨迹诊断，不新增必经实验或控制约束。

不采用这些材料中的强断言：轮心纵向错开必然形成三脚架支撑、所需力矩指数下降、
删掉某项成本必使Hessian特征值归零、全局advantage必压制低速、PCGrad/等变网络/WBC/MPC
保证无损或绝对稳定、CMDP期望成本等价逐时刻安全。这些均超出当前证据和冻结接口。

### 8.5 Swing合法性、观测/奖励适用性与最小前置诊断（2026-10-08修正）

原Swing候选初始化8/8有效、保留构型且用户GUI确认；这是合法训练起点，无需先学会新任务才能训练。DrawBack成功与Swing失败只能说明当前策略/配方在不同起点上的行为不同，不能排除观测不足、奖励偏好/时域、探索裁剪、critic/optimizer迁移或状态覆盖。不要把原因提前限定为std。

已确认当前Recovery来源为P2 B的update25（B25），不是Motion B250。 两份actor均80204个保存参数元素（含6个std参数），相同150→256→128→64→6网络外形不能识别模型。Motion B250为runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt，SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e；该B是cohort-width A/B的保留旧任务窄tracking宽度臂，腿动作尺度.5rad。Recovery B25为runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44；该B是轮std初值减半臂，腿动作尺度1.6rad；两者独立任务/谱系，不可互换播放spec。两块Swing实际更新分别smoke10+formal100、smoke10+formal75，共195；不拼接为同一模型连续训练250更新。若用户所指B250是另一Recovery实验，先核验checkpoint/spec/terminal后才引用其250更新证据。

“已有成功轨迹”具体指B25从原DrawBack起身保持的轨迹（例如runs/2026_10_8-16_53__recovery_b25_swing_support_probe_ppo0/evaluation_00.json），不包含Swing起点，也不证明Swing能到达其中任一帧。Swing合法来源独立于它，为历史姿态经新USD闭链适配并真实初始化核验的swing_candidate_from_historical_r1。第8.1节原本针对起身后的动态收稳，不是Swing到DrawBack已存在路径的证据。

完整动态restore原则上可作为独立声明的reset：root pose/velocity、全主动/被动joint pos/vel、闭链分支、控制history/previous action与任务时钟语义明确；无需追加沉降或托举，但必须短时读回验证。恢复这些量不保证恢复PhysX接触缓存/求解器内部状态；现有部分trace不足以精确restore。该起点成功不替代原Swing端到端验收，动态reset不是所有Swing训练的强制前置。

下一诊断同时覆盖以下层面，运行须另立有界PPO0预算，CPU准备不改变150D接口：

1. 显式记录真实pre-action policy25D及oldest-to-newest五帧history125D、env/episode/pose/family、初始化完成标记、恢复计时、阶段、物理状态；不能从缺字段的旧trace伪造完整150D输入。
2. 逐维输出样本数、mean/variance/min/max/p05/p95及近常量标记；按family×phase分别统计，分开episode内时间方差与episode均值间方差。环境间方差在共同时间/姿态条件下另报；输入缩放前物理量与实际缩放后输入对应检查。单帧、缺样本或未采集标UNKNOWN/NO_SAMPLES，不补0。
3. 与DrawBack/R0同窗口及同checkpoint对照。零命令、固定高度命令、初始化速度/history重复可以正常低方差；方差小不等于没接线、不具可观测性或actor对其不敏感。反之方差大不保证网络利用它。结合物理状态变化、输入字段读回、实际网络输出以及可物理解读的离线敏感性检查，区分未变化、缩放过弱、字段失接和策略响应不足。
4. 观测可区分性：现有150D含关节/速度/重力/角速度/history，不直接含root height、全平移速度或接触。检查相似输入是否对应需要不同控制的物理状态（height、支持、被动闭链分支等）；缺这些字段不自动证明必须扩维，存在任务相关混淆证据时才准备单变量观测版本迁移及checkpoint适配，不现场改冻结接口。
5. 同时记录actor未裁剪均值、实际std、实际采样/裁剪动作、逐通道裁剪与力矩限幅；确定性与随机诊断单列，不额外消耗RNG改变原采样。检验std附近是否能产生有效不同动作，不能只看std标量。
6. reward按family×phase读回raw/weighted/dt贡献、gate激活、一次事件与终止；比较抬升/支撑收益、pitch/vertical/effort等成本及失败前实际回报，检验低位奖励是否有辨别力和可达成功反馈。奖励不直接提供环境梯度；信号量级不是因果结论。若需要，真实on-policy batch再诊断critic/return/advantage，PPO0不能冒称已有该证据。

纯CPU逐维统计已提供domain.observation_diagnostics.summarize：输入显式N×150 tensor及唯一env/episode ID、调用方先按family/phase分组，输出150维标签及时间/episode间方差；不运行模型、不读Isaac/RNG/文件。后续已完成显式runtime采集与真实150D统计；实际输入/动作/reward、时相核验及结论见本节顶部2026_10_8-17_39诊断报告。CPU helper通过本身仍不是行为认证。

“优化迁移”细分为：来源actor在新Swing状态分布上的泛化（冻结模型也可诊断）；共享actor同时学习Swing/DrawBack/R0的更新干扰（须实际更新/分组优化证据，旧组退化只证明现象）；来源critic价值预测与Adam一二阶矩在新回报/梯度分布上的适用性（继承正确不等于适用，不能无证据清Adam）。三者不能统称为已确认梯度冲突。

建议诊断顺序：CPU先核验来源/接口/实际字段和reward公式，利用旧轨迹量级；一次有界采集共同记录输入/物理状态/动作/奖励，先判字段时相/缩放/历史接线，再判状态可区分性及actor裁剪响应，再审奖励信号；只有这些不足以解释，才另申请真实on-policy batch的critic/GAE/advantage/分组优化诊断。近零方差+物理量变化需对照字段定义与同一时相逐样本映射才可判失接，不单凭方差。

首轮runtime采集原提案（后续用户已批准，147.458秒/PPO0完成；下述为批准边界）：冻结Recovery B25，原合法Swing/DrawBack/R0，单seed104、每组64env布局/8scored，确定性推理、每组最多23仿真秒，三请求最多69仿真秒；真实失败按原终止提前结束，不延长失败episode或为了方差重置重采。总墙钟上限900秒（含App初始化/采样/写盘/清理，至少60秒退出余量），PPO/optimizer0，GPU0 shared、UUID核验与逻辑cuda:0，不停止其他进程。随机动作本轮不执行，仅对保存输入离线算未裁剪mean/std和Gaussian裁剪尾概率，不消费采样RNG；如需实测随机探索轨迹另定预算。

新config/run使用集中命名recovery_b25_input_action_reward_probe_ppo0，独立spec/ledger/publication/授权，raw限定8scored env、policy100Hz、最多55200行；NPZ保存真实150D及pre/post对齐物理数组、动作mean/std/executed与有效mask，JSON保存字段/单位/布局/身份/时钟/请求/终态/分项reward与诊断汇总，Markdown给复盘。重算reward和实际runtime读回分别标注，缺字段UNKNOWN；保存实际physical root/joint/contact用于观测可区分性，不宣称完整PhysX可恢复。所有文件仅写新configs/experiments/<集中名>、runs/<集中名>、isolated/<新审计目录>；旧run/checkpoint/spec/ledger/raw只读，外部同事项目不写。建议存储总上限256MiB，达到上限记不完整并有界退出，不能静默丢字段后给结论。所有路径/预算在采集spec中冻结；本提案不是运行授权。通知默认禁用，若用户需要通知，另明确授权当前session作为唯一接收目标。

根据联合诊断选择一个变量：实际字段失接先修工程；相似输入对应不同必要控制才研究观测；奖励对恢复进展辨别不足才研究奖励；实际裁剪阻碍动作变化才研究探索/分布。保留B25及DrawBack/R0评估，不预设只能调std，也不同时修改观测、奖励和探索。

### 8.6 下一执行块：优先检验Swing前段wheel mean越界（2026-10-08）

#### 目的、来源与唯一变量

回答：“在奖励、物理与采样保持不变时，让Swing前段raw wheel mean离开持续裁剪区域，能否带来有效动作变化与起身进展，同时保住旧组？”诊断已发现左轮mean距边界至少10.85个std；不能默认用再次减std解决。

来源固定为Recovery P2 B25：runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。严格继承actor/critic/全部Adam及实际std，不清历史矩、不再次减半、不从失败new75续训。初态仍为已合法且GUI确认的Swing、原DrawBack/R0，固定训练family环境26/25/13；新USD、150D输入、6D动作、奖励、成功事件/终止与原验收协议保持。

唯一新增项为作用于当前on-policy真实Swing/pre_entry受控输入的wheel rawmean辅助loss：lambda=.001、margin=.9仅为CPU起始提案；腿/std没有直接辅助loss，旧组/初始化/入口后样本mask=0。它是优化干预，不是环境reward或控制器，不乘policy dt，不改动作执行映射。方案B和任何观测/reward修改本块关闭。

#### 第一步：工程接线与可审核的CPU交付

1. 新schema独立声明版本、wheel channels2/5、lambda/margin、eligibility、样本选取/分母、每个优化步骤应用次数、梯度裁剪顺序和启用phase；默认关闭。公共Recovery准备器保留统一publication/spec/ledger身份，不复制trainer。
2. 从真实pre-action env/family/episode/initialization/first-entry metadata生成mask；rollout输入detach并复制，不将source轨迹当on-policy PPO数据，不根据root height猜Swing。确认所用observation正是actor看到的policy＋history150D。采样metadata记录不消耗RNG、不改变distribution缓存。
3. 先审核RSL-RL公开optimizer pre-step hook和真实minibatch数据访问：若有可靠索引，使用本minibatch受控样本分母；若无，明确采用本rollout固定诊断/辅助batch及其独立分母与复用频次，不能伪称当前minibatch，不能替换optimizer私有实现。实际选择必须在spec冻结，不能以“都是mean loss”掩盖权重变化。
4. CPU使用真实B25网络和显式样本，核对auxiliary gradient方向、稀释后的lambda量级、actor参数梯度norm及PPO/entropy/auxiliary分开。历史数据没有真实PPO梯度，相关比较记UNKNOWN；实际runtime再记录。检查hook发生在梯度裁剪前还是后，保证最终合成梯度正确裁剪且不改变非启用路径。不得无证据称lambda=.001已足够或保证不遗忘。
5. 测试真实接线：off路径无参数/Adam/RNG/缓存差异；只轮输出项和指定mask进入loss；旧组loss0不代表共享网络不会改变；metadata reset边界、空eligible batch、非有限、输入形状、梯度合成/clip、source_eval不干预。独立CPU fixture可做optimizer测试，但记录它不是PPO/仿真成果，不导出或覆盖来源checkpoint。
6. 根据CPU/接线结果确定一个固定lambda和分母；若改起始lambda，写清量级证据后再发布新声明。本块不做在线lambda搜索、增大std或多系数A/B。生成未授权新spec/budget/poses/manifest＋完整发布SHA、严格初始化审核、PORTABLE冻结CPU验证及supervisor零写plan。

交付必须包含：requested→effective loss接线、mask/分母/复用次数、全部参数/std/Adam恢复读回、已知PPO梯度证据缺口和明确可提交状态。当前proposal_costs仅纯CPU函数，以上接线尚未实现，不能把2个函数测试当完成。

#### 第二步：首块runtime建议额度（须新明确授权）

| 阶段 | 上限与实际证据要求 |
|---|---|
| source_eval | PPO0，≤900秒；同一B25三组23秒协议基线，原Swing允许失败、旧DrawBack/R0要求完整通过；身份/物理/初始化异常阻断 |
| smoke | 10更新、≤900秒，81920样本；三组有效初始化和真实completed-episode事件；至少一次真实optimizer更新、eligible Swing loss/gradient实际非零，source_eval关闭干预；不要求尚未学会的Swing先成功 |
| formal | 最多50更新、≤5400秒；409600样本；建议10/25/50保存与完整三组评估，最终不足计划点也保留实际结束候选；不自动耗完额度 |
| 总计 | 最大60实际更新/491520样本、phase墙钟≤7200秒、chain≤7260秒含60秒退出余量；含启动/保存/评估/清理，旧账本余额不复用 |
| 资源 | 延续物理GPU0共享政策，提交前核验UUID/逻辑cuda:0；不停止他人进程、不自动换GPU |
| 通知 | 默认不发送。因用户此前希望自动收到终态，下一运行审批须明确“完成后通知当前负责人session一次”是否授权，再冻结开关/target；不默认套用旧通知授权或继续误用禁用设置 |

上述runtime额度是提案，不是本轮文档修改授权。公开提交只走supervisor，正式前须匹配wiring_certificate；一次有界握手后交后台，不轮询、不增加watcher。

#### 评估与停止：避免只把mean变好看

固定三组同checkpoint完整评估，旧DrawBack/R0各8/8完整10秒为保留标准，Swing最终也必须同协议8/8，不能拼模型或放宽continuous_contact/tilt门限。

同时记录family×phase有效transition/初始化比例、rawmean范围、analytic clip概率（注明沿访问状态）、真实随机训练action clip与PD限幅、实际std、auxloss/eligible数/梯度、source与checkpoint actor行为差异；优化器真实样本探针和PPO损失分开，不能把fullrollout探针当minibatch统计。

Swing学习进度看首次.30米穿越、真实entry率、首入口保持前缀、tilt/失触时序、同窗peak height及恢复寿命；从约.231米增加几毫米不称实质成功。高度变高但翻倒更快/旧组丢失不接棒；reward或clip下降不能单独选best。

旧组连续两次固定完整评估失败触发保护；非有限/闭链/穿透/限位/缺失证据按原保护处理。若完整三组通过，保存该候选并停止本块，在新授权下做独立三seed复验，不因预算剩余继续训练。

| 本块结果 | 后续动作 |
|---|---|
| mean/真实采样裁剪改善，Swing入口或保持前缀实质改善，旧组保留 | 保留该局部候选；未完整通过仍不能accepted，下一有界块须新授权 |
| mean改善但Swing仍约.23米/tilt早终止，旧组保留 | 不继续只调lambda；转向低位reward辨别力或可观测性证据，选择一个独立干预 |
| mean/loss没实测变化或eligible为0 | 先核查metadata/hook/梯度clip/实际PPO量级，不直接延长或增大系数 |
| 旧组退化 | 停止分支，认证B25保留为fallback，不从latest继续 |
| 真实状态相关输入仍混淆 | 先提供相似输入但不同必要控制的证据，再设计版本化观测迁移；不先加维度猜测 |

#### 方案B后备与研究边界

弱低位physical clipped wheel-effort cost（−.1/秒、.20–.32米gate）已有反事实量级；它不是零轮矩、制动、LQR或virtual-leg控制，且力矩饱和区可能无法区分不同rawmean。只有A结果提供转向依据时，另从完整来源准备reward单变量；不在A中启用B、不同时打开低位pitch/roll/vertical项或加对称。

浙江大学材料的原仓库URL/版本与实机验证出处仍待核验。提供原链接后，可只读比较Recovery函数、轴/腿长/力矩语义，用作可检验机制；不因传统控制实机成功就将其控制层接入本项目。动态restore仍可选，不是合法Swing训练的门槛。

### 8.7 浙江大学实机控制知识迁移：替代持续调mean系数的下一方向

论坛与附件身份已核验，PDF第13.6节和图9支持Swing后转向向下支撑、收短腿，再进入平衡。首选任务是低位几何进展塑形的CPU核算与端点处理，详见[方法与实施边界](RECOVERY_ZJU_GEOMETRY_METHOD_20261008.md)。本节覆盖第8.6节及顶部历史“下一继续审核lambda”优先级；未授权新的reward runtime或PPO。以B25为来源，方案A关闭、轮矩方案B独立后备、150D及现有控制保持。

### 8.8 快速摆腿支撑与及时收腿：2026-10-09讨论后的下一假说

本节更新第8.7节的下一审核方向：几何进展奖励和仅轮均值有界的实验均未学会Swing，不能继续只按腿长更短或轮clip更少推定可恢复。用户提出快速摆腿触地后机体反弹、立即折腿的机制；认可为待验证动力学假说，尚非本机器人已证明可执行的轨迹。

**原文明确内容**：原PDF第13.6节（35–38页、图9）先让Swing双腿伸长并到预备角；DrawBack同时向竖直向下摆腿（参考200°/s）与收短（参考1.2m/s、目标0.10m），满足双侧收短、等长、向下及机体姿态条件后Return交接平衡。第47页Recovery轮力矩分派为零。上述数字和虚拟腿坐标属于浙江大学串联腿控制，不直接复制到本项目闭链实体关节；原文没有明确要求先制造双轮腾空或一次独立跳跃。

**待验证机制**：快速摆腿建立地面支撑反力，可能产生短时冲量与机体抬升，为同步收腿、将轮心移到机体下方创造空间。摆腿、收腿与抬升可能部分同时发生，不预设必须“先砸地、再收腿”。200°/s是参考角速度，不等于实测撞击速度或可用冲量；单独追求跳高/冲击不能作为成功指标。

**当前原始证据**：最新策略在Swing约0.05s倾角超过0.18rad、0.06s发生接触门槛失触，最终无入口；右两个主动关节在动但相对角差几乎恒定、腿长约0.376m。首步多个PD通道触40Nm，目标没有被主动关节限位裁掉。说明失败不仅是没有抬升，也缺少双侧构型收缩和支点转移；事件先后不能确定冲量或失稳的唯一原因。证据见[腿执行审核](RECOVERY_LEG_EXECUTION_AUDIT_20261009.md)。

下一步按以下顺序准备，不自动启动新运行：

1. **CPU闭链几何审核**：从保存的合法Swing全关节状态及实际新USD分支出发，扫描现有限位内实体主动关节的小幅组合，解闭链并核验closure、轮心位置、腿长和理想碰撞。找到双侧收短/轮心转入支撑位置的方向与候选连续路径；几何可达不等于动态可恢复，不以root高度插值或人工托举替代真实来源。
2. **已有事件重评分**：对齐摆腿速度、真实长度变化、机体高度/垂向速度、左右接触与倾角，区分支撑抬升、腾空和失稳。当前100Hz轮接触力及heldPD不能精确还原1ms接触冲量，也可能缺少连杆触地力；缺字段明确UNKNOWN，不用轮力代替全部支撑力。
3. **必要时提出最小有界动力学诊断**：只有几何方向和字段需求明确后，再声明独立GPU/墙钟/存储/采样预算，采pre/post全关节、必要PD子步及相关碰撞体接触力，验证“抬升空间＋及时收腿”是否发生。需新授权，不能用CPU文档批准启动物理验证。
4. **据证据选择一个训练变量**：目标是形成支撑、及时双侧收腿、进入DrawBack可恢复区域并保持；若发现可达动作没有被探索，优先对应实体腿探索/课程候选，若动作已出现但回报排序错误，再调整奖励。不能同时叠对称、腿bias、轮制动与reward；不直接奖励撞击或跳跃峰高。

150D/6D实体关节控制、新USD、Plane、40/5.5Nm和原控制时序保持；不增加LQR/虚拟腿映射/补偿/隐藏状态机或限矩。浙江大学Recovery零轮矩是机制对照，不在本项目偷偷启用。保留认证B25和完整DrawBack/R0验收，Swing成功必须包含起身与后续保持，不能仅靠一次弹起晋级。本次更新仅编辑计划，未启动GUI、仿真或PPO。

### 8.9 用户确认：缺口是动态过渡，不继续寻找沉降静态桥接态

2026-10-09用户明确反馈：DrawBack附近一旦向Swing方向扰动，被动沉降不能停在过渡态，会自然到Swing；因此撤回“通过一系列沉降静止中间态逐级连接”的优先建议。本反馈作为当前机构课程设计约束，与此前静态中间候选回落/初始化失败相符，但不夸大成全部构型的数学不可能性证明。本节覆盖顶部和此前报告中“下一静态逆向桥接”的建议；保留历史实验事实。

当前任务改为从已经合法的Swing初态研究**动态过渡的可达动作及时序**：

1. 摆腿建立支撑反力，为机体抬升与构型转换创造空间。
2. 失稳前及时双侧收腿并转腿，使轮子进入机体下方的支撑位置。
3. 到达已掌握的DrawBack恢复/平衡区域，由同一自主策略最终完成起身和保持。

三个过程允许重叠，不预设先腾空再收腿；触地冲击、腾空、跳高和几何缩腿都不能单独作为成功。DrawBack“区域”必须用全关节/根姿态速度、轮心与接触证据核准，不能只用root高度或腿长判定；静止DrawBack成功不代表任何高速过渡落点都能恢复。

下一首先准备CPU诊断方案与接口：实体关节目标轨迹/速度和重叠时序的有限候选、各候选的闭链/限位/理想碰撞核验，以及pre/post全关节、必要PD子步、相关碰撞体接触力、机体垂向运动字段。原0.15rad局部几何路径只是方向线索，不直接冒充完整摆腿/收腿动作。浙江大学串联腿参数不直接复制。

若要测试显式诊断动作，必须新声明与新预算，将动作来源、控制覆盖区间、退出条件、限矩和策略接管时刻全部记录；这属于可达性实验，不能称RL自主起身，不能写入常规CommandEnv形成隐藏控制。现行6D实体目标接口/PD/40与5.5Nm/新USD不改；是否允许诊断动作及如何隔离需在具体方案中审查，不从本次文档确认推导物理运行许可。

只有出现真实成功动态轨迹，才可以讨论以其中完整状态做动态restore/动作后缀课程；不要求不存在的静态沉降桥接，不伪造成功来源。后续迁移到RL若使用示教/辅助loss/课程是新的显式变量，需验证旧能力保留并独立授权。当前未找到成功Swing轨迹、无新训练在运行；下一阶段不自动续训、多分量policy重构或叠加奖励。

### 8.10 回到RL的下一交付（覆盖8.9继续开发手写诊断的优先级）

暂停诊断动作adapter扩展，优先一次有限CPU训练目标审核：仅Swing受控前100ms，四腿actor均值相对当前q超出.15rad的软中心成本；不指定收腿符号、不覆盖env动作、不改变reference/std/reward/轮分布。该项明确是PPO＋辅助loss，可能影响旧任务或抑制必要发力，必须先核梯度/PPO量级，不直接进入runtime。

审核通过才准备新同源A/B短训（每臂smoke10/formal≤25、10/25完整联合验收），完整来源、预算、loss定义和停止条件见[下一交付草案](RECOVERY_RL_NEXT_DELIVERY_20261009.md)。当前无新spec/ledger/仿真PPO授权，旧几何和手写动作不是成功示教。

## 9. 当前 Swing-only 选模、认证与后续拓展 — 2026-10-10

### 候选排序

1. 同一checkpoint从合法Swing起身并完成原要求10秒保持，全部必需Swing scored env通过优先；DrawBack/R0不参与accepted。
2. 未通过时分别报告入口数、两侧收腿/轮心进展、落地接触、保持前缀与失败项；诊断候选不冒充成功策略。
3. 镜像误差、动作/力矩和漂移解释行为，不以对称程度或总奖励单独选best。
4. source/latest/best_new/best_overall/accepted独立记录，不拼接不同模型成功点；旧技能模型独立保留。

### 认证层级

| 层级 | 可作出的声明 |
| --- | --- |
| CPU/冻结计划通过 | 接线与声明已验证，不代表恢复能力 |
| 双侧几何或入口前缀进展 | 局部学习进展，不是起身成功 |
| 固定seed的必需Swing scored env完整起身+10秒保持通过 | 规定初态范围内的初步成功候选 |
| 同一checkpoint多个评估seed/合法Swing扰动通过 | 对已测范围的重复性或泛化；评估seed不是独立训练seed |
| 独立起身后100秒保持通过 | 耐久证据，需另定预算；不是任意倒地或实机认证 |

DrawBack/R0可选评估只给诊断结果，不阻断Swing任务学习或选模。未通过旧组不能称通用模型，旧结论不重写。出现完整Swing成功候选后及时保留和有界复验，长训预算不是必须用完。

### 课程顺序

当前直接学习合法Swing起身；不再要求先扩大静态DrawBack扰动、找到可沉降中间态或证明旧组持续通过。DrawBack只是动态构型参考。学会Swing后才另议初态扰动、泛化或其他倒地姿态，不自动启动Level4或能力合并。

## 10. 历史多初态决策表（被第0/9节覆盖，不作为Swing-only停训依据）

| 观察到的结果 | 首选动作 | 不做什么 |
| --- | --- | --- |
| 新高度协议已有完整候选 | 同模型有限PPO0复验，再准备下一小扰动级 | 为了“训练够久”盲目追加 |
| R0仅因旧0.38上限失败 | P0从完整trace按新协议重评分，检查其他真实失败项 | 直接宣布不会平衡，或直接回填通过 |
| DrawBack仍冲高后滑行失稳 | 先P1完整任务覆盖；结合geometry原对照决定是否保留其成本 | 再提高lift、同时加多项惩罚 |
| 新任务保持2–10秒样本始终为0 | 区分FSM提前终止与policy确实过早失败；前者修接线，后者是行为训练问题 | 将普通失败当所有程序都不能运行 |
| 随机训练大量饱和，确定性更好 | 逐通道/阶段确认后P2轮探索单变量 | 改力矩上限、PD和std三项一起救 |
| R0会保持、真实落点不会 | P3实际过渡状态覆盖 | 找另一站立模型直接硬切来掩盖当前能力 |
| 对齐变好但起身更差 | 回退，否定本次具体干预收益 | 加更强对齐或硬锁左右动作 |
| 全部reward/姿态/运动指标后段变差 | 提前选优并停止该分支，查采样/优化证据 | 说一定是“速度换姿态”的必要权衡 |
| 协议字段/证书/冻结路径错误 | 完成CPU修复与冻结worker验证，按真实已用预算准备有界重试 | 覆盖旧snapshot、改历史通过数、重置账本 |

## 11. 交付、预算与后台执行

每次只准备一条明确问题的实验链。新目录通过集中命名函数生成
`YYYY_M_D-HH_MM__purpose`，独立spec/ledger/output，保留source/asset/code/protocol SHA。
Recovery已用额度按本线exact attempt核对，不借用Motion剩余预算，也不从旧10000声明推断新许可。
计划预算是上限而非必须用完；source_eval、smoke、formal、复验、清理分别记录墙钟。

先完成共享代码与冻结副本CPU验证、plan-only，再核对实际授权和资源。
沿用已明确的物理GPU安排时核对UUID；新的shared使用仍须满足已有明确共享授权，
不停止别人的进程，不因GPU繁忙擅自迁移设备。当前运行副本不热更新。

后台supervisor只一次有界启动握手；报告准确阶段，source_eval/smoke不等于formal已开始。
既有owner执行预算、检查点评估、结算和已授权通知；交互worker不轮询、不另建watcher。
终态通知本身不授权续训。新阶段如已有覆盖授权，按其分支和额度执行；否则只发布准备结果。

### 每轮最少交付

- 一页结论：选哪个完整身份模型，来源/新候选各有什么能力，是否继续该分支。
- 逐family/pose/环境结果，完整通过与诊断前缀分开；失败原因与未采集字段可见。
- reward raw/weighted/dt、阶段覆盖、std物理量、逐通道限矩和必要优化探针。
- 实际更新/样本/墙钟、attempt终态、used/remaining及重复提交检查。
- 精确改动文件和验证命令；当前工作树、Git提交、冻结run三个身份分开。
- 下一项最多一个实验变量及具体触发条件，避免继续用“未定位唯一根因”代替可执行结论。

## 12. 本次计划的验证范围

本次只编辑本文。依据是已完成的20_55终态及25/50/100原始评估、18_06历史训练/评估、
冻结实现、前述新离线图/事件数据和三份参考材料审阅；没有新增PPO/物理采样。
已经核实的事实与待实现方案按章节分开；P1新协议、新reward和新FSM尚未实现或训练验证。
最终使用前按当前代码核对函数位置，不能把本文的新语义名称当成已存在的CLI参数。

## 13. 后续执行者的简短指令 — 2026-10-10

> 先读AGENTS/README/STATUS与本计划第0节。现实起点只有合法Swing，DrawBack是人为设置的动态支撑参考；准备Swing-only采样、Swing-only必需评估和旧组仅诊断的停止/选模契约。
> 优先审核并显式设计双侧收腿/轮心位置进展与镜像分项，避免继续只提高乘积奖励或拉近当前位置；允许过渡腾空，最终仍要求落地起身与完整保持。
> 150D/6D实体动作、新USD、Plane、40/5.5Nm及1/5/10ms保持。CPU准备后发布独立新配方和预算，运行另需授权，不续历史余额、不改旧run、不停止他人、不将工程PASS当能力PASS。
> 本文为计划，当前代码/spec未自动变成Swing-only；先核查公共准备器、smoke事件和单family评分接线，不靠虚构旧证书通行。

---

## 历史记录：以下原文保留，不覆盖上述新目标与计划

<details>
<summary>展开2026-10-06至2026-10-07此前决策、旧来源和旧高度协议</summary>

最新授权：用户明确批准20_42失败后的新独立尝试2026_10_7-20_55__recovery_level2_alignment_from50，同source50/DrawBack与弱几何成本。
旧失败证据保留；source600s、smoke10/600s、formal<=100/3600s，25/50/100筛选。
实际运行状态以新run为准；下方20_42 FAILED属于前一次尝试。

最新终态纠正：20_42对齐短训source_eval因full_trace_updates协议字段接线遗漏失败，
smoke/formal均0；当前无该链formal更新。共享代码修复不等于重启，原失败证据保留。
见[失败复盘](RECOVERY_LEVEL2_ALIGNMENT_20261007.md)。下方提交说明为历史启动事实。

## 当前更新：Level2起身后收稳单变量试验 — 2026-10-07

用户已批准[弱轮心对齐短训练](RECOVERY_LEVEL2_ALIGNMENT_20261007.md)，新根2026_10_7-20_42__recovery_level2_alignment_from50。20_17补采已完成；8env事件顺序为错位增大、高度出带、失触，窗口复算一致，仍非因果证明。只增加-.1高度门控轮心成本（.32–.36m、4cm死区、20cm尺度），不改轮平滑/制动/腿长项。source18_06 update50；source600s、smoke10/600s、formal<=100/3600s，总110；25/50/100完整评估与R0回归，GPU0共享。旧“补采未授权/待执行”均为历史，当前状态以本次run为准。

## 当前交接决定：转向自主起身 — 2026-10-07

用户已批准并提交[冻结50完整几何补采](RECOVERY_UPDATE50_GEOMETRY_PPO0_20261007.md)：
20_17独立根，固定8env/seed104/23秒，单次600秒、零PPO，原模型/控制不变。
用于区分剪刀构型、失触和高度事件，未启动对称或轮平滑训练；不轮询等待。

[剪刀腿参考核查](RECOVERY_SCISSOR_REFERENCE_REVIEW_20261007.md)：轮心纵向错位
与腿长差分别测量，new50采样支持剪刀趋势但未证明因果；wheel normalized delta成本
对new100目标跳变量级弱，下一步优先冻结50完整几何PPO0补采，预算未授予。
不同时启动几何约束/轮平滑两个干预，不照搬参考材料保证性论断或重构控制架构。

最新[轮控制时序诊断](RECOVERY_WHEEL_TIMELINE_REVIEW_20261007.md)已完成离线核查。
new100明确出现约50Hz逐策略步目标/力矩交替，new50末段无此问题。
new50关节镜像偏差不等于腿长差，完整height/geometry时序缺失；先做action历史/
轮成本尺度检查，需完整几何时再独立PPO0补采。暂停提前加腿长惩罚的提案。
本项用户只批准离线诊断，不启动新训练。

最新执行回顾：[Level2收稳诊断](RECOVERY_LEVEL2_TRANSITION_REVIEW_20261007.md)。
用户随后明确批准18_06水平成本probe独立预算：source600秒/PPO0、smoke10/600秒、
formal最多100/3600秒；当前账本AUTHORIZED，下文未授权为准备阶段记录。
用户批准后已做离线分段量级审计与report/ranking修复；没有续训。
新准备根2026_10_7-18_06__recovery_level2_settle_cost_probe，预算UNAUTHORIZED，
拟议保持旧1000/DrawBack/newUSD，只降水平成本幅度-4→-1并补评估control证据。
这是待检验干预，不把奖励幅度、限矩饱和或初始化课程解释为唯一根因。

### GUI复核后的初态纠正 — 2026-10-07

用户现已通过旧update1000 GUI确认该manual0001正是所需收腿支撑初态，
并明确授权迁移新限位USD、开启Level2。现行声明见
[Level2迁移](RECOVERY_LEVEL2_DRAWBACK_20261007.md)，独立根
`2026_10_7-17_21__recovery_level2_drawback_from1000`。
source用旧抬升update1000、strict恢复150D和实体动作；source资产身份与新资产身份分开。
新预算source600秒/PPO0、smoke10/600秒、formal最多100/3600秒，不动旧耗尽账本。
当前接口/证书要求两个family各自有效episode，提交后不交互轮询。

用户指出本轮低位构型属于Swing预摆位，要求回到保存过的DrawBack收腿初态。
已找回原始manual0001：
`runs/recovery_pose_capture_20261002_145814/pose_0001_73d09dbe.json`，
SHA256 `1ebaf39d3c07283c01cb519f3ab8e5b3acd7c5d5ded4a08faa88f29ac41b699c`。
实测root0.168474m、chassis理想净空0.098474m；实体关节left/right hip
约-0.02339/+0.02338rad、active-link约+1.43179/+1.43216rad。
这是原保存的实际joint_pos，不是capture UI显示的requested_leg_rad；后者仍是
旧请求[1.4,-1.2,-1.4,-1.2]，PASSIVE模式下不代表实际构型，不能用于复建初态。

早期spec `recovery_r1_manual0001_20261002`与`recovery_self_stand_from1500_20261003`
的R1 train/holdout均确实采用这一构型。manual0001 retry正式433更新，update400
有抬升但旧handover gate0/8；后续self_stand正式1000更新，update1000最终高度
约0.439m，仍因旧自主稳定条件未满足而0/8。它们证明这份初态曾用于训练且
学到明显抬升，不等于今天起身/10秒保持验收通过。

本轮使用的是10月3日另一捕获构型的闭链修正版，hip约±1.14rad、active-link约
-1.41rad。与manual0001虽高度相近，关节支撑构型不同；此前未将原manual0001
纳入PPO0定位，是初态追溯不足。两份插值中间姿态沉降失败不能否定原收腿初态。

当前knee-stop资产离线复核：manual0001原joint_pos闭链最大2.72e-7m、所有关节
均在当前authored limits内，原root高度下理想最低间隙约-1.41e-7m。
旧asset SHA与当前不同，因此仍需当前资产下独立运行初始化验证；本次未仿真。
下一步优先在新声明中复用这份实测收腿构型、实际方向与闭链分支，比较source50
和具备历史抬升证据的候选；经GUI/几何确认它对应用户所指DrawBack，再进行
课程Level2。保留Level1回归，不从本轮退化update100继续，不启用Swing/随机翻转。
高度只是诊断，轮相对root的纵向偏置和实际接触须一起确认，不用人工改root高度
冒充正确收腿姿态。参考材料中的力学死点、探索势垒仍是假说；不据此加软制动、
强对称或动作偏置。此纠正不增加模拟/PPO预算，不自动续训已结束链。

用户现在的优先目标是**尽快学会自主起身，并在起身后不摔、基本水平**。

执行更新：用户随后明确批准实行本计划。现行配方与独立预算见
[首次低位起身](RECOVERY_RISE_LOW_20261007.md)，当前根为
`2026_10_7-16_18__recovery_rise_formal_from50`（正式阶段）；已完成的来源/smoke
证据在`2026_10_7-15_58__recovery_rise_low_from50`。PPO0定位已证明两个新中间姿态
被动沉降后初始化无效，暂不训练；已有低姿态8/8有效，故首轮直接采用此低位组。
训练期限定为11.5秒，独立观测23秒含初始化与起身后完整10秒保持；
下文15秒仍为历史提案，不是当前运行值。首个15_51提交在AppLauncher前失败，
消耗0；修复冻结身份接线后使用新根，旧证据保留。运行事实以新run优先。
15_58的10次smoke完成后又被completed字段接线误报阻止formal；仅在新目录
更正证书、导入已有使用和身份记录后执行formal-only，未重复smoke或增加总预算。

本节取代下文历史段落的“下一步”、入口和预算建议；历史内容保留以追溯来源。
最初计划编辑阶段不授权 AppLauncher、PPO或额外评估；后续用户执行授权
仅限上方新声明与独立预算，仍不允许旧链续训。
执行时仍按 AGENTS → STATUS → 新 spec → 实际 manifest/ledger/raw evaluation 核验。

### 已有证据与默认来源

默认起点仍是 `runs/standing_scissor_20261006/formal/model_update_50.pt`，SHA256
`1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。
这是当前 survival/level 协议下保留的来源，不是已认证的任意倒地起身策略。

| 原始证据 | 当前可作出的判断 |
| --- | --- |
| [source_capability 终态](../runs/recovery_coverage_ab_20261007/source_capability/terminal_report.json)：R0、R0_perturbed，各 seed104/205，各8环境×10秒，总32/32，PPO0 | 来源已覆盖本组近站立扰动；不再为已通过的这组初态单独安排 R1 PPO。不能外推到更大扰动或低姿态。 |
| [A_first 正式结果](../runs/recovery_coverage_ab_20261007/A_first/formal/analysis.json)：100更新/819200样本；25、50各8/8，100为0/8 | update100 全部因 roll 超限失败，均完成10秒且无 runtime fault；这是水平退化，不是本轮跌倒。 |
| [B_uniform 正式结果](../runs/recovery_coverage_ab_20261007/B_uniform/formal/analysis.json)：同预算；25、50、100各8/8 | 全 rollout 有效样本均匀选择支持减轻 roll 退化；只有一组训练随机流，不能保证长期无遗忘。 |
| 两组 candidate_selection：best_new=update25，best_overall/accepted=source50 | 不从最新100继续训练；B 的通过不等于净收益，mean abs vx由来源约0.704升至1.105m/s。漂移仍仅为诊断。 |
| 本轮两组 durability=NOT_RUN | 本轮没有100秒新认证。已有历史100秒评估/重评分需按其模型与协议身份单独引用，不能套给本轮候选。 |

课程名与 pose family 必须区分：课程 R1 是 `R0_perturbed`；family `R1`
是历史低位姿态，属于课程 R2。不按字符串“R1”直接判定难度。
两组完成事件分别为 A `250b545a9918a358c91f6cf0`、B `f865405426068218aa206370`。
通知中的 accepted=True 指来源回退，不代表最新模型通过。

### 最短推进路线

1. **先做 CPU 证据整理与起身接线检查。** 定位已有低位自主 Recovery 的 checkpoint、
   原始逐环境轨迹与 pose 身份，确认是否有可复用的自主抬升片段。旧模型只进入候选清单；
   旧2秒、teacher handover 或不同高度协议不等于当前自主起身认证。已有
   [manual0001](RECOVERY_MANUAL0001_START.md)记录约0.168m低位姿态，但历史几何检查
   不替代下一轮的初始化回读。
2. **准备一次有界 PPO0 能力定位。** 在新声明中明确一组闭链一致、可实际落地的
   中间低姿态和 captured0001，比较 source50 与有证据的历史自主 Recovery 候选；
   数量、seed、起身期限和墙钟先冻结，不做无限 checkpoint sweep。
   测初始高度、最大抬升、首次到达站立区、连续保持、倾角、接触及失败原因。
   普通起身失败是能力边界，不是训练前必须通过的 gate；非法初态/闭链故障才阻断。
3. **从最近的能力边界训练。** 如果来源在某组低姿态已经能起身，保留该能力并向
   更低一级扩展；如果完全不能抬升，先选择更近的中间姿态。按实测 root height、
   腿构型、方向和接触分组，不凭空指定0.15/0.20m为可行 reset。
   本轮只启用一个新难度组；不重新花主要预算训练已通过的近站立扰动。
4. **固定任务配方，分段保留候选。** 建议首轮 smoke10+formal最多100更新，
   formal评估25/50/100；64×128下总110更新/901120样本。这是待定预算提案，
   尚未创建 spec/账本或分配墙钟；PPO0基线与评估/清理须各有有限墙钟。
   smoke必须覆盖实际起身/超时事件及真实参数更新，不能仅证明程序启动。
   不能覆盖完整事件时报告证据不足，不静默增加更新额度。
5. **按新增起身成功与旧能力保持选模。** 保留来源和早期 checkpoint；失败分支
   不成为下一阶段默认起点。当前新组获得独立多seed起身结果且旧R0无回归后，
   才另行考虑下一难度。100秒耐久是所选候选的后续独立验收，不把它当作
   首轮低位探索的前置条件，也不宣称10秒通过已经耐久。

### 起身奖励、终止与成功必须重新对齐

当前 coverage 配方是近站立保持：`lift=0`、`upright=0`，height正项3，
pitch/roll平方成本各-4且 unconditional，failure_once=-1；连续项乘dt一次。
不能原样用于低位起身，也不能先凭感觉提高惩罚权重。

- **恢复阶段信号：** 恢复显式、有限的抬升与直立信号；检查低高度下的有效量级。
  现有 lift 是相对初高的高度进度，不是相邻状态势差，不称为有最优策略不变保证的 PBRS。
  精细水平和减速成本在接近站立时平滑增强；记录 gate 覆盖，避免低位必要运动
  被终态成本压制。具体权重/高度门槛在新 spec 冻结前以实测状态离线对比。
- **保留项：** uniform_rollout 作为优先候选，coefficient先保留0.02；仅约束
  来源已认证的近站立有效输入，不对低位输入强行模仿未知来源行为。
  reset 初始建议旧任务40%、新组60%，属待检验提案；另测实际样本占比，
  episode 长短不同会使 reset 比例与 rollout 占比不同。记录 family/pose/episode/
  时间覆盖；不同时改变环境数、LR、网络或 advantage normalization。
- **快速失败 reset：** 当前 `minimum_up_cos=0.5` 即总倾角约60°以上可立即终止
  对应环境 episode；不是停止整个 trainer。当前代码还检测禁止接触、初始化拒绝
  和 runtime fault。站立 gate 的均值0.10rad/峰值0.15rad不是当前全程立即终止门槛。
  低姿态需要独立核验60°是否排除了合法初态/恢复路径；不要把站立的小角门槛
  直接施加于恢复全程。接近站立后可以另声明带连续超限时间的倾角失败规则，
  但不能在本轮历史 run 中追溯应用。
- **接触规则：** 起身允许已确认的支撑接触。当前允许模式包括 robot、轮和多种连杆；
  因此不能声称“任意机身触地就失败”。逐个核对实际 body 分类与传感器，
  弱组件未建模仍为UNKNOWN。不为了易通过而禁用闭链、穿透、非有限或关节安全保护。
- **成功事件：** Recovery actor 自主从声明低位到达0.34–0.38m站立区，
  以现 survival/level 高度、水平、接触标准连续保持2秒作为拟议训练成功；
  期间无 teacher 接管。建议最多15秒起身期限，超时失败仍属任务数据。
  在线事件奖励只发一次；成功 episode 的bootstrap/终止语义在新 spec明确。
  独立验收记录完整恢复过程，随后同一episode连续保持10秒，保持指标窗口从
  达到站立条件起计算，不能把固定[2,10]直接当作低位起身后的稳态窗口。
  总时长必须足以容纳起身期限与10秒保持，早终不能缩短要求；所有初始环境
  进入分母，禁止只评分已成功的子集。这是拟议新协议，尚无运行认证。

最少诊断：每pose有效初始化数/尝试数/成功数、起身耗时、峰值抬升、
连续保持时间、首次失败原因、姿态/高度/接触/力矩限幅/闭链，分阶段reward
raw与dt后量级、return/value/advantage，以及retention eligible/selected覆盖。
runtime fault、物理失败、超时和保持证书失败分开统计；未知历史梯度不补零。
新 evaluator 若尚不支持事件对齐保持窗口，应先补纯CPU fixtures与plan-only，
不能用错误窗口启动训练。

### 两份参考材料如何使用

[TRAINING_EXPERIENCE_REUSE](../TRAINING_EXPERIENCE_REUSE.md)提供证据优先级、
真实事件接线、奖励单位/量级、旧能力回归、同源对照和候选筛选规则；其历史
“当前未运行/固定站立”描述不代表今天状态。
[参考文献](../参考文献.md)可借鉴逆向初态课程、支撑几何排查和分阶段奖励，
但没有可追溯论文来源或本项目干预证据。短腿一定更容易起身、两腿必须完全同步、
门控消除局部最优等只是假说；先核对原生机构与轨迹，不将其写成根因。

不引入硬状态机代替策略起身、残差轨迹控制、虚拟腿映射、WBC/LQR、重力补偿、
限矩增加或无限力矩“解冻”；不硬锁轮/左右动作，不修改USD。
合法滚动不等于滑移，不因轮转就盲目加入强轮速/对称惩罚。
本任务不训练速度跟踪，不能把“趴地偷速度reward”当作已确认机制。

### 实施边界与下一位执行者

只通过 `native_stand.command_v6.supervisor` 提交；下文旧 launcher/train_stages
命令仅历史说明。新配置/run根使用Asia/Shanghai的
`YYYY_M_D-HH_MM__purpose`，独立ledger，记录来源/资产/代码/协议SHA。
先CPU回归和零写入plan-only，再按明确授权预留exact attempt。
用户此前允许共享GPU0且禁止停止其他进程；资源同意不等于新的PPO或评估预算。
当前两组已COMPLETED，不重启、合并账本或使用剩余额度；当前会话身份需重新记录。

最初计划编辑阶段仅改本文，未新增spec、预算、模拟、训练或历史重评分；
后续执行阶段的新增声明与实际使用见本节顶部执行更新及对应run。

---

以下为历史决策，所有“当前/下一步/授权”仅属于所注明日期和run。

## Current Decision: User-Approved Survival and Level Posture -- 2026-10-06

New authorized implementation supersedes the preparation paragraphs below:
[survival/level R0 -> R1](RECOVERY_SURVIVAL_LEVEL_20261006.md), fresh10000total
updates3smoke+9997formal. Read STATUS for actual detached startup and runtime.
New frozen protocol removes motion/symmetry gates consistently across reward,
online success, curriculum, evaluation and selection. Old experiments stay intact.

The user accepts `runs/standing_scissor_20261006/formal/model_update_50.pt`
by GUI and changes the current objective to **avoid falling and keep the body
level**. Zero-speed regulation, bounded planar drift and strict leg symmetry
are no longer promotion requirements for this next task; retain them as
diagnostics. This is a changed task, not an improvement of the old acceptance
score. Original specs, evaluations, ledgers and automated selections stay intact.

Next source SHA256:
`1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`.
Its existing full evaluation records 8/8 continuous10s, no runtime fault,
mean root height0.36667m, dual support100%, mean absolute pitch1.26deg and
roll4.15deg. Mean absolute vx0.70411m/s is a diagnostic, not a rejection under
the user's new goal. The model is GUI-approved for this goal; it is not certified
under a new machine-readable protocol or the old stationary-standing protocol.

Proceed next to **R1 enlarged near-standing perturbations**, keeping R0 samples.
R1 does not mean the captured bottom-down pose: that is curriculum stage R2.
In code, R1 uses pose family `R0_perturbed`; pose family `R1` is the low-pose
family and must not be selected by confusing family names with stage IDs.
Do not require the newly harder R1 cases to succeed before starting R1 learning.
Validate their initialization, closure and control path first.

Before submission, create a new spec with matching reward, success/FSM,
curriculum and evaluation semantics. Do not leave old speed/drift/symmetry
conditions silently active after removing them from the report. Retain height,
support, pitch/roll, continuous survival and all physical runtime protections.
A proposed level tolerance consistent with the accepted GUI is mean absolute
pitch/roll<=0.10rad each and peak<=0.15rad; these are proposed new values,
not retroactive thresholds or a completed new acceptance test. Promotion to
R2 should still require two non-overlapping128-episode windows and two full
evaluations under the frozen new protocol. Only subsequent resets change stage.

This update records task intent and the next source. It starts no simulation/PPO,
allocates no budget and does not enable stages in a historical spec.

## Previous Decision -- 2026-10-06

Wheel alignment probe is COMPLETED/reviewed:53updates, offset16.69->8.08cm,
but vx0.704m/s and roll/leg-length gates fail. Not a stable/symmetric solution.
No continuation; lower-weight same-source comparison is the next proposal.
See root STATUS and STANDING_SCISSOR_EXPERIMENT_20261006 completion review.

Current task supersedes BC test: [wheel alignment probe](STANDING_SCISSOR_EXPERIMENT_20261006.md).
Source1500 unchanged, fixedBC0.02, only wheel-center geometry reward added;
53updates transferred,1140old remaining unspent. Runtime/FK64samples passed,
3smoke complete, formal startup actual1. No automatic extension. Read STATUS.

Current authorized next experiment: [BC gradient / annealing A/B](STANDING_BC_AB_20261006.md).
Yaw-only chain is completed at103updates,0/8 strict acceptance. Two new arms
transfer206updates (3smoke+100formal each), leaving1193 old updates unspent.
Same source1500, seed/Adam/LR/reward/physics; only full-channel BC schedule differs.
No automatic wheel-only/mirror experiment or long continuation. Read root STATUS
and pair run manifest/terminal for actual state; paragraphs below are history.

Superseding entry: [yaw-only review](STANDING_YAW_REVIEW_20261006.md).
The separately authorized2000-update v2 long run stopped at498updates;103remaining
updates are transferred to source1500 yaw-only smoke3/formal100. Remaining1399
old updates are not automatically resumed. Original metadata below is historical.

Bounded v2 source10s/smoke3/candidate10s verification is now complete;
[report](../runs/standing_level_v2_check_20261006_151025/completion_report.md).
3updates/24,576samples,216.52s. Both models survive10s but fail drift/vx/yaw/mirror;
source remains best observed, accepted=null. No long continuation authorized;
the new ledger's formal limit is0. Earlier UNAUTHORIZED statements below describe
preparation history, not permission to restart or reset usage.

The user stopped the chain after1189formal+3smoke updates. Do not resume it or
reuse its remaining8808updates automatically. Formal STOPPED_BOUNDED and
wrapper COMPLETED conflict is preserved in original evidence.
See [height-gate review](STANDING_HEIGHT_GATE_REVIEW_20261006.md) and the
[new CPU-only v2 spec](../configs/experiments/recovery_standing_level_v2_20261006/spec.json).
The ledger was UNAUTHORIZED during preparation; its bounded verification is now
consumed and formal remains0. R0 settling, pitch/roll and geometry costs are
unconditional; upright weight0; source retention0.30-0.40m, same coefficient.
Original source1500, physics and acceptance stay fixed. These are mechanism
repairs, not demonstrated convergence improvements. The short physical verification
above is complete; no long run was launched.

## Historical Authorization — 2026-10-06

The user has now authorized this complete detached chain: at most10000
actual PPO updates,10h cumulative wall,3smoke+9997formal,81920000samples.
Baseline300s,smoke300s,formal34740s,durability600s and60s cleanup reserve.
Ledger is AUTHORIZED and starts with zero usage. The execution uses the
experiment's independent `execution_snapshot/src/native_stand` so a concurrent
motion trainer keeps its own code/config. Snapshot CPU/fake-process checks:
81 passed. The older500-update budget proposal below is superseded.
Run: `runs/recovery_standing_balance_20261006_chain_1140`.
HAPI target: `6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1`.
One startup handshake; no conversational log polling after submission.
No other control, reward, protocol or enabled-stage changes accompany the
budget increase. R0 remains the only enabled stage.

Updated: 2026-10-06. This is the handoff and context-recovery entry, not a new
simulation/PPO authorization. Start from AGENTS -> STATUS -> this document ->
the current spec -> the actual run manifest. Check the ledger and process
identity before submission; never resume from a historical PID.

## Current Evidence

- Frozen source: `runs/recovery_stage0_stand_from1000_20261005_chain/formal/model_update_1500.pt`.
  SHA256: `c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82`.
- It passed 8/8 autonomous **2-second** hold. It has no continuous10s/100s
  standing certificate and no bottom-down Recovery certificate.
- The subsequent symmetry-only500 run survived15s but achieved0/8 holds;
  last2s mean abs vx0.416m/s exceeded0.30m/s. Height/contact/tilt remained good.
  Stronger symmetry penalty is not a demonstrated improvement.
- Source, latest, accepted and GUI-approved models are separate identities.
  Do not substitute B200, old500 or Gym47250.

## Historical v1 Recipe

[spec](../configs/experiments/recovery_standing_balance_20261006/spec.json),
[budget](../configs/experiments/recovery_standing_balance_20261006/budget.json).
This recipe was authorized and subsequently stopped by the user. Its original
spec, ledger and source snapshot are historical evidence; do not edit them.

Target: command `[0,0,0.36]`, autonomous stable standing by Recovery itself.
No handover/teacher control is used to obtain success. Physical configuration
remains the knee-stop USD copy, plane0.5/0.5/0, physics1ms, PD5ms, policy10ms,
leg40Nm/wheel5.5Nm, action leg1.6rad/wheel100rad/s and no pair projection.
25D physical-joint frame +125D oldest-to-newest history =150D actor/critic.

This is a multi-term standing adaptation, not a single-variable reward ablation:

| Term | Definition / Frozen Value |
| --- | --- |
| Height | Gaussian around0.36m, width0.04m, weight3; saturated lift weight becomes0 for this R0 recipe |
| Pitch/roll | Existing canonical squared costs, weight-4 each, scale0.12rad; full gate now0.36m |
| Linear settling | Existing full-speed Pseudo-Huber, scale0.1m/s, weight-0.6 |
| Angular settling | Existing Pseudo-Huber, scale0.35rad/s, weight-0.4 |
| Vertical motion | Squared vz/0.1, weight-0.1 |
| Level angular motion | Body x/z angular speed squared, scale0.3rad/s, weight-0.1 |
| Mirror posture | Hip sum and active-link difference, deadband0.03rad, scale0.2rad, weight-0.02 |
| Leg-length balance | Hip-anchor to main-wheel-center length difference, scale0.02m, weight-0.02 |
| Wheel differential | Left/right wheel-speed difference, scale10rad/s, weight-0.01; same authored wheel-axis signs |
| Source retention | Auxiliary actor-mean MSE, coefficient0.02, <=256 real pre-action inputs/rollout; only zero command and height0.34–0.38m |

The six new costs use a0.30–0.36m height gate except Gaussian height.
Continuous terms are multiplied by policy dt exactly once; success/failure
bonuses remain once-only. Existing effort/action/contact penalties are retained.
Retention teacher is frozen **source1500**, with the same1.6/100 action semantics;
it is not the older0.5rad STAND network. Retention adds an explicit gradient
through PyTorch's public optimizer pre-step hook; no optimizer method replacement.
It may inhibit necessary adaptation, so log its loss and selected input count.
Coefficient0.02 is a proposed recipe value, not a proven optimum.
Real pre-action observations/masks are copied in fixed-size batches; eligible
inputs are selected once at the first optimizer step, not by per-policy-step
GPU boolean indexing. At64x128x150 this cache is about4.7MiB plus masks.

## Course and Promotion

1. R0: nominal near-standing pose70%, small closure-consistent leg perturbations30%.
2. R1: enlarged near-standing leg and orientation perturbations.
3. R2: captured bottom-down low pose.
4. R3: enlarged asymmetric low-pose distribution.

Only R0 is enabled in this500-update recipe (`max_enabled_stage=0`). No motion
commands or automatic jump to low poses. The other stages are explicit future
interfaces, with offline candidates that still require runtime validation.
Before enabling each stage, validate its initialization and retain >=40% of
previously mastered tasks in a separately versioned recipe; the present recipe
does not claim that future rehearsal mix has been tested or enabled.

The curriculum manager requires two non-overlapping128-completed-episode windows,
each success rate>=90% and runtime faults0, **plus two consecutive full10s
evaluations**. Success includes low-speed/height/tilt/contact and geometry gates,
not reward alone. A short2s screen cannot promote a stage. Failed full evaluation
resets its confirmation streak. Stage changes affect subsequent resets only.

## Independent Acceptance

Training may end a successful episode after2s. Independent standing evaluation
suppresses that success-only reset and continues the **same episode**; true faults
and falls still end it. All terminal data come from pre-reset snapshots.

| Criterion | Required Value |
| --- | --- |
| Continuity | 8/8 complete10s, no reset/fault; final selected candidate100s separately |
| Height | 2–10s mean0.34–0.38m; >=90% samples in range; initial minimum reported |
| Speed | Mean abs vx/vy<=0.03m/s; yaw<=0.03rad/s |
| Drift | Whole-episode maximum planar excursion<=0.20m from pre-physics origin |
| Level | Mean abs pitch/roll<=0.05rad each; peak<=0.10rad; peak tilt<=0.12rad |
| Symmetry | Mean mirrored joint error<=0.10rad; mean leg-length difference<=0.01m |
| Support | Dual contact>2N in >=95% steady samples; mean normalized force difference<=0.30 |
| Safety | Closure<=5mm; sampled saturation<=5%; existing fault protections intact |

These symmetry/support values are proposed v1 thresholds pending physical
feasibility checks. Contact force is sensor resultant magnitude, not verified
normal load. Policy-sampled saturation is not every-PD saturation certification.
Body COM offsets may require a small persistent load difference. Never lower
thresholds in a running experiment; record infeasibility and create a new spec.
Never require raw left/right actions to be identical or lock the wheels.

## Execution and Budget Proposal

New baseline<=300s/PPO0 -> smoke3updates/300s -> formal<=500updates/7200s ->
selected candidate100s/600s. Total proposed actual PPO<=503updates,
samples<=4,120,576; formal alone4,096,000samples. No old budget is reused.
Source10s may fail the new behavioral gates; that is not a runtime fault.
Before PPO, require8 continuous source episodes, valid initialization and no
runtime fault under this exact spec. If the source cannot survive10s, diagnose
the reset/control path first.

Formal checkpoint every100;2s screening every100;full10s every250/final.
For500updates this means6 checkpoint identities (including evaluated250),
4 light screens and2 full evaluations. Light screens never certify standing.
Final100s uses only an already10s-accepted candidate; otherwise report no accepted
candidate. The durability phase must remain independently budgeted.
Ordinary full milestones retain summaries and bounded failure windows; source,
final and selected durability evaluations retain compact trajectories. Candidate
registries exclude these arrays so repeated summaries do not rewrite trajectories.

CPU-only plan (no Isaac/output/ledger mutation):

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/tools/preflight.py \
  --spec configs/experiments/recovery_standing_balance_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_balance_source_NEW
```

After explicit runtime budget approval, use the existing launcher for source_eval,
then the existing sequential Recovery train_stages for smoke/formal; supply the
confirmed HAPI target explicitly. Do not call the older Recovery chain: its
autonomous baseline validator targets the historical2s protocol.
The source-only trainer builds actor only, writes evaluation_source and a source
candidate registry; smoke preflight checks exact baseline spec/checkpoint identity.

Actual runtime CLI (verified against `--help`; **not executed**):

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  src/native_stand/command_v6/launcher.py \
  --spec configs/experiments/recovery_standing_balance_20261006/spec.json \
  --phase source_eval --output-dir runs/standing_balance_source_NEW --launch
```

After that exact baseline completes and is validated, the existing detached
smoke/formal supervisor can be submitted with the confirmed HAPI ID. Do not
submit both commands concurrently or manually turn the ledger into AUTHORIZED
without an explicit runtime budget. The `train_stages` CLI takes `--spec`,
`--output-dir`, `--hapi-session`, and optional `--tensorboard-logdir`.

## CPU Verification (2026-10-06)

Focused regression: **78 passed**. Full suite: **159 passed, 7 failed**;
the seven failures concern historical configs referencing an outdated colleague
YAML SHA. The capture CLI's actual error is `colleague_config identity differs`.
Historical configs and evidence were not rewritten to hide the drift. The new
recipe freezes the current dependency identity and records the old/new hashes.

Coverage includes the actual source1500 actor/critic and all17 Adam states,
strict150D loading, exact parameter/moment equality and effective LR3e-5;
inference-mode inputs followed by real Adam retention backward; CPU fake
environments that reset their live state after falling; complete10s scoring,
0.4m final drift, sign-alternating velocity, missing/nonfinite diagnostics;
stage caps,128-episode windows, two full confirmations and regression stops.
The new source-only plan returns `READY_NEEDS_AUTH`, CPU-valid, zero files
written. Smoke preflight accepts a physically valid10s source baseline even
when it fails the new behavioral gates, but rejects a2s or mismatched baseline.

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q \
  tests/test_recovery_standing_balance.py tests/test_recovery_autonomous.py \
  tests/test_recovery_dense_reward.py tests/test_recovery_settling.py \
  tests/test_completion.py src/native_stand/command_v6/tests/test_domain.py
```

CPU evidence does not establish that R0 can pass these thresholds in PhysX.
No new runtime baseline, smoke, formal, or100s durability result exists.

## Required Review / Do Not Drift

- First decide whether source1500 retains standing for10s; don't silently call2s10s.
- Compare matched-duration source/candidate windows and all checkpoint identities.
- Track retention cost, level angles, mirror/leg lengths, vx/yaw, dual contact,
  saturation, closure, per-pose acceptance and complete success counts.
- Rank full acceptance, survival, passed-env count, drift, level and symmetry;
  never rank early-death/low-drift or reward-only as best.
- If two consecutive full zero-command evaluations regress, stop escalation and
  preserve earlier candidates. Do not automatically add updates or change STAND.
- R0 success is standing from near-standing reset, not successful low-pose recovery.
- The next low-pose recipe must restore explicit lift progress and verify that
  the near-standing Gaussian doesn't eliminate the low-height learning signal.
- No external force, gravity compensation, hard wheel lock, hidden action gate,
  USD edits or effort-limit increase.
- Completion notifications request review and never authorize continuation.

</details>


### 2026-10-10 接管重试决策纠正

16_34正常基线首10ms倾角终止，其他21组未运行。准备器误排Motion原生reset四元数槽位，因此当前基线不合法等价，不能宣称B250新USD能力0/8。已仅CPU修复原样槽位，14项/冻结9通过，16_44新声明未授权。下一优先更正后原生正常基线，8/8才展开接管扫描；不续Recovery PPO。详见[重试复盘](RECOVERY_MOTION_HANDOFF_RETRY_REVIEW_20261010.md)。


### 2026-10-10 接管诊断完成：保留B50动态衔接

22组/176评分episode完成，合法Motion正常基线8/8，直接Swing0/8。B50受控.50秒后切Motion B250在7/8环境完成≤2秒入口＋同episode10秒保持；切换高度约.184m、vx+1.19m/s，Recovery不必先独立站稳。env4因截止前roll未满连续.20秒入口而失败，未达到全组8/8。其他19接管点倾角终止0/8。优先独立PPO0细测B50 .40/.45/.50/.55/.60秒邻近窗口和失败环境roll，不重训、不自动部署固定时刻、不放宽gate。正常基线＋5时刻建议48评分episode/900秒/256MiB，另需授权；此轮无新运行。详见[完成复盘](RECOVERY_MOTION_HANDOFF_COMPLETED_REVIEW_20261010.md)。

### 2026-10-11 17_12课程终态事实

已COMPLETED，12＋100更新/917504samples/1606.82秒。Swing各点0/32入口及完整保持；normal各点8/8入口但0/8保持、倾角终止。formal有效Actor533375，其中Swing144255低于25万目标、normal389120；槽位32/32并不代表有效样本等量。来源BC仍是完整任务排名保留对象，暂无accepted学生，不自动续训。站姿入口改善尚未迁移为落地稳定或自主起身收益；下一先复盘normal首次入口后的失稳及Swing有效覆盖不足，再冻结下一变量。

### 2026-10-12：22_43终态

已完成312更新/约60分钟。new200可走完normal10秒窗口、无倾角终止，但速度约1.55m/s及触限/平均姿态失败，主协议0/24，最终0/32；Swing0/8。新200是站立专项实验候选而非accepted，new300接触/yaw退化，不自动续训。下一需区分持续轮支撑与快速滑行，对速度、触限及镜像误差进行同窗口复盘；不能凭前缀9.68秒声称完全合格保持。
