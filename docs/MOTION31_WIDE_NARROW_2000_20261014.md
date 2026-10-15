# Motion31宽核引导与证据驱动精修：2000更新声明

用户新授权“请尝试开启训练，授权2000次”。这是新实验，不继承旧链余额，也不从退化的u100/u200续训。

## 冻结运行身份和预算

- spec：`configs/experiments/2026_10_14-19_04__motion31_wide_narrow512_2000/spec.json`。
- run：`runs/2026_10_14-19_04__motion31_wide_narrow512_2000`；独立账本同spec目录`budget.json`。
- 来源：`isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt`。
- 来源SHA：`a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`。
- 总计最多2000次真实在线更新：smoke50＋formal1950；总采样上限131,072,000。来源PPO0不计在线更新。
- 512env×128steps/update=65,536条；固定槽zero128、±0.5/±1各96。只解锁L1，无yaw/高速自动升级。
- 全链18h；来源≤1h、smoke≤1h、formal≤16h；产物≤2GiB，保留terminal空间，先到预算或停止条件则结算。
- physicalGPU0 UUID`GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`→logicalCUDA0，共享授权；不抢占/停止其他任务。
- 当前冻结owner：`191bacc3-e5c7-4b8f-ae3d-5677eada837b`。沿用既有后台报告和终态通知流程，不由Codex轮询。

## 本轮唯一奖励机制变化

显式奖励版本`student_motion31_tracking_reward_refinement_v2`，旧v1默认行为不变。

非零直线cohort使用`(1-alpha)*exp(-e²/1.0)+alpha*exp(-e²/0.04)`；alpha初始0，每次符合精修条件的连续两次完整评估后增加0.25，上限0.75。至少25%宽核及现有非饱和Huber尾部始终保留。zero、yaw奖励及所有权重、几何成本、探索、LR、Adam初始化、归一化、网络和物理不变。此方案不预称根因修复。

精修条件逐命令、8/8全部满足：保持MAE≤0.20m/s、方向≥0.95、gain∈[0.8,1.2]，并通过连续30秒、height/contact/saturation/closure/clearance/tilt及同来源pitch/roll guard。缺字段/未完成/不安全不精修。普通失败继续本级预算；失败时清空精修确认streak，已有混合比例冻结，不增加预算、不自动回滚换配方。

只在完整固定评估之后、创建下一训练环境前改变混合比例，不以ramp瞬时速度重标任务。决定绑定评估文件SHA，保存`reward_refinement_after_<update>.json`；checkpoint保存实际已使用的refinement state。scoring协议保持既有完整五命令，训练奖励精修并不放宽验收。

formal每100更新完整五命令评估，最终1950另评；完整两次通过可提前有界完成。旧已认证来源能力连续两次退化停止；runtime/非有限/身份/存储/预算故障停止。来源Motion未认证，不因当前未学会运动阻止进入PPO。

Actor/std原样迁移；来源不含Motion Critic/Adam/RNG，因此新建49D Critic、Adam和冻结seed，前5次为critic warmup并计入在线预算。formal重新从原始来源初始化，不继承smoke模型；不宣称完整恢复旧物理状态。

## 启动前证据

授权后的真实奖励快照与混合曲线：`artifacts/2026_10_14-19_04__motion31_wide_narrow512_2000/reward_snapshot_authorized.json`。各phase在AppLauncher前另保存绑定最终spec/code的`reward_snapshot.json`。

CPU：全PORTABLE 423 passed、8 skipped；定向56 passed；绑定来源模型/Adam/std初始化readback通过，实际LR3e-5，零写supervisor plan PASS。记录：同名artifacts目录`cpu/validation_result.json`及spec目录`cpu_supervisor_plan.json`。formal单阶段保守估算含临时/terminal约1.485GB，当前磁盘空闲约56GB；实际全链仍由2GiB硬上限保护，不保证耗完2000更新。

接线修正：Motion统计从`student_training`读取schedule（`motion_training`只有block元数据），manifest记录公共handshake所需pid/start及progress attempt ID，避免把提交阶段误报formal已运行。

## 状态和可见性

公共supervisor已发起一次30秒启动握手。最终提交结果以同名artifacts的`submission_handshake.json`和run的`startup_handshake.json`为准。SOURCE_EVAL/SUBMITTED不等于formal首更新，不等于能力通过。

握手实际结果：worker PID876644，submitted=true、submission_verified=true、worker identity OK；run_state/current_stage为SOURCE_EVAL/source_eval，formal_first_update_verified=false、started=false（指formal尚未核验）。后台自行执行后续阶段；本worker结束交互，不读训练日志或等待整场训练。

TensorBoard复用`http://127.0.0.1:6006/`，新分组按实验名区分。reward raw/std、weighted density、dt contribution、bounded-tail比例及分命令controlled/hold/parking姿态/对称/接触等轻量统计随实际更新记录；历史缺失值不补造。

几何有界成本仍可能在严重形变时饱和，已经在快照及TensorBoard监测；本轮不同时修改其尾部。宽窄核不能保证快速收敛或解决所有姿态问题。

## 本轮源码改动

- `students/motion_tracking_reward.py`：显式v2 mixture，旧v1保留。
- `students/motion_refinement.py`：纯数据评估驱动状态更新。
- `students/motion_training.py`、`training_recipe.py`：显式reward版本声明校验。
- `students/motion_runtime.py`：同命令来源的实际mixture接线。
- `students/motion_reward_audit.py`：实际混合曲线及CPU状态导数。
- `students/motion_runner.py`：schedule接线修正、metadata、refinement日志/checkpoint。
- `scripts/prepare_motion31_training.py`：显式refinement选项及包含smoke的预算。
- `tests/test_motion_refinement.py`：独立回归。
- AGENTS/TOOL_INDEX/STATUS及本文：新声明边界和证据导航。未提交Git。
