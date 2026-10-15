# v14 wiring2终态复盘

事件86f01a3467baf486884321ab。只读复盘，无自动续训、物理评估、进程停止或历史文件改写。

## 结论

工程smoke已PASSED，正式训练300更新后在update300第二项评估保存时因`Handoff storage cap exceeded`停止。实际smoke12＋formal300＝312更新、2555904原始samples；formal有效Actor2416640、smoke57344；链6300.51秒（105.01分钟）。688未用不授权续训。各attempt已终态，smoke/formal ledger wall_s为null，不伪造精确分阶段结算。

## 同协议表现

下表指标为各已完成case/环境的首30秒平均；质量gate使用固定末10秒，不能混为同一窗口。来源/u100/u200各3case×8；u300仅normal_native8例，其余INCOMPLETE/NOT_RUN。

| 模型 | 生存/已评分 | 完整质量通过 | abs vx m/s | pitch rad | roll rad | 轮心前后差 cm | 腿长差 cm | 接触 |

|---|---|---|---|---|---|---|---|

| 来源u988 | 24/24 | 0/24 | 2.2852 | 0.2321 | 0.20512 | 2.400 | 8.778 | 1.000 |

| model_update_100 | 24/24 | 0/24 | 1.3011 | 0.2438 | 0.11364 | 3.264 | 4.573 | 1.000 |

| model_update_200 | 24/24 | 0/24 | 0.8622 | 0.2360 | 0.00001 | 3.247 | 0.250 | 1.000 |

| model_update_300 | 8/8 | 0/8 | 0.3227 | 0.2250 | 0.00001 | 0.556 | 0.044 | 1.000 |



u300已保存单case显示明显减速、roll及几何改善，末10秒水平速度p95约.36m/s、pitch约.226rad仍失败；不是全case成功。各已完成评估未见闭链/离地间隙/触限gate失败。随机训练2580completed episodes，其中387normal timeout，最长30秒；这次真实训练已观察timeout路径，不能把所有随机episode都称为稳定站立。

## 确定工程问题

students/training.py evaluate_cases将`min(evaluation_max_bytes,chain_remaining)`传给handoff_evaluator.atomic_result。后者却将整个phase目录的历史产物＋新产物与该cap比较。128MiB被当作阶段累计上限，formal已127.38MiB，下一轨迹约17MiB触发；链总4GiB与物理磁盘仍约9.88GB空闲，不能称磁盘ENOSPC。

下一修复应把单产物增量限制、phase/chain累计限制明确分开，CPU覆盖多次评估＋已有checkpoint/log及原子失败清理；不靠提高上限绕过错误。

## 证据和选模限制

u300 checkpoint已保存SHA64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f；只有evaluation_06.json完整，第二项INCOMPLETE、第三项NOT_RUN。progress/registry/latest仍u200，不等于最新磁盘checkpoint。

原选择仍来源best_overall、u100 best_new。它不说明u200/u300没有改善：当前rank在零通过时优先生存/最短时长，再排质量，及通用selection描述残留旧窗口措辞；不可据此自动修改旧登记或宣称唯一最佳。完整质量accepted仍null。

## 唯一优先下一步

先CPU修正存储cap单位与范围并测试，然后准备有界工程恢复声明，保留FAILED和已耗312，不重置额度。u300是最近完整训练状态但能力评估不完整；恢复前核验Actor/Critic/Adam/RNG和补齐同协议评估。用户新明确运行授权前不提交；暂不改reward/std/控制周期，不因本次存储故障判定配方失败。

本轮仅新增本报告、comparison.json并更新STATUS。逐环境、逐gate、末10秒指标与输入SHA见`artifacts/standing_survival_wiring2_terminal_20261014/comparison.json`。
