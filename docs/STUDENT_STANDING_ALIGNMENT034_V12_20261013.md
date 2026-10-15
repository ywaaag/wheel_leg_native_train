# 31D学生0.34m站立与实体对齐候选v12

用户授权设计奖励、累计1000次PPO、训练不设墙钟截止，随后明确允许GPU0共享。本候选是独立新配方，不改历史v10/旧任务或运行冻结代码，不宣称奖励改造已证实解决根因。

## 来源与训练边界

Actor来源：v10 update100，`runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt`；SHA `bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d`。继承Actor和固定std，reward改变后新Critic/Adam/RNG；每阶段前5次为原有Critic warmup，也计入真实更新预算。31D/40D、128/64/32 Actor、原学生1.5rad/100rad/s实体动作、PD/限矩/USD不变。64normal，零vx/yaw、高度.34，无教师动作、无Swing/运动/Jump训练。

新spec `configs/experiments/2026_10_13-17_16__student_standing034_alignment_v12/spec.json`；授权后SHA `81a6c4d2ecaabb599e78eb0b965e4073d1c3f27538b6d61eee7810d7992d8504`。独立账本smoke12+formal988=1000次、8192000完整rollout samples上限；smoke/formal无墙钟截止（null），不是用巨大秒数伪装不限时。source工程评估900秒保护，不授予额外PPO。用户允许smoke充分验证不意味着另加无限更新；本轮冻结12次以覆盖完整episode，普通行为失败不阻断formal，工程失败停止、不重试。正式数据不继承smoke末尾，从同一v10 Actor重新初始化，不冒称精确续训。

## 奖励设计

版本student_standing_alignment034_v12 / student_standing_alignment_reward_v12。沿既有v11管线，仅新版本分派。Huber(x)=.5x²(|x|<1)，否则|x|-.5，不封顶。

- 高度：+4 exp(-((h-.34)/.04)²)/秒，替换旧slot0。
- 实体关节镜像：-.5 mean(Huber([qLhip+qRhip,qLactive-qRactive]/.20rad))/秒。
- 实体轮心前后差：-.5 Huber(relu(abs(offset)-.01m)/.05m)/秒。offset为实际轮心在水平native forward上的投影差，不用动作相等代替几何。
- 零速：-.5 sum(Huber([vx/.5,vy/.02,yaw/.03]))/秒，替换原附加velocity项。
- 保留原支撑、归一化努力、实际目标变化、入口后角速度及基础velocity项；不增加滤波/补偿/动作投影。
- 新高度、镜像、轮差、零速项在valid student control生效，不因姿态不佳关闭；连续reward乘dt=.01恰一次。
- 本候选entry/success/failure事件reward均0，事件/终止/验收逻辑不取消，避免短期稀疏奖励成为主要收益。

这是一个完整站立reward候选包，不能将效果单独归因某个系数。diagnostics记录新增四项raw/density/dt rollout均值，真实几何/关节由评估trace保存。

## 验收与选优

正常站姿合法初始化不强放.34；策略自行调节。入口2.5秒内连续.20秒满足.34±.02m及原姿态接触，之后固定首1000interval/10秒，不能挑后续好看窗口。

高度MAE≤.02m、峰误差≤.04m；pitch/roll平均绝对≤.10rad、各峰≤.15rad、tilt峰≤.18rad；原双轮合力>2N、净空/闭链/触限≤5%/vx≤.5、vy≤.02、yaw≤.03规则保留。关节镜像两项MAE≤.05rad/P95≤.10rad；额外轮心错位MAE≤.02m/P95≤.04m。工程容差表示可检验的对齐，不宣称数学完全零差。

每100formal更新评估三个normal初态/小yaw组各8例共24例，最终988也评。至少两个不同完整checkpoint相隔100更新均24/24才accepted；能力只指正常站姿0.34站立对齐，不认证起身或运动。同分选优保留早期稳定模型，不以latest替代已评估best。不自动升档、回滚、换种子或加额。

## 运行和工程检查

GPU0共享明确授权，不抢占/切GPU。4GiB链存储上限，单项评估128MiB；触限由现有物理执行器约束，非有限/闭链/控制权/关节保护/保存或账本异常停止。无墙钟截止不取消故障与存储边界。

17初始专项、55奖励/站立/提交回归、43最终选优/接口回归通过；协议附加后20通过，冻结提交副本通过。全量951passed/8skip/22errors：22项均旧Motion工程恢复PROJECT_DATA fixture因当前configure.py SHA变化拒绝，未降低SHA或跳过；本候选不消费该历史恢复证书。新版本schema与实际supervisor check-submission PASS/READY。验证产物`artifacts/standing_alignment034_v12_20261013/`。源检查与smoke实际物理结果仍由后台产生，CPU通过不代表站稳。

主要代码：students/standing_alignment.py（新纯reward）、recovery_task.py（版本分派）、standing_certificate.py（轮差在线/离线共同门槛）、runtime.py（实际几何数据接入）、training_recipe.py（固定配方/预算）、training.py（无墙钟deadline/rollout指标/两次确认）、evaluator.py（有效协议）、command_v6/stand_chain.py（null链墙钟）、tools/register_authorization.py（严格限v12的无墙钟授权）、scripts/prepare_standing_alignment034.py、tests/test_standing_alignment034.py。旧版本默认行为不变。

## 实际后台提交

公共supervisor --launch --handshake-wait-s 30已提交，worker3502115，chain attempt `55d00d5bacc14f2082801a5fffbff913`。一次握手SOURCE_EVAL，submission_verified=true，formal_first_update_verified=false、started=false；说明后台worker已接管来源检查，不代表正式PPO已开始或站立通过。物理GPU0/UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72、CUDA_VISIBLE_DEVICES=0；共享授权和当前session核验通过。

run：`runs/2026_10_13-17_16__student_standing034_alignment_v12/`，日志chain.log/source_eval.log/smoke.log/formal.log，状态chain_progress.json，终态chain_terminal_report.json/completion_report.md。配置同名budget.json；启动证据artifacts目录launch_receipt.json。后台既有owner管理评估、checkpoint、预算与终态；本次交互不轮询、无自动工程重试。旧17_14未提交准备声明保持原样，不花其额度。终态目标为当前会话191bacc3-e5c7-4b8f-ae3d-5677eada837b，不沿用其他worker会话。
