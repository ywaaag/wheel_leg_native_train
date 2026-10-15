# motion_recipe evidence repair and CPU analysis
> 证据注记：部分引用目标已于 2026-10-14 存储精简中清理，原始数据不可再访问；相关结论按当时 run 身份与协议保留，不重建、不补零。集中说明见 docs/README.md。


本轮0物理样本、0在线PPO、0离线optimizer step；不改奖励/学习率/课程。历史run、评估、模型、账本均保留。新机器结果：`isolated/motion_recipe_20261004/diagnostics/evidence_repair/analysis.json`。

## 证据清单与边界

历史正式证据位于`runs/motion_recipe_20261004_formal_20261004/formal_run`。source checkpoint为`runs/wide_leg_from_scratch_20261002_formal/model_update_500.pt`；50/100、metrics、10个独立评估、retention、manifest/source_snapshot和ppo_diagnostics均存在。来源SHA fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1；100 SHA 370bdb2d472e8c48635298c152c20acd22a28026768baf82b331ac2df6aaeeb1。历史100updates/819200samples/1538.023s，retention停止。

三份transition各8192行，policy[8192,25]、history[8192,125]、actions[8192,6]；value/return/advantage/old/new logprob各[8192]；old/new distribution为mean/std二元组。机器结果保存逐字段shape及文件SHA。

- 直接复算：保存批次的surrogate、ratio/clip/KL估计、逐命令value/return/advantage统计。
- 来源重建验证：仅update1旧actor/critic输出；最大value误差1.43e-6、logprob2.00e-5、mean2.61e-7、std0。未声称重建update2/3旧模型。
- 反事实：来源/50/100在同一update1观测上的确定性动作，以及一致改写当前和五帧history command的敏感度。不是物理验收。
- 缺失：raw reward、done/timeout、末端bootstrap、pre-update optimizer/RNG、历史shuffle、50/100完整更新批次。无法独立历史GAE；不从returns反推reward。

本轮没有有限重放：已有STOP_AND_PPO_AUDIT与三个ppo_replay_evidence JSON覆盖实际/参考PPO对照及shuffle对齐；optimizer_matrix已做冻结batch对照；motion_momentum物理清零一阶矩仍站立退化。重复该变量没有明确新增问题。模型/critic独立构建，参数ID交集为空；不支持共享参数梯度冲突解释。

## 历史早期真实更新

标准objective=mean(min(A*r,A*clip(r,.8,1.2)))，更新前r=1。全批次改善：.001156304/.001279439/.003460805，与用户结果一致。

|命令|样本/次|u1改善|u2改善|u3改善|
|---|---:|---:|---:|---:|
|-.2|1152|-.000949|+.001515|-.001229|
|-.1|1408|+.000800|+.000492|+.003719|
|0|3968|+.001802|+.000184|+.003077|
|+.1|512|+.002645|+.009510|+.004463|
|+.2|1152|+.000812|+.002120|+.008713|

机器JSON包含每组均值/std/分位数、正负优势比例、ratio分位数、clip、KL及正负概率变化和优势加权贡献。±.2三次归一化优势均为负；零命令优势均值.479/.485/.519，正优势比例约.82。这不证明reward错号，也不证明归一化bug。-.2在u1/u3目标变差而全局变好，证明早期批次存在组间收益不一致；零命令早期目标改善仍不保证长期站立保持。共享网络不要求每样本都改善。

## 动作共同偏移与命令敏感度

动作顺序为左腿两通道、左轮、右腿两通道、右轮。乘尺度[.5,.5,100,.5,.5,100]得到腿目标offset rad及轮目标rad/s；腿绝对目标还需reference，不能把offset冒充目标。完整六通道分组值在JSON。

一致零命令反事实扫描：source左右轮均值约+.038/-.125rad/s；50约-3.198/-2.245；100约-6.723/-4.986。共同偏移显著。

反事实(+.2)-(-.2)轮响应差：source+4.510/+.875rad/s；50+4.309/+.432；100-12.071/-6.284。100发生网络命令响应差异的符号改变，而非仅所有命令加上同一偏置。结合独立物理评估的正向反转与零命令漂移，支持二者同时存在。没有仅凭轮动作符号推导前进方向；左右轴映射未在本轮重新物理验证。姿态和接触未全面崩溃削弱“站立鲁棒性不足导致摔倒”的解释。

## 修复及验证

仅未运行`isolated/motion_recipe_20261004`修改：

- 新domain/evaluation_plan.py为trainer/CLI共享目标协议，显式fixed/ramp、时长、窗口、seed/scored env与gate。CLI使用active_stage并实际传command_mode；非零gate与trainer同解析；duration override显式标记。未修改旧来源评估，来源运动同协议基线仍缺失。
- tools/prepare_evidence.py原子创建新spec/零used/空attempts/UNAUTHORIZED账本，已有路径拒绝；SHA/外部终态身份错误在写入前失败。外部来源/smoke引用只进入external_prerequisites，并在preflight及ledger.reserve均验证，不拷贝历史attempt。
- monitor.py抽取真实supervise调用，复用timeout/launcher；无session时不发送通知。reconcile继续只结算exact attempt，并已测第二次调用不重复结算。
- train.py快照增加新解析/准备模块；evaluate_checkpoint.py plan记录resolved_protocol。
- offline_review.py及test_evidence_cpu.py新增CPU工具。未启动launcher。

运行：
`/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q isolated/motion_recipe_20261004/test_recipe_cpu.py isolated/motion_recipe_20261004/test_evidence_cpu.py`
结果24 passed。测试覆盖原16项及新准备SHA/身份失败、重复路径、plan不写、真实monitor fake child正常/失败/超时、缺终态/重复结算。协议测试验证共享解析与两个入口调用；未模拟整个Isaac evaluator。精确独立CLI plan-only返回fixed/9s/[2,6]/seed104/8scored、150D，simulation/PPO/files_written=0。新代码仍需未来物理验证。

监督者未来入口是isolated包native_stand.command_v6.launcher→monitor→train；launcher exact ledger reservation、一次握手，monitor硬超时/异常补结算，trainer评估/保存/更新计数。CPU监督测试不等于已提交后台任务。本轮不写旧spec/ledger，误复制事实保持原状。

## 下一步

未发现早期保存批次loss符号或actor/critic共享参数错误。新增证据最支持“优化时全批次收益与命令分组/长期行为不一致，伴随共同动作偏移及命令敏感度反转”；未确定哪种机制导致后期变化。单纯upright权重过大、物理崩溃、继承动量唯一根因等解释均未获充分证实。

需要的最小新数据问题是：退化模型附近一次真实更新是否改善保存批次目标却加重偏置，以及GAE来源是否正确。建议另行授权PPO0采集64x128=8192样本、总<=300s，固定50模型和它自身optimizer（只用于诊断，不续训）；完整保存所有env raw reward分项/dt、obs/history/执行command、raw/clip/action目标、done/timeout/pre-reset末态、最后bootstrap、actor/critic/optimizer/RNG及依赖身份、storage与shuffle。随后有限CPU重放，不把重放模型用于训练。若50 checkpoint缺可核验optimizer则阻断，不从来源冒充。独立GAE/对齐不一致支持实现问题；一致而分组贡献相反支持优化/多任务归因。此建议未授权未执行，不重复一阶矩物理A/B，也不追加长训。来源fixed基线若未来需要能力对照仍须独立补齐，不能本轮填通过。
