# Motion31来源复用与最小接线smoke

用户明确要求减少formal前重复评估。本轮仅实现新显式启动策略，当前10_26链的spec/ledger/证书/进程不改、不停止或重复提交；检查时smoke已经完成5个真实更新，仍在旧冻结的独立能力评估。旧流程会自行收尾进入formal，本修复不会追溯把旧未完成评估改为通过。

## 新路径

专用course准备器默认发布`motion_startup.version=motion31_minimal_startup_v1`与`motion31_wiring5_no_capability_eval_v2`：

1. 来源按checkpoint SHA、asset、scoring protocol、command/seed/family/yaw/duration及物理/IO契约匹配旧raw JSON。准备时核验trace SHA，运行前重验raw/spec SHA与trace引用。复用不是新仿真，不修改旧证据。
2. 仅缺失端点执行完整source评估，然后按声明命令顺序合并旧/新证据。来源能力未通过不阻止学习，但缺数据不冒充通过。
3. smoke仍5个真实PPO更新、4critic＋1actor；核验非零reward、所有命令保持段采样、Actor/Critic确实更新、固定std、pre-action mask、实际Actor命令/task读回、runtime控制/资产/地面读回、checkpoint保存读回。
4. 不执行smoke后全量独立能力评估，明确`NOT_RUN`。不授予能力accepted、不冒称训练完整episode/reset/timeout已覆盖；正式能力由formal固定里程碑评估。
5. formal仍按公共wiring_certificate消费者验证，仅由原run_phase生成证书；未绕过授权、账本或source prerequisites。

旧spec未声明该版本，继续旧short_wiring协议；本次不热切换在运行任务。新准备器默认零写，不创建第二条run/账本或占用新训练授权；明确`--write`才发布，提交仍只supervisor。

## 实测CPU证据

`artifacts/2026_10_15-11_15__motion31_minimal_startup_cpu/source_reuse_plan.json`核对真实三seed来源证据，当前七命令中5项可复用，只剩±1.5两项；smoke全量评估0项。旧来源五项各约172秒，能减少约14分钟；省去smoke七项约20分钟。该时间是基于历史耗时估算，不是新物理benchmark，不保证端到端恒定加速。

新增纯文件边界模块`students/motion_startup.py`，准备器/recipe validator/runner/certificate/storage增量接线；测试覆盖协议/模型/物理不匹配不复用、证据变更拒绝、顺序/缺失端点、真实smoke命令读回缺失拒绝、默认旧路径不变。全PORTABLE473pass8skip，最终定向18pass，零写真实准备plan通过。没有新仿真/PPO/Git提交，旧raw/spec/ledger均不改。

精确变更文件清单与身份见同名artifacts/change_manifest.json。本轮未宣称当前formal已开始，运行状态应在用户明确查询或终态通知时读取，不轮询守候。
