# v10 update100正常站姿0.34m命令PPO0

run: runs/2026_10_13-16_59__v10_normal034_identity_ppo0；用户授权GPU1独占，一次64sim/8scored、seed20261013、13.52秒请求、600秒墙钟上限。实际84.634293秒/7.02MiB，COMPLETED，PPO/optimizer0。无教师，实际controller全3、Actor高度输入全.68；旧模型和旧0.40冻结声明不改，合法normal出生姿态不变，不强放到.34。

来源v10 update100 SHA bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d。原始trace SHA核验，逐env结果及账本见artifacts/v10_normal034_20261013/results.json。

入口8/8，完整首次10秒保持窗口2/8，主协议0/8；其余6例9.71–10.18秒结束，不完整。2例完整也在高度、姿态、接触、速度和触限失败。

下表为每环境最早1000个有效学生样本，不足则实际9.71秒；诊断宏均值及环境范围，不是完整保持gate，不称稳态。

|指标|宏均值|环境范围|
|---|---:|---:|
|height_mean|0.39286|0.39011–0.39736|
|height_MAE034|0.05848|0.05742–0.05918|
|mean_abs_vx|1.50827|1.44952–1.54584|
|mean_abs_vy|0.04633|0.02942–0.06635|
|mean_abs_yaw|0.13759|0.08839–0.15921|
|double_contact|0.93086|0.90200–0.96000|
|saturation_any|0.47902|0.45314–0.49700|
|pitch_abs_mean|0.11640|0.10955–0.12463|
|roll_abs_mean|0.10581|0.10080–0.11682|
|wheel_offset_MAE_m|0.21084|0.20983–0.21327|
|leg_length_diff_MAE_m|0.02577|0.02510–0.02657|
|hip_mirror_MAE_rad|0.51682|0.51218–0.52476|
|active_mirror_MAE_rad|0.72266|0.71821–0.72926|

几何：轮差为轮心沿水平投影native forward=-rootZ的错位；腿长为声明hip anchor至轮心欧氏长度；hip镜像abs(qLhip+qRhip)、active镜像abs(qLactive-qRactive)。关节误差与实体腿长差不可互相替代。双轮接触为传感器合力>2N，不称法向载荷。均值包含失败前变化。

共同最早2秒：实际高度.40358m、mean abs vx .24865、接触.983125、触限.270625。开始能维持高姿态，但没降至.34，随后明显滑行/失触/姿态恶化。不能认为旧v10改命令即可良好站立，也不能据此认为31D不可学。

工程修改：students/requests.py增加显式MCU student command_height_m校验；students/evaluator.py在reset前注入并退出恢复；tests/test_student_diagnostic_height.py新增两项，另student_interface/mcu_v2十项通过，py_compile/diff检查通过。无reward/网络/物理修改，无自动续训/通知。

16_56声明缺teacher manifest来源绑定，在reserve前拒绝，无仿真；16_59新声明绑定v10自己的数据manifest后READY，不更改旧声明。

下一步先看已有0.34站立专项最新独立证据，再决定重新训练来源；本次仅PPO0，不授予训练。
