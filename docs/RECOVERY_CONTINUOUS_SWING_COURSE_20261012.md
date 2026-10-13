# 同一Recovery学生的持续动态课程

用户2026-10-12明确授权本任务累计PPO更新不限量、计划内自动续训/晋级/有限回退/认证。不是旧余额续用，不覆盖旧run。任务级授权plan以null表达无累计更新/墙钟上限，子run独立spec/ledger/exact-ID，formal最多300更新、全块14400秒含评估清理、产物2GiB。GPU0共享、不抢占不换卡；工程故障/磁盘不足/用户停止停链，不自动重试。后台复用stand_chain与monitor，没有新增watcher或私有trainer。

源为00_12 formal update300，SHA2a587c31bbf81f2db669561965431cc97598c9e13b87043553582b8a09237a9a；normal实验候选，不是accepted。31D/40D、网络、固定物理std、1.5rad/100rad/s、PD60/2/1、1/5/10ms、40/5.5Nm、限位USD/Plane保持。BC0，无Progress、历史、GRU、滤波、投影、隐藏补偿。

## 一次证据复算

具名control schema与evaluation/trace SHA核准。最新24个normal窗口：轮目标每步变化RMS8.7715/9.6399rad/s、力矩变号584.375/549.125次、触限25.908/38.625%、最长连续触限均值.0292/.0404秒。B2508normal对应.0523/.0761rad/s、0/2.75次、触限0。全部为100Hz latest held PD力矩，不是完整PD频谱。Swing8env受控33interval=.33秒后倾角终止；env0曾双腿收短到.233/.225m、峰高.331m，不能概括成没有收腿或真正耗尽2.5秒期限。离线新增成本重放只核单位量级，不证明训练因果。

## 配方与课程

A：v8沿v7仅加首次入口后实际轮目标变化成本−.2×mean((Δwheel/10rad/s)^2)/秒，dt一次。normal评估24env，100/200/300；连续两次完整通过可提前结束，300后其他项有效且触限下降≥20%可再一块，累计formal最多600随后强制进入动态课程。退化时保留原update300候选。

B：v9真实Swing→B50至.50s→B250→学生永久接管。前缀1.80/1.50/1.20/1.00/.80/.65/.50/.40/.25/.10/0秒，32current/16previous/8normal/8unassisted；第一级重复1.80单列。每个模型原生输入/尺度，实体目标只解码一次，教师/学生上一实际目标连续；交接不reset、不清速度、不沉降，Actor不读教师/前缀时间。保存真实Swing初始高度基准，Critic三个计时仅代表学生后缀。Huber/弱mirror/轮平滑只在入口后启用。最终0前缀通过→32独立原生/新小yaw复核→56Swing/8normal无教师巩固最多300→再认证；保留已认证模型，不自动采用latest。

教师和初始化步骤不更新Actor/entropy/BC，也不拟合Critic；真实时间序列与GAE仍完整。全无学生样本minibatch两网grad None，Adam不推进。任务成功只有完整Certificate；辅助动态后缀通过不生成独立Swingaccepted。

新reward首次Critic/Adam新建、5次warmup、12次smoke；同配方后续块恢复Actor/Critic/Adam、Python/NumPy/Torch CPU/CUDA RNG、累计update、课程状态和认证集合，不重做warmup或smoke。实际环境重启reset单列，绝不声称恢复PhysX瞬时状态。公共校验严格消费同配方checkpoint与实际smoke证书，和工程故障恢复证书分开。

晋级24/24两次独立评估且中间至少一次PPO更新；评估100次一次，300检查旧后缀/normal/unassisted。失败计数1→0→1。3块无实质改善按用户定义一次完整最佳状态回退、同间隔最多两级中间前缀，仍停滞为NEEDS_DESIGN，不写预算耗尽。阶段A不受该规则无限延长。

## 工程交付范围

新增students/course.py纯课程决策、course_requests.py身份/续训边界、course_io.py公共准备与owner结算续块、course_runtime.py共享物理动态前缀、resume.py完整状态、course_statistics.py紧凑轮执行统计、course_certification.py既有supervisor独立认证。增量改recovery_task/training_recipe/model/ppo/requests/evaluator/training/training_evidence，以及shared controlled_ppo/wiring/stand_chain/supervisor/register_authorization。公共prepare_student_recovery_ppo新增--continuous-course，不另建launcher。旧150D/1182D/31D旧配方保持。

任务manifest与累计账本：isolated/recovery_continuous_course_20261012/task。首块09_56 recovery_course_a_prefix0_block0000。STOP文件是用户停止的可审计入口；停止后不启动下一块。未启用消息通知。修改只限本项目，教师/历史实验只读，未commit/push。

## 实际CPU与提交验证

相关62通过；全CPU895通过/22错误，对比修改前873通过的22个Motion engineering recovery fixture，错误ID和configure.py契约原因逐项相同，无新增失败；未放宽SHA或改Motion配方。最终冻结PORTABLE32通过，实际冻结schema与public supervisor零写plan通过。CPU optimizer验证只在内存副本执行，不计在线PPO，未新增BC。源码/教师/source SHA核准，历史run/ledger未改。

首块新spec configs/experiments/2026_10_12-09_56__recovery_course_a_prefix0_block0000/spec.json；task-derived授权经公共register_authorization登记有限312次（smoke12/formal300），task总额度仍null。GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES=0→cuda:0，共享；一次提交前可用32627MiB，要求至少4096MiB，非持续可用保证。check READY，已public supervisor --launch，正在一次≤600秒事件握手；实际阶段以submission.json返回为准，不轮询日志/进程/GPU。后续块由stand_chain owner结算并按持续授权调用公共supervisor，重新核验资源，非新watcher。

## 实际启动结果（仅一次握手）

source_eval已COMPLETED，学生normal0/24、Swing0/8、B250正常基线8/8，工程有效。smoke已COMPLETED，12更新/98304samples/有效Actor57344，wiring_certificate PASSED无错误，正常站姿行为0/8；能力未通过不阻塞formal。首次有界600秒内事件握手确认FORMAL actual_updates=1（Critic warmup）、started=true、identity_verified=true、formal_first_update_verified=true。formal exact attempt 0e19917c92684a9fa2a17d1879b3d61d。此为握手时事实，不推断后续实时更新数。

共享GPU0/冻结命令/session/实际worker与trainer身份均匹配；没有停止其他任务。启动JSON及已完成阶段摘要在isolated/recovery_continuous_course_20261012/submission.json、startup_completed_phases.json。现在由owner执行剩余块、评估、保存、结算和课程续训；worker不轮询，不自动重试工程错误。动态前缀接线经CPU验证，真实B阶段首次source/12smoke仍将核验教师完整组合与真实交接；尚不能宣称学生已接住任何辅助后缀或无教师Swing。
