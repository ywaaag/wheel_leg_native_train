# v14 smoke证书停止复盘

事件f56450e92d00f8e6b8d6fc5d，run `runs/2026_10_14-09_37__standing034_survival_quality_v14`。链FAILED的直接原因为wiring证书`v14 smoke real30s normal timeout missing`，不是trainer/Isaac崩溃。source/smoke均COMPLETED exit0，无runtime failure；formal NOT_RUN。

实际新增26PPO更新/212992samples、有效Actor172032；原1000预算实际已用26，formal974尚未用，但余额不授予恢复。链915.0465秒。source ledger530.2401秒，smoke账本wall_s为null，trainer清理前380.1084秒，不能伪造smoke精确结算墙钟。source phase没有PPO。

来源v13/u988三组各8，共24例完成30秒，但24/24质量失败：姿态、速度/yaw、镜像及腿长等不合格。source在新环境确实能持续存活；不能把质量不合格写成来源物理不可用。
smoke实际592个completed episode、592次tilt终止；normal_timeout0。最长controlled episode约6.4701秒。前5次Critic warmup期间已出现tilt，说明不只是Actor更新导致：随机探索/训练分布与确定性来源评估并不等价。是哪一个噪声通道、reset差异或状态引起仍UNKNOWN，没有轨迹对照不能先归因reward或std。

## 工程流程问题

本次新增的“随机smoke必须生存满30秒才能进入formal”把能力要求混入接线证书。smoke证明source加载、实际Actor/Critic更新、非零reward、真实结束/reset、保存读回与保护；长时normal timeout/bootstrap接线应由确定性PPO0来源30秒及CPU真实storage/runtime fixture分别证明，而不是要求未学会的随机策略先通过长期存活。
该门槛在新实验中应移出随机训练硬前置，但不能直接删掉全部证据要求或假造timeout计数。需要确认现有source评估实际到达true truncated、terminal Critic缓存和bootstrap链；缺测则有界PPO0接线诊断，不追加在线PPO解决工程证据。
CPU核对已证明公式/shape/存储，不能等同真实runtime timeout正确。592次普通tilt是任务失败，不是控制权/闭链/非有限故障；正式预算尚未开始，不能宣称v14长训失败或收益已验证。

smoke末尾独立确定性评估另有8/8生存30秒、0/8质量通过、online_certificate_matches=true，模型update26 SHA `c78b200913e7ef597920a07d03db65fcda95641ff5334716b4e33766b3134543`。因此必须区别训练随机action的592次tilt与确定性mean action的完整生存，不能称smoke模型只存活6.47秒。末尾评估见smoke/progress.json latest_checkpoint/evaluations；该phase没有candidate_selection.json，缺文件不补造。确定性timeout/bookkeeping已实际执行，但PPO storage timeout bootstrap仍只CPU验证，因为训练中没timeout。

## 唯一下一步

先准备版本化smoke证书调整：工程证据与生存能力分别记录，随机smoke不要求30秒能力通过；真实timeout路径使用身份匹配的独立来源诊断证明。保留FAILED/原wiring/26更新消耗，新增恢复声明或新spec，不能在活动/旧spec上改规则再追溯通过。
然后以原u988同reward/物理/探索继续新的formal授权范围；不把短smoke模型直接当好来源，也不同时改std/reward/网络。本通知不授权实施恢复或重新运行，当前只读复盘，不自动提交。

## 同事参考结论

只读对照已完成：同事RMUC复核（该报告已按文档整理删除，长期结论见 TRAINING_EXPERIENCE_REUSE.md §12）。优先借鉴完整episode计数、真实受力/几何均衡与密集误差信号，不能复制动作/物理/外环或把早期11/56报告视为当前全部能力。对本次最直接的启发是训练接线不应要求已经学会的行为；独立能力验收仍严格。

本轮仅新增复盘/同事报告与更新STATUS。没有修运行代码、改历史证据、启动PPO或重试。
