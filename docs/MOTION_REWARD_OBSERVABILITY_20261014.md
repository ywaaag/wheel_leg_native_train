# Motion31奖励区分度、饱和与宽窄核设计

本轮增加CPU审计和轻量指标，没有修改奖励公式、权重、LR、std、PPO、物理、课程或gate；没有启动Isaac/PPO/续训。历史停止链只作输入，原报告和账本不变。新指标尚无物理运行验证。

## 当前实际奖励快照

实际源码`students/motion_tracking_reward.py`经CPU调用和autograd输出：raw、weighted density、乘dt后贡献、状态误差导数。快照绑定reward源码/spec/source SHA，不复制源码树。准备器发布小型快照，每次runtime在AppLauncher前exclusive-create启动快照，并由manifest记录其SHA；授权等元数据变化后启动快照绑定最终spec，不能冒用准备时spec SHA。

本轮已有快照：`artifacts/2026_10_14-18_48__motion_reward_observability/reward_snapshot.json`。其中`proposed_width_comparison`是明确标记未执行的设计对比，不是当前配方。

实际几何成本是有界`x²/(1+x²)`；5倍scale达到0.9615，10倍达到0.9901。严重剪刀腿、长短腿继续恶化时增加的成本很小。因此不能将“raw接近1”解释为几何改善，也不能仅靠tracking变窄解决几何成本饱和。

## 宽核引导、窄核精修

建议下一次独立配方采用证据驱动切换，当前未启用：

1. 较大误差先用宽核，保留现有非饱和Huber尾部。`exp(-e²/d)`中d是误差平方分母，不能再次平方。
2. 同一命令在两个真实更新间隔的完整评估中进入精修范围，同时zero和旧命令保留后，才允许新cohort逐步增加窄核比重。阈值、混合权重、迟滞与切换时间在新spec预先冻结；不同cohort独立登记，不因ramp经过某速度就重标任务。
3. 保留小比例宽核或非饱和误差尾部，避免扰动离开窄核后收敛信号消失。切换在episode/stage边界，不按瞬时误差每步跳变，不在运行中放宽gate。
4. 优先只比较tracking核宽度；几何成本尾部的替换另做单变量实验，避免一次修改两种机制而无法归因。

以误差1m/s为例：d=1时Gaussian分数约0.3679，状态误差导数绝对值0.7358；d=0.04时约1.39e-11、导数6.94e-10。窄核在大误差区域几乎没有区分度。直接缩窄不是加速收敛的保证。这里的导数是reward对显式状态误差的CPU导数，不能当作PPO对Actor参数的实际梯度。

## 真实训练指标与边界

TensorBoard保留旧序号tag，并新增`reward/raw/<field>`、`reward/raw_std/<field>`、`reward/weighted_density/<field>`、`reward/dt_contribution/<field>`及`reward/total_per_step`。density只在记录有明确dt时输出。现有raw均值/std覆盖整rollout，包括eligible以外的零值；eligible数量另报，不能当作保持段指标。

新增`reward_bounded_tail_fraction/{mirror,wheel_alignment,leg_balance}`：eligible样本中raw≥0.95比例，只是进入有界尾部的监测，不是严格梯度饱和率。

`cohort_statistics`按固定episode目标命令分组，controlled/hold/parking分开，记录vx/MAE、yaw、height、pitch、roll、双腿长度差、关节镜像差、轮心水平前后差、closure、双轮接触、限矩命中、raw动作越界和物理故障比例。记录来自现有pre-reset snapshot，训练统计不等于独立评估通过；没有样本输出null，zero方向率不定义为通过。接触统计明确使用两轮力均>2N，限矩命中不自动构成行为失败。

限矩字段`controller_effort_limit_hit_any`来自现有控制器限幅后的effort，不能冒称独立测得的applied torque饱和率。

所有逐步计数在设备端累积，每rollout一次export；无新增逐物理步数组持久化。episode时长改用episode政策步时钟，FSM age只表示阶段时间；旧记录不回写。保持/停车窗口从冻结训练schedule解析，与独立eval窗口区分。

## 验证

定向CPU：`tests/test_motion_reward_observability.py`、`tests/test_motion31_training.py`、`tests/test_student_performance.py`。覆盖曲线有限性/dt/导数方向、宽窄核平坦区域、RNG不变、具名TB字段、缺失值、pre-reset快照、窗口分离及真实episode计时。

尚缺：新指标真实Isaac采集、GPU吞吐开销测量、实际PPO梯度和任何宽窄核训练A/B结果。没有快速收敛或站稳能力保证。

实际结果：PORTABLE 75文件，420 passed / 8 skipped；定向53 passed；9文件CPU compile通过；512准备器plan exit0、simulation0、onlinePPO0、files_written0，未创建新配置/run。记录在同一artifacts目录`validation.json`、`cpu_plan.json`。TensorBoard历史分项一次导入完成，logdir为`artifacts/standing_survival_v14_20261014/tensorboard/motion512_reward_named_review`；旧记录不含dt时不生成density，详细cohort指标只对未来新记录可用。

## 本轮精确改动文件

- `src/native_stand/students/motion_reward_audit.py`
- `src/native_stand/students/motion_statistics.py`
- `src/native_stand/students/motion_runner.py`
- `src/native_stand/students/performance.py`
- `src/native_stand/command_v6/tools/metrics_tensorboard.py`
- `scripts/audit_motion_reward.py`
- `scripts/prepare_motion31_training.py`
- `scripts/prepare_motion31_wiring_recovery.py`
- `tests/test_motion_reward_observability.py`
- `AGENTS.md`
- `TOOL_INDEX.md`
- `STATUS.md`
- 本文。

未提交Git，保留其他dirty changes。旧run/spec/ledger/checkpoint/evaluation未写入。
