"""人工奖励入口：只在新实验的独立源码副本中使用。

configuration修改权重；evaluate可以追加自己的纯Tensor reward。
context均为post-physics/pre-reset状态，base为现有v10计算结果。
禁止在这里改机器人状态、调用控制器或读Isaac。每秒成本乘dt一次。
"""
import copy
import torch

# 六个连续项的每秒权重；修改这里即可，不必改src下的共享代码。
WEIGHTS = {
    "height_progress": 2.0,
    "support_quality": 3.0,
    "effort": -0.02,
    "target_change": -0.002,
    "post_entry_angular": -0.05,
    "post_entry_velocity": -0.10,
}
WHEEL_SMOOTH_PER_SECOND = -0.20
CONTACT_DEFICIT_PER_SECOND = -0.20
ZERO_VELOCITY_HUBER_PER_SECOND = -1.0
MIRROR_PER_SECOND = -0.05


def configuration(base):
    cfg = copy.deepcopy(base)
    cfg["version"] = "manual_recovery_reward_v1"
    cfg["weights"] = dict(WEIGHTS)
    cfg["hold_wheel_smooth"]["weight_per_s"] = WHEEL_SMOOTH_PER_SECOND
    cfg["hold_contact_deficit"]["weight_per_s"] = CONTACT_DEFICIT_PER_SECOND
    cfg["motion_zero_tracking"]["weight_per_s"] = ZERO_VELOCITY_HUBER_PER_SECOND
    cfg["weak_mirror"]["weight_per_s"] = MIRROR_PER_SECOND
    return cfg


def evaluate(context, base, cfg):
    """返回同样的具名字典；raw→每秒权重→dt→事件奖，保留初始化mask。"""
    result = dict(base)
    fields = ("height_progress", "support_quality", "effort", "target_change",
              "post_entry_angular", "post_entry_velocity")
    result["weighted_density"] = base["raw"] * base["raw"].new_tensor(
        [cfg["weights"][name] for name in fields])
    result["continuous_dt"] = result["weighted_density"] * cfg["dt"]
    result["motion_mirror_weighted_density"] = base["motion_mirror_raw"] * base["raw"].new_tensor(
        [cfg["motion_zero_tracking"]["weight_per_s"], cfg["weak_mirror"]["weight_per_s"]])
    result["motion_mirror_dt"] = result["motion_mirror_weighted_density"] * cfg["dt"]
    for term in ("hold_wheel_smooth", "hold_contact_deficit"):
        result[term + "_density"] = base[term + "_raw"] * cfg[term]["weight_per_s"]
        result[term + "_dt"] = result[term + "_density"] * cfg["dt"]
    result["total"] = (result["continuous_dt"].sum(-1) + base["events"].sum(-1)
        + base["pre_entry_angular_dt"] + result["motion_mirror_dt"].sum(-1)
        + result["hold_wheel_smooth_dt"] + result["hold_contact_deficit_dt"])
    # 自定义例子（默认不启用）：只罚入口后的pitch，单位为rad。
    # custom_density = -0.1 * context['angles'][:, 0].square() * context['entered']
    # result['total'] += custom_density * cfg['dt']
    return result
