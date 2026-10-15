# Codex 工作流

本文件只维护步骤和判断分支；工具参数在TOOL_INDEX，边界在AGENTS，模块职责在ARCHITECTURE。
先从STATUS定位用户请求的任务，不把Motion和Recovery的证据/授权混用。

## 1. 接手与范围

读AGENTS、README导航、STATUS对应任务，然后读spec/ledger/manifest/冻结代码/terminal/raw evaluation。
区分：当前已修复的历史问题、仍在执行的bug、实验配方选择、证据缺口。
历史行为由run快照解释；新CPU/文档任务不授权仿真或通知。不凭旧PID/旧“RUNNING”判断活跃。
用户要求状态时可一次只读检查；状态不明先查已有receipt/exact attempt，不重复提交。

## 2. 准备或修复

- 工程修复：改共享下一次执行代码，保留活动冻结副本，补真实调用边界/生命周期CPU测试。
- 新实验：先复用经验指南，选择一个问题，冻结source/model/asset/protocol身份和允许改动。
- 采用公共准备器显式输入parent/checkpoint/request/current session/GPU；默认零写计划。
- --write仅发布独立未授权spec/budget/来源与差异清单；未知输入拒绝，失败不使用半成品。
- Recovery课程以独立request声明采样family/权重与评估点；编译sampling、assessment、纯评分rising_task三份契约。准备器审核父库旧姿态、完整初始化及删除的旧干预。姿态库同事务发布，完整标记最后写入；授权登记前核验全部文件SHA。
- 旧ledger消耗只读引用；授权额度与实际消耗分别记录，不因新spec清零跨实验预算。
- 同轨迹重评分写新报告，旧gate/spec/结论保持原身份，不追溯“历史已通过”。

新实验名由experiment_naming生成Asia/Shanghai `YYYY_M_D-HH_MM__purpose`；
config/run/spec.experiment/artifacts.run_name一致，phase目录用source_eval/smoke/formal/A/B。
重名追加suffix并独占创建；旧路径保持不动。名称不授权运行。

## 3. 验证与授权登记

执行必要CPU回归和真实入口零写plan；新字段既测schema，也测source/smoke/milestone/final参数构建。
审核requested→effective→实际源码；协议/调度/storage分别解析；外部PPO实现SHA也记录。
根据用户本轮明确范围登记新独立ledger，包含更新、样本、墙钟和清理余量；未授权准备保持未授权。
授权不完整时报告具体缺项，不从历史文件自行推导许可。
迁移旧Recovery声明时生成新声明和差异清单；旧sampling字段由只读适配层解析，不改历史spec。核验新旧有效概率、验收协议及保护范围一致，再提交任何新物理验证。
新多臂声明先核验publication_complete文件，再用register_authorization一次计划/明确登记；
绑定每臂spec/ledger SHA、总更新和总phase墙钟，保留批准范围与receipt。登记工具不提交。
获运行授权后做一次check-submission：当前负责人session、物理GPU/UUID、资源政策、fresh output、
exact账本和前置证书。配置PASS≠提交就绪；资源快照只证明检查时刻，不保证未来可用。

### 受限 Motion 工程恢复

先分开审核优化接线、故障路径补测、原来源能力和新模型能力。工程 light 完整不等于完整运动验收。
已完成一次更新后因已知 None 窗口异常失败，可用同 checkpoint 的独立 PPO0 轻补测与逐文件工程审核建立 v1 恢复证书。
各检查保留独立诊断结果；相关变更必须给出旧/新 SHA 和理由，行为变化不进入此恢复类型。
发布新 UNAUTHORIZED 声明，历史记录不改；source/smoke额度为0，累计预算统一计算，formal从原来源完整状态开始。
CPU真实入口 plan 核验证书；有后续明确授权时，公共 supervisor 只提交一次 formal，reserve 复核并锁定一次性证据。
新候选是否有完整能力仍由正式评估决定，不把补测结果迁移为候选 accepted。

## 4. 一次提交与握手

公开supervisor detached提交一次，后台owner依次管来源、smoke、formal或独立PPO0评估。
来源物理/身份故障阻断后续；新能力尚未学会属于学习结果，按冻结spec判断，不临时提高gate。
正式前wiring certificate必须匹配spec/source与实际事件；smoke时长足以覆盖声明事件。
握手反馈submitted、当前阶段、worker/attempt/output、actual首更新证据和GPU映射。
SOURCE_EVAL/SMOKE不是formal started，UNKNOWN时started=false。worker不循环等到formal。

长训一次有限握手后结束交互；后台owner自主采样、评估、晋级、保存、保护、结算。
worker不得反复tail/progress/ps/GPU、sleep/wait，也不移交新watcher/子agent轮询。
明确有界前台CPU或物理诊断可等待自身退出；不扩大其预算或自动重试。

## 5. 终态与复盘

owner在清理前写child terminal；等待child真正退出，核对exit与terminal，再精确结算ledger。
清理错误、预算结束、普通能力未达标、物理故障分别记录；exit0/COMPLETED不等于accepted。
逐项结果及时原子保存，预算不足保留已完成证据，缺项MISSING而不是补通过。
一次读取manifest/terminal/monitor/ledger和raw结果，核验实际更新/样本/墙钟及证据完整性。
phase limit、reservation、actual completed和settled分别呈现；冲突定位，不把used当唯一训练计数。

候选选择完整同checkpoint命令集，source/latest/best_new/best_overall/accepted/fallback分开。
同源A/B结束后一次compare_arms，分别报告source、实际初始化和后续checkpoint std；
初始化倍率不是全程探索倍率，不新增等待比较的watcher。
同时报告方向、MAE、漂移、姿态、接触、闭链/执行约束和最差环境，不能拼各模型最好点。
完整保持窗口但证书失败是hold_certificate_failed，不混作未收满窗口；缺数据保持未知。

owner生成hash匹配report_ready，按冻结负责人目标at-most-once通知。evaluation-only monitor当前不自动通知。
路由冲突/未知投递不重发、不重启训练；通知事件仅提示复盘，不授权接管或续训。
历史报告只读时不调用会重写报告的completion默认模式；人工发送/ack各需明确权限和归属。

## 6. 工程与文档交付

列明本轮文件、具体修复、实际命令/结果、缺失物理证据和剩余限制。
CPU测试数量不证明行为改善；离线optimizer/动作扫描不冒充物理能力。
工具用途只更新TOOL_INDEX，流程只更新本页，架构只更新ARCHITECTURE，任务事实只更新STATUS。
日期实验报告记录证据和结果，不另造必读导航；保留来源SHA、raw路径和历史协议。

按用户要求才commit/push。明确路径stage，检查staged diff，保留无关dirty changes；不git add .。
源码/测试/声明/文档可版本化，runs/isolated/artifacts大数据、资产/checkpoint、mutable ledger/receipt
保持本地；不force-add。Git checkout不回滚预算，也不能凭当前源码虚构旧run实现。

Motion复盘优先显式提供模型与evaluation身份，先核对同command评分组件、完整窗口及完整episode，
再计算逐环境差值与响应gain；提前终止/缺测不拼认证。提交后可从已有授权receipt和一次握手
生成交付摘要；保留formal首更新验证状态，不为生成摘要重新轮询。准备测试使用fixture或冻结
快照，授权测试验证状态转换；活动ledger仅用于明确授权的只读审计。

Recovery固定交付：只读终态审计→身份绑定来源/候选→family×phase实际transition覆盖→共享事件对齐→
形成下一课程请求，再交公共准备器。缺失初始化/控制trace明确UNKNOWN，不从episode均值反推阶段时间。
固定槽位先核对ppo.envs和env→family映射；运行前冻结测试先分类，再在独立副本执行PORTABLE测试，
项目历史集成测试在本体单独运行。该流程不创建新launcher、不守候任务、不自动授权下一配方。

sim2sim先绑定冻结身份与native actor/COM语义，再用具名轴loader审计静态／已有轨迹。
分别报告PASS字段、动力学差异与UNKNOWN；完整动态输入缺失不能用历史重建补齐。
需要新采集时选择显式paired_state，先CPU/零写plan再申请有界物理授权；迁移诊断不改奖励或模型参数。
旧重复审计入口已删除，历史证据保留；所有命令以TOOL_INDEX中的新公共入口为准。

提交前先看storage_budget的产物量/临时峰值/终态余量；不足时停止准备提交，不自动清理。
基础设施重试先检查来源证书能否复用；显式绑定source_evidence_reference，保留旧消耗引用，
新attempt仅结算本次实际工作，不重获历史预算。摘要交付核验raw路径/SHA，不嵌入完整轨迹。

授权前同时核验单臂及多臂publication标记；实验prepare脚本只提供request，复用唯一公共文件包。
存储治理先列活动排除/来源依赖/派生报告计划，保持raw和checkpoint不动；归档/删除另行批准并记账。

工程故障后先核对失败exact账本/完整checkpoint，再收集同身份补充PPO0，审核相关代码差异，生成受限恢复计划。
轻评估仅用于故障诊断，完整认证另列；READY不是运行授权或smoke替代。新运行累计额度扣除历史真实更新，
旧FAILED/账本不改写。身份审核同时看相关依赖SHA与完整快照SHA，排除无关变化不代表忽略相关变化。

### GUI预览与诊断存储

先用共享play默认CPU计划核验spec/checkpoint/分布/姿态family/设备和单环境reset选择；
Recovery preview使用holdout，Motion键盘仍使用共享CommandEnv。实际GUI须明确授权，CPU通过不代表渲染通过。
清理先保留原错误及结果，再尽力关闭环境/Kit；任何清理异常单独报告，不覆盖原始失败。
新诊断声明可显式选择压缩轨迹编码，先确认消费者已通过公共evaluation_loader读数据；
历史数据不自动转换，来源checkpoint保留。一次终态审计和registry事件复盘复用公共工具，不轮询活动任务。


## 接管候选第一阶段

先读新receiver spec/manifest及B50、B250冻结身份。CPU准备→相关边界/optimizer测试→PORTABLE冻结验证→public零写plan，声明UNAUTHORIZED且零attempt。用户新授权后登记独立账本，提交前核验session/GPU UUID/资源/发布marker/源模型；先窗口PPO0，确认合法正常基线且完成复盘后再提交独立接管短训。失败不自动重试、预算不足不换卡。短训source_eval评估来源组合/正常回归与原Motion返回；smoke证明真实交接、valid更新、episode结束、保存，formal25/50/100评估，formal从来源初始化不继承smoke模型。mask/storage计数必须一致，真实故障和数值保护仍阻断。短训不自动接长训、不因旧Recovery0/8停训，也不将receiver零速证书发布为原Motion全部能力。既有owner监督结算，通知需要另有明确收件人授权。

### Recovery学生工程准备

显式选择parent spec/source checkpoint → 按case_id严格核验评估矩阵 → 冻结原配方与来源SHA/差异 →
发布未授权声明 → 公共frozen CPU验证真实构造/首步/异常路径 → review-only提交准备包 → 新授权登记 →
公共supervisor提交检查。CPU任务止于准备包，不自动登记权限/重试/运行。
同输入复用通过的冻结结果，变化则重新验证；保留首次失败与最终成功收据，磁盘分类不等于删除许可。
历史Motion证书22项SHA fixture冲突单列，不用学生CPU通过来抵消或降低生产校验。

## Recovery持续课程（2026-10-12新持续授权）

公共准备器发布task_manifest/累计账本与首块，CPU/冻结验证后由task授权调用公共register_authorization登记有限子额度；public supervisor每块核准共享GPU0 UUID/session/资源/身份。首次新reward source→smoke12→formal；同配方续块source→formal，并验证原smoke与完整resume状态，不重置已用额度。owner结算后做课程决策，按持续授权首次提交下块；worker仅一次有界握手。用户STOP或工程故障禁止自动下一块，无资源不循环等待。总额度null不是999999；单块≤300formal/4h/2GiB。最终认证与巩固成功后自动结束，不开展其他技能。

Recovery首B dispatch工程停止：用户明确批准恢复后，公共准备器--recover-task-from核准旧task ENGINEERING_STOP及子run零attempt/零消耗/无run，发布新task/spec/ledger，承接历史累计消耗和课程状态。修复测试、冻结PORTABLE及零写plan通过后，经公共授权登记/supervisor共享GPU0首次提交。此人工恢复不构成工程无限重试许可，不改旧状态为成功。

已真实运行并结算FAILED的动态v9块不能走零attempt恢复入口。用户新授权后用--recover-failed-task-from：核准task停止且active_spec为空、所有attempt已结算、failed spec/terminal/已评估checkpoint身份；发布新v10任务账本继承历史用量，记录已执行但未保存的更新。新配方首次source→smoke12→formal，CPU/冻结/零写plan后公共登记、提交检查、一次有界握手。旧故障证据不完整时写UNKNOWN，不删除保护或伪称故障已修；再次工程故障停止，不自动重试。

第7节时间平滑A/B：旧课程已结算停止→固定v10 update100完整训练状态→新task累计账本＋两个未授权spec→共同源码及源receipt审核→CPU与两份冻结PORTABLE/零写plan→task授权公共登记A→supervisor共享GPU0核验并一次握手。A普通能力失败继续既定B；A工程失败/STOP则停止。A正常结算后既有owner核准资源与同源码SHA并首次授权提交B，不能继承A末权重。B结束生成比较并停止，不自动追加系数或长训；实际optimizer恢复、有效pair梯度由新smoke证书认证。

## 人工 Recovery 实验

推荐人工步骤依次为init-source（首次）→编辑editable/src和settings→freeze→publish→validate→公共零写plan→authorize→公共check-submission→人工launch。每一步独立执行，写入需显式确认参数，不自动调用下一步骤。公共命令集中维护TOOL_INDEX；源码位置、单位与结果阅读说明见manual_train/recovery/README.md。

editable是可变的真实源码副本；freeze只复制人工改动，运行从独立冻结副本读取。分步流程的奖励真源是editable/src/native_stand/students/manual_reward.py，根reward.py仅作旧一键流程/首次初始化模板，不能混用。活动实验代码、旧模型与账本只读。

新奖励/源码/超参实验仅继承选定Actor，新建Critic/Adam/RNG与smoke。完整同配方续训由人工选择已结算的新版manual formal检查点，校验原smoke证书及源码/奖励/asset/recipe身份，复用原bundle恢复Actor/Critic/Adam/RNG/累计更新/课程；创建新draft、新spec、新账本，重新授权并提交，不重复smoke/warmup。PhysX状态不恢复，新进程reset记录。失败未结算、改配方、旧版无契约检查点不能走正常resume。

公共supervisor内部source/smoke/formal仍由既有owner执行预算和结算；本版没有拆成三个手动物理提交。任务结束只结算并STOP，不自动新块。人工STOP仅作用于指定实验。CPU通过不代表真实物理smoke或能力通过。

## 0.34m站立对称专项连续块

用户本次明确不限累计Recovery站立授权绑定task/session/GPU0共享，total_update_limit=null；每块仍formal300/4h/2GiB独立账本，初块新配方smoke12、Critic warmup5。工程测试/冻结/零写plan、显式授权和一次资源核验后，supervisor提交一次有界握手；owner负责后续结算和同配方全状态续训，不通知、不自动晋级Swing。

每100评估normal三组24，块末四组32＋Swing回归；完整保持、0.34m高度及腿对称一起通过才专项认证。两次确认间至少一次更新；5000formal后才按连续三块停滞进行一次完整状态回退，仍停滞保存NEEDS_DESIGN。通过或用户停止/工程故障提前停止，不要求先学会才能开始PPO。复用物理保护，任何越界取证不自动放宽限位或retry。新版normal配方/协议不回填历史v7/v10/A/B评分。

## Motion0.34m/±2m/s不限累计更新任务

读取当前STATUS指向的task/spec，不重复提交已存在chain_submission。使用该声明的v2源码路径，先公共零写plan、授权登记、PORTABLE冻结验证，再显式GPU0/shared提交；每次提交仅一次有界握手。source_eval普通行为失败允许学习，缺失、runtime fault及身份故障停止。source→smoke25真实episode结束/实际Actor更新/保存→formal300（100/200/300三个命令完整评估）。正式来源不继承smoke末尾。

既有owner有限子账本结算后，恢复同配方Actor/Critic/Adam/std/CPU+CUDA及Python/NumPy RNG、累计计数并公开提交下一块；无外加监视器。两次连续联合24/24后保存该完整候选并结束；至少5000formal后连续三个块无改善，仅一次完整状态回退，再停滞则NEEDS_DESIGN。工程、资源、磁盘或用户STOP不自动重试，不换卡/抢占/删历史。

修复一次已知入口工程故障时，旧run/spec/budget/冻结代码保持只读，新task通过history/origin绑定旧SHA和实际消耗；新声明仍重新测试、授权、预检和独立smoke。UNKNOWN或FAILED握手不写成RUNNING，更不写成formal已更新。

## Motion先站稳并对称

用户同意停止旧配方后写本任务STOP，由原owner在更新边界保存并结算；保留旧账本和模型。只在新task/spec启用新的mirror配方，保持合法初始化，不为凑目标高度硬改初态。独立bundle完成相关与PORTABLE冻结验证、零写plan、公共授权及共享GPU提交检查后，一次launch/有界握手；SOURCE_EVAL不等于formal首更新。

来源候选仅从完整零速原物理通过证据中选取，镜像未达标不能称accepted。新reward首块Critic/Adam重新初始化；后续同配方按完整训练状态续块。每块自身smoke证据匹配；两次联合零速8/8通过保存并停止，驾驶回归另立声明，不自动训练±2。

Motion新Adam工程故障修复：原FAILED与账本不重写。用户明确修复并继续后另建执行副本/task/spec，真实CPU测试覆盖新Adam空state、warmup部分state和历史完整state；零写plan、冻结身份、授权、资源检查完成后只提交一次。首次新reward仍Actor/std继承、新Critic/Adam、warmup5，同配方后续完整续训。

Motion alignment首块：旧任务STOP结算后，新bundle注册reward/gate/schema，具名trace离线重放，实际reward、公共gate、freshAdam和Criticwarmup测试，冻结PORTABLE/preflight与零写plan；用户确认尝试启动后新授权receipt，sharedGPU/session/UUID/源码与source核验，公共supervisor只提交一次/30秒握手。每100formal评估；formal300或预算/故障后owner结算停止，不自动追加设计试验块。保持峰高通过不冒称完整启动或实机限高认证。

## 新链的校验与身份记录

1. 用TOOL_INDEX中的validate_cpu对共享src运行PORTABLE测试及零写plan；不创建执行副本。
2. supervisor在预约前核验授权、资源与前置证据；ledger锁内再次核对关键文件SHA和预算，将提交凭证绑定exact attempt。
3. trainer消费已预约凭证，保存requested/effective配置及实际源码身份；代码变动记录为差异，不冒充相同版本比较。
4. 收尾优先使用运行记录，报告异常生成保守缺证据摘要；通知仍按已有负责人授权及at-most-once机制执行。CPU结果不授予仿真或能力通过。

## 新声明的模型、预算与保存校验

准备时显式绑定source SHA和初始化语义，由公共ModelAdapter读取checkpoint，不按文件名或宽度认定新接口。来源/cadence/storage可以是新实例字段；reward、PPO、课程或物理改变仍须单变量声明和新授权。

ExecutionLimits负责update/sample/wall口径。smoke/formal的显式null表示没有墙钟上限，不表示无限更新；授权模板保留null，由用户明确批准。来源与PPO0评估仍须有限墙钟，账本实际消耗不重置。

保存策略在提交前声明；checkpoint清理只由运行owner在更新边界执行，先记录意图、再核验SHA并更新inventory。CLI仅审阅计划；历史目录不纳入运行清理。评估/选择引用优先于keep_last配额。默认不开启日志轮转或清理，开启后的字节/备份/终态余量均从spec读取。

## 保存中断与补充诊断

checkpoint owner删除前同时保存intent及inventory的removal_pending；删除后再标removed。
若进程中断，下一次同exact RUNNING owner会核对记录并结算已删项；普通缺文件或变成被引用的缺失模型仍拒绝。
已结算旧run仅输出pending事实，不写恢复或再删除。

optimizer初态仅显式指定phase/update保存，先核对字节上限；不会替代完整rollout或自动执行离线重放。
提交计划分别显示配置、账本授权、前置证据和资源就绪，未实际检查资源显示null，而非默认通过。
学生诊断从显式父声明和模型dataset身份构建，禁止默用旧日期模板；CPU通过不授予PPO0物理运行。

## 站立工程smoke与能力分离（v14 wiring2）

工程证书验证真实更新/episode结束reset/reward/保存，不要求随机策略已经完成30秒站立；timeout实际覆盖单独记录。完整生存与末段质量验收不放宽。新授权、新spec/ledger、新run，不改旧FAILED或消费旧余额；source→smoke12→formal988由既有owner执行，单次握手后结束交互。配方与本轮证据见[修订记录](docs/STANDING_SURVIVAL_WIRING2_20261014.md)。

## v14存储故障后的训练状态恢复

父formal终态及已耗额度→受限storage_resume证据/原smoke核验→新命名spec/独立余额账本→CPU容量回归及Actor/Critic/Adam逐tensor恢复→公共授权/提交→一次握手。source补齐checkpoint完整评估后formal，不重复smoke/warmup。缺旧RNG显式记seed重置，物理重新reset；新checkpoint保存RNG。历史FAILED/312消耗保留，剩余688不是额外1000。具体见[恢复记录](docs/STANDING_SURVIVAL_STORAGE_RECOVERY_20261014.md)。

### 已知恢复状态机错误的单次重试

零PPO故障终态→原完整source身份核对→具名continuation的完整worker CPU测试→新retry声明/独立ledger→显式授权登记→公共提交一次。source只读复用，RunState记reused再formal；不重算旧source消耗、不复制轨迹。失败后无自动下一次重试。见[执行记录](docs/STANDING_SURVIVAL_RESUME_STATEFIX_20261014.md)。

## 性能优化验证

先CPU比较原/缓存轨迹及rollout统计、异常/RNG清理→有界GPU张量微基准→新GPU1 PPO0声明与原评分协议→公共授权/资源/提交→一次身份握手后结束。物理评估完整回收后才能讨论实际case wall节省，不能把微基准倍数当作整场加速。训练统计启用须下一次新声明；不改活动进程。见[记录](docs/STUDENT_PERFORMANCE_OPTIMIZATION_20261014.md)。
