# 低位几何目标奖励：完整回报CPU核算

本轮用户同意执行目标型几何项的早死/冲高门控/必要转姿与量级审核。未模拟/PPO/optimizer，未改历史reward/checkpoint/run/ledger，没有准备可提交runtime声明。

## 实际轨迹反事实

使用身份核验的17_39冻结B25三组8env输入采集，具名geometry/state schema及实际rewardTotal（含once事件）。收腿尺度.15/.375米、height smoothgate.22/.30米、成本中收腿/方向各.5；只有Swing初始化完成且first-entry之前eligible。两个旧组新增项严格0。反事实与原runtime reward分开，不冒称新训练结果。

负成本−.3/秒*g*C*dt：Swing每env累计约−.06168（约为原连续lift+upright等累计+.3367的18.3%，并非仅lift比值）；DrawBack/R0为0。低位一直较差的轨迹持续受罚，高度越过.30后cost为0，未要求几何确实改善便可退出。早死更少累计负成本、冲高得到减免是具体待防漏洞，不能通过终态失败−1就断言完全排除。

正奖励+.3/秒*g*prod_i[(1−normalized_length_error_i)*max(cos_down_i,0)]*dt：单侧收短或短腿朝上不取满分；实际Swing8env新增奖励全0，因为右侧约.376m令normalized lengtherror截断为1，乘积全0。当前区域没有可用连续几何进展信号，不能为了双侧严格一致又制造奖励死区。

## 完整折扣合成场景

这些场景是抽象CPUfixture，不是经USD确认可达的轨迹，基础连续reward rate显式设定用于边界压力测试。失败末步−1、成功末步+10，gamma.99、policydt.01；相同时长fixture才能比较纯几何效果，跨时长结果同时受基础reward/失败折扣影响，不能称单一因果。

权重.3时（原回报/负成本后/正质量后）：
- 静止长腿100步：.2642/.1349/.2642。
- 提前失败长腿30步：−.4869/−.5400/−.4869。
- 短腿向下驻留100步：.2642/.2642/.4544。
- 只单侧收短100步：.2642/.2167/.2642。
- 短腿朝上100步：.2642/.1691/.2642。
- 高度越门控但长腿/方向差100步：.2642/.2642/.2642（负成本确实被绕开）。
- 收腿后站立1100步：5.0001/4.9784/5.0383。

在此fixture中安全站立仍优于驻留/早死，但没有保证所有可达轨迹都符合该排序；正质量项给短腿驻留增加回报，必须把这项目标偏好明示。几何更漂亮不替代真实站立/保持验收。

## 决策

暂不选择负距离cost或硬乘积bonus作为首训：前者高度逃逸/早死权衡，后者当前真实Swing全0且驻留激励，均没有达到上一“提供可辨别信号且不压必要转姿”的设计要求。严格PBRS、直接负距离、硬乘积bonus三种已核算候选都不是当前可提交reward；不继续浪费PPO验证日志已经暴露的信号问题。

下一CPU设计应优先满足两个要求：每侧在实际Swing长度/角度范围内仍有非零局部辨别力（例如平滑宽核而非长度误差截断后硬乘积），并将“转支点进展”与“停留短腿”明确区分。不能直接把这视为允许加入多项reward：只准备一个完整公式版本，检查实际曲线斜率、两侧独立贡献、无进展驻留/震荡/抬升/失败的总回报。若引入有限阶段或一次里程碑语义，必须基于可测几何事件、可用观测与终止时钟，先声明再校验；不硬切控制权。

保留Swing合法初态、认证B25/原DrawBack/R0，150D/控制/限矩/std/Adam保持；meanaux关闭和B轮矩成本不叠加。只要CPU未达到设计要求，就停在设计而不假造权重/运行授权。用户本轮授权的审核已完成，新runtime需具体可审spec与独立预算。

## 改动与验证

support_geometry_proposal.py新增target_terms仅CPU；新增scripts/audit_recovery_geometry_target.py及tests/test_recovery_geometry_target.py（PORTABLE3项），加原potential6项共9passed，.80秒；全输出isolated/recovery_geometry_target_audit_20261009/audit.json。模型/原reward未改，文件按新目录独占写。脚本身份校验与AST/diff通过。更新Recovery计划、新方法说明、STATUS与TOOL_INDEX。
