# Recovery → Motion B250接管：任务修正与CPU契约 — 2026-10-10

最终实际部署为Swing→Recovery动态状态→Motion B250零速接管→2秒内收稳→完整10秒保持。Recovery自身无站立入口仍可作为接管候选，不再要求Recovery自己先站稳或精确静止DrawBack。本次新组合协议不追溯改历史0/8。仅CPU，无仿真/PPO/optimizer。

## 已核验事实和修正

B末2秒8env平均(height/vx/pitch)：初始化(.199102m,+2.36977m/s,−.34385rad)、25(.217354,+1.85147,−.54057)、50(.196605,+2.94645,−.32189)、100(.197556,+2.96259,−.33015)。B100env0 .25秒vx+.42224，2秒+2.94734。之前“低位驻留”描述缺少平移运动，应纠正为低位持续高速运动，不能再把速度未知当静止。vx是现有native定义，不冒称世界轴。

Motion checkpoint runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt SHA5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e，自己的formal/source_snapshot/spec.json与内部identity匹配，严格actor载入。原USD不是新knee-stop资产，不能迁移其旧通过数。Motion腿scale.5/height command.40，Recovery1.6/.36；两者physical1/5/10ms、PD60/2/1、40/5.5Nm与closure5mm一致。Recovery旧stand_checkpoint为wide_leg update500，不是B250；当前rising task不交接。

## 接管接口契约与测试

新增纯recovery.motion_handoff：从实际物理legs/wheels按各自scale编码previous action，保留raw/outside/clipped和information_loss；Motion命令[0,0,.40]、各自frame/history；非reset时连续shift，不在切换fillhistory。动作各自decode实体目标，不混归一化动作、不重复缩放。纯接口传入explicit reference，没有读取环境或自动改reference。

新score要求Motion controller连续，2s内height≥.30/水平/接触条件连续.20确认，随后下一1000sample完整保持；沿原Recovery姿态/接触/closure/saturation，并加冻结B250零速meanabs vx≤.02、vy≤.02、yaw≤.03。速度门槛来自其旧零命令gate，不从新motion_absolute误差.3随意替换。组合协议不是旧30s命令schedule复现，需独立版本认证。切换前失败保留失败、episode拼接/缺窗/非finite拒绝。

五项CPU测试通过：物理target编码及包络信息损失，独立Motion命令和连续history，dwell后完整窗口/速度失败，22组和未切换/晚入口失败，切换前失败及episode身份拒绝。CPU证明数据语义，不是Isaac物理接管结果。

## 诊断准备与尚未完成的执行接线

scripts/prepare_recovery_motion_handoff.py已核验四个Recovery B init/25/50/100、B250、parent spec/资产/姿态库SHA和严格网络state。输出isolated/recovery_motion_b250_handoff_preparation_20261010/preparation.json及完整marker：22条件×8=176episodes、PPO0、wall≤3600s、storage≤1GiB。第1正常站姿baseline（历史合法R0 holdout姿态来源明确，不称新USD runtime已有效）失败即停止扩大扫描；第2直接Swing B250，余20为4候选×.10/.25/.50/1/2s。每case真实重跑前缀，不从不完整trace恢复PhysX，不清动量。

当前status CPU_CONTRACT_READY_RUNTIME_ADAPTER_PENDING、runnable=false，未发布可提交spec/ledger。未完成同RecoveryEnv运行时实际physical direct switch、Motion历史shadow生产、接管后专用终止/采样窗口接线、公共supervisor自定义PPO0请求adapter及有界压缩trace结算。不能打开旧stand开关冒充该诊断，不能用纯CPU通过申请“已准备好直接运行”。下一继续完成这些明确adapter和冻结CPU验证后，才发布独立声明、集中请求本条尚未给予的PPO0运行授权。

运行数据需逐step记录controller、pre/postswitch目标与实际力矩、两套frame/history与previousaction损失、完整q/dq/root/contact及failed stage；恢复动作与Motion动作的回报归属不在本轮设计。有限样本通过只能称该协议下有限时接住的状态，不宣称数学收敛域或critic是成功概率。

本次新增src/native_stand/recovery/motion_handoff.py、scripts/prepare_recovery_motion_handoff.py、tests/test_recovery_motion_handoff.py及CPU身份包；更新计划/STATUS/TOOL_INDEX/ARCHITECTURE，本报告。无Motion或历史源码/资产/模型/raw/ledger改动，无新仿真通知训练，无commit。
