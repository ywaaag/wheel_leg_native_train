# Recovery Swing闭链几何方向与局部连续路径审核

2026-10-09用户同意实施计划8.8的下一CPU步骤。本轮从合法保存Swing全关节状态、新USD和冻结hip anchors出发，小幅扫描实体主动关节，复用AssetPoses.solve/forward/support；没有Isaac/动力学/optimizer、没有新增reset或训练spec。

## 局部几何方向

保存Swing主动q约[+1.1420,−1.4102,−1.1427,−1.4091]rad，左右hip→wheel长.375930/.375957米。USD解析的limits及被动关节闭链按原分支初值continuation。

单通道每步.025rad、最多±.15rad，双通道±.10rad网格：左hip增加或left active-link增加可收短；右hip减小或right active-link增加可收短。反向试探在接近伸长端的位置出现closure residual>.0005米而被停止，这表示本次静态solver无法在该方向闭合，不是动力学卡死或全球不可达证明。

左右各最优局部组合：左[+.10,+.10]、右[−.10,+.10]rad，对应腿长约.351527/.351361米，所有active/passive关节limits通过、closure误差<1e-4米。本机器人是镜像实体轴，右侧方向不能直接照抄左侧两个同号；不将此转换成虚拟腿action映射或控制规则。

## 双侧连续几何路径

进一步同时扫描[+δ,+δ,−δ,+δ]，δ从0到.15rad、16个离散样本。两侧腿长单调缩短至.338449/.338276米，约收短3.75cm；最大closure3.28073e-5米（起点保存状态误差），终点≈5.12e-9米，无关节限位违规。相邻被动关节增量峰值约.01777rad，未出现大数值跳跃；这增加局部solver连续性的证据，不认证所有物理branch或无自碰撞。

固定保存root姿态/高度的ideal collider最低地面间隙≥约0（数值−5.4e-14），终点约+.000217米。这个检查仅排除该离散局部路径明显穿平面的最低点，不检查自碰撞、接触面法向/摩擦、轮下支撑、离地空间、关节速度/力矩或真实solver稳定性。

轮中心root坐标仍在原Swing附近，δ=.15没有达到DrawBack；DrawBack保存状态腿长约.15149/.15152米。未找到或验证完整Swing→DrawBack动作，不能把局部缩腿路径称为能起身的姿态或新的合法runtime reset。

## 与实际失败动作的关系

右腿实际两个主动q同向增加、q0−q1近.268rad固定，腿长约.376米；局部geometry要求右hip减小、active-link增加来改变相对构型。来源policy首步右target约[+.452,−1.600]rad，相对保存初始[−1.143,−1.409]，目标主要推右hip增加/active-link减小，与局部收短方向相反。闭链/接触会让实际q不同于目标，不能直接将目标方向判成动力学唯一根因或PD反号。

该证据支持：右腿不收短不是因为所有收短目标都被新增主动limits排除，而是当前策略/执行轨迹没有利用已找到的局部几何收缩方向。增加轮探索已解决部分轮sample别名，但没有自动改变腿协同。

## 下一准备

先用已有NPZ做纯CPU腿探索覆盖核算：把真实raw/sample/clipped腿目标与这些实体几何方向对照，按family/episode起步时相统计是否曾采到双侧局部收短方向，并核对advantage；不将静态solver对观测点的梯度当作已验证reward。

同时准备最小有界物理诊断的字段契约：pre/post全关节、5ms PD及必要接触体力、机体垂向运动，才能检验“摆腿支撑抬升后及时收腿”的动力学假说。预算、GPU、存储、是否施加任何诊断动作必须明确后新授权；本轮不自动运行、不导出前馈轨迹、不改初态或奖励/腿std/限矩，不接LQR/hiddenFSM。

## 产物和验证

新增`scripts/audit_recovery_swing_geometry.py`，CLI --spec/--output-dir默认纯CPU，独占发布SHA绑定audit。初次局部扫描`isolated/recovery_swing_geometry_scan_20261009`保留；最终含双侧continuation `isolated/recovery_swing_bilateral_geometry_scan_20261009/audit.json`。输入spec/pose library/USD SHA核验，实际全扫描执行成功；额外核验16样本闭链阈值/所有limits/固定root理想planegap/双侧长度单调。没有额外镜像实现或数据重写测试。

修改仅该脚本、TOOL_INDEX、STATUS、RECOVERY_STANDING_PLAN与本报告。旧USD/pose/checkpoint/raw/spec/ledger未改，无仿真/GUI/PPO/通知/清理/Git提交。
