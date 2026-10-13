# 多技能路线图：第一阶段起身＋基础运动

长期目标统一以[PROJECT_MASTER_PLAN](../PROJECT_MASTER_PLAN.md)为准：首版Motion/Recovery/Jump，不预建独立Traverse，越障先规划Motion与Jump组合。以下旧路线与1182D记录属历史导航。

本轮MCU v2 31D/40D小学生CPUBC/ONNX/PPO0完成：Recovery0/32、MotionZero入口8/8保持0/8；教师32/32与8/8。Jump仅接口。见[当前交付](MCU_V2_STUDENT_COMPLETED_REVIEW_20261011.md)。

有效日期2026-10-11。本文件区分已接线、待物理验证与规划，不登记运行授权。

| 类别 | 职责 | 当前状态 |
|---|---|---|
| Motion | 站稳、前后直线高低速、自转、行进转弯、主动内倾 | 原B250及已有证据保留；接管候选单独训练、单独认证；±4m/s/±4rad/s未认证 |
| Recovery | 新学生全程Swing起身并保持，随后接Motion驾驶 | B50准备＋B250抬升/保持分段教师，31成功episode BC完成；闭环未测 |
| Jump | 起跳、腾空、落地、收稳 | 规划，第一版不训练；小/大跳优先用同一策略幅度命令 |
| Traverse（历史分类） | 接触式越障与自动上台阶 | 总纲首版不设独立模型，由Motion/Jump路线规划 |

一个类别可包含独立训练、分别认证的候选版本。高低速不预先拆大量模型。首版允许独立Motion接管候选：Recovery→receiver→原Motion，原B250保留；接管零速通过不表示替换全部驾驶能力。

新版目标状态机：合法Swing初始化→RecoveryStudent全程起身及保持→MotionStudent基础运动。旧Recovery→receiver→Motion组合保留为历史路线与教师对照，非本轮训练目标。任一周期只有一个执行策略；transition记录control owner、actor_valid、输入/命令/输出/实际目标、阶段计时与切换原因。不能切换时reset/清速度/托举/沉降，不混归一化动作或隐藏补偿；速度和历史连续。

部署传感器只有IMU和关节位置/速度。无需固定朝向横移；侧翻、仰翻恢复不纳入第一版。仿真高度、世界速度、接触等评价量不自动成为部署观测。状态触发器须以后验证可测代理，不将单个成功时刻或critic值当成功概率。

接口版本：legacy150D保留；multiskill_student_v1已实现固定1182D Actor（51帧本体＋valid＋skill命令）、1191D privileged Critic、six-channel bounded mean Gaussian及1.5rad/100rad/s物理解码。两个独立256→128→64 ELU学生、新Critic/new Adam；Motion目前只零命令预训练，不声称迁移±4、高速yaw或压弯。小/大跳的米单位命令只是保留字段。

第一阶段交付：版本接口、具名pre-action教师数据、31成功组合分阶段BC、学生独立runtime/公共PPO0与播放分派、未来ControlledPPO装配接口（未提交在线训练）。旧组合近邻窗口.50秒三yaw24/24，其余前缀失败；不将31episode当31种恢复状态。

后续次序：可靠组合恢复和接回基础运动→独立扰动/可部署触发复验→Motion速度/yaw扩展和转弯内倾→Traverse与Jump分别验证。晋级依据独立行为证据，不按总reward或某单一几何量决定。
