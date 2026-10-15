# 25D Motion学生＋34D特权Critic：真实PPO链准备

本轮用户同意继续工程。已实现/CPU验证/发布独立声明；未启动Isaac、GUI、新采样或在线PPO。CPU optimizer测试仅更新内存副本，BC学生源和教师文件只读。此任务是Motion正常零速站立，不是Swing Recovery；其他worker dirty changes保持。

## 接通的路径

manual_train/motion/frame25_ppo_preparation_20261013/engine/src为独立完整public bundle，supervisor→source_eval/smoke/formal→CommandEnv→原reward→ControlledPPO→checkpoint→原评分器/GUI模型工厂。没有第二套trainer/physics/owner。最终使用16_54声明；16_48是未运行的中间CPU声明，两者没有attempt。

输入显式分派：物理环境仍按legacy150D契约产生policy25/history125，以便原CommandEnv/PD和旧模型不变；spec.actor_interface_version=motion_frame25_distilled_v1及frame25_training=motion_frame25_asymmetric_ppo_v1严格绑定新Actor25/新Critic34。Actor只读policy25，不读history或frame25_critic。Critic34＝当前25＋高度m1＋native线速度m/s3＋轮合力N/100两维＋真实episode受控秒/30、连续入口确认秒/.2、首次确认后的保持秒/10三维。native速度[-bodyZ,-bodyX,+bodyY]，root高度仍原机体坐标原点；不是COM或实机高度感知。Actor不输入这些特权字段，Critic不部署。

Actor25→128→64→32→6ELU/linear mean（不擅自改BC为tanh），Critic34→256→128→64→1ELU。普通Gaussian mean坐标采样，环境clip另行执行，没有squash Jacobian；rawaction/logprob真实保存。固定std归一化[.1,.1,.02,.1,.1,.02]＝腿.05rad/轮2rad/s，log_std不优化；部署仅mean。原.5rad/100rad/s/PD60-2-1/1-5-10ms/40-5.5Nm/USD/Plane不变。

BC来源isolated/motion_frame25_actual034_bc_20261013/best_validation.pt，SHAe86b7922d099f2519b1f0c00959399b40c9848add9be32fcf39ec3f6a2df23ab。source_state只加载其Actor，显式检查接口/网络/角色/teacher/dataset/manifest；prefix映射仅把Sequential参数名转换为mlp名，无参数数值变换。Critic、PPO Adam和声明RNG独立初始化，BCAdam不载入。smoke/formal各独立从该BC Actor开始，前5更新Critic-only，后续真实更新Actor/Critic，BC0。

所有原生Motion步骤都是policy真实控制；没有初始化零力矩或teacher前缀，pre-action mask为true，受控失败末步保留。继续ControlledPPO原时间轴GAE；empty mask不更新Actor/Adam；计时不因rollout更新清零，实际reset后按env局部重建。计时只提供Critic上下文，不是最终Certificate/不发额外成功奖。首次20个连续policy interval质量满足后确认，第21步才累加保持；相位不进Actor。评估后沿共享trainer原显式reset刷新obs/cache并单独计数，不把旧obs跨评估使用。

source_eval的8个首episode必须身份/分母/运行有效；普通tilt/task_failure允许继续学习，runtime fault/未知或不完整证据拒绝进入PPO。smoke仍需真实episode结束/Actor更新与公共wiring_certificate，不要求先学会站稳。没有恢复旧DrawBack/R0、teacher救场、硬对称或额外补偿。

## Reward与验收

直接复用05_39 Motion来源有效零速配方：upright2/height2、heightwidth.06、combined velocitytracking8/zero denominator.04/yaw denominator.09、contact.5/effort-.02/actiondelta-.01（wheel factor100/6，保留物理成本）/jointmargin-.05/terminal-1，连续dt.01一次。未继承零reward学生PPO0，不叠加新对称/phase/BC奖励。actual postphysics/prereset reward由原CommandEnv提供，真实CPU方法执行验证sum(weighted)*dt与terminal-1。

先只训64zero/heightcommand.34；原Motion原生root.40初始化不擅改。每25次更新评估一次零速固定10–20秒保持窗，完整轨迹只在25/100/200/300保留，其余按原summary存储。原motion_standing034_v1、保持.32–.36，旧zero vx.5等阈值不变；通过不等于严格对称、实机峰高≤.36或±1运动全部保留。非零运动不作为本次零速课程晋级前置，也未在线训练；zero能力通过后另准备完整运动回归，不能把本次BC教学当运动证书。

## 独立声明与待批准预算

configs/experiments/2026_10_13-16_54__motion_frame25_asymmetric_ppo_from_actual_bc/spec.json；budget.json独立UNAUTHORIZED，attempts={}。

source_eval≤900秒/8评分episode；smoke25≤1500秒/204800samples；formal300≤11700秒/2457600samples；合计最多325PPO更新/2662400samples，整链14400秒含清理，新增产物2GiB（runtime reserve128MiB），GPU0shared，不抢占不换卡不重试不续长训。formal每25更新零速8环境，共96评分episode；smoke末8，source8，当前声明共112。来源0/8不阻断工程有效的PPO。预算、授权、在线更新与CPU测试分开记账。

spec登记后仍需新授权。GPU UUID/session/resource/source/module和ledger必须在reserve前重新核验；本轮未查询或占用GPU。public supervisor/stand_chain已有monitor管预算、保存、退出与结算；后台只做一次握手。运行命令只维护TOOL_INDEX。

## 修改与验证

新增motion_course/frame25_ppo.py：显式recipe/Actor/Critic/固定std/source与候选检查/纯critic编码/计时器/存储边界。增量公共module factory/config/preflight/checkpoint_input/play/evaluator；runtime.configure/env挂接真实34D与mask、reset计时；共享train只改明确flag分支，source Actor-only、新Critic/Adam、warmup、ControlledPPO、轻量mask/梯度、checkpoint全部路径绑定interface/recipe/dataset/manifest/asset/spec/source代码SHA；stand_chain source工程有效判定与整链时间上限。

CPU真实模型+reward+storage+optimizer+计时/reset等8项，新专项与旧ControlledPPO/诊断合计18passed；实际train._snapshot并验证冻结逐module SHA，冻结PORTABLE18passed。CPU optimizer内存副本证明：BC mean逐值一致、特权只影响Critic、warmup不动Actor/Actor Adam、warmup后Actor更新且std不变、empty mask Actor/momentum不动、Gaussian logprob和raw action对应。

全量共享当前基线943pass/8skip/22error（逐ID证书fixture源码root绑定错误）；本bundle与未加入本轮功能的父bundle各933pass/8skip/10fail/22error，全部32个ID相同。额外10项分别MCU公共preflight、Motion absolute plan、Recovery frozen test files、handoff plan、student motion probe、3个checkpoint绑定、standing034 smoke、temporal receipt，固定shared root或副本无tests目录。完整ID及具体原因保留full_regression_comparison.json和3份原始pytest日志。未放宽SHA/跳过关键测试；实际新decl公开preflight另外验证通过。

最终零写plan cpu_valid=true/READY_NEEDS_AUTH，仅AUTHORIZATION_MISSING，files_written0。未创建训练attempt或runtime产物；接口工程通过不是行为通过。

## 当前结论

已具备申请一个有界零速PPO实验的工程条件，物理初始化/输入34D实际运行与smoke证书仍需下一次授权内验证。Critic特权可以改进value/advantage估计，不保证25D Actor充分；若PPO仍失败，再根据学生闭环最早偏离研究一个可部署的输入或更新变量，不自动回150D/1182D、GRU或改变PD。

## 授权提交与工程停止（2026-10-13）

用户授权325更新后公共登记16_54，submit health发现仍按legacy要求mlp名/已训练Critic/asset/update，提交前拒绝、attempts={}。独立engine_healthfix补显式BC metadata与数据/五组actual034 teacher SHA资产核验，19CPU/19冻结通过。新17_06声明消费同一用户授权代替未启动16_54；submission READY，GPU0/shared/UUID一致，可用显存充足，单次握手worker已提交但source_eval首物理step FAILED。exactchain05ba0f049dfb46de86158b85955114bd，source attempt e57e8795d1834c5ca1ef5631707fbe0d。实际冻结与CPU逐SHA一致。

根因是新增Critic计时入口eligible将closure_each真实[N,4]直接与[N]布尔量相与；CPU原fixture错误只用[N]，漏掉runtime shape。source_eval wall4.8408秒/全链7.7111秒，PPO0/samples0，source评分无完整结果，smoke/formal NOT_RUN。旧FAILED/spec/ledger/frozen源码不改。

已独立engine_closurefix仅修复闭链四项all(-1)，真实runtime方法CPUfixture改[N,4]并添加单个闭链故障拒绝计时回归；19CPU/19实际冻结通过。最终待重试声明17_09 motion_frame25_asymmetric_ppo_closurefix_from_bc，UNAUTHORIZED、无attempt，零写plan cpu_valid=true/READY_NEEDS_AUTH，仅缺授权。没有自动物理重试。本轮授权含“失败不自动重试”，所以需要用户明确允许此工程故障后的新attempt；原消耗保留，不能以原FAILED余额默认为授权。运行命令更新TOOL_INDEX，GPU/session/resource在新reserve前重核验。

## 修复后明确授权重试提交

用户明确“允许，并且修复”。17_09声明独立登记一次物理重试授权，budget原325update/2662400samples/14400秒/2GiB；旧17_06 FAILED和7.711秒消耗保持，未借旧attempt重启。source/dataset/asset与实际bundle逐SHA核验；public submit PASS/READY，GPU0 UUID-e704e7d4-2965-4712-9759-ba6b9910bd72、CUDA_VISIBLE_DEVICES0/shared实际生效，提交资源可用>32GiB，未停止其他任务。

public supervisor一次提交，chain attempt5f8ef06f4c0d46b4816c9b93386b4fe7；一次30秒有界握手SOURCE_EVAL，submitted=true/submission_verified=true，worker身份OK；formal_first_update_verified=false/started=false（不代表进程没提交，而是formal首更新未核验）。实际执行冻结与19passed CPU冻结模块逐SHA一致。receipt/actual identity/submit check保存在frame25_ppo_preparation_20261013/closurefix_*。从此交互不轮询，由既有owner执行source/smoke/formal与预算/保存/评估/结算；结束停止，故障不自动再重试，notifications disabled。
