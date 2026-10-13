# Motion对称专项新Adam故障修复与继续提交（2026-10-13）

用户明确要求“请修复，并且继续训练”。本次是一次新声明重新提交，非原owner自动重试。

## 根因与修复

原08_29专项source_eval完成8评分episode，smoke构造新Adam时wheel-envelope转换直接访问state[param]['exp_avg']，触发KeyError。该配方本应使用全新Critic/Adam，新Adam尚无moment是合法状态；甚至100→100等尺度转换也触发旧代码。原smoke/formal均0更新，总253.6715376秒，旧FAILED/run/spec/ledger/frozen保持只读。

新完整公共副本manual_train/motion/standing034_symmetry_engine_v4，只在command_v6/domain/warmstart.py修复转换：不通过defaultdict索引制造空state；新/尚未更新的参数保持无state；已有Adam moments仍按原坐标转换；残缺/shape不符的state先报错，参数修改前验证完毕。没有伪造Adam step、预热optimizer或恢复旧Adam绕过问题。

motion_course/io.py只绑定新v4执行根。reward、gate、源Actor/std、网络、动作尺度、初始化、PD/USD/限矩不变。新recipe仍Critic/Adam独立、warmup5；同配方正常续块完整状态恢复。

## 验证

新增真实初始化边界回归在旧v3上复现同一KeyError，v4修复后通过。manual_train/motion/tests/test_standing_symmetry.py覆盖实际源Actor、新Adam轮转换、Critic-only更新、随后Actor真实更新；另覆盖部分moment/继承moment转换、不完整moment拒绝且不修改参数。CPU optimizer只更新独立内存副本，不计在线PPO。

相关54pass/1deselected（该项硬编码shared-root，独立bundle下不冒称portable）；冻结PORTABLE18pass，冻结身份与preflight PASS。旧三命令课程16项在其原v2模块下通过，不能把旧fixture强行加载零命令对称v4模块；四个不兼容测试的原因已逐项定位。全量shared CPU943pass/8skip/22errors，22test-ID与修改前相同；生产SHA校验未放宽。

## 新任务与实际提交

新task manual_train/motion/tasks/standing034_symmetry_adamfix_20261013，账本history绑定原失败总账SHA及更早1488更新，不删除旧消耗、不借旧额度。
新spec `configs/experiments/2026_10_13-09_07__motion_standing034_symmetry_block0000/spec.json`。
新run `runs/2026_10_13-09_07__motion_standing034_symmetry_block0000`。
spec SHA `6d0748245f366b52d820a8716c94a5a6b0e08496610f4d487b772b01b5fad413`。
来源仍旧block3 update300，SHA4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb。

公共零写plan PASS/0writes；授权登记、资源检查READY；GPU0共享/UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72、CUDA0、提交时可用30094MiB，未停止其他任务。一次30秒握手submitted=true/submission_verified=true，SOURCE_EVAL，formal_first_update_verified=false。实际冻结220模块与CPU副本逐SHA一致。尚不能称正式PPO首更新或能力通过。

每块smoke25＋formal300/325updates/2662400samples/4小时/2GiB，任务累计不限。后续既有owner根据联合站立与对称证书继续/停止；工程错误停止，不自动重试。通知关闭，worker不轮询。Recovery任务及共享src未修改。

准确命令仅维护TOOL_INDEX；源码修复、测试、声明及验证目录为本轮新增，STATUS/ARCHITECTURE/WORKFLOW/manual_train/motion/README导航收口。没有commit/push。
