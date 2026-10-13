# 同一31D Recovery学生：任务PPO工程与授权提交

**最新执行快照：13_35新批准后一次提交，来源评估和smoke已COMPLETED、工程证书PASSED；单次握手确认formal首更新1（Critic warmup）。formal终态尚未复盘，由既有owner结算。12_54/13_11历史FAILED保留。**

本轮目标为同一个Recovery学生从合法Swing独立收腿、转腿、抬升、收稳并保持10秒。来源固定CPUBC学生，不新增BC、不更换PPO起点、不切旧教师执行、不加入历史/GRU/阶段输入。来源0/32是行为失败，不是工程禁训条件。

## 固定身份与真实接线

来源isolated/recovery_mcu_v2_bc_20261011/best_validation.pt，SHA 7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470。两位教师成功组合仍是该单一学生的已有教学来源，B50准备、B250转腿/抬升/收稳/保持；本轮lambda_BC=0，不抽BC minibatch，不更新BC分支，不在学生失败状态伪造专家标签。MotionZero/Jump/高速/量化/真机不推进。

interface multiskill_mcu_v2与recipe student_recovery_ppo_bc_v1分开绑定。Actor31→128→64→32→6，Critic40→256→128→64→1，ELU、tanh mean/普通Gaussian采样raw action。Actor加载固定学生，Critic和PPO Adam新初始化，原Critic/BC Adam/教师RNG均不恢复。std腿.05rad/轮2rad/s，log_std不优化。每阶段前5个计费更新只Critic，之后Actor＋Critic；smoke不接棒formal。

公共prepare→config/preflight→supervisor→既有stand_chain/monitor→公共train.py内学生recipe适配→共享RecoveryEnv物理＋ControlledPPO/Storage→checkpoint→独立评估→wiring/终态/ledger，未另建私有launcher、watcher或日期trainer。学生始终Recovery/NONE六通道；仅Swing及已有.01rad小yaw，旧DrawBack/R0槽位、retention、receiver前缀、历史位置×镜像/纪录奖励和11.5s deadline均不消费。旧v2没有完整recipe时仍拒绝在线请求。

物理不变：USD SHA 32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7；Plane/PD60/2/1、1/5/10ms、腿1.5rad/轮100rad/s、40/5.5Nm与机械限位。

## Reward与完整证书

纯recovery_task显式post-physics/pre-reset：
H=clamp((h-h0)/max(.30-h0,.05),0,1)，h0为首个受控动作前高度。
U=exp(-(pitch²+roll²)/.30²)，C=双轮>2N合力且净空>0，S=HUC。
密度2H+3S-.02努力-.002实际目标变化-.05入口后角速度-.10入口后速度/yaw，全部dt=.01一次。
努力为六通道实际applied torque/40或5.5平方均值；D腿实际目标差/.1rad、轮/10rad/s；水平角速度bodyX/Z，native vx=-bodyZ、vy=-bodyX、yaw=bodyY。W/V首次入口后才启用。
事件entry+1/success+10/failure-1一次，不乘dt。初始化reward0、actor mask false；runtime fault无reward且单独工程终止。低位静止无无关存活奖，.42不超高处罚，不跟踪教师固定时刻。

Certificate累计第一次入口后下一1000interval高度/姿态/接触/净空/闭链/采样触限与vx/vy/yaw；window_complete与certificate_passed分开，失败不重新挑窗口。2.5s入口+.20s确认+完整10s保持，环境13.52s容纳初始化。纯CPU在线/离线证书通过、接触坏样本/速度.51/短窗拒绝；训练评估也核对在线success与原离线score一致。
真实终止使GAE吸收；正常rollout不done，末观测bootstrap；不删初始化时间步，保留critic完整轴。工程timeout/预算退出不伪装成功。评估在完整更新后另建同物理env，之后训练明确重建/reset并用新obs，清空rollout边界不拼GAE。

## 离线校验，无新BC

既有教师成功与学生失败各8首episode重放；teacher样本entry奖+1/success+10各一次，学生failure-1一次。首例教师总未折扣回报约64.66，学生约-.861；仅符号/单位/事件检查，非训练有效性证明。
合成单元测试覆盖低位驻留零奖、腾空H可有奖但不作为站立、冲高.42不罚、重复入口无重复奖、1000窗坏接触/速度不发success、fault零reward及早终止。
来源固定输入离线逐通道误差，见[完整机器审核](../isolated/student_recovery_ppo_fixed_input_audit_20261011/fixed_input_audit.json)，包含每个episode教师切换前/后各5帧。相近输入不是相同输入，目标跳变不证明31D不可能学习；早期准备腿尾部和后续动态轮是风险，本轮不以拟合参考线为PPO前置。

| 阶段 | 通道 | 单位 | MAE | P95 | 最大误差 |
|---|---|---|---:|---:|---:|
| preparation | left_hip | rad | 0.048651 | 0.191232 | 0.237544 |
| preparation | left_active_link | rad | 0.041642 | 0.137534 | 0.174944 |
| preparation | left_wheel | rad/s | 0.557888 | 1.058092 | 1.217121 |
| preparation | right_hip | rad | 0.077445 | 0.308781 | 0.384957 |
| preparation | right_active_link | rad | 0.027447 | 0.054603 | 0.073262 |
| preparation | right_wheel | rad/s | 0.913775 | 2.454740 | 2.845728 |
| turn_lift | left_hip | rad | 0.031825 | 0.014506 | 0.666133 |
| turn_lift | left_active_link | rad | 0.025293 | 0.015448 | 0.521168 |
| turn_lift | left_wheel | rad/s | 0.399989 | 0.380869 | 6.741142 |
| turn_lift | right_hip | rad | 0.054649 | 0.025395 | 1.076127 |
| turn_lift | right_active_link | rad | 0.015595 | 0.020153 | 0.254693 |
| turn_lift | right_wheel | rad/s | 0.282768 | 0.120311 | 6.393588 |
| dynamic_settle | left_hip | rad | 0.010616 | 0.028323 | 0.050572 |
| dynamic_settle | left_active_link | rad | 0.007994 | 0.020336 | 0.031019 |
| dynamic_settle | left_wheel | rad/s | 1.492132 | 4.786859 | 10.140008 |
| dynamic_settle | right_hip | rad | 0.012722 | 0.033235 | 0.048589 |
| dynamic_settle | right_active_link | rad | 0.010878 | 0.022981 | 0.042758 |
| dynamic_settle | right_wheel | rad/s | 1.774221 | 5.888442 | 11.061078 |
| stable_hold | left_hip | rad | 0.003161 | 0.005521 | 0.012456 |
| stable_hold | left_active_link | rad | 0.001675 | 0.007788 | 0.013477 |
| stable_hold | left_wheel | rad/s | 0.805905 | 1.255502 | 2.603822 |
| stable_hold | right_hip | rad | 0.003523 | 0.005953 | 0.020152 |
| stable_hold | right_active_link | rad | 0.004256 | 0.006760 | 0.017500 |
| stable_hold | right_wheel | rad/s | 0.902103 | 1.127617 | 4.548211 |

## 新预算、采样和保存

独立声明configs/experiments/2026_10_11-12_54__recovery_mcu_v2_task_ppo_from_bc/spec.json，独立budget，旧12_50准备未授权零attempt，不提交或覆盖历史。用户本轮新授权已由公共工具登记：
- source_eval一次，原四组学生32＋原生教师组合8，共40episode/900s。
- smoke12更新/98304samples/900s；真实初始化、非零reward进Storage、mask、reset、warmup前后Actor变化、BC0/std固定及checkpoint回读证书；末原生8episode，不要求先起身。
- formal100更新/819200samples/5400s，25/50/100四组各32共96episode；同组完整通过数→入口数→首窗有效保持前缀→更早候选选模，来源也参与。
- formal末单一选定候选原生＋三新小yaw seed20261013/14/15共32episode复核，预算不足NOT_RUN，不拼模型。
- 在线112更新/917504samples、物理阶段累计7200s、评分episode上限176、产物≤2GiB。
- 64环境×128/8192更新；有效Actor样本目标≥250000，不足不追加。lambda_BC0，无额外CPU BC。
- PPO lr3e-5、4epochs/4minibatches、gamma.99/GAE.95、clip.2/value.5/entropy.001/grad1。
- 保存source完整、smoke1/6及formal1/6/25/100选定rollout、固定评估、checkpoint25/50/100和故障32帧尾部。逐update保存轻量reward raw/weighted/dt/event、returns/value/adv、KL/clip/grad、mask/episode/event/目标变化/clip/触限。源snapshot/model/dataset/资产SHA全绑定。
- GPU0共享，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，逻辑cuda:0，不抢占/不换卡/不自动重试。公共提交检查READY。通知明确disabled，不额外发送消息；终态由既有owner保存结算，worker不轮询。

## CPU验证与提交状态

提交前35相关测试通过、冻结PORTABLE26通过；修复后验证另列最终机器结果，配置/零写plan消费完整recipe。全CPU801通过/22errors，修改前788通过/相同22errors，逐ID及fixture内容一致：旧Motion证书configure.py SHA错误；本轮未改configure.py、不放宽SHA或跳过关键测试。本轮新增一次测试fixture缺case_id错误已修正，未将其当历史错误豁免。
实CPU optimizer只更新独立内存副本，证明warmup/空mask不更新Actor/其Adam、之后Actor实际更新、std固定、BC零梯度、不改变diagnostic RNG；这些是CPU回归，不计在线或BC训练。

一次公共supervisor提交，启动握手与实际阶段在本报告下方补记；尚未终态不能声称formal100完成或闭环改善。既有owner按同一授权完成source→smoke→formal并写报告；worker不得守候长训或自动重提。
工程与授权证据位于isolated/student_recovery_task_ppo_submission_20261011，源码冻结测试位于artifacts/student_recovery_task_ppo_launch_frozen_cpu_20261011。命令只维护TOOL_INDEX。

## 本轮改动

- src/native_stand/students/recovery_task.py
- src/native_stand/students/training_recipe.py
- src/native_stand/students/training.py
- src/native_stand/students/training_evidence.py
- src/native_stand/students/runtime.py
- src/native_stand/students/requests.py
- src/native_stand/students/ppo.py
- src/native_stand/students/model.py
- src/native_stand/students/evaluator.py
- src/native_stand/recovery/controlled_ppo.py
- src/native_stand/command_v6/train.py
- src/native_stand/command_v6/stand_chain.py
- src/native_stand/command_v6/wiring.py
- src/native_stand/command_v6/completion.py
- scripts/prepare_student_recovery_ppo.py
- scripts/replay_student_recovery_reward.py
- scripts/audit_student_recovery_fixed_inputs.py
- tests/test_student_recovery_task.py
- tests/test_student_recovery_ppo.py
- tests/test_student_recovery_training_boundary.py
- PROJECT_MASTER_PLAN.md
- docs/RECOVERY_STANDING_PLAN.md
- ARCHITECTURE.md
- TOOL_INDEX.md
- STATUS.md
- docs/STUDENT_RECOVERY_TASK_PPO_SUBMISSION_20261011.md

## 终态后必须回答

1. 同一学生完整教学目标仍为B50准备＋B250抬升/收稳，运行时只有学生。
2. 本轮额外BC为0，固定输入只是识别准备腿尾部/教师边界风险。
3. 在线真实更新数、有效actor样本、warmup与std/BC状态以terminal/metrics/ledger为准。
4. 同四组候选与固定来源比较完整成功、入口、首窗保持；不能按reward/最高高度/latest选。
5. 区分早期动作、转腿、落地和持续保持，评价轮振荡；事件先后不是唯一根因。
6. 下一轮仅据终态选择单变量；如仍无改善才考虑少量可部署阶段信息或短历史，不自动回1182D或叠GRU/reward/PD，不自动续训。

## 本次唯一物理attempt终态与修复

启动管道返回FAILED，而非formal首更新。链attempt 593a52115eac44a1a082c0753d63ae32、source attempt 69488bef56e846ca8839c168e3f3f0ab。source_eval在第一policy interval的父类_get_dones访问task_phase时AttributeError：
TrainingStudentEnv在父类构造结束后新装Certificate，但删除旧rising_task后父类不再初始化task_phase；本轮适配器也未补齐。此前简化CPU父类fixture没有执行真实RecoveryEnv构造/_get_dones，漏掉这项依赖。这是本轮工程错误，不是历史22项fixture问题，也不是学生能力失败。

实际source attempt=1、ledger wall5.567381s，monitor含清理5.567802s；在线更新/样本/effective actor均0，新增BC0，smoke/formal0。第一组INCOMPLETE、其余四组NOT_RUN，无完整评分episode；不能写成学生0/32或教师失败，也不能声称PPO改善。新增run产物约2,506,931bytes。实际子进程exit0但terminalFAILED（Kit快速close默认exit0），owner依据FAILED停链，没有放行smoke。
原FAILED、冻结代码、ledger和报告只读保留，未重试或复用旧额度。

修复仅共享下一次执行代码：
- TrainingStudentEnv显式初始化task_phase，作为既有父类控制/评分缓存，不加入31D Actor。
- 新CPU fixture使用真实RecoveryEnv构造及真实_get_dones，主动删task_phase复现相同异常，再确认补齐后初始化/受控步/终态reward正确。
- Kit清理显式close(exit_code=1 on failure)，终态和清理预记录先写，避免快速退出导致错误exit0。
- 首步失败也保留pre-action-only数据，明确不能冒充已执行完整interval；之后错误保存partial raw与INCOMPLETE矩阵。
- 未改变reward、PPO参数、物理、Actor来源或预算；额外BC/仿真重试均未运行。

修复声明：[13_11 spec](../configs/experiments/2026_10_11-13_11__recovery_mcu_v2_task_ppo_from_bc/spec.json)、[独立未授权ledger](../configs/experiments/2026_10_11-13_11__recovery_mcu_v2_task_ppo_from_bc/budget.json)。零写plan只缺新重试授权，不创建run。该声明未自动授权/提交，不借用12_54剩余更新。
本轮用户明确“工程故障后不自动重新提交物理attempt”，所以完成修复与CPU/freeze/plan后必须再次批准一次物理重试，才能实际进入source→smoke→formal；既有CPU修改授权继续有效。
本轮尚不能回答学习改善或最大动态瓶颈；现有离线风险仍为准备腿尾部和教师切换边界，下一实际任务是修复版本一次有界PPO，非新增BC或改接口。

最终修复验证：36相关通过、27冻结PORTABLE通过；全CPU802通过/22errors，与本轮修改前788通过的22项ID/fixture原因逐项相同。13_11零写plan唯一缺项为新物理授权，零attempt、未创建run，源模型SHA未变。机器交付：isolated/student_recovery_task_ppo_submission_20261011/failure_and_runtimefix_delivery.json。


## 13_11批准后的实际重试与共享修复

本次通过公共register_authorization登记新批准并由supervisor一次共享GPU0提交。启动检查READY，GPU UUID为GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES=0，逻辑cuda:0；无抢占。链attempt为1465021236c3481da5ffbb4b26c148a2，source attempt为e3ca97b52cf34eb0a75e967b6a653b47。仅一次事件握手，返回FAILED，未轮询后台。

四组学生共32个首episode完整落盘：初始化32/32有效、入口0/32、完整保持0/32，在线与离线证书一致。第五组教师对照首个interval抛出HandoffEnv.task_phase缺失，保存pre-action-only故障数据；该组INCOMPLETE，不能伪造教师0/8能力结果。链48.3278秒，source账本46.5381秒；PPO更新/在线样本/新BC均0，smoke及formal均NOT_RUN。产物约4.93MiB。原始FAILED和ledger未修改。

12_54只补学生子类，遗漏了同样在父类构造之后安装clock的教师接管子类。现在task_phase在RecoveryEnv中无条件分配，与可选phase_coverage解耦；TrainingStudentEnv删除重复分配。tests/test_student_recovery_runtime_parent.py同时执行真实HandoffEnv构造、前置动作和父类_get_dones，并验证教师controller及post joint快照。没有修改reward、来源、接口、PD或PPO参数。

相关36项通过；冻结PORTABLE27项通过；全量802passed/22errors，与修复前22项错误ID及configure.py unchanged-contract SHA fixture原因完全一致，未放宽SHA检查。机器结果位于isolated/student_recovery_task_ppo_retry_20261011/review.json；下一冻结验证artifacts/student_recovery_parent_clock_final_cpu_20261011。

新声明13_35由公共命名/准备工具发布，固定同一BC学生、BC0、source40/900s、smoke12/900s、formal100/5400s、112更新917504样本/7200s/2GiB。零写plan仅缺新物理授权，ledger UNAUTHORIZED、零attempt、无run。工程故障后的再次物理提交需新明确批准；本次未自动重试，不借两次FAILED余额。准确公共命令见TOOL_INDEX。


## 13_35新批准后的实际提交

用户本次明确批准共享父类修复后的新物理链。公共授权登记绑定13_35独立spec/budget与当前会话；201项冻结输入无漂移，GPU0 UUID和CUDA_VISIBLE_DEVICES=0匹配，显式shared且无抢占，提交检查READY。新冻结27项已通过；未再次修改训练源码、reward或预算。

来源评估COMPLETED：学生四组0/32，教师组合8/8；学生未通过被保留为行为结果，不冒称能力通过。来源前清理墙钟113.0309秒。smoke COMPLETED：12次真实PPO更新、98304原始samples、45991有效Actor samples，wiring_certificate PASSED/errors=[]；smoke确定性行为0/8。smoke前清理墙钟171.2916秒。

600秒内单次有界事件握手返回FORMAL，formal attempt63e838e0293d4437bf9f6ca11d32ac96，actual_updates=1，started=true、identity_verified=true、formal_first_update_verified=true。此更新是声明内前5次Critic warmup之一，不能写成formal Actor已更新；smoke证书已证明warmup后Actor更新链路。formal从固定BC来源独立初始化，没有继承smoke末模型。

后续由既有owner按formal100/5400秒执行25/50/100评估、选模、最终复核和exact-ID结算。worker在握手后不再查formal进度、日志、PID或GPU，不守候，不自动重试/追加预算。notifications保持disabled；未登记本次额外通知权限。总预算112更新917504samples/7200秒/2GiB保持。

机器提交证据：isolated/student_recovery_task_ppo_parentfix_retry_20261011/authorization_result.json、check_submission.json、launch_handshake.json、submission_delivery.json。当前来源SHA仍为7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470，授权后spec SHA为48d8eb0dbb368f318b898f2ea33f6104546a545aa8891c818862a63525468226。
