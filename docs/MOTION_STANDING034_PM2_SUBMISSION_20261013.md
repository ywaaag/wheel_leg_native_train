# Motion0.34m/±2m/s并行长训提交

本轮用户明确要求旧Motion与Recovery并行，站立及前后2m/s，当前新高度命令0.34m，累计训练不限量。两条链均已public supervisor提交，握手仅确认SOURCE_EVAL与owner身份，**没有声称formal首更新或新能力通过**。

| 任务 | 当前声明 | 启动握手 | 有限子块 | 无限父任务 |
|---|---|---|---|---|
| Motion | 2026_10_13-00_16__motion_standing034_pm2_block0000 | SOURCE_EVAL | smoke25＋formal300，4h，2GiB | 累计上限null，owner正常自动续接 |
| Recovery | 2026_10_13-00_20__recovery_standing034_smoke_fix_block0001 | SOURCE_EVAL | smoke12＋formal300，4h，2GiB | 原normal0.34m/对称专项，累计账本继承 |

## 来源与边界

Motion为原B250 `runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`，SHA `5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`，自己的frozen spec作谱系。原模型训练命令0.40m；新目标0.34m不是历史通过的迁移认证。

Actor/Critic legacy150D、256/128/64、Gaussian原std/完整Adam/RNG继承；动作腿.5rad/轮100rad/s，原USD/Plane/1/5/10ms/40与5.5Nm。训练0/+2/-2固定槽位26/19/19；实际transition比例由原metrics记录，不把槽位当样本比例。source、smoke和formal分别从声明来源开始，formal不继承smoke末模型。奖励使用B250实际执行的combined公式，保留upright2、height2、velocity8、contact.5和努力/变化/关节余量/终止成本；只将高度命令切为.34、采样切为三个目标。原spec里无效split/per-command描述已由effective recipe披露并迁移，未伪称历史按新配方训练。

Motion评分明确新gate_identity=motion_standing034_v1，均高.32–.36、90%保持样本在带内、每个保持样本≥.30；固定10–20秒保持、30秒全流程。旧Motion其余v3门槛保留：速度误差≤.3、方向≥.95、zero mean(abs(vx))≤.5、vy≤.02、tilt峰值≤.5、contact≥.95、policy采样触限≤.5、闭链≤5mm。这不是Recovery更严格的连续接触/姿态/触限证书。停车和位移仍有诊断，不冒称精确定点或高速/yaw通过。

## 启动故障与修复

Motion v1 `2026_10_13-00_02__motion_standing034_pm2_block0000`在初始化后因新增停止检查局部STOP触发UnboundLocalError；PPO0，6.9365537秒。v2增加正确模块级声明，真实train.main＋Ledger＋finally的CPU注入异常测试确认原异常和终态保存，不只有源码字符串测试。旧FAILED、spec、budget、冻结代码不改，旧任务账本曾被wrapper错写RUNNING已纠正为owner实际ENGINEERING_STOP；新账本通过previous_attempt_accounting保留原SHA、总量与耗时。

Recovery旧23_25 run完成12次smoke更新后错误将8环境结果用于formal24汇总，formal0，249.1886065秒/98304samples/57344有效Actor。修复仅让smoke记录行为，formal仍要求24；新task继承旧12实际更新与所有块、SHA、耗时，从原v7来源重新执行独立smoke/formal，不把失败smoke作为formal来源，不改奖励与验收。

## 验证

Motion专项99通过；正确PORTABLE冻结16通过，公共planner/授权/实际冻结身份通过。Root迁移的旧测试错误文案在共享根与真正source_snapshot根有两种正确拒绝，测试明确接纳这两种identity错误，SHA检查不变。另一次误包含PROJECT_DATA测试的冻结调用正确拒绝了不匹配的旧spec收据，已记录，最终只选PORTABLE。Recovery专项35、正确冻结48通过。全量943passed/8skipped/22errors；22个Motion旧工程证书fixture逐ID与修复前相同，原因是旧runtime/configure SHA不匹配，没有拿它豁免新边界。

GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`、CUDA_VISIBLE_DEVICES=0、逻辑cuda:0，public shared显式授权；Recovery提交时资源读回已有Motion训练进程占2488MiB且未停止，仍余30117MiB。实际两run冻结与各CPU冻结逐模块及spec SHA一致，机器核验见 `manual_train/motion/verification/actual_submission_freeze_check.json`。两次已完成的有界握手之后没有个人log/PID/GPU轮询。

## 消耗与下一步

当前启动阶段实际新PPO次数未由握手核验，不能写成formal已开始。旧失败实际消耗单独保留；后续全由owner在各exact-ID子账本结算。source普通能力失败不阻断Motion学习，runtime/身份/证据故障停止；本轮不自动更改网络/PD/USD、不抢占其他任务。

Motion连续两次同协议三命令联合24/24后保留完整同一checkpoint；≥5000formal后若三块停滞，一次完整状态回退，再停滞则NEEDS_DESIGN。正常续接不需要追加更新额度，每块仍有墙钟和产物安全保护。Recovery normal专项通过只认证站立与对称，不能冒称Swing完整起身。两策略共同资产和未来接管仍待物理验证。

精确命令只维护TOOL_INDEX，状态只维护STATUS，结构只维护ARCHITECTURE。源文件范围：Motion全部位于manual_train/motion执行副本；共享仅students/standing.py与students/training.py的smoke统计修复，两个测试文件及任务文档。无commit/push，无旧模型或历史运行文件改写。
