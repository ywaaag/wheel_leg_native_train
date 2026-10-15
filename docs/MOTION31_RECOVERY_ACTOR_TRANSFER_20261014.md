# 独立31D Motion初始化模型迁移

用户明确指定10_16/formal/update300作为来源，只执行离线权重迁移，不启动Motion仿真/PPO或改正在运行的站立链。

## 实际产物

{
  "checkpoint": "/home/kellen/wheel_leg_native_train/isolated/2026_10_14-13_39__motion31_from_recovery_u300/motion_actor_initial.pt",
  "checkpoint_sha256": "a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266",
  "proof": {
    "samples": 3000,
    "naive_switch_action_mae": 0.051426663994789124,
    "naive_switch_action_max": 0.1874675452709198,
    "mapped_action_max": 1.7881393432617188e-07,
    "std_equal": true,
    "scope": "CPU forward identity only; no motion capability evidence"
  },
  "actor_layers": [
    31,
    128,
    64,
    32,
    6
  ],
  "migration": {
    "version": "recovery_to_motion_actor_column_transfer_v1",
    "source_checkpoint": "/home/kellen/wheel_leg_native_train/runs/2026_10_14-10_16__standing034_survival_quality_v14_wiring2/formal/model_update_300.pt",
    "source_sha256": "64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f",
    "source_spec": "/home/kellen/wheel_leg_native_train/configs/experiments/2026_10_14-10_16__standing034_survival_quality_v14_wiring2/spec.json",
    "source_spec_sha256": "b28f87acec36d77c33f06ee7d35072d89416ff942c18261c147f69bba64ed553",
    "mapping": {
      "source_skill": "Recovery",
      "destination_skill": "Motion",
      "source_first_layer_column": 26,
      "destination_first_layer_column": 25
    },
    "target_height_m": 0.34,
    "source_capability": "normal stance30s survival and alignment improvements; full quality gate failed; Swing and motion not certified",
    "initialization_only": true,
    "critic_initialization": "not transferred; fresh49D Critic planned for new Motion recipe",
    "optimizer_initialization": "not transferred; new Adam planned",
    "RNG_restored": false
  },
  "training_ready": false
}

Actor结构31→128→64→32→6，ELU隐藏/Tanh动作均值、相同std及实体动作接口。复制完整Actor，首层Motion输入列25复制来源Recovery列26，其他列/层/bias/std不变；Recovery来源checkpoint原SHA不变。新角色MotionZeroStudent，输出为新初始化checkpoint；未继承recipe_version/旧update/critic/optimizer，因此不会把它解释为旧Recovery续训或已完成Motion训练。

真实3000条观测由SHA绑定source evaluation JSON及NPZ提取，mode映射最大输出差约1.79e-7；CPU前向等价仅证明相同其余输入的初始函数保持，不证明闭环Motion、非零速度、yaw或Swing能力。来源update300完整normal三case24/24生存30秒、质量0/24，遗留pitch和速度问题不会通过模式迁移自动消失。

## 尚未启动的下一步

定义独立Motion版本化配方：相同31D Actor和49D Critic结构，真实vx/yaw/height任务输入、正常站姿reset；明确Motion计时特权的语义。新Critic49/Adam、原Actor/stdwarm-start；不继承Recovery价值和Adam动量。先同协议零命令评估，再低速双向训练和zero/姿态/几何保留检查。新spec/ledger/run/预算及运行授权另立；当前Recovery授权不能用于Motion。

当前学生runtime速度/yaw输入写死零，新Motion训练接线尚未实现；不只是换role或改文件名。不是新网络蒸馏，没有BC数据采集、优化器步或训练指标；不声称快速收敛。

修改文件：students/motion_transfer.py、scripts/migrate_recovery_actor_to_motion.py、tests/test_motion_actor_transfer.py、新报告及TOOL_INDEX/STATUS。CPU迁移/mcu回归7通过；实际保存读回验证、逐列变化检查和源SHA保护通过。精简产物为motion_actor_initial.pt、manifest.json、publication_complete.json，不复制源码/历史轨迹，完整来源引用与代码SHA在manifest；没有Git提交。
