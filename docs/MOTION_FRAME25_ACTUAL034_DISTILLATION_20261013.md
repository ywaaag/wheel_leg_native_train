# Motion25D真实0.34m教学重新蒸馏

本轮用户明确要求重新蒸馏。实际执行CPU BC，不启动Isaac/GUI/GPU/PPO。旧教师、v1反事实数据/旧学生/run均只读；新数据与模型独立保存。

教师05_39/block0003/formal/update300 SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb。只使用其实际0.34m零速/±.5/±1成功闭环数据，不混07_21来源，不改教师输入高度、不重新teacher-query。来源为12_15四命令和12_47的-1原始JSON/NPZ/actor_capture，逐SHA核验；manifest保留身份和已通过协议。

40成功首episode×3000interval=120000唯一样本；每命令4env训练/2env验证/2env测试，合计20/10/10episode、60000/30000/30000样本。切分完整episode，不随机拆相邻帧；这些是相近初态并行重复，不是40独立工况或不同training seed。

严格pre-action frame25→同interval实际执行目标；具名motion_policy_control_v1 groups读取q/dq/clipped_action/leg_target_after_projection，腿最终target/.5、轮已执行归一化target，对照mean与clip、下一帧previous/q/dq误差<1e-5。当前轨迹腿机械目标与clip解码一致，不伪称在所有资产上无需机械限位。time dt=.01、完整首episode valid3000条、原有post-step闭窗协议身份保留。label均可表示，无静默裁剪。无初始化固定控制伪标签（本Motion原生reset后Actor从首interval控制）。

接口仍motion_frame25_distilled_v1：25当前帧，无额外历史/RNN/教师ID；25→128→64→32→6、ELU、最后线性mean，环境clip±1，left-first、.5rad/100rad/s；归一化与原Motion25D完全相同，heightcommand.34*5=1.7。新角色MotionFrame25Student，教学涵盖五个命令，不能冒称±2或yaw通过。

四采样阶段：首20step、step20–999、1000–1999、2000–2999，分别是启动/加速/固定保持/减速。每batch512每阶段128，再均衡命令、episode、时间点。这是离线采样分层，不是部署时序或Actor输入。损失四腿物理误差/.1rad平方均值＋两轮/10rad/s平方均值；网络、种子20261013、batch512、LR.001与旧蒸馏相同，避免同时改模型。CPU线程4，上限5000step/1200秒，每200验证，5次无改善早停；测试不选模。

实际CPU BC 3800 optimizer step，15.631秒，best step2800，早停five_validations_without_improvement；PPO0更新为0，没有物理采样。random_initialization/best_validation/latest/BCAdam/dataset/manifest/result均保留。teacher_unchanged=true。

|测试阶段|腿MAE rad|轮MAE rad/s|唯一样本|
|---|---:|---:|---:|
|first_20_steps|0.0011406|0.139391|200|
|acceleration|0.0002855|0.049821|9800|
|hold|0.0002295|0.048066|10000|
|braking|0.0002585|0.051141|10000|

逐通道MAE/P95/max见training_result；逐命令/阶段见export_report；实际抽样/唯一被抽样数见sampling，重复抽样不计新物理经验。验证和测试参考线达标只说明动作拟合。原学生0/40事实保留，新模型闭环NOT_RUN，不能据离线指标宣布站稳。

best_validation.pt SHAe86b7922d099f2519b1f0c00959399b40c9848add9be32fcf39ec3f6a2df23ab；ONNX SHA43906a719ada613d108eb33993d312f768104bb4f93407bd2ecf194fb654a101。Actor13862参数/55448FP32bytes/13632MAC；ONNX文件56376bytes，固定[1,25]float32→[1,6]mean，仅Gemm/Elu；86个实际测试与声明边界输入，ONNX ReferenceEvaluator maxoutput误差1.78813934e-07，腿8.94069672e-08rad，轮1.78813934e-05rad/s。TorchScript误差0。HARDWARE_UNVERIFIED，无MCU时延或真机认证。

源码目录manual_train/motion/frame25_actual034_distillation_20261013：data.py、distill.py、export_review.py、test_actual.py、prepare_evaluation.py及独立public evaluation_engine。未修改共享src；新版probe角色与教师/dataset/manifest严格绑定，不凭输入宽度猜模型。CPU真实数据边界/实际模型/公开config3passed，实际_snapshot冻结逐SHA相同、PORTABLE3passed；public supervisor零写plan cpu_valid=true/READY_NEEDS_AUTH、simulation0/files_written0、attempts={}。

物理验证准备：最终16_05 motion_frame25_actual034_student_teacher_ppo0，新spec/独立budget.json，UNAUTHORIZED。学生/教师按0/+.5/-.5/+1/-1逐命令交替，各8scoreenv共80评分episode、64simenv、max3000秒含清理、512MiB、GPU0shared、PPO/optimizer0。原Motion正常root.40初始化，不认证实机.36峰高；沿原motion_standing034_v1固定10–20秒保持，不新增对称通过宣称。学生全程独立Actor、不调用教师救场。工程故障不重试，能力失败继续其余cases。提交前核验实际GPU UUID/CUDA0/资源/session，不能用旧物理额度。命令统一TOOL_INDEX。

下一步单一重点：验证真实数据重蒸馏学生是否改善零命令闭环及五命令运动。若仍早期失稳，以最早偏离查观测/previous/目标及离线覆盖；不能先假设25D不足，也不自动叠加GRU/量化/PD修改。

## 物理评估实际停止

用户授权后本16_05新PPO0已提交并执行，后用户明确停止剩余case。7完整case/56episode：新student4×0/8，teacher3×8/8；student均约2.08s tilt。monitor STOPPED_BOUNDED，1546.432秒；模型前后SHA相同、PPO/optimizer0。teacher+1正在运行时中断，结果INCOMPLETE，不算失败/通过；student-1与teacher-1 NOT_RUN。最新机器结果evaluation_review.json及首偏离zero_student_teacher_divergence.json在本轮源码目录；下一设计见MOTION_FRAME25_PPO_NEXT_DESIGN_20261013.md，无新PPO已提交。
