# Motion25D无历史学生测试重试：有界终态与学生优先补测

用户“同意”授权修复后一次重试。公共register→冻结PORTABLE6→supervisorREADY/sharedGPU0→evaluation-only launch/wait均实际完成。执行220模块与CPU冻结SHA一致，specSHAe9565f6e8ade7177ed3587b79fce5afeaf6661346bd34563bb0e13fa6d0f38b3，GPU0 UUIDe704e7d4-2965-4712-9759-ba6b9910bd72/CUDA0。未停止其他任务、未换卡、PPO0/optimizer0，通知未启用。

## 实际终态

run runs/2026_10_13-12_15__motion_frame25_student_teacher_ppo0，attempt e162254e4b044d5ea42c4f3192abffc7，STOPPED_BOUNDED；monitor实际wall1331.990362秒，child报告1331.584469秒，32完成评分episode、768000全部64simenv-step/96000评分env-step，产物47377708bytes约45.18MiB。无新runtimefault，actor参数未变，结果成功原子保存。

停止原因：已完成项的最大耗时用于保守下一项时间估计；剩余1800秒额度不足完整下一item＋cleanup，owner正常停止，不是工程故障或已耗尽1800秒。原matrix教师五组全部排在学生五组之前，当前共享负载下导致学生未执行。该调度安排不合适，不能将teacher成绩写成student成绩。

|role/command|实际meanvx|vxMAE|meanheight|通过|
|---|---:|---:|---:|---|
|teacher0|.001239|.001243|.352251|8/8|
|teacher+.5|.507127|.017490|.355516|8/8|
|teacher−.5|−.478533|.021467|.349084|8/8|
|teacher+1|1.152033|.154897|.358615|8/8|
|teacher−1|NOT_RUN|—|—|NOT_RUN|
|student0/±.5/±1|NOT_RUN|—|—|全部40episode未运行|

四个teacher条件均双轮contact1、torque-saturation0，最大tilt分别.0389/.0815/.0389/.1232rad。此为motion_standing034_v1评分，不含新symmetry联合标准；完整启动峰高均约.39966m，不能称实机≤.36通过。8并行重复/单seed20261013，不是8独立训练seed。

## 原始输入执行核对

四项atomicJSON+numericNPZ/captureSHA复核，preframe25与前一postq/dq、previous action、实际clipped_action对应：action/previous/q最大差0，dq缩放最大7.16e-8；actor参数不变。上次保存相对导入错误已消除。actual actor仍legacy150Dteacher；25Dstudent此次没有物理输出，无法判断站稳或非零运动能力。

teacher固定0.34来源05_39/u300 SHA4750ee…cafb；studentbestvalidation SHAe56dc7f5b07f15bcd14abcc34fde14bdf09316c9716d3918460ac80435fedd06不变。测试前后无BC/PPO更新，未采用新模型覆盖来源。

机器逐项结果manual_train/motion/frame25_evaluation_20261013/completed_review.json包含每条件状态、rawSHA、archive验证、terminal和exact账本。旧12_04 FAILED约412.39秒单独保留，不合并称一次评估。

## 已准备的学生优先补测

新probe motion_frame25_student_priority_v2，新engine_student_priority从修复副本复制，不改旧已执行engine或声明。

先studentzero、+.5、−.5、+1、−1各8环境；最后只补teacher−1共8环境，总新48episode/1800秒/512MiB，GPU0共享、PPO0/optimizer0。已完成四个teacher结果逐文件SHA、source/asset/physical/control/pass进行严格只读验证，作为历史同协议对照，**不冒称来自新attempt**。不重跑已完成教师速度项，不借旧剩余墙钟，原账本与实际消耗保留。

新spec `/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_13-12_47__motion_frame25_student_priority_ppo0/spec.json`，独立budget UNAUTHORIZED/0attempt/0used，无run。7source测试、7冻结PORTABLE通过，public零写planREADY_NEEDS_AUTH，唯一缺项运行授权。输入history不影响student、数据身份、按文件入口atomic保存、历史teacher证据SHA及物理契约拒绝覆盖。初版shared全943/8skip/22逐ID同baseline，仅新的独立副本变更，无sharedsrc变化。

本轮不自动再提交。新批准后按register＋GPU/session/UUID资源核验＋publicsupervisor一次evaluation wait提交。下一结果应优先回答studentzero是否能站稳，再报告非zero泛化，不能用BC小误差替代闭环。

准确命令仅TOOL_INDEX，事实STATUS；本报告不改变电控接口或宣称真机能力。
