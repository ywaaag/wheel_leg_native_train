# Recovery P2 B臂完成：早期候选完整通过

事件d9da6b8293caceaa2ace3598报告SHA已核对，既有CLI确认reviewed。
B链COMPLETED，source/smoke/formal均正常；smoke20+formal100，共120更新/983040样本，3192.978秒（53.22分钟）。
本轮只读B终态与原始证据，未检查A进度、未续训/仿真、未修改历史结果。
[输入SHA与训练统计](../isolated/recovery_p2_B_terminal_review_20261008/review.json)。

## 原始认证

| B checkpoint | DrawBack | R0 | 联合接受 |
| --- | --- | --- | --- |
| 原来源new50 | 未联合通过 | 0/8 | False |
| update25 | 8/8完整10秒 | 8/8完整10秒 | True |
| update50 | 8/8完整10秒 | 8/8完整10秒 | True |
| update100 | 自身10秒全部通过，外层因retained R0失败计0 | 0/8，接触失败 | False |

25/50每环境首次入口后均1000样本、前缀10秒、双轮接触100%、采样触限0%，初始化有效、runtime fault0，完整结束task_success。
update25 DrawBack逐env最低高度平均.42806m，mean abs pitch .01046/roll .00822rad；R0最低高度平均.43127m，pitch .00852/roll .00610rad。
update50 DrawBack最低高度平均.42782m，pitch .01721/roll .00444rad；R0 .43242m，pitch .01686/roll .00313rad。
这些数值是8env平均，完整通过依据为各env全部gate，不是均值代替最差环境。
选中的update25 SHA：8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44。
update50 SHA：a646b6d09bd7882b38f3fd5568784a0e445f3a631b99cf9409aa6273ce3403d3。
保留两个完整候选，不从latest100接棒。

update100 DrawBack依然自身通过，但R0首次前缀7.32–7.63秒，双轮接触平均96.725%，最后联合接受False。
外层retained_family门槛将DrawBack success置False，所以表面0/8不能说它失去起身；真正回归的是R0连续接触。
一轮失败没有触发冻结的“两次连续检查”停止规则，故formal按上限完成100更新，不是owner故障。

## 干预落实与随机训练

smoke/formal progress均记录仅两个轮std初值减半，腿std/actor mean/critic/Adam保留；物理轮std9.48249/7.56781→4.74125/3.78390rad/s。
checkpoint实际轮std：25为4.88557/3.88416，50为4.89435/3.84680，100为4.55816/3.85636rad/s；std没有冻结，继续由PPO更新。
训练各family×phase逐轮触限约37.4–38.6%/25.8–27.6%，仍非零。与此前P1约54–56%/45–47%的数值差异是跨运行线索，最终干预对照需等待A同源结果。
formal训练completed R0=219/DrawBack=316，535个task_failure、训练随机episode成功0、runtime_fault0。
不能将确定性冻结验收通过写成随机训练每episode都成功；低std改善也未完全解决随机轨迹。

## 通过范围和下一步

这是同一checkpoint在本次seed104、声明DrawBack与R0范围各8/8的完整10秒初步候选。
未执行三seed104/205/306复核、未见holdout或100秒耐久，未证明任意倒地/Swing/实机；起跳本身不要求绝对无腾空，因此通过不等于GUI动作完全平滑。
A臂本次未读取或判断，不能仅凭B成功宣布std干预因果有效；后续依据A终态通知做同协议、同来源比较。
优先保留B25/B50并做肉眼与独立冻结复核提案，不自动续训成功模型；新增PPO0/GUI/耐久均按明确授权执行。

本轮新增复盘与离线统计，STATUS记录B终态；共享代码和原始checkpoint/spec/ledger不修改。
