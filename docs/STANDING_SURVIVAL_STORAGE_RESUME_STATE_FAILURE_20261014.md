# v14存储恢复链状态机阻塞复盘

事件87f9ae90cd4c93d4cdfb8156；12_44恢复链FAILED。本次只读复盘，新增文档/离线摘要，不修改旧证据，不修共享训练代码，不自动重提。

## 确定的接口错误

stand_chain.worker已把student_storage_resume分派到source_eval→formal，但只对recovery_course.resume生成continuation证据。run_state.transition允许SOURCE_EVAL→FORMAL的前提是受验证的continuation，且目前只认识verified_course_continuation_v1。student storage恢复没有对应证据/版本，所以record_state在调用run_phase(formal)之前抛出ValueError。

这是上一轮实现遗漏，不是模型跌倒或reward失效；先前CPU验证覆盖容量、恢复张量与preflight，却漏测真实worker到RunState的恢复路径。不能以“CPU通过”表述完整后台恢复已被验证。真正Actor/Critic/Adam的运行时恢复尚未执行，只有CPU逐tensor读回。

## 实际消耗

本次source_eval唯一attempt COMPLETED/exit0，663.343秒；全链665.273秒（11.09分钟）。新增PPO0、samples0；formal没有attempt、未运行。父链已耗312次未变、余688，旧FAILED不改。通知只授予本次复盘，不授予重试。

## update300完整复核

三组normal_native/normal_yaw10/normal_yaw11各8例，全部连续30秒生存，质量0/24。checkpoint SHA64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f。来源评估NPZ/JSON均完整保存，本次没有再次触发storage cap；不能据一次source保存证明后续所有容量边界均已物理验证。

三组30秒均值几乎一致：abs vx约0.3228m/s、高度0.32749m、pitch约0.22498rad、roll约0.000010rad；轮心前后差约0.556cm、腿长差0.0437cm、hip/active镜像误差0.02181/0.01931rad，双轮接触1.0、触限约0.0333%。

评分末10秒：水平速度p95约0.3606m/s，高于0.3；最差姿态轴平均约0.2256rad，高于0.10。每组8例均失败posture_mean/posture_peak/tilt/horizontal_speed，其他高度、yaw、接触、限矩、轮差、关节镜像、腿长、闭链、间隙检查均通过。

几何改善已在同一模型完整24例得到支持，不仅是上一轮单case；仍不是稳定零速直立合格，不能用腿对称改善替代pitch/速度验收。三组包含两种seed/微小yaw设置，不冒称三个训练seed或最终三seed认证。

## 唯一下一步

修复student storage恢复的具名continuation证据：先verify(spec)核验父失败、原smoke、SHA与余额，再向RunState传入独立受支持版本；普通无证据SOURCE_EVAL→FORMAL继续拒绝。CPU执行真实worker fixture，模拟成功source和formal进入，覆盖缺证据、错误SHA、余额冲突及重复提交；不能只测试transition函数。

保持update300和688剩余上限，不改reward/std/LR/物理，不再创建需要重新训练smoke的链。重复来源评估应通过严格身份的只读引用复用本次完整三case，若当前公共学生路径不支持，就先补最小证据适配；不要又重复消耗约11分钟来源评估。新run/新恢复声明仍需用户明确运行授权，当前不自动执行。

逐环境指标、gate和输入SHA：artifacts/standing_survival_storage_resume_terminal_20261014/audit.json。修改文件仅本报告、STATUS和该离线JSON。
