# 可复用键盘GUI入口

固定脚本：`/home/kellen/wheel_leg_native_train/scripts/play_motion_keyboard.py`。
使用原生150D actor、闭链USD、plane和原有PD；无PPO、无checkpoint写入。
运行代码固定引用项目内`isolated/motion_gpu1_20261002/src/`，
不加载其他训练框架，不依赖调用时的cwd或PYTHONPATH。

## 默认模型

默认加载运动smoke update5。桌面终端执行：

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python \
  /home/kellen/wheel_leg_native_train/scripts/play_motion_keyboard.py --run
```

去掉`--run`仅做CPU身份检查，不打开Isaac或写运行记录。

## 更换模型和参数

```bash
/home/kellen/anaconda3/envs/issaclab/bin/python \
  /home/kellen/wheel_leg_native_train/scripts/play_motion_keyboard.py \
  --checkpoint /home/kellen/wheel_leg_native_train/runs/motion_gpu1_20261002/formal/model_update_100.pt \
  --spec /home/kellen/wheel_leg_native_train/isolated/motion_gpu1_20261002/configs/experiments/motion_gpu1_20261002/spec.json \
  --speed 0.1 --yaw-speed 0.1 --max-wall-seconds 1800 --run
```

| 参数 | 接口含义 |
| --- | --- |
| `--checkpoint` | 要查看的模型绝对路径；保留严格网络/spec/资产身份检查 |
| `--spec` | 模型对应的实验配置；新实验需传其实际spec，不能只换模型后忽略配置 |
| `--speed` | 初始线速度档位，0至`--max-speed` m/s |
| `--yaw-speed` | 初始旋转速度档位，0至`--max-yaw-speed` rad/s |
| `--max-speed` | 箭头调速上限，默认4 m/s，最大4 |
| `--max-yaw-speed` | 箭头调旋转速度上限，默认4 rad/s，最大4 |
| `--max-wall-seconds` | GUI墙钟上限，默认1800秒，最大7200秒 |
| `--run` | 真正启动GUI；不传时只输出plan |
| `--help` | 查看完整参数接口 |

兼容本项目原生STAND/运动150D模型及匹配spec；Recovery、Gym策略或不同
observation/action契约不能通过此入口通用播放。默认来源STAND模型也可
通过`--checkpoint`加载。身份不匹配时先检查模型与spec，不绕过校验。

## 操控

点击GUI视口。W/S前后，A/D原地左右旋转；↑/↓调整线速度档位，每次
0.02 m/s；←/→调整yaw档位，每次0.02 rad/s；范围由两个max参数指定。
松开WASD或Space平滑停车；R复位；Esc退出。
档位、目标命令、执行命令和实际速度分别显示。方向键只调档位，
按住W/S或A/D才发运动命令。yaw未训练，GUI观察不等于能力验收。
允许输入1.0等更大命令，不代表smoke update5已学会这些速度。

## 设备与验证

入口仅为该GUI子进程设置`CUDA_VISIBLE_DEVICES=0,1`：4080/GPU0呈现当前
桌面，3060/GPU1运行物理及策略。不得使用旧的GPU1单卡可见GUI命令；
它会造成renderer枚举或presenting queue错误。不会修改训练进程设置。
需从有效桌面DISPLAY环境运行，脚本不会猜测或重设显示会话。

键盘逻辑4项CPU测试通过。底层GUI此前60秒有界运行正常，设备读回为
RTX3060/cuda:1。新增固定入口已验证默认模型及显式模型的plan-only调用。
