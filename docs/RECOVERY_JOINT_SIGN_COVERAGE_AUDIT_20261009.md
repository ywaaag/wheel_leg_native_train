# Recovery关节符号接线与起步探索覆盖审核

2026-10-09用户同意核准符号接线及已有腿样本。本轮纯CPU，消费10_50 boundedmean三组真实150D/fulljoint capture和09_40原Gaussian frozenB25随机rollout。未翻转通道、改控制/奖励、启动仿真或PPO。

## 接线结论

没有发现左右实体通道、q观测或腿目标符号接反。真实Isaac全关节顺序不同于action顺序，但explicit activeindices=[1,0,33,3,2,35]正确取出left_hip,left_active_link,left_wheel,right_hip,right_active_link,right_wheel。三组所有受控sample独立复算frame q部分=(q−reference)*2，与150D当前frame误差0；target_before_joint_limit=reference+clip(action)*1.6，与实际保存target误差0。不要直接用全joint数组前6维当action顺序。

USD四腿均axis=X，但left_hip localRot0/1=[0,1,0,0]（绕Y180°），right_hip与两active-link为identity。因此“都写X”不等于左右全局正方向相同；左hip轴框架翻转符合此前局部几何左[+,+]/右[−,+]收短方向，而不是控制脚本随意取反。本轮只读轴/body0/body1/限位与坐标关系，没有独立engine force sign probe，不能称全physics逐子步认证。

## 实际探索缺口

09_40 frozenB25原Gaussian共有2496个受控Swingsample。preframe明确含(q−reference)*2，target−preq可由1.6*clippedsample−frame_q/2复算，不假定reference为0、不用postq冒充preq。

按同postcontrol clock分组，0.01–0.04秒416samples：左hip目标朝已找到局部收短方向的比例0%、左active82.21%、右hip0%、右active4.81%。平均target−preq=[−1.2479,+.5387,+1.5025,−.1802]rad，即两个hip主要把腿向相反方向推。0.05–0.10秒551samples两hip方向比例仍0；所有2496sample中均没有四通道同时符合[+,+,−,+]方向，故没有可计算该组合advantage的样本（UNKNOWN/null，不能填0）。

该组合是此前找到的一条充分局部几何缩腿路径，不是收腿的必要条件。零覆盖不能排除其他关节幅度组合收短、constraint动态引起收短或完整全局路径；尤其大目标差超出±.15rad静态方向审核范围，不以局部符号预测完整非线性动力学。

随机证据来自原GaussianB25，**不是10_58训练new25的新随机轨迹**。新有界wheelmean改变rollout状态，训练未保存完整随机腿trajectory，不能宣称最新策略也统计为0。其确定性raw仍右腿不收短，但“是否随机探索到”尚有证据缺口。

## 下一明确方向

不翻转右hip输出、不添加固定镜像补偿；这会改变已有DrawBack/R0行为，且接线已符合实体坐标。问题更支持源policy在Swing附近目标偏离有效局部收短方向、腿探索覆盖不足，而非简单符号bug。

下一先准备最小有界最新候选随机诊断：绑定10_58 new25 checkpoint及其boundedmean spec，保留原全部接口，记录pre/post fulljoint、同一次ppo.act mean/std/sample、实际targets/heldPD/geometry/record/value/advantage；对比双侧局部收短与其他组合，不要求先成功。建议沿用2×64×128/PPO0、wall≤600s、NPZ≤64MiB，新独立ledger/run，不自动调用旧仅sourceB25假设的reader。此处只提出范围，未发布/授权运行。

如最新样本依旧没覆盖有效构型，再CPU设计实体腿探索或课程单变量；如覆盖有而实际不能收短，再提出必要5msPD/1ms接触诊断。必须先选证据对应分支，不同时加对称/std/bias/reward或改变限矩，不把静态geometry路径当控制先验注入。

## 产物及核验

新增`scripts/audit_recovery_joint_signs.py`；输出`isolated/recovery_joint_sign_coverage_20261009/audit.json`绑定spec/USD/evaluation/captureSHA，三组control counts239/8725/8805。核验具名active顺序、frame公式、target公式及各阶段样本总数2496与已有review一致；成功执行，无runtime。USD轮无限limits在新报告用null并明示语义，原资产Infinity不改。新增报告并更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX；无源码控制修改/新checkpoint/旧raw写入/删除/Git提交。
