# Recovery DrawBack 镜像稠密奖励接线与独立声明 — 2026-10-09

本轮用户批准CPU检查与正式接线准备；无仿真/GUI/随机采样/PPO。正式声明`configs/experiments/2026_10_9-18_34__recovery_drawback_mirror_guidance_from_new25/spec.json`已完整发布，ledger UNAUTHORIZED、零使用、空attempt，无run。不得把CPU PASS当提交就绪。

## 实验配方

来源仍为10_58 bounded_mean实验new25，SHA34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c；不是B25退化分支。严格actor/critic/Adam/std保持，腿中心辅助关闭。原support_record beta.3与起身奖励保持，新增唯一一个耦合reward包：真实root轮心DrawBack目标位置质量×实体hip和active镜像质量。

位置尺度.25m、镜像尺度.10rad（不是验收容差）。镜像零误差最高分；奖励不能保证动作或物理完全镜像。只对合法受控Swing起身前样本发放，失败/fault步0，DrawBack/R0原group追加值0，不对动作投影。

新增每步reward=1/秒×.01秒×P×S×fade(h)。fade为1−3u²+2u³，u=clamp((h−.22)/.08,0,1)，.22以下完整、.26一半、.30以上0。这是显式高度退场，不是成功门控或actor切换；原起身和保持奖励始终存在。若再次落回低位会重新激活，无历史状态/新增critic别名；没有负成本减免、终止势能释放、永久短腿目标。entry确认后额外奖励0，不改变现有评分窗口。

## 反事实和刷分边界

实际来源Swing8env每episode新增平均约.0067764，单步≤.01，初始化/失败步0。权重1/秒的理想DrawBack驻留最高追加1/秒，理想站立原正reward分量约6/秒（未扣成本）；因此不额外奖励比站立更高的理论驻留速率，但仍可能形成局部最优，不能证明一定会继续起身。

低位空中收腿可取得部分几何奖、在接近目标范围内反复运动也可累计奖励。高于.30m不再取得本项，但这个fade不是飞行检测。用户允许动态支撑顺序重叠，故不武断用全程双轮接触硬门控抹掉必要动作。候选有上述已知风险，短块必须对照入口率/几何/接触/旧能力，不能用总奖励或镜像更齐宣称成功。

未证明全局没有reward hacking；CPU场景核验与全部8env反事实保存于isolated/recovery_drawback_guidance_ready_20261009/reward_audit.json。此前设计中的“没有驻留收益”并非本实现承诺。来源Swing signal仍弱，当前只是可证伪实验，不能保证学习成功。

## 接线及验证

纯proposal只接收显式wheel centers、实体q、height、eligible/failure/config，不读runtime/files。RecoveryEnv计算root坐标几何，新增reward字段drawback_mirror_guidance，reward_fields统一校验，task_metrics读取eligible/positive、失败和mask违规、镜像误差与轮心距离累计及reward sum。默认关闭，不改变actor input/动作/physics或采样RNG。

smoke wiring要求真实positive事件、读回存在、failed/ineligible奖励违规为0，并绑定metrics SHA。CPU不能认证实际Isaac运行或公式逐帧重放；真实wiring尚未生成，formal须通过新smoke，不复用历史证书。评估full geometry/posture/control仍保留用于峰值/均值/95分位等离线分析；当前runtime统计仅累计值，不能凭累计值伪造p95。

初步相关16测试通过；Recovery及publication回归238 passed/2既有JIT warnings。本声明独立冻结5项PORTABLE测试通过，严格checkpoint/Adam初始化核验通过，spec/poses/budget完整发布SHA验证通过。没有运行全仓库Motion测试或声称其旧证书问题已解决。

## 具体预算与下一步

新单臂source_eval1≤900秒、smoke≤10更新/900秒、formal≤25更新/3600秒，formal10/25三组完整评估。35更新286720样本，整链5460秒（91分钟上限，不是预计时间）。保留fixed26/25/13，USD实体限位/plane/40与5.5Nm、1/5/10ms均不变。同源旧A只作为已完成参照，不额外授权重跑A。

运行前须用户明确批准这个新声明预算；现有notification声明指向当前session但未执行/发送。批准后登记独立授权、共享物理GPU0 UUID并核验资源/身份/新输出，通过supervisor一次提交、有界握手后结束。事件型smoke缺实际positive/mask证据则阻断formal。新候选须Swing入口与完整保持共同评价，旧组退化不得续latest。

## 本轮文件

修改src/native_stand/recovery/drawback_guidance_proposal.py（版本声明/退场/验证）、validation.py、reward_fields.py、runtime.py、command_v6/domain/recovery_course.py、tools/prepare_recovery_course.py、wiring.py；新增scripts/prepare_recovery_drawback_guidance.py、tests/test_recovery_drawback_guidance.py、本报告、新config目录、isolated/recovery_drawback_guidance_ready_20261009及artifacts/recovery_drawback_guidance_cpu_20261009。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX与ARCHITECTURE。旧run/checkpoint/spec/ledger/资产未修改，未commit。
