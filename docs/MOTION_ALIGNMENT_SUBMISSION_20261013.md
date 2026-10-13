# Motion关节与轮支撑对齐首块提交

用户明确“继续，尝试开启训练”，覆盖新设计的一次实际执行。旧Motionv4已STOPPED522updates/formal472/4276224samples/6801.65075秒，保留原账本/旧FAILED与模型。Recovery独立任务未改变。

## 实际接线

独立完整公共bundle manual_train/motion/standing034_alignment_engine_v5，复用supervisor→stand_chain→CommandEnv→原PPO，不另造trainer/监控。版本motion_standing034_alignment_course_v3，gate motion_standing034_alignment_v3。实际reward模块新增named hip_mirror/active_mirror/worst_joint/wheel_heading四日志项，runtime真实提供postphysics/prereset q和轮心几何；无效数据明确失败。evaluator保存geometry并计算轮差固定窗MAE/P95；publicgate分别检查两关节和wheel，不靠平均抵消。

原镜像项分开记录、密度相同−.5H(eHip/.2)−.5H(eActive/.2)；新增−.5max(Hip,Active)及−.5H(relu(abs(wheelForwardDiff)−.01)/.10)，dt.01一次。原站立reward/PPO/std/network/PD/USD/限矩不变。不加hardmirror或滤波。高度命令.34，64zero。来源仍原05_39/update300 SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb，新Critic/Adam/RNG、5critic-only warmup；source/smoke/formal独立初始化，不用smoke末模型。

新联合验收：固定10–20s保持窗，两关节各MAE≤.05/P95≤.10rad，wheel前后MAE≤.02/P95≤.03m，zero meanabs vx≤.05m/s、vy≤.02、yaw≤.03；meanheight.32–.36且保持每sample≤.36m，原物理检查保留。注意原Motion真正zero门槛字段是zero_mean_abs_vx_max_mps，不能只改vx_error_max_mps。CPU反例已覆盖。新保持峰高不证明合法启动或完整实机高度通过。

选模先jointpassed、physical/zeroeligible，再hip/active/wheel最差归一化偏差。首块完成停止复盘，不自动继续下一块。

## 验证

奖励设计5CPU测试；actualreward、schema未知字段、freshAdam/criticwarmup、publicgate的wheel/速度/高度反例及源码边界测试18通过。相关公开调用42passed/1deselected（硬编码shared源码root项不能在独立bundle冒充portable）。实际冻结PORTABLE18passed，preflightPASS。shared全量943passed/8skipped/22errors，逐ID与修复前baseline完全相同，未放宽SHA或掩盖生产错误。离线重放4完整固定窗各8000sample，1不完整拒绝，参数不在运行中自适应。

新发布由公共准备/授权消费真实配置，零写planPASS/files_written0，提交检查READY。GPU0shared，UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES0，提交核验可用28657MiB，未抢占/换卡。

## 提交与额度

spec：configs/experiments/2026_10_13-11_19__motion_standing034_alignment_block0000/spec.json；SHA cbffbabcee1da3ee579223147d56785f54ba77b17752d4fb47df13b76bd351d8。
run：runs/2026_10_13-11_19__motion_standing034_alignment_block0000。
task：manual_train/motion/tasks/standing034_alignment_final_20261013，历史绑定旧账本SHA和实际消耗，首块有限325update，不从旧余额扣用。

source_eval≤1200s；smoke25≤1200s；formal300≤11700s；整链≤14400s/4h，2662400rawsamples，产物≤2GiB；source8评分环境，smoke8＋formal100/200/300各8。普通未学会不阻止formal，工程错误/预算/用户STOP准确保存退出，不自动重试。

一次30秒握手submitted=true/submission_verified=true/SOURCE_EVAL，formal首更新尚未确认。实际冻结221模块与CPU副本逐SHA一致。worker没有进一步轮询。既有owner负责评估/保存/退出/结算；通知disabled。

## 文件

新v5完整副本增量：motion_course/alignment.py、symmetry.py、domain.py、io.py；command_v6/domain/reward.py、protocol.py、evidence.py；runtime/env.py、tools/evaluate_checkpoint.py。测试/冻结/plan/receipt目录alignment_execution_20261013；此前设计与replay目录alignment_design_20261013。STATUS、TOOL_INDEX、ARCHITECTURE、WORKFLOW、manual_train/motion/README及本报告更新。未改共享src、旧run/checkpoint/spec/ledger；未commit/push。
