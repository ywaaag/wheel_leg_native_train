# Recovery动态过渡诊断：CPU候选与字段预算草案

2026-10-09用户同意计划8.9下一准备。纯CPU在保存合法Swing fulljoint、新USD及当前原生6D目标范围内扫描收腿与转腿组合；不寻找沉降中间态、不启动物理运行或PPO。

## 候选路径

实体主动轴顺序left hip/left active/right hip/right active。相对起点变化为[a−b,a+b,−a+b,a+b]，a表示此前局部收缩方向的延伸，b表示叠加另一关节组合；两者仅CPU几何参数，不是虚拟腿控制。a=.15/.30/.60rad、b=−.20/0/+.20rad，共9条；每条31个离散点、passivebranchcontinuation。

六条在既有动作位置范围±1.6rad和USD全部jointlimits内闭合，三条因动作目标包络超出停止，不扩大包络。已核验此前真实Swing capture reference=0，仍须未来runtime再次读回；未把USD较宽limits误当策略动作可达范围。所有通过路径closure≤1e-4m；只核理想碰撞体最低地面间隙，不认证selfcollision。

通过路径a=.15时腿长约.338m，a=.30时约.297m，a=.60/b=.20时约.211m。b正向提高与重力向下的cos，但最深终点cos仅约.465，未达到竖直DrawBack（仍不等于其.15m构型或平衡域）。b=.20的三条在固定root姿态/高度出现理想地面穿入，这不是合法静态reset，也不是动态必然不可达：需要机体随支撑反力运动后才能判断。

此前“仅局部.15rad已足够”的误读排除：更深收腿与朝下方向仍须协同，完整Swing到DrawBack尚未构造/验证。路径未包含接触冲量、力矩可执行性或机体转动，不能在runtime直接照抄。

## 物理诊断草案（非运行spec）

建议独立PPO0显式动作可达性诊断，首块最多6候选、每episode最多3s、总wall≤900s含清理、详细数据≤128MiB、共享physicalGPU0并在reserve前核对UUID。所有时序、目标速度/加速度、动作来源与退出条件须继续准备并审查，当前reference_schedule=unset、runnable=false、runtime_authorized=false。该草案不是已授权预算，不能直接submit。

先从已核验合法Swing初态开始，不施加root托举/外力/重力补偿、不改40/5.5Nm/PD/USD。诊断reference若显式覆盖actor，只能作为隔离的可达性实验、逐步记录override，不写常规CommandEnv隐藏控制，不宣称RL学会起身。策略接管在诊断阶段默认不启用；只有完整动态状态满足实际可恢复证据后，另评估handover，不能用单腿长/高度阈值硬切策略掩盖失败。

必须记录pre/post fulljoint/rootpose/rootvelocity、原生target/reference、5msPD requested/clipped/applied torque、关键支撑碰撞体具名1ms或有明确积分语义的contactforce/impulse、轮心/closure、episode/initialvalid/reset/actionorigin/override等。轮力不代替机体/连杆全部支撑力；缺字段UNKNOWN。是否需要完整1ms所有体力应按首块字段成本核算，不无限制保存。

摆腿/收腿应允许时间重叠，不能预设先腾空；需要评估力矩饱和、机体抬升空间、双侧收短、轮心转入机体下方、姿态和后续保持。冲击峰值或跳高不是接受标准。

## 下一工作

下一CPU工程准备是完善短时序候选（角位置/速度/加速度和动作包络审核），及既有supervisor/evaluator下显式诊断adapter的测量/动作来源接口与异常清理测试，再发布独立可审查spec/ledger。闭链几何路径对地面穿入只能提示需要rootmotion，不能从中计算所需冲量或保证可执行；若没有完整诊断接口就不启动物理运行。

此阶段没有可接受新策略或成功Swing轨迹；认证B25与旧DrawBack/R0事实保持，先检验动态路径再考虑RL示教/课程/奖励迁移，后者均独立变量。

## 改动和验证

新增`scripts/prepare_recovery_dynamic_geometry.py`（pureCPU），发布`isolated/recovery_dynamic_geometry_draft_20261009/geometry_candidates.json`，绑定spec/pose/USD SHA；实际9路径执行，复核6合法路径每点closure/action包络，真实reference0读回。新增本报告、更新任务计划/STATUS/TOOL_INDEX。无旧run/checkpoint/raw/specledger/asset修改，无仿真/GUI/PPO/随机采样、无Git提交/清理。
