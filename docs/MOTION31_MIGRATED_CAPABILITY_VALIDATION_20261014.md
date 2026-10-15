# 迁移31D Motion模型独立PPO0验证

用户明确同意按AGENTS新工具链验证，验证预算不限。此次选择一次有界矩阵而非无界任务：0/±0.5/±1m/s，固定yaw0、高度.34，每命令8评分环境、64实际环境、30秒受控窗口、同seed20261014；3600秒运行安全上限/512MiB评估产物上限。在线PPO/optimizer0，不消费Recovery更新预算；普通能力失败仍继续剩余命令，runtime/初始化/非有限物理故障立即停止。

来源独立Motion Actor：isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt，SHAa7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266，原Recovery来源64f96ac…7829f。新声明configs/experiments/2026_10_14-13_47__motion31_u300_fixed_command_ppo0/spec.json，同名run/独立ledger。没有重新蒸馏或训练。

## 显式接线与测量

新student_motion31_validation_v1声明启用Motion role的真实vx/yaw/height命令；旧Recovery与其他学生默认零命令路径不变。Actor输入22～24为command/[4,4,.5]，模式25Motion=1、26Recovery=0；实际采集Actor输入逐样本readback核验，否则runtime拒绝。Critic49输入布局显式继承、不加载或训练Critic，计时仍原standing字段语义不冒充新Motion价值定义。

独立固定命令诊断：第5～30秒tracking，末20～30秒姿态/几何/接触/限矩；完整30秒存活要求不缩短。零命令worldXY模长p95≤.3，非零MAE≤.3、方向率≥.9、均值有符号增益.8～1.2。v14姿态/高度/轮差/镜像/腿长/接触/closure/间隙原门槛保留；运动时不拿水平速度≤.3误判非零命令。协议不能认证停车/急启停/高速/yaw。逐环境独立报告，不能用总体速度均值替代8/8。

v14 Clock只为此次PPO0的完整30秒终止/物理安全提供环境接线；reward不优化、物理动作不变。原standing online质量事件不是Motion gate，明确使用独立Motion评分，不能把两者混称证书一致。固定命令起点可能导致任务失败，仍如实保存。

## 新工具链

prepare_motion31_validation.py默认零写，--write只发布新未授权spec/ledger/marker；validate_cpu共享src/无源码复制→授权登记→supervisor --evaluation-only --check-submission→detached监控子进程。monitor结算后仅此显式Motion诊断调用精简report/notify，at-most-once通知当前owner；不另建watcher、不轮询训练日志。不会改现有Recovery spec/ledger/进程/已加载配方。

CPU：定向Motion/preview/runtime16通过；PORTABLE365通过/8跳过（加入末项report缺case回归之前），最终公共validator见artifacts/motion31_validation_20261014/cpu_final/validation_result.json。测试覆盖task接线、零/非零分母窗口、反向/近零增益、短窗口不能通过、缺case报告不能accepted、离线迁移与无教师preview。

## 改动

新增students/motion_validation.py、scripts/prepare_motion31_validation.py、tests/test_motion31_validation.py；增量students/runtime.py/evaluator.py/requests.py和command_v6/monitor.py。AGENTS增加显式Motion49D PPO0特例，TOOL_INDEX/STATUS导航及本报告。旧reward/PPO/物理/动作scale/网络不改。未提交Git，所有实际运行事实以receipt/terminal/raw JSON为准。

剩余：真实物理结果尚未完成；迁移函数等价不是已学速度响应，尚无Motion在线训练配方或预算。

## 实际提交

{
  "monitor_pid": 361797,
  "attempt_id": "93489e00c53a4af0978586c14a486766",
  "command": "/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.monitor --spec /home/kellen/wheel_leg_native_train/configs/experiments/2026_10_14-13_47__motion31_u300_fixed_command_ppo0/spec.json --phase evaluate --output-dir /home/kellen/wheel_leg_native_train/runs/2026_10_14-13_47__motion31_u300_fixed_command_ppo0 --attempt-id 93489e00c53a4af0978586c14a486766 ",
  "run": "/home/kellen/wheel_leg_native_train/runs/2026_10_14-13_47__motion31_u300_fixed_command_ppo0",
  "spec_sha256": "eb0b702bcb3e688283aeb232ef10fc225e3585658167b5aa681e05cce6d72d8c",
  "monitor_identity_verified": true,
  "physical_gpu": 0,
  "logical_device": "cuda:0",
  "online_PPO": 0,
  "assessment_passed": "NOT_YET_KNOWN",
  "status": "SUBMITTED_EVALUATION"
}

最终公共CPU10pass，schema[]、零写plan/提交READY。health原把学生role硬编码RecoveryStudent而拒绝迁移Motion；本轮修正显式Motion来源角色，逐tensor核验准确列迁移，蒸馏数据仍回溯原Recovery角色，不跳过身份。增量health_check.py，相关定向8pass。一次monitor PID/argv/attempt/output/spec/CUDA核验已通过；尚无物理结果，不报告能力通过。后台monitor结算后写completion/report_ready并at-most-once通知当前owner，worker不轮询。
