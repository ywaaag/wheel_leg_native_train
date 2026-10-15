# Motion31宽窄核链：smoke接口错误复盘

终态事件`52e44d2dead8055a168c1d48`，run为`runs/2026_10_14-19_04__motion31_wide_narrow512_2000`。原始终态FAILED保持不变；本轮没有仿真、重试、续训、预算追加或Git提交。

## 已确认实现错误

`students/motion_runner.py`先把来源Actor权重存入局部变量`initial`，再在v2分支导入`motion_refinement.initial`。Python局部名称被函数覆盖，首次真实PPO update和metrics落盘之后，进度中的`initial.items()`抛出`AttributeError: 'function' object has no attribute 'items'`。

这是本worker新增精修接线造成的工程错误，不是生存gate拒绝训练，不是奖励不收敛、GPU故障或机器人跌倒。先前CPU回归覆盖了奖励和精修纯函数，遗漏了runner初始化到进度汇总的组合路径。

已最小修复：来源权重改名`source_actor_weights`，精修导入别名`initial_refinement`；新增直接执行真实runner AST初始化/变化检测表达式的CPU回归，覆盖同名覆盖问题，不启动Isaac。

另一处计数缺口：progress更新晚于可失败的诊断。现将实际更新、samples和有效Actor样本立即记入内存progress，并在真实optimizer完成后、诊断序列化前扣账。后续诊断异常仍可由finally保存真实次数与最新checkpoint。新增异常后的计数回归。旧报告、账本和checkpoint不补写。

## 实际消耗与证据冲突

- 来源五命令完整完成，40/40连续30秒存活，0/40Motion验收通过。
- 账本smoke=1、formal=0；metrics唯一记录update1、65,536条样本。
- 此次为critic warmup：critic changed=true、16个critic optimizer minibatch；actor changed=false、actor optimizer steps=0。因此没有学出新Actor，也没有新能力改善证据。
- 阶段terminal/progress错误记录actual_updates=0，原因是更新后的进度诊断异常；链报告采用账本显示1，符合真实optimizer和metrics证据。
- 没有smoke通过证书和smoke checkpoint，formal NOT_RUN，精修切换未执行。
- 全链897.4447秒，约14.96分钟。source_eval账本wall874.4013秒，失败smoke账本wall=null；实际失败阶段terminal cleanup前17.8206秒。恢复预算应采用完整链897.4447秒，不能把null计成无消耗。
- 原授权在线2000的未用余额1999，**余额不授权续训**；旧失败尝试只读保留。

## 同协议来源结果

| 命令m/s | 保持vx均值 | 保持MAE | 生存 | Motion通过 | 主要失败gate |
|---|---:|---:|---:|---:|---|
| 0 | +0.34756 | 0.34756 | 8/8 | 0/8 | parking、zero_horizontal |
| +0.5 | +0.22731 | 0.27269 | 8/8 | 0/8 | parking、gain、sustained_fraction |
| -0.5 | +0.53662 | 1.03662 | 8/8 | 0/8 | parking、tracking、direction、gain、sustained_fraction |
| +1 | +0.12749 | 0.87251 | 8/8 | 0/8 | parking、tracking、gain、sustained_fraction |
| -1 | +0.78551 | 1.78551 | 8/8 | 0/8 | parking、tracking、direction、gain、sustained_fraction |

五个raw JSON均核对checkpoint SHA和冻结protocol，trace逐文件SHA核验通过；详细逐环境数据和输入SHA：`artifacts/2026_10_14-19_25__motion_refinement_failure_review/review.json`。来源仍是原始迁移Actor `a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`，并非新训练候选。

## 下一步唯一优先行动

CPU修复完成后，若用户重新明确授权运行，优先新建受限工程恢复声明，继承真实已耗1次和897.4447秒、严格复用这次完整来源证据；剩余在线最多1999。重新验证未通过的smoke，不跳过wiring、不从不存在的checkpoint续、不重复完整来源物理评估。现有恢复准备器只处理“完整smoke已通过、formal存储preflight失败”，不适用于本次；需先扩展明确的partial-smoke故障类型和CPU验证，不能直接借旧证书进入formal。

本轮未执行该恢复。新修复尚缺真实smoke物理验证；奖励有效性、快速收敛及站立/Motion能力均UNKNOWN。

## 修改与验证

修改`src/native_stand/students/motion_runner.py`、`tests/test_motion_refinement.py`、`STATUS.md`及本文。定向CPU58 passed，motion_runner静态compile通过；`scripts/test_portable_cpu.py`全PORTABLE425 passed、8 skipped。未改变reward/PPO/物理/来源、历史run/spec/ledger/evaluation。
