# Motion25D学生优先补测完成复盘

## 结果

用户明确“批准”，新48episode/1800s/512MiB的一次PPO0已执行。新run runs/2026_10_13-12_47__motion_frame25_student_priority_ppo0，attempt e98b9e518f674dcd87871bcd5308b412，终态COMPLETED。childwall866.925019s，monitorexactwall867.355418s，产物33286779bytes约31.74MiB，48评分episode，64simenv×3000policyinterval×6=1152000全部模拟env-step，144000评分env-step。onlinePPO0/offlineoptimizer0，无retry/额外预算，通知关闭，GPU0shared/UUIDe704e7d4-2965-4712-9759-ba6b9910bd72/CUDA0。

|对象/请求vx|通过|第一个episode结果|
|---|---|---|
|25D学生0|0/8|8环境1.38s tilt终止|
|25D学生+.5|0/8|同上，尚在零命令入口期|
|25D学生−.5|0/8|同上|
|25D学生+1|0/8|同上|
|25D学生−1|0/8|同上|
|150D教师−1|8/8|完整30s，vx−1.0311，MAE.04791，meanheight.34753m|

学生五组总0/40、无保持窗口，不把缺测的保持mean/速度MAE填成0。真实actorcapture核验前138interval commandvx/yaw均0、height归一化1.70；所以不是五种非零速度下均独立摔倒，而是所有请求都在相同2s零速阶段失败，非零跟踪NOT_REACHED。

教师其余0/±.5/+1来自前一12_15attempt，32/32，严格原JSON/NPZ/captureSHA及source/asset/control同协议核验；加本次−1，总五命令40/40教师证据，但**不是同一个attempt完成**。所有8parallel为相近初态重复，seed20261013，不是独立训练seed认证。该协议未要求新增对称联合gate，不能称教师已严格对称。全启动峰高约.39966m，仍不认证实机最大.36m。

## 模型身份与执行

teacher旧05_39/formalupdate300 SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb；student bestvalidation SHAe56dc7f5b07f15bcd14abcc34fde14bdf09316c9716d3918460ac80435fedd06。student接口motion_frame25_distilled_v1、25/128/64/32/6ELU/linearmean、leg.5rad/wheel100rad/s，student独立六输出，无history/teacher救场；共享原CommandEnv、USD/PD/限矩不变。requestframe25_student_priority_v2仅评估，不定义在线reward/critic，不可据此启动PPO。

授权后7PORTABLE冻结测试通过、publicplanPASS、submissionREADY，资源快照无compute进程，允许shared而未抢占其他任务。actual220模块与authorizedCPU冻结逐SHA相同，specSHAb59d8776962690bdf725fec26f4c0e90ad691c6fcbf59d080c47d24ca61c7097。此前shared943pass/8skip/22逐IDbaseline一致。新声明spec/budget/receipt只读，所有结果成功atomic保存，参数不变。

## 最早偏离与证据边界

全部6casepreactionframe与执行clip/previouscache/前一步postq对齐最大差0，dq缩放最大1.43e-7；没有已测input/cache/scale错位或runtimefault。studentzero首动作相对teacher很近：腿平均差.000237rad、轮.0372rad/s。随后两条实际轨迹按同policyindex比较，轮target差>5rad/s最早pretime.01s，tilt差>.05rad在posttime.14s，腿target差>.05rad在pretime.24s。到post.50s studenttilt约.243/teacher.039rad，post1.38s studenttilt约1.087/teacher.035，studentheight约.240m。

这是事件顺序和条件输出差，不是轮误差导致倾倒的唯一因果证明，不能把不同轨迹状态的动作差当作同状态监督误差。另一CPU诊断将teacher在student真实状态及连续重构legacyhistory上query，前.05s腿MAE约.0281rad、轮8.336rad/s，前.10s轮11.277rad/s；说明离开原BC数据后拟合误差明显，**不证明teacher在任意这些offpolicy状态均有正确专家能力**，不自动把它们加入正示教。

旧BC使用.40m原状态/.34m重新query标签：teacher实际动作反馈与.40m状态/previousaction来源不一致，是已知数据分布缺口。当前不能从失败断言25D必然不足；先用实际.34m成功闭环的数据替换counterfactual教学，再判断历史是否必要。

## 下一单变量

优先真实.34m成功teacherpreframe25→actualphysicaltarget重新蒸馏，保留同25D网络/单位/loss/seed/优化预算，不同时改PD、量化、历史或reward。actual034_teacher_sources.json已登记五命令40个成功episode与逐文件SHA，数据里确有.34m输入和对应实际执行输出；不是再次使用.40状态改height标签。下一轮先认证studentzero，再评估运动。此报告未执行新增BC或物理/PPO。

现student不accepted、不替代原teacher、不供实机；原ONNX可作工程样品，不能以导出数值通过代替稳定性。部署限高启动另外验证。

## 文件与统计

机器：student_priority_completed_review.json、student_teacher_final_comparison.json、student_effective_command_check.json、zero_student_teacher_divergence.json、same_student_state_teacher_query.json、actual034_teacher_sources.json及actualidentity/resource/receipt；原子JSON/NPZ在run。review_student_priority.py/review_zero_divergence.py支持具名numericNPZ的逐step嵌套reference与invalidmask，earlytermination缺测不伪造。

源码和新spec/ledger为前轮已准备的engine_student_priority与12_47，当前授权后未更改执行行为。STATUS记录结果；TOOL_INDEX准确replay入口；此报告仅复盘，旧run/model和活动Motion/Recovery源码不改，未commit/push。

额外工程发现：公共evaluator在评分firstepisodes均已结束后仍运行声明完整3000interval，增加普通失败评估时间。下一CPU工程改进可在全部评分episode终止后提前停止采集，仍按原完整窗口判失败，不能缩短成功验收窗口；本次未修改活动代码或回填结果。
