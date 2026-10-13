# Recovery下一交付：回到RL，审核短时腿探索中心辅助目标

2026-10-09用户要求下一交付以RL自主起身为主。暂停扩展手写动态动作、physics接触adapter和固定mixture分支；已完成的几何/事件审核仅作为训练假说依据，不当作已验证示教或runtime控制。

## 核心问题与单变量

当前有界轮mean已明显解除轮探索别名，旧两组保持；Swing腿mean远离当前构型，两hip局部收短边界约14–16std。仅beta/std/更多迭代未产生有效收腿覆盖。因此下一优先CPU审核一个训练期辅助目标：只在Swing初始化有效、受控前100ms，软约束四腿actor均值不要远离当前实体q，帮助探索中心接近当前可达构型，再由原PPO回报选择摆腿/收腿动作。

候选作用在训练loss，不覆盖env动作、不翻左右符号、不加入手写时序或固定收腿目标。只用150D已有q−reference信息，四腿偏移均对称处理，**不将CPU局部[+,+,−,+]方向强行写入actor**。这不是纯reward-PPO，而是明确的PPO＋探索中心正则实验；不能隐藏名称或宣称几何示教来自成功轨迹。

候选物理误差e_i=1.6*mu_leg_i−(q_i−reference_i)，当前frame qpart/2给出后项。L_aux=lambda*mean_i(relu(|e_i|−.15rad)^2)，仅eligible样本计算、分母全部受控transition固定。使用未clip腿mean，避免actionclip区梯度消失；四腿mean仍原坐标，两个轮保持现有boundedmean。±.15rad只是来自已核验局部几何的起始候选宽度，不代表这个盒内所有动作都安全/可执行。

初步mask为Swing受控clock前.10s，排除init/failure/entry后；按实际pre-actionclock明确闭开区间。训练外不使用mask去改actor输出，部署actor仍独立输出。限制只出现在loss也会通过共享网络影响旧组，不能宣称无损。

## 为何这个候选与此前不同

此前wheelmean辅助只促轮输出回界内；腿探索问题尚未以此方式干预。固定mixture第二分量无可学习中心、难教原actor；这里loss直接作用原actor mean，使它能够收到清晰梯度。currentqresidual改了部署动作reference并破坏旧target，这里保持原target映射。该候选仍可能让策略保守驻留/削弱所需快速摆腿，必须与真正动态起身指标共同验证，而不是仅看误差减小。

## 下一交付应包含的CPU结果

1. 在14_00真实latestnew25数据上，按起步时相输出辅助loss、四腿mean梯度方向、现有原PPO代理目标的actor梯度及两者夹角/量级。只重算一个冻结batch梯度，不执行optimizer.step、不导出模型。需明确这不是历史多epoch训练精确重放。
2. 固定宽度.15rad，审核多个lambda量级但只选一个候选，说明对当前Adam尺度与PPOactorclip的影响；没有实际优化梯度就不能用reward比例代替gradient比例。
3. 检查init/failed/旧组/时窗外loss严格0、来源actorcriticAdam未变、noextraRNG/forwardcache污染，代码默认关闭。旧DrawBack/R0输入上的输出变化只能通过真实更新/评估确认，梯度mask为0并不保证网络不影响旧任务。
4. 反事实采样覆盖只作信号评估，不能宣称可达或成功。若loss主导PPO或完全抑制必要动作，不进入训练，明确否决原因，不自动循环增加lambda。

## 有条件的首块RL实验建议（尚未授权/发布）

CPU审核通过后，准备新独立同源A/B：A=有界轮mean＋现有beta.3的原配方，B=只增加上述短时腿中心loss。优先来源10_58 new25（SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c）绑定原boundedmean spec，作为有完整两旧组证据的实验来源；认证原B25仍保留fallback。需新source复验且分布身份明确，不直接继承旧run预算。

每臂smoke10、formal最多25，10/25联合验收Swing/DrawBack/R0；两臂同起点、采样/std/Adam/RNG/物理/reward，只有loss开关不同。阶段各自严格warmstart来源，不拿smoke模型拼接。两臂共最多70更新/573440samples，建议source900/smoke900/formal3600秒每臂，另清理余量；这些只是待审预算，不授予运行。是否能复用同身份来源证书由公共source_evidence核准，不绕过。

主要读回：随机腿实际mean/sample/target覆盖、双侧长度与轮心支点转移、lift/entry/完整10秒保持/tilt/contact，及旧两组完整证书；loss更小、局部组合更多、轮clip更低均不单独算成功。旧组连续两次full退化停止该臂，来源/early/latest/accepted分开。25更新有有效行为趋势才考虑新授权延长，不自动做100/500。

## 当前状态与边界

本交付是具体RL方案草案，辅助loss尚未实现/标定，A/B spec/ledger尚未发布，无新仿真/PPO授权；本轮只编辑文档。现有手写动态diagnostic草案留作参考，不继续默认开发、不执行。没有静态沉降中间态课程、没有成功Swing示教、没有架构大重构、hiddencontrol/LQR/外力/限矩修改。

下一项实际工作应是一次有限CPU梯度/量级审核和是否采用的明确结论，而不是新增一轮传感器或动作生成工具。若候选CPU通过，再以具体配方/预算请求训练授权。
