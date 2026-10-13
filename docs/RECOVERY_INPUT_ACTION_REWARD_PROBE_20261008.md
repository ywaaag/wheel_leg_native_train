# Recovery B25 真实输入—动作—奖励联合诊断

## 实验与边界

用户批准900秒PPO0提案，实验2026_10_8-17_39__recovery_b25_input_action_reward_probe_ppo0，GPU0 shared，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda:0；原Swing、DrawBack、R0分别64env布局/8scored，seed104、最多23秒/请求，确定性actor执行。来源Recovery B25 SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44（非Motion B250）。奖励/终止/USD/控制/观测/动作尺度不改，不重复失败episode、不执行随机动作/PPO/optimizer，不停止其他任务、外部通知禁用。

终态COMPLETED，evaluate1，实际结算147.458秒（child terminal147.014秒，区别包含退出清理）。Swing0/8、DrawBack/R0各8/8；有效控制记录240/8687/8802条，初始化另记320/320/0条。三个NPZ分别保存输入、物理状态和runtime分项reward，目录总96.7MiB，低于256MiB；旧run/ledger/checkpoint均未写。

原始run：runs/2026_10_8-17_39__recovery_b25_input_action_reward_probe_ppo0；input_capture_00/01/02.npz及evaluation_00/01/02.json绑定数组SHA、字段布局和源码身份。
最终逐150D统计/时相验证/各组phase reward：isolated/recovery_input_action_reward_final_20261008/review.json。首次离线分析保存在isolated/recovery_input_action_reward_review_20261008，最终新增gate公式读回标注，不覆盖首次报告。

## 1. 观测接线与变化

由真实root quaternion/world angular velocity、主动关节q/dq、command、previous action/reference重算scaled25D：最大误差Swing4.09e-7、DrawBack4.17e-7、R04.36e-7。history最新帧等于current、同episode oldest-to-newest移位最大误差均0。CPU同checkpoint前向重放mean最大误差分别1.43e-6、5.96e-7、2.68e-7。

Swing当前25D除固定command vx/yaw/height三个维度外，其余22维均有时间变化；不存在某个动态字段保持零方差而对应物理输入明显变化的证据。150维按family/phase全部输出mean/variance/min/max/p05/p95，分开episode内时间方差、episode均值间方差、同step环境间方差。History含重复/延迟帧，近常量标记不是观测无用证明。

本次支持“实际字段映射与history接线正确”，不支持“观测已充分”。Height、平移速度、接触、被动分支未直接输入；只沿同一actor失败路径采样不足以认定这些缺失产生必要控制混淆，也不足以排除。没有用插入新观测救本轮实验。

## 2. 策略在Swing状态上的动作裁剪

Swing有效控制窗口未裁剪mean范围按left-first6通道：
- 左hip约−.246..+.359；左active约−1.218..−.158；左轮−2.300..−1.530。
- 右hip约−.056..+.283；右active约−1.026..−.378；右轮−2.225..−1.008。

归一化std分别.05758/.11361/.04886/.05830/.05919/.03884。两轮deterministic mean全程超出−1，因此实际两轮目标都被裁至−100rad/s；左轮mean距最近边界至少10.85个std。
解析Gaussian裁剪概率平均：左轮约100%、右轮98.63%，左active60.18%、右active8.29%。这是沿确定性访问状态计算的解析尾概率，不是实际随机训练采样裁剪率。

DrawBack入口前左轮裁剪概率约9.96%，其余轮接近0；两个旧组保持窗口轮裁剪概率约0。执行action与clip(mean)逐样本吻合（腿约6e-8误差，轮0）。不存在随机采样加入本次控制。

结论：B25在Swing状态的mean落在原输出边界外，是比std标量更直接的证据。继续减小std不会把确定性mean拉回边界内，反而可能减少逃出边界的尾概率；不能将本次失败简单归为std过大。实际两轮固定目标是策略/动作响应线索，不直接认定轮旋转=滑移或唯一致倒机制。

## 3. 奖励在Swing低位的适用性

Swing受控阶段每秒平均runtime贡献：lift+.672、upright+.3999、support+.0833、effort−.0107、joint_margin−.0147、low-height wheel-spin−.0075；action_delta约−.0002。未越.30米，standing_height=0，pitch/roll、vertical-motion和level-angular-motion为0。按冻结gate公式读回，这些height gate激活比例均0；不是字段丢失/日志失接。

每个Swing终止有实际failure_once−1；8env合计一次事件−8，受控约.30秒/episode，连续正收益不能抵消失败事件。不能说机器人通过趴地不动已经获得更高回报，也不能把失败惩罚当完整低位动作方向信号。

DrawBack入口前同样gate已激活约84.86%，R0入口前100%；两个旧组保持阶段height项平台+5/秒、support+.5/秒，成功事件每env+10。来源配方的低位转姿只有lift/upright/support等较粗信号，精细水平/垂向成本直到.30米才激活。这是新任务reward适用性待检验的具体差别；gate设计可能本来就是允许低位转姿，不能未经干预直接宣布应把低位pitch罚项打开。

## 决策与限制

工程观测接线没有发现错误；观测充分性未证实/未否定。优先级转为：Swing分布下mean越界造成的有效动作覆盖，和低位恢复reward的辨别力，两者分别准备单变量，不同时改网络输入/std/reward。下一不再默认继续降低std；先CPU设计与量级核算，若要验证实际随机探索和critic/GAE/update干扰，需要新有界on-policy授权。不能用本次PPO0声称已测学习梯度或优化迁移。

已有动态restore仍可选，不能作为合法Swing继续训练的强制门槛。任何新干预保留来源B25和DrawBack/R0同协议独立评估，不接new75/latest。

## 文件与工程验证

修改recovery/recipe.py、tools/evaluate_checkpoint.py：仅显式input_capture时记录真实输入/物理/reward，actor每步一次；新增domain/input_capture.py（纯显式张量/无IO/RNG）、tests/test_recovery_input_capture.py（PORTABLE）及scripts/review_recovery_input_capture.py。声明验证限定Recovery PPO0、三同源23秒请求、64/8布局及存储上限；CLI写新NPZ/JSON，原始图形/仿真模块不持有文件路径。

CPU全量623 passed（26.40秒）；冻结schema/plan及7PORTABLE测试通过，验证了输入在step前复制、单actor调用、执行不变、无额外RNG、边界/训练拒绝；AST/diff检查通过。实际成功旧组与原PPO0证书一致，未采随机轨迹、未构造optimizer或更改权重。预接触为最后已记录sensor resultant，reset首帧可能是旧/零值，非刷新接触；post为同transition pre-reset。存储上限检查包括当前文件/原数组与本次JSON估计，超限会不完整退出。
