# Failure-zero学生：动态衔接与短历史离线复盘

本轮授权范围：读取已有证据、CPU离线分析/回归、源码接线和下一声明准备；新增仿真、在线PPO、BC优化均0。旧run/checkpoint/spec/evaluation/ledger只读，不自动续训。

## 实际结果与字段核验

14_32 failure_zero链COMPLETED：smoke12/formal100，917504原始样本，formal有效Actor436553，链1655.58秒；25/50/100均无入口0/32，最终复核0/32，来源BC按原同协议排名保留。取消罚分改变了行为，尚未实现完整恢复。

|模型|评分episode|峰高均值m|受控时长均值s|倾角终止|入口|
|---|---:|---:|---:|---:|---:|
|来源BC|32|.3027|.6625|32|0|
|new25|32|.3264|.2700|32|0|
|new50|32|.3458|.3297|32|0|
|new100|32|.4077|.8022|32|0|
|原生教师组合|8|.3946|11.7275|0|8|

全部学生曾双侧同时收短≤.34m，不能以此宣布支点和站立已解决。new100已抬升并发生回落，瓶颈不是完全没有向上动作。

复盘工具核验冻结reward版本、USD身份、evaluation/trace/checkpoint SHA、具名schema、首episode与受控时间连续性；16组31D输入/执行缓存重建最大误差2.3841858e-7。raw/weighted/dt/event重放按failure_zero真实配方计算，不套上一轮−1事件。每次更新均无训练入口/保持样本，原入口后的W/V成本全为0，不能解释为这些成本在过渡阶段抑制起身。

逐环境/窗口/回报：isolated/student_failure_zero_dynamics_20261011/trajectory_review/review.json。动态锚点、接触、请求/执行目标及100Hz力矩：history_probe/dynamics_history_review.json。图teacher_student_dynamics.png仅env0描述，不作因果认证。

## 动态事件顺序

教师原生env0：约.52秒水平角速度>3rad/s，.54秒倾角>.30rad；.63秒达到.30m，此时pitch约−.542rad、body X角速度约−.579rad/s，之后抬升并收稳，始终未到诊断tilt .60rad。起身本来需要动态倾斜，不能把保持水平gate套到全过程。

new100原生env0：.18秒水平角速度>3rad/s，.21秒tilt>.30rad；.30m锚点仍可抬升，但.50–.75秒高度回落、pitch转正、两轮目标由接近−100转向+100rad/s。约.68秒轮请求力矩125.56/121.35Nm，实际均限为5.5Nm；随后存在双轮失触/非对称接触和角速度放大，.73秒tilt>.60rad，最终严重倾角终止。限矩执行符合原契约，不能将请求大当成实际超限，也不能由事件先后证明轮切换唯一致因。

new25/new50分别更早进入大角速度/倾角失败。取消−1确实打破低位拖延，但更加冲高并不等于完成转腿、落地和收稳。早期瞬时失触可在.01秒出现，因此“首次失触”不是可靠的唯一失稳起点，需结合之后的高度、角速度与目标时间序列。

## 短历史是否值得立即迁移

按总纲4.7，检查当前帧与当前加前四帧（40ms）的邻近标签检索；只用完整连续五帧、按episode隔离train/validation/test，阶段/episode等额抽点。不执行optimizer、不训练模型。历史按原轨迹构造，不混episode，不添加教师ID或切换时刻。

验证集转腿段四腿MAE：当前帧.00467rad，短历史.01363rad；两轮MAE .04496→.13488rad/s。测试描述结果转腿段四腿.00468→.00921rad；动态收稳轮目标MAE也未一致改善。准备段验证检索明显改善，但在测试描述组未重现同等级收益。它只是有限数据上的距离检索，不能证明网络最优拟合或闭环充分性。

教师切换边界相邻当前31D输入L2中位数.00318，而五帧本体历史L2也仅.00861；动作有明显跳变。不能据此称输入相同/不可学，也不能假定加四帧自然消除教师固定切换的标签不连续。

因此暂不迁移接口、不新增阶段输入/GRU、不启动历史BC。若以后实现5×(22+1 valid)+9任务=124D、128→64→32→6，Actor约26534参数、106136 bytes、26304 MAC；这只是假设资源核算，尚无板卡认证，短历史runtime未实现。

## 下一单变量候选：抬升后的过大角速度成本

保持31D、同一个Actor、BC来源、failure_once=0、原reward六项、PD/物理/动作/std/LR/GAE、起点和评分不变。只增加入口前一项成本：

u=clamp((当前post高度−.20)/.05,0,1)
gate=u²(3−2u)
omega=sqrt(body_omega_X²+body_omega_Z²)
raw=gate × min(relu(omega−3)²,9)，仅学生受控、非runtime fault、尚未首次入口确认时有效。
新增密度=−.20 × raw；最终连续奖励再乘dt=.01一次。

高度≤.20m无成本；.20–.25m平滑启用；≤3rad/s无成本，峰值密度−1.8分/秒。无需双轮接触或特定姿态，无仿真量进入Actor；保持阶段仍沿原W/V，避免叠加重复成本。使用当前高度，不引入需要Critic额外观测的隐式“已抬升”锁存状态。

原生8个episode重放新增平均总成本：教师−.03909、BC−.10482、new25−.15119、new50−.09930、new100−.13472。teacher总回报约64.5，说明该成本量级没有在已测成功轨迹上占据主要总回报；并非对探索梯度或所有合法路径的保证。具体参数按这些轨迹量级冻结，不在运行中自动调整。

new recipe student_recovery_ppo_lift_rate_v3 / reward student_recovery_reward_lift_rate_v3。额外raw/density/dt在update轻量统计及选定rollout分别记录；旧v1/v2六项与事件保持原值。通过现有严格recipe验证、runtime、公共训练循环/PPO工厂及checkpoint加载，不另建trainer。

从原BC固定SHA7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470重新开始，不从new100失败分支继承。选模仍看完整通过、入口、首次固定窗口前缀，不用峰高/平均奖励。若减少角速度但重新低位等待，或仍冲高后翻倒，明确未跨瓶颈；不自动增加成本、扩大std或长训。

## 验证、声明和授权

相关CPU34项通过；冻结PORTABLE21项通过；全CPU828passed/22errors，22项ID及configure.py旧fixture SHA原因与上一基线一致，未放宽SHA。随后新增recipe加载版本覆盖包含在相关34项。实际共享父类构造覆盖v1/v2/v3；reward dt、deadband、轴、cap、初始化/故障mask、入口退场、旧reward不变与历史跨episode/缺帧拒绝已测。

15_25新spec/独立budget/poses/完整发布标记：configs/experiments/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc。UNAUTHORIZED、零used/attempt、无run，零写plan唯一缺项为新物理授权。预算建议source40episode/900秒＋smoke12/900秒＋formal100/5400秒，总112更新917504样本、最多176评分episode、7200秒/2GiB。GPU0共享仅是待申请范围，准备默认exclusive；获批准后实际CLI明确shared并核验UUID/资源/会话。

准确命令维护TOOL_INDEX；本轮无CPU BC、无新仿真/PPO/GUI，不commit/push，不覆盖历史证据。


## 15_25新授权后的实际提交快照

本次用户明确授权已通过公共register_authorization登记；204项冻结验证输入无漂移，来源SHA匹配。GPU0 UUID为GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES=0→cuda:0，CLI显式shared，资源检查READY，无抢占/停止其他任务/自动换卡。只提交一次，完成一次600秒上限事件握手。

来源评估COMPLETED：学生四组0/32、教师原生组合8/8，无工程failure；前清理113.7863秒。smoke COMPLETED：12更新98304samples、41062有效Actor样本，工程wiring_certificate PASSED/errors=[]，行为0/8；前清理154.5623秒。未将行为失败写成能力通过，也未以其阻止formal。

握手FORMAL，attempt02c233a243d1464f9d4c86002ac53454，actual_updates=1，started=true、identity_verified=true、formal_first_update_verified=true。首更新属于前5次Critic warmup，不代表formal Actor已更新；formal从固定BC重新初始化，不继承smoke末模型。

既有owner继续按formal100/5400秒预算执行25/50/100完整评估、选模、最终复核和exact-ID结算。worker握手后不轮询log/progress/PID/GPU、不守候、不自动重试/追加预算/长训。notifications保持disabled。本节是启动快照，不是formal终态或能力认证。

授权后spec SHA为61e612a1af2e1730a5fb77bc83e3faf41bd03d6a1794a3e4c20b0bab16f4f3ac；机器证据见isolated/student_lift_rate_submission_20261011/authorization_result.json、check_submission.json、launch_handshake.json、completed_stage_readback.json、submission_delivery.json。前文UNAUTHORIZED是发布准备时状态，不能用于推断未来运行授权。
