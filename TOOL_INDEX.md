# Codex 工具手册

本文件是工具用途、参数和副作用的唯一正文；执行顺序见WORKFLOW，结构见ARCHITECTURE。
所有命令在项目根执行。示例变量必须替换为已核验实际值，不复制历史session/GPU/授权。

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
PYTHON=/home/kellen/anaconda3/envs/issaclab/bin/python
```

模块前缀统一为 `native_stand.command_v6`；CLI参数以当前工作树 `--help` 为准。

## 选择入口

| 工具 | 用途 | 默认副作用 / 显式写入 |
|---|---|---|
| `supervisor` | 唯一公开提交；plan / check-submission / launch | 默认零写；launch预留ledger并启动物理链，须明确授权 |
| `tools.entrypoints` | 当前/内部/历史/退役工具分类 | 只读；--include-historical显示全部 |
| `tools.health_check` | 文档、身份、账本；可选进程核查 | 只读；多任务时显式--spec，不依赖STATUS默认首链接 |
| `tools.preflight` | 当前phase配置/身份/预算/前置检查 | 零写；PASS不代表资源/session就绪 |
| `tools.prepare_motion_experiment` | Motion冻结评估或单阶段课程声明 | 默认零写；--write发布UNAUTHORIZED新目录 |
| `tools.prepare_recovery_retry` | FAILED/TERMINATED已结算phase的重试提案 | 默认零写；--write发布UNAUTHORIZED/零phase额度，不转移余额 |
| `tools.prepare_checkpoint_diagnostic` | Recovery冻结checkpoint/profile评估声明 | 创建未授权新声明；无launch参数，不是Motion准备器 |
| `tools.validate_frozen_cpu` | 冻结源码CPU验证 | 默认零写；--write生成源码/测试副本、SHA、schema/plan/测试报告 |
| `tools.audit_terminal` | 一次终态、事件、逐环境控制与账本审计 | 默认只读输出；--output-dir写新审计 |
| `tools.summarize_run` | phase小文件状态与三类计数 | 一次只读，不证明进程存活 |
| `tools.audit_entrypoints` | 静态引用/历史guard核查 | 默认只读；--output-dir写新审计，不删除工具 |
| `tools.register_authorization` | 新声明统一授权登记 | 默认零写；--write仅在明确用户批准范围内登记，不提交 |
| `tools.compare_arms` | 已结束A/B与共同来源比较 | 默认一次只读；--output-dir写新比较，不轮询 |
| `tools.correct_evidence` | 对已有raw做离线审计/新协议重评分 | 写新output；不覆盖历史结果，不运行optimizer |
| `tools.engineering_recovery` | completed reader错误白名单的受限恢复计划 | 计划零写；发布仍未授权，非通用自动重试 |
| `tools.completion` | 报告再生成/通知/复盘确认 | 默认重写报告；notify发送；ack写review，均不是只读 |

专用Recovery prepare/review工具按 `tools.entrypoints` 与各自--help选择。min-height、geometry、
scissor、wheel timeline和transition的证据范围不同；旧日期prepare仅用于其配方复现。
launcher/monitor/stand_chain/evaluate_checkpoint是内部执行组件，不作为第二条公开提交路线。

## Motion MuJoCo sim2sim诊断

只推荐两个入口：共享`tools.audit_native_parity`作静态／已有证据审计，
`scripts/validate_native_mujoco.py`统一headless/viewer有界运行。旧sim2sim目录中的审计CLI已移除，
历史试算／运行证据保留。这里的迁移诊断不启动Isaac、不更新PPO、不修改外部MJCF。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.audit_native_parity \
 --spec "$FROZEN_SPEC" --checkpoint "$CHECKPOINT" --checkpoint-sha256 "$CHECKPOINT_SHA" \
 --evaluation "$NATIVE_EVALUATION" --native-env-source "$FROZEN_NATIVE_ENV" --xml "$REFERENCE_XML"
# 可选 --output-dir <全新CPU审计目录>；省略则零写入
```

必须显式指定来源与原始证据；核验manifest/checkpoint/asset身份，loader返回具名time/env/channel轴。
旧control缺轴元数据由明确历史生产者契约解析，不能当作新schema或完整动态证据。
输出CAD frame/COM测量contract、关节轴、首动作、目标/torque比较及机器动力学差异表。
如果保存了paired_state，可对最多64个实测冻结输入复算actor；这是CPU重放，不是新物理轨迹。
缺完整双引擎动态输入/root状态仍标MISSING_EVIDENCE；静态误差小不代表动力学等价。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/validate_native_mujoco.py \
 --spec "$FROZEN_SPEC" --checkpoint "$CHECKPOINT" --xml "$REFERENCE_XML" \
 --output-dir "$NEW_SIM2SIM_RUN" --commands 0 0.5 -0.5 --wall-seconds 180
```

默认仅CPU加载模型、静态forward与contract计划，不做mj_step、不创建输出。
--run是实际MuJoCo物理运行，须明确授权；--viewer仍用同一控制／测量循环。
不设“当前最佳”checkpoint默认值。运行使用独立mujoco_diagnostic_budget_v1，不混入native训练ledger；
启动／case计时从计划加载前开始，预留5秒退出保存；各case绑定SHA，异常未知步数标UNKNOWN，预算和终态原子保存。
严格进程级硬超时仍需外部监督；本轮未物理验证清理耗时或GUI关闭。
报告分别列流程完成、完整窗口、诊断gate、能力认证；当前迁移诊断不发完整能力证书。

actor_contract版本native_cad_com_v1：angular/gravity为原CAD body frame，初始gravity=[0,-1,0]；
vx=-CAD_z、vy=-CAD_x、yaw=CAD_y。速度测量点明确为COM，root姿态为wxyz；
CAD_TO_UPRIGHT_REPORTING_ONLY只用于roll/pitch和轮心几何，不能进入actor输入。
friction/damping/armature/collider/solver差异仍未严格parity，不为制造通过而调参。

### 可选动态配对记录

新评估spec或显式request选择`diagnostic_profile="paired_state"`（Motion专用），接共享evaluator；
默认关闭，policy频率有界GPU缓冲、结束后统一保存，不逐physics子步写文件、不增加actor调用。
记录25D＋125D实测输入、raw action、实际command、pre/post root姿态/COM速度、左右轮body origins；
控制target/torque仍由同一control trace记录。具名轴/schema/episode ID和validity明确，terminal/reset
混合样本排除，terminal证据单独保留。wheel body origin不能直接冒称碰撞几何中心。
本轮只完成接口与CPU验证，尚未采集新的paired_state，运行仍需新授权／新声明／独立账本。

验证区历史导航：[sim2sim/README](sim2sim/README.md)。

## Motion 键盘 GUI 预览（当前入口）

当前播放入口 `tools.play --preview --keyboard`；兼容脚本
`scripts/play_motion_keyboard.py` 转调共享 src，不再固定加载旧 isolated validator。
默认无 --run 为 CPU 身份计划，无仿真/输出/账本写入；加 --run 打开 GUI，须明确授权。
键盘只改变输入命令，物理、PD、动作尺度和限矩仍由冻结 spec 配置。

```bash
"$PYTHON" scripts/play_motion_keyboard.py \
 --spec runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/spec.json \
 --checkpoint runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt \
 --physical-gpu 1 --speed 1 --max-speed 2 --max-wall-seconds 600
# CPU计划核验后，在GPU1可用的桌面终端加 --run 打开GUI
```

W/S按住前进/后退，松开平滑回零；上下箭头每次调整速度0.02m/s；
Space回零、R重置、Esc退出。窗口显示命令与实测vx，自动跟随机器人。
默认yaw关闭（max-yaw-speed=0）；A/D及左右箭头仅在显式开启yaw后有效，
B250没有yaw认证。默认线速度上限2m/s；手动播放不是逐环境完整验收。
兼容脚本仅暴露所选物理GPU，映射为cuda:0，不自动切GPU、不抢占任务。
Kit/Vulkan renderer显式选择同一物理GPU并关闭multi-GPU；CUDA逻辑0不等于
显示设备编号0。用户允许GPU0桌面播放时，命令改为--physical-gpu 0。
共享GUI设备解析器统一CUDA/renderer映射；未设置CUDA_VISIBLE_DEVICES时显式赋值，已有不同映射则拒绝。
兼容脚本只转发参数，所有默认值由共享tools.play维护；实际渲染尚未认证。
键盘预览严格核验USD/模块/YAML身份，不豁免历史SHA漂移。

## 准备声明

Motion姿态专用准备器（B250，单次有界姿态目标，不作为高速或Recovery入口）：

```bash
"$PYTHON" scripts/prepare_motion_posture.py --hapi-session "$HAPI_SESSION_ID"
# 默认零写；明确准备授权后加--write发布新UNAUTHORIZED spec/budget/manifest
```

它继承B250真实命令分布/控制/PPO，显式解析legacy requested/effective差异；
只增加bounded_geometry_v1姿态成本，自动保护0/±.5/±1/±1.5/±2旧能力。
发布不等于运行授权，授权登记及提交仍使用公共register_authorization/supervisor。
几何报告posture_diagnostics带轴/字段/valid/window，每个per_env并列姿态指标。
source与25/50完整窗口供候选选优；旧motion gate通过不等于姿态改善通过。

Motion PPO0 batch请求可显式`evaluation_mode="light"`（默认full）；seconds必须匹配spec.evaluation.light_seconds，姿态统计使用light_window_s，motion_window_s为空。仅工程诊断，capability_gate为NOT_RUN/accepted=false，不用于能力选优。通过公共supervisor --evaluation-only提交；Recovery请求拒绝此字段。

Motion比较优先使用通用`tools.compare_motion`：显式指定每个模型checkpoint/SHA及原始evaluation文件/SHA，
复用manifest/raw evidence loader；不依赖B250编号或日期目录，不查询progress。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.compare_motion \
 --request <比较请求.json>
# --output-dir <全新审计目录> 可选；不指定则仅stdout，无文件写入
```

请求形状：`{"models":[{"name":"source","checkpoint":"…","checkpoint_sha256":"…",
"evaluations":[{"path":"…/evaluation.json","sha256":"…"}]}]}`。
每份evaluation同目录须有身份匹配manifest；相同command必须评分身份一致、资产一致；
checkpoint独立绑定，不拼不同模型成功点。输出逐环境窗口完整度、终止原因、旧gate、
新窗口复算、配对差值、zero偏置/双向gain/asymmetry；缺失或早终止不输出认证用gain。
非零vx/yaw分别用保持窗口；zero用steady窗口的mean(abs(vx))，不以abs(mean)替代。

评分比较身份版本evaluation_components_v1分开scoring/schedule/storage。旧effective/scoring SHA保留，
不改写原评估；seed、scored_env、采样频率和窗口/阈值仍属于比较身份。
新评分窗口共享policy_post_step_closed_v1：post-step时间，闭区间；10–18秒/.01对应[999,1800)，
26–30秒对应[2599,3000)。旧float32摘要与新float64复算差异须另列，不能回填旧认证。
`scripts/audit_motion_response.py`仍保留为特定B250短链的历史审计，不推荐为通用入口。

提交交付摘要复用`tools.submission_summary`，只读既有授权receipt和一次握手，不访问PID/progress：

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.submission_summary \
 --spec <spec.json> --receipt <authorization_receipt.json> --handshake <握手.json>
```

输出source SHA、phase预算、跨实验额度引用、GPU声明、当前声明阶段、formal首更新是否已验证、负责人。
缺失握手spec绑定标MISSING_EVIDENCE；SOURCE_EVAL不等于formal运行，摘要不是当前存活证明。


## Recovery课程准备与预览

通用单块入口：`native_stand.command_v6.tools.prepare_recovery_course`。不依赖B25编号或固定预算；
输入父冻结spec、对应checkpoint及预期SHA、姿态库、[请求模板](docs/examples/recovery_course_request.json)。
默认CPU零写；`--write`只发布UNAUTHORIZED新声明，不提交、不授予GPU共享权限。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.prepare_recovery_course \
  --parent-spec <冻结父spec> --checkpoint <对应checkpoint> --checkpoint-sha256 <实际SHA> \
  --pose-library <已核验姿态库> --request docs/examples/recovery_course_request.json
```

请求分别声明current/retained family、各family质量、评估更新和phase预算。
可选`environment_counts`启用`fixed_environment_families_v1`：各family正整数槽位总数等于PPO环境数，family_weights必须等于counts/总数；仅训练reset固定归属，评估按指定family独立选择。未提供时保留随机family_weights_v1。
新声明编译为`recovery.sampling.version=family_weights_v1`，各family质量独立指定；
`recovery.assessment.families/retained_families`分别声明评估范围与旧能力保护组。
当前准备器是单块课程，覆盖当前＋全部保留组；采样权重不再受评分协议的R0/40%要求约束。
旧spec仍由集中只读适配层保留原R0/比例和阶段覆盖语义；新旧字段混用明确拒绝。
train/holdout必须各有有效姿态；旧组除sample_weight外所有记录须与父库相同。
新`rising_task`只含version、deadline、hold以及该版本的高度/entry阈值，不含sampling_version、retained_fraction或retained_families。
输出来源SHA、继承/删除/覆盖清单、严格actor/critic/Adam/RNG审核和std回读；不执行optimizer。
同时输出authorization_request_template：总更新、样本上限、phase墙钟及spec/ledger SHA；
其中approval/session/scope占位符需根据真实用户批准填入，再交现有register_authorization。模板不是授权。
发布spec/budget/manifest/poses后最后写publication_complete.json，标记绑定四份文件SHA。

`scripts/prepare_recovery_swing.py`保留原CLI，现为B25→40/40/20、10＋100预算的薄包装。
其他hold/coverage/rise/level2专用准备器用于历史配方复现；不删除，使用前查entrypoints分类。

GUI优先复用同一实验spec的现有CPU计划，输出USD、pose/family和checkpoint身份：

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.play \
  --spec <新实验spec> --checkpoint <checkpoint> --preview --strict-identities
```

不带--run无Isaac/GUI/写入；实际GUI须另有授权，按spec设备映射运行。
这是策略预览，不是独立静态姿态编辑器或能力证书。授权登记复用下方register_authorization；
提交和终态复盘复用supervisor、audit_terminal/compare_arms，不新增watcher。

## 计划、就绪与提交

授权登记显式请求JSON包含approval_id、user_scope、当前session、physical_gpu、gpu_uuid、
max_online_updates（所有臂smoke+formal合计）、max_phase_wall_s（所有臂声明phase墙钟之和），
arms列表每项为spec绝对路径/spec_sha256/budget_sha256。工具要求UNAUTHORIZED、空attempts、
零used、无submission/既有授权receipt，核验SHA和声明预算一致。工具无法替代用户真实批准。

```bash
"$PYTHON" -m native_stand.command_v6.tools.register_authorization --request "$APPROVAL_JSON"
# 明确批准并审核上述计划后才加--write；登记不等于提交，不复用旧额度
```

多臂prepare使用experiment_preparation.publish受限A/spec.json、A/budget.json等子目录，
publication_complete.json最后写入，绑定发布文件SHA。异常留下无标记目录时不可提交或手工补标记。
授权登记会合法改变spec/ledger，发布标记描述授权前原始声明；新身份由authorization_receipt记录。
登记使用账本锁、原子单文件替换和异常回滚；机器掉电后的跨文件恢复仍需人工核对receipt/ledger，
不能因receipt缺失就自动重复登记或提交。用户批准范围必须有真实依据，工具不验证自然语言授权真伪。

```bash
"$PYTHON" -m native_stand.command_v6.supervisor \
 --spec "$SPEC_PATH" --output-dir "$NEW_RUN"

"$PYTHON" -m native_stand.command_v6.supervisor \
 --spec "$SPEC_PATH" --output-dir "$NEW_RUN" \
 --physical-gpu "$PHYSICAL_GPU" --hapi-session "$HAPI_SESSION_ID" --check-submission
```

评估任务两条命令均加--evaluation-only。普通plan不查GPU；READY_METADATA仍submit_ready=false。
check-submission一次核对资源/current session/UUID/账本，未就绪exit2，不写run或reserve。
未授权准备返回AUTHORIZATION_MISSING是正确结果；准备器不会替你登记运行授权。

只有明确授权并完成预算登记后，提交时才用--launch（不与--check-submission同用）。
--formal-only仅复用同链已核验前置；--resource-mode shared需要明确--sharing-authorization。
--handshake-wait-s指定有限握手；--wait仅用于有界evaluation monitor，不能守候长训。
通知目标选择实际负责人，提交回执不等于formal首更新成功。

## CPU验证与离线审计

```bash
"$PYTHON" -m pytest -q --tb=short
"$PYTHON" -m native_stand.command_v6.tools.validate_frozen_cpu \
 --spec "$SPEC_PATH" --output-dir "$NEW_CPU_DIR" --test tests/test_submission_contract.py
"$PYTHON" -m native_stand.command_v6.tools.audit_terminal \
 --run "$PHASE_RUN" --ledger "$LEDGER_PATH"
"$PYTHON" -m native_stand.command_v6.tools.summarize_run \
 --run-dir "$PHASE_RUN" --ledger "$LEDGER_PATH"
"$PYTHON" -m native_stand.command_v6.tools.audit_entrypoints
```

CPU验证加--write生成验证副本，无runs/checkpoint/环境复制；schema/冻结plan/测试失败exit2。
加--checkpoint-initialization在CPU严格加载来源actor/critic/Adam，执行声明的std初始化，
报告逐参数差异、Adam不变和std换算；不执行optimizer.step、不导出模型，默认仍零写。
选择独立fixture测试，涉及旧项目数据的测试在原项目执行。验证副本零额度，不用于训练。
审计工具加--output-dir写新目录，已有路径拒绝；不重写run、不通知、不轮询。
计数分别列phase limit、reserved（缺失null）、actual completed、ledger charged、settled updates。
缺轨迹/控制字段记UNKNOWN，不补零；policy100Hz限矩读回不等于每5ms PD引擎审计。

离线重评分：

```bash
"$PYTHON" -m native_stand.command_v6.tools.correct_evidence \
 --run "$OLD_RUN" --output-dir "$NEW_AUDIT_DIR" --protocol-spec "$NEW_PROTOCOL_SPEC"
```

同轨迹新协议通过是重评分，不是新学会能力。完整raw由身份loader读取，压缩registry不能充当轨迹。

## Recovery完整冻结复验审查

`scripts/review_recovery_revalidation.py --run <completed_PPO0_batch> --output-dir <fresh_review>`一次读取terminal/manifest/raw，核对同checkpoint、三个seed×DrawBack/R0各8env，完整10秒与初态摘要。写新审计目录，不模拟、不通知、不改历史gate。比较实际初态hash，seed标签不能代替初态覆盖。

## 报告与通知

两臂都结束后一次比较：

```bash
"$PYTHON" -m native_stand.command_v6.tools.compare_arms \
 --run "$A_FORMAL_RUN" --run "$B_FORMAL_RUN" --output-dir "$NEW_COMPARISON_DIR"
```

比较要求共同source和evaluation协议；声明std倍率、初始化readback、checkpoint实际std分别呈现。
std是裁剪前随机动作量级，训练可继续改变；缺初始化readback保留null，不能用spec倍率补填。
takeoff专用审计用--update重复选择checkpoint；dt/hold/动作尺度来自冻结spec，trace布局有版本。

历史run要求只读时，用summarize_run/audit_terminal或直接读取JSON，不运行默认completion。
获得明确报告再生成授权后，才运行completion --run-dir（会写报告）。
仅在有明确通知授权、归属匹配且报告ready时使用：

```bash
"$PYTHON" -m native_stand.command_v6.tools.completion \
 --run-dir "$RUN_WITH_READY_REPORT" --notify-only --expected-session "$HAPI_SESSION_ID"
```

notify-only不重算报告，写锁/投递记录并可能发送；路由冲突拒绝，未知投递不自动重发。
--acknowledge-review写review标记，仅处理明确属于本任务的事件；终态事件不授权续训。

Recovery Swing失败离线复盘：`scripts/review_recovery_swing_failure.py --run <已完成链> --output-dir <新审计目录>`，读取source及25/50/100完整raw、metrics，输出逐环境失败事件与实际family×phase覆盖；无仿真、不改历史。

## Recovery采样覆盖与失败事件

sampling公共模式：`family_weights_v1`随机reset、`fixed_environment_families_v1`固定env任务归属。
固定模式须额外声明environment_counts；其总数必须与ppo.envs一致，权重必须等于counts/总数。
公共课程request可增加environment_counts，不改变评分协议；config/preflight也独立校验，绕过prepare无豁免。
effective与准备报告输出environment_to_family。部分reset保留归属，确定性评估只使用指定family。
新task_metrics分别报告声明槽位、累计初始化与rollout内有效transition覆盖；初始化计数可能含评估／
清理reset，标明确实范围。有效transition排除初始化和确定性评估，不能用名义权重冒充。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.review_recovery_events \
 --run <已结束chain目录>
# 可选 --update 25 --update 50；默认从registry选取所有已保存事件，不写死检查点
# 可选 --output-dir <全新审计目录>；否则仅stdout，零写入
```

输入必须有结束终态、冻结spec、registry、原始evaluation与metrics。身份核验复用raw loader；
缺控制/姿态trace标MISSING_EVIDENCE，不补零。区分NOT_ENTERED、EARLY_END_OR_PARTIAL_HOLD、
COMPLETE_HOLD_WINDOW；完整窗口不等于证书通过。分别输出初始化、恢复入口前、入口后保持时间，
训练mean episode duration另列，无法拆分的历史均值明确UNKNOWN。
`review_recovery_swing_failure.py`只转发共享模块。`review_recovery_takeoff.py`也是薄包装，
共享tools.review_recovery_takeoff保留几何/图表专项；缺完整保持时交付事件诊断，不硬报全窗通过。
所有通用事件读取版本化trace_schema；力矩仍是100Hz held读回，不是5ms子步证书。

## 冻结测试资源

`tools.test_resources.source_file`从实际导入native_stand定位源码，冻结副本无须项目根src。
`project_file`仅定位明确历史资源，独立副本返回None；调用方应skip该历史验证，不假造配置。
测试模块声明`FROZEN_TEST_SCOPE="PORTABLE"`（独立fixture）或`PROJECT_DATA`（项目历史数据）。
validate_frozen_cpu默认计划报告分类；--write执行仅允许PORTABLE，未分类也先拒绝并要求审核。
本次可冻结测试：test_recovery_fixed_slots.py、test_recovery_event_interfaces.py。
历史配置集成测试test_recovery_sampling_contract.py归PROJECT_DATA，继续在项目本体单独验证。

`scripts/prepare_recovery_swing_support_probe.py`：当前B25静态Swing分支支撑四候选＋原DrawBack/R0的PPO0声明，默认CPU零写，`--write`完整发布新spec/library/ledger/manifest及SHA标记；不授权/提交，不改变reward/control或宣称动态状态恢复。

`scripts/review_recovery_support_probe.py --run <已结束PPO0> --output-dir <新审计>`：一次读取终态raw，比较请求q与接管前最后初始化样本，分别报告初始化有效、构型漂移和完整能力；不启动仿真或续训。

Recovery真实输入诊断：PPO0新spec显式`input_capture={version:recovery_input_action_reward_v1,enabled:true,max_storage_bytes:268435456}`，仅三同源23秒64env/8scored请求支持；通过supervisor运行，保存新run/input_capture_00..02.npz及JSON身份。
`scripts/review_recovery_input_capture.py --run <已结束PPO0> --output-dir <新审计>`离线重算frame/history、checkpoint forward、150维按phase统计、Gaussian解析clip概率及runtime reward；不模拟/采样/optimizer。

`scripts/calibrate_recovery_control_priors.py --run <已结束真实input-capture run> --output-dir <新核算目录>`：CPU读取身份绑定NPZ，分别计算候选mean越界loss梯度和low-height clipped wheel-effort反事实reward，不执行optimizer或生成runtime授权。当前proposal_costs为未接线设计模块。

公共prepare_recovery_course请求可显式添加wheel_mean_auxiliary（swing_wheel_mean_excess_rollout_v1固定声明），只支持Swing/pre_entry channels2/5、lambda.001/margin.9、当前rollout固定batch/全部受控分母/public hook复用；与BC/std初始化干预冲突拒绝。该请求声明不授权运行。完整评估点10/25/50由unlock明确，source_eval不应用，smoke须证明eligible非零梯度。

`scripts/audit_recovery_mean_coefficient.py --capture-run <已完成150D采集run> --training-run <已完成aux formal> --output-dir <新审核目录>`：CPU各候选严格重载来源及Adam，单步反事实和lambda0控制，只写audit JSON，不导出模型/模拟/在线PPO；无真实PPO梯度向量，不冒称历史更新重放。

wheel_mean_auxiliary显式版本：v1=swing_wheel_mean_excess_rollout_v1固定lambda.001，v2=swing_wheel_mean_excess_rollout_v2固定lambda.03；其余mask/batch/分母/clip相同。未知版本或错配系数拒绝，通知按新spec显式授权启用。

## 存储门槛与来源证据复用

preflight和ledger.reserve均执行tools.storage_budget：核对实际输出分区可用量，保守估算checkpoint、
完整评估JSON、指定诊断捕获、单次原子写临时峰值，另留512MiB终态余量。不足时在reserve/Isaac前拒绝。
这是容量估算，不是配额锁；其他任务随后占用空间仍可能导致运行失败。不会自动删除文件。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.source_evidence \
 --spec <新spec.json> --source-run <已完成source_eval目录>
```

只读输出REUSABLE/MISSING/CONFLICTING；核验checkpoint、asset、有效配方、评分窗口、执行源码/PPO依赖、
evaluator身份及完整环境覆盖。完整但能力未达标与基础设施缺测分开；当前检查保守拒绝不完整来源窗口。
显式spec.source_evidence_reference才启用复用；preflight/reserve/chain/trainer重复核验，链跳过新来源采集，
引用旧来源作为baseline，不复制历史attempt、不修改旧ledger、不把旧墙钟写成本轮新耗时。
MISSING/CONFLICTING不自动补跑或换模型；先定位具体缺项，再准备明确的新评估请求。

registry/候选/analysis/链终态只保存递归摘要及evaluation路径/SHA，原始几何/姿态/control轨迹仍在raw文件。
本轮未删除或压缩旧产物；旧巨大文件不原地改写。新摘要不替代raw loader，选模仍按原规则。
普通长期诊断默认关闭、完整捕获仅指定update。压缩二进制归档和显式清理工具尚未实现，不宣称已完成。

`scripts/audit_recovery_support_geometry.py --run <已结束B25三组input-capture PPO0> --output-dir <新CPU目录>`：具名trace边界核验及原生hip→wheel geometry/potential/吸收端点折扣核算；不模拟/optimizer，不重写原reward。首transition缺pregeometry时明确省略。

`scripts/audit_recovery_geometry_target.py --run <已结束B25 input-capture> --output-dir <新审核目录>`：纯CPU比较负距离cost/双侧qualitybonus的真实反事实与抽象完整折扣场景，含once事件；不模拟/optimizer/导出模型，抽象场景不冒称物理可达。

`scripts/audit_recovery_support_record.py --run <已结束B25 input-capture> --output-dir <新CPU目录>`：平滑几何Q与episode纪录进展的实际反事实/驻留震荡失败边界审核，纯CPU无optimizer/physics；省略缺exactpregeometry的firsttransition，任务record非PBRS且不冒称actor已观测。

`scripts/review_recovery_support_record_wiring.py --run <已结束support_record PPO0目录> --output-dir <新CPU目录>`：只读terminal/NPZ及来源SHA，核验exactprecontrol USD FK基准、pre/post纪录、raw/weighted公式、初始化/失败/旧组0和episodecap；输出SHA绑定review.json，CPU无仿真/optimizer。

`scripts/prepare_recovery_support_record.py --parent-spec <B25冻结spec> --checkpoint <B25> --pose-library <合法三组库> --session <当前负责人>`：默认纯CPU零写；`--write`由公共course准备器核验并发布独立smoke10/formal25、beta=.3纪录奖励声明。授权登记与supervisor提交独立执行，脚本不授权/模拟。训练metrics记录support_record_progress及support_record_policy真实轮mean/std/sampleclip；smoke正进展事件缺失阻断formal。

## 发布完整性与历史存储审计

experiment_preparation.verify_publication统一检查单臂自身及父级多臂标记，授权登记和preflight复用。
授权后的spec/ledger通过绑定authorization_receipt识别允许的变化；不可变pose/manifest仍按原发布SHA核验。
旧无marker声明标LEGACY_NO_MARKER，不伪称完整发布。公共Recovery课程准备器接受notifications与
 evaluation_schedule显式request；return_package=True可取得唯一publication_package供CPU调用方使用，
其中含严格JSON payload、姿态bytes/SHA和input身份，不重复构建姿态。CLI仍返回可序列化摘要。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.audit_storage \
 --root <待审计历史目录> --exclude <活动或受保护目录> --exclude <另一受保护目录>
```

只读列出派生报告、大产物、冻结spec引用的来源依赖及REVIEW_COMPACTION_ONLY清单，不删除、不压缩、
不通过进程轮询猜活动目录；调用者明确给出排除范围。文件名／大小不能证明可安全删除，后续归档需单独批准。
存储估算消费公共storage_plan的summary/failure_tail/full_transition/paired_state，完成报告记录实际字节数
以便校准。估算仍非硬分区配额，其他进程写入可改变可用量。冻结CPU副本小，不作为优先清理目标。
Recovery reward_fields集中声明runtime/trainer/采集字段；support-record smoke需真实正进展以及baseline/reset
计数，failed/ineligible/episode-budget违规为零。此为接线证据，不是起身能力认证。

`scripts/audit_recovery_record_learnability.py --capture-run <完成的record wiring PPO0> --training-run <完成的record短训链> --output-dir <新CPU目录>`：身份绑定32类真实奖励事件、精确baseline FK、length/腿方向/body rotation三因素Shapley记账及clipped wheel别名；不模拟/采样/optimizer，数学贡献不是动力学因果或PPO梯度。

## 受限工程恢复与Motion补充诊断

已结束run收尾报告若受当前共享源码漂移阻塞，可用`tools.completion --run-dir <原run> --corrected-output <全新独立目录>`离线生成更正报告。旧run只读，不自动通知；不能与--notify/--notify-only合用。历史工程恢复报告只核验原证书、运行manifest、已归档字节及记录依赖，不授予新执行许可；未归档源码仅有manifest身份追溯，不能称完整快照。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.prepare_engineering_recovery \
 --failed-run <失败phase目录> --supplement <已完成PPO0目录> --spec <审核后的spec> \
 --ledger <原账本> --change-review <变更审核.json>
```

默认零写，逐项输出 READY/MISSING/CONFLICTING、身份、拒绝理由和累计预算；异常保留其他已核验信息。
新增版本 `motion_light_none_window_recovery_v1` 仅适用于“一次真实 smoke 更新后，milestone 轻评估姿态 None 窗口异常”。
证据分开绑定：优化接线、同 checkpoint 的完整轻补测、原来源完整能力、逐文件工程变更审核；
4秒 light 补测保持 capability NOT_RUN / accepted=false，不能代替新模型完整验收。
变更审核格式：`version:1,status:REVIEWED,reviewer,reason,target_changes,supplement_changes,decisions`；
两份 changes 为旧/新逐文件 SHA 差异，decisions 每项含 module、disposition、reason。
仅接受 engineering_only / unrelated_to_motion / fault_fix_verified / diagnostic_only；未知行为字段、
reward/控制/网络/PPO身份变化、过期审核、原证据改变均拒绝，占位审核不是批准。

加 `--output-dir configs/experiments/<新日期名> --write` 发布未授权 spec、zero-used/empty-attempts ledger、
工程证书、preparation_manifest 和最后写入的 publication_complete；同一失败证据只允许发布一次。
累计历史墙钟来自历史链、失败链完整 wall 和补测结算 ledger；新 source/smoke 额度为0，formal使用原剩余额度。
公共 supervisor 自动选择 formal-only，并与 preflight、reserve、trainer 复验同一证书；不增加提交入口。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec <新恢复声明/spec.json> --output-dir <全新run路径> --formal-only
```

不带 --launch 为零写 plan；未授权声明返回 READY_NEEDS_AUTH，不会 reserve 或启动。
运行授权仍需明确批准和公共 register_authorization；READY工程证书不授权运行，不改旧FAILED，不自动补smoke。
execution_identity保留全项目snapshot与task_subsystem_v2两层SHA；Motion显式排除Recovery专属子树/工具并记录理由和SHA，
共享Motion模块仍保守纳入逐文件审核。budget/storage/schedule与行为分别绑定；冻结执行副本另有实际模块校验。

通用prepare_checkpoint_diagnostic现支持Motion：显式--commands <JSON双轴命令列表>、--evaluation-mode full/light；
Recovery继续--family。两者冻结protocol、checkpoint及asset，默认CLI零写，--write只发布UNAUTHORIZED。
工程light建议summary或failure_tail，完整profile须显式选择；不能丢失姿态/轮心研究必须字段。
保存checkpoint后立即写actor_update_proof_<update>.json，不依赖随后评估是否成功；证明权重变化不证明能力提升。

batch continuation采用显式evaluation_group和on_group_failure=continue/stop；不再隐式按第三项决定继续。

`scripts/prepare_recovery_rollout_probe.py --parent-spec <当前纪录reward训练声明> --session <负责人>`：零写CPU计划；--write发布独立600秒PPO0随机rollout诊断，2×64×128、详细NPZ上限64MiB、保留固定分组/来源/纪录reward。授权后只经supervisor --evaluation-only提交。
`scripts/review_recovery_frozen_rollout.py --run <完成的frozen_rollout_probe> --output-dir <新CPU目录>`：身份绑定真实样本/物理clipped action/reward/value/GAE，核验global归一化并做固定轨迹bonus扣除反事实；不模拟/optimizer，不证明训练收敛。

`scripts/audit_recovery_phase_advantage.py --run <已完成冻结随机rollout> --output-dir <新CPU目录>`：按100Hz recoveryclock同相中心化比较bonus/收短与advantage、固定轨迹beta0/.3/1/3/10 GAE敏感性；非因果/训练重放。`prepare_recovery_support_record.py --formal-updates 100`显式准备100块（默认仍25），公共course独立发布，授权/submit仍分别执行。

`scripts/audit_recovery_action_distribution.py --run <完成的冻结随机rollout> --output-dir <新CPU目录>`：64point无RNG积分对比原硬裁剪、轮/六维sampletanh、meanclamp、wheelmean-tanh Gaussian；区分确定性迁移与状态内探索std、绑定来源SHA。不运行新policy，不授权分布变更或模拟。

`scripts/prepare_recovery_bounded_mean_probe.py --parent-spec <B25三组capture声明> --session <负责人>`：零写默认，--write发布显式action_distribution=recovery_wheel_bounded_mean_gaussian_v1的三组900秒PPO0迁移声明；保留同一参数/源std，行为改变须独立认证。`scripts/review_recovery_bounded_mean_probe.py --run <完成三组run> --output-dir <新CPU目录>`核验capture SHA、实际mean重放、std和原模型wheel-tanh关系、完整旧组gate。

`scripts/prepare_recovery_bounded_mean_train.py --parent-spec <B25冻结spec> --checkpoint <B25checkpoint> --pose-library <三组合法库> --session <当前负责人>`：默认零写，--write由公共course发布独立meanbounded smoke10/formal25声明；请求含action_distribution版本和beta.3，授权/提交另执行。smoke实际policy证据不足阻断formal，非起身能力证书。

`scripts/audit_recovery_leg_execution.py --run <已完成boundedmean短训链> --output-dir <新CPU目录>`：消费source/new10/new25完整状态/control/geometry同policy轴，独立统计腿rawaction、关节target限位、heldPD限矩及tilt/接触事件；只读SHA绑定摘要，CPU无physics/optimizer。

Recovery GUI preview创建1env，由公共execution mode在初始化和reset前选择preview_family/holdout；不使用训练64slot配额，不更改spec训练采样声明。异常在Kit fast shutdown前stderr立即打印。GUI故障复查可用`PYTHONUNBUFFERED=1 ... --preview --strict-identities --run 2>&1 | tee /tmp/recovery_gui_preview.log`保留终端证据。

## GUI公共模式、模型身份与数值轨迹

`native_stand.command_v6.tools.play`是Motion/Recovery共用的GUI入口；默认不带`--run`仅做CPU计划。
`--physical-gpu 0/1`对两任务均生效，省略时读spec.device.physical_index；已有CUDA_VISIBLE_DEVICES冲突拒绝。
CUDA逻辑设备固定cuda:0，Kit renderer显式对应物理GPU、multi_gpu=false；资源/UUID和真实渲染仍须运行时核验。
Recovery可加`--preview-family Swing`，从spec姿态库挑合法holdout，单环境模式禁用训练固定槽位。
CPU计划输出checkpoint/spec/资产/姿态库SHA、分布version/class/implementation SHA、strict actor load、保存的std及准确GUI命令。
同一参数checkpoint配不同分布是不同策略语义；计划不会将其称为行为等价，也不会授权GUI。

```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.play \
 --spec <冻结spec.json> --checkpoint <checkpoint.pt> --preview --strict-identities \
 --preview-family <Recovery family> --physical-gpu <0或1>
```

已有一次性复盘入口`tools.audit_terminal --run <已结束phase>`、`tools.review_recovery_events --run <已结束chain>`
共用evaluation_loader，输出完整窗口、family/failed_checks、接触事件及policy频率逐通道限矩，缺项UNKNOWN；不新增watcher。

新声明可显式设置`artifacts.evaluation_trace_encoding="evaluation_numeric_npz_v1"`：train及独立batch评估
把数值轨迹写压缩NPZ，JSON保存summary、字段/schema/shape/axes和sidecar SHA，JSON原子独占发布。
`evaluation_loader`按身份检查后还原数值数组供公共复盘读取；历史JSON保持原格式，不自动迁移、删除或覆盖。
使用`json.loads`直接读新证据的专用脚本只能读summary，应迁到公共loader后才用于完整轨迹分析。
表示缺失的None经NPZ保存/回读仍为None，不能补零；validity、时轴、单位继续使用原评估声明。

工具目录检查：`tools.audit_entrypoints`输出`documentation_coverage`，CPU回归强制CURRENT工具出现在TOOL_INDEX。
补齐旧公开薄包装：`scripts/prepare_recovery_wheel_std_ab.py`（轮std独立初始化准备），
`scripts/prepare_recovery_min_height.py`、`scripts/review_recovery_min_height.py`（minimum-height准备/复盘），
`scripts/audit_recovery_survival.py`（survival证据审计）、`scripts/review_recovery_coverage.py`（coverage复盘）。
这些工具不因注册而授权新运行，历史只读规则仍适用。

`scripts/audit_recovery_swing_geometry.py --spec <合法Swing/DrawBack姿态库spec> --output-dir <新CPU目录>`：现有新USD原生主动轴小幅扫描及被动闭链continuation，核验limits/closure/固定root理想planegap，输出SHA绑定摘要；不创建reset/仿真/训练，不认证动力学、自碰撞或完整恢复路径。

`scripts/audit_recovery_joint_signs.py --capture-run <三组实际inputcapture> --random-run <原B25 frozenrollout> --output-dir <新CPU目录>`：读USD轴/框架/具名activeindices，复算frame/target符号及preframe推得target−preq的局部方向覆盖；不把局部充分路径当必要条件或新模型采样证据，不改通道符号/physics。

`prepare_recovery_rollout_probe.py --checkpoint <候选> --parent-spec <该候选exact冻结spec>`严格匹配checkpoint内部spec/asset再新绑定source身份，启用可选fulljoint读回；`scripts/review_recovery_leg_rollout.py --run <完成的new25诊断> --output-dir <新CPU目录>`具名preq/target/局部方向/几何覆盖审核，排除postjoint done污染，不认证全局收腿可达或能力。

`scripts/audit_recovery_leg_exploration.py --run <完成最新new25全关节随机诊断> --output-dir <新CPU目录>`：解析独立Gaussian尾/局部实体目标盒覆盖、std倍数与腿mean/参考变化对旧state输出影响，稳定survivaltail；CPU无新采样/optimizer，不发布runtime配方。

`scripts/audit_recovery_leg_mixture.py --run <完成最新new25全关节随机诊断> --output-dir <新CPU目录>`：复用legcoverage，解析global双分量四腿joint概率/旧target单步偏移；纯CPUproposal无runtime class，必须公开likelihood与entropy/KL/学习责任问题。

`scripts/prepare_recovery_dynamic_geometry.py --spec <合法Swing库spec> --output-dir <新CPU目录>`：有限原生关节收腿/转腿continuation九路径，核closure/jointlimits/现有action envelope/固定root理想planegap，发布非runnable诊断草案；不生成runtime授权或隐藏控制，不将穿地固定root构型当合法reset。

`scripts/prepare_recovery_dynamic_timing.py --spec <合法Swing库spec> --output-dir <新CPU目录>`：六种quintic重叠实体target时序，100Hz命令点USD闭链/限位/envelope审核，1ms目标导数报告和具名测量契约；输出nonrunnable草案，不执行动作/仿真、不授予诊断预算。

`scripts/audit_recovery_leg_center_gradient.py --run <完成最新new25随机诊断> --output-dir <新CPU目录>`：重算两完整batch冻结ratio≈1 PPOactor+entropy梯度和早期腿中心候选auxnorm/夹角/clip，恢复RNG，不执行optimizer或导出模型；非历史minibatch重放，A/B草案非可提交spec。

`scripts/prepare_recovery_leg_center_ab.py --parent-spec <new25的exact冻结spec> --checkpoint <new25.pt> --pose-library <来源姿态库> --session <当前session>`：同源A/B准备，默认零写CPU计划，`--write`独占发布两个UNAUTHORIZED spec/ledger/poses及SHA标记；A关闭、B仅启用早期腿中心训练loss，不授权仿真或PPO。两臂均须独立冻结验证和真实smoke证书。

`scripts/review_recovery_leg_center_transfer.py --rollout <完成来源全输入冻结rollout> --a-run <完成A链> --b-run <完成B链> --output-dir <新CPU目录>`：固定真实150D输入五模型mean重放、源参数SHA绑定、同窗100Hz旧组首次失触前100ms对齐，独占发布；无仿真/optimizer/运行授权。preclock采用历史postclock−dt推断，局部符号是充分路径不是必要条件。

`scripts/audit_recovery_drawback_guidance.py --run <完成三组Recovery链> --output-dir <新CPU目录>`：从合法DrawBack初始化提取镜像轮心target，真实Swing反事实核算位置×实体镜像质量，独占发布SHA证据；候选仅CPU，非runtime spec，不授予仿真/PPO。

`scripts/prepare_recovery_drawback_guidance.py --parent-spec <来源new25精确冻结spec> --checkpoint <来源new25.pt> --pose-library <来源合法库> --session <当前会话>`：默认零写CPU计划；`--write`独占发布DrawBack镜像稠密reward独立UNAUTHORIZED声明，旧奖励保留、腿中心aux关闭，smoke10/formal25。准备不授权仿真/PPO。

`prepare_recovery_drawback_guidance.py --formal-updates 90`准备smoke10+formal90的总100在线更新候选（默认formal25）；formal10/25/50/90评估、墙钟7200秒，新名称/ledger，不覆盖旧25声明。准备不授权运行。

`scripts/audit_recovery_guidance_components.py --run <已结束DrawBack引导链> --output-dir <新CPU目录>`：同前300ms显式位置/镜像/product与局部斜率代理分解，SHA绑定，非PPO梯度或新采样。公共Recovery request可声明retention_regression_policy=recovery_retention_contact_diagnostic_v1，仅完整保持的接触单项失败改记录；不改gate，不授权PPO。

`scripts/prepare_recovery_contact_diagnostic.py --parent-spec <来源new25 exact spec> --checkpoint <来源new25> --pose-library <合法库> --session <负责人> --total-updates 500`：总500=smoke10/formal490，默认零写；--write发布UNAUTHORIZED新contact-only诊断声明，保留reward/gate/control，完整评估10/25/50/100/200/300/400/490。支持总100或500，准备不授权、不提交。

`scripts/audit_recovery_controlled_gradient.py --run <完成fullpreinput冻结rollout> --output-dir <新CPU目录>`复算score-only fullbatch梯度，无optimizer。`scripts/prepare_recovery_leg_initialization.py --run <同rollout> --checkpoint <exactsource> --parent-spec <自身冻结spec> --output-dir <新CPU目录>`一次性约束四腿output校准，失败不导出模型。`scripts/prepare_recovery_swing_actor_ab.py --parent-spec <谱系> --source <A> --candidate <合格B> --reward-recipe <冻结奖励spec> --pose-library <合法库> --session <owner>`默认零写，--write仅发布未授权A/B，须公共授权与supervisor提交。

`scripts/prepare_recovery_motion_handoff.py --output-dir <新CPU目录>`：B250及四Recovery strict身份、共22条件和组合协议CPU准备，当前runtime adapter未接完，输出runnable=false；不授权或执行PPO0。

`scripts/prepare_recovery_motion_handoff_scan.py --session <当前owner>`默认零写，`--write`独占发布22组接管PPO0 spec/poses/ledger/完整marker，未授权。公共`supervisor --evaluation-only --spec <spec> --output-dir <fresh run>`走handoff批量adapter；--launch/--wait须明确新运行授权，baseline8/8才继续，失败不重试。主vx.5/strict.02诊断，输出上限1GiB。


`scripts/review_recovery_motion_handoff.py --run <接管PPO0 run> --output <全新CPU目录>`：仅读原始22组证据，逐文件SHA/具名schema/首episode核验，重新评分并输出切换及1000interval保持指标；无Isaac/optimizer，不改旧run，输出目录存在则拒绝。


Recovery→Motion组合GUI：`tools.play --preview --strict-identities --handoff-condition 12 --physical-gpu 0 --spec configs/experiments/2026_10_10-16_44__recovery_motion_b250_handoff_ppo0/spec.json --checkpoint runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_50.pt --max-policy-steps 5000`默认CPU零写plan；用户桌面终端加`--run`播放Swing→Recovery B50受控.50s→Motion B250，独立history/实体scale，复用HandoffEnv。单环境反复episode，不能当22组评分或8/8认证；不创建训练ledger/run。


## 多策略第一阶段：接管窗口与接管候选准备

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_receiver_stage1.py --kind evaluation --session <真实owner>`默认CPU零写；--write独立发布16组v2窗口PPO0，64仿真/8评分、3seed对应显式world-yaw±.01rad初始化，128episode/1800s/512MiB。`--kind training`准备Motion B250初始化接管候选，冻结B50前缀、32/32、smoke20/formal100、983040 samples/7200s，未授权。两种都不提交或登记运行权限；完整publication marker/各文件SHA绑定。

本轮最终CPU计划（不启动、不查GPU）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_10-22_24__receiver_window_ppo0/spec.json \
 --output-dir runs/2026_10_10-22_24__receiver_window_ppo0 --evaluation-only

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_10-22_19__receiver_zero_from_b250/spec.json \
 --output-dir runs/2026_10_10-22_19__receiver_zero_from_b250
```

UNAUTHORIZED/NOT_READY是正确结果。获得真实新授权并经register_authorization登记后，用同一命令加`--physical-gpu 0 --hapi-session <真实owner> --resource-mode shared --sharing-authorization <真实共享授权> --check-submission`再次核验。提交时以`--launch`替换check；PPO0可以`--wait`等待有界自身诊断，训练detached只做一次握手不wait、不轮询。新授权来源/上限由登记JSON明确，不能引用旧余额。

`scripts/review_recovery_motion_handoff.py --run <完成run> --output <全新CPU目录>`除原SHA/score核验外，输出逐env初始化/Recovery准备/Motion入口前/保持窗口、首次非双轮接触与恢复接触子窗口、world位移/native vx积分/关节构型/角速度，具名schema v1；无新物理执行，不将合力接触当法向载荷认证。

## 新版学生CPU蒸馏与独立验证

`multiskill_student_v1`严格路由，legacy命令不变。下列CPU入口已真实执行；重跑须使用新输出路径，不能覆盖已交付dataset/checkpoint或把已消耗的BC预算当新额度。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/build_student_teachers.py --output <新的CPU数据目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/distill_student.py --dataset <数据目录>/RecoveryStudent.pt --output <新的学生目录> --role RecoveryStudent --steps 5000 --wall-s 1200
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_validation.py
```

准备器默认零写，显式`--write`才公共发布新名spec/poses/ledger/marker；不授权、不提交。当前最终声明`2026_10_11-00_55__student_independent_swing_ppo0`，早期00_40/00_48准备草稿保留未授权，不提交。

已验证零写公共plan：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-00_55__student_independent_swing_ppo0/spec.json --output-dir runs/2026_10_11-00_55__student_independent_swing_ppo0 --evaluation-only
```

收到该新诊断明确授权并用公共register_authorization登记后，提交命令（本轮未运行）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-00_55__student_independent_swing_ppo0/spec.json --output-dir runs/2026_10_11-00_55__student_independent_swing_ppo0 --evaluation-only --physical-gpu 0 --hapi-session "$HAPI_SESSION_ID" --resource-mode shared --sharing-authorization '<用户对此新诊断的GPU0共享授权>' --launch --wait
```

学生独立GUI的CPU计划（未启动GUI；需要单独GUI授权才追加`--run`）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.play --spec configs/experiments/2026_10_11-00_55__student_independent_swing_ppo0/spec.json --checkpoint isolated/recovery_student_bc_20261011/best_validation.pt --preview --physical-gpu 0
```

此预览只有学生控制，不接受handoff-condition/keyboard；当前接口仅声明固定Recovery或Motion零命令。真实验证matrix和预算/证据见STATUS与学生交付，不沿用旧receiver授权。

## MCU v2小学生（CPU蒸馏、导出、独立PPO0）

以下入口已CPU验证。本轮BC和物理预算独立；重跑须新授权及新输出，不覆盖历史数据。

~~~bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/build_student_teachers.py --interface-version multiskill_mcu_v2 --output <新数据目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/distill_student.py --dataset <数据目录>/RecoveryStudent.pt --output <新Recovery目录> --role RecoveryStudent --steps 5000 --wall-s 1200
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/distill_student.py --dataset <数据目录>/MotionZeroStudent.pt --output <新MotionZero目录> --role MotionZeroStudent --steps 5000 --wall-s 1200
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/export_mcu_student.py --checkpoint <学生目录>/best_validation.pt --dataset <数据目录>/<角色>.pt --output <新部署分析目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_validation.py --interface-version multiskill_mcu_v2 --recovery-checkpoint <Recovery绝对路径>/best_validation.pt --motion-checkpoint <MotionZero绝对路径>/best_validation.pt --dataset-manifest <数据绝对路径>/manifest.json
~~~

准备器默认零写，显式--write发布独立spec/pose/ledger/marker。授权仍由公共register_authorization登记。本轮已获授权、一次提交命令如下（不是再次运行许可）：

~~~bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-11_36__mcu_v2_student_independent_ppo0/spec.json --output-dir runs/2026_10_11-11_36__mcu_v2_student_independent_ppo0 --evaluation-only --physical-gpu 0 --hapi-session "$HAPI_SESSION_ID" --resource-mode shared --sharing-authorization '<本轮真实GPU0共享授权范围>' --launch --wait
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_validation.py --run runs/2026_10_11-11_36__mcu_v2_student_independent_ppo0 --output <新离线复盘目录>
~~~

v2在线训练在CPU层明确拒绝，不能通过去掉--evaluation-only将零reward环境用于PPO。ONNX只验证数值；ST工具/真板计时未验证。

## 同一31D Recovery学生任务PPO

普通v2 PPO0仍拒绝在线请求，必须有完整student_recovery_ppo_bc_v1显式声明。当前工具不新增BC或私有launcher。

~~~bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --parent-spec <显式父spec.json> --source-checkpoint <该配方冻结来源checkpoint.pt>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/replay_student_recovery_reward.py --output <新CPU重放目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/audit_student_recovery_fixed_inputs.py --output <新CPU诊断目录>
~~~

prepare默认零写；--write独立发布spec/poses/ledger/marker。通过register_authorization登记本轮source40/900s、smoke12/900s、formal100/5400s授权后，公共命令：

~~~bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-12_54__recovery_mcu_v2_task_ppo_from_bc/spec.json --output-dir runs/2026_10_11-12_54__recovery_mcu_v2_task_ppo_from_bc --physical-gpu 0 --hapi-session "$HAPI_SESSION_ID" --resource-mode shared --sharing-authorization '<本轮用户GPU0共享范围>' --check-submission
~~~

READY后以--launch替换--check-submission，并仅一次有界--handshake-wait-s；不--wait训练、不轮询log/PID/GPU、不自动重试。source行为失败允许继续，smoke工程证书通过才formal；由既有owner执行、评估、结算。


### 任务PPO首步工程故障修复（尚未重试）

12_54来源attempt已FAILED且消耗1，不能重用命令。13_11为共享修复后的独立UNAUTHORIZED声明，原来源/BC0/112更新预算不变；需新的明确物理重试授权。零写命令已实际验证：

~~~bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-13_11__recovery_mcu_v2_task_ppo_from_bc/spec.json --output-dir runs/2026_10_11-13_11__recovery_mcu_v2_task_ppo_from_bc
~~~

新批准后用公共register_authorization登记该spec/ledger精确SHA，再共享GPU0 --check-submission，READY后一次--launch --handshake-wait-s。没有批准不提交，不改旧FAILED或扣旧余额。


### 同一学生PPO共享父类修复后的零写入口（13_35）

13_11已FAILED，不能重用其提交。13_35独立声明未授权，零写命令已实际执行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc/spec.json --output-dir runs/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc
```

新物理重试批准后，使用公共register_authorization绑定新spec/budget SHA与当前session，再以显式GPU0共享--check-submission核验，READY后一次--launch --handshake-wait-s。未批准不提交、不复用旧attempt、不修改旧ledger。

## 学生工程提交准备包（CPU，无运行授权）

`prepare_student_recovery_ppo.py`必须显式输入parent spec和source checkpoint；按case_id而非数组下标选择
student_native/student_yaw10/student_yaw11/student_yaw12/teacher_combination_native。缺项、重复、来源SHA/接口冲突拒绝。
仅复现既有student_recovery_ppo_bc_v1配方，不支持借参数偷偷换reward/网络/优化器；其他来源需先建立新版本配方。
默认零写，`--write`事务发布UNAUTHORIZED spec、zero-used ledger、poses、准备差异清单和完整标记；
resources默认exclusive/no shared approval，不继承父运行授权。`--output-dir`可显式提供新日期名。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.tools.validate_frozen_cpu --spec <新未授权spec.json> \
 --output-dir <新CPU验证目录> --test tests/test_student_recovery_runtime_parent.py \
 --test tests/test_student_engineering_boundary.py --submission-package --write
```

公共validator生成source-only冻结副本，执行schema、实际supervisor零写plan及显式PORTABLE测试；
submission_preparation子目录含review-only spec/budget、execution identity、冻结验证、plan、授权模板及公共supervisor命令。
实际授权模板绑定原发布目录的spec/ledger SHA；包内副本仅供审阅，不能直接当作已授权声明。
不创建run、不reserve、不启动Isaac、不新增提交入口。先CPU PASS；新授权后再经register_authorization及supervisor资源检查。

再次验证相同声明/源码/测试/解释器可加`--reuse-validation <此前通过的验证目录> --write`：
核对全部输入SHA（含conftest），仅生成两文件引用收据，不重复复制源码；输入变化拒绝复用。
冻结仅复制要求的test文件＋conftest；测试需要其他fixture时须显式补入，不自动拿历史目录充当可移植测试。
复用收据不能再次构建完整提交包；原完整验证包仍为依据。

磁盘分类（只读，不读run/progress，不删除）：
```bash
PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.audit_storage \
 --root . --exclude runs --exclude <本次CPU产物目录> --categories-only
```

声明student_training.storage_max_bytes、student_evaluation.max_output_bytes及artifacts.terminal_reserve_bytes
统一供student runtime/preflight使用；checkpoint、selected rollout与故障NPZ以临时文件＋fsync＋原子rename保存。
主异常保留，保存/close异常仅附secondary，RNG在app.close前与finally均恢复。实际Kit退出仍需物理证据。

`scripts/watch_recovery_submission.py`为RETIRED，仅拒绝，import调用finish也拒绝，不发送通知/写报告。
`scripts/select_recovery_checkpoint.py`为HISTORICAL，只接受显式`--historical-replay`的legacy150D Recovery，
拒绝学生/receiver/handoff接口；要求run外全新`--output`，不回写历史run。新任务选模复用公共completion。
现有引用未消除前保留文件，不删除冻结副本。


### Recovery PPO100离线复盘与失败事件消融准备

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_recovery_task_ppo.py --run runs/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc --output <新的离线输出目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --parent-spec runs/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc/formal/source_snapshot/spec.json --source-checkpoint isolated/recovery_mcu_v2_bc_20261011/best_validation.pt --failure-event-zero
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc/spec.json --output-dir runs/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc
```

prepare默认零写，显式--write发布独立命名spec/poses/ledger及marker。本轮14_32已发布，不重复发布同路径。supervisor当前仅零写plan，缺新物理授权为正确结果。获该消融新明确授权后公共register_authorization绑定spec/budget SHA和session，再GPU0显式shared check-submission；READY后一次launch/有界握手，无自动重试或追加。


### 已授权学生声明的GUI预览

学生preview在CPU计划和--run均核验完整发布标记与授权receipt；授权后的spec SHA必须匹配receipt，不回退旧发布SHA，不修改历史声明。

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.play --spec configs/experiments/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc/spec.json --checkpoint isolated/recovery_mcu_v2_bc_20261011/best_validation.pt --preview --strict-identities --physical-gpu 0 --max-policy-steps 3000 --max-wall-seconds 300 --run
```

该命令CPU身份计划已通过；--run打开单环境学生独立GUI，不调用教师，不作能力认证。


学生GUI复用旧播放外观：`--ground-style grid --ground-extent-m 128 --ground-grid-spacing-m 1`为默认设置；可选solid/none只改视觉层，物理Plane不变。共享1800强度dome light、相机eye=(1.3,1.3,.85)/target=(0,0,.35)，每200policy步按机器人XY跟随。原学生命令无需变更；追加这些选项可显式固定地板样式。

动态课程候选的**无教师Swing学生GUI**（已验证CPU身份，用户桌面终端加--run执行；不是动态后缀认证）：
```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.play --spec configs/experiments/2026_10_12-13_29__recovery_course_b_prefix180_block0002/spec.json --checkpoint runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt --preview --strict-identities --physical-gpu 0 --preview-family swing_candidate_from_historical_r1 --ground-style grid --max-policy-steps 3000 --max-wall-seconds 300 --run
```
显式autonomous_preview单环境使用共享TrainingStudentEnv，不加载课程教师、不执行1.80秒前缀；全程学生31D/1.5rad。preview-family按独立student case筛选，不能被同source的normal case覆盖。旧训练/后缀评分默认仍CourseStudentEnv，活动冻结副本不改；学生尚无独立Swing accepted证据。


### Failure-zero动态复盘与lift-rate单变量候选

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_recovery_task_ppo.py --run runs/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc --output <新离线目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_recovery_dynamics.py --run runs/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc --dataset isolated/student_mcu_v2_teachers_20261011/RecoveryStudent.pt --output <新动态与历史probe目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --parent-spec runs/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc/formal/source_snapshot/spec.json --source-checkpoint isolated/recovery_mcu_v2_bc_20261011/best_validation.pt --lift-rate
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc/spec.json --output-dir runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc
```

prepare默认零写，--lift-rate与--failure-event-zero互斥；--write新命名完整发布。15_25已发布未授权，supervisor当前仅零写plan，不追加--launch。新批准后仍须公共授权登记、GPU0显式shared/current session/UUID/资源核验，READY后一次提交/有限握手。


### 学生new100支撑复盘与Motion局部教学探测（PPO0）

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_support_loss.py --run runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc --output <新的离线支撑输出目录>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_motion_probe.py --parent-spec runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc/formal/source_snapshot/spec.json --checkpoint runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc/formal/model_update_100.pt
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor --spec configs/experiments/2026_10_11-16_21__student100_motion_b250_local_probe_ppo0/spec.json --output-dir runs/2026_10_11-16_21__student100_motion_b250_local_probe_ppo0 --evaluation-only
```

prepare默认零写，--write发布新名完整spec/poses/ledger/marker；16_21已发布，UNAUTHORIZED。本轮仅零写plan，9组72episode/1800s/512MiB/PPO0需新授权。批准后公共register_authorization绑定该spec/budget SHA与session，提交时GPU0显式shared/current UUID/资源检查，READY后一次evaluation-only launch --wait等待本诊断自身完成，不重试不追加、不训练。


16_21局部探测的reset工程失败已修复；16_43新声明仍UNAUTHORIZED。零写复核：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_11-16_43__student100_motion_b250_local_probe_resetfix_ppo0/spec.json \
 --output-dir runs/2026_10_11-16_43__student100_motion_b250_local_probe_resetfix_ppo0 \
 --evaluation-only
```
明确新授权后，按冻结submission_preparation中的authorization_template登记；提交仍为该supervisor命令加`--physical-gpu 0 --resource-mode shared --sharing-authorization <本次明确共享授权> --hapi-session "$HAPI_SESSION_ID" --launch --wait`。先核验check-submission与身份/资源，失败不自动重试。本工具不重置16_21历史attempt或额度。


16_43局部接管PPO0已终态COMPLETED，不能重复提交同一声明。只读离线重评分（输出需全新目录）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
 scripts/review_student_validation.py \
 --run runs/2026_10_11-16_43__student100_motion_b250_local_probe_resetfix_ppo0 \
 --output isolated/<全新复盘目录>
```
该入口跳过非学生配对，适用于本次9组混合矩阵；不会执行模型救场或仿真。逐环境切换/缓存核算的本次准确复算入口见isolated/student_motion_probe_resetfix_execution_20261011/analyze.py（输出固定本次独立复盘analysis.json）。


同一个学生站立辅助课程准备（默认零写，--write独立发布；不直接启动）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
 scripts/prepare_student_recovery_ppo.py \
 --parent-spec runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc/source_snapshot/spec.json \
 --source-checkpoint isolated/recovery_mcu_v2_bc_20261011/best_validation.pt \
 --standing-rehearsal
```
17_12声明已按本轮授权登记，公开supervisor使用physical-gpu0/resource-mode shared显式授权后首次launch；同名预算不可重复提交。实际argv与一次握手分别保存在isolated/student_standing_rehearsal_execution_20261011/submission_command.json和submission.json，阶段事实由STATUS导航。准备器不继承历史余额或自动续训。


Recovery站立蒸馏工具（独立新目录；--reset-priority仅改变normal教学采样分层）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_recovery_standing_distillation.py --dataset-dir isolated/student_mcu_v2_teachers_20261011 --source isolated/recovery_mcu_v2_bc_20261011/best_validation.pt --output <新教师数据目录> --reset-priority
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/distill_student.py --dataset <新教师数据目录>/RecoveryStudent.pt --output <新学生目录> --role RecoveryStudent --source-checkpoint isolated/recovery_mcu_v2_bc_20261011/best_validation.pt --steps 5000 --wall-s 1200
```
使用原manifest episode划分；新BC步数单独记录，不能计作PPO更新。公共物理准备器增加--standing-check，4组新Recovery站姿/原Recovery站姿/B250基线/新Recovery原生Swing，非原80episode矩阵；必须指定interface-version、recovery-checkpoint、motion-checkpoint及dataset-manifest并另立授权。已执行20_14和20_19声明不可重复提交。

BC工具新增--device auto（CLI默认）：显式CUDA_VISIBLE_DEVICES=0，共享GPU0显存核验后对CPU/GPU0做短forward/backward测速并选择；可--device cpu或--device cuda:0。测速为独立副本梯度计算0optimizer，不冒称完整Adam吞吐；选择结果写training_result.device_selection。物理仿真仍按公共supervisor授权与GPU映射，不由BC auto绕过。


Recovery基本站立专项PPO准备（默认零写；--write独立发布，固定v5源、64normal，Swing回归）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --parent-spec runs/2026_10_11-17_12__recovery_mcu_v2_standing_rehearsal_from_bc/source_snapshot/spec.json --source-checkpoint isolated/recovery_standing_reset_distilled_20261011/best_validation.pt --standing-only
```
20_46已按当前用户明确PPO授权登记，提交仍公共supervisor --physical-gpu0 --resource-mode shared，实际一次握手isolated/recovery_standing_ppo_execution_20261011/submission.json；不得重复提交同名预算，正式训练GPU0而非BC设备测速路径。

20_46站立专项最佳实验候选update50 GUI（正常站姿起点，原网格地板/灯光；不能称10秒已通过）：
```bash
cd /home/kellen/wheel_leg_native_train
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.play \
 --spec configs/experiments/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/spec.json \
 --checkpoint runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/model_update_50.pt \
 --preview --strict-identities --physical-gpu 0 --preview-family motion_native_normal \
 --ground-style grid --max-policy-steps 3000 --max-wall-seconds 300 --run
```
已验证不含--run的CPU身份计划；学生play允许仅spec/asset/recipe/interface SHA绑定匹配的真实训练候选，不修改历史声明。环境自动重置，会反复显示站姿到倾倒；本次没有启动GUI。


镜像站姿教学数据（独立新目录；明确改normal物理目标，非teacher已验证动作）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_recovery_standing_distillation.py --dataset-dir isolated/student_mcu_v2_teachers_20261011 --source isolated/recovery_mcu_v2_bc_20261011/best_validation.pt --output <新镜像教学目录> --reset-priority --mirror-targets
```
随后distill_student.py --device auto按实际测速选择CPU/GPU0。Progress尚未接入runtime/model，不提供声称可运行的32D命令。镜像闭环22_28单次PPO0的声明身份与结果由STATUS导航，不能重跑已用额度。


从站立专项update50继续的Motion反馈＋弱镜像配方（默认零写）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --parent-spec runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/source_snapshot/spec.json --source-checkpoint runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/model_update_50.pt --motion-mirror
```
--write仅事务发布新的spec/ledger/poses；v6源和reward固定，不接受借字段改任意接口。22_43已按本次明确授权登记并首次public supervisor --physical-gpu0 --resource-mode shared --launch，单次握手证据isolated/recovery_motion_mirror_execution_20261011/submission.json。不可重复提交同名预算；actual-q对称误差是诊断，不替代10秒保持gate。

## 站立update200零速Huber专项（v7）

公共准备器默认零写，`--write`发布独立声明，不授予运行权限：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --parent-spec runs/2026_10_11-22_43__recovery_standing_motion_mirror_from50/formal/source_snapshot/spec.json --source-checkpoint runs/2026_10_11-22_43__recovery_standing_motion_mirror_from50/formal/model_update_200.pt --velocity-huber
```

00_12已通过公共supervisor共享GPU0首次提交；准确调用和一次启动握手保存于isolated/recovery_velocity_huber_execution_20261012。不要重复提交已预留attempt。

## Recovery持续课程公共准备与证据复算

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --continuous-course --task-directory isolated/recovery_continuous_course_20261012/task --authorization-scope "本次用户明确授权的Recovery持续课程范围"
```

默认零写；--write发布全新task及首块。已经存在的task不重复发布或提交。任务级授权与有限子run分开；公共supervisor使用--resource-mode shared/--sharing-authorization，不能沿用exclusive。当前首块身份与实际提交从STATUS进入。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_wheel_hold.py --evaluation runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/evaluation_16.json
```

可多次传--evaluation；默认stdout只读，--output只创建新文件，核验具名schema/trace SHA和时间轴，输出实际目标变化及requested/clipped/applied力矩、100Hz触限与v8成本重放。

## Recovery首B未启动dispatch人工恢复

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --continuous-course --recover-task-from isolated/recovery_continuous_course_20261012/task/task_manifest.json --task-directory isolated/recovery_course_source_binding_repair_20261012/recovered_task --authorization-scope "用户本次明确同意修复并恢复B级；只进行一次人工恢复提交"
```

默认零写，--write仅新文件发布。该recovered_task已发布/首次提交，禁止重复执行或借用其未消耗quota另跑任务。具体授权、资源检查和提交命令JSON位于isolated/recovery_course_source_binding_repair_20261012。

已结算v9动态故障块的**新授权、新失触配方**恢复（默认零写，不能作为自动重试工具）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/prepare_student_recovery_ppo.py --continuous-course --recover-failed-task-from <已停止task_manifest.json> --task-directory <全新isolated任务目录> --authorization-scope '<本次明确Recovery课程/GPU0共享授权>'
```
显式--write才发布新task/spec/ledger；已发布的新任务不能重复登记。真实提交命令记录在isolated/recovery_course_contact_restart_20261012/submission_command.json；由公共supervisor执行，不直接运行trainer。旧v9/旧零attempt恢复入口保持原语义。

入口后失触成本的原始轨迹离线重放（不模拟、不更新optimizer）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/review_student_contact_cost.py --evaluation <具名schema的evaluation.json> --output <新结果.json>
```
--evaluation可重复指定；核验trace SHA，记录控制者与首次入口，禁止输出覆盖原始证据。

第7节Actor时间平滑A/B公共准备（默认零写，--write只发布新声明）：
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.students.temporal_ab_io --task-directory <新isolated任务目录> --authorization-scope '<本次Recovery A/B/GPU0共享范围>'
```
本次最终声明/账本见isolated/recovery_temporal_ab_20261012/final_preparation.json；final_task已登记并首次提交A，不能重复执行。早期preparation.json仅未授权准备记录，不是运行入口。真实公共supervisor命令见同目录submission_command.json；owner在A完成后核验B并首次提交，worker不另建launcher/watcher或守候。

## 人工 Recovery 工作台

源码、逐字段设置、奖励单位、结果文件及两种续训方式见 [人工手册](manual_train/recovery/README.md)。推荐单步CLI；旧prepare.sh/train.sh仅兼容保留。每个步骤由人决定执行，不自动串联。

### 首次建立裸源码与人工修改

```bash
cd /home/kellen/wheel_leg_native_train/manual_train/recovery
# 只在editable不存在时执行一次；已有时直接编辑，不覆盖：
./manual.sh init-source --write
# 用你自己的IDE/编辑器打开这两个入口；下列为终端编辑示例：
nano settings.toml
nano editable/src/native_stand/students/manual_reward.py
```

其余环境、终止、PPO、网络文件在editable/src/native_stand/，手册的源码表给出准确位置。分步流程读取editable里的manual_reward.py；根reward.py只是旧一键入口的模板。

### 第一步：只冻结本次代码

```bash
./manual.sh freeze --write
```

输出一个实际draft路径。下面`DRAFT`的值必须手动替换为刚才输出；这一行是填写位置，不是预先存在的文件名。

```bash
DRAFT='在这里粘贴刚才输出的draft.json绝对路径'
MANUAL_FOLDER="$(dirname -- "$DRAFT")"
EXP="$MANUAL_FOLDER/experiment.json"
```

freeze不生成公共spec、不测试、不授权、不启动。改了代码必须新freeze，不能改冻结副本。

### 第二步：只发布声明

```bash
./manual.sh publish --draft "$DRAFT"
./manual.sh publish --draft "$DRAFT" --write
```

前一条只计划；后一条生成spec、poses、UNAUTHORIZED账本、experiment.json、session.env，不自动验证。

### 第三步：只做CPU冻结验证

```bash
./manual.sh validate --experiment "$EXP" --write
```

生成cpu_validation/validation_result.json，检查passed及tests_result。验证目录已存在时不覆盖；修改实现后回到新的freeze。纯CPU阶段不会预留GPU/attempt。

### 第四步：设置终端环境并查看公共零写plan

```bash
source "$MANUAL_FOLDER/session.env"
"$MANUAL_PYTHON" -m native_stand.command_v6.supervisor \
  --spec "$MANUAL_SPEC" --output-dir "$MANUAL_RUN" \
  --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 \
  --resource-mode shared --sharing-authorization "仅查看人工实验计划，尚未启动"
```

此时UNAUTHORIZED/NOT_READY属于预期，不能把CPU PASS当成GPU资源或授权通过。session.env提供绝对PYTHONPATH指向本实验源码，不引用正在编辑的工作区。

### 第五步：只登记人工授权

```bash
./manual.sh authorize --experiment "$EXP" \
  --approve "本人批准本人工Recovery块按声明更新数和墙钟使用GPU0共享"
./manual.sh authorize --experiment "$EXP" \
  --approve "本人批准本人工Recovery块按声明更新数和墙钟使用GPU0共享" --write
```

前一条验证授权合同但零写；后一条写公共receipt和本块所有权。不读取GPU资源、不自动launch。每个新块单独登记；旧授权不会自动复制。

### 第六步：只核验当前资源与提交条件

```bash
"$MANUAL_PYTHON" -m native_stand.command_v6.supervisor \
  --spec "$MANUAL_SPEC" --output-dir "$MANUAL_RUN" \
  --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 \
  --resource-mode shared --sharing-authorization "本人批准本人工实验GPU0共享" \
  --check-submission
```

要求submit_ready=true，核对GPU UUID与session.env的MANUAL_EXPECTED_GPU_UUID、逻辑cuda:0及来源SHA。当前公共Recovery要求至少4096MiB空闲。失败就停在这里，不抢占、不换卡、不循环等待。

### 第七步：由人单独启动

```bash
"$MANUAL_PYTHON" -m native_stand.command_v6.supervisor \
  --spec "$MANUAL_SPEC" --output-dir "$MANUAL_RUN" \
  --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 \
  --resource-mode shared --sharing-authorization "本人批准本人工实验GPU0共享" \
  --launch --handshake-wait-s 30
```

这一条才使用GPU。内部source/smoke/formal仍是原supervisor/owner监督的训练链，尚未拆成三个手动物理提交；不会自动开下一个实验。资源在reserve前再次检查。握手SOURCE_EVAL或SMOKE不等于formal首更新；UNKNOWN不得推断已训练。重复提交会拒绝。

### 第八步：人工查看结果、播放或停止

```bash
./manual.sh inspect --experiment "$EXP"
# 填写你实际选择的检查点，可为来源或本run的正式检查点：
CHECKPOINT='在这里粘贴实际checkpoint绝对路径'
"$MANUAL_PYTHON" -m native_stand.command_v6.tools.play \
  --spec "$MANUAL_SPEC" --checkpoint "$CHECKPOINT" \
  --preview --strict-identities --physical-gpu 0 \
  --preview-family swing_candidate_from_historical_r1 --ground-style grid \
  --max-policy-steps 3000 --max-wall-seconds 300 --run
# 从站姿播放时，将preview-family换成motion_native_normal。
# 只停止这个人工实验，STOP由原owner处理，不kill其他进程：
./stop.sh --experiment "$EXP" --confirm
```

play去掉`--run`只做CPU身份计划。固定模型副本的便捷播放仍可用`./play.sh --pose swing --run`与`./play.sh --pose standing --run`，保留网格、灯光、视角。候选选择读取candidate_selection.json，不默认用latest。人工可按需读取metrics.jsonl；Codex不轮询长训。

### 下一块：同配方完整resume

只支持本分步版本产生、已正常结算且证书有效的manual formal检查点；源码/奖励/超参/课程不变。它复用父实验bundle，不复制当前editable，不重复smoke/warmup。

```bash
# EXP仍指向已经完成的父实验；CHECKPOINT是你选择的正式检查点。
./manual.sh resume --experiment "$EXP" --checkpoint "$CHECKPOINT"
./manual.sh resume --experiment "$EXP" --checkpoint "$CHECKPOINT" --write
```

第二条只创建新draft，不提交。将新draft路径重新填入DRAFT，重新依次publish、validate、source新的session.env、authorize、check、launch。CPU及公共continuation验证Actor/Critic/Adam/RNG、源码SHA、原smoke证书、累计更新；新进程会真实reset，不声称恢复PhysX瞬间。

### 下一实验：改奖励或代码后从旧Actor继续学习

手动修改settings.toml的source_checkpoint及其自己的source_parent_spec，修改editable源码/奖励。随后重新freeze起步，生成新recipe实例、Critic/Adam/RNG和smoke。不要为了保留Adam而强行把改配方伪装成resume。旧一键工作台只支持这一Actor迁移方式，不能用旧run冒充新分步完整resume。

## Recovery 时间平滑终态离线复盘

只读A/B原始trace和各自冻结具名schema，不启动Isaac、PPO或optimizer；输出文件必须不存在，保留历史分析。

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONDONTWRITEBYTECODE=1 /home/kellen/anaconda3/envs/issaclab/bin/python \
  scripts/review_recovery_temporal_terminal.py \
  --output isolated/recovery_temporal_terminal_review_20261012/manual_repeat.json
```

已有最终机器结果为同目录final_review.json。报告区分完整与截断窗口、source/A50/A100/B50、normal/后缀/Swing、故障标量及全关节证据缺口，不用提前失败后的短窗口平均制造平滑改善。

## Recovery0.34m站立与对称持续专项

实际源v7正常专项update300；无限任务额度用null表达，每子块formal300/4h/2GiB，初块smoke12。独立Swing不参与晋级，不能把normal通过称完整Recovery。当前task/spec及提交证据从STATUS读取，不重复提交已存在任务。

```bash
cd /home/kellen/wheel_leg_native_train
# 只查看新任务声明；--write才发布，task目录必须是新的：
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  -m native_stand.students.standing_io \
  --task-directory isolated/新的任务目录/task \
  --authorization-scope "填写用户对本新任务的明确授权"
# 已有轨迹的0.34m高度/无封顶镜像reward离线重放：
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python \
  scripts/replay_standing034_reward.py \
  --output isolated/recovery_standing034_symmetry_20261012/manual_replay.json
```

真实首块由public register/course_io.authorize_block登记、supervisor --check-submission核身份/GPU0共享，再--launch --handshake-wait-s30。后续仅既有owner在正常终态结算后按taskscope授权新块并公共提交，完整恢复Actor/Critic/Adam/RNG，不重复smoke/warmup；故障停止且不重试。新模型GUI继续使用公共student play，输入高度由recipe.target_height_m=.34显式生产。

## 旧Motion0.34m站立与±2m/s持续任务（已停止，仅历史入口）

当前绑定v2执行副本，不使用共享src解释其后续执行。以下前两条只读，第三条实际提交；已有chain_submission的当前spec不得重复launch。任务状态与最新子块从STATUS进入，不用旧PID推断存活。

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/home/kellen/wheel_leg_native_train/manual_train/motion/standing034_engine_v2/src
export CUDA_VISIBLE_DEVICES=0
MOTION_SPEC=configs/experiments/2026_10_13-00_16__motion_standing034_pm2_block0000/spec.json
MOTION_RUN=runs/2026_10_13-00_16__motion_standing034_pm2_block0000
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
  --spec "$MOTION_SPEC" --output-dir "$MOTION_RUN" --hapi-session "$HAPI_SESSION_ID" \
  --physical-gpu 0 --resource-mode shared --sharing-authorization "用户批准GPU0共享训练旧Motion0.34m与±2m/s"
# 同一命令加 --check-submission 是一次只读身份/资源核验；新声明才可加：
# --launch --handshake-wait-s 30
```

新任务发布工具（会生成新task/spec，须新的目录，授权scope必须是真实用户指令）：

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.motion_course.io \
  --task-directory manual_train/motion/tasks/新的任务目录 \
  --authorization-scope "填写本次用户授权的确切目标和资源"
```

旧source保存原Actor/Critic/Adam/RNG/std。新版高度、协议身份和0/+2/-2评估矩阵显式发布；有限授权由register_authorization工具登记，不能靠编辑AUTHORIZED字符串代替。新bare源码路径及文件职责见manual_train/motion/README。

如需停止自己的两条当前任务，在各自任务目录创建STOP（owner/实际trainer消费，勿kill他人）：

```bash
touch manual_train/motion/tasks/standing034_pm2_fixed_20261013/STOP
touch isolated/recovery_standing034_smoke_fix_resume_20261013/task/STOP
```

## 当前Motion零命令站立与实际对称专项

v4修复副本＋独立task，状态看STATUS。以下为只读plan；本spec已经提交，禁止再次加--launch。height命令.34m，初始化继续原合法root.40m。

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=manual_train/motion/standing034_symmetry_engine_v4/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
  --spec configs/experiments/2026_10_13-09_07__motion_standing034_symmetry_block0000/spec.json \
  --output-dir runs/2026_10_13-09_07__motion_standing034_symmetry_block0000 \
  --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 --resource-mode shared \
  --sharing-authorization "用户同意GPU0共享训练零命令站立与双腿对称"
```

新任务准备仍使用该PYTHONPATH下`python -m native_stand.motion_course.io --task-directory <全新目录> --authorization-scope <真实授权>`，默认零写；--write显式发布，公共授权登记后才可提交。正在运行源码不要硬编码改写，另建版本。

仅停止自己的当前Motion专项：

```bash
touch manual_train/motion/tasks/standing034_symmetry_adamfix_20261013/STOP
```

源码/冻结回归与机器结果位于manual_train/motion/adamfix_verification；测试入口：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=manual_train/motion/standing034_symmetry_engine_v4/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short \
  -o pythonpath=manual_train/motion/standing034_symmetry_engine_v4/src \
  manual_train/motion/tests/test_standing_symmetry.py
```

## Motion关节与轮位对齐首块v5

当前spec只读plan如下；已提交后不得重复launch。task、终态从STATUS进入。零速高度命令.34，首块smoke25/formal300/4h/2GiB，结束复盘，不自动续块。

```bash
cd /home/kellen/wheel_leg_native_train
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=manual_train/motion/standing034_alignment_engine_v5/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_13-11_19__motion_standing034_alignment_block0000/spec.json \
 --output-dir runs/2026_10_13-11_19__motion_standing034_alignment_block0000 \
 --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 --resource-mode shared \
 --sharing-authorization "用户批准新Motion关节与轮位对齐首块GPU0共享"
```

新尚未提交声明才可追加--check-submission核验或--launch --handshake-wait-s30执行。当前停止入口：

```bash
touch manual_train/motion/tasks/standing034_alignment_final_20261013/STOP
```

版本化裸源码位于standing034_alignment_engine_v5/src，活动冻结副本勿改。CPU奖励设计/replay位于manual_train/motion/alignment_design_20261013，实际公共接线/冻结/plan/receipt位于alignment_execution_20261013。

## Motion25D无历史CPU蒸馏尝试

教师离线query＋boundedBC，无物理或PPO；必须新输出目录。当前脚本针对已有16个normal零命令episode，状态原.40、query命令.34，不能冒称.34成功轨迹或非零运动蒸馏。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=manual_train/motion/standing034_engine_v2/src \
/home/kellen/anaconda3/envs/issaclab/bin/python manual_train/motion/frame25_distillation/distill.py \
 --output isolated/全新frame25输出目录
```

当前actor.onnx在isolated/motion_frame25_zero_distilled_20261013；25D新接口不能用旧150D播放命令直接加载。

## Motion25D学生与150D教师运动PPO0

独立请求frame25_probe版本motion_frame25_teacher_comparison_v1，物理CommandEnv仍legacy原单位，学生显式motion_frame25_distilled_v1只读取当前policy25D。当前80episode评估已提交，禁止重复launch。以下仅CPU零写plan：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=manual_train/motion/frame25_evaluation_20261013/engine/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_13-12_04__motion_frame25_student_teacher_ppo0/spec.json \
 --output-dir runs/2026_10_13-12_04__motion_frame25_student_teacher_ppo0 \
 --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 --resource-mode shared \
 --sharing-authorization "用户同意测试无历史学生运动能力，GPU0共享一次PPO0" \
 --evaluation-only
```

新声明CPU/冻结/授权/资源核验通过后才加--launch --wait；允许前台有界等待自身evaluation完成，不轮询其他训练。当前输入捕获actor_capture_*.npz为actualpreframe25和actualmean6，后态/目标/firstepisodevalidity在配套evaluation与numeric traces。

Motion25D第一次12_04已FAILED，不重复提交。修复后12_15只读plan（UNAUTHORIZED，尚无物理attempt）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=manual_train/motion/frame25_evaluation_20261013/engine_writefix/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_13-12_15__motion_frame25_student_teacher_ppo0/spec.json \
 --output-dir runs/2026_10_13-12_15__motion_frame25_student_teacher_ppo0 \
 --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 --resource-mode shared \
 --sharing-authorization "用户批准修复后学生运动PPO0新attempt，GPU0共享" \
 --evaluation-only
```

明确用户授权后先register_authorization、--check-submission，再在同一命令加--launch --wait。scope80episode/1800s/512MiB，PPO0/optimizer0，故障不自动重试；未运行不能标accepted。

### 学生优先补测（未授权）

12_15已STOPPED_BOUNDED，不能重复launch。新12_47按student五组在前、只补teacher−1在后；其他teacher四组严格SHA只读历史对照。以下仅零写plan：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=manual_train/motion/frame25_evaluation_20261013/engine_student_priority/src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec configs/experiments/2026_10_13-12_47__motion_frame25_student_priority_ppo0/spec.json \
 --output-dir runs/2026_10_13-12_47__motion_frame25_student_priority_ppo0 \
 --hapi-session "$HAPI_SESSION_ID" --physical-gpu 0 --resource-mode shared \
 --sharing-authorization "新学生优先PPO0准备，运行需用户批准" --evaluation-only
```

新scope48episode/1800s/512MiB、PPO0/optimizer0。明确批准后register_authorization再check-submission；仅一次launch/wait。不从旧evaluate余额运行新attempt。

12_47学生优先评估已完成，禁止重复launch。逐项原始结果复盘：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/kellen/anaconda3/envs/issaclab/bin/python \
 manual_train/motion/frame25_evaluation_20261013/review_student_priority.py
PYTHONDONTWRITEBYTECODE=1 /home/kellen/anaconda3/envs/issaclab/bin/python \
 manual_train/motion/frame25_evaluation_20261013/review_zero_divergence.py
```

仅读取原始JSON/NPZ并写独立机器汇总，不更改旧run。真实.34教师教学来源索引actual034_teacher_sources.json，新BC/物理/PPO均尚未执行；新增运行另立spec/账本。

## 公开仓库便携CPU检查

`python scripts/test_portable_cpu.py --list`只列显式FROZEN_TEST_SCOPE=PORTABLE文件；
去掉--list执行这些CPU契约测试，不启动Isaac、GUI或训练。CPU依赖与外部资产边界见README/PUBLIC_RELEASE。
GitHub workflow使用相同入口；PROJECT_DATA和未分类历史测试不并入无资产CI，不放宽SHA断言。
