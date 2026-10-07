# update50 完整更新诊断准备

本轮只完成代码、CPU测试和plan-only：没有AppLauncher、Isaac、物理采样、在线PPO或离线optimizer step；没有改旧run/checkpoint/raw evaluation/历史账本。

## 冻结身份

诊断checkpoint为`runs/motion_recipe_20261004_formal_20261004/formal_run/model_update_50.pt`，SHA `af990e413b636b218b4fe35eae2a8a0b32c2c985975b0707dc8d9cbda6b3e4a8`。参数名称/shape、17个optimizer state、Adam step=8800、LR=3e-5、actor/critic参数不共享均已CPU校验。历史spec/asset和formal source snapshot均作为只读身份引用。实际执行代码位于`isolated/motion_recipe_20261004/src`，最新诊断spec的源码/dependency SHA清单在`configs/experiments/motion_recipe_u50_capture_20261004/spec.json`。

历史配方与新增诊断差异明确：物理reward、command、PPO和控制契约保持历史值；新增仅为观测/奖励/终止/状态边界记录、独立GAE、身份校验和诊断监督。`train.py`/ledger/monitor/evaluator存在前轮可追溯修复，因此在spec中标记与历史快照不同；关键物理模块逐项SHA相同。

## 采集计划（待授权）

使用诊断模型自身 actor/critic/optimizer，更新前保存完整模型、Adam、RNG和参数映射；采集期间禁止`optimizer.step`。GPU1只读检查后，通过真实 `native_stand.command_v6.launcher -> monitor -> capture_degraded.py` 链运行，64 env、128步一块、连续8块共1024 policy steps/65,536 samples；块间不reset，不人为终止，覆盖9秒episode边界。内部截止240s，外部timeout260s、kill grace30s，总墙钟上限300s。若只完成部分块写入`incomplete_rollout.pt`并标明不完整，不降低规模、不重试。

每块保存所有64 env：obs/history、command与下一command、episode/step、raw/clip action、腿/轮目标、requested/clipped/applied torque、逐通道饱和、reward raw/weighted/weight/dt/terminal、storage reward、done/terminated/timeout/terminal causes、post-physics状态、pre-reset obs/value、returned obs、old value/logprob/distribution、last obs/value、raw/normalized advantage、returns、RNG和依赖身份。动作、clip和力矩饱和分开记录；力矩为policy-end快照，不冒充每个1ms physics子步。

新reset分布不是历史update51或50→100轨迹的重现。没有真实timeout/termination时分别写`timeout_physically_covered=false`、`true_termination_physically_covered=false`；CPU fixture覆盖逻辑不等于物理验证。

## 独立GAE与重放

`domain/diagnostic_gae.py` 使用独立double precision递推，显式比较：raw→weighted→dt→terminal→storage、安装版timeout使用的`V(obs_t)`、实际pre-reset value反事实、return/raw/normalized advantage、partial reset和rollout末端。不能从return反推reward。

采集后仅分析最后完整块：先核对reward、storage、GAE、生命周期和command/action对齐；误差超限立即停止。`replay_degraded.py --replay`最多固定seed `[81023,81024,81025]`各一次完整4 epoch×4 minibatch更新，保存shuffle索引、每step ratio/KL/clip、逐命令surrogate、优势加权贡献、梯度(clip前/后)、参数变化、动作/物理目标和一致性误差。实际实现和参考实现必须同数据/模型/自身update50 optimizer；重放只产生JSON，不导出候选模型，也不代表历史GPU shuffle或物理能力。

## 验证

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q \
  isolated/motion_recipe_20261004/test_degraded_cpu.py \
  isolated/motion_recipe_20261004/test_recipe_cpu.py \
  isolated/motion_recipe_20261004/test_evidence_cpu.py
```

结果：**36 passed**。覆盖人工GAE、timeout/真实终止/截断、部分env边界、安装PPO timeout语义、reward dt一次、raw/clip/torque区分、capture hooks、checkpoint Adam归属、minibatch全字段对齐、参考loss梯度、准备失败/重复路径/身份SHA和无重复结算。

plan-only入口：

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python \
  /home/kellen/wheel_leg_native_train/isolated/motion_recipe_20261004/capture_degraded.py \
  --spec /home/kellen/wheel_leg_native_train/configs/experiments/motion_recipe_u50_capture_20261004/spec.json \
  --output-dir /home/kellen/wheel_leg_native_train/runs/motion_recipe_u50_capture_20261004
```

实际结果为`READY_NEEDS_AUTH`，显示GPU/采集规模/字段/schema/源码与依赖SHA，`simulation=0`、`online_ppo=0`、`offline_optimizer_steps=0`、`files_written=0`；输出目录不存在，UNAUTHORIZED账本使用量为0。该命令未导入Isaac。

待用户审核的物理命令（**未授权，不执行**）：

```bash
CUDA_VISIBLE_DEVICES=1 PYTHONPATH=/home/kellen/wheel_leg_native_train/isolated/motion_recipe_20261004/src \
/home/kellen/anaconda3/envs/issaclab/bin/python \
  /home/kellen/wheel_leg_native_train/isolated/motion_recipe_20261004/capture_degraded.py \
  --spec /home/kellen/wheel_leg_native_train/configs/experiments/motion_recipe_u50_capture_20261004/spec.json \
  --output-dir /home/kellen/wheel_leg_native_train/runs/motion_recipe_u50_capture_20261004 --run
```

执行前需授权该独立账本、确认GPU1和Recovery只读资源；launcher会拒绝非GPU1，拒绝非空/身份不一致路径，monitor负责硬超时和exact-attempt结算。正式采集前不执行`--replay`；采集未完整完成时不运行重放。

本轮不能回答历史update51/50→100的真实GAE、后期每个transition的reward或物理轨迹，也不能把新采集重放动作变化解释为物理漂移。它只能区分：记录/GAE/对齐错误，或在同一冻结批次上整体surrogate改善伴随某些命令组恶化。等待一次有界PPO0采集授权。
