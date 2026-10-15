# Motion31质量v3：跨命令reset接口失败

事件`e21a8232182c2abe395148ba`，run `runs/2026_10_14-21_14__motion31_posture_quality512_v3`，终态FAILED。用户只授权本次复盘，没有自动续训。本轮CPU修复不启动Isaac/PPO、不改旧run/spec/evaluation/ledger、不提交Git。

## 确认的错误

第一个zero来源评估完成后，复用同一环境开始第二命令，在eager `env.reset()`失败。错误为`Inplace update to inference tensor outside InferenceMode is not allowed`，定位`QualityTermination.reset()`写`self.ticks[ids]=0`。

本worker此前新增`observe()`用`self.ticks=torch.where(...)`替换持久buffer；observe在`torch.inference_mode()`内执行，替换后的tensor带inference属性，退出该上下文后普通reset不能原位写。不是物理故障、奖励不收敛或质量门槛过严，也不是上次free spec错误仍未修复。

最小修复为`self.ticks.copy_(torch.where(...))`，保持原先普通buffer身份。reward、计时公式/阈值、网络、PPO和物理均不变。新增CPU回归连续三次执行75步inference-mode observe、退出上下文再reset，检查buffer身份/inference属性、计时与sent清零和RNG不变。此前测试只覆盖相同普通模式，遗漏真实跨inference/eager生命周期；这里明确补齐。

## 实际覆盖与消耗

- 新smoke0、formal0，未产生新训练checkpoint；历史累计在线仍50次，不能宣称训练效果变差或变好。
- 本链301.676054955秒，累计含历史1973.228449821秒约32.89分钟；原18h余62826.771550179秒。原2000在线余额1950；本次冻结的smoke5+formal1900仍1905，不自动使用另45。余额不授权重启。
- 来源zero原始JSON及trace SHA核验通过，8/8连续30秒生存、0/8accepted；保持mean vx平均+0.3475629m/s，每环境均因parking、zero_horizontal失败。新几何/roll质量gate通过，没有质量终止原因。来源生存不等于Motion或静止站稳通过。
- +0.5状态INCOMPLETE（reset失败），−0.5/+1/−1 NOT_RUN，不拼接历史其他命令作为本轮完整评估。
- `source_eval`FAILED/exit1与链FAILED一致；原阶段报告和账本不修改。

输入SHA、逐环境指标、矩阵和预算审计：`artifacts/2026_10_14-21_22__motion_quality_inference_reset_review/review.json`。该报告为新输出，旧失败证据只读。

## 验证及下一步

定向：`python -m pytest -q tests/test_motion_quality.py tests/test_motion_smoke5.py tests/test_motion_refinement.py tests/test_motion31_training.py`，61 passed。
全PORTABLE：`python scripts/test_portable_cpu.py`，446 passed、8 skipped。解释器固定issaclab，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`。

下一步唯一优先是带跨命令reset修复的受限工程恢复，仍smoke5/formal1900，保留本次失败墙钟；需要新的明确运行授权。本轮不生成新授权、不拓展故障恢复白名单、不复用不完整来源作为完整矩阵。再次运行应先让来源完整五命令通过工程生命周期，再进入短smoke。能力与物理运行验证仍UNKNOWN，CPU通过不代表已在Isaac修复成功。

修改文件：`src/native_stand/students/motion_quality.py`、`tests/test_motion_quality.py`、`STATUS.md`、本文。没有更改reward/PPO/物理参数。

## 用户新授权后的重启（21:23新声明）

用户明确“允许重启训练”。新spec `configs/experiments/2026_10_14-21_23__motion31_posture_quality512_v3/spec.json`，run同名。来源仍原始Actor `a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266`；奖励、阈值、物理和PPO不变，不从不存在的新checkpoint恢复。

在线上限保持新smoke5＋formal1900=1905，历史50总计≤1955，未自动使用原总2000的45次余量。剩余墙钟62826.771550179秒，累计历史1973.228449821秒不重置。CPU PORTABLE447 passed、8 skipped；最终绑定checkpoint/Actor/std/Adam/LR核验通过，零写supervisor plan PASS；全链未压缩产物含reserve1,863,314,432bytes≤2GiB。

恢复校验只新增允许已结算、零新增PPO且错误栈精确指向`motion_quality.py`/`self.ticks[ids]=0`的inference reset故障；非有限、其他模块错误、有PPO消耗或未结算均拒绝。此为明确新授权下新声明准备，不自动retry，不改原FAILED。

本次增量修改`src/native_stand/students/motion_quality_budget.py`、`tests/test_motion_smoke5.py`、`STATUS.md`与本文；前述buffer修复保留。没有Git提交或变更奖励。实际reward快照和启动回执：`artifacts/2026_10_14-21_23__motion31_posture_quality512_v3/reward_snapshot_authorized.json`、`submission_handshake.json`；CPU在同目录`cpu/validation_result.json`。

public supervisor提交来源完整新矩阵→短smoke5→新证书→formal1900；后台owner通知当前session `191bacc3-e5c7-4b8f-ae3d-5677eada837b`。GPU0共享→CUDA0，512env，固定0/±0.5/±1，不抢占其他compute任务。一次30秒握手后worker退出，不轮询训练。来源/提交/接线不等于能力通过。

实际握手：worker37315、submitted/submission_verified=true，SOURCE_EVAL/source_eval，formal_first_update_verified=false、started=false（formal未核验）；TensorBoard一次HTTP200，新registration已写入。后台自行推进，不由worker等完整训练。
