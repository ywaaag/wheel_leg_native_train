# 25D Motion学生：停止复测与下一PPO设计

用户要求剩余感觉无需测试、思考学生PPO及Critic super输入。只停止本轮exact-ID evaluator（SIGTERM，核对pid/attempt/cmd/output），未停止其他任务。终态STOPPED_BOUNDED，attempt82f01f3a83ce44e7a44a3120eb7c5bc0，monitor结算1546.4324秒，PPO/optimizer0。原terminal failure.reason空字符串，是信号中断记录的现有局限；本报告补充原因“用户明确停止剩余评估”，不改历史terminal/ledger。完成7case/56评分episode：student0/±.5/+1均0/8、约2.08秒tilt；teacher0/±.5均8/8。+1teacher中断项没有完整结果，不当NOT_RUN能力失败，其余student-1/teacher-1 NOT_RUN；未发生新的运行故障重试。

读取原teacher/student零速轨迹：学生pre-action/mean/clip/previous/q/dq对应误差0或<1.8e-8，教师零速8/8。env0在.5s与1s高度/倾角接近教师，姿态差>.05rad第一次约1.54s；腿请求目标差>.05rad约1.98s；未出现轮请求目标差>5rad/s。2.08s学生高度.24265m、tilt.95757rad，teacher约.3523m/.0343rad。对比为相同policy index，不同后续物理状态，不能称唯一因果。非零组失败前命令只有很小ramp，稳定非零运动NOT_REACHED。

## 最小下一设计（尚未实现在线训练、未授权、未提交）

固定当前学生来源isolated/motion_frame25_actual034_bc_20261013/best_validation.pt，SHAe86b7922d099f2519b1f0c00959399b40c9848add9be32fcf39ec3f6a2df23ab。不继续重复BC、不增加历史/GRU、不切回teacher、不做运行时filter/补偿，不量化。Actor25→128→64→32→6ELU/最后linear mean与本次BC完全一致，不能加载时擅自tanh导致已学mean变化。Gaussian采样坐标及envclip明确，rawaction/logprob对应自己的样本。

“super输入”暂按asymmetric Actor/Critic的训练特权信息解释。Actor原25D部署信号不变；Critic新34D：Actor25＋高度1＋真实native线速度3＋轮合力/100两维＋受控/入口确认/保持计时三维。native线速度沿原[-bodyZ,-bodyX,+bodyY]、m/s；高度m，计时秒与显式尺度均需recipe固定；body gyro仍原Actor字段，不能重复当新传感器信息。Critic34→256→128→64→1ELU，新初始化不继承teacher/BC Critic、Adam或RNG。Critic不部署。特权输入必须真正进入网络，不只storage metadata。

优先先训原生normal零命令站立，heightcommand.34，64zero，episode覆盖真实启动/稳定/30秒完整原协议；这不是Swing Recovery。用学生亲自执行的on-policy状态纠正teacher数据外的闭环偏离。原机械资产/PD/1-5-10ms/限矩/.5rad-100rad/s不变，root.40原初始化不擅改；仍无实机.36全过程认证。

Reward以05_39来源实际冻结Motion有效配方为基线：upright2/height2（宽.06）/combined velocitytracking8（zero denominator.04）/contact.5/effort-.02/actiondelta-.01（保留原wheel physical scaling）/jointmargin-.05/terminal-1，dt.01一次。不得误继承Recovery零reward或DrawBack引导。首轮不同时加新对称/时间/轮平滑惩罚，以免无法区分PPO学习与新reward作用。对称指标继续记录，本轮零速通过不等于最终严格对称认证。

建议固定物理探索leg.05rad、wheel2rad/s→normalized [.1,.1,.02,.1,.1,.02]，std先固定，不在mean变化之外同时优化探索。PPO LR3e-5、64×128、epochs/minibatches4/4、gamma/lambda.99/.95、clip.2、value.5、entropy.001、gradnorm1；前5更新只Critic，之后Actor/Critic同时更新；BC0，source Actor不变，新Critic/Adam。empty control mask参数gradNone/Adam不推动Actor；正常controlled failure最后一步保留；不删除真实步骤重算GAE。高度/速度/接触与计时只进入Critic/reward/gate，不进入Actor。

## 实现与执行条件

现frame25_probe只允许PPO0，不能删除拒绝条件直接训练。需新明确recipe和训练接口分派，复用public supervisor→CommandEnv→共享训练循环→ControlledPPO；新actor/critic键25/34，strict model loading、checkpoint/GUI/evaluator一致。ControlledPPO本为Recovery适配，Motion使用时必须版本化并验证控制元数据语义，不能沿用receiver/teacher mask。critic输入post/pre时序、末观测timeoutbootstrap、episode跨rollout与评估后reset缓存都需真实调用链CPU测试。

建议待批准预算：source学生零速8＋teacher8；smoke25＋formal300，共325更新/2662400samples；全链最多14400秒/2GiB，formal25/100/200/300评估零速，末尾将候选与来源进行0/±.5/±1回归。smoke不要求先站稳，检查nonzero reward、critic warmup、Actor实际更新、reset/storage/save；formal独立从BC Actor开始，不继承smoke末权重。不要据reward或latest选best：固定完整窗口通过数、未通过时持续有效保持、姿态/速度/触限，来源保留。预算与case总数在最终声明准备时固定，不登记旧无限训练额度。

本用户消息是要求停止与思考，不登记新PPO额度。现在仅有此设计文档，不能称公共在线链已接通、spec可运行或PPO已启动。下一交付是实现并验证25Actor/34Critic真实训练路径，再集中确认新运行范围。Critic信息更全可减小advantage误估，不能保证无历史Actor足够；若PPO仍失败，根据早期偏离及有界学习结果再单变量研究短历史/输入，不预先回到150/1182大网络。
