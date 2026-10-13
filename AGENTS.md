# Codex 执行约束

本项目 `/home/kellen/wheel_leg_native_train`。以正确性、可追溯性和最小变更为先；中文简洁交付。

## 最短阅读链

1. 本文件：授权和不可变边界。
2. `README.md`：导航；`STATUS.md`：选择本次 Motion 或 Recovery 的证据入口。
3. 当前任务的 spec、ledger、manifest、冻结代码、terminal、原始 evaluation。
4. 按任务需要读 `TOOL_INDEX.md`（命令）、`WORKFLOW.md`（步骤）或 `ARCHITECTURE.md`（接线）。

设计/改变 reward、课程、选模或验收前读 `TRAINING_EXPERIENCE_REUSE.md`。
只有自主起身任务需要读 `docs/RECOVERY_STANDING_PLAN.md`。日期报告按证据需要读取，不作为必读链。
Markdown状态是导航快照；run原始证据优先。当前源码描述下一次执行，不解释旧run行为。

## 授权与文件边界

- 仅编辑本项目；保留dirty changes，不reset/clean。外部同事项目、Fudan、sim2sim、wheel_leg_training只读。
- 旧run/checkpoint/raw evaluation/spec/ledger和活动任务的冻结代码只读；不停止或改动其他任务。
- CPU/文档工作不授予仿真、GUI、采样、PPO、通知或续训权限。PPO0也是仿真，仍需明确授权。
- 新配方/课程/gate使用新spec、新run、独立ledger；exact-ID预留和结算，保留历史实际消耗。
- 旧授权、余额、已通过smoke、commit和终态通知均不能授权新运行。状态不明先核验，不重复提交。
- 物理GPU、UUID、逻辑CUDA映射和共享授权显式记录；不自动换GPU或抢占其他任务。
- 通知须有明确授权和实际负责人目标。接收事件不表示任务归属或接管授权。

## 冻结接口与代码规则

legacy150D保持25D frame＋5帧oldest-to-newest history；新版学生仅按显式版本 `multiskill_student_v1`／`multiskill_mcu_v2` 的固定字段/维数/尺度分派，不接受任意接口漂移。6D left-first实体腿位置/轮速目标；
Plane；physics/PD/policy为1/5/10ms；腿/轮40/5.5Nm。各实验动作尺度等以冻结spec为准。
训练、评估、播放共享CommandEnv；不加虚拟腿映射、LQR、补偿、static trim、隐藏控制或限矩增量。
纯domain只接收显式数据，不读文件/env/Isaac状态；CLI负责身份与文件读写。
AppLauncher先于Isaac runtime导入；资产模块根在依赖导入前核验并设置。

评估配置拆成scoring/schedule/storage；requested/effective/runtime读回分开。
缺字段或UNKNOWN不能通过gate/晋级；提前失败不缩短要求窗口。完整窗口与证书通过分别记录。
评估setup/reset/清理异常仍恢复actor模式、临时状态和RNG；清理错误不覆盖原始错误。
诊断默认关闭，只在显式更新启用，不改变采样RNG、分布缓存、梯度或optimizer。
来源/latest/best_new/best_overall/accepted分开；同一模型完整能力，不拼成功点。

## 提交与后台

解释器固定 `/home/kellen/anaconda3/envs/issaclab/bin/python`，共享源码为项目 `src/`。
先CPU测试、零写plan；公开提交只用supervisor。配置PASS不等于submit_ready；
当前session、GPU资源、身份、输出、账本和前置证书在reserve前再次核验。
formal须身份匹配的wiring_certificate，或经公共校验消费的版本化受限工程恢复证书。
恢复流程见WORKFLOW；证书不授予运行权限或新能力通过，不重置smoke额度或修改原FAILED。
事件型smoke必须覆盖真实事件，不能仅凭更新数。
source/smoke阶段提交不等于formal首更新；UNKNOWN握手报告started=false。

长训detached只做一次有界启动握手，然后结束交互。Codex不得循环查log/progress/metrics/PID/GPU，
也不得用sleep/wait、新watcher或子agent守候长训。既有monitor管预算、保存、评估、退出和结算。
明确授权的前台有界CPU验证/物理诊断评估可等待其自身完成，不属于长训轮询。
后台owner写hash匹配报告、report_ready并按at-most-once通知冻结负责人；未知投递不自动重发。
终态复盘只读一次；续训须新用户授权。旧PID或一次资源快照不证明当前存活/持续可用。

## 版本与交付

新实验名由domain.experiment_naming生成 `YYYY_M_D-HH_MM__purpose`（Asia/Shanghai），
config/run/spec名称一致，阶段子目录保留source_eval/smoke/formal；旧实验不重命名。
Git只处理明确本轮源码/测试/声明/文档；不force-add运行数据、资产、checkpoint或mutable ledger。
按明确路径stage，不git add .；commit/push仅按用户指令，提交不能重置预算或冒充历史源码。
公共工具命令只维护TOOL_INDEX，流程只维护WORKFLOW，结构只维护ARCHITECTURE，任务状态只维护STATUS。
新Recovery课程复用公共准备器；sampling/assessment与评分协议分开，新旧采样字段混用拒绝。
多文件声明含姿态库时核验完整发布标记和逐文件SHA后再授权。
固定family配额在config/preflight核验；冻结CPU仅执行PORTABLE测试，源码定位从实际导入模块出发。
sim2sim必须绑定actor坐标与COM测量语义；轨迹消费具名轴/schema，尺寸相同不能替代语义验证。
交付具体改动、验证、剩余证据与副作用；工程通过不代表行为通过。
