# 剪刀腿参考材料与当前Recovery核查

用户同意继续离线诊断并提供参考文献2.md；不启动新模拟/PPO。
新脚本scripts/review_recovery_scissor.py，新输出
isolated/recovery_scissor_review_20261007/review.json；资产、spec、pose library及
evaluation50/100 SHA记录并复核。原始评估/账本/模型未修改。

## 可用的建议

剪刀腿可以表现为一腿前探、一腿后撤，两轮纵向错位，但腿长几乎相等。
这是应区分的几何现象：腿长差、关节镜像误差、轮心纵向偏置不能互相替代。
本项目已有longitudinal_geometry基于轮心和重力方向计算runtime水平纵向错位；
应补采它在起身/保持期间的实际轨迹，不能立即以腿长惩罚代替。

env0控制记录的实际active q，经当前USD离线闭链求解得到：
update50末段沿root-local -Z的轮心纵向错位约20.7cm；10.68秒附近约49.5cm。
update100五个选定点约17.5cm。求解闭链残差均低于0.1mm。
这支持用户肉眼看到的剪刀趋势，但不作为runtime接触支撑多边形认证：
仅一个环境/五个点，实际被动关节历史缺失，闭链分支从捕获姿态初始化；
root-local纵向也不等于倾斜机体的世界水平投影。不能由该数值宣称剪刀腿导致稳定。

## 轮动作历史与平滑成本核查

当前env._pre_physics_step先previous_action.copy_(action)，再执行新目标。
Recovery将action改写为实际执行腿目标归一化/轮速度目标归一化；正常受控步
observation frame末6维为该执行action。history五帧oldest→newest，初始化步action
清零是已有声明行为。源码未发现把新动作当旧动作或反向history的错误；
历史run没有保存完整actor输入，因此不称runtime history逐帧认证。

Recovery process_reward使用(action-previous_action)^2六通道均值，权重-.01，
连续项乘policy dt .01一次。wheel action=wheel target/100，所以真实轮速目标
跳变被100归一化再平方，并除六通道；Recovery路径不使用Motion的
action_delta_wheel_factor。只是当前配方明确量级，不是未生效参数的已证实故障。

env0末5秒new100轮目标每步RMS跳变17.65/11.53rad/s，单独轮delta项约
-0.0000741/秒、-0.000000741/policy步；new50约.188/.137rad/s。
轮振荡约束显著弱于量级为每秒数个单位的姿态/高度项。可作为下一次单变量
wheel delta尺度实验假说，但不直接据此放大权重、增加低通/软制动或改Kv。
动作成本量级小不证明其PPO因果梯度小，更不保证加强平滑后不损失必要平衡。

## 材料中的不可靠推论

参考文献2没有可追溯的具体论文链接/DOI，其项目表混用了来源B250与扩展候选
（此前核对过的+.391/+.791等不是原B250），也不是本次DrawBack配方事实。
“形成三脚架/支撑多边形所以静态稳定”“PCGrad保证无损”“等变网络彻底消除
剪刀腿”“WBC保证绝对平衡”等是过度结论，不能用作改架构或训练的理由。
两轮接触点纵向错位不自动形成有面积的支撑面；滚动与接触力约束需独立分析。
不采用WBC/LQR/MPC、重力补偿、虚拟腿动作或大网络重构，保持AGENTS物理接口。

## 下一步

保留GUI认可update50；先准备其冻结PPO0完整geometry/posture/control复核，
在同一episode记录轮心世界水平偏置、腿长、关节镜像、接触、pitch/roll、高度，
区分进入站立前后。已有full_trace=False仍有control但无完整geometry，这是
证据保存粒度缺口，不凭有限尾窗补全。PPO0需独立明确预算，目前未提交。
之后依据真实事件序列分别选择弱轮心几何约束或wheel delta尺度对照，
不同时改两者；姿态、限矩、起身率和旧能力一并回归。腿长成本提案保持暂停。

本次新增脚本/报告/isolated证据，更新STATUS与RECOVERY_STANDING_PLAN；
AST、离线input SHA、10个闭链采样误差和JSON有限值验证通过；未改变运行代码。
