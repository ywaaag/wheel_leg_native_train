# Motion31绝对姿态与宽容早停、1600三seed确认

## 本轮用户决定

沿用v3原奖励权重和停车训练，不沿用v4增强姿态/取消停车配方。用户容忍pitch .1rad、roll .05rad。当前先确认v3/update1600的0/±.5/±1；不启动新PPO、±1.5课程或域随机化，不将旧1795额度视为新预算。

## 新评估协议

`motion31_absolute_posture_assessment_v4`：仍为30秒受控窗口、准备2/加速8/保持8/回零8/停车4秒。逐环境保持段10–18秒最大绝对pitch≤.1、roll≤.05；原tracking/方向/gain/持续速度、zero、parking、contact/closure/height/geometry绝对安全条件保留。来源相对姿态差不作为gate，旧结果不改。缺完整窗口不缩短验收。

## 早停模块（未来新训练显式启用；本次PPO0不更新）

`motion31_absolute_posture_retention_v1`由`motion_training.early_stop_policy`显式声明，旧默认不变：

- 前300次普通能力波动不累计早停；runtime/nonfinite/闭链/控制权故障仍由现有runtime立即拒绝。
- 固定250次检查；同一已通过旧命令连续3次明显失败才停。不同命令不合并，缺失固定检查打断连续计数；UNKNOWN阻止晋级，不能当能力退化证据。
- 明显失败：某环境MAE>.5且比来源增加≥.2m/s；方向率<.8；zero水平稳态p95>.5；存活不足6/8；保持段pitch或roll超过.1/.05。
- 通过门槛仍严格，允许学习不代表通过。随机探索的单episode严重坏姿态仍按原更宽终止阈值reset，失败样本保留，未把评估绝对门槛直接改成训练episode终止线。
- 独立模块不改reward、PPO、网络、物理或原v3的质量终止。
- 链级现在保留正常退出阶段的STOPPED_BOUNDED，不再将保护提前结束误报为预算COMPLETED；历史报告不重写。

## 三seed PPO0确认

来源：`runs/2026_10_14-21_23__motion31_posture_quality512_v3/formal/model_update_1600.pt`

SHA：`83ee2371d37c48cefcf61c7de98a1cfb5eb1e01c19071efbb2e6949a36f9a820`。

新spec：`configs/experiments/2026_10_15-09_12__motion31_u1600_three_seed_ppo0/spec.json`。

评估seed20261014/20261015/20261016，每seed五命令，每命令8scored env，共120例。它们是多个评估seed，不是多训练seed；如reset确定性很强，seed变化不等于获得广泛随机分布认证。只加载冻结Actor，不训练/恢复Critic或optimizer；环境输入仍具名Motion49布局。保持v3真实reward配置供记录，不进行reward优化。新输出与独立evaluate1账本，online额度0、最长10800秒、2GiB安全上限；compact轨迹完整保留评分状态，不重复保存所有动作流。GPU0共享→CUDA0，不抢占、不自动重试，当前owner终态通知。

新增路径：`students/motion_guard.py`纯数据评分/保护；`students/motion_confirmation.py`文件身份与15case验证；`scripts/prepare_motion31_confirmation.py`专用CPU准备。评估继续走既有supervisor→monitor→evaluate_checkpoint batch，没有新trainer或watcher。通用evaluator/runtime共享底层命令与物理接线，只有新显式协议分支生效。

## 结果处理

来源120例完整通过再准备±1.5，同级失败先按具体命令处理，不增加随机化、不预设必须低速再训2000。新在线预算/阶段声明仍需明确，不能从本次PPO0授权推导无限训练。姿态相对比较保留作诊断，不把旧failed改为新passed。

CPU/零写plan/启动回执位于 `artifacts/2026_10_15-09_12__motion31_absolute_confirmation/`；实际是否提交与终态以该回执和run原始证据为准。未提交Git，未修改历史资产、checkpoint、ledger和评估。

## 实际提交与验证

public supervisor evaluation-only已detached提交，monitor400857、attempt7469cdbb50174fa6a5f101687348832b。一次启动核验argv/spec/output/attempt/启动时间/CUDA0均OK；完整评估结果尚UNKNOWN，不守候或轮询。当前授权仅执行本确认，后续不自动开新PPO。

CPU PORTABLE459通过、8跳过、4弃用警告；绑定定向28通过，schema/零写plan通过、提交前资源与身份检查READY。AST静态编译通过，原v4证据SHA复核未变；精确修改文件清单见同名artifacts/change_manifest.json。没有离线optimizer更新，没有新训练采样，当前是冻结Actor物理评估。声明和runtime都记录小型真实reward快照，未复制源码树。
