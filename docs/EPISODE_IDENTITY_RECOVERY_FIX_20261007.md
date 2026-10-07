# 冻结身份、episode证据与受限工程恢复

本轮只修改当前共享源码、CPU测试和文档。现有dirty changes保留，旧run、
checkpoint、evaluation、ledger及运行快照只读；无仿真、PPO、续训、预算预约。
不修改11.5秒起身期限、reward、控制或正在训练的配方。

## 已实现

1. execution_identity同时记录declared_source_root与actual_execution_root，
   保留旧source_root字段。relative_modules_sha256及排序后的整体SHA不依赖
   复制目录位置；合法冻结副本仍要求原spec SHA、receipt和逐文件SHA完全匹配。
   CPU子进程实际从完整source_snapshot加载preflight，证明路径迁移可通过
   身份检查且没有加载Isaac；旧预算是否通过与源码身份是两类结果。

2. domain.episode_summary统一version=1及completed计数，保留completed_episodes
   alias。producer和证书reader共用schema，兼容两旧字段但冲突必须拒绝。
   非有限/负时长、未知版本、计数缺失不作为真实零。没有重写旧metrics。

3. Recovery新增每pose设备汇总：family/pose、完成、success、task failure、
   timeout、fault、初始化有效数量、平均/最大时长。step期间无CPU读取。
   offline_geometry_valid、runtime_initial_valid与policy certificate分开；
   训练窗口的success计数不成为独立能力证明。

4. wiring_smoke可显式声明required_groups，要求新低位family和旧R0路径分别
   被观察，必要时指定pose及初始化有效。旧spec没有声明时不追溯收紧。
   新prepare_recovery_rise生成rising task_kind与R1/R0各自事件要求；本轮没有
   执行它。正时长要求目前支持一个事件，更多逐事件时长尚未保存，直接拒绝
   多事件时长资格声明，避免最大时长被扩展到全部episode。

5. recovery.task_protocol给holding与rising独立身份、窗口对齐和成功语义；
   显式task_kind与已有声明冲突则拒绝。legacy adapter保留当前reward、FSM和
   窗口语义，未删除standing_task共享posture/BC字段；不是重构环境或PPO。

6. 报告只在Markdown展示层压缩trace及大数组，并链接phase报告/raw目录；
   原analysis、candidate JSON与raw轨迹不删减，旧report_ready报告不重新生成。
   source/latest/best_new/best_overall及累计额度继续使用原公共选优和账本接口。

7. Recovery旧chain/train_stages/extend_training CLI增加历史确认guard，保留
   内部函数与复现用途，不删除文件或关闭任何活动任务的冻结实现。

## 受限工程恢复工具

唯一支持原因：旧证书的错误列表严格等于
`smoke did not observe the required completed_episode`，producer使用completed
且新共享reader复核PASSED。不能用它恢复runtime错误、能力失败或不匹配配方。

默认只读计划：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
-m native_stand.command_v6.tools.engineering_recovery \
--spec <原spec> --smoke-dir <原smoke目录> \
--output-dir <新YYYY_M_D-HH_MM__purpose配置目录>
```

工具核验原失败证书输入SHA、spec/snapshot/manifest/终态、source checkpoint、
asset、exact source+smoke IDs、更新量与used计数；所有attempt必须已结算，
不得存在formal使用或其他阶段。输入不匹配、旧证书有其他错误、重复目录拒绝。
输出plan_sha256，simulation/PPO/files_written均0。

核对计划后，同命令附`--execute --expected-plan-sha <前次SHA>`，仅创建四个
新文件：spec.json、budget.json、corrected_smoke_certificate.json、
engineering_recovery_plan.json；另在configs/experiments下新建publication receipt，
按原exact IDs排他认领，换目标名称也不能重复发布。CLI限定本项目
configs/experiments直接子目录；plan检查receipt存在但不创建它。
original budget及attempt不改写；保留原limits、
used及IDs，导入source/smoke证据SHA。新book始终UNAUTHORIZED，不增加额度，
不自动提交formal-only。运行权限必须另有明确授权并通过公共supervisor。

发布不是完整事务数据库：途中IO异常或原证据并发改变时保留部分新目录并拒绝
使用，禁止自动删除、重复执行或恢复旧预算。新目录只读计划检查后再决定处理。
不支持通用错误的预算转移，也不自动迁移旧会话。

## 验证与仍缺证据

全量CPU回归435项通过（18.61秒），127个Python文件AST语法检查通过，
git diff --check通过。新子进程实际加载冻结preflight，未导入Isaac。
对原15_58起身smoke执行一次恢复plan：15项输入身份绑定，source_eval1/smoke10/
formal0和原limits完整保留；未创建目标目录或publication receipt，原spec、
ledger、FAILED证书和metrics SHA未变。没有实际发布恢复配置或启动训练。

CPU覆盖：schema兼容/冲突、pose计数、不均衡事件拒绝、任务声明冲突、
冻结实际preflight、原SHA不可重绑、默认plan零写入、发布继承IDs/usage且不授权、
拒绝重复和篡改、报告压缩不改raw。后续冻结schema记录的针对性回归43项通过
（2.18秒）。当前总入口见[ENGINEERING_STATUS](ENGINEERING_STATUS.md)。
未实际运行新GPU episode汇总；事件吞吐、真实低位smoke覆盖仍须新运行证据。
没有为旧550个episode补造family/pose身份，不称新接口改善了策略能力。

仍保留的后续工程：准备器通用exclusive-create/身份/账本事务封装；从任意
基础设施故障恢复的工具；彻底拆除legacy standing字段。它们没有被本轮受限
实现替代，不能悄悄扩大恢复白名单或修改训练任务。

改动文件：domain/{episode_summary,metrics,execution_plan}.py；
tools/{execution_identity,engineering_recovery,entrypoints}.py；wiring.py、
completion.py、stand_chain.py、train.py（冻结新schema源码）；recovery/{episode_metrics,task_protocol,runtime,
recipe,validation,chain,train_stages,extend_training}.py；scripts/prepare_recovery_rise.py；
tests/test_episode_evidence_recovery.py、tests/test_completion.py；
AGENTS、README、STATUS、ARCHITECTURE、TOOL_INDEX、.gitignore及本文。
