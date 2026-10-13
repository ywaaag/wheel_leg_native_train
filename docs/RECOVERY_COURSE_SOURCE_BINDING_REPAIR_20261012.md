# Recovery自动续块源码绑定修复与B阶段恢复

用户在工程停止复盘后明确“同意”修复并恢复B阶段。本轮是一次人工批准的恢复提交，不授权自动重复工程失败。仅修复dispatch源码路径与增加显式恢复入口，不改31D/40D、课程、reward、PPO、物理或教师。

## 原故障与修复

09_56 A块已结算312更新/2555904samples/有效Actor2473984/3057.16秒。owner选择保留等权重来源Actor、进入B前缀1.80秒。11_17 B声明已发布授权，但尚未reserve/创建run：公共supervisor因execution_source_root与actual loaded project src不同拒绝。

根因：prepare_block从冻结owner的__file__生成子声明的execution_source_root；旧dispatch却用父spec中的共享PYTHONPATH执行子supervisor。新spec与实际import包不一致，严格身份校验正确拦截。修复course_io.submission_environment只使用新子spec的声明root，并检查repo内路径及supervisor模块存在；finish_block调用它。不修改execution_identity.verify_frozen_root，不关闭SHA、receipt或publication校验。源码被篡改、冻结回执SHA错误仍拒绝。

## 恢复与账本

公共prepare_student_recovery_ppo新增--recover-task-from，仅支持已经ENGINEERING_STOP、首个新reward B级、原子run零attempt/零used/无run/无chain submission的人工恢复。创建新的recovered task manifest/ledger，原task/失败spec/账本/冻结代码只读；完整复制历史blocks与累计totals，记录逐文件SHA和本次用户恢复scope，不清零312次历史消耗。课程从原B prefix180状态继续，不重跑A、不自动恢复latest退化Actor。

新task isolated/recovery_course_source_binding_repair_20261012/recovered_task；源为A formal/model_update_0.pt，SHAaeed1e4c164ff0029e5fa451174f5e50cce4211c9045fcf1e85e7ce70541b710，Actor等同于00_12最佳update300，不称accepted。B新recipe v9首次新Critic/PPO Adam及5次warmup/12smoke；后续同配方仍完整resume，持续授权/晋级/停滞规则不变。

新spec configs/experiments/2026_10_12-11_42__recovery_course_b_prefix180_block0001/spec.json，独立budget/poses/发布标记。上限smoke12＋formal300，312updates2555904samples/14400秒/2GiB；累计课程不限更新，实际消耗在新task累加，原账本保留。教师前缀1.80秒，32current/16previous同1.80/8normal/8无教师Swing；B50前.50秒、B250随后、学生永久接管，不清物理状态。

## 验证

27专项通过：原路径反例真实subprocess复现、修复后实际importroot匹配、冻结worker重定位receipt严格、错误SHA仍拒绝、真实冻结owner→public preparer→public supervisor零写plan、恢复账本原始消耗不变、已有物理attempt拒绝重试。冻结PORTABLE28通过。全CPU901通过/22错误，与895通过基线逐项同Motion configure.py迁移fixture错误，无新失败。CPU源码hash/模型/原始输入均验证，无新增BC或离线训练。

公共授权登记与check-submission READY，GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，CUDA_VISIBLE_DEVICES=0→cuda:0，共享。提交前一次可用32627MiB，非持续保证。首次恢复--launch采用一次≤600秒事件握手；实际阶段写在isolated/recovery_course_source_binding_repair_20261012/submission.json。不轮询日志/PID/GPU，不另建watcher；再次工程失败不自动重试。

未commit/push；实际编辑：students/course_io.py、公共prepare脚本、两个新测试文件，以及STATUS/TOOL_INDEX/WORKFLOW/ARCHITECTURE/Recovery计划和本报告。旧run/checkpoint/evaluation/spec/ledger未改。

## 一次启动握手与用户状态请求快照

有界600秒握手返回SMOKE，worker身份验证OK，formal_first_update_verified=false，不称formal已开始。用户随后询问训练经验时一次只读快照：source_eval COMPLETED，B50→B250完整教师组合8/8；学生1.80秒前缀后三组后缀0/24，normal0/8，无教师Swing0/8。smoke progress记录12更新98304samples/有效Actor43852，最后一更新5545个学生受控样本，initial488/B50为0/B2502159/student5545，记录40次交接；entry事件41、完整成功0。此时smoke终态尚未落盘，formal没有更新证据。该快照不是持续存活保证，不另行轮询。
