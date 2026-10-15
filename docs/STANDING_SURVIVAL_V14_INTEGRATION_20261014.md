# v14接入与未授权准备

用户同意继续工程接入，并提示工具链更新。本轮已读最新入口，保留其他dirty changes；未启动Isaac/GUI/PPO、通知或停止进程。

## 最终提案

spec `configs/experiments/2026_10_14-09_37__standing034_survival_quality_v14/spec.json`，SHA `7ad02ce2a88e5ae0aa0203122ef69a488c948b740279d2f248d27f0a89186b18`。拟run同名，当前不存在；budget UNAUTHORIZED、used全0、attempts空。早期09_31声明保留未授权，不用于最终执行。
来源v13/update988，完整路径`runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt`，SHA `2af573b318d7ebd6df7b1a5919c5ea58e873e5d24761905ba773f8ab02cc72cd`。真实assemble核验Actor全部权重/std相同，新Critic49/空Adam，LR3e-5；不宣称旧Critic/Adam/RNG或仿真状态完整恢复。
拟1000累计更新（尚未授予新运行额度）：smoke26＋formal974，8192000samples，含warmup；source_eval1800秒、smoke3600秒、formal无墙钟截止、4GiB上限。每100及974评估三组normal各8环境，末三seed复核；两个相隔100更新完整24/24才accepted。26rollout的33.28秒只说明理论足够，wiring仍要求真实30秒normal timeout和Actor更新证据。

## 接入与语义

- v14完整替换旧reward，10个具名raw/density/dt，不叠加旧height/support/Huber。低速质量读取实际world root XY，避免倾斜body投影冒充水平速度；Critic native坐标不变。
- 有效控制3000步正常truncated；严格入口不reset、成功不提前reset，物理失败/fault仍terminated。在线与离线共用14列末1000样本质量检查；ring buffer约3.6MiB，不保存每physics步。
- timeout在reset前clone Critic49输入，storage reward加入gamma*V(terminal_state)，raw reward指标不含bootstrap。跌倒不bootstrap，移除安装PPO的旧time_outs重复支路。done仍切断GAE到下一episode；旧v13行为保持。
- source无teacher forward/baseline前置，仅审核学生合法初始化/真实fault，普通质量未学会不阻断。不是放宽资产/身份或物理安全。
- 完整存活候选间先联合质量通过，再生存及最差质量代价；来源与new/accepted分开，新accepted不能冒充来源。最终复核优先accepted_new/best_new，而不是重新评来源后当新成果。
- metrics具名10项，legacy附加诊断null；normal_timeout、controlled_survival_prefix与quality_hold分开。共享smoke证书读声明额度而非硬编码12。

## 新质量协议

首30秒实际学生控制的固定末10秒逐环境：h MAE≤.02m/峰≤.04m；pitch/roll均值≤.10rad/峰≤.15rad、tilt峰≤.18rad；world水平速度p95≤.30m/s、yaw绝对均值≤.30rad/s；双轮接触≥95%、饱和≤5%；轮差MAE≤2cm/P95≤4cm，镜像MAE≤.05rad/P95≤.10rad，腿长差MAE≤1cm/P95≤2cm；闭链峰≤.005m、机身净空>0。
接触95%、腿长阈值及末窗口为本提案明确选择，不冒充旧协议或已验证最优值。缺完整窗口不通过；仅活着且滚动不通过standing gate。

## 当前工具与验证

复用ExecutionLimits、validate_instance、validate_cpu、ModelAdapter/原子保存与账本owner receipt，预算/cadence/storage不写死在reward版本，不复制源码/测试。准备器默认零写，--write仅发布UNAUTHORIZED；公开提交只用supervisor。
64项定向回归通过；公共最终CPU35passed，schema[]，零写plan config_valid=true/submit_ready=false/run_created=false。PORTABLE最终346passed/8skip。真实storage fixture、runtime终态clone、online/offline一致、world速度、smoke30秒事件和来源选优边界已测试。
CPU证据`artifacts/standing_survival_v14_20261014/cpu_complete/`。没有真实v14物理/学习或通知证据，不保证快速收敛。Actor仍没有直接线速度/历史，gamma=.99不暗改。

## 精确修改范围

新增students/standing_survival_task.py、scripts/prepare_standing_survival_quality.py、tests/test_standing_survival_training.py。
修改students/recovery_task.py、runtime.py、training_recipe.py、requests.py、evaluator.py、training.py、training_evidence.py；保留各文件已有其他hunk。上一轮standing_survival_reward.py核心不改变物理接口，本轮实际消费。
文档AGENTS/TOOL_INDEX/STATUS/ARCHITECTURE、设计稿及本记录。不提交Git、不删除历史产物、不修改旧spec/ledger。

下一步审核新增预算/GPU及通知owner范围，再登记/check-submission/一次detached提交；同意工程接入不自动授予新的1000更新。

## 新授权与首次提交

用户随后明确“授权1000次更新”。已公共登记smoke26＋formal974，inclusive1000/8192000samples；授权后spec SHA `8ae7f0d00bcfe7b22dba33f3df7210e41c58cbfc0292c952e310dded73739020`，注册receipt保留授权前SHA，不伪造原发布身份。
公共preflight PASS/check-submission READY，GPU0共享、UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72、逻辑cuda0；只一次detached提交与30秒有界握手。实际启动证据在`artifacts/standing_survival_v14_20261014/launch_receipt.json`，账本不借原v13额度，不自动追加/重试。
本spec notifications.enabled=false，终态报告自动保存，但没有自动HAPI通知；没有擅自改动已授权/活动spec启用通知。提交不等于formal首更新或能力通过，不轮询进度。

## 用户追加通知与TensorBoard

用户明确授权后，以独立terminal_subscription.json启用事件通知，不改活动spec。systemd user native-terminal-0fddb8e8408e.path已active/waiting，report_ready后绑定SHA发送当前owner191bacc3-e5c7-4b8f-ae3d-5677eada837b一次通知，并停止自身path；不轮询训练，不重发unknown。receipt及启动证据在artifacts/standing_survival_v14_20261014。
TensorBoard http://127.0.0.1:6006 HTTP200已验证，server77469、smoke/formal桥77467/77468，复用已有JSONL只读viewer，产物同artifacts/tensorboard。未有更新时页面可以为空，不冒称formal已训练。
新增scripts/subscribe_training_terminal.py和tests/test_terminal_subscription.py；3passed覆盖一次投递、未知不重试、SHA拒绝与spec未修改。更新TOOL_INDEX/STATUS/本记录，无训练代码修改或Git提交。
