# 同一Recovery学生补学站立：2026-10-11

用户要求先蒸馏站立能力、确保基本站稳。此次仅对原BC学生副本进行CPU监督训练，随后公开supervisor有界PPO0验证；不继续17_12 PPO、不训练MotionZero或其他技能。最终仍是单一Recovery学生自主Swing起身和保持，不把教师切换表塞进输入。

## 来源与数据

Actor起点isolated/recovery_mcu_v2_bc_20261011/best_validation.pt，SHA7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470。31D/40D、网络、1.5rad/100rad_s、物理/PD/限矩保持。继承该Actor且重新建立BC Adam；Critic新初始化并不由BC更新，std未优化。没有继承旧PPO Adam/critic/RNG。

读取已核验student_mcu_v2_teachers数据，逐原始文件SHA复核。旧B250正常站姿的16个成功episode（train6/validation2/test8）改用Recovery one-hot，其pre-action本体字段、物理目标标签、上一执行目标、样本时序、原episode划分不变。不平均两教师动作，不把失败数据伪装成教师标签。原B50/B250组合31个成功episode的四阶段仍保留（15/8/8），不是31类独立初态。

新数据isolated/recovery_standing_teacher_data_20261011，共52673唯一transition、47完整episode。新增normal_standing阶段，batch512时standing256＋原四阶段各64；每阶段先均衡episode后选时间点。重复抽样不计新经验。新manifest记录原数据和原始证据SHA、输入重编码及来源身份。

| 阶段 | train唯一样本 | validation | test |
|---|---:|---:|---:|
| 收腿准备 |750|400|400|
| 转腿抬升 |375|200|200|
| 动态收稳 |1466|788|774|
| 起身后保持 |15000|8000|8000|
| 正常站姿保持 |6120|2040|8160|

## 实际CPU训练

5000 optimizer steps、16.114秒、4threads、batch512、Adam1e-3，每200step验证、连续5次无改善早停。最佳验证4800step，选模不使用test。loss仍为四腿物理误差/.1rad与两轮误差/10rad_s分别平方均值。验证集按实际sampling权重选模。

正常站姿验证腿MAE .0012rad、轮MAE .383rad/s，原BC对应.0034rad/.863rad_s；原起身四阶段均仍符合既有MAE/P95参考线。这只是既有教师分布上的动作拟合，不是闭环能力证书。完整per-channel/P95、采样次数、重复次数、各split误差见training_result.json。

新checkpoint isolated/recovery_standing_distilled_20261011/best_validation.pt，SHA5d6209b95e384f663b925f70248e6c9bf0034d1d460ad3b3f14251be0e46c495；latest另存，初始化文件明确inherited_actor_initialization.pt而非伪称Actor随机初始化。教师及源BC文件SHA未变，新学生角色RecoveryStudent，不覆盖旧学生。

## 验证与本次物理范围

29相关CPU测试、真实迁移数据测试1通过、冻结PORTABLE20通过；全CPU849pass/22errors，与本轮前基线22项fixture ID一致，未放宽生产SHA。机械限位、动作尺度、初始化mask与共同模型构造仍由原接口执行。

20_14新独立spec/run/ledger：4组各8评分env=32episode（64仿真env），新Recovery正常站姿、原Recovery正常站姿、B250正常基线、新Recovery原生Swing。PPO与物理期间optimizer均0，总墙钟≤1800秒含清理、≤512MiB。用户此前明确授权后续训练，本次按先补站立的指令执行该必要闭环验证；物理GPU0显式shared、UUID/session/源码/模型/声明核验READY，不停止其他任务、不换卡、不自动重试。

站姿条件为正常初态、不加新角速度扰动；不能称为已验证站立鲁棒性。本轮学生运行全程自身31D输入及Recovery标识，不执行教师前缀或救场。0.20秒入口＋固定1000interval保持，以学生当前协议评分，失败仍保留分母。Swing仅原生初态回归，不冒称四扰动组完整认证。

本轮源码：students/distill.py（显式来源继承与五阶段站立优先采样）、scripts/distill_student.py（--source-checkpoint）、scripts/prepare_recovery_standing_distillation.py（具名数据迁移与SHA）、scripts/prepare_student_validation.py（--standing-check版本明确矩阵）；新增tests/test_recovery_standing_distillation.py。运行产物均独立，不修改旧run/checkpoint/spec/ledger。待终态后追加实际能力结果，不以拟合误差保证站稳。


## 第一版闭环失败与第二版关键帧采样

20_14首版PPO0终态COMPLETED，32episode/99.7188秒，无工程failure。新学生normal0/8入口/保持、原学生0/8、B2508/8；新学生Swing0/8，约2.5秒未进入，不能宣布起身回归通过。正常站姿新学生约.51秒倾角终止，source约.37秒。按teacher动作数据细分，首版正常首个动作验证MAE腿.04871rad/轮1.711rad_s；长期保持腿.00098rad/.374rad_s，说明全局平均掩盖关键入口帧。此为采样不足证据，不是唯一根因证明。

第二版standing_priority_reset_v2保留50%normal＋50%原四阶段，normal内部每256抽样中64首动作、128下一19动作、64其余保持，仍按episode平衡；不新增物理数据、不更改标签、网络/尺度、PD/力矩。从同一原BC重新开始，不从失败首版接棒。独立数据isolated/recovery_standing_reset_teacher_data_20261011，独立学生isolated/recovery_standing_reset_distilled_20261011。新增5000CPU BC steps、17.4793秒，best4800；两版合计10000steps，在线PPO仍0，不借旧额度。

第二版首动作验证MAE腿.00080rad/轮.400rad_s，下一19动作.00247rad/.583rad_s；normal全阶段.00164rad/.408rad_s。第一版、第二版真实分桶误差见reset_bucket_errors.json。验证最佳仍按声明阶段总体加权loss选择，测试集不选模；小初态组不能证明广泛泛化。第二版SHA06c33cf7552d2f43b015fca589b927d4634a914a1e9680a4c07da38109e4e365。

20_19新独立PPO0声明4组32episode/1800秒/512MiB，非20_14工程重试或覆盖，physics0训练；sharedGPU0核验READY首次提交。20冻结PORTABLE通过，全量850pass/22项同基线fixture errors，未忽略本轮新错误。结果待终态追加，不以关键帧拟合宣称站稳。


## 第二版闭环终态及设备选择

20_19 COMPLETED，无工程failure，32episode/134.941秒。新Recovery normal入口8/8，但完整保持0/8，约1.16–1.18秒后倾角终止；原BC normal约.37秒倾倒0/8，B250正常站姿8/8通过10秒，新学生Swing0/8入口、2.5秒deadline。第二版两模型角色与新旧输入/目标缓存经公共review逐环境重评分一致；首动作拟合改善确实带来更长短时站姿控制，仍未保证基本站稳。不要采用为accepted，不替换原完整Recovery排名来源。Swing回归未通过，不能只因站姿1.17秒更长宣布完整能力改善。

两版总CPU BC10000步/33.5933秒；两次物理PPO0共64评分episode/234.660秒，在线PPO及物理期间optimizer0，无新PPO续训。模型和数据集各独立保留；明确区分教学拟合、入口、完整窗口和证书。

用户要求哪个快用哪个：此前使用CPU默认，现新增distill_student.py --device auto（CLI默认auto），CPU/GPU0各10热身＋100个独立副本前向/反向梯度batch测速，不执行Adam、不修改原模型、恢复RNG；记录实际物理GPU0 UUID、显式CUDA_VISIBLE_DEVICES=0、剩余显存≥2GiB及共享快照，不停止其他任务、不换卡。库默认CPU保持旧调用兼容；可显式--device cpu或cuda:0。该测速只覆盖前向/反向，不包含采样与Adam，若完整端到端测量发现差异应进一步按实际吞吐修正。

本次CPU .000636463秒/batch，GPU0 .001187770秒/batch，CPU约1.87倍快；GPU0当时used4326MiB共享有负载，不能推广到GPU空闲状态/大网络/PPO。此次不为设备比较重复训练学生。机器证据device_benchmark.json和completion.json；原模型参数未变。

下一重点：基本站立仍未通过，先检查正常站姿约.2–1.17秒闭环离开教师分布的最早状态，准备站立专门的有界on-policy学习或教师可恢复范围内补教，而非继续以整段平均BC误差作为通过条件。不自动从新候选续Swing PPO，不放宽10秒门槛，不保证已有数据能教会全部扰动。
