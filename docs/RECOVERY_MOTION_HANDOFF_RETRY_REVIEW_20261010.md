# Recovery→Motion接管重试复盘（2026-10-10）

## 结论

16_34重试经公共supervisor执行并COMPLETED结算，但基线主协议0/8，后续21组NOT_RUN。**不能据此判定Motion B250在新USD上能力失败**：离线核准发现准备器错误转换了正常初态四元数槽位，基线不等价于Motion冻结初始化。此次属于初态接口错误。未续训、未换USD/模型/卡、未再启动仿真。

原冻结native_env.py的reset直接设置pose[:,3]=√.5、pose[:,6]=√.5，因此实际root quaternion四槽为[√.5,0,0,√.5]。准备器却因Recovery姿态字段名root_quaternion_xyzw误写成[0,0,√.5,√.5]；Recovery runtime将该四元数值原样转发，初态实际被旋转为另一姿态。不能依照字段名重新排列，也不能把原生正常构型改成自选R0。

## 实际运行证据

- run：/home/kellen/wheel_leg_native_train/runs/2026_10_10-16_34__recovery_motion_b250_handoff_ppo0
- attempt：1a75647b276a4c4fa2092889359614d4；terminal/ledger COMPLETED（诊断流程完成，accepted=false）。
- GPU0 UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，共享，资源检查READY；不停止他人。
- 墙钟含清理：5.419593秒。PPO0、optimizer0；64仿真环境/8评分环境，只执行一个policy interval，all simulated env-step64、scored env-step8。
- 8个评分episode开始，0完整保持窗口；输出目录含冻结代码总计958575字节，低于1GiB。
- root前高度.400m、全关节q/dq0/root速度0；错误quat为[0.0, 0.0, 0.7071067690849304, 0.7071067690849304]。
- 8/8第一步由tilt终止，其他5种cause为false；env0实际tilt=1.568526rad，约89.87°，超过原60°保护。不是2秒确已跑满，也不是10秒保持失败。
- Motion确实控制该interval；首实体目标四腿约[.09755,-.13206,.11319,-.23862]rad，两轮−100rad/s。该输出受到错误重力方向输入影响，不作为正常初态模型输出判断。
- 旧evaluation failed_checks仅给not_settled_within_2s/failure_stage=settle，未充分解释提前终止；本离线复盘依据具名termination_causes补充实际tilt原因，旧原始结果不改写。
- initial_valid=true是已有初始化检查结果，不能替代与Motion原生reset逐槽等价认证。本例说明CPU初态等价回归此前遗漏。
- evaluation_00.json/trace_00.npz/initial_state_00.json先原子落盘，修复后的numpy序列化有效；旧16_28失败原账不改。

## 22组结果

| 条件 | Recovery前缀s | 初始化标记有效 | 实际切换 | 2s内入口 | 完整10s | 主通过 | 严格零速 | 实际失败/状态 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Motion正常初态 | 0.0 | 8* | 8 | 0 | 0 | 0 | 0 | 10ms倾角终止/初态接线错误 |
| Motion直接Swing | 0.0 | — | — | — | — | — | — | NOT_RUN |
| B_init | 0.1 | — | — | — | — | — | — | NOT_RUN |
| B25 | 0.1 | — | — | — | — | — | — | NOT_RUN |
| B50 | 0.1 | — | — | — | — | — | — | NOT_RUN |
| B100 | 0.1 | — | — | — | — | — | — | NOT_RUN |
| B_init | 0.25 | — | — | — | — | — | — | NOT_RUN |
| B25 | 0.25 | — | — | — | — | — | — | NOT_RUN |
| B50 | 0.25 | — | — | — | — | — | — | NOT_RUN |
| B100 | 0.25 | — | — | — | — | — | — | NOT_RUN |
| B_init | 0.5 | — | — | — | — | — | — | NOT_RUN |
| B25 | 0.5 | — | — | — | — | — | — | NOT_RUN |
| B50 | 0.5 | — | — | — | — | — | — | NOT_RUN |
| B100 | 0.5 | — | — | — | — | — | — | NOT_RUN |
| B_init | 1.0 | — | — | — | — | — | — | NOT_RUN |
| B25 | 1.0 | — | — | — | — | — | — | NOT_RUN |
| B50 | 1.0 | — | — | — | — | — | — | NOT_RUN |
| B100 | 1.0 | — | — | — | — | — | — | NOT_RUN |
| B_init | 2.0 | — | — | — | — | — | — | NOT_RUN |
| B25 | 2.0 | — | — | — | — | — | — | NOT_RUN |
| B50 | 2.0 | — | — | — | — | — | — | NOT_RUN |
| B100 | 2.0 | — | — | — | — | — | — | NOT_RUN |

*正常初态8个initial_valid标记为true，但原生初态等价性失败；不能称合法Motion正常基线。NOT_RUN没有切换/保持统计，不能写0/8能力失败。无保持窗口，保持速度/姿态/接触均N/A；不能用10ms平均替代10秒。

## 修复与CPU验证

只改scripts/prepare_recovery_motion_handoff_scan.py，新增native_normal_root_quaternion解析，严格保持冻结reset的实际四槽数值；不改Recovery姿态库全局契约、不改已发布spec/旧run。tests/test_recovery_handoff_interfaces.py新增真实冻结代码→prepare→runtime原样转发回归，并拒绝未识别reset。

共享针对性14项CPU通过；新声明冻结9 PORTABLE通过；public supervisor零写plan完成且未授权不提交。新声明2026_10_10-16_44__recovery_motion_b250_handoff_ppo0，spec/poses/ledger/发布标记独立，UNAUTHORIZED、零attempt，无新run。源码、测试、声明之外只更新本报告/STATUS/Recovery计划与旧工程报告的事实纠正。

## 下一最小行动与授权

先在更正后的原生正常初态验证B250。如果8/8主协议通过，才展开直接Swing与20个Recovery前缀；若仍失败，按完整初态/物理/输入轨迹区分接口、资产兼容和实际行为。尚无任何可接住B候选的证据，也没有否定证据。

重试授权仅执行一次，已消耗并结算。失败不自动重试约束继续有效，因此新声明不自动登记授权或提交；需用户明确再次批准。两次历史消耗5.310061+5.419593秒分别保留，不用旧余额伪造新授权。未训练reward/classifier/critic success model、未commit/push。
