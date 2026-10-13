# Motion25D学生运动评估：首次失败、修复与新声明

## 实际执行

用户同意测试蒸馏后的运动能力。本轮完成公共25D物理评估接线，新frame25_probe请求绑定student/manifest/teacher SHA。环境仍共享CommandEnv原150D物理接口，student actor显式版本motion_frame25_distilled_v1只读当前policy25、输出六通道.5rad/100rad/s；teacher自己的legacy150D网络和分布，不在学生episode救场，不修改两模型参数。

条件：teacher/student各zero/±.5/±1m/s五组，每组8评分环境、64实际simenv，30秒/组，heightcommand.34。单次PPO0上限80episode/1800s/512MiB，在线PPO和offlineoptimizer0。只有zero教学，非zero是泛化诊断，不冒称已蒸馏运动能力。teacherzero若不通过停止矩阵，其他普通行为失败继续。

新run 2026_10_13-12_04__motion_frame25_student_teacher_ppo0，exactattempt b4288aced0fb4390ad76c27c15a7b6c6，GPU0shared/UUIDe704e7d4-2965-4712-9759-ba6b9910bd72/CUDA0。公开supervisor --evaluation-only --launch --wait有界等待。

**终态FAILED**，实际墙钟412.391636s，产物2985827bytes，零PPO/optimizer。firstteacherzero执行3000policyinterval（192000全部simenv-step、24000评分env-step），但结果保存ImportError，完整评分证据没有落盘。8个教师评分episode标INCOMPLETE；其他9组72episodeNOT_RUN，其中学生40episode全部NOT_RUN。不能说student物理失败、teacher8/8或实机高度通过。

保存actor_capture_00.npz保留actualpreframe25和actualmean6，缺poststate完整评分，不拼历史结果生成成功。manifest、runtime_readback、terminal/monitor_exit/budgetexact结算保存。两模型原checkpoint只读。

## 根因与修复

publicmonitor以Python文件路径启动evaluate_checkpoint.py，__package__为空；evaluate_batch此前from .evaluation_storage仅在保存时执行，CPU模块调用未暴露它。首teacher执行后才触发attempted relative import with no known parent package。

原engine和FAILED旧spec/budget/snapshot只读。另建engine_writefix副本，write_batch_result通过绝对模块导入并复用原atomicNPZ/JSON保存；实际batch调用同一helper。新增runpy.run_path真实文件入口测试，验证__package__为空时保存/回读、SHA/数组对应及重复输出拒绝，不用source字符串代替行为测试。

## 验证

首次30相关/5冻结通过，公共planPASS及submissionREADY，实际执行220模块与CPU冻结逐SHA一致、specSHA58d1f1bdcc2ebd7a3cdae2cb63d818a32d9fac85fbb10bc5b66c4d9da5a0e7f1。全shared943passed/8skip/22逐ID与baseline相同，未放宽SHA。

修复后6源码行为测试及6冻结PORTABLE通过，publicbatch真实10case规划、25D/150D加载、history不影响student、RNG不变、参数不变、按文件启动写结果均覆盖。online请求CPU明确拒绝；critic/reward未声明，不能利用此评估路径启动PPO。

## 修复后准备

新spec configs/experiments/2026_10_13-12_15__motion_frame25_student_teacher_ppo0/spec.json，新budget UNAUTHORIZED/0attempt/0used，无run。相同10组、80episode、1800秒、512MiB，上次消耗另记不借旧余额。engine_writefix、frozen_writefix_cpu、writefix_zero_plan均已生成。公开零写plan READY_NEEDS_AUTH，唯一缺项new simulation/PPO budget has not been authorized；不是工程runnable=false占位。

没有自动再次提交。AGENTS明确旧授权/余额不能授权新运行，原一次请求scope也声明不自动重试。需用户批准这份修复后的新PPO0 attempt，然后正式公共登记/再次GPU资源核验/提交，不重复询问代码和CPU验证许可。GPU0当前共享负载使首项较慢，预算耗尽如实标NOT_RUN，不自动加墙钟或并行抢占资源。

## 文件

本轮独立engine内：students/course_requests项目根验证、command_v6/config显式probe/height，preflight在线拒绝、checkpoint_input绑定25D身份、evaluate_checkpoint混合Actor/capture/write，motion_course/frame25_probe严格数据/model工厂。准备/CPUtest/review脚本、spec/ledger/授权/冻结/原始failedreport均隔离。sharedsrc、旧Motion/Recovery活动冻结与checkpoint没有改。

STATUS记录失败和待运行；TOOL_INDEX准确新命令；ARCHITECTURE记录双接口评估结构。没有commit/push或新CPU训练。实机部署及0.36全程限高仍NOT_RUN。
