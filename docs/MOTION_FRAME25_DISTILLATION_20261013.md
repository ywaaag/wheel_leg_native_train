# Motion25D无历史学生蒸馏结果

本轮用户“尝试蒸馏”，实际完成独立CPU监督训练、保存和确定性Actor导出；未启动新Isaac/GUI/PPO/GPU训练/实机，未修改正在执行的Motion/Recovery源码与冻结声明。

## 模型和接口

motion_frame25_distilled_v1，MotionFrame25ZeroStudent；25→128→64→32→6，ELUalpha1、最后线性mean。13862Actor参数、55448FP32bytes、13632MAC/inference。没有history/cache隐状态或teacherID输入，25D字段原Motionframe逐项不变；命令height.34、0vx/0yaw，腿.5rad/轮100rad/s、原reference/leftfirst顺序、推理outputclip±1。输出为完整确定性mean，不随机采样、不装BCAdam到PPO。

此接口与legacy150D不是同一版本，公共旧150D播放/训练入口不接受它。未改旧校验来强行加载。现交付CPU模型/ONNX，独立物理执行适配和公共PPO0声明尚NOT_RUN/未接入；不能用旧GUI命令冒充25D运行。

## 教师和数据边界

教师来源旧0.34站立最佳05_39/update300，SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb。教师冻结，不加载教师Adam更新，前后SHA不变。

状态数据来自两份已通过的B2500.40正常站姿完整firstepisode原始轨迹，motion_frame/history明确为动作前输入。按具名joint_q_pre/dq_pre、motion_previous_input核对frame列；对齐最大误差0.0。四腿reference0、state时轴与controller证据保存manifestSHA。

**标签是离线teacher-query，不是0.34成功实测目标**：将原状态frame/history的heightcommand从.40设.34，由0.34教师确定性输出给标签；仅教师自身既有actionclip±1，记录越包络通道数[0, 0, 0, 0, 0, 0]。没有通过改命令重写原始run/evaluation。学生只能看到当前25D，教师history只用于生成监督标签。

16个相近zero正常episode，train6/validation2/test8；唯一样本train6120/val2040/test8160。按完整episode隔离，不随机拆相邻frame。但近乎相同初态重复不证明泛化，.40状态分布也不能代表真实.34学生闭环。只教零命令，未教非零vx/yaw/Swing；.34成功teachertrace缺完整preframe时不猜测重建。

采样resetearly首20step与后续hold各50%，内部均衡episode，实际两桶各1024000抽样；训练unique120/6000，过采样不是新增物理经验。

## 实际训练与拟合

CPU4threads、AdamLR1e-3、batch512、seed20261013，上限5000step/1200s；实际4000 optimizersteps/12.213s，五次验证无改善早停，bestvalidationstep3000，test只用于最终报告不选模。onlinePPO0。

物理单位loss：四腿mean((error/.1rad)^2)+两轮mean((error/10rad/s)^2)。不改原动作范围，不tanh扭曲原teacher线性mean。

测试集early：腿MAE.000765rad，两轮MAE.185357rad/s；hold腿MAE.0002626rad，两轮MAE.056103rad/s。逐通道MAE/P95/max及outputclipfraction见training_result.json，不能用这些拟合成绩当站稳通过。

## 文件和验证

best_validation.pt SHAe56dc7f5b07f15bcd14abcc34fde14bdf09316c9716d3918460ac80435fedd06。
actor.onnx SHA0507642d2afb73ed0d5d10bc0dbe4a991bc5ce5eba96d80b431262141da98f16，fixed[1,25]→[1,6]float32，operatorsGemm/Elu。ONNX ReferenceEvaluator与PyTorch32个独立test输入最大差5.960464477539063e-08；物理误差上界腿2.9802322387695312e-08rad、轮5.9604644775390625e-06rad/s。TorchScript误差0，goldenvectors保存。

4CPU行为测试验证参数量/拒绝150D、物理解码loss单位、actualepisode拆分、actualcheckpoint/TorchScript一致及teacher不变。未计作物理认证。运行脚本manual_train/motion/frame25_distillation/distill.py；独立dataset/manifest/random/best/latest/ONNX/TorchScript/result均在isolated/motion_frame25_zero_distilled_20261013。

## 下一步

优先接通显式25D publicmodel/evaluator适配，在合法低于.36的初态上做学生独立zero闭环与同条件teacher对照，随后才增加非零运动教学。不能把旧模型实测能力套给新student，也不能称.34实机限高已通过。闭环、STM32时延、真机全部NOT_RUN。本轮未修改电控legacy150D协议，最终若采用25D应另交付对应输入版本。
