# Motion人工源码入口

当前首块：0.34m零速站立，分别约束髋/主动连杆镜像及两轮前后位置。Recovery31D为另一任务。

源码：standing034_alignment_engine_v5/src/native_stand，活动声明冻结SHA，修改另建副本。motion_course/alignment.py为四项成本，symmetry.py为实际joint/wheel固定窗证据，domain.py声明/选模/首块停止，io.py公共准备/授权/账本；command_v6/domain/reward.py/runtime/env.py真实计算和采样；train.py为公共PPO循环。旧v2/v3/v4与历史spec/run只读。

当前task：tasks/standing034_alignment_final_20261013。首块smoke25＋formal300/4h/2GiB，source/smoke/formal独立加载同一声明来源；新reward Actor/std继承、新Critic/Adam/RNG/warmup5。第一块完成停止并复盘，不自动接5000更新。只认证零速站立与对齐，驾驶±2或Recovery不能由此宣称通过。

保留Motion原USD/PD/限矩/legacy150D/.5rad腿/100rad/s轮，合法初态不硬改。heightcommand.34不代表完整启动或运动实际高度已≤.36；部署另验证。准确命令唯一在TOOL_INDEX，实际状态唯一在STATUS。
