# 浙江大学Recovery知识迁移：低位支点构造与收腿进展

## 一手资料核验

原帖：[RM2026串联腿机器人建模与控制开源，浙江大学HelloWorld战队](https://bbs.robomaster.com/article/1946523?source=4)。页面作者烟霞志，正文链接MATLAB仿真仓库https://github.com/Particlela/WBR_simulation，附件包含在机控制PDF及实机演示视频；该仓库未进一步审计，不能称含完整嵌入式Recovery源码。

本地/home/kellen/下载/【RM2026-串联腿机器人建模与控制开源】浙江大学-HelloWorld战队.zip与下载论坛附件均85262871字节，MD5同为91368964ee1331941353a526f35d81a4。原PDF第13.6节（页35–38）已读，第37页图9已渲染核验；轮力矩分派见页47。摘录主要逻辑与原PDF一致。附件视频名为台阶、飞坡、高地演示，尚未逐段观看；不能称已单独核验Swing倒地恢复视频。

正文注明CC BY-NC-SA4.0及非商用交流，方案为本项目分析与机制迁移，不复制大段原文。文档和视频提供该团队控制工程/实机背景；机器人几何、传感器、弹簧补偿、LQR和闭链映射须分别核验，不直接套参数。原PDF也提及五连杆映射，标题“串联腿”不意味着所有机构完全不同或完全等价。

来源身份已确认，替代此前“缺原链接、浙江大学出处未确认”的历史描述；实机效果按用户亲眼观察和附件演示分别注明，不宣称保证本USD学习成功。provenance及PDF副本在isolated/recovery_rm_forum_reference_20261008；用户下载原包只读未改。

## 当前新的判断

暂停继续增lambda/.03分支：虽有实际非零约9%辅助梯度，Swing仍0/8、peak约.232米。mean裁剪依旧存在，但不能一直仅用裁剪指标定义学习目标。

优先借鉴原Recovery的任务分解：已有Swing预摆初态→构造向下支点/收短腿→自主抬升→同actor水平保持。它是奖励/诊断的阶段语义，不是开环动作指令、动作bias、teacher交接或新的控制层；不引入虚拟腿控制映射/LQR/补偿/轮力矩硬置零。

真实B25 geometry env0：Swing首控制hip→mainwheel距离约.3742/.3760米，失败末仍约.3759/.3760米；相对重力向下的连线夹角由约1.274/1.278rad恶化至2.103/1.358rad。成功DrawBack首控制长度约.1526/.1500米、夹角约.770/.751rad，完整保持后长度约.376米、夹角约.18/.14rad。因此“最短腿永久最好”错误；更具体的缺口是低位没有探索收短并重排支点。

这些长度是本USD真实hip-anchor到轮心距离，角度是向量与重力的夹角，不冒称原PDF虚拟腿参数或整体COM在轮轴上方。没有将轮中心当接触点/支撑多边形，也不称这些相关性已经证明因果。

## 首选新方案：只增加低位几何进展塑形

先CPU核准全部8env、各phase及初态的几何分布/闭链分支，测量真实DrawBack构型可达长度范围；不要按原文.10米强行构造目标。本轮约.15米仅是可溯源目标尺度候选，具体范围由全样本核算后冻结。

每侧v_i=wheel_center_root−hip_anchor_root，L_i=||v_i||，d=gravity_body/||gravity_body||。
定义bounded支点距离指标：
C(s)=mean_i[0.5*clamp((L_i−L_D)/(L_S−L_D),0,1)^2 + 0.5*(1−clamp(v_i·d/L_i,−1,1))/2]。
L_S拟由真实Swing约.375米读回，L_D拟由真实DrawBack约.15米读回，均为显式冻结几何参数。短腿但朝上仍有方向成本；指向下但过长仍有收腿距离，双腿均纳入，避免只一侧刷分。系数.5/.5是候选，未确认为最优或力学CLF。

只对真实Swing受控、尚未first-entry样本使用低位gate：g(h)=1在h≤.22米，h≥.30米为0，中间平滑。Phi(s)=−g(h)*C(s)。候选附加项为beta*[gamma*Phi(s_next)−Phi(s_pre)]，gamma与PPO.99一致，terminal/failure/timeout边界必须明确：真正吸收terminal后Phi=0，timeout根据bootstrap语义处理，初始化样本mask0，不在reset后新episode取Phi_next。入口后关闭也必须作为显式状态语义，不能事后截掉负项；各条件纳入定义，先验证边界再称PBRS形式。

该项只奖励状态接近低位支撑构型的过程，不永久给短腿驻留bonus，站起后不要求回到.15米。phi跨终止释放的正项可能混淆失败代价，必须离线显示完整discounted return和terminal贡献；PBRS正确端点处理不凭空新增成功探索方向，不能宣称消除局部最优或保证收敛。若严格potential差分在本时域没有提供可辨别信号，应停在设计审核，不自动改成只给正进展；改目标型几何reward必须另声明它改变目标偏好。

beta未决定：先对已保存Swing/DrawBack/R0轨迹计算逐步raw/weighted/总return，绘制收腿/方向/heightgate贡献，独立CPU合成有利进展/无进展/震荡/失败terminal/成功entry/timeout用例。核算失去支撑、抬升、终止项不能被几何reward压制。奖励依赖明确runtime数据但actor保持150D，不把privileged奖励量悄悄输入actor。

## 实施顺序与单变量边界

1. 原PDF语义→本USD具名几何量CPU对齐，支持closed-chain支路/零长度/nonfinite安全，按schema读取而非裸列号。保留原动作/限矩，不通过geometry reward绕过关节安全。
2. 给出Phi/terminal/timeout/phase接口与反事实量级，选一个固定beta；完成不改变RNG/采样、episode边界、dt和once项测试。progress-difference单位须明示，不套连续per-second项重复乘dt。
3. 准备新奖励版本、新spec/run/ledger，来源认证B25，固定Swing26/DrawBack25/R013，mean辅助完全关闭（不得继承.03），std/Adam/控制/150D/gate保持。新reward接线用公共trainer/supervisor，无架构重构。
4. source/PPO0验证新reward可测量和初始化，smoke必须真实事件+reward激活，未学会Swing不是拒绝工程smoke理由。短训建议smoke10/formal≤25、10/25三组验收，但只有完成系数/接口审核后才声明预算和申请新运行授权；本次用户授权研究和写文档，不启动这些阶段。
5. 同checkpoint保留DrawBack/R0完整10秒并改善Swingentry/hold；只腿更短、角度更直/总reward高或轮速小都不能accepted。失败/退化保持B25，不能从new25继续多因素叠加。

## 轮矩先验是独立后备

原PDFRecovery轮矩为0，这是传统明确模式控制，不等于wheel speed target0（后者常构成制动），也不等于允许轮矩增量。RL仅可独立检验弱低位physical clipped wheel-effort成本；此前−.1/秒量级继续保留，几何首块不叠加。它在饱和区可能无法区分rawmean，不能默认靠加大成本解开当前裁剪。

不在低位直接要求pitch0或强raw关节对称，以免抑制原文允许的转姿/摆腿。左右几何/接触仅报告，严格水平验收仍是原协议入口后。

## 本轮交付与限制

只读论坛、本地附件/PDF、当前已保存轨迹，未模拟/PPO/optimizer，未改checkpoint/旧run/spec/ledger。保存原文来源证据、更新本报告及Recovery计划/STATUS/开源文档来源说明。下一具体工作是CPU几何/奖励量级审核，不是继续lambda调参或自动启动新训练。

## 2026-10-09 CPU审核后的修正

严格PBRS吸收端点完整折扣和只依赖初始Phi，本轮合成/实测核算确认；该形式可能改善价值学习，但不能称新增收腿优先目标。当前不准备PBRS运行。下一有界几何目标cost需另声明其改变奖励偏好，并先检查早终止/门控/抬升权衡，详见RECOVERY_SUPPORT_GEOMETRY_AUDIT_20261009.md。原文上述势能方案保留为被审核候选，不作为已运行配方。

## 2026-10-09目标项审核后状态

负几何cost存在height gate逃逸/早死权衡；双侧hard-product质量bonus真实Swing全0，不能产生需要的进展信号。两者暂不进入runtime。下一单公式设计要求真实Swing区间平滑有辨别力并核准短腿驻留/阶段奖励语义，见RECOVERY_GEOMETRY_TARGET_AUDIT_20261009.md；不扩大训练架构。
