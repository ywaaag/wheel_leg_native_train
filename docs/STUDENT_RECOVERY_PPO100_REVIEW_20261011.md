# 同一31D Recovery学生PPO100：事件与奖励复盘

本次仅已有数据CPU分析、版本化工程与独立声明准备。新增仿真/PPO/BC优化均为0，旧run、checkpoint、evaluation、ledger和冻结副本未修改。

## 原始身份与时间窗口

来源链：runs/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc。BC来源SHA为7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470。学生/教师数据均核验evaluation、trace与checkpoint SHA；字段明确为recovery_policy_trace_v1，消费具名STATE/CONTROL/POSTURE，不靠尺寸猜轴。

只分析首episode，按pre-action actor_valid对齐。初始化结束后首个动作执行后的状态记作0.01秒；不将程序时间当作受控时间。学生BC及25/50/100各四组32episode；教师是同轮原生Swing组合8episode，不能声称教师有四组同轮认证。逐环境、窗口0–.25/.25–.50/.50–.75/.75–1/1–2.5秒和所有源SHA保存在isolated/student_recovery_task_ppo_review_verified_20261011/review.json。时轴对齐只是描述差异，不是同状态的因果干预。

## 观测和真实更新核查

16组学生trace的31D输入由pre root/joint、四腿+两轮previous_targets、声明reference与坐标重建，最大误差2.3841858e-7；Recovery标识与0.40m命令一致。暂未发现输入时相/目标缓存接线错误，不能由此证明31D总是充分。

formal前5更新仅Critic，随后95次Actor/Critic真实更新；有效Actor样本664895，BC更新0，std固定。全部训练入口/保持事件为0，保持段采样为0。选定rollout1/6/25/100中reward=连续dt项+事件项最大差1.86e-9；dt应用一次，初始化奖励0，return/value/advantage有限。mask有效不等于已有高质量起身经验。

## 行为改变

下表高度为各episode峰值的均值；持续时间为受控首episode平均长度。

|策略|episode|双侧曾同时≤.34m|平均峰高m|受控时长s|入口|完整通过|
|---|---:|---:|---:|---:|---:|---:|
|BC来源|32|32|.3027|.6625|0|0|
|update25|32|32|.1702|2.50|0|0|
|update50|32|32|.1689|2.50|0|0|
|update100|32|32|.1695|2.50|0|0|
|冻结教师组合|8|8|.3946|11.7275|8|8|

BC32项均倾角终止；25/50/100各32项均拖到2.5秒入口deadline，未出现倾角终止。由此本轮不是完全没学到变化，而是学成低位等待/运动。双侧收短存在不能代替有效支撑、转腿和抬升。BC中22/32曾达到.30m，仍没有水平接触入口。

原生env0：update100相对BC腿目标差>.10rad始于.01秒，轮目标差>10rad/s始于.05秒，pitch/roll差>.05rad始于.08秒，高度差>1cm始于.56秒。25/50也先改动作再改姿态，随后丢失抬升。阈值是本次离线定位定义，不是评分或因果证据。逐环境数据避免只用env0推断整体。

成功教师在.50–.75秒仍允许动态倾斜与接触变化，但转腿抬升后进入收稳；学生更新后没有进入该动态区域。不能把轮目标大直接解释为打滑，也不能仅凭动作差异确定轮通道是唯一原因。

## 奖励偏好及单变量理由

以下均是固定轨迹离线重放，从首个受控interval计算完整episode折扣回报；不是实际Adam贡献或对未来训练的保证。

|策略|未折扣总回报|gamma=.99总回报|其中失败事件贡献|去掉失败事件后的gamma回报|
|---|---:|---:|---:|---:|
|BC|−.8666|−.4446|−.5191|+.07447|
|update25|−.9617|−.06987|−.08188|+.01201|
|update50|−1.0144|−.08881|−.08188|−.00694|
|update100|−1.0153|−.09003|−.08188|−.00815|
|教师组合|+64.5004|+2.38169|0|+2.38169|

BC抬升失败的连续回报高于低位等待，但−1失败事件早发生，其折扣负值大。失败拖到2.5秒时只剩约−.08188，使低位轨迹的折扣总回报反而优于BC。这里存在可测的“延迟失败更划算”偏好，尽管没有低位存活正奖励。尚未证明该项是唯一根因；总回报比较也不等于参数梯度比较。

训练H/S原始均值从更新1–5的约.04688/.00362降到51–100的.00258/.000215；末期effort与target_change密度成本已大于H/S正项。W/V入口后才启用，实际全程为0，所以本轮不能归因为入口前速度惩罚压制起身。

固定教师输入上的逐腿/逐轮MAE/P95/max及每个episode教师切换前后各5帧保存于isolated/student_recovery_failure_zero_preparation_20261011/fixed_input_comparison.json。BC准备阶段右hip MAE约.0774rad，update100为.1457rad；更新后腿输出发生明显迁移。该检查使用已保存31条相近示教，不增加独立物理经验，未做BC训练，不能宣布短历史一定能解决。

## 下一独立候选：仅取消失败事件罚分

新recipe student_recovery_ppo_failure_zero_v2；reward student_recovery_reward_failure_zero_v2。唯一主要学习变化是failure_once从−1到0。连续6项、entry+1、success+10、gamma/lambda、LR、std、网络、初态、接口与PD均保持。版本字段和源码身份同步变化，仅用于准确声明此干预。

失败事件与终止仍记录、仍结束episode；物理/数值保护、2.5秒入口deadline、首次入口后固定10秒及全部验收不变。不是放宽失败gate，也不增加存活奖励。旧v1默认行为和checkpoint加载保持。

从原BC来源重新开始，不从25/50/100低位候选续训；Critic和PPO Adam新建，前5更新仅Critic；BC0、64×128、smoke/formal独立来源。候选仍由完整通过数、入口数、首次窗口保持前缀和更早保存点排序，不靠reward晋级。

这项消融可能诱发更早失败以回避连续成本，须记录早倾倒率、平均结束时刻、抬升峰值和入口；如果只是恢复早倾倒、仍无入口，则本轮未解决瓶颈，不自动增权/续训。下一再依据实际轨迹决定动作覆盖、局部示教或当前帧加四帧历史，不同时叠加。

## 发布、验证与待授权范围

configs/experiments/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc/spec.json及独立budget/poses/发布标记已生成。账本UNAUTHORIZED，所有used=0，attempts为空，无run。零写supervisor plan唯一错误为新物理预算未授权；配置通过不是提交就绪。

预算保持可比：source40episode/900秒；smoke12更新98304样本/900秒；formal100更新819200样本/5400秒，含25/50/100评估与最终32episode复核。总112更新917504样本、评分最多176episode、7200秒/2GiB。拟申请物理GPU0共享，准备器默认资源exclusive不构成共享权限，实际批准后必须CLI显式shared、核验UUID/current session与资源，再公共supervisor一次提交。

相关51项CPU通过；冻结PORTABLE28项通过。全量820passed/22errors，与13_35提交前基线22项错误ID及configure SHA fixture原因逐项一致，未放宽生产SHA。新增checkpoint版本CPU回归随后包含于51项相关验证。共享工程worker同时改进准备器和异常/存储工具，本轮保留这些dirty changes，不将其算作本轮行为干预。

本轮改动：review_student_recovery_task_ppo.py；recovery_task/training_recipe/runtime/evaluator/ppo/model的显式新reward版本消费；prepare_student_recovery_ppo的--failure-event-zero选项；failure_event_ablation测试及现有真实父类/保存加载测试的版本覆盖。未改历史文件、不commit/push。准确命令仅维护TOOL_INDEX，状态维护STATUS。


## 新批准后的实际14_32提交

用户本次批准该单变量运行；公共register_authorization绑定独立spec/budget与当前会话，204项冻结验证输入无漂移。GPU0 UUID为GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES=0→cuda:0，CLI显式shared；资源检查READY，现有进程未停止，无自动换卡。只提交一次并完成一次600秒上限事件握手。

来源评估COMPLETED，四组学生0/32，教师原生组合8/8，工程无fault；前清理113.8733秒。smoke COMPLETED：12更新98304samples、36739有效Actor样本，wiring_certificate PASSED/errors=[]，行为0/8；前清理155.4904秒。完整恢复未学会不阻塞formal。

握手返回FORMAL，formal attempt3f0e39b4d91540cf865d0686bc542fc8，实际更新1、started=true、identity_verified=true、formal_first_update_verified=true。第1次属于前5次Critic warmup，不能称formal Actor已经更新。formal仍从原BC独立初始化，不继承smoke末权重。

后续由既有owner按formal100/5400秒预算执行25/50/100评估、选模、最终复核与结算。worker不查formal日志/进度/PID/GPU，不守候、不重试、不追加或长训。notifications仍disabled；终态需读取实际报告，不把握手等同完成。授权后spec SHA为b22de1a28af230d7377ddd324091df560839a4cc0f8d97b4e9a03d5af4efdb59。

提交机器证据：isolated/student_recovery_failure_zero_submission_20261011/authorization_result.json、check_submission.json、launch_handshake.json、completed_stage_readback.json、submission_delivery.json。前文UNAUTHORIZED描述仅为准备时快照，当前已有本次明确运行批准，不授权链结束后的新运行。
