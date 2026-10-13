# 浙江大学收腿/支点思路：CPU几何与塑形边界审核

## 授权与执行范围

用户同意执行上一“几何、奖励量级及终止边界CPU审核，再准备单变量实验”方案。本轮只实现纯CPU候选、合成边界测试及现有轨迹反事实核算，未启动仿真/PPO或生成可提交新spec；来源B25、checkpoint、旧run/spec/ledger未改。浙江大学一手资料及原zip身份见RECOVERY_ZJU_GEOMETRY_METHOD_20261008.md。

## 原生几何核算

使用已完成17_39 B25 input/reward PPO0中全部8环境×3family具名trace。hip anchor→wheel center的长度/向下夹角在同一root坐标计算，不控制虚拟腿，不把wheel center当contact point或COM。各组原始SHA、逐环境数组摘要见isolated/recovery_support_geometry_audit_20261009/audit.json。

Swing八环境首控制长度约.37423–.37599m。env0左/右最小长度.36361/.37599m、最后.37593/.37599m；右腿几乎完全不收短，左腿只小幅收缩后恢复。向下夹角首约1.274/1.278rad，终约2.103/1.358rad，支点方向反而恶化。

DrawBack env0首长度.15262/.15000m，最小.15262/.14681m，保持终.37593/.37599m；方向首约.770/.751rad→终.180/.140rad。R0首长度约.345m，保持允许.376m。支持“低位需要探索构型改变”，不支持“永久短腿更稳”或直接照抄原文l_min=.10m。

候选尺度short=.15/long=.375m是本机实测近似参数，用于CPU核算，不是已证实最优目标；bounded收腿距离与向下方向代价各占.5，低位height gate .22–.30m用smoothstep。未把这些参数写入训练reward。

## 严格PBRS端点的结论：本候选暂不进入PPO

Phi=−g(height)*C(geometry)，Swing受控/first-entry前定义，其他group为0；F=beta*(gammaPhi_next−Phi_pre)，gamma=.99，真正吸收terminal的下一Phi置0。无额外dt，不能按per-second连续成本再乘.01。

对每episode完整折扣和有精确恒等式：sum_t gamma^t F_t=−betaPhi_initial+beta gamma^T Phi_terminal；吸收Phi_terminal=0，因此固定初态下完整塑形回报不随中间路径/成功失败改变。正确PBRS可以改善有限采样学习的信号/critic条件，但没有新增“收腿优先”目标，也没有CLF/收敛保证。它并非绝对无用；本项目目前缺证据表明其优势超过端点/critic实施复杂度，不能用几何变好看直接批准训练。

实际Swing env0从首控制后的Phi≈−.675664出发，beta1完整折扣塑形和+.675664，恒等式残差2.22e-16；8env最大残差3.33e-16。beta.1失败末步释放约+.0737–.0742，正项并不是最后一步收腿改善。旧DrawBack/R0因family mask均0。

当前原始geometry为policy-step后的state，未保存与geometry一一对齐的第一控制前wheel center；审计明确省略第一个transition，不冒称精确复现整个episode reward。合成有利收腿/原地/震荡路径独立证明同初态吸收terminal后折扣和一致，不能挑取去掉末步后的正进展当完整训练收益。外部time-limit/truncation需保留nextPhi并与价值bootstrap一致，不能一律terminal归0。

## 下一具体方法：目标型几何项须独立声明，不暗改PBRS

优先继续浙江大学低位支点/收腿机制，但将下一候选明确称“改变任务偏好的几何目标项”，而非保证policy invariance的PBRS。

可审核起点是Swing/pre_entry受控下有界连续成本−w*g(h)*C(s)*policy_dt，同时原lift/成功/失败保持；不取只正delta，不永久短腿、不叠mean辅助/轮effort成本。w尚不选择、不生成runtime spec。该项可能让策略更愿接近收腿支点，也可能因累计负成本诱导更早终止、放弃必要转姿或压抬升，必须下一CPU反事实把这些风险一起核准。

下一最小准备工作：
1. 同初态合成“静止长腿／安全收腿后抬升／只单侧收腿／短腿但向上／绕圈／更早tilt失败”完整回报对照，保持真实once failure/success与discount/time-limit语义；目标项分阶段与门控数值可解释。
2. 在已保存8env轨迹核算w候选与lift/失败项/旧组保持比值，定义完整折扣目标，不能用每秒cost小掩盖更早结束偏好。gate由高度退出不能被冲高刷掉目标项而未形成支点；需显式检查。
3. 确定单个reward版本/系数后，CPU接线和边界测试，再通过公共Recovery准备器发布UNAUTHORIZED新spec/ledger/完整SHA；来源B25固定26/25/13、meanaux明确关闭、原控制/150D/std/Adam/gate保持。runtime/PPO需独立预算授权。

若几何项无法在不鼓励早死/不压必要转姿的情况下提供合理偏好，停止该reward设计，转向实际动作/支点可达性证据；不为了“必须训”自动加强代价或加入控制层。

## 改动与验证

新增src/native_stand/recovery/support_geometry_proposal.py（纯geometry/potential/absorbing-shaping）、tests/test_recovery_support_geometry_proposal.py（PORTABLE6用例）、scripts/audit_recovery_support_geometry.py（身份绑定旧trace审计）、本报告。更新Recovery计划、STATUS、TOOL_INDEX。

相关CPU16 passed（含新6、既有cost2、event8）；涵盖有利进展/无进展/震荡吸收折扣恒等式、terminal释放、truncation不同处理、缩放/gate/zero-vector/nonfinite拒绝。无额外RNG/optimizer/仿真/模型输出。源码AST与diff检查通过。工程/理论审核不是新起身能力结果。
