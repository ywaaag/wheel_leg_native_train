# Level2 原保存收腿姿态迁移

用户通过GUI确认manual0001就是目标收腿支撑位，并明确要求迁移旧update1000、
使用当前限位USD和最新接口，开启Level2；沿用已明确允许的GPU0共享，不停止其他进程。
本轮新根：`2026_10_7-17_21__recovery_level2_drawback_from1000`。
实际阶段以manifest、terminal、ledger和独立逐环境评估为准，准备不是能力认证。

## 来源、姿态与资产

- 来源：runs/recovery_self_stand_from1500_20261003_chain/formal/model_update_1000.pt，
  SHA408e108ed54d31454470726a90a1dde469d7185397716271ea0790f91d941525。
  strict150D actor/critic/Adam；没有改checkpoint内部身份或伪装新USD模型。
- 原保存初态：runs/recovery_pose_capture_20261002_145814/pose_0001_73d09dbe.json，
  SHA1ebaf39d3c07283c01cb519f3ab8e5b3acd7c5d5ded4a08faa88f29ac41b699c。
  使用实际joint_pos/root方向，高度0.168474m；不是requested_leg_rad中的旧UI请求。
  新family drawback_manual0001独立标名，避免与旧Swing family R1混淆。
- 旧USD SHA6bf6ce7f64f8d46cdc759bdf48dba0def85f6e9e6915acca27c543dbcf031a27；
  当前限位USD SHA32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7。
  本次组合后USD逐属性比较仅两处差异：left_knee_pitch下限-0.233rad、
  right_knee_pitch上限+0.233rad。按项目控制分类是被动膝关节限位，
  原六维策略控制hip/active-link/轮，不因“限位变化”推定需要重建动作接口。
  原实测膝角约±1.037rad，当前全部关节在界内；闭链误差2.72e-7m。
  原策略整个动态轨迹是否触及新限位由新基线readback验证，不由初态推出。
- 动作/observation/history声明严格相等；PD/物理时序/限矩一致。
  目标高度由旧0.40变为当前0.36m，需要适应；旧抬升不等于当前站稳。

## 配方与独立预算

DrawBack reset60%+R0 reset40%，保留逐pose事件统计；不启用Swing、随机翻转或自动晋级。
采用当前rising_task11.5秒起身deadline、23秒独立观察、首次站立入口后完整10秒保持。
reward沿用上一版起身lift2/upright.5、height-gated水平成本，保持实体动作和安全保护。
禁止STAND控制/动作偏置/软轮制动/强对称/补偿/限矩增加。
关闭原source50 BC：迁移来源变为旧抬升actor，它未在当前R0下认证，不能盲目当作
当前站立teacher。旧能力通过40%R0 rehearsal和逐环境独立回归观察；这不保证不遗忘。
source baseline在新USD独立验证8个初态，无fault且gate身份正确才允许smoke；
普通起身失败可学习，初始化拒绝或物理故障阻断。未继承历史runtime_valid标记。
smoke必须分别观察drawback_manual0001与R0的有效completed episode，不能用总计代替。

新独立预算：source_eval<=600s/PPO0 → smoke10/<=600s → formal<=100/<=3600s；
总110更新/901120样本，chain4860秒。eval25/50/100，不自动加预算/重试/启用100秒耐久。
此为当前用户新任务授权的有界迁移尝试，不使用耗尽旧账本。
只通过公共supervisor detached提交；一次资源快照和一次有界握手后结束交互，
由现有后台owner结算/通知，不轮询或另建watcher。

新增scripts/prepare_recovery_level2.py、tests/test_recovery_level2.py、新spec/poses；
导航更新README/STATUS/ARCHITECTURE/TOOL_INDEX与RECOVERY_STANDING_PLAN；
entrypoints添加准备器目录项。历史run/ledger/checkpoint/USD未修改。
CPU/plan与实际提交证据见STATUS；未新增控制架构。

436项CPU通过，plan-only PASS，health无finding；一次5秒握手验证worker身份匹配，
submitted/submission_verified=true，当前SOURCE_EVAL，formal首更新尚未验证。
chain attempt466326fc210242bb8abfbbc080672e49，worker3438448，GPU0/shared/preemption=false。
此后由后台owner运行，交互不轮询；启动不表示新USD上已学会或保持起身。
