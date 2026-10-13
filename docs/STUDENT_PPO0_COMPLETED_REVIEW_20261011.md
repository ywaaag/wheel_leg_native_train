# 新学生独立PPO0复盘 — 2026-10-11

结论：CPU动作拟合达标未转化为闭环通过。RecoveryStudent四组0/8（总0/32），同条件B50 .50秒→B250教师四组8/8（32/32）；MotionStudent零命令确认入口8/8，但完整保持0/8，B250正常8/8。流程COMPLETED不表示学生能力accepted。

## 运行与身份

run：`runs/2026_10_11-00_55__student_independent_swing_ppo0`。公共supervisor，GPU0 shared/UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72/逻辑cuda:0。10组×8=80评分episode，64仿真env/8评分env。437.4769秒含清理，99002405 bytes（94.42MiB），PPO0、optimizer0；evaluate1 exact-ID账本COMPLETED，未重试、不追加、不启动训练。所有保存数组有限，80初态有效、模型内存权重不变、依赖checkpoint/数据/资产SHA未变，清理结果保留。

RecoveryStudent SHA bd163dd75b6ac5e8f33f82069fe94f173069ed966f077133c895eb11f1bc499c；MotionStudent SHA 769a0512638dfb3ab47f5f5720c470d4e88c59ed0a67957720e8a3bcba42779d，均为上一轮BC最佳，未覆盖或更新。新学生独立协议≤2.5秒确认入口＋随后1000interval保持，教师仍原.50秒前缀＋2秒接管＋10秒保持。小yaw只±.01rad，不扩展泛化声明。

## 各条件

|case|初态有效|入口|完整10秒|主通过|倾角终止|
|---|---:|---:|---:|---:|---:|
|student_native|8|0|0|0|7|
|teacher_combination_native|8|8|8|8|0|
|student_yaw10|8|0|0|0|8|
|teacher_combination_yaw10|8|8|8|8|0|
|student_yaw11|8|0|0|0|8|
|teacher_combination_yaw11|8|8|8|8|0|
|student_yaw12|8|0|0|0|8|
|teacher_combination_yaw12|8|8|8|8|0|
|student_normal_zero|8|8|0|0|8|
|teacher_normal_normal_zero|8|8|8|8|0|

Recovery学生31/32在约1.34–1.62秒受控后倾角终止；原初态env1在2.5秒未确认入口。学生恢复四组峰高的env平均约.3850–.3855m，已经抬升，不能描述为趴着完全不动；主要问题在抬升后姿态/收稳。高度超过.30不代表满足连续入口水平/接触条件。

Motion零命令学生初始.20秒确认入口，随后约2.63–2.79秒受控时倾角终止，完整10秒未完成。其小拟合误差同样不保证闭环平衡，不能升级为Motion驾驶来源。

## 离线对齐及证据限度

首受控输入：Recovery四组student实际1182D与同条件teacher轨迹用同纯函数重建1182D，最大差约5.96e-8；正常Motion首输入差0。支持排除初始输入明显接线/尺度差异，尚未逐帧排除所有后续encoder时相。教师前.5秒路径上Recovery学生腿平均拟合误差约.0018rad。

对齐真实受控时钟（不含.4秒初始化）：Recovery pitch/roll差首次>.05rad约.99–1.14秒，高度差首次>1cm约1.10–1.18秒，实际腿目标差首次>.10rad约1.17–1.37秒。姿态差较大先于这个粗腿目标差阈值，不证明腿目标无影响，也不证明唯一起因；小动作/轮目标误差可能累积，待进一步局部分析。

Motion零命令pitch/roll差首次>.05rad约1.88–2.04秒、高度差>1cm约2.27–2.43秒，末步之前腿目标差始终未超过.10rad。该阈值很粗，不能据此排除细小动作误差和反馈敏感性。

逐env受控长度、阶段位移/native速度/姿态/角速度、接触、六通道raw裁剪与applied触限，80项SHA一致的同协议rescore，全部见`isolated/student_ppo0_completed_review_20261011/review.json`。100Hz策略末采样不冒称完整200HzPD/1kHz力矩。数据定位阈值只用于离线诊断，不修改gate或部署控制。

## 本轮工程修复

提交前公共health_check仍硬编码旧distribution.std_param、同维Actor/Critic和教师内置资产字段，拒绝新版学生。尚未reserve时已发现并修复显式student metadata分派：读取log_std、1182/1191、dataset/manifest/episode资产谱系SHA，同时保留legacy检查。学生checkpoint不改，不伪填旧训练身份。13针对CPU＋29实际冻结PORTABLE通过；public submission再次READY后首次提交，非失败run重试。

修改：`src/native_stand/command_v6/tools/health_check.py`、新增`tests/test_student_health.py`和`scripts/review_student_validation.py`；新声明授权及账本由公共工具登记结算，STATUS更新本次终态。本轮不commit/push，不改旧run/checkpoint/活动任务。修复/授权/检查/启动入口位于`isolated/student_ppo0_authorization_20261011/`，冻结验证`artifacts/student_authorized_healthfix_cpu_20261011/validation_result.json`。

## 下一最小工作

先离线分析受控.7–1.2秒：在成功教师轨迹与学生实际轨迹上分别计算mean物理误差，分腿/轮及history偏移，核对落地事件、姿态/角速度和previous目标；Motion零命令同样检查1.5–2.5秒的细小反馈误差。只能把教师真实轨迹当有效标签，不能默认B250能给任意学生失败状态正确示教。

如果编码一致且误差积累明确，再准备有界补采/教学或独立监督改进，重新声明预算。当前不直接追加PPO、不延长BC、不放宽评分、不用教师救场称学生成功；新仿真/采样/optimizer均需对应新范围授权。
