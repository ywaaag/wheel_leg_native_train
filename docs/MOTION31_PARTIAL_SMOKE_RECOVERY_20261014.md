# Motion31部分smoke工程恢复

用户在终态52e44d2dead8055a168c1d48复盘后明确同意执行和开启正式训练。本轮仅修复诊断名称覆盖/计数问题并恢复剩余原预算，不改变冻结奖励/课程/PPO/物理，不从退化候选续训。

## 身份和额度

- 新spec：`configs/experiments/2026_10_14-19_43__motion31_wide_narrow_smoke_recovery/spec.json`。
- 新run：`runs/2026_10_14-19_43__motion31_wide_narrow_smoke_recovery`。
- 父run：`runs/2026_10_14-19_04__motion31_wide_narrow512_2000`，原FAILED、progress0/真实ledger1冲突保留不改。
- 来源：`isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt`，SHA `a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`。
- 历史1次＋新smoke≤49＋formal≤1950，总online≤2000；本链新增≤1999，样本≤131,006,464。
- 父链真实897.444681406秒计入18h上限，新链墙钟≤63,902.555318594秒；产物≤2GiB。
- physicalGPU0 UUID`GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`共享→CUDA0；512env×128steps，0/±0.5/±1槽位128/96/96/96/96，不自动升速。
- 来源Actor/std原样加载，新Motion49 Critic/Adam和冻结seed；父失败仅critic warmup且没有checkpoint，不宣称恢复其optimizer/物理状态。新smoke从原始Actor重新验证，前5次critic warmup仍计额度；formal同样原始Actor初始化，不继承smoke模型。

## 来源复用不等于smoke复用

新增受限版本`motion31_partial_smoke_diagnostic_recovery_v1`：只接受已结算、formal未开始、精确`initial.items()`错误、真实ledger/metrics各1、critic warmup/Actor未更新；拒绝不同故障、改变奖励/PPO/物理、预算重置、重复claim或多次恢复链。

完整五命令来源原始JSON/trace逐SHA、spec/checkpoint/asset/protocol、8环境身份、完整30秒生存全部核验；来源40/40生存、0/40Motion通过。复用只授予SOURCE_EVAL工程证据，不产生wiring pass或能力通过。

后台状态：SUBMITTED→SOURCE_EVAL（复用）→SMOKE（49次真实更新和完整评估）→校验新wiring_certificate→FORMAL（≤1950）→结算/报告/终态通知。formal preflight仍须新链PASSED certificate，不能凭恢复元数据跳过。

原父输入通过单次exclusive claim绑定新声明，历史文件未修改。失败若再次出现，结束结算，不自动重试/追加预算。

## 验证与观察

- 全PORTABLE：431 passed、8 skipped；定向包含chain接口75 passed。
- 绑定新spec/来源checkpoint/Actor/std/新Adam CPU核验通过；smoke preflight PASS，零写supervisor plan PASS。
- 一个未标PORTABLE的chain测试不能纳入冻结CPU发布，保留其单独定向结果，改用明确PORTABLE四项生成验证产物，没有放宽scope。
- CPU证据：`artifacts/2026_10_14-19_43__motion31_wide_narrow_smoke_recovery/cpu/validation_result.json`。
- 授权后实际reward快照：同名artifacts `reward_snapshot_authorized.json`；每次AppLauncher前还会保存phase快照。
- 一次30秒公共supervisor启动握手：同名artifacts `submission_handshake.json`，最终状态以该回执为准。提交/SMOKE不等于formal首更新或能力通过。
- 实际握手：worker925027，submitted=true、submission_verified=true、current_stage=smoke、state=SMOKE；formal_first_update_verified=false、started=false（formal尚未核验）。后台自行校验新smoke证书后进入formal，不人工守候。
- TensorBoard复用`http://127.0.0.1:6006/`，新实验registration先显示声明，真实metrics产生后smoke/formal曲线由已有导入器自动写入。
- 当前冻结负责人`191bacc3-e5c7-4b8f-ae3d-5677eada837b`，既有后台负责通知。本worker不轮询/等待长训。

## 修改文件

- `src/native_stand/students/motion_wiring_recovery.py`：严格partial recovery及SOURCE-only核验。
- `src/native_stand/students/motion_training_requests.py`：互斥恢复字段和预算校验。
- `src/native_stand/students/requests.py`：消费复用来源，formal仍检查新wiring。
- `src/native_stand/students/motion_runner.py`：读取已绑定父来源目录。
- `src/native_stand/command_v6/supervisor.py`：实际初始phase和资源检查phase为smoke。
- `src/native_stand/command_v6/stand_chain.py`：复用来源→真实smoke→formal状态链及含历史计数。
- `scripts/prepare_motion31_wiring_recovery.py`：同一入口显式`--kind partial-smoke`，不新增trainer/提交入口。
- `tests/test_motion_partial_smoke_recovery.py`：CPU负向预算/身份/重复claim/不可跳过wiring回归。
- `TOOL_INDEX.md`、`STATUS.md`及本文。未Git提交，不修改其他任务。
