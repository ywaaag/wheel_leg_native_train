# Codex 任务状态入口

核对日期：2026-10-13。仅保留最新已知终态和输入入口；不轮询任务，不推断进程实时存活。
操作命令见TOOL_INDEX，执行步骤见WORKFLOW，边界见AGENTS。任何表项均不授予续训权限。

## Recovery

- 0.34m站立对称专项已修复并按本轮并行指令重新提交：原23_25 run完成smoke12后把8环境工程评估错送formal24统计，FAILED/formal0；12更新、98304samples、57344有效Actor及249.1886秒均保留。新task `isolated/recovery_standing034_smoke_fix_resume_20261013/task`继承旧总账，源v7/v11/31D/物理/标准不变；新spec `2026_10_13-00_20__recovery_standing034_smoke_fix_block0001`。仅修复phase-aware统计，smoke不要求24或能力通过，formal仍严格24。GPU0/shared，30秒握手SOURCE_EVAL、worker身份OK、formal首更新未核验；新冻结源码与CPU逐模块SHA一致。CPU专项35/frozen48通过，全量943pass/8skip/22同基线。由既有owner自动续接，无个人轮询。


- 用户明确0.34m＋站姿对称、不限累计PPO专项已首次public提交：v11仅改v7高度slot0为.34m Gaussian与无封顶镜像Huber（原91.1%封顶），源normal v7 update300 SHA2a587c…a9a，31D/40D/std/物理不变、BC0、新Critic/Adam/warmup5、64normal。task isolated/recovery_standing034_symmetry_20261012/task，首块23_25 smoke12/formal300/4h/2GiB，后续完整状态续块，不自动进入Swing；5000formal后有限停滞回退。正常高度MAE≤.02/峰≤.04、镜像MAE≤.05/P95≤.10及原完整物理保持联合证书，两次24＋末32通过才专项accepted。47冻结、65targeted/34factory/26接口，全CPU942pass/8skip/22逐ID同基线fixture（configure SHA不变）。source/teacher旧文件不改，补故障全q/dq/limits。GPU0 shared/UUID映射/资源READY；一次30秒握手source_eval，worker OK，formal首更新核验=False。真实运行冻结与CPU逐SHA一致，不轮询、不重试、notifications=false。见[配方与执行](docs/RECOVERY_STANDING034_SYMMETRY_20261012.md)。


- 时间平滑A/B已终态复盘：A smoke12/formal100 COMPLETED；B smoke12/formal69，70次rollout第27interval/env53 normal组joint_outside保护触发FAILED；task ENGINEERING_STOP且无active_spec。非NaN/闭链/穿透/初始化错误，缺故障全q/限位无法确定关节；既有B50 normal膝q最近边界但不能当env53定位。两支新模型不采用，保留v10 update100：来源后缀入口24/窗口24/accepted0，A100和B50入口24/窗口0，保持前缀中位3.18→2.51/2.355s；B50共同首2秒轮RMS较A50低约15.6%，但全部先左轮合力不达标后倾角失败，无教师Swing仍0/8。实际本轮193完整更新/1581056samples/1222214有效Actor/4533.50秒；故障未完成采样另列，不记第70次PPO更新。只读CPU分析与2项回归，无新物理/PPO或重试。下一步补故障全关节取证，不继续增大平滑系数。见[终态复盘](docs/RECOVERY_TEMPORAL_AB_TERMINAL_REVIEW_20261012.md)。


- 人工Recovery工作台已改成裸源码＋分步骤：editable/src/native_stand可直接修改奖励、环境、PPO、网络和训练循环；manual.sh逐个freeze/publish/validate/authorize，不自动串联；plan/check/launch由人直接调用公共supervisor。新22_12 human_recovery仅CPU发布，预算UNAUTHORIZED、零attempt、无run。31项冻结PORTABLE＋9项项目测试通过；真实内存Actor/Critic/Adam/RNG恢复、resume无重复smoke预算及失败/SHA拒绝覆盖，公共零写plan与GUI身份计划通过。新增同配方手动resume草稿/原证书核验，复用原bundle；真实续训/仿真/GUI本轮NOT_RUN。共享src SHA未变。见[详细手册](manual_train/recovery/README.md)、TOOL_INDEX分步命令及[本轮验证](manual_train/recovery/step_verification.json)。


- 新计划第7节Actor时间平滑A/B已串行提交A：源v10 update100 SHA bc5245…be4d，保留v10 reward/1.80秒课程/物理，完整Actor/Critic/Adam/RNG恢复（实际恢复待smoke证据）；A系数0/B仅mean轮时间loss系数.01，独立pair RNG/双方梯度/不污染policy缓存。每臂smoke12/formal100/4h/2GiB，50/100评估后缀24＋normal24＋Swing8。CPU919pass/22同基线、两冻结各30pass，实际A冻结匹配；public READY/sharedGPU0，一次30秒握手SOURCE_EVAL，formal首更新未核验。owner A正常完成后核资源/身份首次提交B，故障不重试，B完先比较不自动长训。新final_task承接821历史更新；旧14_54 SOURCE_EVAL→FORMAL状态机错误已修且原FAILED保留。见[本次提交](docs/RECOVERY_ACTOR_TEMPORAL_AB_SUBMISSION_20261012.md)。

- 动态课程候选独立Swing GUI已补齐CPU接线：13_29 update100/SHA bc5245…be4d，显式single-env autonomous_preview跳过教师和课程前缀，family正确选Swing，旧训练默认不变/活动冻结源码不改。22针对性＋6冻结通过，CLI身份计划VERIFIED；未启动GUI或新增PPO，不代表学生独立起身通过。见[播放修复](docs/STUDENT_AUTONOMOUS_SWING_PREVIEW_20261012.md)，准确命令TOOL_INDEX。

- 13_29 B1.80动态课程v10已按新授权调用公共supervisor首次提交：一次600秒握手SMOKE/worker身份OK，formal首更新未核验（started=false）。源11_42 formal/update100 SHA cfb7e5…47cb（未accepted），新增入口后弱失触成本−.2分/秒，其他奖励/31D/物理保持；新Critic/Adam、warmup5、smoke12/formal≤300。新task承接509更新/4169728samples/3696930有效Actor历史用量，累计无上限、单块4h/2GiB、按原课程自动推进。旧B失败根因UNKNOWN（尾部仅前8环境），新全环境故障证据已接线、原保护不放宽、再次工程异常停止不自动重试。CPU909pass/22逐ID同基线，冻结36pass，check READY/sharedGPU0。见[本次恢复](docs/RECOVERY_CONTACT_SUFFIX_RESTART_20261012.md)。

- 11_42 B级1.80秒恢复已按本次用户同意首次提交：一次600秒握手确认SMOKE/worker身份OK，formal首更新未核验；随后用户询问时一次快照source COMPLETED/完整教师8/8/学生后缀0/24，smoke已记12更新98304samples/有效Actor43852，尚无smoke终态及formal更新证据：修复续块必须使用新子spec.execution_source_root（不再父spec PYTHONPATH）；原11_17拒绝声明/零attempt账本和旧ENGINEERING_STOP任务只读。新recovered_task继承312更新/2555904samples累计消耗，从原B180状态和A model_update_0等权重源继续，不重跑A。新recipe首次smoke12/formal≤300/4h/2GiB，GPU0共享check READY。27相关/28冻结通过，全CPU901pass/22同基线fixture；不放宽SHA，不自动工程重试。见[修复与恢复](docs/RECOVERY_COURSE_SOURCE_BINDING_REPAIR_20261012.md)。

- 09_56持续课程首块A已COMPLETED：smoke12/formal300、2555904samples、有效Actor2473984、3057.16秒（约51分钟）。新增轮平滑未改善完整站立：100主协议0/24，200/300均未完成10秒窗口，300保持前缀中位约5.225秒且倾角终止，Swing0/8；保留源00_12 update300 Actor（当前A formal/model_update_0为等权重副本）。owner按计划退出A并准备B前缀1.80秒，但B公共提交被execution_source_root与实际加载源码不匹配拒绝；B零attempt/零更新/无run，task ENGINEERING_STOP。累计授权未耗尽，工程故障按规则未重试；需修复自动子块源码绑定并验证后恢复，不可称B正在训练。原始证据task_ledger.json与A/next_block_submission.json。

- 09_56 Recovery持续课程已按本次明确不限累计PPO授权启动：source COMPLETED（学生normal0/24、Swing0/8、教师normal8/8）；smoke COMPLETED/12更新98304samples/有效Actor57344/工程证书PASSED/行为0/8；一次有界握手确认FORMAL首更新1（Critic warmup）及冻结身份匹配：task manifest/累计账本isolated/recovery_continuous_course_20261012/task，源00_12 update300 SHA2a587c…a9a未accepted。A仅加入口后轮平滑、最多600formal后进入真实B50/B250动态后缀1.80→0秒；31D/40D/物理/std保持、BC0、学生控制样本才更新Actor和Critic。每块formal≤300/全块≤4h/2GiB，新配方smoke12；同配方完整恢复Actor/Critic/Adam/RNG/课程，不重复warmup，不借旧余额。62相关/32冻结通过，全CPU895pass/22同基线fixture错误，无新增失败；public check READY/sharedGPU0 UUID e704e7d4…bd72。用户停止/工程故障禁止下一块，有限停滞处理后NEEDS_DESIGN，最终32认证＋最多300巩固后自动停；无通知。见[持续课程](docs/RECOVERY_CONTINUOUS_SWING_COURSE_20261012.md)。

- 00_12 v7站立零速Huber专项已首次提交：从22_43 update200（SHA34be922…4143/自身冻结parent）继承Actor，保留31D/40D、弱镜像、姿态与物理；仅将窄Gaussian零速tracking替换为高度门控Huber速度成本，新Critic/PPO Adam、BC0、std固定。16条既有轨迹离线重放；30专项、14来源/公共optimizer、24冻结通过，全CPU873pass/22项与867pass基线相同Motion configure.py迁移fixture错误。独立授权source40/900s、smoke12/900s、formal300/10800s，累计312updates2555904samples/12600s/2GiB。check READY、sharedGPU0 UUID e704e7d4…bd72、CUDA_VISIBLE_DEVICES=0；一次5秒握手SOURCE_EVAL/worker身份OK，formal首更新未核验。后台owner监督与结算，不轮询、重试或追加，notifications=false。见[配方与提交](docs/RECOVERY_STANDING_VELOCITY_HUBER_FROM200_20261012.md)。

- 22_43 v6已COMPLETED：smoke12/formal300、2555904samples、3596.53秒（约60分钟），formal有效Actor2416640。update200正常站姿24/24完成10秒窗口、无倾角终止，但完整主协议0/24（平均倾角、触限、vx失败；部分接触/峰值失败）；vx均值约1.55m/s，非站稳。最佳实验候选update200，最终复核0/32，Swing0/8；镜像误差未明显改善，不采用latest300、不自动续训。prefix9.68秒只含瞬时姿态/接触等检查，不含累计速度/触限，不能称9.68秒完整合格保持。见原始完成报告与isolated/recovery_motion_mirror_execution_20261011/completed_summary.json。


- 22_43 Motion反馈＋弱镜像v6已按用户明确要求从站立update50继续首次提交：源SHAd1db35…a92/自身formal冻结parent，31D/64normal/小yaw/物理不变、BC0、新Critic/PPO Adam。原站姿reward保留，新增联合零速tracking最大+4/秒、实际q镜像成本上限−.2/秒，不做teacher目标平均/动作锁定/Progress。24轨迹重放与30targeted/22冻结通过，全CPU867pass/22同基线fixture，configure SHA不变。check READY/sharedGPU0；单次握手SOURCE_EVAL/worker身份OK，formal首更新未核验。首段smoke12＋formal300/312updates2555904samples/12600秒/2GiB，25/50/100/200/300保留候选，normal保持与Swing回归分开；owner监督结算，不轮询、自动重试或无界追加。见[配方与提交](docs/RECOVERY_STANDING_MOTION_MIRROR_FROM50_20261011.md)。


- Motion原地姿态镜像教学实验已COMPLETED：5000 BC steps（auto选GPU0，17.72秒）；22_28独立PPO0 32episode/76.92秒。teacher正常标签非严格镜像（hip/active误差.141/.107rad），新投影标签和原标签独立保存。新学生实际腿更齐（.026/.064rad），但normal约.56秒倾角终止、保持0/8，Swing0/8；B2508/8。新候选不采用，专项PPO50继续保留但未accepted。Progress只完成CPU候选定义/测试，32D/41D尚未接runtime，全部已执行模型仍31D；5相关/17冻结通过，全CPU860pass/22同基线fixture。见[镜像与Progress复盘](docs/RECOVERY_STATIONARY_MIRROR_PROGRESS_20261011.md)。


- 20_46站立专项已COMPLETED：smoke12＋formal300、2555904samples、3181.27秒（约53分钟），formal有效Actor2416640。全部检查点normal入口24/24，但完整10秒0/24、均倾角终止；Swing回归0/8。专项最佳实验候选update50，accepted为空；最终normal复核0/32、Swing0/8。未自动续训，原始完成报告保留。机器摘要isolated/recovery_standing_ppo_execution_20261011/completed_summary.json。


- 20_46 v5基本站立专项PPO已按本次明确授权首次提交：同一Recovery站立蒸馏Actor（SHA06c33c…e365）、64normal训练/小yaw±.01，BC0/新Critic和Adam/31D物理不变。source40＋smoke12＋formal300，总312updates2555904samples/12600秒/2GiB；25/50/100/200/300 normal三组主选模，Swing只回归，认证scope明确normal standing only。31相关/10公共与CPU optimizer/20冻结通过，全CPU856pass/22同基线fixture errors；check READY/sharedGPU0。单次握手SOURCE_EVAL/worker身份OK，formal首更新未核验；owner监督，不轮询或自动重试/追加。见[专项提交](docs/RECOVERY_STANDING_PPO_SUBMISSION_20261011.md)。


- Recovery站立补教已完成两版CPU BC各5000步（总10000/33.59秒）与两次独立PPO0（64评分episode/234.66秒）。第一版normal0/8；第二版reset关键帧优先normal入口8/8、约1.17秒后倾角终止、10秒保持0/8；B250基线均8/8，学生Swing回归均0/8。最佳新站姿实验候选isolated/recovery_standing_reset_distilled_20261011/best_validation.pt（SHA06c33c…e365），尚非accepted，不替换原完整Recovery来源。已增加BC device auto短测速；本次小模型forward/backward CPU .636ms/GPU0共享1.188ms，因此CPU更快，非端到端或硬件部署认证。详见[补教与闭环复盘](docs/RECOVERY_STANDING_DISTILLATION_20261011.md)。


- 17_12 standing_rehearsal_v4已COMPLETED：smoke12＋formal100、917504samples、1606.82秒。formal有效Actor533375，其中Swing144255、normal389120，Swing未达25万覆盖目标。Swing25/50/100入口/完整保持均0/32；normal入口从来源1/8增至各点8/8，但保持均0/8且倾角终止，训练完整成功事件0。完整任务选模仍保留原BC学生，accepted为空，无自动续训。原始[完成报告](runs/2026_10_11-17_12__recovery_mcu_v2_standing_rehearsal_from_bc/completion_report.md)，机器摘要isolated/student_standing_rehearsal_execution_20261011/completed_summary.json。


- 17_12 standing_rehearsal_v4已按用户本次后续训练授权首次提交：同一31D Recovery BC学生，固定32Swing＋32原生normal站姿，normal reset身体XZ各±.25rad/s、小yaw±.01。Swing沿用v3 reward，normal补高度参考；BC0/物理/PPO不变，Swing主选模、normal诊断分开。36相关＋19工程边界＋19冻结通过，全CPU848pass/22同基线fixture errors。public检查READY/shared GPU0，单次握手SOURCE_EVAL/worker身份OK，formal首更新未核验。首段source48＋smoke12＋formal100，总112更新917504samples/7200s/2GiB；既有owner执行结算，不轮询、不自动重试或无限续训。见[课程与提交](docs/STUDENT_STANDING_REHEARSAL_SUBMISSION_20261011.md)。


- 16_43 resetfix局部教学接管PPO0已COMPLETED：9组72评分episode、203.3126秒、PPO/optimizer0、产物19.64MiB。B250正常基线8/8、原B50 .50s组合8/8；学生new100 .30/.40/.45/.50/.55/.60/.65秒接管均0/8入口/保持，56个均已真实切换后倾角终止。9组离线重评分/输入/历史/物理目标缓存核验一致，无新checkpoint。尚未发现可用的B250局部补教状态；下一单一重点为学生抬升后的支撑构型与动态衔接，不自动续训/补采。见[终态复盘](docs/STUDENT_LOCAL_MOTION_PROBE_COMPLETED_20261011.md)。


- 16_21局部接管PPO0尝试FAILED：正常Motion baseline reset时报Unknown evaluation family，尚无完整评分episode；5.3704秒、PPO/optimizer0、evaluate消耗1，其余8组NOT_RUN。已修复case级评估reset契约/public preflight并保留训练Swing-only语义，Kit失败退出码同步修正。31相关/20冻结通过；全CPU842pass/22项同基线configure.py fixture errors，逐项及SHA核准。16_43 resetfix新声明UNAUTHORIZED零attempt、无run，待新重试授权：9组72episode/1800s/512MiB/GPU0共享，失败不自动重试。见[复盘](docs/STUDENT_SUPPORT_LOSS_MOTION_PROBE_20261011.md)。


- 15_25 lift_rate链已COMPLETED：12+100更新/917504samples/formal有效Actor546568/链1637.50s，全部候选入口/保持0/32。支撑事件复盘显示学生峰高.418m后回落，回到.30m时两腿.314/.368m，而成功教师约.223/.265m；教师也腾空/回落，不能将失触本身作唯一原因。已接通student_motion_probe_v1：学生31D/1.5rad前缀→冻结B250原生150D/.5rad，同一物理状态切换；教师救场不计独立学生成功。16_21当时准备9组72episode/PPO0/1800s/512MiB；其后授权尝试工程FAILED，当前状态见上一条；43相关/27冻结通过，全CPU840pass/同基线22fixture errors，源码/冻结SHA无漂移。见[支撑复盘与教学探测](docs/STUDENT_SUPPORT_LOSS_MOTION_PROBE_20261011.md)。


- 15_25 lift_rate_v3已按本次明确授权首次public supervisor共享GPU0提交：204项冻结输入无漂移、资源/身份READY；来源COMPLETED学生0/32教师8/8；smoke COMPLETED/12更新98304samples/有效Actor41062/工程证书PASSED/行为0/8。单次握手确认FORMAL首更新1（Critic warmup）及冻结身份/CUDA映射。formal最多100，25/50/100评估由既有owner结算；worker不轮询、不重试追加或长训。总112更新917504samples/7200s/2GiB，notifications=false。只增入口前高度门控过大角速度成本，原BC独立开始、物理/失败终止/完整验收保持。见[提交与配方](docs/STUDENT_RECOVERY_FAILURE_ZERO_DYNAMICS_20261011.md)。


- 14_32 failure_zero已COMPLETED：12+100更新/917504samples/formal有效Actor436553/链1655.58s；仍入口0/32。轨迹复盘：new25/50/100峰高均值.326/.346/.408m，均倾角终止；new100出现抬升后回落、pitch反向和轮目标反转。输入/缓存重建≤2.38e-7，额外短历史邻近标签检索未一致改善转腿/收稳，暂保留31D。下一15_25 lift_rate_v3只增加入口前高度平滑门控的过大水平角速度成本，从原BC开始；新spec/ledger UNAUTHORIZED零attempt，无新物理/PPO/BC。34相关/21冻结通过；全量828pass/同基线22fixture errors。见[动态证据与下一配方](docs/STUDENT_RECOVERY_FAILURE_ZERO_DYNAMICS_20261011.md)。


- 学生GUI外观复用完成：legacy与学生play共享ground_visual.setup/camera_view，默认128m无碰撞网格、1m间距、1800强度dome light及原视角，每200policy步相机跟随。仅GUI外观，不改变Plane/PD/控制。21相关CPU回归与命令计划通过；未启动Isaac/GUI，实际渲染待用户观察。


- 学生GUI发布校验修复：授权登记更新spec后，students/play原先核验发布前SHA而拒绝13_35。现复用verify_publication(authorized=True)严格receipt校验，且零写preview也执行该校验；篡改spec/receipt仍拒绝。13相关回归与原BC GUI命令CPU计划通过，未启动GUI，旧spec/ledger/marker/冻结代码未改。


- 14_32失败事件消融已按本次新批准首次public supervisor共享GPU0提交：204项冻结输入无漂移，READY；来源评估COMPLETED/学生0/32/教师8/8；smoke COMPLETED/12更新98304samples/有效Actor36739/工程证书PASSED/行为0/8。单次600秒内事件握手确认formal首更新1（Critic warmup）且身份匹配；formal上限100、25/50/100评估由既有owner执行结算，worker不轮询。总112更新917504samples/7200s/2GiB、不自动重试/追加/长训，notifications=false。仅failure_once −1→0，失败终止/完整验收不变，从原BC独立开始。见[消融依据与提交](docs/STUDENT_RECOVERY_PPO100_REVIEW_20261011.md)。


- 2026-10-11 [学生工程边界收口](docs/STUDENT_ENGINEERING_BOUNDARY_20261011.md)：真实共享parent/首步覆盖训练、评估与教师适配；准备器显式来源＋case_id；异常主因/RNG保留、checkpoint/rollout/fault NPZ原子保存、声明存储统一。新14_22学生声明UNAUTHORIZED零attempt，公共frozen提交准备包完成，相关18/冻结9通过；全量783pass/22历史Motion证书SHA fixture errors，不绕过生产校验。watcher退役纯拒绝、历史selector限定legacy150D，磁盘分类/精确验证复用完成。无仿真/训练/通知/重试/进度查询，不授权已有13_35任务变化。


- 同一31D Recovery任务PPO 13_35链COMPLETED：smoke12/formal100，917504样本，formal有效Actor664895，链1770.30s；25/50/100入口/完整保持均0/32，选模保留原BC，最终复核0/32。已有轨迹复盘：BC平均.663s抬到峰高.303m后倾倒，PPO候选低位约.169m拖至2.5s期限；双侧收短保留、抬升丢失。输入重建误差≤2.38e-7，dt/事件/初始化mask无已测接线错误。失败−1在gamma.99下晚发生更划算，列为单变量假说；14_32 failure_zero候选从原BC重新开始，只将失败事件罚分−1→0，终止/验收不变。代码已消费新版本，独立spec/ledger UNAUTHORIZED零attempt，未启动新物理/PPO/BC。51相关/28冻结通过；全量820pass/同基线22fixture errors。见[离线证据、配方和预算](docs/STUDENT_RECOVERY_PPO100_REVIEW_20261011.md)。

- MCU v2已完整执行：31D/40D、Actor14630参数，Recovery BC5000/15.32s、MotionZero BC4600/13.87s；ONNX误差2.00e-6/2.98e-7。11_36一次PPO0 COMPLETED/616.33s/37.85MiB/80评分episode/423872模拟env-step：Recovery双收短32/32但入口/保持0/32，约.64–.69s tilt；MotionZero入口8/8、保持0/8，约3.1s tilt；教师组合32/32/正常8/8。80重评分一致、输入误差≤2.38e-7/cache误差0。26相关/提交前26冻结/最终27冻结；全CPU788pass/同基线22configure SHA fixture errors。硬件未验证、在线PPO0/无重试。下一聚焦Recovery .00–.25s早期腿目标拟合。[完整交付](docs/MCU_V2_STUDENT_COMPLETED_REVIEW_20261011.md)。

- 新学生独立PPO0已COMPLETED：437.48s/94.42MiB/80评分episode/PPO0与optimizer0，80项离线评分一致、所有初态有效/模型不变。Recovery四组0/32（31 tilt/1 deadline），已抬升峰高约.385m但未入口；教师四组32/32。Motion零命令学生入口8/8、完整保持0/8（tilt），教师正常8/8。提交前health显式学生metadata接口已CPU13/冻结29修复验证，未修改checkpoint。下一优先离线.7–1.2s抬升后偏离与零命令反馈，不自动PPO/重试。详见[终态复盘](docs/STUDENT_PPO0_COMPLETED_REVIEW_20261011.md)。

- 新版学生CPU蒸馏已完成：multiskill_student_v1 Actor1182/Critic1191、51本体帧＋valid、1.5rad/100rad/s，legacy150D保持。31成功示教按15/8/8episode划分；Recovery BC5000/26.17s、Motion仅零命令BC2400/12.03s（best1400），验证/测试动作拟合全部达标，不代表自主起身。学生独立runtime/公共PPO0/播放及ControlledPPO装配接口CPU已接，未运行Isaac/GUI/GPU训练/在线PPO。最终00_55学生10组80episode/1800s/512MiB声明UNAUTHORIZED零attempt；39相关/29冻结通过，全CPU778pass/22已核验旧Motion证书configure SHA fixture errors。旧receiver本轮首次核对尚无chain terminal，不停止不重提。详见[具体学生、SHA、误差和待验证](docs/STUDENT_DISTILLATION_DELIVERY_20261011.md)。

- Receiver窗口PPO0已COMPLETED：499.62s/67.99MiB/128评分episode，正常8/8；B50 .50s三个小yaw seed均8/8（24/24），.40/.45/.55/.60均0/8，成功窗口仍窄，模型更新0。128项离线重算一致、无工程故障。按本轮明确授权，22_19接管短训已public supervisor shared GPU0首次提交，单次握手SOURCE_EVAL/worker身份OK，formal首更新未核验；smoke20＋formal100≤983040samples/7200s，由既有owner结算，不轮询续训。通知enabled=false。详见[复盘与提交](docs/RECEIVER_STAGE1_WINDOW_REVIEW_SUBMISSION_20261010.md)。

- 完整组合GUI实启复查成功：2026-10-10 20:50桌面DISPLAY=:1，B50 .50s→B250，单env共享GPU0。Kit环境创建完成/播放loop真实policy2/4/6秒，高度.358→.393→.394m、reset0。先前卡在驱动RTX shader编译，SIGKILL为用户结束；重启未更改渲染/物理/模型，无训练。日志/tmp/recovery_motion_gui_recheck_20261010.log；本次窗口保留供用户观察，GUI非8/8认证。

- 接管22组PPO0全部COMPLETED：正常Motion原生初态基线8/8（strict零速8/8），直接Swing0/8；Recovery B50受控.50s→Motion B250组合7/8完整10s，其他19接管条件0/8，整组尚未accepted。env4在2s内roll未完成入口确认；365.464s/PPO0/optimizer0、176评分episode/44.17MiB。176项离线重算匹配，无续训。下一优先B50 .50s邻近窗口与env4复核，新诊断需独立授权。[完成复盘](docs/RECOVERY_MOTION_HANDOFF_COMPLETED_REVIEW_20261010.md)。

- 接管PPO0重试16_34诊断COMPLETED/主协议0/8，但正常初态quat槽位准备错误，8/8首10ms tilt终止，不能判断B250新USD能力；其他21NOT_RUN，5.419593s/PPO0/optimizer0，原始压缩轨迹已保存。更正原生reset槽位后14CPU/冻结9通过，新16_44声明UNAUTHORIZED零attempt，未再次运行。[重试复盘](docs/RECOVERY_MOTION_HANDOFF_RETRY_REVIEW_20261010.md)。

- Recovery→Motion22组PPO0接线完成并获授权执行16_28一次：正常baseline首interval后numpy.int64 JSON写盘FAILED，evaluate1/5.310s/PPO0/optimizer0，基线INCOMPLETE/其他21NOT_RUN，无能力结论。序列化/异常partial证据已CPU修复，38tests/新16_34冻结9通过，修复声明UNAUTHORIZED/public零写plan需授权；未重试。[实现与失败](docs/RECOVERY_MOTION_HANDOFF_IMPLEMENTATION_FAILURE_20261010.md)。

- 用户目标改Recovery→MotionB250零速接管。B末2s低位但vx1.85–2.96m/s，非静止；早交接需实测。B250身份/PD核验、双观测物理target/历史CPU契约与22组identity计划完成，5tests通过。runtime direct-switch/public PPO0 adapter未接完，runnable=false/无运行授权；下一完成adapter后再独立声明。[接管契约](docs/RECOVERY_MOTION_HANDOFF_CPU_CONTRACT_20261010.md)。

- Swing-only A/B均COMPLETED（各smoke10/formal100）：B初始化及25/50/100均8/8真实双腿≤.34m持续50ms，训练事件5182、有效actor777594；A事件0/有效420668。B缩腿新能力保留但峰高约.20m、无入口/通过0，deadline11.5s timeout；轮心仍未进入DrawBack目标。合计220更新/1802240/52.1分钟，无续训。下一离线对齐缩腿后的转腿/支撑/驻留reward。[最终复盘](docs/RECOVERY_SWING_ACTOR_AB_COMPLETED_REVIEW_20261010.md)。

- 修复14_23 A已COMPLETED：smoke10/formal100、1378.72秒，formal有效actor420668达到25万目标、mask计数一致，但Swing25/50/100均0入口/0通过、双侧收短里程碑0，100失败前缀.84秒且两腿仍.376m。B按已有明确授权核验READY首次提交SOURCE_EVAL/worker身份OK、formal首更新未核验；不续A不追加。[A复盘/B提交](docs/RECOVERY_SWING_ACTOR_A_REVIEW_B_SUBMISSION_20261010.md)。

- 用户失败后重新明确批准14_23修复A/B新账220updates/1802240/10800s（原A10/145.99s另账保留）。完整发布与冻结inputs SHA复核匹配；A已check READY/supervisor提交SOURCE_EVAL/worker身份OK、formal首更新未核验。B已AUTHORIZED无attempt，待A终态按本授权核验首次提交；失败不重试不追加。[提交](docs/RECOVERY_SWING_SMOKEFIX_AB_SUBMISSION_20261010.md)。

- 14_18 Swing-only A链FAILED：source/smoke正常，10更新81920样本，formal0/145.99秒；旧smoke11.5s完整episode条件阻断，非物理故障。受控mask实测35840样本/160optimizer次。公共准备器修正为真实短completed Swing episode+valid事件，不改最终gate；28tests/新14_23两臂各冻结9通过，UNAUTHORIZED。原B未提交因同一已知阻塞；失败不自动重试，待明确新运行及累计预算。[复盘](docs/RECOVERY_SWING_SMOKE_FAILURE_REPAIR_20261010.md)。

- Swing-only受控actor初始化A/B已完成并获明确运行授权：64Swing/空retained、valid-global actor loss、原reward21_58/谱系10_58。B校准.029990rad/旧锚.049990rad合格，方向解析44.3%非技能。最终两臂14_18声明，冻结各8通过；A已supervisor提交SOURCE_EVAL/worker身份OK，formal首更新未核验。B已授权未提交，A终态后核验按本授权首次提交，各smoke10/formal100，总220/1802240/10800s，不重试追加。[交付](docs/RECOVERY_SWING_CONTROLLED_ACTOR_AB_DELIVERY_20261010.md)。

- 总500预算链已COMPLETED/formal STOPPED_BOUNDED：smoke10+formal100、901120样本/2167.31秒，剩余390不继续。25/50 contact-only失败已放行；100 DrawBack改为腿触限失败（env0右hip15.7%），保留保护停止，R08/8、Swing0/8。镜像.329→.133rad，但目标距仅.393→.386m/右腿仍.376m；不接受new100、不续latest。[完整复盘](docs/RECOVERY_CONTACT_DIAGNOSTIC500_COMPLETED_REVIEW_20261009.md)。

- 用户批准总500在线更新，21_58 contact-only诊断新声明已授权提交：smoke10/formal490、4096000样本、chain≤23460s，sharedGPU0。来源10_58new25/reward/control保持，仅旧组完整hold接触单项退化不停止，其他保护/gate保留。冻结5通过/check READY，一次握手SOURCE_EVAL/worker身份OK、formal首更新未核验，不轮询。[提交](docs/RECOVERY_CONTACT_DIAGNOSTIC500_SUBMISSION_20261009.md)。

- DrawBack奖励P/S离线分解完成：乘积保留位置信号约28–35%，目标只接近数mm。新2026_10_9-21_49__recovery_drawback_contact_diagnostic_total100仅将旧组完整hold且仅continuous_contact失败的退化停训改记录；原gate仍失败/其他保护保留。来源与reward不变，Recovery233/冻结5通过；总100候选UNAUTHORIZED，无新run，待明确预算批准。[准备](docs/RECOVERY_CONTACT_DIAGNOSTIC_PREPARATION_20261009.md)。

- DrawBack镜像reward链COMPLETED/formal STOPPED_BOUNDED：smoke10+formal50，491520样本/2747.995秒，剩余40未使用。Swing各点0/8无入口；同前300ms镜像误差.3288→.2312rad，但轮心目标距离.3929→.3897m，右腿仍.37599m。旧组25/50均失触0/8，连续退化保护停止；reward接线通过，不接受新25/50、不续训。[终态复盘](docs/RECOVERY_DRAWBACK_GUIDANCE100_COMPLETED_REVIEW_20261009.md)。

- 用户批准DrawBack镜像稠密reward总100次，按smoke10+formal≤90（819200样本/chain≤9060s）独立18_39声明已授权提交；冻结5通过/check READY，一次握手SOURCE_EVAL/worker身份OK、formal首更新未核验。formal10/25/50/90完整三组评价，sharedGPU0/旧退化保护保留，不轮询、不追加。旧18_34仍未授权。[提交](docs/RECOVERY_DRAWBACK_GUIDANCE100_SUBMISSION_20261009.md)。

- DrawBack位置×镜像稠密引导接线与独立声明CPU完成：`2026_10_9-18_34__recovery_drawback_mirror_guidance_from_new25`，每秒1分上限、.22–.30m平滑退场，原奖励/std/control保持，腿中心aux关闭。Recovery238测试/冻结5通过；ledger UNAUTHORIZED/零消耗。低位腾空/驻留收益仍是实验风险，不能宣称已消除；建议单臂smoke10/formal25需明确新运行批准。[配方与边界](docs/RECOVERY_DRAWBACK_GUIDANCE_PREPARATION_20261009.md)。

- 用户选择Swing→DrawBack镜像对称奖励实验（软奖励，无强制动作投影）。CPU目标轮心位置×镜像质量原型已核算、六项检查通过；Gaussian窄对称信号塌到1e−22，改缓衰减有理式。候选尚未runtime接线/发布可运行spec，DrawBack退场/驻留/腾空/量级检查待完成；无PPO。[设计](docs/RECOVERY_DRAWBACK_MIRROR_GUIDANCE_PROPOSAL_20261009.md)。

- A/B冻结输入迁移及B25失触CPU对齐完成：B25固定早期loss下降6.63%但两hip仍偏离局部收短方向，右腿早期最短仍.37599m；旧组首失触DrawBack9.17–9.69s/R06.15–6.49s，env0发生于约8mm错位/近零roll，先有持续目标误差/轮差速与接触波动。未证明唯一原因；不续B/不自动增lambda。无仿真PPO。[诊断](docs/RECOVERY_LEG_CENTER_TRANSFER_REVIEW_20261009.md)。

- 腿中心A/B均COMPLETED：合计70更新573440样本/1967.23秒。B aux真实560次应用、wiring SHA通过；Swing各点均0/8无入口，B25峰高.230576m。A旧组10/25均8/8；B10各8/8，B25各0/8（窗口完整但连续接触失败，DrawBack95.89%/R083.48%）。不接受B、不续训；下一现有冻结模型固定输入动作迁移/失触离线对照。[完整复盘](docs/RECOVERY_LEG_CENTER_AB_COMPLETED_REVIEW_20261009.md)。

- 腿中心A已COMPLETED：smoke10/formal25，976.95秒；来源/new10/new25 Swing均0/8无入口，峰高.231973→.232035m，DrawBack/R0各8/8完整保持，无实质起身增益。按已批准两臂顺序，B核验READY后独立首次提交；一次握手SOURCE_EVAL/worker身份OK、formal首更新未核验，原预算不追加。下一B终态核实aux真实接线后同协议对照。[A复盘/B提交](docs/RECOVERY_LEG_CENTER_A_REVIEW_B_SUBMISSION_20261009.md)。

- 用户已批准腿中心A/B全部预算并登记AUTHORIZED。A `2026_10_9-15_10__recovery_leg_center_a_from_new25`已supervisor提交，一次握手SOURCE_EVAL/worker身份OK，formal首更新未核验；B已授权/preflight PASS但未提交，待A终态唤醒后核验并顺序首次提交，不需重复批准。sharedGPU0、合计70更新573440样本/整链10920秒上限，不轮询、不重试追加。[授权与握手](docs/RECOVERY_LEG_CENTER_AB_SUBMISSION_20261009.md)。

- 腿中心A/B默认关闭接线及正式声明CPU准备完成：同源10_58new25，B唯一增加lambda.1早期腿中心loss；两臂各冻结9项通过，全回归720pass/22 Motion历史configure身份ERROR。各smoke10/formal25，总70更新573440样本；账本UNAUTHORIZED、零消耗，无新仿真/PPO。下一需两臂独立明确运行批准，再经supervisor提交。[具体声明、预算与限制](docs/RECOVERY_LEG_CENTER_AB_PREPARATION_20261009.md)。

- 早期腿中心loss CPU真实两batch梯度审核完成：lambda.1 aux/已clipPPOactor norm7.83%/3.61%，cos−.152/−.376，来源参数未变、mask外0、2tests通过。固定.1进入具体A/B草案准备，各smoke10/formal25，总70updates573440samples，DRAFT_NOT_SUBMITTABLE/未授权；下一实现默认关闭hook与mask/梯度接线CPU验证，不直接运行。[审核](docs/RECOVERY_LEG_CENTER_GRADIENT_AUDIT_20261009.md)。

- 用户要求回到RL：暂停手写动态adapter扩展；已写具体下一交付草案，先CPU审核Swing前100ms腿actor局部中心辅助loss的梯度/PPO量级，非成功示教/hiddencontrol。通过才准备同源A/B各smoke10/formal25；当前loss未实现/预算未授权，无新运行。[草案](docs/RECOVERY_RL_NEXT_DELIVERY_20261009.md)。

- 动态短时序CPU准备完成：六候选120/240ms×收缩延迟0/40/80ms，quintic实体target、命令点closure/limits/envelope通过；需root动态运动，非完整DrawBack。具名PD/contact/actionorigin契约已定义，2tests通过；substepcontact生产/隔离adapter未完成，runnable=false，无物理运行授权。[准备](docs/RECOVERY_DYNAMIC_TIMING_PREPARATION_20261009.md)。

- 动态过渡CPU草案完成：9条收腿/转腿组合中6条闭链及原动作包络成立，最深双腿≈.211m但方向尚非DrawBack、固定root下穿地，须动态支撑运动。输出仅geometrydraft、runnable=false；建议诊断≤6候选×3s/900wall/128MiB尚未授权，下一准备时序与显式动作/接触测量adapter。无仿真PPO。[草案](docs/RECOVERY_DYNAMIC_TRANSITION_DRAFT_20261009.md)。

- 用户确认动态过渡方向：DrawBack向Swing扰动不能沉降停在中间态，撤回静态沉降桥接优先建议。计划8.9规定Swing摆腿支撑/抬升空间＋及时双侧收腿转腿＋进入可恢复区域，允许重叠；下一CPU显式可达性诊断方案，未授权新runtime/PPO。

- 显式腿双分量CPU候选完成但不提交：w.05局部盒覆盖约4.45e-4（std.05rad），旧DrawBack单步target峰差1.50rad，且固定localcenter远离原mean使baseactor学习responsibility极低。mixtureentropy/KL/params及deterministic接口未完成，2数学tests通过，无runtime/PPO。下一优先CPU逆向课程连续构型桥接审核，不伪造动态成功来源。[审核](docs/RECOVERY_LEG_MIXTURE_PROPOSAL_AUDIT_20261009.md)。

- 腿探索CPU候选审核完成：起步两hip收短边界离mean约14–16std；std×2/4、alllegtanh、currentqresidual均不足，×8增加裁剪且局部盒覆盖仍低。旧任务目标迁移代价明确，不发布训练spec；下一审核显式多中心policy候选的覆盖/概率/旧能力，非env偏置/隐藏控制。1数学测试通过，无仿真PPO。[审核](docs/RECOVERY_LEG_EXPLORATION_PROPOSALS_20261009.md)。

- 最新10_58new25随机腿PPO0诊断14_00COMPLETED：16384transition/NPZ16.62MiB/权重Adam不变，起步332samples两hip目标均偏离局部收短方向；受控2504sample无四通道该路径、无双侧明显收短，右最短.37542m。wheelclip15.65%/8.51%已改善，下一CPU腿探索中心/参数化与旧能力迁移候选审核，不翻符号/续训。[复盘](docs/RECOVERY_NEW25_LEG_ROLLOUT_REVIEW_20261009.md)。

- 关节符号CPU核验完成：三组active name映射、frame_q与target公式误差0；left hip USD局部轴框架180°翻转，不是右通道接反。旧GaussianB25起步416样本两hip目标均偏离已找到收短方向、2496样本无四通道同时命中该路径；非收腿必要条件、非最新new25随机证据。下一准备新候选有界PPO0腿探索读回，未运行。[审核](docs/RECOVERY_JOINT_SIGN_COVERAGE_AUDIT_20261009.md)。

- Swing闭链CPU局部扫描完成：实体收短方向左[+,+]、右[−,+]；双侧δ0→.15rad16点腿长约.376→.338m、closure≤3.28e-5m、关节limits通过、固定root理想planegap约非负。未达DrawBack/未验动力学或自碰撞，不发布reset/训练spec。当前右target方向与局部收短方向相反；下一CPU腿样本覆盖/advantage对照。[报告](docs/RECOVERY_SWING_GEOMETRY_SCAN_20261009.md)。

- 用户GUI环境setup后退出：发现tools.play1env仍训练fixed64slot，reset配额不匹配；已关闭preview.curriculum_training并选择holdout，异常在Kit关闭前打印。6CPU测试及原命令身份plan通过，未自动启动GUI，视觉复验待用户。[修复](docs/RECOVERY_GUI_RESET_FIX_20261009.md)。

- 腿执行CPU事件对齐完成：三候选各8env tilt>.18先在.05s、失触在.06s；首步三个腿通道达40Nm。右两个active q持续同向动、相对角差≈.268rad不变，wheel length≈.376m，无收短；关节target限位裁剪0，不能归因新USD挡目标。2tests通过，无runtime/PPO；下一CPU闭链原生目标方向/构型可达性扫描。[审核](docs/RECOVERY_LEG_EXECUTION_AUDIT_20261009.md)。

- 10_58 boundedmean短训COMPLETED：smoke10/formal25、286720samples、994.29秒。实际轮sampleclip降至17.08%/8.76%，两旧组10/25各8/8；Swing仍0/8无入口，peak.23136→.23197m，右腿几乎不收短。new25仅实验候选未联合通过，保留B25、不自动续训。下一CPU腿动作/实际q/力矩/几何事件对齐。[复盘](docs/RECOVERY_BOUNDED_MEAN_TRAIN_COMPLETED_REVIEW_20261009.md)。

- 用户授权轮meanbounded单变量短训10_58已提交：B25strictwarmstart，beta.3/std/腿/control固定，smoke10/formal≤25、10/25三组评估，35updates286720samples/chain≤5460s/sharedGPU0。冻结14pass，CPU694pass/22既知Motion源码证书identityerrors；一次握手SOURCE_EVAL，worker身份核验成功、formal首更新未核验。smoke新增实际两轮未全clip证据，后台通知、不轮询续训。[提交](docs/RECOVERY_BOUNDED_MEAN_TRAIN_SUBMISSION_20261009.md)。

- 仅轮meanbounded版本接口及独立PPO0已完成：10_50三组150.16秒、PPO0，DrawBack/R0各8/8完整10秒，Swing0/8。真实mean/std重放通过，预计Swing轮目标随机std4.16/3.60rad/s（非实测随机采样）；旧能力迁移固定seed未立即丢失，下一独立短训准备。冻结7通过；全回归692pass/22Motion源码证书identityerrors，未绕过旧证书。无新checkpoint/训练。[交付与跨任务影响](docs/RECOVERY_BOUNDED_MEAN_MIGRATION_REVIEW_20261009.md)。

- 动作分布CPU候选审核完成：首选准备仅轮mean=tanh(rawmean)、原Gaussian std/log_prob不变；源状态Swing有效轮探索std约4.18/3.62rad/s（原0/.082）。旧DrawBack轮目标峰差23.83/14.43rad/s，不能宣称无损，先接版本API再独立PPO0保护复验。四腿不变，入口腿动作偏差仍未解决；4tests通过，未接runtime/无新spec仿真PPO。[审核](docs/RECOVERY_ACTION_DISTRIBUTION_AUDIT_20261009.md)。

- 100更新块09_53已COMPLETED，formal STOPPED_BOUNDED：smoke10/formal100、901120samples、2133.25秒；Swing10/25/50/100均0/8、无入口，峰高最终.23051m。旧DrawBack/R0在50/100各0/8（完整10秒但失触），连续退化保护生效。new25仅诊断best，不是Swing成功；保留B25、不续latest。100次无净收益，下一CPU动作分布/初态动作迁移候选审核。[终态复盘](docs/RECOVERY_RECORD100_COMPLETED_REVIEW_20261009.md)。

- 用户批准时相配对后同配方100更新检验已提交：`2026_10_9-09_53__recovery_swing_support_record100_from_b25`，B25/β.3/std/control保持，smoke10/formal≤100，10/25/50/100完整三组检查；110更新/901120samples、链≤9060秒，sharedGPU0。CPU685/冻结14通过，一次握手SOURCE_EVAL、worker身份核验成功，formal首更新未核验。CPU时相内相关接近零，未见明显反向排序，但不保证可学习；终态自动通知、不轮询/追加。[交付](docs/RECOVERY_RECORD100_SUBMISSION_20261009.md)。

- 09_40 frozenrollout guardfix已COMPLETED、28.67秒，累计含前次失败33.99秒；采16384transition、NPZ11.19MiB、PPO0，actor/critic/Adam不变。Swing受控2496/15.23%，轮clip100%/98.60%，无双侧收短；403正bonus样本normalizedadv正仅5.96%，固定轨迹bonus扣除不改rawadv正负号。输入reward/GAE读回通过；不证明长训无效，不自动续训。[真实读回复盘](docs/RECOVERY_FROZEN_ROLLOUT_COMPLETED_REVIEW_20261009.md)。

- 冻结随机rollout诊断首run09_33 FAILED：标准Recovery profile读取None，采样前失败，PPO0/无NPZ，ledger5.33秒已结算。共享分支读取已修并补回归；CPU683/冻结5通过。独立09_40 guardfix声明UNAUTHORIZED，累计余594.67秒、2×64×128、NPZ64MiB，尚未重试。25更新不足仍是假说，无新长训授权。[修复交付](docs/RECOVERY_FROZEN_ROLLOUT_PROBE_GUARDFIX_20261009.md)。

- 纪录奖励离线可学习性审核完成：8env共32个正奖事件只在受控.01–.04秒；几何分解显示length/腿方向贡献正、body rotation贡献负，未见这些事件靠翻转刷分。首步三腿通道目标误差约1.1–1.6rad，轮raw变化大但clipped目标基本同为−100rad/s，尚不证明唯一原因。2 CPU测试通过、无新runtime/PPO；下一准备冻结B25有界随机rollout reward/value/advantage读回，需独立授权。[审核](docs/RECOVERY_RECORD_LEARNABILITY_AUDIT_20261009.md)。

- 支撑纪录短训`2026_10_9-08_59__recovery_swing_support_record_from_b25`已COMPLETED并结算：smoke10/formal25、286720样本、979.01秒；来源/new10/new25 Swing均0/8、无入口、tilt失败，峰高.231374→.231843m。DrawBack/R0各8/8完整10秒。formal25/25有真实新增reward，但轮实际sampleclip100%/98.48%，无明显双侧收腿；保留B25，不接latest/自动续训。下一CPU奖励可学习性与动作别名审核。[终态复盘](docs/RECOVERY_SUPPORT_RECORD_COMPLETED_REVIEW_20261009.md)。

- 用户授权支撑纪录单变量短训已提交：`2026_10_9-08_59__recovery_swing_support_record_from_b25`，B25严格warmstart，smoke10/formal≤25、10/25三组完整评估，共35更新/286720样本、整链≤5460秒，sharedGPU0。CPU660/冻结13通过；一次握手SOURCE_EVAL、worker身份核验成功，formal首更新未验证。终态自动通知当前负责人，不轮询/续训。[交付](docs/RECOVERY_SUPPORT_RECORD_SUBMISSION_20261009.md)。

- 2026-10-09支撑纪录reward接线及独立三组PPO0已COMPLETED：149.57秒、evaluate1/PPO0，657 CPU/10冻结测试通过；exact baseline/公式/失败和初始化0/旧组0/episodecap全部读回通过。Swing新增均值.005374但仍0/8，DrawBack/R0各8/8；无新checkpoint/训练。下一准备独立smoke10/formal≤25，仅geometryrecord变量，须新授权。[交付](docs/RECOVERY_SUPPORT_RECORD_WIRING_20261009.md)。

- 2026-10-09平滑geometryrecord候选CPU完成：真实Swing Q约.237→.253，β.3新增回报约.00473；仅刷新纪录发奖、不重复驻留/震荡，无heightgate/terminal释放。7相关测试通过；存在150D未显式观测record的critic别名风险，runtime/PPO0未接/未运行。[交付](docs/RECOVERY_SMOOTH_SUPPORT_RECORD_20261009.md)。

- 2026-10-09目标型几何reward CPU审核完成，9项测试通过。负cost有heightgate减免/早死权衡；双侧hardqualitybonus真实Swing全0且有驻留收益。候选未达设计要求，不发布可提交训练spec，无仿真/PPO。[完整核算](docs/RECOVERY_GEOMETRY_TARGET_AUDIT_20261009.md)。

- 2026-10-09几何/PBRS CPU审核完成：全部8env几何支持Swing未有效收短；strictPBRS固定起点/吸收端点折扣和恒定，末步正释放不代表进展。相关16测试通过；不将该候选接PPO，下一准备目标型几何reward的早终止/门控/量级审核，无runtime授权。[交付](docs/RECOVERY_SUPPORT_GEOMETRY_AUDIT_20261009.md)。

- 最新研究方向已改为浙江大学Recovery低位收腿/向下支点几何进展：原论坛标题/附件MD5/PDF章节已核验，约.375米Swing与.15米DrawBack起点几何差异已从真实轨迹读取。暂停继续lambda调参，先CPU势能/端点/量级设计；无新runtime/PPO。[方法与证据](docs/RECOVERY_ZJU_GEOMETRY_METHOD_20261008.md)。

- 用户授权Recovery-only清理已完成：删除37个不再使用run，文件约15.18GiB；保留本日任务/B25及祖先/pose/STAND依赖、Motion引用路径，checkpoint SHA核验。config/ledger/源码/资产/Motion未动，无进程停止。删除后可用约24.78GiB。[清理索引及失效raw说明](docs/RECOVERY_STORAGE_CLEANUP_20261008.md)。

- λ=.03块2026_10_8-20_39已COMPLETED（smoke10/formal25，1065.68秒）：10/25 Swing0/8、旧DrawBack/R0各8/8。auxnorm约.095仍轮sample clip≈100%/98.8%，未解除裁剪，不续训。
- 原链收尾报告ENOSPC（completion_error.json），未形成report_ready/通知。独立恢复报告isolated/recovery_aux003_completion_recovery_20261008/completion_report.md及notification.json，原run保持只读；当前磁盘快照剩余9.8GiB，未清理文件。

- λ=.03 v2新块`2026_10_8-20_39__recovery_swing_mean_aux003_from_b25`已提交，一次握手SOURCE_EVAL、worker身份核验通过；formal首更新未验证。B25严格warmstart，smoke10/formal≤25、full10/25，35更新/286720样本，chain≤5460秒，sharedGPU0。终态自动通知当前会话已启用，不轮询/自动续训。
- [预算、通知、验证及回执](docs/RECOVERY_MEAN_AUX003_SUBMISSION_20261008.md)。

- [mean系数CPU独立审核](docs/RECOVERY_MEAN_COEFFICIENT_AUDIT_20261008.md)完成，5个系数控制各1个CPU反事实Adamstep、仿真/在线PPO0、未导出checkpoint。建议.03作为新固定候选，smoke10/formal≤25独立预算尚未运行。旧组输出受共享参数影响，不能称无损；保留B25。

- 方案A终态已复盘：10/25/50 Swing均0/8、峰高.23147→.23270；旧DrawBack/R0全部8/8。800次aux hook有真实梯度，但aux/incoming clipped actor norm平均.316%，两轮mean/采样裁剪仍接近100%；未解除越界、无起身净收益。认证fallback保留B25。
- [终态行为与接线量级](docs/RECOVERY_WHEEL_MEAN_AUX_REVIEW_20261008.md)。下一先准备独立系数量级审核，不自动增加lambda/继续latest或叠方案B。

- 方案A `2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25`已COMPLETED，smoke10/formal50，1538.56秒；完整accepted为空，报告最佳新候选formal/update10。本次仅核对终态，未完成逐候选行为复盘。
- 用户现明确授权完成后自动通知并唤醒当前负责人会话；本块已向session7bbabd67-183d-4185-b686-1aefcd55781b补发一次，transport返回sent/0，新回执isolated/recovery_mean_aux_notification_20261008/delivery.json。旧冻结禁通知及旧run记录未改；以后新运行在其新spec冻结通知目标。通知不授权续训。

- 已提交方案A `2026_10_8-18_14__recovery_swing_wheel_mean_aux_from_b25`，一次握手SOURCE_EVAL，worker身份核验成功，formal首更新未验证。B25＋固定26/25/13，只加Swing/pre_entry轮rawmean辅助loss；smoke10/formal≤50、10/25/50完整三组评估，独立60更新/491520样本、chain≤7260秒。shared GPU0、不停止其他进程、不轮询。
- [接线、量级、预算与提交回执](docs/RECOVERY_WHEEL_MEAN_AUX_SUBMISSION_20261008.md)。外部通知仍禁用，后台保留终态报告；未自动续训，方案B关闭。

- 下一执行计划已明确：[RECOVERY_STANDING_PLAN第8.6节](docs/RECOVERY_STANDING_PLAN.md)。优先A接线＋CPU梯度量级审核，再准备未授权smoke10/formal≤50声明；10/25/50完整三组评估、旧能力保护。当前未接线、无可提交spec，本次只编辑文档；运行/通知需新明确授权。

- 当前CPU准备：[控制先验独立候选](docs/RECOVERY_CONTROL_PRIOR_PROPOSALS_20261008.md)。优先Swing前段wheel rawmean辅助loss，低位轮effort reward为独立后备；2测试通过、实际旧轨迹反事实核算完成。未接trainer/runtime、runnable=false、无新spec/仿真/PPO；参考材料出处尚需原链接核验。

- 最新真实150D联合诊断`2026_10_8-17_39__recovery_b25_input_action_reward_probe_ppo0`已COMPLETED，evaluate1/PPO0、147.458秒；Swing0/8、DrawBack/R0各8/8。输入/history接线核验未发现错误；Swing轮mean全程越界、解析clip100%/98.63%，低位水平/垂向gate0。96.7MiB新目录，无旧run修改。
- [逐维方差、动作、reward与下一判断](docs/RECOVERY_INPUT_ACTION_REWARD_PROBE_20261008.md)；未启动新训练。

- 用户要求的观测/奖励适用性诊断已写入计划第8.5节；CPU helper及后续实际runtime采集已完成，最新结果见上方联合诊断；PPO0，不代表优化梯度诊断。

- 最新Swing支撑PPO0 `2026_10_8-16_53__recovery_b25_swing_support_probe_ppo0`已COMPLETED，evaluate1/PPO0，结算171.884秒。原DrawBack/R0各8/8；四个静态中间请求均未提供新能力：首个沉降回Swing后8/8初始化、0/8起身，后三个初始化0/8。
- [动作范围、实际初态与下一决策](docs/RECOVERY_SWING_SUPPORT_PROBE_20261008.md)。未启动新PPO；保留认证B25，下一准备真实150D输入—动作—奖励联合诊断（观测/奖励与探索并列假说），动态restore仅可选，不再把沉降回原构型算桥接成功。
- 固定分组块`2026_10_8-16_08__recovery_level3_swing_fixed_slots_from_b25`已COMPLETED：smoke10/formal75，旧组连续两次完整失触退化保护停止；Swing有效transition23.58%但仍0/8，峰高约.232米。new25旧组通过，new50/75旧组失败，不接latest。

| 历史证据 | 已知结果／用途 |
|---|---|
| [B25冻结复验](docs/RECOVERY_B25_REVALIDATION_20261008.md) | DrawBack/R0六项完整10秒通过；范围内重复验证 |
| [小扰动](docs/RECOVERY_B25_SMALL_PERTURBATION_20261008.md) | PPO0八项通过；不代表任意姿态泛化 |
| [Swing桥接](docs/RECOVERY_B25_SWING_BRIDGE_20261008.md) | 原组通过，Swing起身未通过；Level3学习依据 |
| [P2 B终态](docs/RECOVERY_P2_B_COMPLETED_REVIEW_20261008.md) | B25/B50两组通过；B100未联合通过，不接latest |
| [P2 A/B历史提交](docs/RECOVERY_P2_WHEEL_STD_AB_PREPARATION_20261008.md) | 当时SOURCE_EVAL，不代表A现在存活 |
| [P1终态](docs/RECOVERY_MIN_HEIGHT_P1_COMPLETED_REVIEW_20261008.md) | COMPLETED但accepted为空；诊断排序不等于认证 |

## Motion

- 25D学生优先补测12_47已COMPLETED：48episode/867.3554秒/31.74MiB/PPO0/optimizer0，学生0/40全1.38s tilt、命令尚在2s零速入口期，非零跟踪未达到；teacher−1新增8/8，结合上次四teacher历史同协议五命令40/40（跨attempt明确区分）。输入/action/previous/q对齐0、dq≤1.43e-7、参数不变；首动作接近但随后轮目标/倾角很快偏离。旧BC .40状态→.34query有反馈状态分布缺口，不能判25D必然不足。已登记真实.34成功teacher五命令40episodepreframe/mean/physicaltarget及SHA，下一只换教学数据重蒸馏同25D、先zero闭环，不加history/PD/量化。student不采用/实机NOT_RUN，完整峰高.39966仍未认证.36限高。见[完整学生结果](docs/MOTION_FRAME25_STUDENT_COMPLETED_REVIEW_20261013.md)。


- 用户批准的25D学生测试重试12_15已STOPPED_BOUNDED/1331.9904秒/45.18MiB/PPO0/optimizer0：教师0/±.5/+1均8/8，保存正常/参数不变/输入cache对齐≤7.16e-8；teacher−1和student五组均NOT_RUN，学生未测。矩阵教师排前在共享慢速下触发下一项＋cleanup预算保护，不能称学生失败或成功。真实32评分episode/768000simenvstep，0.36实机峰高仍不通过。已完成学生优先新probe：student5先/teacher−1最后48episode/1800s/512MiB，其余teacher历史严格SHA参考；新12_47spec独立UNAUTHORIZED0attempt，7源码/7冻结/publicplanREADY_NEEDS_AUTH。未自动再提交，等用户新批准。见[终态与补测](docs/MOTION_FRAME25_RETRY_REVIEW_20261013.md)。


- 25D蒸馏学生运动PPO0首次FAILED：12_04 run/exactattempt b4288a…15a7b6c6，412.3916秒/2.85MiB/PPO0/optimizer0。首teacherzero3000interval已执行，但保存相对导入错误导致完整评分缺失，teacher8INCOMPLETE、其余72NOT_RUN（student40未运行），不能判学生能力。原失败保留；另engine_writefix绝对导入atomicwriter，真实runpy无package文件入口写回归+其他边界6/冻结6通过。新12_15独立spec/ledger UNAUTHORIZED零attempt，publicplan READY_NEEDS_AUTH、10case/80episode/1800s/512MiB准备完成，未自动重试。首次30相关/5冻结，全shared943/8skip/22同baseline；source/control/identitySHA核验。见[失败复盘与修复](docs/MOTION_FRAME25_EVALUATION_FAILED_FIX_20261013.md)。


- 用户要求尝试无历史Motion蒸馏已实际完成：新motion_frame25_distilled_v1 Actor25/128/64/32/6、13862参数，原.5rad/100rad/s/leftfirst；CPU4000BCsteps/12.21秒，best3000，新随机Actor/Adam。教师0.34站立旧05_39/u300冻结；16个正常成功.40状态episode按6/2/8拆分，在.34命令离线teacherquery标签，非真实.34轨迹证据，zeroonly。testearly腿.000765rad/轮.1854rad/s，hold腿.000263/轮.0561；4CPU通过，ONNXreference误差5.96e-8，TorchScript0。模型isolated/motion_frame25_zero_distilled_20261013，25D公共物理执行尚未接入，闭环/PPO/GPU/实机NOT_RUN，不修改当前训练或legacy电控协议。见[蒸馏与数据边界](docs/MOTION_FRAME25_DISTILLATION_20261013.md)。


- 用户确认尝试启动Motion关节/轮位对齐v5：新task `manual_train/motion/tasks/standing034_alignment_final_20261013`，spec/run `2026_10_13-11_19__motion_standing034_alignment_block0000`，源旧05_39/update300 SHA4750ee…cafb，64zero/height.34/原物理；新增worstJoint与wheelForwardHuber，分别MAE/P95gate＋zero vx.05＋保持peakheight.36。42相关/18冻结通过，全943/8skip/22逐ID同baseline，公共planPASS/READY、GPU0shared；一次30秒握手SOURCE_EVAL，formal首更新未核验；实际221模块冻结一致。source+smoke25/formal300/4h/2GiB首块结束停止复盘，不自动续块/重试，owner监督。实际实机限高与启动仍未认证。见[配方与实际提交](docs/MOTION_ALIGNMENT_SUBMISSION_20261013.md)。


- 用户要求停止并设计：standing034_symmetry_adamfix任务已STOPPED、active_spec=null，累计522PPO/formal472/smoke50、4276224samples、6801.65075秒、64episode。旧记录保留，Recovery未停止。新设计从旧05_39/update300零速基线恢复，保留Motion奖励，拆hip/active日志＋新增最差关节Huber与轮前后差Huber；关节MAE.05/P95.10、轮差MAE2cm/P953cm、zero vx.05及保持峰高≤.36联合新gate。5CPU原型测试与4完整窗口离线重放完成，新runtime/物理训练NOT_RUN，不伪称已发布可运行spec。见[设计与停止结算](docs/MOTION_ALIGNMENT_NEXT_DESIGN_20261013.md)。


- 电控交接协议包已创建于根deployment_protocol：Motion legacy150D/0.34m命令，逐维输入、历史实际时序、实体输出/PD、CAD坐标与joint极性、USD限位读回、硬件MotorID/IMU/encoder标定模板。模型暂不选择、无ONNX/真机执行；20组NumPy与实际Motion contract对照全部误差0，reset与重复step验证通过。0.36m实机峰高仍未认证，仿真初始化.40不当作实机启动方案。入口[协议说明](deployment_protocol/README.md)。


- 用户明确修复并继续后，Motion镜像专项v4已一次public提交：原08_29 source_eval完成8episode/253.6715秒，smoke新Adam转换KeyError(exp_avg)、PPO0，task ENGINEERING_STOP。修复转换用state.get，不制造空moment，已恢复moment保留原转换、残缺状态提前拒绝；奖励/gate/源/物理不变，旧FAILED不改。新task `manual_train/motion/tasks/standing034_symmetry_adamfix_20261013`，新run `2026_10_13-09_07__motion_standing034_symmetry_block0000`。54相关/18冻结/旧v2课程16通过；943shared/8skip/22逐ID同基线。GPU0/shared/UUID映射READY，单次30秒握手SOURCE_EVAL，formal首更新未确认，实际220冻结SHA一致；owner监督，不轮询/重试，旧历史消耗另列。见[修复与提交](docs/MOTION_SYMMETRY_ADAM_FIX_SUBMISSION_20261013.md)。


- 用户同意优先对称且不强求初始化0.34m：旧Motion任务正常STOPPED，1488更新/formal1363/12189696samples/27695.02秒，历史保留。新零命令站立＋实际关节mirror专项已public提交：64zero，高度命令.34、合法root.40初始化不变；源旧block3 update300 SHA4750ee…cafb（7个零速8/8完整候选中mirror误差最小，仍约.31rad）。新增无封顶Huber实际q镜像成本，联合gate MAE≤.05/P95≤.10，原物理不变；新Critic/Adam/warmup5，续块完整状态恢复。task `manual_train/motion/tasks/standing034_symmetry_selected_20261013`，首块`2026_10_13-08_29__motion_standing034_symmetry_block0000`；GPU0/shared，单次30秒握手SOURCE_EVAL，formal首更新未核验。81相关/9冻结通过，943全CPU/8skip/22逐ID同基线，实际220冻结SHA一致；owner监督续块，不轮询/通知/重试。仅零速专项，±2及Swing不宣称通过。见[具体配方、来源与验证](docs/MOTION_STANDING_SYMMETRY_SUBMISSION_20261013.md)。


- 用户授权旧Motion并行不限累计训练0.34m站立与前后±2m/s，已公开提交：B250 SHA5d3389…b89e，保持legacy150D、.5rad/100rad/s、原USD/PD/限矩；26zero/19forward/19backward固定槽位，height command=.34，联合0/+2/-2各8环境、30秒流程中的10秒保持。任务 `manual_train/motion/tasks/standing034_pm2_fixed_20261013` 总额度null，子块smoke25/formal300/4h/2GiB；normal续训恢复Actor/Critic/Adam/std/Torch+CUDA/Python+NumPy RNG，owner公开提交，不使用watcher。新spec `2026_10_13-00_16__motion_standing034_pm2_block0000`，GPU0共享，30秒握手SOURCE_EVAL、worker身份OK、formal首更新未核验。v1首次启动STOP局部变量错误FAILED，PPO0/6.9366秒，原run与消耗保留；v2真正main异常收尾回归通过。专项99/frozenPORTABLE16，通过实际冻结SHA核验；共享全量22证书fixture错误逐ID同基线、不放宽SHA。Motion仍用原USD，与Recovery限位USD的联合部署未认证。[源码导航](manual_train/motion/README.md)，[本轮证据](docs/MOTION_STANDING034_PM2_SUBMISSION_20261013.md)。


- 2026-10-09 [GUI/分布/证据接口修复](docs/GUI_MODE_DISTRIBUTION_STORAGE_FIX_20261009.md)：共享training/evaluation/preview模式及两任务GPU/renderer接线，完整CPU模型身份与holdout预检，Recovery分布隔离，可选NPZ＋摘要JSON和目录一致性检查完成。专项85通过；全量680 passed, 2 warnings, 22 errors in 29.14s。22项历史Motion证书fixture因当前runtime/configure SHA变化拒绝，原证书未绕过/重写；10_14声明当前须重新审核相关变更，不能沿用当时READY提交。Motion共享learning两文件与旧冻结SHA一致。真实GUI/Kit关闭未验证，无仿真/训练/进程控制。


- 2026-10-09[update50±2 PPO0补评与报告修复](docs/MOTION_POSTURE_ENDPOINT_COMPLETION_20261009.md)已完成：两项8/8连续30秒，MAE+.29046/-.08197、接触1，无runtime；PPO0/耗426.31秒。原累计余585.51秒（9.76分钟），训练更新额度用完。update50九命令诊断cost下降20.13%，但update25失败、两次完整重复通过未成立，补测跨执行版本不授严格合并认证。独立corrected report已生成，旧故障/registry/ledger不改，未重发通知、不续训。

- 2026-10-09[B250姿态formal复盘](docs/MOTION_POSTURE_FORMAL_REVIEW_20261009.md)：formal50/409600，STOPPED_BOUNDED。update25九命令中+2 MAE.3413导致0/8，其余通过；update50七命令8/8但+2预算中断、-2未评，不能接受。共同七命令姿态成本改善33.3%，局部腿长差/roll改善，剪刀腿未消除。累计余1011.83秒，更新额度用完。收尾报告因当前共享config.py SHA漂移失败，notify未执行；未续训或重发通知。

- 2026-10-09用户批准[B250姿态formal恢复](docs/MOTION_POSTURE_FORMAL_RECOVERY_SUBMISSION_20261009.md)，已提交GPU1独占。恢复spec `2026_10_9-10_14__motion_posture_engineering_recovery`，授权后SHA `e2fec82cefc4dbe8f288af87cdfeb8e5b8c312344fed2caadf5c3ab9ce043e6c`。一次握手RUNNING/identity_verified、formal实际首更新1已完成；trainer1017417/monitor1017415、exact attempt c80ded162b1444c5a2656aef831fe7a7。source/smoke不重跑，formal最多50、25/50验收、墙钟4013.33秒，累计预算不重置。未认证姿态改善；后台结算/通知，不轮询或自动再试。

- 2026-10-09 [Motion工程恢复认证](docs/MOTION_ENGINEERING_RECOVERY_CERTIFICATION_20261009.md)已完成：新声明`2026_10_9-10_14__motion_posture_engineering_recovery`为UNAUTHORIZED；原失败smoke＋独立light PPO0＋原九命令source＋逐文件审核形成READY工程证书。公共supervisor零写plan为READY_NEEDS_AUTH、cpu_valid=true，唯一阻断为未授权；不是缺少新PPO0。累计剩4965.170556秒，smoke新额度0/formal最多50；不改旧FAILED，不启动训练。专项76/全量676 passed。


- 2026-10-09独立[PPO0轻评估验证](docs/MOTION_POSTURE_PPO0_LIGHT_VERIFICATION_20261009.md)COMPLETED：run `2026_10_9-09_11__motion_posture_smoke_light_ppo0`，原smoke checkpoint的0/±.5各8env连续4秒，姿态短窗口151valid样本，None异常未复现。online0，耗88.41秒；累计余4965.17秒/82.75分钟，smoke1已用、formal0。能力gate NOT_RUN，不改旧FAILED证书；formal仍需合法工程恢复证据及明确授权。CPU663 passed。

- 2026-10-09姿态轻评估None窗口已修：[修复与恢复资格](docs/MOTION_POSTURE_LIGHT_WINDOW_FIX_20261009.md)。共享窗口解析、closed时间轴完整性和runtime接线CPU验证通过，全量662 passed。旧smoke证书仍FAILED、源码变化下source复用CONFLICTING；离线actor确有更新不冒充证书。没有仿真/重试或追加smoke，下一步先独立PPO0工程验证并建立合法证据迁移，formal仍从B250。

- 事件3bb21a4b40e4f8cbdeeca999：storage姿态重试FAILED，[轻评估故障复盘](docs/MOTION_POSTURE_LIGHT_WINDOW_FAILURE_20261009.md)。来源九命令完整30秒各8/8；smoke真实更新1次/8192样本并保存checkpoint，姿态轻评估非零command引用None窗口崩溃，formal未运行，无候选。累计5746.42秒，原预算余5053.58秒；smoke1额度已消耗，不能自动补跑或续训。本次无磁盘错误，不等于姿态优化失败。

- 2026-10-09用户明确批准姿态storage重试，已通过supervisor detached提交GPU1独占。配置`2026_10_8-22_51__motion_b250_posture_storage_retry`授权后spec SHA `1951dc1e27a3c11498bdd0542d338df56308564c345784b41906c0f1862b2d0d`；worker931944，chain attempt `c18f058434b94ec39efb6e36aa828796`。一次5秒握手submission_verified=true、SOURCE_EVAL、formal_first_update_verified=false；不是正式PPO或能力通过。累计余6993.33秒、smoke1/formal50，source重新评估。终态通知本会话`191bacc3-e5c7-4b8f-ae3d-5677eada837b`；不升速、不自动再试、不轮询。

- 2026-10-09存储修复后姿态实验准备完成：[准备核验](docs/MOTION_POSTURE_STORAGE_PREPARATION_20261009.md)。新配置`2026_10_8-22_51__motion_b250_posture_storage_retry`仍UNAUTHORIZED，B250/原配方不变；累计剩6993.33秒，smoke1/formal最多50，25/50验收。空间门槛PASS；九命令旧source完整但代码/元数据身份CONFLICTING，不绕过复用、不使用半写-2。尚未创建run、reserve或启动仿真/PPO。

- 2026-10-08用户授权退役历史Motion run清理：删除50个旧目录约4.025GiB，保留B250完整来源链和近期姿态/sim2sim记录；配置ledger未动，Recovery未动。详见[清理索引](docs/MOTION_STORAGE_CLEANUP_20261008.md)。旧文档指向已删除run的链接仅是历史索引，原始证据已不可用，不得冒充可复核结果。

- 事件987abea1ae3b69622d957f9f：姿态metrics重试链FAILED，
  [磁盘故障复盘](docs/MOTION_POSTURE_DISK_FAILURE_20261008.md)。source最后-2 JSON写入ENOSPC；
  已存8项各8/8，-2只有部分tmp，完整9命令不成立。smoke/formal未运行、PPO0；ledger已结算。
  一次磁盘快照根分区100%/仅2.2MiB，inode正常；两次累计墙钟3806.67s，原额度剩6993.33s。
  未删除/迁移证据、未自动重跑，下一步先解决空间与产物预算。下方启动记录是历史快照。

- 2026-10-08姿态metrics工程错误已修，用户批准的新独立重试已提交GPU1：
  [交付](docs/MOTION_POSTURE_METRICS_RETRY_20261008.md)，
  [spec](configs/experiments/2026_10_8-20_29__motion_b250_posture_metrics_retry/spec.json)。
  原配方不调参，累计旧墙钟1927.08s扣除，新链8872.92s上限，PPO累计仍51。
  CPU635/frozen7通过，plan PASS/health OK；一次握手worker462853，SOURCE_EVAL，formal首更新未验证。
  新run同名；后台结算/通知，交互不轮询、不再自动重试，旧失败证据保留。

- 事件a800778e8d785c11dbc4dd24：姿态v2链FAILED，
  [复盘](docs/MOTION_POSTURE_FAILED_REVIEW_20261008.md)。source9命令各8/8，
  Isaac真实zero错位4.95cm、+2腿长差14.20cm/roll.307rad、-2差8.12cm/roll.168rad。
  smoke首rollout因新增posture_balance未接入RolloutMetrics字段声明失败，PPO0，formal未运行。
  已结算无RUNNING，整链1927.08秒，无候选；属新增统计接线错误，不是姿态训练失败证据。
  未自动修复/重试/续训；下方启动状态是历史握手。

- 2026-10-08用户授权B250姿态优化已提交GPU1独占，
  [配方与交接](docs/MOTION_POSTURE_BALANCE_20261008.md)，
  [spec](configs/experiments/2026_10_8-18_03__motion_b250_posture_balance_v2/spec.json)。
  新增有界轮心/腿长差/roll成本，保留B250原0/±.5/±1训练分布，保护0至±2九命令。
  smoke1/formal50、51updates/417792samples，整链10800s上限；25/50运动+姿态重复确认。
  CPU630 passed、冻结6tests/严格初始化审核通过，plan PASS/health OK。
  一次握手worker332739，SOURCE_EVAL，submission_verified=true，formal首更新尚未验证。
  后台owner自动完成评估/保护/结算/通知，交互不轮询。18_02首版未授权不执行。

- 事件8cb50f802e7871b821859052已只读复盘：[rehearsal终态](docs/MOTION_REHEARSAL_COMPLETED_REVIEW_20261008.md)。
  链COMPLETED，formal50达预算，smoke1合计51/417792samples，约7200.96秒，账本已结算。
  accepted=null；new50 +2恢复8/8，-2及±2.5仍0/8，不能升±3或三seed认证。
  actual类别样本zero28.98/old55.88/new15.14%，新正负10.97/4.17%，固定配额未实现。
  比例调整有部分改善但没有完整能力保留；B250仍为已验证来源，不从new50续训。
  未自动启动或准备下一实验；下方启动/未授权段落为当时快照。

- 2026-10-08MuJoCo首轮适配错误已确认并修正：native actor用CAD重力[0,-1,0]，
  不是Fudan canonical[0,0,-1]。[配对复盘](docs/MOTION_SIM2SIM_FRAME_PARITY_20261008.md)，
  验证区[sim2sim](sim2sim/README.md)。8env真实Isaac首动作最大差1.49e-7，38joint轴对应。
  corrected run `sim2sim/2026_10_8-17_10__motion_b250_corrected_mujoco/`：11命令各30秒，
  330000physics/33000policy samples、PPO0，双轮接触1.0；zero持续后滑约-.208m/s，
  -1.5/-2/-2.5误差超门槛，roll/轮心错位已量化，非完整sim2sim认证。
  上轮0.18秒失败属错误观测输入，不判B250能力失败；旧证据保留。GPU1被占用，不抢占，无新Isaac。

- 2026-10-08用户授权MuJoCo迁移诊断已完成，未通过：
  [复盘](docs/MOTION_MUJOCO_SIM2SIM_20261008.md)，run为
  `runs/2026_10_8-16_58__motion_b250_mujoco/`。B250直接实体关节/150D/原PD与40/5.5Nm，
  只读参考MJCF；零命令准备0.18秒JOINT_SAFETY终止，11目标重复同一起点失败，保持/停车UNKNOWN。
  轮饱和各1.0、tilt.522rad、闭链最大1.26mm，实际输出与PD请求一致；
  有摩擦/阻尼/碰撞/solver差异，运行观测parity未认证，不判native能力失效。
  MuJoCo CPU1980physics steps/198policy samples，PPO0；未触及后台训练。

- 2026-10-08用户授权的旧端点rehearsal已提交GPU1独占：
  `runs/2026_10_8-14_56__motion_old_endpoint_rehearsal/`。独立授权登记51总更新
  （smoke1/formal50，417792samples），source/smoke/formal墙钟2500/600/9000秒。
  43项针对性CPU通过，授权后plan PASS、health OK零写；仅一次5秒握手，
  worker145263、chain attempt4f1cfbdbbfd3438fabebbdd107f8595f，argv/start/spec/output/GPU/session核验通过。
  当时SOURCE_EVAL，submission_verified=true、formal_first_update_verified=false；
  不能称正式PPO已开始或能力通过。后台owner负责25/50评估、旧能力保护、结算与当前会话通知；
  不升±3/yaw、不自动重试、不轮询。下方UNAUTHORIZED是准备时快照，实际授权/用量看新ledger。

- 2026-10-08已完成B250/formal25/50同协议逐环境复盘及唯一rehearsal准备，
  [报告](docs/MOTION_REHEARSAL_PREPARATION_20261008.md)。±2增益1.083→1.200→1.288；
  formal50 -2.5为joint_safety早终止，不是完整保持结果。用户roll/约5cm轮心错位
  已记录，现有raw缺对应几何字段，未量化。新[spec](configs/experiments/2026_10_8-14_56__motion_old_endpoint_rehearsal/spec.json)
  从B250恢复，只改reset采样权重，名义64槽16/旧各4/新各8，保持随机采样；
  smoke1/formal50，ledger UNAUTHORIZED/used0，preflight仅缺运行授权，run未创建。
  CPU559 passed，未仿真/训练/通知；不升±3、不从失败候选续训。

- 2026-10-08键盘预览兼容已补齐：play_motion_keyboard.py转调当前共享tools.play，
  B250身份CPU计划无警告、零模拟/零文件/零PPO。默认GPU1、±2m/s、yaw关闭；
  按键/回零/最新history命令同步3项通过，全量CPU546 passed（23.07s）、五文件AST及diff检查通过。
  只完成CPU核验，未启动GUI/训练、未查资源；实际桌面键盘和GPU运动尚待运行验证，命令见TOOL_INDEX。

- 来源身份：`runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`，SHA `5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。
- 最新短链：`runs/2026_10_7-20_29__motion_b250_2p5_short/`。
- [Spec](configs/experiments/2026_10_7-20_29__motion_b250_2p5_short/spec.json)；budget.json在同目录。
- [链终态](runs/2026_10_7-20_29__motion_b250_2p5_short/chain_terminal_report.json)：链COMPLETED；formal STOPPED_BOUNDED/50更新，旧能力连续失败停止；smoke1，总新增51。accepted=null。
- [来源与提交记录](docs/2026_10_7-20_29__motion_b250_2p5_short_REPORT.md)是历史启动记录；最新结论用上述terminal及formal原始评估。
- [来源PPO0复核](runs/2026_10_7-20_18__motion_b250_endpoint2p5/baseline/baseline_review.json)：±2.5双向超速，MAE约.402/.343，未通过.3门槛。
- 本次通知接收不代表负责人接管；复盘或新尝试按实际任务归属和用户授权进行。

## 工程证据

- 2026-10-09工程恢复接口：执行依赖／全快照双身份、行为／预算／storage分离，独立checkpoint actor更新证明、显式batch group继续策略、Motion诊断准备和受限失败＋补测计划当时已补齐；当前完整认证见Motion最新入口。680项全量阶段、最终14项专项通过，原FAILED/账本不改。
- 产物artifacts/engineering_recovery_interfaces_20261009/；未执行物理、未提交恢复链。真实失败＋补测READY证书尚未核验，轻诊断不能替代完整能力或smoke。


- 2026-10-09发布/Recovery字段/历史存储工程：单臂＋多臂完整性公共校验，support-record准备器只传request，reward字段集中、smoke轻量reset/baseline/违规计数接通。真实B25零写准备通过；668项全量阶段、最终39项专项通过，不模拟／不查后台。
- 旧已结束Swing链只读盘点derived约6.64GiB，三个主要报告各约974MiB；仅输出压缩审核计划，未删除／改写旧文件。证据artifacts/publication_storage_recovery_20261009/。


- 存储工程：preflight/reserve容量门槛、递归摘要去轨迹、严格来源复用证书已接入；未删旧产物／运行仿真。专项37项通过。全量637通过、3项因历史模型/spec已缺失失败，非新增逻辑失败；证据artifacts/storage_evidence_engineering_20261008/。


- sim2sim工程升级：CAD/COM显式contract、具名轴trace loader、通用静态parity、可选paired_state记录及独立诊断结算schema已接入。旧sim2sim/audit_native_parity.py已移除，仅保留共享tools.audit_native_parity入口；旧运行和更正证据不改。
- 624项全量阶段、最终11项专项、独立冻结4项/schema/零写plan通过；已有B250首动作差1.49e-7复核。新配对样本0、physics step0，动力学严格parity与GUI仍未知，产物`artifacts/sim2sim_semantic_cpu_20261008/`。


- Recovery采样/事件工程补齐：公共config/preflight固定槽位总数校验与env→family映射；槽位、累计初始化（可能含评估reset）、有效transition分开。
- 共享registry事件审计与薄脚本包装已运行在已结束Swing链，实际占比1.567%复算；未读取活动任务进度。604项CPU、最终独立冻结11项/schema/零写plan通过，产物`artifacts/recovery_event_interfaces_20261008/`。
- 未启动仿真/PPO；历史未保存阶段时钟的训练均值仍不能拆成精确初始化/恢复/保持时间。


- Motion窗口/身份/比较工程已补齐：通用compare_motion、冻结submission_summary、共享GUI设备映射和显式采样语义。历史formal50 −2.5早终止识别为诊断窗口，未改旧结论。
- 本轮最终专项30项通过；全量阶段592项通过，最终回归见本地`artifacts/motion_engineering_interfaces_20261008/`。未访问后台进度、未模拟/PPO；实际GUI渲染仍未认证。


- Recovery课程准备已参数化；Swing为薄包装，姿态库加入同事务发布，标记最后绑定四文件SHA。工具注册/旧准备器分类/GUI身份计划已同步。
- 本轮570项全量CPU回归通过（26.64s），最终26项专项通过；真实B25零写计划核验actor/critic/std不变、17个Adam状态及RNG字段。未启动仿真、未查询训练进度。
- 采样/协议解耦已完成：新声明为sampling.family_weights＋assessment评估/保护组＋纯评分rising_task；runtime reset和retention统一接公共解析器。旧字段仅在集中只读适配层保留，不改历史spec；混用拒绝。
- 本轮584项CPU全量通过（29.37s）；真实B25零写计划通过，新旧评分一致、40/40/20质量一致、初始化不变。证据`artifacts/recovery_sampling_decoupling_20261008/`；尚未新物理验证，未查活动进度。


- 多臂工程优化：受限子目录publish＋完整标记、统一授权登记、纯域std换算、冻结CPU初始化审核、版本trace与结束后compare_arms已补齐；命令只维护TOOL_INDEX。
- 本轮CPU541项阶段回归与真实checkpoint初始化审核；产物`artifacts/multiarm_engineering_20261008/`。未读取P2训练进度、未授权/重提活动臂、未模拟/PPO或通知。

- [公共流程补齐](docs/ENGINEERING_WORKFLOW_COMPLETION_20261008.md)：528项CPU阶段验证、冻结CPU25项、raw审计；不是GPU行为认证。
- [通知/证据修复](docs/NOTIFICATION_EVIDENCE_FIX_20261008.md)：路由、评分边界、raw loader、完整窗口语义。
- [整合前状态与入口原文](docs/history/ENTRY_DOCS_BEFORE_CONSOLIDATION_20261008.md)归档保留；无需在新会话中默认加载。
