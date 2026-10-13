# Recovery→Motion接管诊断实现与首运行失败复盘 — 2026-10-10

本轮用户明确授权22组×8/176评分episode、3600秒含清理、1GiB、PPO/optimizer0，physical GPU0共享，不停止他人、不换卡、正常基线失败止后续、失败不自动重试。实施诊断后经公共supervisor --evaluation-only --launch --wait执行一次。

## 协议和评分修复

先复现了1220条时间戳全0仍可通过，以及保持1000条initial_valid=false仍可通过的旧score漏洞。新协议recovery_motion_zero_handoff_v2明确recovery_policy_trace_v1具名schema、dt=.01、真实连续policy时间（正首timestamp、差分严格10ms容差2e-6）、同episode、连续Motion控制、每条有效保持sample及完整1000interval。零/重复/跳步/缺窗/初始化/失效/拼接/提前失败拒绝。正常窗口结束事件与提前fault分开。

Motion后2秒内连续20条entry确认，下一1000sample保持：height≥.30、不限制.42上界，pitch/roll mean≤.10/peak≤.15、tilt≤.18、双轮传感器合力>2N每样本、净空>0、closure≤.005、policy any-channel saturation≤.05。主meanabs vx≤.5，vy≤.02/yaw≤.03；strict_vx_0p02_pass只诊断，不加漂移gate。在线clock/planner/offline共享handoff_protocol声明，旧Recovery11.5s deadline不结束Motion窗口。全程60°严重倾角、joint USD limits、closure/非finite/穿透等原物理保护保持。

## 正常初态、模型与接口

B250 SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e，自身formal/source_snapshot/spec和原model_factory Motion构造，非Recovery bounded分布。正常初态从B250冻结native_env.py::_reset_idx解析：root env_origin+[0,0,.4]、wxyz[√.5,0,0,√.5]，全关节q/dq0、root速度0，原生direct zero reset，不复用R0_holdout。新USD SHA32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7，PD60/2/1与1/5/10ms、40/5.5Nm不变；旧USD通过不迁入。

Recovery Binit SHA d074488410257e02b44704f8b2119612617cf44267c50d6e4561f72d39a9ab51、B25/B50/B100自己的raw evaluation/spec SHA核验。Binit是未训练校准源。reference当前全0且两模型坐标一致；root pose为link frame，root_lin_vel_w及root_ang_vel_w来自Isaac articulation对应测量属性，native vx=−bodyZ、vy=−bodyX/yaw=bodyY，不能当worldX速度或COM位置精确认证。

HandoffEnv是RecoveryEnv共享物理/PD子类：每interval只有选定策略输出按其scale解码一次，不混action/no blend/filter；Motion frame命令[0,0,.40]、Recovery[0,0,.36]，独立连续history，初始化期zero previous、后续由actual physical targets分别按.5/100和1.6/100编码，记录raw/input/loss。切换不reset/写速度/改姿态/资产/PD；Motion前缀只更新shadow history不调用actor。prefix完成10/25/50/100/200interval后下一interval切换。Motion首执行后clock .01，policy/init/controlled/motion clocks具名区分。

shared safety/dones生产pre-reset root全关节/state/control snapshot，失败不从reset后状态补样本；每env first episode mask维持分母8。原TASK保持评分在专用offlinescore，不同时启用Motion低高度/腿角任务失败。正常baseline8/8后才展开；矩阵先baseline/directSwing，再按时刻分组4候选。逐case JSON+压缩NPZ，真实100Hz双frame/history、q/dq/root/轮心/contacts/控制者/目标/请求限幅actualtorque和switchstate，数据不能冒充5ms/1ms完整冲量。

## 首运行事实与局限

16_28声明预先CPU48项、接口12项、冻结9 PORTABLE通过，public plan/check READY，独立evaluate1账本与exact attempt0dc4103daadf440d989ee3c452e255fc。通过supervisor一次有界evaluate等待，正常基线第一interval后结果序列化失败：numpy.int64的switch policy_index未转JSON primitive，TypeError。child terminal FAILED，monitor账本FAILED结算5.310061秒，PPO0/optimizer0，all simulated env-steps64/scored8。

基线状态INCOMPLETE，其他21项NOT_RUN，completed列表为空，评分episode实际完整结果0。没有evaluation JSON或raw NPZ完整落盘（旧atomic失败清掉临时文件），因此不能给出基线8/8或0/8、不能判断是否资产兼容/构型失败；也不能对接管状态收敛作结论。已留manifest/runtime readback/traceback/terminal/monitor_exit/ledger精确消耗，全部原始只读。

该故障发生结果写盘，不是PPO、模型训练或预算耗尽。正常组只有一个policy interval就结束，但缺已持久化动力学结果，不能从该现象猜测底层物理原因。B250模型状态在内存逐项核查后未变，未构建optimizer；不把缺raw的运行包装成完整冻结能力证明。

## CPU修复和准备

本轮记录接口遗漏已修：JSON边界递归转换numpy scalar/array为primitive，先严格finite序列化、atomic同名拒覆盖；新增真实switch np.int64/float32/bool roundtrip和非finite拒绝测试。异常路径尝试写INCOMPLETE压缩partial结果，不覆盖已完成证据；每case初始root/q/dq/reference先独立落盘以便后续基线失败溯源。旧16_28失败/证据/ledger不修改。

修复后针对性38测试通过；新16_34声明独占发布UNAUTHORIZED/evaluate1零attempt（相同矩阵/协议），冻结9 PORTABLE通过，public supervisor零写plan READY_NEEDS_AUTH/NOT_READY原因仅未授权。没有第二次仿真。原授权明确失败不自动重试，故需要新用户批准修复后重试，不自动耗原余额。

## 下一最小行动

先重新授权修复后同22组预算（PPO0/optimizer0、≤3600s/1GiB、GPU0共享），公共supervisor从真实Motion正常初态基线开始。若基线不能合法运行或不通过新主协议，保留原始完整失败，其他21组NOT_RUN，不让Recovery追逐未经验证的目标；基线通过才测直接Swing及20交接点。

本轮无法回答B250新USD基线、直接Swing、各接管点能力；这些标UNKNOWN/NOT_RUN，不能把此次工程错误当策略失败。没有新Recovery/Motion训练、reward修改、分类器或critic概率。

## 精确改动

新增src/native_stand/recovery/handoff_protocol.py、handoff_clock.py、handoff_runtime.py、handoff_requests.py、handoff_evaluator.py、scripts/prepare_recovery_motion_handoff_scan.py、tests/test_recovery_handoff_interfaces.py；修改recovery/motion_handoff.py、tests/test_recovery_motion_handoff.py、command_v6/config.py、tools/evaluate_checkpoint.py（可选Recovery诊断分支，Motion默认不变）。新增16_28声明/授权/运行证据及16_34未授权修复声明、artifacts冻结证据、isolated身份与失败复盘。文档更新STATUS/TOOL_INDEX/ARCHITECTURE/Recovery plan及本报告。旧run/checkpoint/raw/spec/ledger不覆盖，外部/安装目录不编辑，无commit/push。


## 后续事实纠正

重试发现本文正常初态“wxyz[√.5,0,0,√.5]转换posefilexyzw”实现有误：runtime原样转发该字段，必须直接保存冻结reset四槽[√.5,0,0,√.5]，不能按字段名重排。16_34正常初态因此首10ms倾角终止，不能判断策略能力。修复及证据见[重试复盘](RECOVERY_MOTION_HANDOFF_RETRY_REVIEW_20261010.md)。
