# update700零速＋49D Critic组合实验v13

用户明确授权组合方案1000轮，沿本任务GPU0共享安排。目标为0.34m零速站立、减少持续后退与后翻，同时保留姿态、实际关节镜像、轮心对齐、接触及限矩。组合实验不分离两项改动的因果贡献。

## 来源与恢复

来源`runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_700.pt`，SHA256 `73a7a09e713afcb5e96fbc74b0f0527d9bff4d4a439deec105d2bcee3696c2c0`。
继承31D Actor128/64/32和固定std，实际权重一致已CPU验证。新49D Critic256/128/64、新Adam、新seed，不声称恢复旧40D Critic/Adam或缺失的training_rng。物理环境重新reset。smoke/formal各自从同一来源初始化，不继承smoke末尾。LR3e-5/std腿.05rad轮2rad/s/PPO与归一化保持，BC0，动作/PD/限矩/USD不变。

## 两项改动与信号语义

纵向Huber速度尺度由.5变.1m/s，权重仍-.5/秒，dt=.01一次；其他高度/姿态/支撑/镜像/轮差/努力/动作变化和横向/yaw成本不改，无隐藏制动控制。
接口仍multiskill_mcu_v2，Actor固定31D，Critic子版本standing_privileged49_v1固定49D，旧默认40D不变。增加world root vz1、实际applied torque6按40/5.5Nm归一化、左右滚动速度模长残差2：abs(qdot)*.06-abs(native vx)。.06m为冻结spec轮半径；该残差是模长proxy，不是有符号接触点滑移率，不假设轮轴正负极性。Critic不进入部署Actor。

## 预算和证据

spec `configs/experiments/2026_10_13-22_14__standing034_zero_privileged49_v13/spec.json`，同目录独立budget.json；run `runs/2026_10_13-22_14__standing034_zero_privileged49_v13/`。
smoke12＋formal988＝1000实际更新，含每阶段5次Critic warmup，最大8192000samples。新额度不借旧余额、不自动追加或重试。沿原任务smoke/formal无墙钟截止，source900秒保护、4GiB产物上限，当前空间约11GiB，reserve通过。
formal每100及988评估三组normal各8环境；最终三seed复核，两个相隔100更新完整24/24才accepted。原高度/姿态/接触/闭链/触限/镜像/轮差门槛保持；vx原.5m/s门槛不放宽，另报告趋零表现，不认证精细定点。目前没有通过模型。
原v12跑完988更新后final assessment KeyError(student_native)已修：只加入声明的Swing案例，未评Swing为null。旧FAILED及旧冻结代码不变。

## 验证和修改

公共validate_cpu 20passed，schema/零写plan PASS，无源码或测试复制，证据`artifacts/standing_zero_privileged49_v13_20261013/cpu/`。真实runtime/factory/梯度/单位/Actor权重继承及实际reward分派已验证。
广泛PORTABLE最初4failed/288passed/8skip；两项本次optional属性兼容问题已修并定向回归，其余既有快照复制fixture及corrected目录行为失败保持，未放宽、未声称全量通过。
check-submission READY，物理GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72/逻辑cuda0，共享不抢占。当前终态通知负责人191bacc3-e5c7-4b8f-ae3d-5677eada837b。

新增students/standing_zero_privileged.py、scripts/prepare_standing_zero_privileged49.py、tests/test_standing_zero_privileged49.py。修改students/standing_alignment.py、recovery_task.py、training_recipe.py、model.py、ppo.py、runtime.py、evaluator.py、requests.py、training.py及command_v6/tools/model_factory.py、register_authorization.py；终态修复另覆盖tests/test_standing_alignment034.py。更新AGENTS/TOOL_INDEX/STATUS及本记录，不提交Git。
后台既有owner管理预算/保存/评估/结算/报告/最多一次通知。一次握手后结束交互，不轮询；source/smoke提交不等于formal首更新或能力通过。

实际首次提交成功：worker3820246，单次30秒握手SOURCE_EVAL，submitted/submission_verified=true；formal首更新未核验。receipt在`artifacts/standing_zero_privileged49_v13_20261013/launch_receipt.json`。没有人工等待整场训练或轮询进度。
