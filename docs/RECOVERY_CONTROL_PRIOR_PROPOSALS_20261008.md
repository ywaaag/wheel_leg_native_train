# Recovery控制先验迁移：两条独立CPU候选

## 范围与证据

用户同意准备“动作mean越界”和“低位奖励”单变量方案，并要求参考参考文献.md、开源文档.md。本轮仅文档/CPU设计与实际轨迹量级核算，不修改runtime/trainer/spec，不启动仿真/PPO，不生成可提交授权账本。原B25、USD/控制接口/150D/左优先动作/40与5.5Nm保持。

本地开源文档.md是第13.6节Recovery的摘要，含Init/TurnOver/YawFront/Swing/DrawBack/Return、腿长/摆角规划和轮力矩Recovery置零；没有仓库URL、版本/commit、作者或原报告链接。用户称其为浙江大学实机部署材料，这一身份与实机证据本轮未独立确认。web搜索接口返回404；GitHub检索一次返回无匹配，后续DNS失败。因此不将摘要等同核验过的浙江大学原代码，不伪造外部引用；有原仓库/文档链接后再核查函数实现/硬件参数。

参考文献.md是思路材料，无可追溯作者/DOI。关于“纯端到端被全行业抛弃”“门控彻底封死reward hacking”“PBRS/CLF消除局部最优”“逆向课程必然解决”的绝对结论不采用。本项目已有原生关节位置/轮速度目标＋PD，不是raw torque RL；已有1/5/10ms多时间尺度控制，不需为了材料换成WBC/LQR。Recovery没有velocity tracking正奖励，不接受“趴地偷速度reward”的根因解释。

## 可迁移和不宜直接迁移

| 摘要做法 | 本项目可用方式 | 边界 |
|---|---|---|
| Swing→DrawBack→Return按几何/接触/姿态判定 | 事件划分、支撑几何诊断、课程及条件化奖励 | 不硬切控制权，不把预定顺序当已经存在可达路径 |
| DrawBack收短腿、摆到竖直 | 只作轮心—hip相对位置/实测长度/闭链支路的诊断假说 | 不直接复制l_min=.10m、l_max=.33m或虚拟腿角，不增加虚拟腿控制映射 |
| Recovery期间轮力矩置零 | 独立检验“减少低位轮驱动负担”的弱cost | zero effort不是wheel target=0或制动；不强制轮矩/轮动作归零，不改Kv/限矩 |
| Return锁存当前测量以减少突跳 | 诊断首步target与实际q、限幅及history/previous action | 不加static trim、动作bias轨迹或隐式teacher |
| 双腿同步与水平门限 | 保留镜像/轮心/接触的诊断及终态水平证书 | 未有因果证据不加强镜像或raw动作相等成本 |
| 重力投影判定 | 当前观测已有projected gravity，核验轴/测量语义 | 加速度计在动态中包含比力，不可无条件当真实重力；不复制原IMU阈值 |

奖励工程可用原则是明确状态/量纲、bounded terms、按实际trajectory校准、continuous dt乘一次、once event不乘dt、来源回归独立验证。Gaussian或二次成本没有普遍优劣，PPO不通过仿真器reward曲线直接求动作梯度。PBRS的gammaPhi(s')−Phi(s)若要实现须处理terminal/time-limit/reset边界；本轮非PBRS，不宣称保持最优策略或CLF稳定证明。单纯正向height差可能奖励反复抬升，暂不新增。

## 方案A：Swing前段轮mean越界辅助损失，优先准备

定义在实际参与当前PPO训练的Swing/pre_entry受控样本：

L_aux = .001 * mean_samples( mean_two_wheels( relu(abs(mu_raw) - .9)^2 ) )

eligibility必须来自实际family/初始化完成/未确认首次入口的pre-action metadata，不从高度猜family；来源DrawBack/R0样本mask=0。margin=.9为留出.1单位裁剪余量的提案，未运行验证；只轮2/5，腿/std/mean输出映射/物理动作裁剪均不改。是一项优化辅助损失，不是环境reward、不乘policy dt，不改变source checkpoint或raw动作/控制器。计算分母必须明确为当前minibatch全部有效受控sample，不能由短Swing样本单独平均后无意放大权重；诊断按family均值另报。

本次确定性Swing 240受控sample，raw excess mean .89975，lambda=.001时每Swing sample loss约.00089975；相同输入CPU梯度方向对负越界mean为负，梯度下降向上推动。旧DrawBack/R0样本loss及输出梯度均0，但更新共享网络仍可能改变旧能力，不能称无损保证。系数仅可审核的起始候选：没有真实PPO gradient/Adam步骤，不能证明它与PPO项相称或一次更新有效。

先准备真实公开optimizer hook的接线/metadata mask/单batch梯度量级测试及独立spec，继承当前固定26/25/13课、B25全部权重/std/Adam/RNG语义，奖励和控制完全保持。不得将本次CPU output梯度称为真实PPO学习。短块建议smoke10/formal50、25/50三组验收，时间/样本需新明确声明；只在实际runtime授权后运行。若无改善不自动加lambda或续latest。

## 方案B：弱低位物理轮驱动力矩cost，独立后备

raw = g(h) * mean_two_wheels((tau_physical_clipped / 5.5Nm)^2)
g(h) = clamp(1 − (h − .20m)/(.32m − .20m),0,1)
r = −.1/秒 * raw * .01秒

必须使用现有physical clipped torque，不用PD请求或raw wheel speed代替；只改这一项reward，现有其他项/auxiliary/std/actor初始化/控制/终止不改，不同时启方案A。阈值复用现有低位wheel-spin gate，只为减少新变量，不称已证明最优。tau在物理限幅内，raw在[0,1]，单步惩罚最大.001，不硬锁/制动，不模拟传统零轮矩控制。

对真实记录反事实评分：Swing增加−.06609/秒、每env约−.01983，约为lift累计的9.83%；原连续累计约+.3367、终止事件−1。DrawBack增加每env约−.01012、约为其lift累计的.047%，R0为0。不得把这些反事实分数当新策略效果，不改历史reward。

mean越界后执行目标和力矩可能固定在同一限幅，方案B在该区域对不同rawmean动作的reward辨别力有限；仅期待通过不同动作/状态的回报改变策略，不保证可脱离饱和。因此优先方案A；方案B作为传统“减少非必要轮驱动”机制的独立检验，不因为材料实机成功就优先换整个控制架构。

## 输出与验证

纯CPU未接线函数src/native_stand/recovery/proposal_costs.py、测试tests/test_recovery_proposal_costs.py（PORTABLE）2 passed，验证输出梯度方向、仅轮/指定mask作用、gate边界、符号独立及dt单次。首次测试发现full=.32边界浮点残差，加入明确边界归零，已通过。没有optimizer.step，没有改actor/std/Adam。

复用脚本scripts/calibrate_recovery_control_priors.py --run <input-capture PPO0> --output-dir <新目录>核验原始SHA，在CPU计算两个独立cost与输出梯度。最终证据isolated/recovery_control_priors_calibration_final_20261008/calibration.json；前一核算保留，未覆盖。JSON清楚标runnable=false及缺少接线/独立预算，非新训练spec，不能提交。

本轮变更文件：上述函数/测试/脚本/报告，docs/RECOVERY_STANDING_PLAN.md、STATUS.md、TOOL_INDEX.md。不删除旧脚本、不写runs或历史spec，不检查活动训练。下一实际任务首先完成A接口CPU接线与梯度量级审核；B单独保留，不运行并列双臂或大预算。

## 当前执行顺序

2026-10-08后续用户要求明确计划：下一先完成方案A真实optimizer hook/metadata/分母/gradient-clip接线与CPU审核，方案B保持独立后备。统一执行步骤和建议runtime预算（source≤900秒、smoke10/≤900秒、formal≤50/≤5400秒，10/25/50评估，总60更新/491520样本、chain≤7260秒）只维护RECOVERY_STANDING_PLAN第8.6节。预算提案未授权，当前函数/核算不等于runnable spec；本次仅更新文档。
