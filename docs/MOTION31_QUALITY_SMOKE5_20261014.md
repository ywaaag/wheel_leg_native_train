# Motion31质量v3：5次短接线smoke

用户明确授权启动，smoke最多5次，并多次指示继续。本轮修复已失败source评估的协议汇总错误，重新准备并提交独立链，不修改历史spec/run/账本。

## 父链失败与实际消耗

事件`a3c9e404403ddccb670f2c52`对应20_04姿态质量v3，来源评估后序列化触发`NameError: name 'spec' is not defined`。`evaluator._rollout(env,actor,row)`没有spec参数，却在新protocol表达式读取spec；这是本worker的接线错误。未进入smoke/formal，在线PPO0，不是奖励不收敛或姿态能力失败。没有完整来源JSON/trace可复用，不拼接半写证据。

已修为读取实际env显式quality_config版本来生成协议，CPU直接执行真实AST中的表达式，在没有spec变量的命名空间覆盖新旧两种协议。旧FAILED保留。之前stop检查发现父链已结算，无活动attempt，未发送信号；receipt `artifacts/2026_10_14-20_16__motion_smoke5_stop/stop_receipt.json`。

历史更新仍50；累计墙钟1671.552394867秒，包含20_04失败评估301.022886515秒。新链预算：smoke5＋formal≤1900，新online≤1905；加历史50≤1955，原2000中45次不自动使用。剩余墙钟63128.447605133秒约17.54h，2GiB，不重置原18h约束。

## 新声明

- spec：`configs/experiments/2026_10_14-21_14__motion31_posture_quality512_v3/spec.json`。
- run：`runs/2026_10_14-21_14__motion31_posture_quality512_v3`。
- source：`isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt`。
- source SHA：`a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`。
- Actor31D / Motion49 Critic，512env×128steps，0/±0.5/±1，GPU0共享→CUDA0，UUID`GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`。其他compute任务不停止/抢占。
- v3奖励、质量终止、物理、动作尺度、限矩、PD、PPO、LR、std、归一化保持20_04声明；仅短smoke接线profile改变，formal初始化语义不变。
- 后台来源新协议完整评估→smoke5→新wiring校验→formal1900。旧来源未认证不阻止学习；来源工程fault则停止。正式每100更新完整五命令、1900终点；不解锁速度/不自动重试。

## 短smoke的明确边界

显式`motion31_quality_short_wiring5_v1`只在新quality recipe启用：smoke前4次Critic warmup，第5次真正Actor更新；formal仍前5次Critic warmup，重新从原始来源初始化，不继承smoke模型或缩短formal warmup。

必须有真实Actor/Critic更新、非零reward、pre-action valid mask对账、五cohort保持段样本、checkpoint roundtrip、独立评估结果身份和协议。证书使用动态16项reward字段，修复原证书只认可旧14项的潜在阻塞。

5×128×0.01=每env6.4秒，不能证明完整30秒training episode/reset/timeout。短证书不强制声称这些事件已发生；分别输出实际episode完成数、normal timeout数、reset_observed、timeout_bootstrap_observed，`full_training_episode_verified=false`。独立物理评估虽可覆盖完整窗口，也不冒充训练storage timeout路径。CPU继续验证真实失败transition不被删、正常timeout bootstrap、质量失败优先。

## 验证与可见性

全PORTABLE445 passed、8 skipped；新声明绑定CPU checkpoint/Actor/std/新Adam/实际LR3e-5核验通过，零写supervisor plan PASS。全链未压缩含reserve估算1,863,314,432bytes≤2GiB。实际启动reward快照：`artifacts/2026_10_14-21_14__motion31_posture_quality512_v3/reward_snapshot_authorized.json`。

既有后台负责预算/评估/结算和终态通知owner`191bacc3-e5c7-4b8f-ae3d-5677eada837b`；只做一次30秒提交握手，不轮询log/progress/PID/GPU。回执同名artifacts `submission_handshake.json`，CPU `cpu/validation_result.json`。SOURCE_EVAL不代表formal已更新，不代表能力通过。

TensorBoard复用`http://127.0.0.1:6006/`，新实验Text registration预先显示配置；smoke/formal真实metrics出现后自动显示reward与姿态等曲线，不补造零数据。

实际握手worker31704、submitted/submission_verified=true、state/current_stage为SOURCE_EVAL/source_eval，formal_first_update_verified=false；不把提交当作formal已经更新。一次HTTP检查旧6006连接拒绝，已通过相同解释器detached提交新TensorBoard server，回执`tensorboard_server_submission.json`，只读viewer不控制训练。

## 本轮改动文件

- `src/native_stand/students/evaluator.py`：实际env协议读回，消除free spec引用。
- `src/native_stand/students/motion_quality_budget.py`：只接受已结算user stop/精确source0PPO协议故障，并递归核对历史消耗。
- `src/native_stand/students/motion_training.py`：短smoke profile和分phase warmup。
- `src/native_stand/students/training_recipe.py`：显式profile严格验证。
- `src/native_stand/students/motion_training_requests.py`：5次/50次按声明校验，不放宽旧默认。
- `src/native_stand/students/motion_runner.py`：smoke4/formal5 warmup dispatch。
- `src/native_stand/students/training_evidence.py`：短接线证书、覆盖属性、动态reward字段、报告真实warmup。
- `scripts/prepare_motion31_training.py`：`--smoke-updates 5`，新目录/新授权/独立账本，不修改旧运行。
- `tests/test_motion_smoke5.py`：真实协议表达式和短证书正负回归。
- `AGENTS.md`、`STATUS.md`、`TOOL_INDEX.md`及本文。无Git提交。

剩余物理证据：短smoke真实接线、formal是否进入、坏姿态终止后能否收敛均UNKNOWN。工程测试通过不能代替这些行为结果。
