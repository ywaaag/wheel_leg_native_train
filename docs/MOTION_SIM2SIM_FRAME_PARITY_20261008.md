# Native Motion MuJoCo坐标修复与配对证据

2026-10-08。用户批准下一步parity并允许在native项目新增sim2sim目录。
本轮复用已结束的Isaac原始证据，新增CPU MuJoCo验证；无新Isaac/GPU仿真、PPO或通知。
一次资源快照GPU1有compute进程，不抢占、不切GPU0；没有读取后台训练进度。

## 已确认并修正的适配错误

上一轮我误用了参考Fudan runner的CAD→canonical旋转作为native actor输入。
冻结native `_motion_state`实际为：angular/gravity直接取原CAD body-frame，
up=-gravity[1]、vx=-linear[2]、vy=-linear[0]、yaw=angular[1]。
因此直立初始gravity必须[0,-1,0]，而不是[0,0,-1]。
现已修正scripts/validate_native_mujoco.py；canonical旋转仅用于roll/pitch及轮心几何报告。
旧run及旧报告保存；新增本报告更正，不宣称之前0.18秒失败证明B250不可迁移。

## 配对身份和检查

来源B250：runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt。
SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。
Isaac原始数据：runs/motion_recheck_20261007_gpu1/attempt1/evaluation_00.json；
对应model SHA一致，100Hz的3000时间×8环境×54控制字段，24,000条记录。
最终parity输入路径与SHA在sim2sim/2026_10_8-17_07__motion_b250_frame_parity/corrected/parity.json。

- 8env首动作与正确CAD零状态CPU actor输出，最大通道差各1.490116e-7。
- 错误canonical输入首动作与env0记录最大差2.044774；会把轮动作推入clip边界。
- reset history重复5帧，当前frame/history输入长度25/125，与actor150D匹配。
- USD/MJCF 38个对应转动joint axis差最大1.224647e-16，包含实体主动及被动关节。
- 24,000条native clipped_action→四腿target变换误差0，physical_clipped→实际执行器误差0。
- MuJoCo轮gear换算保持输出限矩5.5Nm，实际qfrc_actuator与PD限幅请求差0。
- 安装版Isaac root_lin_vel_w是root_com_lin_vel_w别名；MuJoCo mj_objectVelocity返回
  body COM速度。测试按COM偏置cross项核验，不误把freejoint原点速度当COM速度。

这是静态/首帧/控制输出证据。原始数据没有每个policy actor输入及完整root quaternion，
不能宣称整个动态root/observation历史已经逐步配对认证。native q/dq为policy末端，
torque为前一5ms持有值，不能用末端q/dq反算精确历史PD时刻请求。
没有利用缺失历史字段伪造配对状态。

## 修正后真实MuJoCo结果

独立run：sim2sim/2026_10_8-17_10__motion_b250_corrected_mujoco。
同一只读参考MJCF（SHA663e121ef9aed4bfab09ff0d3d98321b7ce77d80b63584235e4da691bd3aebf3），
原1ms物理、5ms PD、10ms actor，原40/5.5Nm、动作尺度、零位；无物理或奖励调参。
墙钟43.1877秒（测试主体，不含外层初始化），330000物理步、33000policy样本，PPO0。
每个命令单个确定性环境，各完整30秒，双轮保持接触率均1.0，没有同前次的joint_safety提前失败。

|command m/s|保持vx|MAE|roll绝对均值rad|轮心前后错位绝对均值cm|速度误差诊断|
|---|---:|---:|---:|---:|---|
|0|-.2077|.2077|.0016|6.21|低速滑行门槛内，但持续后滑|
|+.5|.2585|.2415|.0115|5.94|≤.3|
|-.5|-.6930|.1930|.0146|6.96|≤.3|
|+1|.7446|.2554|.1413|6.08|≤.3|
|-1|-1.2489|.2489|.1709|9.29|≤.3|
|+1.5|1.2909|.2091|.2570|6.36|≤.3|
|-1.5|-1.8919|.3919|.2171|12.48|失败|
|+2|1.9148|.0852|.2969|7.09|≤.3|
|-2|-2.5464|.5464|.2166|15.74|失败|
|+2.5|2.6267|.1483|.3151|8.22|≤.3|
|-2.5|-3.1217|.6217|.1951|18.00|失败|

全部11命令流程COMPLETED，不等于全能力通过（all_passed=false）。非零保持方向率均1。
zero停车abs vx约.208，运动停车约.20–.23；漂移、全部姿态/控制轨迹见独立JSON。
轮心几何为当前upright/body-heading-frame水平前向分量，不是世界固定轴或腿长差。
零命令6.2cm错位支持“MuJoCo上存在剪刀腿构型”，不替代用户在Isaac观察的5cm量测。
较高正向roll偏斜约.30rad，与速度误差分别报告，不因速度gate通过就称姿态理想。

## 结论边界与下一步

**已确认实现错误**：首轮sim2sim actor坐标基错误，已修，真实轨迹结果随之改变。
**运行证据支持**：修正后B250在参考MJCF可完成30秒且保持双轮接触，但有共同后滑偏置、
负向高速度超速、roll歪斜与真实轮心前后错位。
**待验证机制**：MJCF/PhysX动力学差异或策略自身不对称对上述现象的贡献。
**UNKNOWN**：严格惯量/碰撞parity、整个动态actor输入逐帧匹配、跨seed能力、±4/yaw。

参考MJCF仍有摩擦1.1、DOF阻尼/armature、碰撞proxy和软约束差异；原native材料配置.5/.5。
本诊断gate是子集，不是完整Isaac gate，非轮body-contact等检查尚未等价认证。
新结果不授予课程晋级，不更改训练gate，不恢复/停止当前训练。
下一步先用这套MuJoCo工具诊断同源策略的roll/几何与共同偏置，
需要跨引擎动态归因时再明确预算采集短Isaac配对窗口，不先加控制补偿或几何奖励。

本轮修改scripts/validate_native_mujoco.py、tests/test_native_mujoco_adapter.py；
新增sim2sim/audit_native_parity.py、sim2sim/README.md、独立证据目录及本报告；
更新TOOL_INDEX、ARCHITECTURE、STATUS和上轮报告更正入口。未提交Git。

验证：MuJoCo/键盘相关CPU9 passed（2.35秒），三文件AST、git diff --check通过；
11案例各30000physics steps，8环境首动作证据数量与误差核验通过。
本轮没有重新跑全仓库测试，不把局部CPU回归当物理能力验收。
