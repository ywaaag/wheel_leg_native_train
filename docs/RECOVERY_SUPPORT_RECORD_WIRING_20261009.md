# Recovery平滑支撑纪录奖励：runtime接线与PPO0读回

2026-10-09，用户批准的接口接线与独立有界诊断已完成；没有启动新PPO训练。认证来源仍为Recovery B25，SHA `8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44`，不是Motion B250。

## 原始证据和实际消耗

- 新声明：`configs/experiments/2026_10_9-08_42__recovery_support_record_wiring_ppo0/`，授权/发布身份和独立budget保留。
- 新run：`runs/2026_10_9-08_42__recovery_support_record_wiring_ppo0/`；terminal、monitor_exit、三组evaluation及SHA绑定的NPZ均在此。旧run/checkpoint不改写。
- attempt `3741b8d4297d4b00bbafff882e3ec4c7` 已COMPLETED并结算evaluate1；PPO/optimizer updates及训练样本均0。账本149.573836秒，terminal149.173138秒，差额是退出/清理。
- 独立evaluate墙钟上限900秒，三组每组最长23秒、8scored/64布局。Swing因原tilt失败提前结束，不能称完成23秒保持；DrawBack/R0各8/8完整原10秒协议。
- physicalGPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72` → cuda0，共享授权；没有停止其他任务。
- 离线复核：`isolated/recovery_support_record_wiring_review_20261009/review.json`，保存输入SHA，wiring_pass=true。review自身不模拟、不更新权重。

## 真实读回结果

| 检查 | 结果 |
|---|---|
| 基准 | Swing每env首次受控pre-step Q约.235；firstbest=preQ；全关节USD FK重建误差最大1.3263e-6 |
| 实际新增回报 | Swing8env平均.00537418，env0四次纪录刷新，总.00539382；不是先前省略首步的反事实.004728 |
| 逐步奖励 | weighted=.3*max(postQ-prebest,0)*eligible*(1-failed)，raw*beta一致；最大公式误差0 |
| 初始化/失败/旧组 | 新增奖励均严格0；DrawBack/R0不建立eligiblebaseline |
| 几何读回 | post根坐标轮心/重力独立重算Q误差小于2e-7 |
| 纪录与预算 | Swing单episode单调不减；各env总奖不超.3*(1-Qinitial)，约.2295 |
| 行为 | Swing0/8，DrawBack8/8，R0 8/8；冻结模型，不是学习改善 |

episode partial reset、基准清除、snapshot保留和schema冲突由CPU测试验证；本次确定性诊断只跟踪每env首episode，不能冒称覆盖了训练中的随机重复reset或所有跨入口组合。mean/std/control没有干预；关闭meanaux。原actor输入、限矩、USD、评分与起身reward保留。

## 改动与验证

本轮源码：`recovery/support_record_proposal.py`（版本声明、校验及RecordState）、`recovery/validation.py`、`recovery/runtime.py`、`recovery/recipe.py`、`command_v6/domain/input_capture.py`；路径均在`src/native_stand/`。
新增离线读回脚本`scripts/review_recovery_support_record_wiring.py`；测试`tests/test_recovery_support_record_proposal.py`和`tests/test_recovery_input_capture.py`。更新STATUS、任务计划、TOOL_INDEX、ARCHITECTURE；本报告及新声明/CPU产物/新run为本次证据。

CPU全回归657 passed；最终冻结PORTABLE验证10 passed。最初fake runtime测试缺可选状态属性已修正为getattr/早期初始化；初次失败记录保留。离线报告首次序列化numpy.float32失败，转换为Python float后成功；未重新模拟或修改原始数据。

## 下一步与限制

接线成立且已有非零信号，可以准备下一条独立单变量短训：从认证B25严格warmstart，固定26/25/13 family槽位，关闭meanaux，仅新增beta=.3纪录奖励；smoke10、formal最多25，10/25完整Swing+DrawBack+R0评估，旧能力退化保护、来源/早期候选保留。训练预算、墙钟和真实事件wiring certificate必须在新spec独立明确，不能复用本次PPO0授权。

必须同时读回左右length/direction贡献、起身峰值、入口与10秒完整保持、轮mean/std/clip和reward实际量级。非零小奖不保证突破探索死区；平均双侧quality可能奖励单侧改善，且150D未显式观测纪录会使critic条件化有别名。不得只因geometry/reward更高接受候选，也不同时改std、轮矩、观测或奖励系数。此次没有可用新checkpoint，不自动续训。
