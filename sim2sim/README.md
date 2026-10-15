# Native Motion sim2sim 验证区

本目录只用于native策略迁移诊断。源模型/资产仍在原位置只读使用；不加入训练控制、
不修改wheel_leg_sim2sim参考仓库，不读取或接管后台训练。
命令唯一维护于项目TOOL_INDEX；下面仅导航和证据说明。

## 当前结论与更正

首轮MuJoCo失败由适配器观测坐标错误影响：native actor消费CAD body-frame，
初始gravity=[0,-1,0]。Fudan runner的canonical变换不能直接用于native观测。
修正直接作用于独立MuJoCo诊断脚本，不修改Isaac训练源码、reward、checkpoint或物理参数。

旧证据`runs/2026_10_8-16_58__motion_b250_mujoco`保留；0.18秒失败不能用于评价
B250的真实迁移能力。该run中canonical几何/roll输出可解释其自身轨迹，但actor输入错误。

## 证据目录

- `2026_10_8-17_07__motion_b250_frame_parity/corrected/parity.json`：最终离线parity。
  上级parity.json试算把control时间/环境轴混淆，后者仅env0首动作结论有效；
  corrected明确layout=[policy_time,env,channel]，不改写试算。
- `2026_10_8-17_10__motion_b250_corrected_mujoco/`：修正后真实CPU MuJoCo运行。
  manifest/输入SHA/独立budget/11个trace/terminal/report/post_validation齐全。
- 当前静态审计入口是共享`native_stand.command_v6.tools.audit_native_parity`；旧目录CLI已移除。
  显式指定冻结checkpoint/spec/evaluation，历史结果保持原始身份，命令只维护根TOOL_INDEX。

详细解释见[本轮复盘](../docs/MOTION_SIM2SIM_FRAME_PARITY_20261008.md)。
没有最终sim2sim验收、多个seed认证、MuJoCo高速/yaw认证。

## 不可变边界

- 25D当前帧＋125D oldest→newest history，实际6实体关节，原动作scale/PD/40及5.5Nm。
- MuJoCo转动关节gear只做力矩单位转换，不做虚拟腿映射/补偿/LQR/初态优化。
- CAD body-frame用于actor；upright reporting-frame只用于roll/pitch、轮心水平几何。
- root线速度是COM速度，不能误用freejoint link-origin速度。
- 当前参考MJCF有friction/damping/armature/collider/solver差异，不自动调参制造通过。
- 新运行目录用集中日期时间命名，拒绝覆盖；每次仿真需明确授权和独立消耗记录。

## 当前选定0.34m Motion教师（2026-10-13）

`2026_10_13-19_46__motion034_teacher_mujoco`绑定05_39/u300 SHA4750ee…cafb，零速/±.5/±1各30秒，全部完成但速度明显后偏（zero-.468m/s），不是完整迁移通过。部署ONNX45输入输出与checkpoint一致。详见[最新复盘](../docs/MOTION034_TEACHER_MUJOCO_REVIEW_20261013.md)，命令维护TOOL_INDEX，旧B250证据保留。
