# 任务时长、诊断profile与checkpoint准备器

本轮增量工程，不改后台冻结评估、不启动仿真/PPO、不新增运行授权。
现场已有其他任务的23秒rising修复与复盘工具改动，本轮保留并复用。

Recovery batch时长统一从recovery.task_protocol.batch_seconds解析：合法rising
从任务返回23秒，holding从冻结protocol返回其时长，legacy请求默认10秒。
schema默认值、planner和runtime消费同一个已解析seconds，不再各自猜10/23。
rising的rise_protocol同样消费任务解析。错误时长仍拒绝，不改现有deadline。

## 保存profile

新batch请求可声明diagnostic_profile及required_diagnostic_fields。

| profile | 保存范围 |
| --- | --- |
| summary | 汇总和terminal，不保存transition数组 |
| failure_tail | 失败第一episode最后最多1秒state/posture/control/geometry；成功不保存完整时序 |
| full_transition | 第一episode全部有效policy样本state/posture/control/geometry及terminal |

计划输出diagnostic_storage：字段、scope、采样频率、required_fields和限制。
必需字段不被profile支持时CPU plan拒绝；runtime字段不可用同样拒绝。
请求未指定profile保持旧full_trace/diagnostics行为，不追溯重解释旧结果。
采样仍是policy-rate（本契约100Hz），PD力矩是最近一次held值，不宣称记录
每个5ms PD/1ms physics步。缺历史height/posture/geometry不能用新接口补造。
full_transition为显式诊断用途，有额外序列化开销，不能默认加到训练里程碑。

## 冻结checkpoint诊断准备

新入口tools.prepare_checkpoint_diagnostic，必需参数：parent-spec、checkpoint、
output-dir、family、protocol、hapi-session、physical-gpu、gpu-uuid。
可选diagnostic-profile、wall-s。CLI --help列精确用法。
它验证parent资源SHA、pose库/family、checkpoint输入结构和内部身份，protocol
必须与parent相同，不能借准备器换gate。日期时间命名、exclusive-create、
独立PPO0预算统一保存。spec仍使用原source恢复身份，待诊断模型写入显式request。

创建spec.json、budget.json和preparation_manifest.json：所有输入SHA、checkpoint
身份及保存profile绑定，evaluate最多一次，formal/smoke=0，book UNAUTHORIZED。
工具不授权、不启动、不发送通知、不自动切GPU；shared资源批准不能继承parent。
新spec需公共supervisor plan及独立授权后才运行。没有在项目configs创建真实实验，
仅CPU tmp fixture验证。准备中IO异常保留partial目录，禁止覆盖或无限重试。

目前支持Recovery，Motion准备未泛化。诊断timeline/scissor/transition脚本保留，
没有合并或删除；共享列解析可另做小范围工作，本轮不重构控制或PPO。

改动：domain/evaluation_requests.py、diagnostic_profiles.py；tools/recovery_batch.py、
evaluate_checkpoint.py、prepare_checkpoint_diagnostic.py、entrypoints.py；
recovery/task_protocol.py、rising.py、recipe.py；tests/test_diagnostic_profiles_duration.py；
AGENTS、README、STATUS、ARCHITECTURE、TOOL_INDEX及本文。

验证：全量CPU441 passed（17.89秒），133个Python文件AST通过，git diff --check
与新CLI --help通过。对已有update50 geometry spec做一次只读profile计划：23秒、
100Hz、state/posture/control/geometry字段完整声明；原budget已耗尽仍拒绝启动。
output未创建、输入spec/ledger SHA未变。prepare只在tmp CPU fixture发布未授权
配置，未创建项目新实验、未启动Isaac/PPO或发送通知。新profile的真实GPU保存
与事件前后时序尚未验证，不能宣称已经补齐update50历史缺失数据。
