# 工程精简第一批实施记录

本批仅收口提交/身份/报告链，不改变reward、PPO、物理或课程。用户指定不保留旧用法兼容；旧validate_frozen_cpu入口已删除，配置归档和历史证据读取仍保留。历史目录未迁移。

## 实际变化

- 公共stand_chain、train、两种A/B owner及monitor失败落盘改用共享src，保存配置/源码身份，无Python整树/扁平副本。source_identity记录相对模块SHA、Git/dirty、外部PPO及依赖；阶段引用父身份或记录差异。
- preflight返回进程内Approval；ledger锁内验证目标、关键输入SHA、预算原文件，保存submission_receipt_v1。runtime要求exact receipt并校验预算上限，拒绝旧无receipt的运行预约。模型/资产/原始前置证据及压缩轨迹sidecar保持严格校验。
- 当前源码变化作为运行事实记录，不宣称字节级复现；source evidence的代码/依赖差异记录告警，行为/协议/模型/资产冲突仍拒绝。未保存dirty源码时不能重建当时代码。
- completion优先读取已记录身份。丰富报告失败时落保守摘要：能力UNKNOWN、accepted=false、原因保留；不能覆盖更正目录，不能改变ledger结算。通知负责人、授权及at-most-once规则保持不变。
- validate_cpu直接在共享src执行PORTABLE tests、schema与零写plan；复制字节为0，重复输出拒绝，复用验证要求输入/测试/解释器严格一致。

## 本批修改文件

核心：command_v6/{train,stand_chain,launcher,supervisor,monitor,ledger,completion,motion_width_ab,retention_ab}.py。
工程工具：command_v6/tools/{source_identity,submission_receipt,execution_identity,preflight,source_evidence,motion_recovery_certificate,evaluate_checkpoint,validate_cpu,submission_preparation,entrypoints}.py；删除validate_frozen_cpu.py。
调用迁移：students/{requests,training,evaluator}.py、recovery/{probe,handoff_evaluator}.py。
测试：test_shared_execution_receipts新增；test_student_engineering_boundary、test_student_motion_probe、test_mcu_v2、test_episode_semantics_interface、test_engineering_workflows、test_recovery_event_interfaces、test_chain_interfaces、test_motion_cohort_width_ab、test_standing_balance_submission及command_v6/tests/test_preflight_ledger迁移新契约。
入口：AGENTS、TOOL_INDEX、WORKFLOW、ARCHITECTURE、STATUS、plan.md及本记录。以上路径以src/native_stand或tests为前缀。工作树已有其他并行变更，未reset、未把它们算成本批成果。

## CPU验证

解释器：/home/kellen/anaconda3/envs/issaclab/bin/python；PYTHONPATH=src。日志在artifacts/engineering_simplification_20261013。

- scripts/test_portable_cpu.py：第一次最终PORTABLE结果296 passed / 8 skipped（之后新增预算竞争回归）。
- pytest -q tests/test_chain_interfaces.py tests/test_motion_cohort_width_ab.py tests/test_standing_balance_submission.py src/native_stand/command_v6/tests/test_preflight_ledger.py tests/test_shared_execution_receipts.py：51 passed。
- 全项目pytest：历史Motion工程恢复fixture仍有22项setup错误，runtime/configure.py与历史审查身份冲突；未改fixture或放宽生产SHA。最终973 passed / 8 skipped / 22 setup errors，0 test failures；详见同目录project_regression_final.txt及result.json。
- 实际CLI validate_cpu --spec artifacts/engineering_simplification_20261013/cpu_fixture/spec.json --output-dir artifacts/engineering_simplification_20261013/cpu_validation_verified --test tests/test_shared_execution_receipts.py --test tests/test_student_engineering_boundary.py --write。实际CLI通过，专项22 passed；仅CPU声明，UNAUTHORIZED，plan未创建运行目录、未预约账本。

## 后续边界

本批不是全部plan完成：ModelAdapter、通用无墙钟上限预算、人工工作台局部可编辑引擎、checkpoint/轨迹存储策略留待独立批次。历史frozen reader与旧配置档案用于解释历史，不是旧CLI兼容。新链shared src不能保证运行中延迟导入的文件不变；应在运行期间避免编辑相关执行源码。

未验证：Isaac runtime、真实checkpoint恢复、物理行为、真实通知投递。本次没有任何optimizer update或新增训练。禁止依据本CPU结果宣布能力通过。


# 第二批：剩余工程项收口（2026-10-14）

本批从plan.md逐项核对执行；现行完成表位于plan.md顶部，不把未执行物理验证写成能力完成。

## 本批精确文件

新增：

- src/native_stand/command_v6/domain/execution_limits.py
- src/native_stand/command_v6/domain/checkpoint_policy.py
- src/native_stand/command_v6/domain/artifact_policy.py
- src/native_stand/command_v6/tools/model_adapter.py
- src/native_stand/command_v6/tools/artifact_io.py
- src/native_stand/command_v6/tools/checkpoint_lifecycle.py
- tests/test_engineering_simplification_remaining.py

修改：

- src/native_stand/command_v6/{config.py,completion.py,monitor.py,stand_chain.py,train.py,motion_width_ab.py}
- src/native_stand/command_v6/tools/{health_check.py,checkpoint_input.py,checkpoint_initialization.py,evaluate_checkpoint.py,play.py,prepare_checkpoint_diagnostic.py,engineering_recovery.py,execution_identity.py,register_authorization.py,storage_budget.py,submission_preparation.py,validate_cpu.py,entrypoints.py}
- src/native_stand/students/{artifacts.py,course_io.py,model.py,ppo.py,requests.py,training.py,training_recipe.py}
- src/native_stand/recovery/chain.py
- tests/{test_entrypoint_catalog.py,test_recovery_rising.py,test_student_course_source_binding.py,test_motion_cohort_width_ab.py}
- plan.md、STATUS.md、TOOL_INDEX.md、WORKFLOW.md、ARCHITECTURE.md及本记录。

删除（已迁移当前调用；历史文字只读保留）：

- scripts/submit_motion_high_speed_formal.py
- scripts/continue_motion_high_speed_submission.py
- src/native_stand/command_v6/tools/motion_batch.py

工作树中其余已有/并行改动保留，不归成本批成果。没有Git提交、历史删除或活动任务操作。

## 修复与简化的实际范围

1. ModelAdapter统一describe/validate/strict load。health不再硬取唯一参数名或无条件读取Critic/Adam；actor-only BC元数据可读取，是否能初始化仍按明确recipe/interface和真实模型加载判断。不会从25D/31D/49D宽度推断新接口。
2. ExecutionLimits将updates/samples/wall与reward版本分开。source/evaluate要求有限墙钟，正更新上限的smoke/formal可显式null；runtime、monitor、授权、plan共用解释。历史sample_limit可能只算formal或是较松上限，读取时明确披露；新的授权登记仍严格要求跨smoke+formal总样本一致。
3. 学生validate_instance将source SHA、milestones、capture、final seeds和storage作为显式实例字段，reward/PPO/std/初始化保持原版本约束。smoke保存/评估终点读取声明，不再写死update12。没有修改现有spec或给它们扩大额度。
4. 实际共享包是执行事实：identity记录declared/actual差异，course子进程固定使用已导入共享src，不再被父spec旧bundle的PYTHONPATH误导。历史frozen receipt reader继续用于解释旧记录，不用于新执行选择。
5. checkpoint与NPZ共用原子writer；保存失败保留原文件并清理temp。显式生命周期策略只允许当前RUNNING exact owner在ledger锁内删除自身未引用文件，保护source、update0、latest、milestone及所有registry/selection/阶段引用。未声明不清理，CLI始终只读；本轮仅在pytest临时目录检验删除，没有删除历史run。
6. artifacts可声明日志上限/备份数、输出字节上限及terminal余量；旧monitor拥有子进程并执行可选日志轮转，没有新launcher/watcher。students使用其实例存储上限；与artifacts重复声明冲突则拒绝，避免字段被静默忽略。
7. 压缩轨迹与摘要接口已存在，继续复用evaluation_numeric_npz_v1/evidence_summary，未重写历史JSON。CPU验证与审阅包不重复保存全源码SHA表，改存源码摘要/身份引用，并将依赖版本与外部PPO文件SHA纳入复用校验。
8. Motion A/B、独立评估/播放及Recovery阶段链补齐现有Approval传递；R0专用准备探针保留其专门前置检查，不误套“策略完整source评估”。correct_smoke_receipt迁至工程恢复实现。无新提交入口。

## 执行中的修正记录

- 第一轮统一sample校验把历史formal-only/较松sample上限误认成inclusive错误。已改为明确分类旧口径，新的授权入口仍强制inclusive；未改历史数据来迁就测试。
- 实际CPU审阅包两次暴露缺项：旧CPU声明没有device；package直接索引未声明sample_limit。前者现在在执行前明确拒绝，CPU fixture显式标为虚拟设备而非真实资源检查；后者从真实在线额度和rollout尺寸推导。失败目录保留，成功包为PREPARED_UNAUTHORIZED，未提交。
- 扩展结构校验曾先报输出通道错误，遮盖错模型身份；已调整checkpoint_input顺序，身份冲突优先，之后仍完整检查结构。

## 验证与完成边界

解释器固定/home/kellen/anaconda3/envs/issaclab/bin/python，PYTHONPATH=src。

- scripts/test_portable_cpu.py：317 passed / 8 skipped，最终日志artifacts/engineering_simplification_20261014/portable_delivery.txt。
- pytest -q --tb=short：993 passed / 8 skipped / 0 failed / 22 setup errors，最终日志同目录project_delivery.txt；22项历史Motion工程恢复fixture仍在setup拒绝未审核的runtime/configure.py变化，不放宽生产SHA或重写旧fixture。
- 实际validate_cpu --spec artifacts/engineering_simplification_20261014/cpu_declaration/spec.json --output-dir artifacts/engineering_simplification_20261014/CPU_delivered --test tests/test_engineering_simplification_remaining.py --test tests/test_shared_execution_receipts.py --submission-package --write。
- JSON结果位于同目录result.json；plan未创建运行目录、账本attempts保持空、未产生授权、真实GPU资源未检查。
- git diff --check已通过。

历史证据、旧日期复现脚本、手工工作台独立可编辑引擎不迁移或清理。手工引擎是用户编辑的实现，不等于公共链的每run源码归档；本批不修改其活动副本或把其特殊网络合入共享物理接口。

未执行Isaac、GUI、真实PPO/采样、物理能力评估、通知或自动续训。CPU fixture的有限optimizer测试不生成实验候选、不消耗运行账本。新保存/预算策略的真实无人值守运行仍待独立授权验证。本批是工程收口，不是运动学习机制已修复的证明。


# 第三批：复查尚未接通的规划（2026-10-14）

第二批完成表曾把“存在helper”和“实际接线完成”混在一起。本次按真实调用复查，以下漏洞已修：

1. 链报告仍把ledger-owned receipt中的requested/effective配置重复嵌入多个JSON。现在ledger_summary只保留计数、attempt状态及原ledger/receipt路径和SHA；候选详情也改为身份摘要+candidate_selection.json路径/SHA。完整选择文件仍保留逐环境证据，health_check核验引用；历史无引用格式继续按内容一致性检查。
2. checkpoint unlink后、inventory写回前崩溃，旧代码下一次会把自己删除的文件当成损坏。现在先持久化removal_pending，再删除再标removed；只在同一RUNNING exact owner及ledger锁内恢复。普通缺文件、SHA冲突、缺失但后来被引用的模型仍拒绝。CPU测试人为注入unlink后写回失败并核验恢复，无历史数据删除。
3. 规划要求指定update捕获optimizer初态，实际未接。新增optimizer_capture_v1显式phase/update白名单和总max_bytes；两个trainer在真实ppo.update前保存Actor/Critic/Adam、参数名、Python/NumPy/CPU/CUDA RNG、配置/源码身份SHA。默认关闭，无optimizer step，不导出训练候选；完整GAE/replay还需要另外声明完整rollout，初态不冒充完整批次证据。
4. prepare_student_validation还默选早期receiver模板、历史模型和教师。现改为parent spec、Recovery/Motion checkpoint、dataset manifest必填；teacher按父case身份匹配而非数组顺序，核验teacher/spec、dataset文件、pose和资产SHA。standing比较还须显式comparison checkpoint。旧用法不兼容；真实输入零写plan通过，无新实验目录。
5. submission_readiness原来把配置、许可与前置条件混成单个status。现在输出config_valid、authorized、prerequisites_ready、resource_ready，未核验资源是null，不默认通过；生产拒绝条件不变。
6. students/evaluate_cases的compact分支写尚未定义的candidate，已移除该无关赋值；训练warmup消费已声明字段，不再另写常量5。reward、PPO参数、物理及旧声明没有更改。

## 本批精确文件

新增：tools/optimizer_capture.py、tests/test_plan_final_gaps.py。
修改：domain/{artifact_policy.py,evidence_summary.py}；tools/{checkpoint_lifecycle.py,storage_budget.py,health_check.py,preflight.py,entrypoints.py}；command_v6/{completion.py,stand_chain.py,supervisor.py,train.py}；students/{requests.py,training.py}；scripts/prepare_student_validation.py。
上述domain/tools/command_v6均位于src/native_stand/command_v6，students位于src/native_stand/students。
文档：plan.md、TOOL_INDEX.md、WORKFLOW.md、ARCHITECTURE.md、STATUS.md及本记录。
未覆盖其他并行dirty changes。未commit、启动仿真/训练/通知、查询后台或改旧run。

## 实际核验

结果与精确命令在artifacts/engineering_simplification_20261014_followup/result.json及日志。

- 专项调用链：pytest tests/test_plan_final_gaps.py tests/test_completion.py tests/test_health_submission_followup.py。
- 可移植回归：scripts/test_portable_cpu.py。
- 全项目：pytest -q --tb=short；既有22项历史Motion工程恢复fixture的未批准runtime/configure.py SHA冲突保持拒绝。
- 实际validate_cpu CLI，spec为前批CPU-only UNAUTHORIZED声明，检查两个新PORTABLE测试，源码复制0、plan不创建run或预约账本。
- prepare_student_validation真实历史输入CPU plan已执行：父声明2026_10_11-11_36，两个mcu_v2 BC checkpoint和同一dataset manifest明确传入。只读plan，PPO0并未执行。两教师顺序来自父case身份；输出里resource_check=NOT_RUN。

## 仍未实施的原规划

- 历史大文件迁移/删除及全仓库准确可回收量：计划明确未授权存量清理；本次不执行。
- 手工日期prepare变体合并及独立25D/34D构造迁到共享接口：涉及冻结工作台和网络接口变化，本次保留，不把ModelAdapter元数据读取称为已迁移全部网络。
- 所有历史数据测试转成小fixture及完整外部调用审计：尚未完成；PORTABLE入口已独立，全量22项证书setup错误不是通过。
- 新保存/预算/捕获链的Isaac真实运行：未验证；CPU工程通过不等于能力提升或运行授权。

plan顶部已将这些剩余项改成明确“未实施”，不再笼统宣布规划全部完成。

第三批最终结果：专项报告/health调用链44 passed，PORTABLE345 passed / 8 skipped，全项目1021 passed / 8 skipped / 0 test failures / 22历史证书setup errors。实际CPU CLI的27项专项通过，plan未创建run，账本保持UNAUTHORIZED/空attempt。工具注册变更另经entry_contracts验证。
