# 新版学生分阶段蒸馏交付 — 2026-10-11

## 已完成与能力边界

已产生独立RecoveryStudent与零命令MotionStudent，1182D接口、教师数据、真实CPU BC、学生独立runtime/public PPO0与GUI的零写计划已完成。未启动Isaac/GUI/采样/GPU训练/在线PPO；未认证自主起身或运动能力。旧receiver首次核对没有chain_terminal_report/completion_report，不作当前存活或终态推断，不再查询、不停止或重复提交，由原owner负责。新版不依赖它，不采用其checkpoint。

## 接口与物理

版本multiskill_student_v1。Actor=51×(22＋valid)＋9=1182D，当前与前50个10ms frame、oldest→newest、不足历史零填valid=false；真实初始化frame保留但不作标签。body角速度3×.25、body单位gravity3、四腿q-reference/1.5、active dq6×.05、previous实体腿4/reference/1.5及wheel2/100；任务onehot4＋vx/4＋yaw/4＋height/.5＋两个米单位jump字段。Actor无仿真高度/速度/contact/教师ID/未来成功/切换时刻。Recovery整条任务命令[0,0,.36,0,0]且Recovery标识不变。Motion零命令[0,0,.40,0,0]。

Critic1191D真的读取Actor1182＋height1＋native线速度3＋contact2/100＋controlled/2.5、entry/.2、hold/10。native线速度[-bodyZ,-bodyX,+bodyY]，root pose为link frame，速度保留原Isaac root COM属性语义；无差分伪造IMU加速度。Critic新初始化，BC不训练它。

两学生都是新MLP256→128→64 ELU、6输出，参数不共享教师；全部mean tanh有界，但随机动作普通Gaussian，logprob无squash Jacobian。BC只优化MLP动作mean，std固定物理腿.05rad/轮2rad/s。left-first动作0/1/3/4腿、2/5轮；reference六通道零、腿±1.5rad/轮±100rad/s，再执行原USD限位。原Plane、限位USD、1/5/10ms、PD60/2/1、40/5.5Nm不变。拒绝未知interface、未降低legacy150D严格校验；新版不沿用Motion .5rad任务终止，真实机械保护不删。

## 教师与原始数据

B50：runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_50.pt，SHA 46add82fa9d32c04fcc0a8b79c6339a27df3b9ca6c95050b8e13f52b644b7f75。B250：runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt，SHA 5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。两者自己的冻结spec与checkpoint内部spec SHA相符，训练前后checkpoint SHA不变。

数据来自16_44组合诊断与22_24邻近窗口；全部消费的evaluation spec SHA/trace SHA、schema、active names/indices、原资产与PD核验。成功31条=旧7＋新24，不是31种独立恢复或training seed。真实pre-action本体＋previous物理目标→本次实际执行的腿/轮目标；control四腿＋两轮按具名字段转换为left-first学生尺度，不能复制旧normalized action或把post q当标签。不符合包络直接失败，无静默裁剪。旧Motion .6×.5=.3rad映射学生.2的往返已测试。

Recovery train15条=旧7＋最新seed20261010的8；validation8条=20261011；test8条=20261012，完整episode互斥，test从未选epoch。失败env4登记在manifest.excluded诊断，不进入成功监督；其他失败条件原始轨迹不混入正向数据。

|阶段|train唯一样本|validation|test|训练实际draw|重复draw|
|---|---:|---:|---:|---:|---:|
|preparation|750|400|400|640000|639250|
|turn_lift|375|200|200|640000|639625|
|dynamic_settle|1466|788|774|640000|638534|
|stable_hold|15000|8000|8000|640000|625000|

总Recovery唯一样本36353；每batch四阶段各128（25%），阶段内均衡episode后均匀抽time，保留真实连续历史，不拼段。turn_lift是Motion第一25 interval，dynamic_settle随后至首次入口确认，stable_hold下一1000interval；这是数据分层，不是部署时间表。共2,560,000 BC采样draw只是重复教学，不是新增物理经验。

Motion仅采用两个诊断的16条正常零命令完整episode（旧6train/2validation、新8test），16320唯一样本；已有入口前20帧与1000帧保持分层，各50%抽样。阶段名turn_lift在正常组仅表示入口初始短段，不代表Motion执行起跳。其实际教学命令只有0/0/.40，独立前后/yaw/高低速尚未蒸馏。旧motion_recheck post-step状态/control不足以构建每100Hz pre-action角速度/gravity/previous执行目标及连续0.5秒history，未消费；缺字段和最小补采记录在supplemental_identity_and_motion_gap.json。不同USD历史能力不冒充当前验证。

## 实际CPU BC与误差

两学生上限各5000step/1200秒，batch512、新Adam lr.001、线程4、每200step验证、连续5次无改善早停。CPU优化使用新学生副本，无教师/旧Adam/RNG复制。Recovery实际5000step/26.1747秒、best5000、step_limit；Motion2400step/12.0303秒、best1400、五次无改善早停。合计7400离线optimizer step，在线PPO0；CPU数据/加载/assembly测试没有对这两个候选再执行optimizer step。

|Recovery阶段（测试）|腿MAE rad|轮MAE rad/s|腿P95 rad|轮P95 rad/s|动作拟合参考|
|---|---:|---:|---:|---:|---|
|preparation|0.001818|0.170035|0.003743|0.324928|PASS|
|turn_lift|0.002999|0.237766|0.006023|0.415570|PASS|
|dynamic_settle|0.003972|0.901696|0.011536|2.562258|PASS|
|stable_hold|0.001782|0.480980|0.003661|0.668292|PASS|

验证集四阶段也均通过（腿MAE.00181–.00418，轮MAE.169–.996，P95腿≤.01159/轮≤3.046）。Motion测试入口短段腿MAE.000195/轮.03012/P95腿.000476/轮.08115；保持腿.000374/轮.03724/P95腿.000704/轮.08811，均动作拟合通过。每阶段train/validation/test、逐次验证、过采样、初始化SHA、dataset/manifest SHA与Adam状态在training_result.json/checkpoint保存。只有零命令，所以“每命令”只有该一项，不伪称覆盖非零驾驶。

## checkpoint与身份

|角色|checkpoint|SHA256|
|---|---|---|
|完整恢复BC候选（闭环未测） / best_validation.pt|isolated/recovery_student_bc_20261011/best_validation.pt|bd163dd75b6ac5e8f33f82069fe94f173069ed966f077133c895eb11f1bc499c|
|完整恢复BC候选（闭环未测） / latest.pt|isolated/recovery_student_bc_20261011/latest.pt|24e5d4f364ebb5c8ee5b08e231feed2d270fb66d412865492bf5af128d064c53|
|完整恢复BC候选（闭环未测） / random_initialization.pt|isolated/recovery_student_bc_20261011/random_initialization.pt|9fc16d1ca1b1d4bffe63ad05b6f9c4b7de4b2ebf837a67b59dc66a927005bd90|
|零命令预训练（驾驶未迁移） / best_validation.pt|isolated/motion_student_zero_bc_20261011/best_validation.pt|769a0512638dfb3ab47f5f5720c470d4e88c59ed0a67957720e8a3bcba42779d|
|零命令预训练（驾驶未迁移） / latest.pt|isolated/motion_student_zero_bc_20261011/latest.pt|4333867fdbcd5785bc948b119262f9154270a36fc677631e974066d347ee9adb|
|零命令预训练（驾驶未迁移） / random_initialization.pt|isolated/motion_student_zero_bc_20261011/random_initialization.pt|43deec3a657bc116e5f0b2fc5d953979e4c4bb03f9e317c202972ec45187ec7d|

dataset：isolated/student_teachers_20261011/RecoveryStudent.pt SHA 6582a751047e2e1dcffdacf9cd2b02342de79360b0e0e6adaa297b2717e1bc08；MotionStudent.pt SHA 4141b7557eecd7293ec37d7fc86ea6842d8ed425492fb897e47377e252737506。manifest、补充身份/缺数据报告位于同目录。候选没有能力accepted证书，不能自动部署。

## 已接通的链与待验证部分

config/model_factory按interface显式分派；public supervisor --evaluation-only复用monitor/ledger/evaluate_checkpoint→students.evaluator→StudentEnv共享原RecoveryEnv物理/PD。学生分支只学生forward，无B50前缀/无B250接管；ForbiddenTeacher哨兵拒绝隐藏救场。按真实episode policy时间构建历史，重复观测不重复追加，partial reset仅对应env；Critic特权字段直接进入1191D网络。请求、动作裁剪、限位裁剪、执行目标、力矩、root/q/dq与first-episode/owner保存100Hz轨迹；数据不冒称完整200Hz/1kHz。异常partial/terminal先落盘，cleanup不覆盖原异常，actor模式/临时状态/RNG恢复；加载候选不消耗采样RNG。

新学生协议≤2.5秒（含20interval确认），其后同episode1000interval保持；零时间轴、重复/跳步、无效保持/reset拼接/提前失败不通过。过渡允许失触，保持仍height≥.30，level mean≤.10/peak≤.15、tilt≤.18、双轮sensor合力>2N（非独立法向载荷认证）、closure≤5mm、policy触限≤5%、vx≤.5/vy≤.02/yaw≤.03。教师组保持原2秒接管协议，旧结果不变。

students.ppo真实装配ControlledPPO/rollout storage已CPU消费1182/1191＋pre-action mask，读取学生raw采样与自己的old logprob，新Critic/new empty Adam；不导入BC optimizer。actor/critic不共享、完整物理GAE时间轴、all-invalid语义继承既有实现并回归。独立BC辅助loss接口不伪装on-policy。当前没有新版在线reward/formal提交声明，因此不声称在线PPO已完全可提交，也不创建日期型trainer或开展长训。

## CPU/冻结/零写验证

相关39项通过；冻结实际source副本29 PORTABLE通过、schema PASS/public plan零写，最终冻结inputs逐SHA无漂移。全CPU778pass/22ERROR：所有错误同一个已有Motion工程certificate fixture，未修改的runtime/configure.py与旧证书SHA不符；已与本轮之前的receiver baseline证据核对，不重写旧证书/不将全suite称全绿。详见isolated/student_delivery_validation_20261011/与artifacts/student_delivery_frozen_cpu_20261011/validation_result.json。

公开zero-write plan只有AUTHORIZATION_MISSING，无配置/模型/schema阻塞；GUI命令只做zero-write plan，未启动。00_40/00_48为未授权零attempt准备历史，最终仅使用00_55声明，不删除旧声明或重用账本。

## 下一次物理验证（未授权/未运行）

spec：/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_11-00_55__student_independent_swing_ppo0/spec.json
ledger：/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_11-00_55__student_independent_swing_ppo0/budget.json
spec SHA：d698e95fa24ae821dff01d3c066f00079a5b694822878c41dcc290835f6850ce

共10组×8=80评分episode：原Swing＋三小yaw学生独立恢复4组、同条件冻结B50 .50秒→B250教师对照4组、MotionStudent正常零命令及B250正常基线各1组。64实际仿真env/8评分env；PPO/optimizer0、总墙钟1800秒含初始化/评估/清理、输出512MiB。计划物理GPU0共享，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，逻辑cuda:0；本轮不查询或宣称资源当前空闲，授权后提交前公共核验。准确命令唯一维护TOOL_INDEX，不复制到多文档。

尚未运行的关键问题：学生独立闭环是否起身、是否在最早抬升/落地区间偏离、10秒保持及位移/倾角/触限代价。三个小yaw验证不足高度/速度/地形泛化。若闭环好再设计有界PPO；若早偏离先复盘并准备有限合法教师标注/补采，不能默认B250能教任意失败Swing。

## 实际修改文件

本轮在既有dirty版本上增量修改，保留他人变更；无commit/push，未改外部项目、历史run/checkpoint/spec/ledger或旧活动冻结代码。

- AGENTS.md
- ARCHITECTURE.md
- TOOL_INDEX.md
- STATUS.md
- docs/MULTI_SKILL_ROADMAP.md
- docs/RECOVERY_STANDING_PLAN.md
- docs/STUDENT_DISTILLATION_DELIVERY_20261011.md
- src/native_stand/command_v6/config.py
- src/native_stand/command_v6/tools/model_factory.py
- src/native_stand/command_v6/tools/preflight.py
- src/native_stand/command_v6/tools/evaluate_checkpoint.py
- src/native_stand/command_v6/tools/play.py
- src/native_stand/recovery/handoff_protocol.py
- src/native_stand/students/__init__.py
- src/native_stand/students/data.py
- src/native_stand/students/distill.py
- src/native_stand/students/evaluator.py
- src/native_stand/students/interface.py
- src/native_stand/students/model.py
- src/native_stand/students/play.py
- src/native_stand/students/ppo.py
- src/native_stand/students/protocol.py
- src/native_stand/students/requests.py
- src/native_stand/students/runtime.py
- scripts/build_student_teachers.py
- scripts/distill_student.py
- scripts/prepare_student_validation.py
- tests/test_student_interface.py
- tests/test_student_data.py
- tests/test_student_execution.py

新增数据与checkpoint/声明/冻结验证目录见上述路径；新声明UNAUTHORIZED零attempt。所有学生角色/字段/命令只是相应显式版本，不放宽成任意维数。Jump/Traverse/压弯本轮仅预留任务命令，未开展技能训练。
