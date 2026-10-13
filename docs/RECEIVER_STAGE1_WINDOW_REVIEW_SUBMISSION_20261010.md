# Receiver邻近窗口完成与短训提交（2026-10-10）

本轮授权：GPU0 shared，PPO0≤1800秒/512MiB；接管短训smoke20＋formal100≤983040 samples/7200秒，累计≤9000秒。失败不重试追加。

## PPO0实际结果

16组/128评分episode，64仿真env/8评分env。COMPLETED，499.6227秒含清理，71290505 bytes（67.99MiB），PPO与optimizer均0。正常基线8/8，128项SHA及同协议离线评分匹配，数据有限/初态有效/模型未变；无非有限、闭链或机械安全故障。

|case|初态|切换|入口|完整10秒|主通过|严格vx|倾角终止|
|---|---:|---:|---:|---:|---:|---:|---:|
|native_baseline|8|8|8|8|8|8|0|
|B50_40_seed20261010|8|8|0|0|0|0|8|
|B50_45_seed20261010|8|8|0|0|0|0|8|
|B50_50_seed20261010|8|8|8|8|8|0|0|
|B50_55_seed20261010|8|8|0|0|0|0|0|
|B50_60_seed20261010|8|8|0|0|0|0|7|
|B50_40_seed20261011|8|8|0|0|0|0|8|
|B50_45_seed20261011|8|8|0|0|0|0|8|
|B50_50_seed20261011|8|8|8|8|8|0|0|
|B50_55_seed20261011|8|8|0|0|0|0|0|
|B50_60_seed20261011|8|8|0|0|0|0|8|
|B50_40_seed20261012|8|8|0|0|0|0|8|
|B50_45_seed20261012|8|8|0|0|0|0|8|
|B50_50_seed20261012|8|8|8|8|8|0|0|
|B50_55_seed20261012|8|8|0|0|0|0|0|
|B50_60_seed20261012|8|8|0|0|0|0|8|

三个seed仅小幅世界yaw±0.01rad；保存的root初态读回确实不同，不代表高度/速度/地形鲁棒性。0.50秒三组24/24通过，其余12组96/96未在2秒完成入口；其中倾角提前终止单列，不归作保持失败。本轮无已进入后保持失败。0.50秒24个完整保持的严格vx≤.02诊断均失败，主vx≤.5通过。不能把相对历史7/8变化归因学习，本轮权重完全冻结。成功只证明三个声明yaw条件，成功窗口仍窄。

逐环境、位移/速度/姿态/触限分阶段、切换目标跳变及全部来源SHA见：
- `isolated/receiver_stage1_window_completed_20261010/review.json`
- `isolated/receiver_stage1_window_completed_20261010/matrix.json`
- `isolated/receiver_stage1_window_completed_20261010/submission_prerequisite.json`

## 已授权短训首次提交

按原配方B50冻结0.50秒、32 Swing＋32正常站姿；只训练从Motion B250初始化的接管候选。原Motion及Recovery不变。初始化与冻结前缀actor mask关闭、GAE保持真实时间轴。formal独立从来源初始化，不承接smoke。25/50/100组合、正常及返回原Motion±.5评估由既有owner执行。

public supervisor资源再次核验READY，实际shared；GPU UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`，物理0→CUDA_VISIBLE_DEVICES=0→逻辑cuda:0。声明SHA `6925391e3b6442b957990838b99e32797112dd90946930b35625eee2e5be8081`。

训练run：`runs/2026_10_10-22_19__receiver_zero_from_b250`。单次有界握手：SOURCE_EVAL，worker身份OK；formal首更新未核验，不能声称已发生学习。chain attempt `7c488b04b4744a0d87b89efe5ff78a21`。后续由既有owner监督结算，worker不再轮询。通知配置enabled=false，不声称自动唤醒已开启。

授权、检查、启动及握手原件：`isolated/receiver_stage1_authorized_submission_20261010/`。本轮只登记两份新声明/新ledger及写本次报告、STATUS；未修改物理/奖励/源码，未覆盖旧run。CPU与冻结验证沿用本轮提交前SHA无漂移的最终验证（targeted70、冻结17/14；全CPU762pass/22旧Motion证书SHA fixture errors，具体证据见工程交付）。

## 尚未回答的学习问题

训练尚未完成，不能回答候选相对冻结组合的成功率、收稳、返回运动改善幅度。终态必须分别报告组合保持与返回Motion运动；零命令保持成功不能代替完整恢复—运动闭环。
