# Motion原地姿态教学、镜像对称与Progress候选

## 本轮依据及授权

用户GUI观察20_46 update50初期平稳随后滑倒，要求尝试Motion原地姿态蒸馏、双腿对称，并考虑0~1 Progress。承接会话明确后续训练授权，执行镜像教学的CPU/GPU离线工程、蒸馏与独立PPO0验证；不并行追加PPO、不改历史run和旧接口。先分开对称目标和Progress变量，避免无法解释哪项有效。

20_46已formal300结束，专项update50约5.02秒后倒、有效保持前缀2.52秒，完整10秒0/24。原BC和新蒸馏/PPO学生均尚未accepted。Motion B250正常站姿已在同限位USD多次8/8通过，固定teacherSHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e。

## 实际Motion站姿不是严格镜像

native实体关节镜像定义e_hip=q_Lhip+q_Rhip，e_active=q_Lactive−q_Ractive，不是左右q数值相等。已核验normal标签均值绝对误差hip.14107rad、active.10662rad，P95 .14270/.10786rad。成功B250实际q误差约.14644/.14606rad；PPO50全episode实际q误差约.30647/.25392rad、PPO300 .46479/.42686rad。时窗不同且含倾倒，不能把差异直接当因果；说明不能一边要求原样复制teacher、一边声称严格镜像目标与teacher完全相同。

原始source/teacher/trace具名schema与SHA保留于isolated/recovery_stationary_mirror_delivery_20261011/symmetry_audit.json。关节镜像误差不等于轮心错位，轮差速不是机械腿对称的等价量。

## 新离线目标候选及蒸馏

仅normal_standing阶段四腿目标做最小成对L2投影：a=(Lhip−Rhip)/2，b=(Lactive+Ractive)/2，目标[a,b,−a,b]。轮目标完全保留teacher。保存original_normal_teacher_labels.pt及SHA；投影目标明确标为未物理验证的新参考，不伪装成实际teacher执行动作。旧Swing四阶段标签不改；pre-action输入/上一实际teacher执行目标/episode划分不改，不伪造新轨迹的状态或缓存。

投影四腿目标全部位于学生±1.5rad包络及当前USD主动hip±3.1rad/active±2.6rad实际限位内；这不保证闭链动态分支和接触行为，仍需物理验证。无运行时投影/强制相等/隐藏偏置，策略自身学习镜像目标，预测仍可有误差。

新数据isolated/recovery_standing_mirror_teacher_data_20261011，standing_priority_reset_v2：50%normal＋原Swing四阶段各12.5%；normal内部首动作25%、下一19步50%、余保持25%。仍按episode平衡，复用原完整episode train/val/test，新增物理样本0。源Actor沿用原BC SHA7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470，31D/40D物理/模型不变，新BC Adam、新Critic不由BC优化、std不更改。没有用失败latest300接棒。

实际5000离线optimizer steps，17.7182秒，设备auto此次选择cuda:0（显式物理GPU0共享核验，未停止其他任务），best4800。best_validation.pt路径isolated/recovery_standing_mirror_distilled_20261011，SHA5bdaf8dfcd02afb55dbfc7aa84102f9145c3aa568a5888461155a17891cd2abc。验证normal腿MAE .02534rad/P95 .03361、轮MAE .804rad_s/P95 .931；拟合预测hip/active镜像误差均值.05838/.04281rad、P95 .06074/.04423；标注投影为0但网络预测不严格0，不宣称完全对称或已站稳。保留BC5000实际消耗、原始teacher文件SHA和新dataset身份。

## Progress建议：尚未启用

pure CPU候选recovery_elapsed_progress_proposal_v1：Progress=clamp(受控动作前计时/2.5秒,0,1)，初始化期间0、实际episode reset清零，2.5秒后保持1。可由部署policy100Hz计数构造，不依赖仿真高度、接触、teacher ID、未来success；不会在.50秒指定切Motion。它是“已经过去多久”，不是“已完成多少动作”，学生失败时它也可能达到1。

若使用，需要独立显式接口版本32D Actor/41D Critic，保留旧31D/150D/1182D加载与行为，不原位改接口。不能让Actor以teacher分段ID或固定动作表获得答案。真正基于动作阶段的progress若依赖高度/力传感器，不满足目前仅IMU/关节部署条件；应先声明基于本体状态的识别逻辑及可复现误差，不能伪造高度观测。

Progress可能帮助区分相近姿态处于不同起身时序，也可能学成时间脚本而降低扰动适应，当前未被验证。此次仅实现纯函数/契约和测试，不进入采样、模型、训练或GUI，不与镜像试验叠加。以后若走32D，应绑定迁移方法（第31输入新增权重初始0，先证明0进度行为等价）及新数据/spec，不将CPU提案标记运行接通。

## 测试和物理验证

5项镜像投影/进度/真实数据标签保持测试通过；冻结PORTABLE17通过；全CPU860passed/22errors，与修改前22项fixture ID完全相同，生产SHA校验不放宽。真实数据回归核验旧Swing标签/轮标签、normal上一执行目标输入和episode split不变。

22_28独立spec/run/ledger，4组×8评分env=32episode、64仿真env：新镜像学生normal、原BC normal、B250 normal对照、学生原生Swing回归。PPO/物理optimizer0，≤1800秒含清理/≤512MiB，GPU0显式shared，提交前session/UUID/CUDA/模型/source校验READY；公共supervisor执行一次有界PPO0，故障不自动重试。沿旧同协议固定入口.20秒＋10秒窗口，teacher别组运行不救场学生，能力分母不删。结果待终态追加。

源码新增students/standing_mirror.py、扩展scripts/prepare_recovery_standing_distillation.py --mirror-targets；测试test_student_mirror_progress.py及test_recovery_standing_distillation.py；本文、STATUS、Recovery计划、TOOL_INDEX、ARCHITECTURE维护相应边界。本轮没有修改动作控制器/PD/限矩、原USD、旧checkpoint、历史run/spec/ledger，也不commit/push。


## 实际闭环终态

22_28 COMPLETED，无工程failure，32评分episode/76.9168秒，PPO/物理optimizer0，BC实际5000步。新镜像学生normal入口8/8但保持0/8，约.56秒后倾角终止；实际q镜像MAE hip.02622rad、active.06449rad，较B250全段.14644/.14606更对称，仍没有站稳。原BC normal约.37秒倒0/8，B250正常8/8，镜像学生Swing约.35秒倾角终止0/8。保持完整分母，评估/trace SHA和离线重评分匹配。

相比未镜像reset优先BC normal约1.17秒，新候选更早倾倒，因此本轮不采用为新站立来源，也不从它续PPO。已有专项PPO50作为当前站立实验保留对象仍在，未accepted。标签镜像改善不等于闭环支撑改善，不能宣布严格对称物理姿态或“对称有害”：它只是一次修改teacher目标的受控候选，wheel/body支点、闭链动态反馈不等同于关节符号平均。

下一建议先保留真实B250站立反馈与执行目标，不再直接改成未经验证的对称标签；若研究对称，优先独立弱镜像成本并共同评估支撑/保持，不能为对称刷分。复杂Swing起身的elapsed_progress可作为独立32D版本实验，但只CPU设计、没有改变本次31D或训练。未启动新PPO、Progress模型或额外补采，无自动重试。
