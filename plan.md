# Native 架构精简计划：配置记录优先、证据最小化、减少重复门槛

2026-10-14实施核对。本文保留设计依据；工程完成范围与验证入口见下表。
本批只执行代码、CPU与文档工作；未运行仿真/PPO/GUI、未查询后台任务、未清理历史文件。
此前“全部收口”过于笼统：2026-10-14复查新增发现了链报告receipt重复、删除中断恢复、optimizer捕获、诊断准备默认路径与就绪状态拆分缺口，现已补齐并增加实际调用测试。

> **状态归属**：本表只记录本设计的实施快照与验证入口；工程批次的当前状态、授权与未决事项
> 以 [STATUS](STATUS.md) 为唯一正文，本表不重复声明授权或“当前/下一步”。

## 实施状态（2026-10-14）

| 项目 | 当前状态 | 实际入口/限制 |
|---|---|---|
| 配置/源码零复制、阶段身份差异 | 已实现 | source_identity；CPU报告也只保留源码摘要与身份引用 |
| preflight→锁内reserve→runtime提交凭证 | 已实现 | submission_receipt_v1；补齐Motion A/B、独立评估/播放调用；R0准备探针仍按自身前置协议处理，不冒充策略source评估 |
| 历史报告不依赖live src、保守降级 | 已实现并回归 | completion；关键证据损坏保持UNKNOWN/accepted=false；selection详情按路径/SHA引用 |
| 统一模型结构读取及严格加载 | 已实现 | ModelAdapter供health、checkpoint_input、初始化审计、学生load、evaluator/play使用；仍按显式网络/interface构造，不支持凭宽度推断新接口 |
| reward→metrics、light窗口/height override/真实闭链shape | 已存在修复并复核 | 保留producer→consumer专项测试；不重复改公式或物理 |
| 单一ExecutionLimits/null语义 | 已实现 | config/学生声明、授权、trainer/monitor/plan；新授权仍要求inclusive预算，历史formal-only计数显式标注 |
| reward版本与来源/cadence/预算解耦 | 已实现 | validate_instance严格保留算法/初始化契约，source SHA、milestones、capture、storage显式绑定实例；历史模板默认值不决定新预算 |
| 压缩数值证据、摘要只存引用 | 实际剩余接线已补 | chain_report现在账本/receipt只存摘要和路径/SHA；压缩轨迹仍须显式encoding，历史JSON不重写 |
| checkpoint生命周期、日志/字节限制 | 已实现并补中断恢复，显式启用 | 仅RUNNING exact owner可按新声明清理自身未引用文件；公共CLI只读计划；不清历史 |
| 减少窄包装/旧命令 | 已实现 | 删除validate_frozen_cpu、motion_batch及两个deprecated submit壳；correct_smoke_receipt迁至工程恢复模块 |
| 显式学生诊断准备 | 已补齐 | prepare_student_validation必填父spec/两个checkpoint/manifest，teacher按case身份匹配，取消历史默认路径 |
| 指定optimizer初态捕获 | 已补齐实际训练调用 | 默认关闭，phase/update白名单与总字节上限，两个trainer在ppo.update前调用，RNG保持 |
| 提交就绪状态拆分 | 已补齐 | config_valid / authorized / prerequisites_ready / resource_ready，未查资源为null |
| CPU/零写plan/提交审阅包 | 已实现 | validate_cpu记录依赖/PPO SHA，复用拒绝依赖漂移；输出UNAUTHORIZED审阅包，不产生新运行 |

准确改动、实际测试和未通过的历史证书fixture见[工程记录](docs/ENGINEERING_SIMPLIFICATION_20261013.md)。
以下规划仍未执行，不能写成已完成；分别有明确边界：
- 存量文件迁移/GC与精确可回收磁盘量：未执行，本计划明确不授权存量删除；只有临时fixture测试新owner清理。
- 日期型人工prepare变体统一：未实施，路径位于历史手工工作台，涉及已冻结独立网络；需下一批显式迁移设计，不修改原证据。
- 全部模型格式统一构造：部分完成。ModelAdapter已有describe/validate/strict-load，但25D手工Actor/34D Critic的独立构造没有迁入共享固定接口，保留原始版本，不开放按shape自动推断。
- 历史能力集成测试资源分类：并未全部迁成小fixture；PORTABLE入口已隔离历史数据，全项目历史证书fixture仍有22项未批准行为SHA冲突。
- 旧日期脚本全调用/外部CLI审计：未完成，只删除已有替代且当前调用已迁移的入口；历史源码包与复现脚本保留。
- 手工工作台的独立可编辑引擎不是公共链的执行归档；本轮不把它迁回共享src，也不修改活动引擎。
- 旧Motion恢复证书涉及未批准的runtime/configure.py变化，保留严格拒绝；不把源码记录策略当作行为等价审查。
- 新物理实验、训练配方变量、checkpoint实际物理能力均未执行或认证。源码只有hash仍不能重建dirty内容。

## 1. 用户选择：不保存不可变源码包

本次用户明确不要求源码字节归档，采用共享src执行、配置及身份记录方案。取消新CAS、硬链接物化和不可变执行包，避免为几MiB源码再建设存储框架。

每实验只保存requested/effective配置、checkpoint来源身份、实际模块路径、源码摘要、外部算法/依赖版本与命令。新phase可复用同一身份记录；实际检测到变化时追加一个简短phase差异记录，不复制源码、不重复全表落盘。预算及原始结果继续保存。

此方案支持追溯声明及版本差异，**不保证之后逐字节重放**。未提交的dirty源码仅有hash不能重建；共享源码可能在延迟导入或后续子进程启动时变化。正式任务期间避免修改其相关执行模块；如确需修改，现有进程不重启、不抢占，阶段边界记录新身份，跨版本结果不能自动宣称严格同代码对照。没有记录到的变化标UNKNOWN，不能说只存配置就保存了全部历史实现。

源码/文档身份变化以记录为主，不再因当前工作树不同阻塞历史报告。错误checkpoint、物理/输入输出不兼容、预算重复消费和不完整行为验收仍保留必要拒绝。旧源码快照只读兼容，不在本次计划修改时清理；存量删除另按用户具体授权执行。

## 2. 我的实际卡点及对应修复

| 实际卡点 | 涉及接口 | 应改什么 |
|---|---|---|
| 新posture_balance能由环境输出，却首rollout在metrics报字段不匹配 | domain/reward.py、domain/metrics.py、train.py | reward term单一声明直接产生统计字段；新增项测试真实reward→metrics→summary，不再各维护字段列表 |
| 非零命令轻评估motion_window_s=None，姿态统计下标崩溃 | tools/evaluate_checkpoint.evaluate_actor、posture_geometry | 从effective protocol产生唯一具名窗口，score和diagnostics消费；短窗不可被称完整保持 |
| 前次完整来源九命令因预算元数据/无关Recovery变化无法复用，多次重复约31分钟来源评估 | source_evidence.recipe/check、execution_identity | 分开behavior/scoring/schedule/storage/budget；历史来源完整数据保留原执行身份，新代码只决定兼容性，不直接抹掉历史能力 |
| 训练结束后共享config.py变化使报告生成失败，notify未执行 | completion.finalize_report、motion_recovery_certificate、monitor.main | 历史报告只消费记录配置及终态，禁止重新验证当前共享src。通知至少能发送简短“训练结束、报告失败”事件，详细报告另行更正；幂等投递仍保留 |
| 原smoke真实更新已完成，补PPO0成功后仍需专用证书迁移流程 | wiring、prepare_engineering_recovery、motion_recovery_certificate | 区分update证明、故障路径补测、来源能力、新候选验收；一个recovery receipt引用已有证据，不复制历史attempt或层层嵌套新证书 |
| 新诊断继承早期BC模板，health拒绝teacher manifest binding | students.requests/evaluator、prepare_student_validation | 诊断从checkpoint自己的父spec构建，显式height override；不拼接无关模板元数据。checkpoint provenance由一个reader提供 |
| 新1000更新/无墙钟配方需在多处修改版本与预算 | students.training_recipe、training、stand_chain、register_authorization | 单一ExecutionLimits声明updates/samples/wall，null语义统一；reward版本不应决定有没有墙钟上限 |
| 删除用户已退役run后CPU测试失败 | test_motion_absolute_recheck、test_motion_cohort_width_ab | 可移植接口测试用小fixture；历史能力核验单独integration类别，缺数据输出NOT_AVAILABLE，不伪造通过、不让所有CPU测试依赖历史数据永久存在 |

这些问题不说明PPO数学或闭链物理整体错误。尤其站立2.5秒未入站后的策略失败，应作为行为事实，不因接口精简而改成成功。

## 3. 校验按三个时刻收敛

### 3.1 准备：轻量、零写plan

配置schema、未知字段、网络shape、动作单位/顺序、资源请求和额度语义检查。需要读checkpoint时一次读取缓存；不重复计算整个源码树，不扫描全部历史STATUS链接作为提交硬门槛。

提交相关字段明确分开：config_valid、resource_ready、authorized、prerequisites_ready。plan不承担全项目修复。

### 3.2 提交/预约：一个原子边界

创建一次submission receipt：spec ID、source checkpoint SHA、asset ID、source identity ID、协议ID、GPU UUID/逻辑映射/共享授权、session、预算、exact attempt。锁内再次核对文件未改变和未重复预约。

trainer启动后只核验这份receipt与实际读回，不再重新遍历证书祖先；实际加载路径或版本改变只追加差异记录。preflight、reserve、trainer不各自重跑同一昂贵审计；reserve必须保留锁内TOCTOU检查，不能因为去重取消它。

### 3.3 收尾/复盘：历史只读

终态+已结算ledger+checkpoint inventory+raw evaluation引用足够生成结果；不依赖当前src、当前全局健康状态或新授权。原证据缺失/损坏标MISSING/INVALID，仍可完成解释性报告，不赋予accepted。

下面保留硬门槛：输入/动作版本不兼容、资产或checkpoint拿错、关键输入损坏、非有限/控制权故障、重复预算消费、非法资源、评估window/模型绑定不完整时接受失败。

下面降级为告警：当前工作树与旧run不同、无关模块变化、报告格式不同、历史文档链接失效、通知失败。通知故障不改变训练终态，报告故障不阻止终态摘要产生。

## 4. 真正复用的边界

继续保留supervisor（公开请求）、launcher（创建进程）、monitor（owned child退出/预算）、stand_chain（阶段顺序）。职责不同，不为“一个入口”把它们并成巨型文件。允许明确的task-local preparer/reviewer，不要求每个辅助动作再套一层公共CLI。

只共享确实跨Motion/Recovery/学生使用的：发布fresh目录、checkpoint元数据reader、执行receipt、预算记账、trace加载与字段schema、终态事件写入。domain纯函数不读取文件仍有价值，但无需把两行局部转换强行拆模块。

当前不具备可靠全调用图，不能声称下列工具“只有一个调用方”或立即删除：

- tools/completion是CLI、completion.py是实现，应保留。
- prepare_engineering_recovery和motion_recovery_certificate用途非常窄；后者已被train/wiring/preflight/completion共同消费，不能直接内联删除。新通用receipt消费既有已审核恢复证据；原工具仅解释其版本适用的历史工程故障，不再增加新提交入口。
- scripts/prepare_motion_posture.py、prepare_standing_alignment034.py是任务专用配方生成器，保持局部清晰即可；不可强行变成万能prepare。
- submit_motion_high_speed_formal.py、continue_motion_high_speed_submission.py：仅剩历史文档/禁用测试引用，当前兼容壳已删除并迁移catalog测试；外部旧命令不再支持。
- prepare_motion_cohort_width_ab.py/report_motion_recheck_20261007.py与日期型preparer先撤出当前导航，保留复现；只有通用工具覆盖且无活动任务引用时退役。

删除前须列运行调用、测试调用、文档引用和动态import/CLI风险，不按rg命中次数证明“无外部调用”。

## 5. 最值得集中化的声明

- train.record_run_configuration中的手写文件名重命名表：取消扁平副本，记录真实package路径及源码身份ID。
- reward版本与training_recipe固定SOURCE_SHA、update编号、milestones、12次smoke、300次formal混绑：reward公式独立版本，source/cadence/limits是实例声明。固定31D/40D等物理接口仍由版本校验，不开放任意维度。
- prepare脚本固定ROOT/实验路径/teacher manifest：参数接收checkpoint及父spec；通用reader提供实际来源字段，具体配方只填变化。
- GPU资源、共享授权、HAPI及run命名：唯一提交receipt；准备器不默认历史session、GPU或旧run。
- smoke最低数量：按工程事件时长算采样需求，完整优化路径即可，不把“新策略已经站稳”当训练前置；首次新reward必要，完全同配方续块不重复。
- score/runtime/review阈值和窗口：生成同一effective protocol，不再复制魔法字段。每份统计附scope与observed/required samples。

## 6. 源码/CPU验证方案：零复制

stand_chain worker直接使用共享src；train.record_run_configuration替换为记录requested/effective spec、实际入口与source identity引用，不复制整树或扁平文件列表。一次实验的一张相对路径hash表足够，派生task map/绝对map不重复存盘。可记录git commit及dirty=true；dirty内容不归档时明确不可重建。

validate_cpu改为普通CPU验证入口，默认在当前src执行，保存测试名称/源码身份/解释器/结果摘要，不创建完整副本。名称及文档改为避免声称“冻结验证”；旧工具入口移除，调用统一迁移。相同代码/测试/依赖可复用结果，相关变化重新测试，无关变化告警。

不通过运行一次测试的import集合证明完整runtime依赖；phase实际模块路径/摘要作为观测记录，不充当全程无漂移保证。不另建CAS、硬链接或新执行包存储。

## 7. 数据保存与预算

真实占用历史：项目约77GiB中的runs约76GiB，源码当时约3MiB；部分analysis/chain_terminal/candidate_selection单文件.9–.95GiB。整树复制应简化，但第一存储收益在raw数组重复嵌入与逐update捕获，不能误称源码是主要磁盘来源。

raw numeric trace一份压缩NPZ+具名schema；JSON只逐env摘要、协议、轨迹路径/SHA。selection/analysis/terminal不重复嵌入raw或完整候选对象。现有students已用NPZ，legacy路径分批迁移，旧格式reader保持。

保存策略：source/accepted/stage passed/best evaluated/latest保留；普通中间checkpoint按spec策略保留最近K及里程碑；optimizer capture默认关闭、只指定update；失败尾窗单独上限。在线默认不自动删除其他run；清理由显式保护清单和用户授权执行。

日志轮转与trace上限明确，终态空间留余量；容量估计不是锁。存量清理先列所有保留run/教师/验证引用；reader验证及保护清单通过后才按具体授权删除旧副本。旧物理结果不重评分为新协议通过。

## 8. 优先级：只先改三件事

1. **配置+receipt一次绑定，收尾与live src解耦。** 覆盖stand_chain/train.record_run_configuration/execution_identity/completion/monitor，消除身份漂移导致重复source和无通知；停止源码复制，仅保留身份和相关变化记录。
2. **effective配置/协议/limits单一声明，接口测试覆盖真实producer→consumer。** 先治reward字段、light窗口、height override、预算null的实际接线，而非新增证书；将工程资格与行为成功分开。
3. **报告/轨迹去重与checkpoint生命周期。** 原始数组只存一次，终态摘要总能写出；发布+核验+GC有回执。收益比优先精确裁剪几MiB源码大。

## 9. 实施与验收

分三批：声明/receipt reader兼容 → 新提交写入点及共享src执行 → 报告/数据迁移。每批只做本项目CPU/离线验证，具体仿真另授权，不改活动冻结代码。

必测：无关工作树修改不影响历史报告；phase源码变化会记录且不伪称同版本；源码复制字节为0；错误配置或checkpoint损坏拒绝；未成功新策略仍能进入有界学习；行为缺测不发accepted；预算重复预约拒绝；report失败仍落终态摘要但投递不重复；旧runreader保留；配置原子写入/并发预约及清理引用保护；plan零写。

AGENTS只增量调整：规定运行声明来自receipt，源码身份仅记录，不保证重放，不规定每步复制或每个辅助步骤走公共CLI。保留授权、GPU、物理边界、历史只读、预算、后台不轮询及不伪造能力。不要整体重写掉已明确的边界。

未授予本轮存量清理。精确外部调用/历史磁盘可回收量仍需另行审计，不采用未核实的“33个”“只有一个调用方”作为完成标准。工具和subagent只是可选方式，不列为强制实施依赖。

## 10. 本次执行worker补充：25D迁移中的具体阻塞

本节仅补本会话可定位的使用经历与当前调用核对，不将前文其他报告的经历当成本worker亲历。现有计划保留；下面是下一批实现时应直接覆盖的案例。

### 10.1 最痛的两次错误发生在同一条提交链

1. 25D BC来源的准备和preflight可通过，但submission health仍硬取`checkpoint['actor']['mlp.0.weight']`，拒绝实际采用其他state_dict键名的BC模型；同时误要求其具有PPO来源的Critic/update元数据。证据是`manual_train/motion/frame25_ppo_preparation_20261013/submission_check.json`，当前共享代码的硬键在`tools/health_check.py:checkpoint_metadata`。为解决这个边界，制作了healthfix执行副本、重新发布声明，再重新冻结验证。
2. 随后真实环境首rollout又暴露`closure_each`为`[N,4]`、资格mask为`[N]`的对接错误。此前CPU fixture没有代表实际环境形状；closurefix才改为真实四闭链数据并测试归约。工程失败并非“策略不会站立”，不能通过降级机械检查来绕过。

优先建立一个ModelAdapter提供`describe/load/validate`：模型格式、Actor/Critic维数、分布、继承规则由它统一解释，preflight、health、训练和播放消费同一结果。BC来源允许没有PPO Adam/Critic，是否新初始化由recipe显式决定；不靠放宽所有字段解决。增加真实形状的环境状态→reward→metrics→storage CPU测试，不能只增加证书文件。

`tools/execution_identity.verify_frozen_root`还同时要求目录名恰为`source_snapshot`及manifest位置，路径不符先于内容判断拒绝。这使独立工程副本/可移植测试依赖原目录布局。改为显式传ExecutionContext与bundle receipt；位置作为运行记录，内容与语义才决定身份。不能把每个模块的`parents[k]`当项目根契约。

### 10.2 本次查到的窄复用点

以下只扫描共享`src/`和`scripts/`中的具名调用，不包含动态CLI、冻结副本或外部用户，不据此立即删除：

| 函数/工具 | 已见调用 | 建议 |
|---|---|---|
| stand_chain.correct_smoke_receipt | tools/engineering_recovery.py一处 | 移到工程恢复调用处或其局部模块；阶段调度器不应承担修复历史receipt的职责 |
| stand_chain.reconcile_durability | stand_chain.worker一处 | 留作调度器内部函数即可，无需新增公共工具或证书层 |
| tools/motion_batch.validate_request | 本身仅作task拒绝与domain.motion_request转发 | 下一轮枚举调用方后，考虑由请求dispatcher直接调用domain解析器；不是建议删除纯domain契约 |
| manual_train/motion/frame25_ppo_preparation_20261013/prepare*.py | prepare、healthfix、closurefix三个任务变体 | 后续收敛为一个局部可编辑recipe和显式source/bundle参数；历史变体只读保留，不继续复制日期型分支 |

不建议将所有prepare/review合成万能脚本。人工工作台可以保留直白的独立步骤：编辑recipe、CPU验证、查看plan、提交、离线review、GUI；公共共享仅限身份读取、预算提交、模型适配和轨迹schema等真实多调用边界。旧命令不保留兼容壳；迁移现有调用后移除重复入口。历史证据读取仍保留。

### 10.3 过度保存的已测范围与限制

本次仅统计三个代表目录的文件逻辑字节，不是全仓库存储审计，也未计算hardlink去重后的实际磁盘占用：

- frame25_ppo_preparation_20261013：1487文件，总约10.85MiB，其中Python约9.95MiB。
- frame25_actual034_distillation_20261013：499文件，总约3.92MiB，其中Python约3.28MiB。
- 17_09 closurefix训练run：456文件，总约34.07MiB，其中Python约2.71MiB。

整树重复、层层哈希表和执行副本确实增加维护歧义，但这组数据不能证明源码复制是当前磁盘的主要来源。大轨迹、checkpoint及报告嵌入数组的收益须另用按产物类型的inventory核验。原先stand_chain整包copy、阶段扁平copy、CPU副本现已改为共享src执行、每链一份源码身份记录及阶段差异，避免同链三套归档方式；不是取消旧run唯一可复现源码。

`execution_identity.identity`当前对同一组py分别计算absolute和relative哈希，另产生task子集。文件SHA计算一次，派生视图按需生成；task依赖表不应手工认定所有Recovery代码都与Motion无关，因为跨任务适配可能复用其PPO组件。不要用不完整依赖裁剪换取错误的“身份相同”。

### 10.4 本worker的实施排序与验收例

1. **先统一模型/执行上下文和真实接线测试。** 同一BC checkpoint必须在准备、health、训练构造、播放获得一致解释；真实`[N,4]`闭链字段在启动物理前经CPU边界测试。收益是少一次无效提交，而非少一张证书。
2. **再合并校验结果与提交凭证。** 一次准备检查、一次预约锁内身份核对、一次运行读回；CPU验证直接运行共享src。当前工作树改变不阻碍旧run报告，关键输入和凭证损坏仍拒绝。能力未通过不阻止工程有效策略训练。
3. **最后简化局部recipe和保存层。** source、接口、reward、评估协议、预算各有一个声明来源；局部prepare只列差异。trace一次保存、摘要只引用，CAS及checkpoint策略实施前给出实测节省量。

补充验收：GUI灯光/镜头设置独立于训练spec身份，修改视觉设置不重新发布训练声明；模型与动作尺度仍严格绑定。CPU测试从实际公共CLI调用到模型加载及原子结果写入，覆盖`python -m`与子进程入口，不只测试纯函数。历史run证据读取保留；旧命令入口不作兼容。本文为分批实施计划，已完成批次见STATUS。
