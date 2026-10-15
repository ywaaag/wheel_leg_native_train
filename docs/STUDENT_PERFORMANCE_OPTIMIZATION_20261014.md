# 学生训练与评估性能优化

用户明确要求减少GPU→CPU传输、训练统计GPU聚合、评估串行开销，并允许GPU1使用。仅新增默认关闭student_performance_v1配置；不热改当前站立spec、ledger或已加载训练代码，不停止/重启同事任务。实际GPU1性能物理验证为新Motion PPO0声明，不新增PPO更新。

## 具体接入

1. DeviceTrace按字段预分配GPU缓存，保留原dtype和policy_sample/scored_env/feature轴；每步copy_仅8评分env，采集后按字段批量传回CPU。默认256MiB缓存上限，超限拒绝而非漏字段；first_episode_valid、pre/post、控制/几何及失败前完整区间保持。异常时仅输出已完成interval；首步失败只输出真实pre-action，不伪造post状态。在线安全/nonfinite/initialization检查频率不变。
2. RolloutCounts GPU累积有效样本、非零reward、done、entry/complete/success、短腿、handoff；episode duration预存128×env，rollout末CPU一次读取，保持原done顺序/样本。原浮点reward累计、PPOstorage/log_prob/advantages未动；物理分支和mask.equal断言仍同步。故障tail可选最近32步在GPU clone，出错再整块CPU保存；旧默认关闭。
3. EvaluationEnvironment复用同kind/role/family的normal独立学生环境，每case重新seed/reset；家庭/控制语义变更则close/recreate。course/teacher混合任务不允许开启复用；成功/异常均单owner关闭，RNG/actor模式由原rollout清理恢复。没有减少case、8env、30秒、评分字段或改变阈值。CPU等价不证明PhysX场景复用在所有初态完全一致，所以新物理验证结果尚待回收。
4. 训练每update记录rollout+statistics/PPO host wall计时；评估记录environment acquire、rollout/scoring/transfer、保存耗时及实际create/reuse次数。非CUDA kernel独占计时，不虚构历史分项。
5. 公共Motion31准备器支持--physical-gpu1和--gpu-uuid，CUDA_VISIBLE_DEVICES=1映射逻辑cuda0，公共supervisor核UUID/资源/授权。学生GUI可显式物理GPU1，必须与spec声明匹配，不自动切GPU。旧GUI CPUfixtures补显式device并验证GPU1 launcher前映射。

## 显式配置

```json
{"performance":{"version":"student_performance_v1","evaluation_gpu_buffer":true,"evaluation_reuse_environment":true,"training_gpu_statistics":true,"failure_tail_on_device":true,"trace_buffer_max_bytes":268435456}}
```

旧spec没有performance全部关闭；合法性能字段只改变证据传输/统计，不影响reward/采样/网络/std/optimizer/RNG。训练聚合需在下一次明确授权的新声明启用；当前站立不会自动启用。GPU1本轮PPO0只启用评估两项，training字段为false。不能直接用这份配置把活动run变为另一实验。

## 实测和验证

GPU1（RTX3060）纯张量微基准：8评分env、18字段、1000步、三次，legacy中位.18524秒、buffer .10336秒（约1.792倍）；逻辑host传输18000→18，全部数组exact equal。这是无PhysX/Actor/PPO的传输子系统基准，不是整场训练1.79倍或每case数分钟节省的证明。脚本benchmark_student_trace_transport.py，结果artifacts/student_performance_20261014/gpu1_tensor_transport.json。

CPU回归覆盖真实rollout旧/缓存路径字段值与dtype完全一致、RNG/模式恢复、mutable-source克隆、提前done掩码、完整故障interval、pre-only、容量拒绝、GPU统计与原统计逐项一致、真实evaluate_cases环境复用/异常关闭、GPU1显式映射及原站立bootstrap。期间失败fixture分别为旧GUI未声明device与测试output上层共享临时目录占用了小容量，已修fixtures，不放宽生产容量/身份约束。最终结果以portable_verified.txt/cpu_final为准。

## 独立物理检查

configs/experiments/2026_10_14-15_03__motion31_u300_fixed_command_ppo0/spec.json：同冻结迁移Actor与既有0/±.5/±1固定命令协议，physicalGPU1 UUID GPU-dfc076b6-b082-3065-512a-e21064067db1、逻辑cuda0，40episode/PPO0，3600秒/512MiB。普通能力失败继续矩阵，runtime故障立即停止，不自动重试；原GPU0结果和本次GPU1不能直接用终态墙钟算纯优化倍数（设备/并发不同），重点核验完整产物、评分/初态、复用次数与分项计时。

公共CPU→plan→授权登记→check-submission→detached一次握手→既有monitor收尾/通知，不新增worker轮询或watcher。旧报告/账本/训练模型不覆盖。

## 修改文件

新增students/performance.py、tests/test_student_performance.py、scripts/benchmark_student_trace_transport.py。
修改students/evaluator.py/training.py/requests.py/storage_resume.py/play.py、scripts/prepare_motion31_validation.py、tests/test_student_preview_publication.py；文档为本报告/TOOL_INDEX/WORKFLOW/STATUS。没有改变PPO/物理/env数量或reward，没有Git提交。

## 实际提交及最终CPU

{
  "status": "SUBMITTED_EVALUATION",
  "monitor_pid": 539818,
  "attempt_id": "19d4d159db2f43fa8762d8ee0408a874",
  "monitor_identity_verified": true,
  "command": "/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.monitor --spec /home/kellen/wheel_leg_native_train/configs/experiments/2026_10_14-15_03__motion31_u300_fixed_command_ppo0/spec.json --phase evaluate --output-dir /home/kellen/wheel_leg_native_train/runs/2026_10_14-15_03__motion31_u300_fixed_command_ppo0 --attempt-id 19d4d159db2f43fa8762d8ee0408a874 ",
  "physical_gpu": 1,
  "logical_device": "cuda:0",
  "spec_sha256": "4d3851b2fdd9062e4f217ac4e49ac89acc5c981bdfda41a5163529da6f5413f1",
  "online_PPO": 0,
  "behavior_result": "UNKNOWN"
}

最终PORTABLE375pass/8skip、公共CPU26pass、schema[]、零写plan未创建run、提交READY。GPU1仅一次monitor身份/CUDA映射核验；本轮没有守候训练。STATUS两条已授权永久删除历史产物的点击链接改为不可复核文字，保留原历史值。物理行为和实际端到端节省尚UNKNOWN，终态通知回收结果后复盘。
