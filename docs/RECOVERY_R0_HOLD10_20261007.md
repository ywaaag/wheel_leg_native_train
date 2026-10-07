# R0持续保持实验

2026-10-07：当前用户同意并要求执行Recovery持续保持方案。
新spec：`configs/experiments/recovery_r0_hold10_from50_20261007/spec.json`。
独立账本：同目录`budget.json`；新run：`runs/recovery_r0_hold10_from50_20261007`。
不使用或重启旧链额度，不覆盖旧模型/评估/账本，不扩展R1。

## 问题与冻结变量

检验取消2s成功reset和+10成功事件后，PPO是否能保持source50的R0长期水平能力。
这是episode/事件reward的联合修正，不是单因素因果归因。
来源为`runs/standing_scissor_20261006/formal/model_update_50.pt`，
SHA256 `1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71`。
USD SHA256 `32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7`。
R0原pose数据按原样复制且SHA不变。150D输入、six actual-joint targets、
1ms/5ms/10ms、40/5.5Nm、1.6rad/100rad/s、plane/PD和所有连续reward不变。
strict加载source50 actor/critic/Adam，LR3e-5，无critic warmup；BC coefficient.02、
all channels、前256个eligible输入选取方式不变。

## Episode与评分

仅显式`standing_task.training_episode.mode=fixed_horizon`启用新路径；历史spec语义不变。
训练持续1000个policy steps=10s，不因2s成功提前结束，不进入STAND/teacher控制。
普通跌倒/fault仍终止；正常10s结束为time limit，即使窗口gate未通过也不是吸收失败，
不产生failure_once。success_once=0。失败事件-1仅用于真实任务失败/fault。
wrapper维持is_finite_horizon=false；安装的PPO使用gamma乘transition.values进行
timeout bootstrap，沿用其已测试实现，不宣称已实现terminal-next-state value修正。

GPU流式计数、均值、峰值统计与独立survival_level_v1评分器一致：
2–10s高度均值.34–.38、范围比例>=.9、双轮>2N比例>=.95、
mean abs pitch/roll各<=.10；全episode峰值各<=.15、tilt<=.18、
closure<=.005、policy采样饱和<=.05。窗口通过只在10s结束记录，
用于episode/curriculum统计；stage cap0阻止晋级。正常超时、未通过窗口、
真实失败和fault分别记录。Independent evaluation持续首个物理episode，禁用训练time limit。

## 预算与流程

source10s/PPO0/300s -> smoke10updates/450s -> formal最多100updates/2400s。
64env x128steps；总PPO<=110，samples<=901120，阶段墙钟和cleanup合计上限3300s。
smoke10覆盖12.8s，能够观察至少一次正常10s结束；最后light评价只证明接线。
formal从source50重新初始化，不从smoke10接续；source与smoke都有独立attempt。
formal完整10s评估25/50/100；checkpoint每25，未通过的latest不替代source。
连续两次完整评估退化可有界早停，无自动续训/下一轮。
本次不运行最终100s durability；它没有额外授权额度。

选定更新1/8/25/50/100开启reward事件、duration、storage value/return/advantage、
KL/ratio、actual optimizer gradients和BC/PPO诊断；其余更新保持关闭。
diagnostics不改训练目标、采样或optimizer。

## CPU验证与启动

新增窗口与独立评分一致性、局部reset、failure/fault覆盖deadline和新spec/预算测试。
全量CPU结果、plan-only和实际状态以STATUS及run manifest/progress/terminal为准。
新启动必须使用公共supervisor、当前HAPI session和明确physical GPU0；
它冻结共享代码、source/spec/asset SHA，验证source与smoke certificate再进入formal。
GPU检查保留其他simulation/未知compute进程的占用保护；已核实的
`/usr/NX/bin/nxnode.bin`桌面服务不是独占simulation owner，不为此停止桌面。
smoke certificate还要求metrics实际记录正常10s timeout和完整10s训练episode。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src CUDA_VISIBLE_DEVICES=0 \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.supervisor \
  --spec configs/experiments/recovery_r0_hold10_from50_20261007/spec.json \
  --output-dir runs/recovery_r0_hold10_from50_20261007 \
  --physical-gpu 0 --hapi-session 7bbabd67-183d-4185-b686-1aefcd55781b --launch
```

此命令只适用于本次一次性授权；已有submission/run时不得再次运行。

## 本次改动文件

- `src/native_stand/recovery/holding.py`：纯Torch完整episode计数/评分。
- `src/native_stand/recovery/runtime.py`：显式opt-in horizon、局部reset、timeout与窗口统计。
- `src/native_stand/recovery/validation.py`：新配方边界校验，旧配方保留。
- `src/native_stand/command_v6/train.py`：正常timeout计数及事件语义描述。
- `src/native_stand/command_v6/wiring.py`：smoke必须有真实正常10s结束证据。
- `src/native_stand/command_v6/tools/health_check.py`：整体最佳允许来源；NoMachine桌面不算独占仿真任务。
- `scripts/prepare_recovery_hold.py`、`tests/test_recovery_holding.py`：准备工具和CPU回归。
- `configs/experiments/recovery_r0_hold10_from50_20261007/{spec.json,poses.json,budget.json}`：新声明和本地独立账本。
- `README.md`、`STATUS.md`、`ARCHITECTURE.md`、`TOOL_INDEX.md`及本文：入口/契约记录。

提交前最近全量CPU回归351 passed，13项holding检查通过，plan-only PASS、health OK。
用户随后明确允许共享GPU0，禁止随意停止其他进程；本次没有停止其他进程。
实际source/smoke/formal完成与否以新run的terminal/progress/certificate为准。

## 启动实证

source10s完成71.23455s，8/8 accepted、runtime_fault0。
smoke10完成136.21032s/81920samples，certificate PASSED/errors[]。
smoke update8：64个episode mean/max duration均10.0s，正常timeout64，
physical failure0，window_failed_timeouts64。随机训练窗口失败与确定性独立
验收不是同一个分布；不能把它们混同成跌倒或声称smoke通过能力验收。
selected diagnostics实际包含critic value/return/advantage、optimizer梯度和BC/PPO数据。

formal单次握手：RUNNING/actual_updates1、identity_verified=true/started=true；
attempt `43e96c5cc5d846779640bbc3edefd3c2`，trainer3168977，worker3164611。
运行源码冻结于run/source_snapshot，不受后续共享代码修改影响。
formal上限100及25/50/100全评估由后台owner完成。这里未宣称训练完成或能力改善。
