# Motion512进入formal前存储与记账修复

用户明确同意执行修复并继续原授权学习；没有新增reward、物理或速度课程。

## 实际阻塞

旧链 `runs/2026_10_14-16_51__motion31_parallel512_l1_2000` 终态FAILED，原因 `ValueError('insufficient output storage before reserve')`。source完整、smoke真实50更新/3,276,800samples，五命令40/40生存30秒但Motion accepted0/40；wiring_certificate为PASSED。**不是因为不会生存而拦截训练**。formal目录及formal attempt均不存在。

两处确定工程错误：

1. storage_budget仍以JSON每数值32字节和Recovery默认命令数估算，而此路径实际写float32 NPZ＋compact scoring proof，估出约2.84GB超过2GiB声明；磁盘仍约55GiB，并非ENOSPC。改为Motion专用NPZ字段/真实五命令/100更新节点估算，保留原容量门，formal总估计含临时峰值与终态余量1,485,420,544字节。每个中间checkpoint保留完整评分输入；完整control/Actor trace限来源、smoke和终点，不因单env通过就反复大保存。
2. motion_runner遗漏Ledger.charge：实际50更新但旧ledger记0、链汇总也记0。新增每个真实optimizer update后exact-ID扣账；旧账本和报告不改。独立恢复证据将原progress/terminal/50行metrics绑定SHA，明确真实历史消耗50，不能拿旧0当作免费训练。

## 恢复边界

新声明：`configs/experiments/2026_10_14-17_40__motion31_parallel512_storage_recovery/spec.json`；新run同名。受限 `motion31_preformal_storage_recovery_v1` 仅接受上述已结算preformal存储失败、无formal attempt、原PASSED wiring、逐文件SHA完整来源/smoke矩阵，禁止行为变化及重复claim。

复用原来源评估与smoke，不再浪费采样或评估。formal仍从原始迁移Actor/std开始，新Motion Critic/Adam/seed，与原冻结formal初始化相同；**不继承smoke model_update50的权重**。512env、128steps、0/±0.5/±1、reward/LR/std/归一化/网络/时相/物理全部保持。

新formal最多2000，smoke0；历史50＋新formal≤2050。旧链耗时2183.060236秒，原18小时余额62616.939764秒（约17.39小时），不重置；新产物仍≤2GiB，先到即停。source→formal生命周期携带受限证书，缺失/篡改证据仍拒绝；普通能力失败不拦截开始学习，物理fault仍立即停止。

纯CPU PORTABLE与定向测试覆盖NPZ容量、旧账本保留/真实消耗、行为变化和墙钟扩额拒绝、无重复smoke、显式恢复状态转换、真实PPO fixture。新声明公共preflightPASS、submitREADY、health无finding；运行证据由后台产生，不由CPU冒称。

修改：`students/motion_runner.py`、`motion_training_requests.py`、`motion_wiring_recovery.py`、`training.py`；`command_v6/wiring.py`、`stand_chain.py`、`supervisor.py`、`tools/run_state.py`、`tools/storage_budget.py`；专用prepare_motion31_wiring_recovery.py和test_motion31_training.py。没有改原FAILED、旧raw评估、旧spec/ledger/checkpoint或停止其他任务。

## 实际提交

PORTABLE416passed/8skipped，定向58passed。新链已public detached提交，worker763197、monitor763238、trainer763240，formal attempt `e5aefb0e73d546faa4ddceadcdee41f5`。唯一启动读取实际formal3、progress3、新ledger3一致；已经进入学习，尚无100更新独立验收。

公共握手识别FORMAL但因Motion manifest缺PID/启动时间及progress attempt-id保守记UNKNOWN；不覆盖该记录、不重启活动训练。单独一次只读启动补充核验PID/argv/spec/output/attempt/start/CUDA均OK，见同名artifacts/supplementary_startup_identity.json。该报告接线缺口留待下次工程修复，不影响实际已执行PPO，也不冒称原公共握手PASSED。

原50smoke是工程已通过证据而不是能力前置。恢复formal依旧采用原sourceActor和新Critic/Adam，前5次Critic warmup；没有重新执行smoke。后台继续有界预算/评估/结算/当前owner终态通知。TensorBoard6006新17_40分组、bridge764620；bridge只读，不控制训练。不轮询，不自动重试。
