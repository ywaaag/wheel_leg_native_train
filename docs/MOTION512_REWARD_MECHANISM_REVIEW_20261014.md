# Motion512退化机制：奖励、PPO与旧150D方法

本轮仅离线读源码、冻结spec、metrics和已保存完整评估；没有仿真、训练或改配方。原始数值与推导：`artifacts/2026_10_14-18_33__motion512_terminal_review/reward_mechanism_audit.json`。

## 已有改善及其局限

update100的+1保持MAE从来源0.8725下降至0.3524，方向仍正确；但零共同偏置0.3476→1.6406，−1误差1.7855→3.0595。双向增益±0.5由−0.309→−0.762，±1由−0.329→−0.706，未学会正命令增速/负命令减速的响应关系。source和u100均40/40生存，因此确定性评估并没有新增生存通过数。训练随机rollout后段更多normal timeout，表示探索中的生存有改善，不能直接与来源确定性存活作因果比较。

训练窗口6–25、76–100、176–200平均每步reward分别0.06780、0.06085、0.02695；linear tracking raw约0.371、0.381、0.185；height0.896、0.797、0.466；upright0.515、0.418、0.221；leg_balance成本0.016、0.261、0.960。不同窗口状态/phase/episode分布不同，不是同命令稳态对照，但没有总reward持续上升的证据。训练长保持占比后段约85.9%，不能把缺保持段当作唯一解释。

## 奖励设计短板

腿长差bounded_cost=x²/(1+x²)、尺度0.02m、权重−0.15：1cm成本0.030、2cm0.075、10cm0.1442、13.5cm0.1468、20cm0.1485。严重形变仍只能损失0.15density（每step约0.0015），且边际区分不断减弱。mirror和wheel成本上限0.2/0.3；相比linear tracking4、yaw2、height2，这些几何约束偏弱。gate不会反向成为PPO奖励，Critic知道状态也不会自动强化这些目标。

pitch/roll用一个合并饱和函数，pitch≈.225已削弱局部区分；没有独立摆角差reward。左右主动关节镜像不等于真实轮心/腿长几何。任务门槛要求姿态不劣于来源，但reward只给软约束，未严格表达该保持目标。

独立yaw/lateral正项允许速度失败时仍获得相应奖励；不能将这些低变化正项直接解释成Actor错误梯度，但会改变任务return背景与Critic拟合。失败step dense归零、无独立失败event损失，也不是天然等价于长期站稳目标。应比较失败前return和真实advantage，不能直接断言它导致了当前漂移。

linear Gaussian+Huber的误差方向、dt一次经CPU解析检查正确：目标两侧状态误差导数均指向减误差，不奖励反向行驶；但状态导数不等于非可微仿真中的Actor梯度。没有完整on-policy旧value/log_prob/return/minibatch/optimizer capture，因此真实历史PPO步为何使同命令行为恶化仍UNKNOWN。当前不能用“梯度有限/CPU测试通过”证明PPO优化方向或整体收敛。

## 其他待验证机制

来源是Recovery Actor映射Motion one-hot，保住近似原行为却本来具有负速度增益；Actor没有直接vx及history。轮速/IMU可以间接提供信息，但轮滑移、倾斜和不同命令下存在部分可观测混淆，privileged Critic不能消除Actor信息缺口。新Critic/Adam、前5次warmup在reward改动后是否足够尚UNKNOWN。512env改变batch与每次更新样本量，没有同源等样本64/512对照，不能归因于env数；global normalization也没有因果A/B证据。

另确认一个统计问题：RolloutCounts episode duration读取state[:,0]即Recovery FSM age，后段正常timeout显示约1.2秒不是30秒真实受控episode时长。timeout来自实际Episode.steps>=3000；duration应未来改成reset前受控秒数，旧数据保留。这个日志错误不能直接解释Actor退化。

## 可以借鉴150D，但不照搬

旧B250基于已具备运动能力的150D来源、历史帧、完整Actor/Critic/Adam恢复、小步LR；0/±0.5使用0.04窄核、±1使用1.0宽核，明确旧能力保留。它的spec虽然写separate/per-command，已保存domain_reward及复盘明确实际combined tracking/global normalization，不能按声明复制一个未执行方案。

31D本轮同时不同于旧方案的来源技能、history、腿动作语义/scale（1.5对旧0.5）、Critic/Adam和512env；旧权重收益不可独立归因。最值得借鉴的是“先得到正确的双向Actor，再小步保留已有能力”，而不是依靠一个强生存Recovery来源自然学会Motion。

保留31D的可选路线：用已验证150D Motion策略生成同协议Motion teacher样本，按实际物理腿目标/轮速目标转换为31D的action标签，训练31D Actor，独立核验正负响应后再PPO。旧history输入与新当前帧存在信息差，蒸馏不保证全部保留；尺度/坐标必须具名核验，不能直接载150D权重或生硬截断输入，也不改变执行器。该路线需要新准备/采样授权，本轮没有执行。

## 唯一优先下一步

先完成离线reward/post-state与pre-action command核对、同一冻结目标的CPU真实PPO方向/初始化重放，并为下一次最小受控诊断保存一次真实on-policy update capture。历史capture不存在的字段明确UNKNOWN。若排除接线，再在独立版本里只改几何成本尾部（同尺度/权重改Huber）做有界对照，或单独批准Motion teacher蒸馏；不要一次把reward、Actor输入、env数、课程和优化器全部改掉。当前200轮表现是持续恶化、没有目标收敛证据，继续原配方1800轮缺乏依据。
