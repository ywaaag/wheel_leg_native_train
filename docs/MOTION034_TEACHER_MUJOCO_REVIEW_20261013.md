# 当前0.34m Motion教师MuJoCo验证

用户明确授权“尝试MuJoCo验证”，并指定项目sim2sim目录。实际run：sim2sim/2026_10_13-19_46__motion034_teacher_mujoco；source为05_39/block0003/formal/update300 SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb，与部署ONNX对应，不是旧B250。

复用scripts/validate_native_mujoco.py、只读wheel_leg_sim2sim MJCF。CAD/native观测轴/COM速度/150D历史/实际6joint/原reference/.5rad-100rad/s/PD60-2-1/1-5-10ms/40-5.5Nm保持；gear仅单位转换，不加补偿、filter或初态优化。原Motion原生root.40仍存在，不认证实机.36启动限高。CPU6适配器测试与零写plan通过。对.34新诊断明确heightmean范围.32–.36；旧.4诊断保持.34–.46，旧run不改。新版本native_mujoco_height034_v2，8秒10–18s保持窗（不是Isaac10秒10–20窗），速度门槛zero.5/运动.3，因此不能直接跨协议比较通过率。

一次CPU headless有界物理运行，五命令单确定性env各30秒，共150000physics step/15000policy sample，wall26.1535秒，PPO0/optimizer0，最大600秒；无GPU/真机运行，源checkpoint/外部XML/mesh未改，输入SHA结束后全部复核一致。状态COMPLETED/all_windows_completed=true/all_passed=false/capability_certified=false。

|命令m/s|实际vx|MAE|平均高度m|双轮接触|诊断失败|
|---:|---:|---:|---:|---:|---|
|+0.0|-0.4684|0.4684|0.3496|1.00|[]|
|+0.5|+0.1578|0.3422|0.3519|1.00|['SPEED_ERROR']|
|-0.5|-1.0190|0.5190|0.3465|1.00|['SPEED_ERROR']|
|+1.0|+0.7891|0.2109|0.3547|1.00|[]|
|-1.0|-1.4881|0.4881|0.3438|1.00|['SPEED_ERROR']|

全部不摔、双轮>5N接触率1，保持高度范围通过；zero虽然以宽松.5速度门槛诊断通过，持续-.468m/s后滑绝不是实机零速站稳通过。+.5/-.5/-1失败速度误差；+1MAE.211在.3门槛内。轮前后错位约4.2–11.2cm，原对称问题未解决。全程最高rootheight约.39982m，仍无≤.36实机峰高证据。

45个实际MuJoCo pre-action150D输入，对照交付actor.onnx与实际checkpoint raw输出最大差1.19e-7，故导出数值差异不是这些明显速度偏差的解释。该对照CPU读数据，不增加物理样本。

结论：能在该参考MJCF保持轮支撑，但速度迁移明显后偏，当前模型未通过完整sim2sim运动认证，暂不把MuJoCo结果当真机可直接部署。参考MJCF的contact/friction/damping/armature/inertia/collider/solver与原物理资产严格动力学parity未认证。下一最小诊断是同源零命令配对状态和相同PD目标响应，优先核对轮速度/接触/驱动单位及动力学差异；不要未经证据自动加static trim、改PD、提高限矩或改网络掩盖后滑。本次没有自动下一轮仿真/训练。原deployment_protocol仅实机内容不放仿真报告，验证报告在docs/sim2sim。
