# MCU v2小学生：完整执行与闭环复盘
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


本轮完成31D接口、两个独立小学生CPUBC、两份确定性ONNX、CPU数值/冻结验证，以及一次GPU0共享PPO0。工程和导出数值通过；两个学生均未通过完整10秒能力。在线PPO=0，真机=NOT_RUN，Jump=NOT_TRAINED，硬件=HARDWARE_UNVERIFIED。

| 模型 | BC实际步／最佳步 | Actor参数 | ONNX最大误差 | 入口 | 完整10秒 | 主要失败 |
|---|---:|---:|---:|---:|---:|---|
| RecoveryStudent | 5000／5000 | 14,630 | 2e-06 | 0/32 | 0/32 | 约.64–.69s大倾角终止，无入口确认 |
| MotionZeroStudent | 4600／3600 | 14,630 | 2.98e-07 | 8/8 | 0/8 | 已入口，约3.09–3.16s倾倒 |
| B50→B250教师组合 | 0（冻结） | 原模型 | 未重新导出 | 32/32 | 32/32 | 无 |
| B250正常零命令 | 0（冻结） | 原模型 | 未重新导出 | 8/8 | 8/8 | 无 |

## 接口、物理与在线边界

显式multiskill_mcu_v2：Actor31→128→64→32→6、ELU alpha1/tanh mean；Critic40→256→128→64→1，新初始化，BC不训练/不部署。Actor14,630参数、FP32权重58,520 bytes、14,400线性MAC。运行库/激活/固件/critic/std另计；1044bytes是forward张量总浮点估计，不是ST内存规划或栈实测。

31D：身体角速度3×.25、重力3、四腿q-reference÷1.5、sixdq×.05、previous实际腿目标4÷1.5及轮目标2÷100、vx/4/yaw/4/height/.5、Motion/Recovery/Jump one-hot、NONE/SMALL/BIG one-hot。无历史、教师ID、教师时刻或未来标签；Recovery全程Recovery/NONE，高度命令.40。四腿LH/LA/RH/RA，six关节LH/LA/Lwheel/RH/RA/Rwheel。xyzw及native前向-bodyZ/侧向-bodyX/向上+bodyY不变，硬件IMU/编码器零点与传动标定未验证。

执行先clip action→1.5rad/100rad/s解码→实际USD限位→缓存实际目标→原PD与40/5.5Nm。Plane、1/5/10ms、PD60/2/1不变。reset采用声明初始化目标，切换不清速度/重置/沉降。legacy150D、1182D v1按各自版本加载，非按维度猜版本。

StudentEnv reward仍零，仅供PPO0；public config/preflight和ppo.assemble明确拒绝v2在线训练，不宣称具备有效在线reward链。普通Gaussian采样坐标、tanh mean，未加squashed Jacobian；std腿.05rad/轮2rad/s，BC不优化std。

## 教师、数据与划分

B50 SHA 46add82fa9d32c04fcc0a8b79c6339a27df3b9ca6c95050b8e13f52b644b7f75；B250 SHA 5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。自身checkpoint内部spec SHA匹配各自冻结spec，见teacher_identity.json。B250训练资产为旧版本，不将旧资产通过迁作当前证书。本轮教学轨迹与评估限位USD SHA 32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7。

[独立数据manifest](../isolated/student_mcu_v2_teachers_20261011/manifest.json)。原始具名pre-action关节、target_pre与当前after-limit标签分开使用，未复制旧action/使用post-q/混入初始化或失败示教。新height .40仅重新编码学生输入，不改原教师输入。

Recovery31个成功episode、36353唯一样本：train15（历史7＋最新seed20261010的8），validation8（20261011），test8（20261012）。相近初态/小yaw重复，不是31种工况或独立training seeds。阶段train/validation/test：
- preparation：750/400/400。
- turn_lift：375/200/200。
- dynamic_settle：1466/788/774。
- stable_hold：15000/8000/8000。

每batch四阶段各128/512，先均衡episode再时间点。每阶段640000次实际抽样、总2560000次BC抽样，不是新增物理经验；unique/repeat和各阶段可用episode见training_result及dataset_stage_and_boundary_audit。

MotionZero仅正常站姿零命令16个episode/16320样本，train6/validation2/test8。其turn_lift桶只是正常入口前20样本，不是跳跃。没有教学非零vx/yaw、高速或驾驶能力。

## CPU训练、模型与导出

两个学生Actor/Critic/BC Adam独立新初始化，seed20261011，不继承教师参数/旧Adam/RNG。batch512、Adam1e-3、4threads、200步验证、5次无改善早停。仅Actor mean优化，Critic/std保持新初始化。Recovery5000step/15.3166s；Motion4600step/13.8664s，best3600。总9600BC step/29.1830s，与物理PPO0 optimizer0分账。test只在验证选模后计算。

| 模型／测试阶段 | 腿MAE／P95 rad | 轮MAE／P95 rad/s | 参考线 |
|---|---:|---:|---|
| RecoveryStudent／preparation | 0.048808／0.170199 | 0.735043／2.038587 | 未达到 |
| RecoveryStudent／turn_lift | 0.031819／0.024270 | 0.341203／0.380497 | 达到 |
| RecoveryStudent／dynamic_settle | 0.010293／0.025488 | 1.480124／5.162220 | 未达到 |
| RecoveryStudent／stable_hold | 0.003130／0.006431 | 0.840658／1.198209 | 达到 |
| MotionZeroStudent／turn_lift | 0.001269／0.003696 | 0.255837／0.774597 | 达到 |
| MotionZeroStudent／stable_hold | 0.000527／0.001150 | 0.061655／0.151783 | 达到 |

逐通道MAE/P95、训练/验证指标、标签±1和输出≥.99统计保存在training_result。Recovery准备腿P95、动态轮P95未达标，未调seed/扩网络/追加预算/放宽参考线。

- RecoveryStudent：[best_validation](../isolated/recovery_mcu_v2_bc_20261011/best_validation.pt)，SHA 7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470；[ONNX](../isolated/recovery_mcu_v2_deploy_20261011/actor.onnx)，SHA 653aeda7326f230aceabfc746e9bb2e001c6e8fd589041f457f936e41bbcc05a。同目录有random_initialization、latest、training_result。
- MotionZeroStudent：[best_validation](../isolated/motion_zero_mcu_v2_bc_20261011/best_validation.pt)，SHA 63d32431db87966a7c7e1e773f6b8d62a96d592cc1e68386dfcf63a8c3866bc4；[ONNX](../isolated/motion_zero_mcu_v2_deploy_20261011/actor.onnx)，SHA 3a53647e050245765c26ffafe8d7bbe10b6a218f717876fa60ba7bd9d296a322。同目录有random_initialization、latest、training_result。

ONNX固定float32[1,31]→[1,6]，仅Actor mean，算子Gemm/Elu/Tanh。每模型196组goldens：96教师、64实际v1学生失败重建、32合法合成包络（非可达认证）、4reset/交接记录。ONNX ReferenceEvaluator CPU对照（未装ONNX Runtime），最大归一化误差均≤1e-5。Recovery腿最大误差2.995e-6rad、轮4.023e-5rad/s；Motion4.470e-7rad/2.980e-5rad/s。

[部署分析包](../isolated/mcu_v2_delivery_20261011/mcu_v2_deployment_package.zip)含两份ONNX/manifest/goldens/预处理与解码。ST CLI未安装；真板计时/Flash/RAM/激活/固件分析NOT_RUN，HARDWARE_UNVERIFIED，不把桌面CPU或MAC当H723 100Hz证书。

## 一次PPO0身份、成本和协议

[spec](../configs/experiments/2026_10_11-11_36__mcu_v2_student_independent_ppo0/spec.json)，SHA 9b5c2fc0196870a83b3e92b477684aa44817b3ed5fa4ebd29dbd44e65b685fba。
[terminal](../runs/2026_10_11-11_36__mcu_v2_student_independent_ppo0/terminal_report.json)、[monitor结算](../runs/2026_10_11-11_36__mcu_v2_student_independent_ppo0/monitor_exit.json)，attempt 290fb8a0e2574a80b07eadc4763edbc5。
独立ledger evaluate限额1/实际1、COMPLETED exit0，在线PPO/诊断optimizer=0。无重试/追加/续训。
GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES0→cuda:0，CLI shared实际生效；已有其他同卡进程，未停止/抢占/换卡。
616.32945s包含初始化/评估/退出清理；39693490bytes（37.85MiB），低于1800s/512MiB。
64仿真/8评分环境，80评分episode；模拟env-step 423872、评分首episode env-step 52865，80episode不是全部物理计算量。

四组条件与v1逐项核验case ID/family/seed/yaw/seconds一致：原Swing＋三个小yaw，非地形/高度/速度泛化。
学生student_autonomous_swing_v1协议：受控2.5s内连续.20s入口，随后1000interval保持；高度每样本≥.30（.42允许）、pitch/roll mean≤.10/peak≤.15、tilt≤.18、双轮>2N合力连续接触、闭链≤5mm、采样触限≤5%、mean|vx|≤.5/|vy|≤.02/|yaw|≤.03。严格vx .02仅诊断，无位置漂移上限；全程约60°终止不等于保持水平gate。
教师保持recovery_motion_zero_handoff_v2（.50s准备＋接管后2s入口）。旧结果不追改。学生v2相对v1评分无放宽，接口/网络/高度命令改变；不同协议或接口结果不能直接冒称训练提高。

| case | 初态有效 | 入口 | 完整保持 | 主协议 |
|---|---:|---:|---:|---:|
| student_native | 8/8 | 0/8 | 0/8 | 0/8 |
| teacher_combination_native | 8/8 | 8/8 | 8/8 | 8/8 |
| student_yaw10 | 8/8 | 0/8 | 0/8 | 0/8 |
| teacher_combination_yaw10 | 8/8 | 8/8 | 8/8 | 8/8 |
| student_yaw11 | 8/8 | 0/8 | 0/8 | 0/8 |
| teacher_combination_yaw11 | 8/8 | 8/8 | 8/8 | 8/8 |
| student_yaw12 | 8/8 | 0/8 | 0/8 | 0/8 |
| teacher_combination_yaw12 | 8/8 | 8/8 | 8/8 | 8/8 |
| student_normal_zero | 8/8 | 8/8 | 0/8 | 0/8 |
| teacher_normal_normal_zero | 8/8 | 8/8 | 8/8 | 8/8 |

## 最早偏离与证据边界

80项offline accepted/entry/hold/失败项与online全部一致，finite、初始化80/80有效、模型不变。
独立root/quaternion/角速度/关节/上一target重建31D最大误差2.38e-7，上一周期after-limit执行缓存误差0，首次学生/教师编码差≤5.96e-8。支持单位与时序接线正确，不代表排除全部拟合/反馈问题。

Recovery32/32双腿同时≤.34m持续50ms；首例.07s、高度.1696–.1703m、双轮接触、pitch .075rad。腿和轮心构型实际改变、峰高.296–.309m，已有收腿/转腿/抬升，但无水平入口；32/32约.64–.69s大倾角终止。不能称原地不动，也不能把折叠或达.30m称完整起身。

统一受控时钟比较：
- Recovery腿目标相对教师最大差>.10rad从.10s，pitch/roll差>.05rad从.16s，height差>1cm从.23s；早于教师.50s交接，不能将所有失败归于交接点。
- MotionZero入口8/8，pitch/roll差>.05rad2.03–2.09s，height差>1cm2.59–2.65s，腿目标差>.10rad2.85–2.91s；3.09–3.16s倾倒。稳定数据拟合良好不等于闭环反馈可靠。
- 教师.50s边界相邻31D变化约.00155–.00164，腿目标却跳约1.48rad；学生边界最大腿误差约.38rad前/1.06–1.07rad后。是边界拟合难点，不是早期失败唯一根因证明。
- 高轮速/触限不直接等于空转；事件先后不当因果。逐env位移/速度/接触/力矩/姿态窗口及双收短上下文已保存。

[离线review](../isolated/mcu_v2_ppo0_completed_review_20261011/review.json)、[机器证据目录](../isolated/mcu_v2_delivery_20261011)。

## 回归与源档案

针对性26通过；提交前冻结PORTABLE26通过。终态发现旧flat snapshot未含students/model_factory：本轮已与提交前完整CPU源归档逐模块SHA一致，见runtime_source_provenance.json，未补写已完成run。仅对后续学生spec修补公共_snapshot归档，新增snapshot真实回归，最终冻结27通过。

最终全项目788通过/22errors，修改前779通过/同22errors；逐项ID和fixture内容完全一致，旧Motion工程证书unchanged configure.py SHA校验失败。本轮未改configure.py、未放宽校验/跳过关键测试。完整输出/逐项对照保存。其他worker dirty changes、旧run/model/ledger/freeze保留，不commit/push。

## 精确改动

总纲ROJECT_MASTER_PLAN→PROJECT_MASTER_PLAN，仅命名/标题/heading/导航，不改目标。其余为固定版本分派、真实编码缓存、数据/BC/导出/评估、CPU测试、档案与导航：
- AGENTS.md
- PROJECT_MASTER_PLAN.md
- README.md
- ARCHITECTURE.md
- TOOL_INDEX.md
- STATUS.md
- docs/RECOVERY_STANDING_PLAN.md
- src/native_stand/students/mcu_interface.py
- src/native_stand/students/model.py
- src/native_stand/students/data.py
- src/native_stand/students/distill.py
- src/native_stand/students/requests.py
- src/native_stand/students/runtime.py
- src/native_stand/students/evaluator.py
- src/native_stand/students/ppo.py
- src/native_stand/students/export.py
- src/native_stand/command_v6/config.py
- src/native_stand/command_v6/tools/preflight.py
- src/native_stand/command_v6/tools/model_factory.py
- src/native_stand/command_v6/tools/evaluate_checkpoint.py
- src/native_stand/command_v6/tools/play.py
- src/native_stand/command_v6/tools/health_check.py
- scripts/build_student_teachers.py
- scripts/distill_student.py
- scripts/prepare_student_validation.py
- scripts/export_mcu_student.py
- scripts/review_student_validation.py
- tests/test_mcu_v2.py
- tests/test_mcu_v2_data.py
- tests/test_mcu_v2_export.py
- src/native_stand/command_v6/train.py
- docs/MULTI_SKILL_ROADMAP.md
- docs/MCU_V2_STUDENT_COMPLETED_REVIEW_20261011.md

## 下一项单一重点

优先处理Recovery .00–.25s早期腿目标拟合与闭环偏离，保留31D与现有物理；用已有成功教师输入/标签检查局部误差、相近输入/不同目标，区分拟合不足与教师覆盖外状态。现已定位.10/.16/.23s，不要求先证明唯一根因才准备有界学习。
仅在有教师能力证据的局部状态提供补充教学；教师覆盖不到的部分另立明确reward/PPO声明，不能提交当前零reward环境。不是默认返回1182D/叠加GRU/量化/PD/续旧receiver。本轮不再采样/BC/PPO/真机，下一实验需新授权。
