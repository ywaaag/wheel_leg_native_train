# Recovery时相配对审核与100更新同配方检验：提交交付

2026-10-09用户同意先CPU配对审核，再在无明显回报排序问题时实施同配方100更新实验。CPU结果没有发现明显反向时相内关联，但相关性接近零且无真实成功收腿轨迹，不能证明奖励足够；按本轮授权提交更长块，检验“25次更新不足”，不暗改beta/std或接退化latest。

## CPU时相配对与敏感性

只读09_40真实冻结随机rollout NPZ：按受控Swing相同post-control recovery_clock（100Hz tick）中心化，比较recordbonus/连续同episode双侧平均收短与rawadvantage。同clock correlation分别+.03615、+.00515，接近零；不是按动作/状态严格配对的因果实验。不同env、重复episode与状态混杂仍存在；不能凭弱相关认定无reward问题。

固定trajectory、values、dones与原GAE下，beta0/.3/1/3/10的正bonus样本rawadvmean约−.51066/−.50742/−.49987/−.47830/−.40279；normalizedadv正比例约5.96%/5.96%/5.96%/6.45%/9.18%。提高beta到3/10把初Q=.235的episode额外预算升到2.295/7.65，可能显著改变失败路径偏好，不能因正adv比例较高就采用。beta=.3不变，未修改模型或reward配置。

新增`scripts/audit_recovery_phase_advantage.py`，输出`isolated/recovery_phase_advantage_audit_20261009/audit.json`绑定spec/evaluation/NPZ SHA；两项数学测试验证时相中心化消除时相间混淆、GAE贡献不跨terminal/rollout。该脚本依赖repo-local scripts，测试标PROJECT_DATA。

## 独立训练声明

- spec/budget/poses/preparation/publication/approval/authorization_receipt：`configs/experiments/2026_10_9-09_53__recovery_swing_support_record100_from_b25/`。
- 新run：`runs/2026_10_9-09_53__recovery_swing_support_record100_from_b25`，阶段source_eval/smoke/formal；来源认证RecoveryB25，SHA8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。
- smoke/formal各自严格加载同一B25 actor/critic/Adam及std，保留来源、早期、末尾候选；不从smoke末尾或本次旧new25接棒。
- 保留当前reward（beta=.3 record、original reward）、fixed26/25/13三family、新USD、150D、6D原控制、限矩和v2完整10秒验收；meanaux/std干预关闭。
- smoke10/formal≤100，合计110更新/901120samples；source≤900秒、smoke≤900秒、formal≤7200秒、链≤9060秒含60秒收尾。是151分钟最大预算，不是预计必用完；不授权自动延长/重试。
- 完整联合检查点恰为10/25/50/100（已逐update核验schedule）；普通checkpoint25/50/75/100及10评估前保存，失败不抹去早期候选。未授权100秒耐久。
- 原smoke真实episode/group事件与正recordreward证书要求保留；缺wiring阻断formal。source独立新评估，不借旧证书绕过；旧两组连续两次完整失败停止该分支。
- sharedphysicalGPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72→cuda0；effective CLI共享声明与UUID核验，不停止其他任务、不自动换卡。
- notifications enabled=true，负责人session7bbabd67-183d-4185-b686-1aefcd55781b，at-most-once自动终态通知；通知不授权后续。

## 验证与一次握手

全CPU685 passed（25.93秒），最终冻结PORTABLE14 passed、schema/零写plan/来源完整初始化通过：`artifacts/recovery_support_record100_frozen_cpu_20261009/validation_result.json`。public supervisor check-submission READY、配置PASS、当前session/output/资源/存储/账本核验。

一次5秒握手submitted=true、submission_verified=true，worker991072、链attempt6cbc736ffa0042699d5f755adc827e7d，SOURCE_EVAL；formal_first_update_verified=false。不能声称正式PPO已更新；后续不轮询、不新建watcher。回执声明目录chain_submission.json。

## 终态判断与限制

首先比较Swing双侧收短、height入口/完整保持、tilt/contact及DrawBack/R0完整能力；geometry/总reward/限幅率不独立决定接受。100更新块旨在检验时间不足这一假说，没有事先宣称可收敛。若无净收益，保留B25并复盘，不能再自动延长或同时改多个因素。动作clip严重、critic record未显式输入150D、新reward对已有trajectory影响小等风险保持公开。

## 本轮文件变更

新增`scripts/audit_recovery_phase_advantage.py`、`tests/test_recovery_phase_advantage.py`；修改`scripts/prepare_recovery_support_record.py`允许显式25/100块并继续复用公共course发布器，没有新trainer/控制层。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX与本报告。独立新声明/CPU审计/冻结验证/run为本轮产物；旧run/ledger/raw/checkpoint和其他dirty changes保留，未删除文件、未Git commit/push。
