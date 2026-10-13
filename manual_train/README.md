# 人工训练工作台

从 [Recovery 工作台](recovery/README.md) 开始。这里提供完整裸源码副本、分步骤命令、配置/奖励/续训手册，使用项目已有的训练、评估、播放与预算监督链。

人工实验和 Codex 实验分别发布，不修改对方的源码快照、模型或账本。Recovery 提供完整分步骤工作台；[Motion](motion/README.md)现提供本轮0.34m/±2m/s持续任务的裸源码与公共提交入口，Jump尚未加入。
已完成人工工作台：/manual_train/recovery。

你主要修改两个文件：

settings.toml：训练模式、更新数、学习率、来源模型。
reward.py：奖励权重与计算。
人工开启实验：

bash


cd /home/kellen/wheel_leg_native_train/manual_train/recovery
./prepare.sh --write
./train.sh
./train.sh --run --approve "本人批准此人工实验按声明预算使用GPU0共享"
播放已整理的模型副本：

bash


./play.sh --pose swing --run
./play.sh --pose standing --run
保留原来的网格地板、灯光和视角。另有 status.sh 查看信息、stop.sh --confirm 请求停止自己的人工实验。

每次准备都会冻结独立源码和奖励，后续人工修改不会影响已准备实验或当前 Codex 任务。默认新建 Critic/Adam，仅继承 Actor，暂不提供完整状态续训。

已新增工作台脚本、模型身份目录及两个测试文件，更新 README、TOOL_INDEX、WORKFLOW、ARCHITECTURE、STATUS。三种训练模式各 28 项冻结测试通过，工作台相关测试 6 项通过；共享源码 SHA 未变。

本轮未启动新训练或 GUI。模型目录是固定候选副本，尚不能称为已通过完整自主起身的策略。完整命令见 TOOL_INDEX。