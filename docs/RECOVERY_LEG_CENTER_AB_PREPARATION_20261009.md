# Recovery 腿中心 A/B 接线与准备 — 2026-10-09

当前状态：CPU工程准备完成，两臂UNAUTHORIZED、ledger使用量全零、无attempt；未启动仿真、GUI或PPO。配置通过不等于submit_ready。

## 配方及身份

两臂同源：`runs/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25/formal/model_update_25.pt`，SHA `34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c`。这是保住DrawBack/R0的实验new25，不是已通过的原始B25，更不是Motion B250。严格保留actor/critic/Adam及实际std，不修改USD、实体控制、奖励、动作尺度或终止条件。

- A：`configs/experiments/2026_10_9-15_10__recovery_leg_center_a_from_new25/spec.json`，来源配方继续学习，不启用腿中心loss。
- B：`configs/experiments/2026_10_9-15_10__recovery_leg_center_b_from_new25/spec.json`，唯一增加`leg_center_auxiliary`，lambda=.1、band=.15rad。

仅合法Swing受控pre-clock [0,.1)秒、尚未入口的样本参与；step后用真实failure/fault读回剔除失败样本，不使用reset后状态判别。四腿mean目标偏差为`e=1.6*mean_leg-frame[9:13]/2`，loss为四通道`relu(abs(e)-.15)^2`平均，再按全部受控rollout transition数归一。每个optimizer step复用当前rollout全部eligible输入，顺序是PPO裁剪→辅助梯度→actor重新裁剪；critic仅PPO。该项为训练辅助loss，不是reward，不规定收腿符号、不覆盖runtime动作、不注入手写时序。

默认关闭。仅声明B的smoke/formal阶段安装hook；source_eval、独立评估和播放不应用辅助梯度。记录eligible_count、分母、loss、梯度norm和应用次数；smoke wiring要求真实eligible事件及非零辅助梯度，CPU不能替代该证书。

## 预算与选模

每臂独立source_eval 1次≤900秒，smoke≤10更新/900秒，formal≤25更新/3600秒；formal10/25完整三组评估。每臂35更新286720样本，整链≤5460秒；两臂合计70更新573440样本、阶段墙钟10800秒、含清理整链10920秒（182分钟上限，不是预计耗时）。顺序共享物理GPU0（UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，逻辑cuda0），不停止其他任务，不自动切GPU。

两臂都保留Swing/DrawBack/R0固定26/25/13配额及原评分协议。比较起身入口、双侧收腿/接触、完整保持与倾角，保留来源及早期候选；不能因loss下降接受B，不能拼不同checkpoint成功点。辅助loss可能压制必要摆腿、与PPO冲突；mask外直接loss为零不保证共享actor旧能力不变。

## 验证与限制

两臂多文件发布标记及SHA核验通过；预算未授权无消耗，严格初始化参数和Adam一致，实际std未改。新辅助及既有mean辅助/纯候选共9项PORTABLE CPU测试通过；两臂各自冻结CPU验证9项通过。

完整CPU回归720通过、22项ERROR、2 warnings。22项均为Motion工程恢复证书fixture拒绝当前`command_v6/runtime/configure.py`历史SHA变化；本轮未修改该文件，不绕过保护、不重写历史证书。因此不能称全仓库回归通过。

真实runtime mask、实际PPO更新后行为和smoke wiring尚未认证，无新checkpoint。下一步需明确批准上述两臂训练预算，提交前再核验session、GPU共享、身份、输出、ledger和证书，仅经supervisor提交；失败不自动重试或追加。授权模板位于`isolated/recovery_leg_center_ab_ready_20261009/approval_request.json`，模板不是授权。

## 本轮文件

新增`src/native_stand/recovery/leg_center_auxiliary.py`、`scripts/prepare_recovery_leg_center_ab.py`、`tests/test_recovery_leg_center_auxiliary.py`及本报告；修改`recovery/mean_auxiliary.py`、`recovery/validation.py`、`command_v6/domain/recovery_course.py`、`tools/prepare_recovery_course.py`、`train.py`、`wiring.py`。声明为上述两个config目录，CPU证据位于`artifacts/recovery_leg_center_{a,b}_cpu_20261009/`与`isolated/recovery_leg_center_ab_ready_20261009/`。同步STATUS、计划、TOOL_INDEX与ARCHITECTURE；保留其他dirty changes，旧run/资产/checkpoint未修改。
