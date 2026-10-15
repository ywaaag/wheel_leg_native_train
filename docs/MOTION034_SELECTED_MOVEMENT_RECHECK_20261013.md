# 0.34m Motion运动候选选择与冻结复测

用户要求筛选当前运动能力最强的0.34m Motion并测试运动能力。本轮读取已完成0.34m/±2任务原始candidate_registry；以同模型0/+2/-2完整协议通过数排序，次排序同三项速度误差。未用对称专项latest替代运动模型，也未把零速最佳当作高速最佳。selection.json列出所有同协议完整三命令组。

选中07_21 block0004/formal/model_update_100.pt，SHA df60f53cc4bcca08a7ecc07b9d57c7fbbe24f4fa7c0705af64646cb7467e5a3d；旧证据zero8/8、+2为0/8、-2为8/8，共16/24，是相对排名最高的实验候选，不是三命令accepted。前向+2旧证据同时有高度、速度误差和场地边界失败。

对照事实：05_39/u300 SHA4750ee…cafb是此前零速/低速实测较可靠的来源，0/±.5/±1各8/8跨两个PPO0 attempt，不能把该通过说成±2也已通过。不同意义的“最佳”必须明确速度范围与gate。

本次一次PPO0：同一个选中模型，0/±.5/±1/±2各8评分env，64simenv，最大56评分episode/1800秒含清理/512MiB，GPU0共享，无PPO或offline optimizer。沿原motion_standing034_v1评分，30秒观察、10–20秒固定保持窗、.32–.36m保持高度范围；原宽松zero vx.5与motion误差.3等保持，不冒称严格对称gate或实机峰高认证。初始root.40m，未擅自修改姿态。

复用独立完整public bundle standing034_engine_v2副本；增量motion_course/recheck.py显式请求身份、students.course_requests的project_root分派、config严格限定本PPO0才允许.34、evaluator结果存储absolute import修复及512MiB保留清理空间检查。旧run/旧engine/共享src只读。public supervisor提交一次；当前模型与资产SHA、实际GPU UUID/CUDA0/shared及资源检查READY。CPU公共请求/真实模型严格加载3passed，实际冻结3passed。

最终声明2026_10_13-15_12__motion034_selected_movement_recheck_ppo0，attempt8acf4902f2d2437c94f0c8bb757b1e66。普通能力失败继续其余命令；工程故障/预算终止准确结算，不重试。后台既有monitor负责保存/退出，本次有界诊断只等待自己的结束信号；不新建watcher。终态与数字以manual_train/motion/strongest034_recheck_20261013/result.json和本run raw为准，尚不能预先宣称通过。命令只维护TOOL_INDEX。

历史hold_mean_abs_error在zero组可能保存yaw误差，不能通用视为vx误差。最终review使用具名mean_vx_mps和mean_abs_vx_error_mps。选中模型在通过数16/24上唯一领先，字段问题未改变本次第一排序选择。

## 本次实际终态

COMPLETED，attempt8acf4902f2d2437c94f0c8bb757b1e66，账本结算1501.6963秒（约25分02秒），56评分episode/40通过，PPO0/optimizer0，输出67268276bytes（约64.15MiB）；64simenv、8scoreenv，全部模拟env-step1344000/评分168000。七组均完成30秒，原checkpoint文件SHA前后相同，无工程异常/未运行项。

|vx命令|实际vx|vxMAE|平均保持高度|通过|
|---:|---:|---:|---:|---:|
|+0.0|-0.0895|0.0895|0.3558|8/8|
|+0.5|+0.4415|0.0585|0.3588|8/8|
|-0.5|-0.5985|0.0985|0.3517|8/8|
|+1.0|+1.1336|0.1391|0.3615|0/8|
|-1.0|-1.0527|0.0637|0.3490|8/8|
|+2.0|+3.4347|1.4347|0.3689|0/8|
|-2.0|-2.2326|0.2521|0.3465|8/8|

+1失败为height_steady_mean/fraction；+2还失败hold_absolute_error与max_excursion。各case均双轮接触1、100Hz采样触限0，但这些不替代严格对称/实机限高证书。零速后滑.0895m/s仍通过原宽松.5门槛，不能称高精度零速。

选模结论：07_21/u100是已有0/±2联合通过数最高的实验候选，但本次+1/.34超高，不适合双向统一采用。优先低速双向运动与站稳仍保留05_39/u300 SHA4750ee…cafb，已有0/±.5/±1各8/8，证据来自之前两个独立attempt、不是此次同attempt模型对照。不能声称其±2通过；没有0.34m三端点全部通过模型。下一单一重点为限制前进时高度及速度超调，而不是立即采用对称专项latest；本次未启动下一训练。
