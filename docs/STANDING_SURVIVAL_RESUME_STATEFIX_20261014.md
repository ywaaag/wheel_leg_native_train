# v14恢复状态机修复与一次明确授权重试

用户在事件87f9ae90cd4c93d4cdfb8156复盘后明确同意重试。原12_44 FAILED、source663.343秒、PPO0保留；父10_16链已耗312。新13_17恢复声明/独立ledger仅剩688，累计最多1000；原09_37链26次仍作为另一授权历史记录，不重置或擦除。

## 接线修复

stand_chain.worker进入formal前调用students.storage_resume.verify，产生verified_student_storage_continuation_v1并交给RunState。RunState只新增该具名证据版本，普通缺证据SOURCE_EVAL→FORMAL继续拒绝。完整worker CPU fixture覆盖执行source与复用source两条路径，以及恢复证据失败时不调用formal。

学生恢复重试声明student_v14_storage_resume_retry_v2只接受12_44已知SOURCE_EVAL→FORMAL故障且只有一个已完成source attempt、smoke/formal使用均0。绑定原spec/ledger/terminal/source manifest/config/registry/progress、三份JSON及压缩轨迹SHA；checkpoint、协议、三case顺序、8env编号及在线/离线评分一致核验。拒绝行为配置、预算、身份冲突。每个失败恢复spec只允许一次独立发布claim，不在旧claim/FAILED上覆写。

原source评估24例全部30秒生存但质量0/24，不把复用证据当作成功。worker登记SOURCE_EVAL reused后进入formal，不再启动AppLauncher采集来源；trainer直接引用旧candidate_registry，不复制轨迹/源码树，不给新ledger伪造source消耗。

## 恢复配方

来源10_16 formal/model_update_300.pt SHA64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f。CPU真实学生assemble及restore逐tensor核对Actor/Critic/Adam相同，std固定、LR3e-5，无optimizer step。旧RNG缺失仍显式seed重置、PhysX新reset，不宣称完整仿真或随机状态恢复；后续checkpoint保存RNG。

formal688最多5636096samples，不重复smoke/warmup；局部100～600及688评估对应父formal400～900及988。奖励/网络/std/PPO/归一化/物理/10ms均不变。GPU0shared/current owner通知、TensorBoard6006沿用明确授权。只一次握手，不人工轮询或自动再重试。

## 验证和文件

完整worker及chain接口定向17pass；PORTABLE358pass/8skip。公共validator实际结果见artifacts/standing_survival_resume_statefix_20261014/cpu/validation_result.json，schema与零写plan检查运行。test_chain_interfaces非PORTABLE，因此仅在单独项目CPU执行，不伪标或放宽validator的test scope。

修改：command_v6/tools/run_state.py、command_v6/stand_chain.py、students/storage_resume.py、students/training.py、scripts/prepare_student_storage_resume.py、tests/test_student_storage_recovery.py；文档为本报告、TOOL_INDEX、WORKFLOW、STATUS。此前存储修复与其他dirty保留，无Git提交。新spec/receipt/ledger/run为执行产物，不提交Git。

运行事实由单次submission.json握手记录，正式update若未核验须明确标记，不把提交视为站立能力通过。

## 一次实际启动握手

{
  "chain": "/home/kellen/wheel_leg_native_train/runs/2026_10_14-13_17__standing034_v14_resume_statefix",
  "worker_pid": 311681,
  "submitted": true,
  "submission_verified": true,
  "run_state": "FORMAL",
  "current_stage": "formal",
  "formal_first_update_verified": true,
  "started": true,
  "identity_verified": true,
  "reason": null,
  "spec_sha256": "2c7c65390134fc7d69b59e858026e8891a905b607632f2c39c12a82fc2f52777",
  "source_sha256": "64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f",
  "remaining_online_updates": 688,
  "historical_online_updates": 312
}

最终公共CPU33pass，schema[]、零写plan不创建run、提交READY；旧输入SHA提交后核验未变。TensorBoard6006 HTTP200、只读bridge312051，新分组13_17/formal，局部update与父累计指标分别显示。当前owner终态通知冻结启用，未新增训练轮询、未自动追加预算。
