# Motion 通用准备器与提交契约

本轮只做共享工程代码、CPU验证和未授权准备文件；未启动AppLauncher、
未采样/PPO、未改活动任务的冻结执行副本，也没有删除历史工具。

## 当前执行链

`prepare_motion_experiment → config/recipe/身份审计 → 新spec/零使用账本/差异报告`
`→ supervisor默认plan → supervisor --check-submission → 获新授权后supervisor提交`

准备器不是提交包装器。唯一公开提交入口仍为supervisor；已有monitor、
stand_chain、trainer、evaluator、ledger和completion继续负责执行与结算。

## Authorization/session

复用已在工作树的`domain.submission_contract.authorization`：
旧字符串与旧字典只兼容解析，返回统一字典，不改旧spec/SHA、不产生运行授权。
config、stand_chain与supervisor已有接线，本次复验；health_check也改为共用解析，
非法字段报告CONFIG_ERROR。新准备器统一生成status=UNAUTHORIZED及显式session。

默认plan分别展示配置preflight和submission_contract：
READY_METADATA仅元数据完整，resource_verified=false；`--check-submission`读取一次
资源后才可能READY。不就绪返回2，仍不预留账本/创建run/启动子进程。
实际launch复用同一提交判断；未授权、缺session、错误GPU/UUID、重复输出和旧receipt
在reserve前拒绝。当前session由CLI显式提供，提交时与环境当前session及spec绑定核对。
该接口不代表未来阶段能力通过或资源永久可用。

## 准备器输入与边界

入口：`python -m native_stand.command_v6.tools.prepare_motion_experiment`。

- 显式parent spec、checkpoint及预期完整SHA、request JSON、输出目录、session、GPU index/UUID。
- 可选audit与预期SHA；仅身份引用，不能自动导入通过证书、历史attempt或旧额度。
- parent必须是已有明确effective_recipe_version=1的Motion配方，legacy迁移另行做行为等价审查。
- 默认零写plan；`--write`只发布本项目configs/experiments下的全新日期时间目录。
- 输出spec.json、budget.json、preparation_manifest.json；预算一律UNAUTHORIZED、used=0、attempts为空。
- 同时记录parent/request/model/asset/module/YAML SHA、实际源码/依赖/PPO身份、
  requested/effective、完整字段差异与允许修改范围。
- 用共享learning.model在CPU严格加载actor/critic，核对parameter_names与Adam参数顺序、
  moment shape/有限值/二阶矩及step，记录RNG字段。没有构造或运行optimizer更新。
- 写入前复验输入SHA；重复目录拒绝；发布失败仅清理本工具新建文件，不复用半成品。

当前支持两种明确请求，而非任意patch引擎：

|mode|明确行为|
|---|---|
|evaluation|冻结模型PPO0请求集合；继承评估时长、协议与window，可显式评估seed和墙钟|
|course|单阶段0.5增量课程；零/对称旧端点/当前一对端点，显式weights、总在线上限、smoke额度、完整评估频率及各phase墙钟|

course只准备当前阶段，max_enabled_stage=1；不生成更高可采样命令。
yaw准备要求retained包含直线±4，当前端点上限±4；保留命令权重必须为正。
训练reward/PPO/动作/PD/物理/termination和现有gate保持父配方；cohort宽度保留父语义，
只将有效阶段denominator映射到新单阶段ID。请求中的reward、LR、std、gate等字段明确拒绝。
预算按inclusive total=smoke+formal，例如100=1+99；不把两个阶段都配置为100。
准备器不把声明的retained任务当作已验收，后续source前置回归仍由共享链核验。

## 精确用法

设置实际PARENT_SPEC、CHECKPOINT、CHECKPOINT_SHA、CONFIG_DIR及本次session/GPU。
CONFIG_DIR名称用`domain.experiment_naming.new_experiment_name`生成。
以下只有CPU准备，不会启动：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
 -m native_stand.command_v6.tools.prepare_motion_experiment \
 --parent-spec "$PARENT_SPEC" --checkpoint "$CHECKPOINT" \
 --checkpoint-sha256 "$CHECKPOINT_SHA" \
 --request docs/examples/motion_course_request.json --output-dir "$CONFIG_DIR" \
 --hapi-session "$HAPI_SESSION_ID" --physical-gpu 1 --gpu-uuid "$GPU_UUID"
```

默认返回files_written=0；确认声明内容后同一命令加`--write`生成未授权文件。
PPO0示例请求为`docs/examples/motion_evaluation_request.json`。
然后用现有supervisor检查，示例没有--launch：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
 --spec "$CONFIG_DIR/spec.json" --output-dir "$NEW_RUN" \
 --physical-gpu 1 --hapi-session "$HAPI_SESSION_ID"
```

evaluation任务另加`--evaluation-only`。未授权准备文件返回AUTHORIZATION_MISSING是
正确结果，CPU有效不授予运行额度；后续授权应登记独立累计预算，再检查提交就绪。

## CPU与实际入口验证

新测试`tests/test_motion_preparer.py`使用独立小型150D网络/Adam/资产fixture，
覆盖真实CLI零写/无Isaac、错误SHA、资产漂移、参数名映射、未知字段、权重、
跳档、单方向rehearsal、完整恢复字段、引用audit不授权、重复路径、发布故障清理。
现有submission_contract回归覆盖训练/评估入口、缺/旧session、GPU、UUID、
预算拒绝、输出冲突、只读检查与launch互斥。测试不启动子进程训练或物理评估。

实际B250 CPU准备与supervisor plan证据：

- `configs/experiments/2026_10_7-20_56__motion_preparer_cpu_evaluation/`
- `configs/experiments/2026_10_7-20_56__motion_preparer_cpu_course/`

两者均UNAUTHORIZED、零用量、空attempts；对应run目录不存在。
parent/checkpoint/旧ledger未写入；source B250严格网络/Adam审核通过。
prepare默认零写、supervisor返回READY_NEEDS_AUTH/AUTHORIZATION_MISSING，ledger字节不变。

## 新增反馈的处理范围

本轮已落实：公共来源/SHA/允许差异/新目录/预算流程，以及独立fixture测试。
轨迹时间对齐、reward与gate分层、diagnostic_profile收敛沿用各自已有模块，
未为准备器另写转换、评分或轨迹保存系统。后续可先提取时间索引公共函数，
再逐条验证profile覆盖；这些改变应独立做工程回归。
Recovery standing文档的历史“当前”段落整理可作为文档任务处理，本轮不迁移
Recovery流程或重写活动配方。

现存限制：单阶段停止仍通过父配方兼容cohort_width_ab标志接线；
实验标签与控制语义的彻底分离未在本轮实施。准备器明确记录该差异，
不会把它宣称为新算法或完整后台课程生成器。
跨实验预算集中预留及通用物理比较报告仍是后续工作，本轮不自动导入旧余额。

旧脚本保留historical guard；通用替代经后续使用验证后，再缩成薄包装或归档。

## 本轮文件

新增tools/experiment_preparation.py、tools/prepare_motion_experiment.py、
tests/test_motion_preparer.py、两个docs/examples请求文件及本报告。
修改tools/health_check.py共用授权解析、tools/entrypoints.py登记入口及根导航文档。
既有submission_contract/config/stand_chain/supervisor/test_submission_contract是
此前工作树已有修复，本轮复用复验，并未另造第二套实现。

## 最终验证记录

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

最终491 passed in20.74s。新增Python AST、请求JSON解析及git diff --check通过。
实际B250两模式的最终CLI零写计划通过，CPU恢复审核17个Adam参数状态。
最终计划记录为两个准备目录的final_cpu_plan_receipt.json；准备声明未获授权，
spec/budget字节保持不变。新准备manifest的发布计数字段在本轮校正为3，
仅声明元数据校正，未改任何历史run或冻结证据。
没有真实--check-submission资源采样、launch、物理复核、在线PPO或离线optimizer更新；
提交资源分支使用CPU fixture验证，实际可用性留到获授权的新提交检查。
