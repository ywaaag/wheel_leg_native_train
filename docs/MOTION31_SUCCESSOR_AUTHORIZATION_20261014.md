# Motion31：当前训练终态后的新授权

本记录依据用户本轮明确授权，不由旧预算余额、smoke 或终态通知推导授权。

## 执行触发

当前父链为 `runs/2026_10_14-21_23__motion31_posture_quality512_v3`。继续原冻结配置，不提前停止、不热改代码/spec/ledger。

新授权机器记录：`artifacts/2026_10_14-23_59__motion31_successor_authorization/authorization.json`。owner 为 `191bacc3-e5c7-4b8f-ae3d-5677eada837b`。已核验父 manifest 的 owner/target、notifications.enabled 与 spec SHA；核验时 report_ready 尚不存在。

复用既有 monitor 的终态通知唤醒本会话，不新建 watcher、不轮询或睡眠守候。本次用户独立授权允许以下一次后续实验，无需再次确认。收到父链事件时须读取本记录。用户随后要求删去通知中的禁止续训措辞：公共通知与订阅通知均改为“请读取报告复盘，并按当前有效用户授权处理后续工作”。已运行进程若缓存旧代码，仍可能发送旧文案；不为更新文案重启训练或通知进程，旧措辞不撤销本次授权。

## 终态选模

比较父链原始来源与完整五命令评估的 formal checkpoint；核验 checkpoint SHA、同协议、逐命令8环境及真实窗口。不能拼模型或选择未完整评估的 latest。

先要求完整且物理安全的有效评估，再依次排序：

1. 非零命令同时满足 tracking、direction、gain、sustained fraction 的环境数。
2. 非零命令方向正确的环境数。
3. 非零命令最差环境 MAE 越小越优。
4. 零命令水平速度 p95、保持段 pitch/roll、轮心/腿长不对称。

完整 accepted、停车通过、零容差来源姿态 guard 不作为进入学习的先决条件。保留原 gate 的所有真实失败；“最佳可训练起点”不等于能力通过。若证据不足或存在未解决 runtime fault，先修复/补齐。update300只是中途候选，不能提前冻结为最终来源。

## 下一次配方

- 仍为512 env、0/±0.5/±1 m/s，槽位128/96/96/96/96；不升速、不加入 yaw。
- 保留独立 zero cohort。非零训练准备0.5秒、加速1秒、保持28.5秒，取消末端回零与停车；30秒到时正常 truncation 和 bootstrap。
- 新显式 reward 版本拟将 upright 权重2→4、pitch/roll excess 各−0.5→−1；其他权重、核宽和质量终止阈值不变。启动前审查实际 reward 曲线、斜率、分项贡献与饱和，不预称快速收敛。
- 原完整评估流程保留用于同协议来源比较；停车结果单列，不作为下一版持续跟踪阶段的晋级条件。采用新评分身份，不修改旧评分结论。
- 从选中完整 checkpoint 恢复 Actor/Critic/Adam/std/RNG，明确 reward 改变后的 critic 适应安排，不静默重置；新物理 reset。
- Actor31/Critic49、PPO/LR/std/归一化、动作尺度、PD、物理、资产不变。
- 本次同时改变时相和水平姿态权重，结果不能单独归因于其中一个。

## 预算与操作

新授权2000次更新，保守记为新增 online PPO 总上限：smoke≤5、formal≤1995，失败尝试也计入。新链安全上限18小时、2GiB，先到即停，不自动重试、不再次花父链余额、不自动启动第三条链。

父链结算与逐 gate 复盘→选模/SHA→新时间戳 spec/独立 ledger→新版本 CPU 实现与回归→零写 plan→实际 reward_snapshot→smoke→public supervisor detached 提交→一次握手→结束交互。既有 monitor 管评估、预算、结算和当前 owner 通知。

现有512 validator固定原始来源，continuation要求reward不变；新来源/时相/reward须通过显式新声明接入，补恢复、时相与评分CPU测试，不能绕过校验。在父链结束后执行共享源码接线，避免影响活动训练。

下一轮重点诊断 gain 是否转正、逐 cohort reward/advantage、质量终止率、零速漂移与几何；缺真实 rollout/optimizer capture 时，PPO因果方向仍标 UNKNOWN。

本次仅登记授权和执行规则，没有新仿真/PPO/通知或Git提交。最终来源、新spec、账本及启动身份待终态后实际生成。

## 2026-10-15执行追加

父事件e838ff5a0c7be39497a902d7已到达，按本授权已完成终态复盘和选模，选1600 SHA83ee2371…9a820；新v4声明经CPU/登记授权/零写plan后public提交，来源评估阶段握手确认worker325129；formal尚未核验。详见 `docs/MOTION31_QUALITY_V3_TERMINAL_AND_V4_20261015.md` 和STATUS。此授权已用于该一次新链，不可再次凭同一授权启动另一链；单次claim已创建。
