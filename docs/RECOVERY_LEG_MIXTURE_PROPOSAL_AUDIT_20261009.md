# Recovery腿双分量策略候选：CPU覆盖与可学习性审核

用户同意显式多中心policy审核。本轮实现纯CPU候选及精确联合likelihood验证，并在14_00 new25真实332个早期Swing状态上核算覆盖/旧目标代价。没有接共享model/runtime、没有新模拟/采样/optimizer或训练spec。

## 明确分布

一个component选择控制四个腿通道，概率(1−w)沿用policyGaussian，概率w使用center=(q−reference)/1.6，std=候选targetstd/1.6；center由当前150D frame[9:13]/3.2得到，不读取family/隐状态、不添加收短方向符号bias。两个轮仍完全沿用当前有界meanGaussian。action仍reference+1.6*clippedsample，不改变PD或物理映射。

联合log_prob=wheelGaussian + logsumexp(log(1−w)+原四腿Gaussian jointlogprob,log(w)+局部四腿Gaussian jointlogprob)。不能用选中分量单独logprob或四个独立mixture的乘积代替。纯CPU测试与torch MixtureSameFamily联合密度一致，源均值链式梯度有限，center按150D可重算。没有新增采样调用或policy class，schema仅候选说明。

## 覆盖收益

w=.05时四腿同时沿已审核局部方向的概率约.003125；targetstd=.025/.05/.10rad时，沿该方向.025–.15rad局部盒概率约3.17e-5/4.45e-4/6.26e-4，比原约1e-92级明显增加。这是同一prestate单步解析概率，不是多步协同或动力学恢复概率；该方向只是一条充分局部路径。

局部分量std=.05rad时rawlegclip概率极低，主要改变探索中心而非增加冲击噪声。但“近当前q”的探索也可能让腿驻留而非抬升；不证明接触冲量/反弹与支点转移可完成。

## 两项实质阻塞

**旧能力干预频繁且单步大。** 局部currentq目标相对原policy deterministic腿目标，DrawBack最高约[.723,1.503,.831,.838]rad、R0最高约[.735,1.056,.533,.469]rad。w=.05每100控制步至少选中一次的概率99.41%，10秒1000步几乎必然反复选择；不能用加权平均偏移仅几百分之一rad掩盖单步大变化。训练/确定性播放还必须显式选择原component输出、mixturemean或mode，三者不等价；不可静默在eval关闭候选而宣称同一完整policy能力。

**固定局部中心不会自动教原actor。** mixture梯度对原component均值按posterior responsibility加权；局部sample远离原mean（hip边界14–16std）时，原component密度极低，responsibility趋近0。局部center从观测直接算、weight固定，局部分量既无可学习中心也无可学习gate，因此即使局部sample获得正advantage，也未必推动原actor学到该动作。这不是概率错误，而是候选的学习结构不足。仅证明合成sample对logprob有finitegradient，不能保证该grad对每个远中心localaction非零或有实际量级。

## PPO接口尚不完整

当前RSL调用distribution.params、entropy、KL；mixture不能冒用原Gaussian闭式entropy/KL或将混合std当真实Normal。需明确component参数存储、观测条件中心、旧/新logprob、deterministic/export语义和正确entropy/KL估计。若改为learnable第二头/gate或蒸馏先验，网络/Adam/策略容量与来源迁移都改变，超出当前“不做大架构重构”的默认范围，需要具体审查而非直接接线。

## 决策与下一方向

本次固定全局w、固定currentq局部分量**不达到可提交标准**，不启动PPO0或训练。不要把失败的多中心探索包装成已解决；也不为了旧能力采用family隐式开关或env固定动作bias。

建议下一优先重新走有证据的逆向课程路径：审核原DrawBack到已知Swing之间的连续闭链构型及实际动态可恢复区，保持同一policy/控制接口，让有限课程变化逐步覆盖source当前没有的动作状态，而不是直接让不匹配的远距离Swing目标靠噪声探索。当前只有局部几何路径，不含成功Swingtrajectory；先CPU寻找候选路径/机械支撑条件，静态候选只作待验证状态，不冒称来自成功动态轨迹、合法沉降或可恢复。若找不到合适桥接再明确讨论learnablepolicyprior的架构成本。任何物理诊断与训练仍需新独立预算/授权。

## 文件和验证

新增`src/native_stand/recovery/leg_mixture_proposal.py`（纯CPU，无runtime调用）、`tests/test_recovery_leg_mixture_proposal.py`（PORTABLE），2tests通过；新增`scripts/audit_recovery_leg_mixture.py`复用已有覆盖核算，输出`isolated/recovery_leg_mixture_cpu_20261009/audit.json`含输入SHA、9候选覆盖/三family迁移摘要。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX和本报告。未改learning/runtime/控制/网络checkpoint/旧specledger，无仿真/新随机采样/PPO/Git提交/清理。
