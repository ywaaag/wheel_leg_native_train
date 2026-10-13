# 姿态重试磁盘故障复盘

事件987abea1ae3b69622d957f9f；仅只读核验终态和一次磁盘快照，不重试、不清理。
run：runs/2026_10_8-20_29__motion_b250_posture_metrics_retry。
chain FAILED，source_eval FAILED，smoke/formal未运行，online PPO0、训练samples0。
不是姿态能力失败，也没有验证metrics修复后的真实PPO路径。

确定异常：OSError(28, 'No space left on device')。
冻结train.py第345行_write(output/label,result)，第52行tmp.write_text(json.dumps(...,indent=2))。
错误发生于最后来源-2命令序列化；现有evaluation_source_-2_0.json.*.tmp仅2097152字节，
没有有效完整JSON，不能宣布该项通过。临时文件原样保留。
先前8个source JSON均完整、各8/8：0、±.5、±1、±1.5、+2；每项约17.8–18.1MiB。
该阶段completion_report.md缺失，analysis临时文件0字节；以chain/phase terminal和ledger为准。

磁盘快照：/dev/nvme0n1p5 384G，Used364G、Avail2.2MiB、Use100%；inode11%，非inode耗尽。
此为检查时刻快照，不自动判断可清理文件，不touch其他任务。

source主体1876.339s，整链1879.591s；ledger exact attempt
b3ab60eaed5b43b7858c91b8e9b127a6已FAILED结算，used source1/smoke0/formal0，无RUNNING。
两次姿态链累计1927.081+1879.591=3806.672秒，原10800秒预算保守剩6993.328秒；
仍无训练更新，剩余额度不授予新启动权限。

下一步先解决存储再考虑工程重试：
1. 只读盘点项目产物占用，列明用户可决定的迁移/归档候选；不删除旧run/raw/checkpoint/ledger。
2. preflight增加可用字节与预计产物预算，启动前拒绝空间不足；终态保留小文件写入余量。
3. 压缩存储trace或二进制数组，JSON仅摘要和引用；同步loader/schema/SHA，不能丢失几何证据。
4. 若复用完成source结果，必须验证新旧spec/evaluator/recipe身份并使用新输出更正记录，
   不将半写文件当证据；防止每次基础设施失败重复花30分钟做同一来源评估。

本次只新增本文、更新STATUS，未修改运行代码/存储方式/旧账本，未仿真/PPO/通知/Git提交。
