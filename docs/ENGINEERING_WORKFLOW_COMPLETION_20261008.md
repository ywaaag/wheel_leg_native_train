# 公共工程流程补齐

范围：本项目共享下一次执行代码、CPU工具、离线新报告；本轮没有仿真/PPO、
通知发送、任务轮询、旧账本改写或活动冻结代码迁移。

## 五项落实与边界

|反馈项|本轮交付|使用边界|
|---|---|---|
|统一冻结CPU验证|tools.validate_frozen_cpu|默认零写；--write明确源码/测试验证副本，schema/冻结入口plan/指定CPU测试与逐文件SHA；不复制runs/checkpoint/Conda|
|通用终态事件审计|tools.audit_terminal|一次读取manifest/terminal/progress/ledger/raw，计数/身份/失触最长时间/逐通道物理clip比例；缺字段null|
|公共时间轴|domain.time_axis|半开index窗口、边界时间、post-step时间、恢复时钟和初始化UNKNOWN明确；rising/min-height评分及几何审计接入|
|统一保存计划|domain.diagnostic_profiles.storage_plan|source、额外source端点、milestone、final、独立CLI/batch共用；未声明profile保留legacy行为，显式冲突在CPU拒绝|
|Recovery legacy effective披露|recovery.effective.disclose|resolve/preflight/manifest统一记录所有Recovery/reward叶子；明确override/兼容用途/未核验consumer，而不是猜测已生效|

完整字段清单不是“全部字段已实际运行认证”。原P1声明205个叶子及兼容字段已列出；
未逐项证实的消费者写DECLARED_REQUIRES_CONSUMER_REVIEW，conditional reward激活依赖raw指标。
minimum-height新protocol覆盖旧窄height band；actor height command和FSM兼容存储仍保留。
配方、奖励、验收阈值和物理执行不变。

reserved/actual/settled使用domain.accounting唯一解析，audit_terminal和summarize_run共用。
phase limit不是attempt reservation；历史没有reserved_updates时保留null。
actual取terminal，缺terminal才取progress；ledger_charged单列，settled_updates仅终态结算后给值。
无法从用量推出实际完成时，不填造一致结果。

## 精确工具命令

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
PYTHON=/home/kellen/anaconda3/envs/issaclab/bin/python

# 默认只计划：不创建验证目录
"$PYTHON" -m native_stand.command_v6.tools.validate_frozen_cpu \
 --spec "$SPEC_PATH" --output-dir "$NEW_CPU_DIR" --test tests/test_submission_contract.py
# 明确授权CPU副本后加--write；结果失败exit2，保留验证报告

# 默认一次只读输出，不重写终态、不通知
"$PYTHON" -m native_stand.command_v6.tools.audit_terminal \
 --run "$PHASE_RUN" --ledger "$LEDGER_PATH"
# 需要保存离线审计时加--output-dir "$NEW_AUDIT_DIR"，拒绝已有目录

"$PYTHON" -m native_stand.command_v6.tools.summarize_run \
 --run-dir "$PHASE_RUN" --ledger "$LEDGER_PATH"

"$PYTHON" -m native_stand.command_v6.tools.audit_entrypoints
# 可加--output-dir "$NEW_REFERENCE_AUDIT_DIR"保存一次静态引用清单
```

Frozen CPU工具新建自身UNAUTHORIZED/零phase额度的验证账本，故plan出现缺授权/预算
是预期的拒绝运行，不是训练准备已经获许可。源码副本有manifest receipt和逐模块SHA，
只用于明确CPU测试，不执行AppLauncher、实际模型评估或optimizer。
要求选择CPU测试文件，涉及真实历史目录的测试应仍在原项目运行；副本专项测试使用独立fixture。

## 已实际验证

- 全量CPU528 passed in21.28s；后续配置冲突检查/审计字段标注另有针对性复验。
- artifacts/engineering_cpu_validation_20261008：实际冻结副本schema0、plan0/run_created=false、
  25项submission_contract CPU测试通过，逐模块输入SHA记录。对应快照是验证时源码，不替代之后共享代码。
- artifacts/terminal_event_audit_20261008：真实已结束P1 formal三评估项审计，actual100/ledger100/settled=true，
  原始ledger字节不变；新增审计代码字段明确定义不会改旧raw或旧报告。
- artifacts/recovery_effective_inventory_20261008/effective.json：205项完整声明清单，原spec字节不变。
- 公共时间轴/保存计划/三类计数/跳转边界均由独立CPU fixture覆盖。
- 最终接口补齐后针对性40 passed in1.31s；最终冻结副本
  artifacts/engineering_cpu_validation_final_20261008再次schema/plan/25项测试通过，passed=true。
  git diff --check与修改入口AST通过。

## 旧脚本审计

tools.audit_entrypoints现已扫描src/scripts/tests/docs引用和historical guard。
artifacts/entrypoint_reference_audit_20261008/audit.json记录18个历史/弃用/退役入口；
18个均有guard及引用。动态调用和冻结run复现也需保留，因此没有以静态扫描结果直接删除。
两submit/continue已经是拒绝运行的兼容壳，fixed runtime/watch已有禁用边界；
日期配方保持历史分类，新实验走公共prepare_motion_experiment/prepare_recovery_retry和supervisor。
这次完成引用审计与公开入口迁移，并不等于全部历史配方语义适合合并成一个生成器。
专用几何/剪刀/轮时序/transition脚本证据范围不同，保留它们的原入口与用途。

## 修改范围

新增domain/time_axis.py、domain/accounting.py、recovery/effective.py；
tools/validate_frozen_cpu.py、audit_terminal.py、audit_entrypoints.py；tests/test_engineering_workflows.py。
修改domain/diagnostic_profiles.py、recipe.py、config.py；train.py、tools/evaluate_checkpoint.py、
tools/summarize_run.py、tools/entrypoints.py；recovery/min_height.py、rising.py、recipe.py；
scripts/review_recovery_geometry.py及根文档/操作手册导航。未删除旧脚本。
legacy控制字段保留但披露，工程接线不被包装成新的训练或行为改善。
