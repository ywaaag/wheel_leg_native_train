# Motion31 来源1600冻结rollout审计（2026-10-15）

## 结论

本次新授权诊断已COMPLETED；只有实际仿真和随机采样，没有online/offline optimizer更新。没有修改reward、核宽、课程槽位、Actor/Critic结构、std、Adam或物理配置，不自动续训。

本批不支持“global centering把旧任务正确动作的正advantage翻成负值”的具体解释：raw全局均值−0.017984，所有组的raw正→normalized负比例均0。存在更值得追踪的起点分布问题：−1.5组占18.75%样本，贡献98.599%的全局advantage离均差平方和，且局部Actor surrogate梯度远大于旧任务。方差集中不等于已证明normalization错误；难任务本来可能产生较大梯度。

## 身份与边界

- run：`runs/2026_10_15-16_00__motion31_u1600_frozen_advantage_probe`
- spec：`configs/experiments/2026_10_15-16_00__motion31_u1600_frozen_advantage_probe/spec.json`
- attempt：`4c6364fd842943a7881162cdbd3ded66`，独立evaluate1账本已COMPLETED结算。
- source：`runs/2026_10_14-21_23__motion31_posture_quality512_v3/formal/model_update_1600.pt`
- source SHA256：`83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`
- parent：已结束的`2026_10_15-10_26__motion31_straight_yaw512_course`冻结spec，SHA256 `8f07982f33cc3214dbad5cfd828117c0f8e54b795e184a551758be1c2199b506`。
- 物理GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`→CUDA0，共享授权；不操作其他任务。
- 上限600秒、capture未压缩128MiB；实际账本wall69.646秒，capture43,906,288bytes（约41.87MiB）。本诊断未开通知，不新增watcher。
- 实际采样512env×(800预运行＋128采集)＝475,136 transitions；其中65,536条完整storage用于审计。初始化和reset语义沿用原环境，不恢复历史仿真状态。
- 完整恢复Actor/Critic/Adam/std/可恢复RNG及cohort mix，但不调用update/optimizer.step。最终Actor/Critic/Adam state_dict逐项相等，原checkpoint SHA未变。
- mix仍为`[0,.75,0,.75,0,0,0]`；命令仍为0/±.5/±1/±1.5，槽位`128/48/48/48/48/96/96`。

## 真实样本结果

以下为随机策略在一个1.28秒捕获窗口的统计，不是30秒确定性能力验收。前六组全部处于训练保持段；−1.5因为失败reset，仅8,787/12,288条处于保持段，其advantage统计仍包括全部12,288条有效transition，不能和保持段速度混作相同窗口。

|目标vx|有效样本|保持段vx|保持段MAE|raw A均值|normalized A均值|raw A标准差|
|---|---:|---:|---:|---:|---:|---:|
|0|16384|.02649|.02662|.00678|.05441|.01055|
|+.5|6144|.49245|.01299|.02453|.09340|.01322|
|−.5|6144|−.41560|.08440|.00191|.04370|.01277|
|+1|6144|.98770|.01642|.04775|.14442|.02218|
|−1|6144|−.84578|.15422|−.00428|.03011|.01807|
|+1.5|12288|1.46012|.04002|.08018|.21568|.03066|
|−1.5|12288|−1.04854|.45146|−.22009|−.44404|1.02396|

捕获中12次terminated全部来自−1.5；truncated0。预运行另有84次terminated，未保存预运行逐命令原因，不将其归因到具体命令。捕获没有逐项quality termination cause tensor，因此具体触发gate仍UNKNOWN；不能仅凭termination数量断言关节或姿态实现错误。raw action clip fraction各组均0。保持段height约.342–.345m，平均abs pitch约.029–.045rad；这些短窗值不授予完整姿态通过。

全局raw A均值−.017984、标准差.455141，positive比例68.744%；normalized后positive比例84.099%。−.5/−1的符号变化主要是负→正；不是旧任务正样本被翻负。按命令误差区间的全部分布、value/return及具名reward贡献见audit.json。

## 数学与前向一致性

- 使用真实ControlledPPO/storage/compute_returns，没有自行替代在线GAE。
- CPU独立逐步GAE/return复算最大误差0；valid-global normalization复算误差0；Actor列22–24命令readback误差0。
- 同输入重复CPU前向差0；CPU与采集GPU action mean最大差1.069e−6，old log-prob差8.202e−5，报告为浮点差异，不宣称CPU/GPU bit-exact。
- 来源与候选检查无observation running normalizer；Student.update_normalization为空，命令固定除以4，不适用running mean/std漂移假设。

## 离线局部梯度：有信息，但不是历史更新复现

对已保存状态/动作/normalized advantage，在冻结来源上计算ratio严格等于1时的Actor surrogate梯度。按真实全batch分母加权，不进行optimizer，不生成新checkpoint，不把重构梯度冒称历史训练梯度。

- −1.5组范数2.56324，五旧命令合计.17238，全batch2.67153。
- −1.5梯度与全batch cosine .99478；剔除−1.5梯度后与原全batch cosine .42164。
- 旧五组与新两组合计cosine **+.40681**；−1.5与旧五组也约+.40679，因此不支持“所有新旧梯度都反向冲突”。+1单组与全batch约−.07481，是局部弱冲突，不能泛化到所有命令。
- Actor/Critic不共享参数。Critic通过advantage影响Actor，不是二者梯度直接抵消。
- 实际PPO还有多minibatch、多epoch、clip、Adam和梯度裁剪，以上不能代替其实际更新方向。
- 本次Critic仍是来源1600；没有执行原formal最初5次Critic适应。因此结果是**未经新任务价值适应的起点证据**，不能证明update250–1000的历史分布也相同。

## 唯一下一优先

不立即改reward、Adam、global normalization或重新长训。先用这批固定数据做有限CPU单步Adam方向对照，检查包含/消融−1.5梯度时旧命令动作分布的变化；明确只是离线反事实，不能直接解释机器人速度。若要在线检验task weighting，另立同源单变量声明及运行授权。保持来源1600为基线，不从750/1000续训。本次没有执行任何offline optimizer step。

## 工程改动与证据

新增：

- `src/native_stand/students/motion_advantage_probe.py`：仅显式版本启用的冻结采集/独立预算验证/公共evaluate adapter。
- `scripts/prepare_motion31_advantage_probe.py`：默认零写准备；不自动授权或启动。
- `scripts/review_motion31_advantage_probe.py`：SHA绑定CPU GAE、归一化、命令读回、前向及局部梯度复核；exclusive-create新审计目录。
- `tests/test_motion_advantage_probe.py`：CPU实际PPO storage无step测试、独立GAE、契约拒绝、局部梯度无参数/RNG修改。

增量接线：`students/requests.py`、`students/evaluator.py`、`command_v6/tools/health_check.py`。初次submit在reserve/AppLauncher前被健康检查误用训练2000预算规则拒绝；已用显式诊断validator修正，没有增加物理attempt或绕过来源/资产/父配方身份。

导航：本文件、STATUS、TOOL_INDEX。不改历史run/spec/raw evaluation/ledger/checkpoint，不Git提交。

证据：`artifacts/2026_10_15-16_04__motion31_advantage_audit/audit.json`、`audit.md`、`gradient_summary.json`；run内`probe_result.json`、`rollout.npz`、`runtime_readback.json`、`reward_snapshot.json`、`terminal_report.json`；账本在新spec同目录。

CPU验证：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python scripts/test_portable_cpu.py`，477 passed、8 skipped、4 warnings；7个本轮Python文件AST解析通过。原parent spec、来源checkpoint、USD SHA复核未变。精确改动及哈希见审计目录`implementation_manifest.json`，完整测试输出见`cpu_tests.txt`。
