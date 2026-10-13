# Recovery 人工开发与训练工作台

这里是一份可以直接打开源码、手动改参数、逐步检查并继续迭代的工作区。推荐入口是 `manual.sh` 的**单步骤命令**，不再要求使用旧的 prepare.sh/train.sh 一键流程。完整可复制命令只维护在 [TOOL_INDEX：人工 Recovery 工作台](../../TOOL_INDEX.md#人工-recovery-工作台)。

## 先找到实际源文件

可编辑源码在 **`editable/src/native_stand/`**。这是一份真实源码副本，不是只含参数的接口占位。你可以在IDE中直接编辑。冻结、发布、测试、授权、资源检查和启动分别由你决定何时执行。

| 你想改什么 | 可编辑源文件（相对于 editable/src/native_stand/） | 说明 |
|---|---|---|
| 常用奖励权重、自定义Tensor奖励 | `students/manual_reward.py` | 当前人工奖励入口；优先从这里开始 |
| 高度/支撑/角速度等基础奖励公式与完整保持累计器 | `students/recovery_task.py` | `reward()`、`configuration()`、`Certificate`；改公式时同步其声明和测试 |
| reset、31D观测生产、实际目标缓存、reward/终止调用 | `students/runtime.py` | StudentEnv、TrainingStudentEnv；物理后/reset前状态必须对齐 |
| 教师前缀和学生交接 | `students/course_runtime.py` | CourseStudentEnv，只有bridge模式使用教师前缀 |
| 网络结构与动作分布 | `students/model.py` | 当前31→128→64→32→6、40D Critic；更改结构属于新接口实验，不直接给旧checkpoint强行加载 |
| PPO组装和优化参数 | `students/ppo.py` | assemble()；常用LR建议先改settings.toml，避免声明与实际实现冲突 |
| rollout、GAE、更新、保存、评估调用顺序 | `students/training.py` | 共用真实训练循环；BC为0，初始化/教师控制样本被mask |
| 受控样本Actor/Critic优化 | `recovery/controlled_ppo.py` | mask、全空minibatch、有效样本归一化 |
| 31D/40D编码和物理目标转换 | `students/mcu_interface.py` | 固定字段与left-first顺序；不能只改Tensor维度 |
| 2.5秒入口与10秒证书 | `students/protocol.py`、`students/recovery_task.py` | 奖励与验收不是同一件事，不能调奖励时顺手放宽gate |
| 公共提交、monitor、账本 | `command_v6/` | 保留身份、预算与物理保护；通常无需修改 |

**`editable/.../students/manual_reward.py` 是新分步流程的奖励真源文件。** 根目录的 `reward.py` 仅供旧一键工作流和第一次init-source使用；初始化editable后，两者不自动同步。不要在两个地方同时修改。新freeze只读取editable里的代码。

`editable/src/native_stand/students/manual_parameters.py` 由freeze从settings.toml生成，不要把它当作第二份参数入口。对应实参及spec都需一致，校验不一致时会拒绝，不静默选择其中一份。

## 两种不同的迭代

| 情况 | 操作方式 | 保留状态 | 重新执行什么 |
|---|---|---|---|
| 改奖励、源码、课程或学习率 | 改editable与settings，从选定旧Actor开新实验 | Actor；教师只读 | 新Critic、Adam、RNG；source、smoke12、formal；各阶段5次Critic warmup |
| 配方、源码、课程和超参完全不变，只想多训练一块 | 对已结算的新版人工formal检查点执行resume | Actor、Critic、Adam、RNG、累计update、recipe_updates、课程状态 | 新run/账本和来源评估；复用原公共smoke证书，不重复smoke或warmup |

完整resume**复用原来的执行源码**，不读取你之后修改的editable代码。它恢复训练状态，不恢复PhysX瞬间；新进程真实reset会记录。旧版工作台或其他Codex配方不能直接冒充同配方resume；可以用其Actor启动新实验。

工程FAILED、未结算、证书缺失、来源SHA漂移不能走正常resume。没有“latest必定最好”；由你选择已保存检查点。每个新块独立授权与结算，不自动开下一块。

## 分步骤流程及每步产物

| 步骤 | 输入 | 输出 | 会不会用GPU |
|---|---|---|---|
| 1. init-source（首次一次） | 当前共享实现、初始设置 | editable源码和测试副本 | 否 |
| 2. 人工修改 | settings.toml、editable源文件 | 你的工作区改动 | 否 |
| 3. freeze | 你的可编辑代码与设置 | experiments/新名字/src、draft.json、冻结设置 | 否 |
| 4. publish | draft.json | 独立spec、poses、未授权budget、experiment.json、session.env | 否 |
| 5. validate | experiment.json | cpu_validation及测试、schema、零写plan报告 | 否 |
| 6. 人工plan与检查 | session.env、spec | 公共supervisor只读计划 | 否 |
| 7. authorize | 明确批准说明 | 公共授权receipt和本实验所有权账本 | 否；不会自动提交 |
| 8. check-submission | 已授权spec、GPU0共享 | 资源、UUID、session、输出、来源核验 | 读取GPU信息，不启动仿真 |
| 9. launch | 通过检查的声明 | 新run，由既有owner执行预算内训练 | **是** |
| 10. 人工复盘与播放 | terminal、评估、checkpoint | 决定继续、换奖励或停止 | 读报告不需要；GUI需要 |
| 11. resume或新实验 | 选定检查点 | 新草稿，重新走publish以后的步骤 | 建草稿不需要；提交后需要 |

所有写文件步骤都需显式`--write`。省略该选项只返回该步骤的计划。任一步失败都不会替你自动执行下一步。分步工具不自动授权、提交、轮询或续训。

**物理启动的边界：**最后手动调用的公共supervisor内部仍执行source→smoke→formal并由owner监督预算与结算；本版没有把这三个物理阶段改造成三个独立手动提交。它不自动启动下一个实验。需要修改算法时改editable代码；不要绕开supervisor直接运行无账本的私有trainer。

## settings.toml每项含义

| 字段 | 默认/范围 | 用途 |
|---|---|---|
| purpose | human_recovery；小写英文/数字/下划线 | 新实验名字后缀。不同人建议不同purpose |
| mode | swing / standing / bridge | 训练状态分布，见下表 |
| teacher_prefix_s | 0–1.80秒，10ms对齐 | 仅bridge有效；从合法初始化后开始计时 |
| formal_updates | 100；6–300 | 本块formal更新数，不是累计训练上限 |
| learning_rate | 3e-5；1e-6–1e-3 | 新实验的PPO学习率，声明与真实assemble一致 |
| seed | 20261013 | 新实验随机初始化；完整resume恢复检查点RNG |
| chain_wall_s | 7200；2400–14400 | 包含来源、smoke、评估、保存和清理 |
| source_checkpoint | 本地recovery_source.pt | **新实验**继承的Actor |
| source_parent_spec | 该checkpoint自己的formal/source_snapshot/spec.json | 核验训练谱系，不是随便选一个相似spec |
| physical_gpu/resource_mode | 0/shared | GPU0共享，不抢占、不换卡 |

| 模式 | 64环境实际配置 | 学生要做什么 |
|---|---|---|
| swing | 56无教师Swing＋8正常站姿 | 学生从Swing全程自主起身 |
| standing | 64正常站姿 | 站立专项；不能以通过专项宣称Swing通过 |
| bridge | 32当前前缀＋16同长度前缀＋8normal＋8无教师Swing | 从教师产生的真实动态状态接住后半段 |

bridge里0–0.50秒是B50、之后是B250，前缀到时学生永久接管；不reset、不清速度。辅助后缀通过不能等同于无教师Swing通过。两位教师和31D学生各用自己的观测与动作尺度。

默认新实验smoke12＋formal100，共112更新、917504原始样本；64×128＝8192样本/update。source/smoke各900秒，formal使用剩余墙钟。完整resume不重复smoke，因此同样formal100为100更新、819200样本，source900秒，其余墙钟给formal。有效Actor样本少于原始样本，两者分开统计。

## 如何手改奖励

manual_reward.py的`WEIGHTS`依次是高度进展、支撑质量、努力、六通道实际目标变化、入口后角速度、入口后速度。下面四个常量分别是入口后轮平滑、双轮接触不足、零速Huber、弱镜像。改变常量后freeze，运行中不会热加载。

`evaluate(context, base, cfg)`接收post-physics/pre-reset数据。base含现有具名raw、weighted、dt和events结果。连续项是每秒密度，乘dt=.01**一次**；entry/success事件不再乘dt。当前manual_support要求返回原有字段集合、形状与有限Tensor；自定义项若需独立新日志，要同时扩展support及training.py保存路径，不能只新增dict字段就假定会自动记录。

| context字段 | 含义/单位 |
|---|---|
| height / h0 | 实际机体高度 / 本episode真实起始高度，m |
| angles | 当前实现顺序的pitch、roll，rad |
| contacts / clearance | 左右轮传感器合力N / 机体净空m；不是已认证法向载荷 |
| torque | 六主动关节policy采样力矩，Nm；不代表完整1kHz记录 |
| previous_targets / executed_targets | left-first实际物理目标，腿rad、轮rad/s |
| angular_body | native身体坐标角速度rad/s；水平姿态轴使用基础实现的[0,2] |
| velocity_native / yaw | native线速度m/s / yaw角速度rad/s |
| active_leg_q | left_hip、left_active、right_hip、right_active，rad |
| entered / controlled / fault | 首次入口确认、该步学生真实控制、runtime fault标记 |
| entry_event / success_event / failure_event | 一次性事件；窗口结束不是成功证书 |

不要从不清楚的坐标猜pitch/速度符号；查看runtime和mcu_interface的实际编码。初始化、教师控制及fault的总reward仍被强制置零。优先单变量改动，比较同协议来源与候选，而不是只看训练reward增加。

## 保持的接口与物理

Actor31D、Critic40D；动作6D left-first。Actor输入为身体角速度、重力、四腿位置、六主动关节速度、上一实际执行腿/轮目标和命令/技能标志。具体索引、归一化以mcu_interface为准。Recovery技能全程不切换。

腿reference＋1.5rad×action，轮100rad/s×action；动作裁剪后解码，再机械限位，最后更新实际目标缓存。physics/PD/policy＝1/5/10ms、40/5.5Nm、原Plane/闭链USD/PD保持。本工作台不以改力矩、隐藏控制器或过滤器获取“进步”。

你可以阅读全部源码，但改网络、接口、动作尺度或验收需要新版本及相应适配，不是只硬编码一个数字就仍称原模型兼容。

## 训练后看哪些文件

| 文件 | 作用 |
|---|---|
| runs/实验名/chain_terminal_report.json | 全链终态、失败、阶段和墙钟；COMPLETED不等于accepted |
| formal/metrics.jsonl | 每update的奖励、有效样本、KL、梯度、触限等 |
| formal/progress.json | 已记录的更新、checkpoint和评估入口；不是进程存活证明 |
| formal/candidate_registry.json | 来源及各检查点的同协议评估 |
| formal/candidate_selection.json | source/latest/best_new/best_overall/accepted分开 |
| formal/evaluation* | 各条件、各环境的第一episode原始行为结果 |
| formal/source_snapshot/spec.json | 该训练checkpoint自己的parent spec |
| configs/experiments/实验名/budget.json | 本实验真实消耗和attempt，别手改used来续训 |
| experiments/实验名/task_ledger.json | 本块结算，始终不自动提交下一块 |

先确认是否真正完成入口和固定10秒保持，再看触限、轮目标变化、pitch/roll、速度和位移。训练reward或最高高度不能单独选最佳。学生跌倒是行为结果，接口/非有限/闭链故障是工程或物理异常，分开处理。

## 人工协作、磁盘与常见问题

- editable可以边训练边编辑，正在运行的实验使用冻结副本；改动只影响下次freeze。
- 每一步显式使用自己的draft/experiment路径，不依赖last_experiment。多个人不要同时编辑同一个editable；另开独立副本并明确工作目录。
- 源码、奖励、模型SHA漂移：新freeze，不改发布标记或关闭校验。
- GPU资源不足：不启动、不换卡。没有attempt时可由人工稍后再做check；已消耗或FAILED不能原地重复launch。
- init-source提示已存在：直接编辑现有editable，不覆盖它。
- label/接口/recipe不符：核对checkpoint自己的冻结spec；B50/B250不是31D学生。
- GUI不代表认证，GUI也会占GPU；停止自己的GUI不代表停止后台训练。
- 每块产物上限2GiB，预留128MiB结算空间，不自动删旧run。editable及冻结源码只复制代码，不复制整个历史训练目录。
- models/catalog.json是固定副本身份，不是实时best；当前副本未被声明为完整自主起身accepted。

旧prepare.sh/train.sh保留兼容，但不是推荐人工流程；它们仍会组合多个准备/提交步骤。新版分步流程、裸源码和完整resume以本文及TOOL_INDEX为准。

## 验证状态

本轮只执行CPU准备、冻结测试与零写计划。真实仿真、GUI、PPO和完整resume的物理行为均未运行，不能宣称技能通过。CPU测试覆盖真实Adam/Actor/Critic/RNG恢复和续训预算；真实resume还需要首个人工实验已结算、相同源码和有效公共smoke证书。
