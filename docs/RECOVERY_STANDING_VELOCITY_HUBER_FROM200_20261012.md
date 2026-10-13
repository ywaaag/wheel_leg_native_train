# 从站立update200继续：零速大误差反馈v7

用户明确“做下去，允许开启新的PPO训练”。本轮直接从22_43最佳实验候选formal/model_update_200.pt继承Actor，不从latest300或失败镜像蒸馏来源开始。source SHA34be92249e25069f7a31e063e42c2451a3f560e8be589b118607d9b8a3384143，自己的formal/source_snapshot/spec.json SHAee612fd572d1553cfef108ee2578440349c1adc2f8b5fe8ba175b4060d805401。源未accepted，完整normal0/24；能够完成10秒窗口但持续滑走、触限与姿态失败，不能把它称通过。

## 单一主要变量与动机

IO仍multiskill_mcu_v2，31D Actor/40D Critic；网络、std、PPO参数、64normal训练、小yaw±.01、USD/Plane/PD、1/5/10ms、40/5.5Nm、动作尺度和机械保护均不改。保留现有弱镜像成本，不同时增加镜像/姿态惩罚、接触制动、Progress、历史或终止条件。BC0，无教师动作执行。

新recipe student_recovery_ppo_velocity_huber_from200_v7 / reward student_recovery_reward_velocity_huber_v7。唯一主要reward改动：替换v6正Gaussian零速tracking为negative Huber native velocity cost。原六项、pre-entry角速度成本、weak_mirror、入口/成功/失败事件、dt和完整证书完全保持。Critic与PPO Adam新建以匹配新回报，源RNG不恢复，smoke/formal各从相同update200独立开始；不加载旧value或Adam再宣称新目标对应。

定义residual=[vx/.5,vy/.5,yaw_rate/.3]，Huber(x)=.5x²（|x|<1）否则|x|−.5，r_velocity_density=−1×H×sum(Huber(residual)) /秒。H沿现有站立有效高度质量，不乘U：避免倾斜降低姿态质量时同时逃避速度成本；这属于同一个零速反馈的公式/gate设计。连续项乘dt=.01一次，无控制/初始化/fault0，真实受控失败末步保留。vx/vy为当前native速度，yaw单位rad/s；系数是训练偏好，不修改验收mean abs vx≤.5m/s、vy≤.02、yaw≤.03，不增加位置漂移门槛。

Huber小误差平滑且大误差保留线性变化，不像窄Gaussian在vx1.55m/s接近0。无上限截平速度成本；物理异常/非有限仍runtime fault。选择每秒−1、linear_scale .5/yaw .3是首轮待验证设计，不称最优。弱镜像继续−.05×H×clip(mean(e/.2rad)²,0,4)，最大−.2/秒，不硬锁动作。

## 真实轨迹重放

读取已结束22_43 B250正常8条、update200正常8条，共16episode，逐evaluation/trace SHA和schema核验；post-physics/pre-reset角速度/q、原实际物理目标和cache重放，原六项/事件及weak mirror完全一致。只连续项回放，事件另由Certificate回归；没有仿真或optimizer更新。

B250整段vx abs约.0074m/s，新速度成本约−.0001/秒，旧tracking+3.9685/秒；总连续density旧8.9212→新4.9526/秒。update200首2秒vx.4357m/s，新速度−.4812/秒；最后2秒vx2.4224m/s，新成本−4.3654/秒、总density旧+2.7830→新−1.5825/秒；整段旧+3.9581→新+1.2107/秒。这说明持续滑行不再靠持续存活拿相同净收益，并保留低速站立正收益；固定轨迹比较不能证明学习成功或唯一根因。注意新旧reward数值不能当跨配方能力分数。

## 新声明与预算

00_12独立声明configs/experiments/2026_10_12-00_12__recovery_standing_velocity_huber_from200/spec.json；公共prepare --velocity-huber核验精确update200与它自己的冻结parent/dataset/manifest。新spec/run/ledger/pose_library/发布标记，不改22_43旧预算或结果。

首段source40评分episode/900秒＋smoke12更新/900秒＋formal300/10800秒，总312updates2555904samples/12600秒含评估清理、产物2GiB。formal25/50/100/200/300同normal三组24env主评估＋Swing8回归；最后单模型normal原生和3新小yaw组32env＋Swing8，总最大248评分episode。64sim env/每case8scored分别记录。

选模仍normal完整主协议通过→入口→首次固定保持有效前缀→更早候选；源及早期候选保留，latest不自动采用。前缀不含累计速度/触限时明确说明，不能称完全合格保持。normal接受不证明Swing自主起身；Swing只是单独回归。gate仍2.5秒内确认.2秒入口、下一1000interval保持10秒，height≥.30允许.42、原水平/接触/净空/闭链/触限/速度要求。普通行为失败不因未站稳停止预算，工程故障/非有限/机械保护/用户停止/预算按规则退出，不自动retry/无限续训。

## 接线、测试与授权流程

recovery_task.py增量v7明确公式/版本，runtime沿既有post四腿q输入；training_recipe.py固定精确新源，prepare_student_recovery_ppo.py新增--velocity-huber、复用public course/identity声明。额外raw/density/dt、速度/镜像、grad/advantage/limit日志沿v6保持，无新私有trainer/launcher/watcher。原v1–v6、legacy150D/1182D/31D旧语义不变。

测试新增test_student_velocity_huber.py：0/小/高速/反向、yaw/横速、Huber斜率不消失、dt一次、fault/初始化、.42允许、原项不变；runtime_parent扩v7真实共享路径；preparation_contract核准update200public config，独立CPUoptimizer仅更新内存副本验证warmup/actor/固定std/source不变，不计在线更新。准备/重放/测试isolated/recovery_velocity_huber_preparation_20261012，冻结artifacts/recovery_velocity_huber_cpu_20261012；授权/提交isolated/recovery_velocity_huber_execution_20261012。

GPU0共享、不停止其他任务、不自动换卡，当前session/UUID/CUDA/身份/资源在reserve前核验。公开submit仅supervisor、detached后一次有界握手，既有owner负责保存/评估/结算，worker不循环查询。notifications=false；未commit/push，历史checkpoint/run/spec/ledger/evaluation/冻结副本只读。验证与实际单次提交阶段随后追加，不将SOURCE_EVAL说成formal首更新。

## 实际验证和首次提交

专项30通过，来源及公共CPU optimizer14通过，冻结PORTABLE24通过；全CPU873通过/22错误，与此前867通过基线的22个Motion迁移fixture错误ID和configure.py契约原因逐项一致；未放宽SHA或修改Motion。CPU optimizer仅独立内存副本，未改来源checkpoint、不计在线训练。机器证据verification.json。

独立新授权已通过register_authorization登记。check-submission READY/shared；GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，逻辑CUDA_VISIBLE_DEVICES=0→cuda:0，未停止其他任务。public supervisor首次launch，attempt b8e01ed45a344ffa9a1ba530013cd7a5；5秒有界握手确认worker与冻结命令/session/物理GPU一致，状态SOURCE_EVAL。formal_first_update_verified=false，不能称formal已更新。授权和握手JSON在isolated/recovery_velocity_huber_execution_20261012；owner负责后续阶段、预算和结算，本worker不轮询或自动重试，notifications=false。

本次交付只确认工程验证与提交；抑制滑行、对称和10秒主协议是否改善须由该run评估回答。普通能力失败不是工程失败，不自动追加预算。
