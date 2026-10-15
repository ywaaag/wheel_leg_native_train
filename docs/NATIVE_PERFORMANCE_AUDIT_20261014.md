# Native性能诊断与优先优化顺序

用户希望压榨主机性能。本次明确有界5秒host诊断（pidstat/nvidia-smi dmon/iostat），只读一次run指标并审源码；不是守候训练。未启动仿真/optimizer，未停止同事或当前站立任务，未改其冻结配方/环境数/控制周期或系统功耗设置。数值产物artifacts/native_performance_audit_20261014。

## 实测

CPU i7-12700KF/12cores20threads、RAM125GiB/约93GiB available、swap几乎0。5秒主机CPU空闲约83～86%，native trainer约118%（1.18逻辑核心等效），92线程并不等于92线程有效计算。GPU0 SM busy约92～96%，显存约9.7GB、功耗约92～94W/320W、核心2760MHz/温度39～40°C；GPU1利用率0%。同事仓库另有1024env进程503261共享GPU0（快照），不抢占，也不由本次擅自改变其设备。

不能将GPU busy理解成满峰值FLOPS；大量小kernel、串行依赖和同步也能busy且功耗低。本次只有全GPU计数，没有CUPTI/Nsight逐kernel或native单进程占比，不能证明哪一个kernel占多少百分比。时钟与温度不支持明显热/功耗墙；powersave标签不代表锁低频，intel_pstate active/turbo开启，没有证据支持先提高功耗/超频。

磁盘iowait约.05～.2%，NVMe该窗口util约1.6～3.7%，不是当时训练吞吐主要瓶颈；分区只剩约8GB级可用，容量风险与带宽瓶颈要分开。

普通update间隔中位约15.3秒，每update8192sample，约535原始envsample/s；包括128policy步/1280physics步、PPO及摘要写入，不是单Actor推理速度。每环境rollout仿真1.28秒。真实update边界100→101与200→201间隔约859/936秒，主要包括3case完整评估、保存/环境重建及下次update；不能称精确eval-only时间。update181有暂停，排除正常训练估计。Motion5casePPO0账本42.8分钟包含暂停，不是纯GPU时间。

## 源码中的具体瓶颈候选

1. students/evaluator._rollout每policy步对16项以上字段调用detach().cpu().numpy().copy()，3000步×多case，大量小host同步；同一小tensor传输启动成本可高于内容。actor/critic输入、root_pre/post、joint、control、geometry、events等都立即转CPU。这是明确静态风险，当前未用profiler证明占比。
2. students/training.execute每步int(valid.sum())、int(nonzero.sum())、int(dones.sum())、s[dones,0].tolist()和3个event int；还有真实mask equal/boolean检查及domain finite检查。约1000级host同步/update，且仅64env小kernel。必要物理故障检查不能盲删，但统计转换可以汇总到rollout末。
3. 正式评估每100update逐case单独create/close64env，而只score8env；每次3case约14～16分钟，使有效PPO吞吐被评估大幅稀释。若普通100update约26分钟，则全套评估约占周期三分之一。不能为了提速缩短30秒或忽略失败env。
4. 网络很小/环境数64，GPU批量较小；增加256/512env有机会提高sample吞吐，但会改变每update数据量、随机采样和PPO预算语义，属于新性能/训练对照，不能原地扩大当前run或承诺倍数。
5. 缺rollout/PPO/eval/序列化分项计时，尚不能定位训练15.3秒中究竟物理还是PPO更慢；先计时才改线程/AMP/compile。

## 唯一优先实施路线

第一批：不变样本/物理/算法，新增分项time.perf_counter计时，并将评估scored8env完整trace先存GPU预分配buffer，episode结束统一copy到CPU；training只将统计GPU聚合后每rollout转换。必须逐字段与旧采集比对、terminal pre-reset对齐、相同dtype/RNG/action/storage和评分一致。普通断言和安全故障是否移频另审，不以性能理由关闭。所有这些在新明确版本及下一次进程启动生效，不热改当前loaded trainer。

第二批：同一app并行多case槽位评估，保留每case8/完整30秒/预定seed/原协议/initial独立记录。跨envseed/reset顺序会影响RNG，必须建立等价初态与行为回归，不能简单把8×3合成一个随机batch称同协议。

第三批：在新预算中固定真实sample量对照64/128/256env和Torch线程1/2/4，报告sample/s、eval耗时、有效Actor样本和学习表现；GPU1可以承担独立评估或另一实验，但当前学生入口强制GPU0，需要显式GPU映射适配和新授权范围，不直接移正在训练的任务。多GPU不自动加速单个小Actor/PhysX场景。

不建议先做：8ms（增加物理调度负担，不保证墙钟更快）、同时换LR/AMP/network、盲目设置20Torch线程/超频/增加power limit、关闭closure/limits或砍验收窗口。硬件利用率最大化应以有效sample和验收结果/小时为准，不是nvidia-smi数字越高越好。

## 当前交付

新增本报告与audit/raw5秒采样文件，STATUS导航。未修改运行源码、系统设置、GPU分配或训练预算，没有实际优化后的物理吞吐证据；不能承诺已经提速。下一轮首选GPU缓冲评估采集＋GPU统计聚合，前后保留相同证据。
