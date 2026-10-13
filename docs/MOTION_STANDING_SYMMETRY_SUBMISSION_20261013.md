# Motion零命令站立与实际双腿对称专项：2026-10-13

本轮用户同意先攻克对称，初始化不强求0.34m。原合法Motion初始化root高度0.40m、原关节reference和初始化流程保留，训练高度命令仍0.34m。Recovery任务及其冻结代码没有修改。

## 已停止的旧任务与来源

旧standing034_pm2_fixed任务正常STOPPED，无active_spec：1488次PPO更新（formal1363、smoke125），12189696samples，27695.015478秒，552评分episode。历史账本、checkpoint、spec及原始evaluation不修改。

逐项比较7个零命令原物理验收8/8且完整保持窗口有效的候选，选实际镜像误差最小者：
`runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt`，SHA256 `4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb`。其零速实际hip/active镜像MAE约0.3102/0.3132rad，尚未对称通过。它不是所有驾驶命令均通过的模型。机器证据见manual_train/motion/symmetry_verification/source_selection.json。

## 已实现的新配方

完整执行副本为manual_train/motion/standing034_symmetry_engine_v3/src/native_stand，增量复用公共supervisor、CommandEnv、PPO、evaluator和stand_chain，未新增私有trainer或watcher；未修改共享src和活动Recovery源码。

64环境全部零速度/零yaw，高度命令0.34m；保留legacy150D、Motion动作腿0.5rad/轮100rad/s、原USD、PD、1/5/10ms与40/5.5Nm。

保留来源原Motion reward，只新增实际post-physics/pre-reset关节镜像Huber成本：e=[left_hip+right_hip,left_active-right_active]，尺度0.20rad、delta=1、两通道均值、权重−1/秒，连续项乘dt=.01一次，无封顶，无硬对称动作投影。

离线重放8000个有效保持样本，来源成本密度均值−1.05849/秒、每步−0.0105849。合成严格镜像为零、错误符号/大偏差非零且梯度未封顶。奖励有效不表示已学会。

新recipe首次只继承Actor/std，新Critic/Adam/训练RNG及5次Critic warmup；同配方续块恢复完整Actor/Critic/Adam/std/RNG，不重复warmup。

新联合验收要求固定10–20秒保持窗原物理站稳且实际mirror MAE两项≤0.05rad、P95≤0.10rad；缺失、无效、短窗口不通过。height均值0.32–0.36m、带内比例≥90%、保持每样本≥0.30m。保留原Motion姿态/接触/速度/闭链/触限要求，不冒称采用Recovery更严格验收。额外记录腿长差、轮位置差、roll和目标镜像，仅作诊断。

## 验证与实际提交

相关CPU81 passed/1 deselected；排除项硬编码共享src根，不能在独立bundle下冒充portable，生产SHA校验未放宽。实际冻结PORTABLE9 passed，冻结preflight PASS。两次真实CPU optimizer更新仅使用独立内存副本，验证Critic warmup冻结Actor及之后Actor实际更新；来源checkpoint SHA不变，不计在线PPO。

共享全CPU943 passed/8 skipped/22 errors；22个错误逐test-ID与修改前baseline完全相同（既有Motion工程证书SHA fixture），对照保存在baseline_comparison.json，未作为新测试豁免。

零写plan/授权/submit检查完成；GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`，共享，不抢占、不换卡；提交时可用28800MiB，最低要求4096MiB。逻辑CUDA0，当前session绑定。

task：manual_train/motion/tasks/standing034_symmetry_selected_20261013。
spec：configs/experiments/2026_10_13-08_29__motion_standing034_symmetry_block0000/spec.json。
run：runs/2026_10_13-08_29__motion_standing034_symmetry_block0000。

一次30秒握手submitted=true/submission_verified=true，当前阶段SOURCE_EVAL，formal_first_update_verified=false。不可称已完成PPO或能力通过。实际运行冻结220个模块与CPU副本逐SHA一致，spec SHA63952d9e9eda835e33a693adc295531a658c0afde0d36d55d1515ca1a3f4a844。

每块smoke25＋formal300、325更新/2662400samples、4小时、2GiB；任务累计上限null。100/200/300评估；连续两次完整8/8联合通过则停止并保留该站立候选。至少5000formal后固定停滞规则、有限完整状态回退；工程/资源/磁盘故障停止，不自动重试。通知关闭。既有owner续块，worker不轮询。

该专项只认证零命令站立与对称，不自动恢复±2m/s，更不认证Swing或两资产接管。站稳且对称后再准备驾驶回归。准确命令仅维护TOOL_INDEX。

## 本轮文件范围

新执行副本增量模块：motion_course/{symmetry,domain,io}.py，command_v6/domain/{reward,recipe,evidence,protocol}.py，command_v6/runtime/env.py，command_v6/tools/evaluate_checkpoint.py，command_v6/train.py。

新测试manual_train/motion/tests/test_standing_symmetry.py；新task/spec、symmetry_verification机器结果；文档STATUS、TOOL_INDEX、WORKFLOW、ARCHITECTURE、manual_train/motion/README及本报告。其他worker既有dirty changes保留；无commit/push。
