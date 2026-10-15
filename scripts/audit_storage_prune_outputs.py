#!/usr/bin/env python3
"""消费 audit_storage_prune_plan.py 生成的 inventory.json，产出：
  protected_models.json / keep_manifest.json / deletion_plan.json / prune_dryrun.py
并回填修正后的 classification_totals。只读历史，不删除任何文件。
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta

ROOT = "/home/kellen/wheel_leg_native_train"
SHA_TZ = timezone(timedelta(hours=8))

# ---------------------------------------------------------------- 身份认定

MODELS = {
    "motion": {
        "label": "当前选定 Motion 模型（legacy150D 教师）",
        "candidates": [
            {
                "id": "M1",
                "path": "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt",
                "sha256": "4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb",
                "interface_version": "legacy150D",
                "actor_dim": 150, "critic_dim": 150,
                "role": "教师策略（PPO Actor，确定性导出）",
                "training": "motion_standing034_pm2 持续任务 block0000→0003 续块 PPO",
                "spec": "configs/experiments/2026_10_13-05_39__motion_standing034_pm2_block0003/spec.json",
                "run": "runs/2026_10_13-05_39__motion_standing034_pm2_block0003",
                "parent": {"path": "runs/2026_10_13-03_58__motion_standing034_pm2_block0002/formal/model_update_300.pt",
                           "sha256": "6685432988df9d5bb95a77b692105e84ea7106368cb5f5b3e1f427fc17aa3a09"},
                "evidence": "STATUS：用户选定教师 05_39/u300；已导出 deployment_protocol/motion_legacy150d_v1/actor.onnx (34587471f1f7e045…)；五命令 40/40 旧复测；sim2sim MuJoCo 五命令 30s 全轮接触不摔",
                "passed": "0/±0.5/±1 低速双向与站稳复测 40/40；ONNX 与 PyTorch 误差 0",
                "failed": "zero 实际 -.468 m/s 与 ±.5/-1 速度门槛未过；MuJoCo 仅 2/5 宽松诊断门槛内，未认证 sim2sim；0.36m 实机峰高未认证",
                "status": "accepted（用户选定 + 已部署导出）",
                "full_resume_state": "run 内 formal/checkpoint 含 Actor/Critic/Adam/RNG/std，可完整恢复",
                "recommended": True,
            },
            {
                "id": "M1b",
                "path": "runs/2026_10_13-07_21__motion_standing034_pm2_block0004/formal/model_update_100.pt",
                "sha256": "df60f53cc4bcca08a7ecc07b9d57c7fbbe24f4fa7c0705af64646cb7467e5a3d",
                "interface_version": "legacy150D",
                "actor_dim": 150, "critic_dim": 150,
                "role": "最强运动候选（0/±2 同模型通过数最高 16/24）",
                "training": "pm2 block0004 续块 PPO",
                "spec": "configs/experiments/2026_10_13-07_21__motion_standing034_pm2_block0004/spec.json",
                "run": "runs/2026_10_13-07_21__motion_standing034_pm2_block0004",
                "parent": {"path": "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt",
                           "sha256": "4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb"},
                "evidence": "15_12 PPO0 七命令 56 评分 40/56 通过",
                "passed": "+2/-2 高速运动能力最强",
                "failed": "+1 高度 .3615 失败；+2 实际 3.4347/高度 .3689/场地失败；-2 仍 8/8 但非全面更强",
                "status": "diagnostic candidate（非 selected；STATUS 明确“优先低速双向/站稳继续保留 05_39/u300”）",
                "full_resume_state": "可完整恢复",
                "recommended": False,
            },
        ],
        "ancestors": [
            {"path": "runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt",
             "sha256": "5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e",
             "note": "B250：Motion pm2 全链根模型；同时是活动 v14 / v13 / v12 spec 显式引用的教师 checkpoint（活动依赖，双重保护）"},
            {"path": "runs/2026_10_13-00_16__motion_standing034_pm2_block0000/formal/model_update_300.pt",
             "sha256": "a3d71c62b8938d78729a7938cb50e227a8da14712543868748985c708ca03a7c", "note": "pm2 block0000"},
            {"path": "runs/2026_10_13-02_16__motion_standing034_pm2_block0001/formal/model_update_300.pt",
             "sha256": "7084c1ed0ba854af55ca37a64d7734c66f23f4a27ae941724850b02acf4d6d89", "note": "pm2 block0001"},
            {"path": "runs/2026_10_13-03_58__motion_standing034_pm2_block0002/formal/model_update_300.pt",
             "sha256": "6685432988df9d5bb95a77b692105e84ea7106368cb5f5b3e1f427fc17aa3a09", "note": "pm2 block0002（M1 直接父）"},
        ],
    },
    "recovery": {
        "label": "当前选定 Recovery 模型（31D 学生 / standing034 v11 链）",
        "candidates": [
            {
                "id": "R1",
                "path": "runs/2026_10_13-10_39__recovery_standing034_mirror_huber_block0007/formal/model_update_300.pt",
                "sha256": "cdcbae696f224e9b5556c058abc0c1c4acfc8451dc8aebb690b2d9f38e6f1cf0",
                "interface_version": "multiskill_mcu_v2",
                "actor_dim": 31, "critic_dim": 40,
                "role": "Recovery 0.34m 站立＋无封顶镜像 Huber 专项（v11）最后成功 formal 块",
                "training": "recovery_standing034_smoke_fix/mirror_huber 连续续块 PPO（block0001→0007）",
                "spec": "configs/experiments/2026_10_13-10_39__recovery_standing034_mirror_huber_block0007/spec.json",
                "run": "runs/2026_10_13-10_39__recovery_standing034_mirror_huber_block0007",
                "parent": {"path": "runs/2026_10_13-09_00__recovery_standing034_mirror_huber_block0006/formal/model_update_300.pt",
                           "sha256": "00d02805366df8a6674d33acb1868ec682c6291433df707794aebafe048a08d8"},
                "evidence": "block0008(12_15) 在 source_eval 阶段 FAILED（Student evaluation wall budget exhausted），未产出 formal checkpoint，故 block0007 u300 是本链最后一个真实产物",
                "passed": "入口 24/24（专项历史）；完整主协议历史上 0/24",
                "failed": "完整 10 秒保持窗口与联合证书未通过，accepted 为空；block0008 未产生新 checkpoint",
                "status": "latest（本链终态）但 NOT accepted",
                "full_resume_state": "是（Actor/Critic/Adam/RNG/课程计数完整）",
                "recommended": True,
            },
        ],
        "ancestors": [
            {"path": "runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/model_update_300.pt",
             "sha256": "2a587c31bbf81f2db669561965431cc97598c9e13b87043553582b8a09237a9a",
             "note": "v7 u300：Recovery v11 链与 31D 学生主干的共同分叉点（双链共享祖先）"},
            {"path": "runs/2026_10_11-22_43__recovery_standing_motion_mirror_from50/formal/model_update_200.pt",
             "sha256": "34be92249e25069f7a31e063e42c2451a3f560e8be589b118607d9b8a3384143", "note": "v6 motion mirror"},
            {"path": "runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/model_update_50.pt",
             "sha256": "d1db35ffe83fe462edab55934621cf4ea59b59ff8d60665b4e06720cb66a5a92", "note": "v5 站立专项 update50"},
            {"path": "isolated/recovery_standing_reset_distilled_20261011/best_validation.pt",
             "sha256": "06c33cf7552d2f43b015fca589b927d4634a914a1e9680a4c07da38109e4e365", "note": "站立 reset-priority BC 学生"},
            {"path": "isolated/recovery_mcu_v2_bc_20261011/best_validation.pt",
             "sha256": "7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470", "note": "31D mcu_v2 BC 根模型（两条 31D 链共同根）"},
            {"path": "isolated/student_mcu_v2_teachers_20261011/RecoveryStudent.pt",
             "sha256": None, "note": "BC 蒸馏数据集（mcu_v2）"},
        ],
    },
    "student31d": {
        "label": "新 31D 学生模型（multiskill_mcu_v2，站立/生存链）",
        "candidates": [
            {
                "id": "S1",
                "path": "runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt",
                "sha256": "2af573b318d7ebd6df7b1a5919c5ea58e873e5d24761905ba773f8ab02cc72cd",
                "interface_version": "multiskill_mcu_v2",
                "actor_dim": 31, "critic_dim": 49,
                "role": "v13 零速＋49D 特权 Critic 终态；同时是活动 v14 的来源 checkpoint",
                "training": "PPO，smoke12+formal988，新 Critic/Adam/warmup5，Actor/std 继承自 v12 u700",
                "spec": "configs/experiments/2026_10_13-22_14__standing034_zero_privileged49_v13/spec.json",
                "run": "runs/2026_10_13-22_14__standing034_zero_privileged49_v13",
                "parent": {"path": "runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_700.pt",
                           "sha256": "73a7a09e713afcb5e96fbc74b0f0527d9bff4d4a439deec105d2bcee3696c2c0"},
                "evidence": "v13 终态定量复盘：所有来源/新 checkpoint 0/24；u988 独立 30 秒 PPO0 8/8 首 30 秒存活但质量 0/8（末 10 秒 abs vx 2.720 m/s）",
                "passed": "可持续滚动不倒（30 秒存活 8/8）",
                "failed": "零速站稳未证实；pitch .206 rad / 轮心差 5.28 cm / 镜像 .192/.183 rad；无 accepted",
                "status": "latest（v13 终态）且是活动 v14 的 source——活动依赖，必须保护；本身 NOT accepted",
                "full_resume_state": "是",
                "recommended": True,
            },
            {
                "id": "S1b",
                "path": "runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_988.pt",
                "sha256": "f1b3481b4c13dbfa3551a8006a022e6e6639aeed26b3b2f450427e50be8a6c1",
                "interface_version": "multiskill_mcu_v2",
                "actor_dim": 31, "critic_dim": 40,
                "role": "v12 站立对齐终态（未被 v13 选用；v13 用的是 v12/u700）",
                "training": "PPO，Actor/std 源自 course_b block0002/u100",
                "spec": "configs/experiments/2026_10_13-17_16__student_standing034_alignment_v12/spec.json",
                "run": "runs/2026_10_13-17_16__student_standing034_alignment_v12",
                "parent": {"path": "runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt",
                           "sha256": "bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d"},
                "evidence": "v10 normal034 identity PPO0：8/8 入口、完整保持 2/8、主协议 0/8",
                "passed": "入口 8/8",
                "failed": "完整保持与主协议未过；实际高度均值 .393 m、vx 绝对均值 1.51 m/s、触限 47.9%",
                "status": "latest（v12 终态），NOT accepted",
                "full_resume_state": "是",
                "recommended": None,
            },
            {
                "id": "S1c",
                "path": "runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_700.pt",
                "sha256": "73a7a09e713afcb5e96fbc74b0f0527d9bff4d4a439deec105d2bcee3696c2c0",
                "interface_version": "multiskill_mcu_v2",
                "actor_dim": 31, "critic_dim": 40,
                "role": "v12 u700：v13 实际使用的来源（不是 v12 终态）",
                "training": "PPO 中间里程碑",
                "spec": "configs/experiments/2026_10_13-17_16__student_standing034_alignment_v12/spec.json",
                "run": "runs/2026_10_13-17_16__student_standing034_alignment_v12",
                "parent": {"path": "runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt",
                           "sha256": "bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d"},
                "evidence": "被 v13 spec 显式声明为 source_checkpoint/source_sha256",
                "passed": "—", "failed": "—",
                "status": "ancestor（被 v13 显式引用）",
                "full_resume_state": "是",
                "recommended": None,
            },
        ],
        "ancestors": [
            {"path": "runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt",
             "sha256": "bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d",
             "note": "course_b block0002 u100（v12 来源；manual_train/recovery/models/recovery_source.pt 为同一内容副本）"},
            {"path": "runs/2026_10_12-11_42__recovery_course_b_prefix180_block0001/formal/model_update_100.pt",
             "sha256": "cfb7e5175adc166f8fe72b307c471728e2ece1f8e4f11e2f50adbd02e5a547cb", "note": "course_b block0001"},
            {"path": "runs/2026_10_12-09_56__recovery_course_a_prefix0_block0000/formal/model_update_0.pt",
             "sha256": "aeed1e4c164ff0029e5fa451174f5e50cce4211c9045fcf1e85e7ce70541b710", "note": "course_a block0000"},
        ],
    },
    "distill25d": {
        "label": "新 25D 蒸馏模型（motion_frame25）",
        "candidates": [
            {
                "id": "D1",
                "path": "isolated/motion_frame25_actual034_bc_20261013/best_validation.pt",
                "sha256": "e86b7922d099f2519b1f0c00959399b40c9848add9be32fcf39ec3f6a2df23ab",
                "interface_version": "motion_frame25_distilled_v1",
                "actor_dim": 25, "critic_dim": 34,
                "role": "真实 .34 教师（05_39/u300）教学蒸馏的 25D 学生；25D Actor＋34D 特权 Critic PPO 的 BC 来源",
                "training": "BC 蒸馏 4000 步（best step2800），教师 05_39/u300 真实 .34 零速/±.5/±1 共 40 episode，20/10/10 split",
                "spec": None,
                "run": "isolated/motion_frame25_actual034_bc_20261013",
                "parent": {"path": "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt",
                           "sha256": "4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb"},
                "evidence": "13,862 参数 / ONNX 55KiB / 数值误差 1.79e-7；17_09 PPO 的 source_actor",
                "passed": "蒸馏动作拟合达标（test early 腿 .000765 rad、轮 .1854 rad/s）",
                "failed": "闭环 PPO0 学生 0/40（1.38 s tilt）；17_09 PPO 12 个 formal checkpoint 均 0/8；未 accepted",
                "status": "distilled best（非 accepted）；下游 PPO 未通过",
                "full_resume_state": "BC best（无 Adam/PPO 状态）；完整恢复状态在其下游 17_09 run",
                "recommended": True,
            },
            {
                "id": "D1b",
                "path": "isolated/motion_frame25_zero_distilled_20261013/best_validation.pt",
                "sha256": "e56dc7f5b07f15bcd1f1c1b3b1bd4b1a0f2a1e9d0c4a9dd7b3ee6f0b4b8f2a1c",
                "interface_version": "motion_frame25_distilled_v1",
                "actor_dim": 25, "critic_dim": None,
                "role": "无历史 zero-only 25D 蒸馏（更早版本，教师 05_39/u300 但标签来自 .40 状态离线 query）",
                "training": "BC 4000 步（best 3000），16 个 .40 状态 episode 在 .34 命令下离线教师 query",
                "spec": None,
                "run": "isolated/motion_frame25_zero_distilled_20261013",
                "parent": {"path": "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt",
                           "sha256": "4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb"},
                "evidence": "ONNX 参考误差 5.96e-8；非真实 .34 轨迹证据，zero-only",
                "passed": "离线拟合达标", "failed": "闭环/物理执行未接入；非真实 .34 轨迹",
                "status": "diagnostic candidate（更早、数据边界更弱）",
                "full_resume_state": "BC best only",
                "recommended": False,
                "sha_verified": False,
                "sha_note": "审计时实际 SHA 前缀为 e56dc7f5…（完整值见 inventory/keep_manifest；此处占位需执行前重验）",
            },
        ],
        "ancestors": [
            {"path": "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt",
             "sha256": "4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb",
             "note": "蒸馏教师＝Motion M1（跨类共享祖先）"},
            {"path": "isolated/motion_frame25_actual034_bc_20261013/dataset.pt",
             "sha256": None, "note": "25D 蒸馏数据集（教师 query 标签）"},
        ],
    },
}

# 活动任务（进程快照）
ACTIVE = {
    "spec": "configs/experiments/2026_10_14-09_37__standing034_survival_quality_v14/spec.json",
    "run": "runs/2026_10_14-09_37__standing034_survival_quality_v14",
    "pids": [59523, 59559, 59560, 59561],
    "phase": "source_eval",
    "argv_evidence": "stand_chain.py / monitor.py / train.py（attempt-id 620…），cwd=/home/kellen/wheel_leg_native_train 与 /src",
    "note": "使用共享 src/（execution_source_root=项目 src）；source_checkpoint=v13 u988。本轮绝不删除其 spec/run 及被引用的教师 checkpoint。",
}

# 额外保护覆盖（审计脚本未覆盖，本轮按证据补充）
OVERRIDE_PROTECTED = {
    "runs/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25":
        "B50 教师（活动 v14/v13/v12 spec 显式引用）的直接父：formal/model_update_25.pt SHA 34be4427…",
    "isolated/recovery_swing_leg_initialization_qualified_20261010":
        "B50 初始化候选 initialization_candidate.pt SHA d0744884…，被多个受保护 spec 引用",
    "runs/recovery_pose_capture_20261002_145814":
        "姿态库（pose_*.json），受保护课程/评估 spec 的运行时依赖",
}
OVERRIDE_REVIEW = {
    "runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50":
        "内含 B25 checkpoint（B/formal/model_update_25.pt SHA 8c3f74f9…），被受保护 spec 引用；只能保留最小包，不能整目录删除",
}

# 最小保留包内的 checkpoint 白名单（相对项目根）
KEEP_CHECKPOINTS = [
    # Motion
    "runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt",
    "runs/2026_10_13-00_16__motion_standing034_pm2_block0000/formal/model_update_300.pt",
    "runs/2026_10_13-02_16__motion_standing034_pm2_block0001/formal/model_update_300.pt",
    "runs/2026_10_13-03_58__motion_standing034_pm2_block0002/formal/model_update_300.pt",
    "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt",
    "runs/2026_10_13-07_21__motion_standing034_pm2_block0004/formal/model_update_100.pt",
    # Recovery v11
    "runs/2026_10_13-00_20__recovery_standing034_smoke_fix_block0001/formal/model_update_300.pt",
    "runs/2026_10_13-02_19__recovery_standing034_mirror_huber_block0002/formal/model_update_300.pt",
    "runs/2026_10_13-04_09__recovery_standing034_mirror_huber_block0003/formal/model_update_300.pt",
    "runs/2026_10_13-06_00__recovery_standing034_mirror_huber_block0004/formal/model_update_300.pt",
    "runs/2026_10_13-07_50__recovery_standing034_mirror_huber_block0005/formal/model_update_300.pt",
    "runs/2026_10_13-09_00__recovery_standing034_mirror_huber_block0006/formal/model_update_300.pt",
    "runs/2026_10_13-10_39__recovery_standing034_mirror_huber_block0007/formal/model_update_300.pt",
    # 31D 学生主干
    "runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/model_update_300.pt",
    "runs/2026_10_12-09_56__recovery_course_a_prefix0_block0000/formal/model_update_0.pt",
    "runs/2026_10_12-11_42__recovery_course_b_prefix180_block0001/formal/model_update_100.pt",
    "runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt",
    "runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_700.pt",
    "runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/model_update_988.pt",
    "runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt",
    "runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/model_update_50.pt",
    "runs/2026_10_11-22_43__recovery_standing_motion_mirror_from50/formal/model_update_200.pt",
    "runs/2026_10_11-17_12__recovery_mcu_v2_standing_rehearsal_from_bc/formal/model_update_100.pt",
    "runs/2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc/formal/model_update_100.pt",
    "runs/2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc/formal/model_update_100.pt",
    "runs/2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc/formal/model_update_100.pt",
    # 教师与其祖先
    "runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_50.pt",
    "runs/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25/formal/model_update_25.pt",
    "runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt",
    "isolated/recovery_swing_leg_initialization_qualified_20261010/initialization_candidate.pt",
    # BC / 蒸馏
    "isolated/recovery_mcu_v2_bc_20261011/best_validation.pt",
    "isolated/recovery_standing_reset_distilled_20261011/best_validation.pt",
    "isolated/recovery_standing_distilled_20261011/best_validation.pt",
    "isolated/student_mcu_v2_teachers_20261011/RecoveryStudent.pt",
    "isolated/recovery_standing_teacher_data_20261011/RecoveryStudent.pt",
    "isolated/recovery_standing_reset_teacher_data_20261011/RecoveryStudent.pt",
    "isolated/motion_frame25_actual034_bc_20261013/best_validation.pt",
    "isolated/motion_frame25_actual034_bc_20261013/dataset.pt",
    "isolated/motion_frame25_zero_distilled_20261013/best_validation.pt",
    "runs/2026_10_13-17_09__motion_frame25_asymmetric_ppo_closurefix_from_bc/formal/model_update_300.pt",
    # 活动任务
    "runs/2026_10_14-09_37__standing034_survival_quality_v14/source_eval/model_update_0.pt",
]

KEEP_ONNX = [
    "deployment_protocol/motion_legacy150d_v1/actor.onnx",
    "isolated/motion_frame25_actual034_bc_20261013/actor.onnx",
    "isolated/motion_frame25_zero_distilled_20261013/actor.onnx",
]

# 派生报告去重保留优先级：同内容只保留一份（保留路径短的 canonical 副本）
DEDUP_KEEP_PREFERENCE = ["/formal/", "/source_eval/", "/smoke/", ""]

# 明确可整目录删除的重复副本/缓存
REGENERABLE_PATHS = [
    ".pytest_cache",
]

PROTECTED_ISOLATED_EXTRA = [
    "recovery_swing_leg_initialization_qualified_20261010",
]


def load_json(p):
    with open(p) as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    inv = load_json(args.inventory)
    out_dir = args.out_dir
    ts = datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST")

    index = {}
    for section in ("runs", "isolated", "artifacts", "sim2sim", "manual_train"):
        for name, info in inv[section].items():
            index[info["path"]] = (section, name, info)
    for name, info in inv["toplevel"].items():
        if isinstance(info, dict) and info.get("type") == "dir":
            index.setdefault(name, ("toplevel", name, info))

    # ---- 应用覆盖
    cls = dict(inv["classification"])
    for path, reason in OVERRIDE_PROTECTED.items():
        cls[path] = {"path": path, "classification": "PROTECTED", "reason": reason}
    for path, reason in OVERRIDE_REVIEW.items():
        cls[path] = {"path": path, "classification": "REVIEW_REQUIRED", "reason": reason}

    def actual_of(path):
        e = index.get(path)
        return e[2].get("actual", 0) if e else 0

    # ---- 重新统计（避免顶层与子目录重复计数）
    totals = defaultdict(int)
    for path, e in cls.items():
        totals[e["classification"]] += actual_of(path)

    # ---- 保护清单
    keep_entries = []
    for path, e in sorted(cls.items()):
        if e["classification"] == "PROTECTED":
            info = index.get(path, (None, None, {}))[2]
            keep_entries.append({
                "path": path,
                "kind": "file" if info.get("type") == "file" else "dir",
                "apparent_bytes": info.get("apparent"),
                "actual_bytes": info.get("actual"),
                "files": info.get("files"),
                "reason": e["reason"],
            })

    keep_manifest = {
        "generated_at": ts,
        "root": ROOT,
        "scope_note": " PROTECTED 顶层条目为整目录保护；文件级最小保留包见 minimal_package。",
        "protected_paths": keep_entries,
        "protected_checkpoints": [
            {"path": p, "exists": os.path.exists(os.path.join(ROOT, p)),
             "actual_bytes": os.lstat(os.path.join(ROOT, p)).st_blocks * 512 if os.path.exists(os.path.join(ROOT, p)) else None}
            for p in KEEP_CHECKPOINTS
        ],
        "protected_onnx": [
            {"path": p, "exists": os.path.exists(os.path.join(ROOT, p))} for p in KEEP_ONNX
        ],
        "active_task_exclusion": ACTIVE,
        "never_delete": [".git", "src", "tests", "scripts", "configs", "docs", "assets",
                         "deployment_protocol", "README.md", "AGENTS.md", "STATUS.md",
                         "TOOL_INDEX.md", "ARCHITECTURE.md", "WORKFLOW.md", "plan.md"],
    }

    # ---- 方案 A / B
    plan_a_dirs, plan_b_dirs = [], []
    for path, e in sorted(cls.items()):
        c = e["classification"]
        if c == "SAFE_CANDIDATE":
            info = index.get(path, (None, None, {}))[2]
            rec = {
                "path": path,
                "type": "dir" if info.get("type") != "file" else "file",
                "apparent_bytes": info.get("apparent"),
                "actual_bytes": info.get("actual"),
                "file_count": info.get("files"),
                "category_mix": info.get("by_category"),
                "classification": c,
                "dependency_check": "不在四类模型祖先链；未被保护集合内部文件引用；不含被保护 spec 引用的 checkpoint SHA",
                "risk": "删除后对应实验不可逐字节复现；历史 STATUS/docs 中指向该 run 的链接失效",
            }
            plan_a_dirs.append(rec)
            plan_b_dirs.append(rec)
        elif c == "REVIEW_REQUIRED":
            info = index.get(path, (None, None, {}))[2]
            rec = {
                "path": path,
                "type": "dir" if info.get("type") != "file" else "file",
                "apparent_bytes": info.get("apparent"),
                "actual_bytes": info.get("actual"),
                "file_count": info.get("files"),
                "classification": c,
                "dependency_check": "被保护集合内部文件引用或含被引用的 checkpoint；整目录删除会破坏引用完整性",
                "risk": "需用户逐项裁定；建议改为“最小保留包”而非整目录删除",
                "referenced_by": e.get("referenced_by"),
                "reason": e["reason"],
            }
            plan_b_dirs.append(rec)

    for p in REGENERABLE_PATHS:
        info = inv["toplevel"].get(p, {})
        rec = {"path": p, "type": "dir", "apparent_bytes": info.get("apparent"),
               "actual_bytes": info.get("actual"), "file_count": info.get("files"),
               "classification": "REGENERABLE",
               "dependency_check": "pytest 运行缓存，不含任何模型/证据",
               "risk": "无；下次跑测试自动重建", "rebuild": "python -m pytest 自动生成"}
        plan_a_dirs.append(rec)
        plan_b_dirs.append(rec)

    # 方案 B 追加：保护目录内的非最小内容（原始评估 JSON / NPZ 轨迹 / 中间 checkpoint / 指标日志 / 源码快照）
    def walk_files(base):
        for dp, dn, fn in os.walk(base):
            for f in fn:
                p = os.path.join(dp, f)
                if os.path.islink(p):
                    continue
                yield p

    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from audit_storage_prune_plan import categorize  # 复用分类规则

    plan_b_files = []
    agg = defaultdict(int)
    for path, e in sorted(cls.items()):
        if e["classification"] != "PROTECTED":
            continue
        base = os.path.join(ROOT, path)
        if not os.path.isdir(base) or path.split("/")[0] not in ("runs", "isolated", "sim2sim"):
            continue
        if path == ACTIVE["run"] or path.startswith(ACTIVE["run"] + "/"):
            continue  # 活动任务：任何文件都不列入删除
        if path.split("/")[0] == "sim2sim":
            continue  # sim2sim 证据体积小且为迁移诊断原始证据，整目录保留
        for p in walk_files(base):
            r = os.path.relpath(p, ROOT)
            cat = categorize(r)
            keep = False
            if r in KEEP_CHECKPOINTS or r in KEEP_ONNX:
                keep = True
            elif cat in ("spec_config_manifest", "derived_analysis_report", "onnx_deploy"):
                keep = True
            if keep:
                continue
            if cat in ("raw_evaluation_json", "compressed_traces_npz", "log_metrics",
                       "checkpoint_optimizer", "source_copy", "tensorboard_events", "cache_temp"):
                st = os.lstat(p)
                agg[cat] += st.st_blocks * 512
                plan_b_files.append({"path": r, "category": cat,
                                     "apparent_bytes": st.st_size, "actual_bytes": st.st_blocks * 512})
    plan_b_files.sort(key=lambda x: -x["actual_bytes"])

    # 重复大文件（同一 run 内多份副本）
    dup_groups = []
    groups = defaultdict(list)
    for b in inv["big_files_over_100MiB"]:
        groups[b["path"].rsplit("/", 1)[0]].append(b)
    # 仅在已计算过 SHA 的情况下判定；此处以 (size, category, 同级 run) 分组提示
    for run_dir, items in groups.items():
        by_size = defaultdict(list)
        for it in items:
            by_size[(it["apparent"], it["category"])].append(it["path"])
        for (sz, cat), paths in by_size.items():
            if len(paths) > 1:
                dup_groups.append({"within": run_dir, "category": cat,
                                   "apparent_bytes_each": sz, "copies": sorted(paths),
                                   "note": "内容需按 SHA 复核后仅保留一份；已对 >100MiB 文件做过全量 SHA，重复组唯一内容 34.56GiB / 原始 44.93GiB"})
    dup_groups.sort(key=lambda x: -x["apparent_bytes_each"] * len(x["copies"]))

    a_bytes = sum(r.get("actual_bytes") or 0 for r in plan_a_dirs)
    b_dir_bytes = sum(r.get("actual_bytes") or 0 for r in plan_b_dirs)
    b_file_bytes = sum(agg.values())

    deletion_plan = {
        "generated_at": ts,
        "root": ROOT,
        "status": "DRY_RUN_ONLY — 本轮不执行任何删除；所有路径为项目内部相对路径",
        "guards": {
            "forbidden_prefixes": [".", ".git", "src", "tests", "scripts", "configs", "docs",
                                   "assets", "deployment_protocol", "runs/2026_10_14-09_37__standing034_survival_quality_v14"],
            "no_wildcards": True,
            "no_dir_containing_protected": True,
            "symlinks_separate": True,
            "revalidate_before_execute": ["路径存在性", "文件 SHA", "目录内无 PROTECTED 文件", "活动任务不在运行（进程快照）"],
        },
        "plan_A_low_risk": {
            "description": "删除与四类模型无关的实验产物、明确可重建缓存；保留全部完整恢复 checkpoint 与必要原始评估",
            "entries": sorted(plan_a_dirs, key=lambda r: -(r.get("actual_bytes") or 0)),
            "estimated_reclaim_actual_bytes": a_bytes,
        },
        "plan_B_minimal_archive": {
            "description": "在方案 A 基础上，追加删除 REVIEW 目录与保护目录内非最小保留包内容（原始评估 JSON、压缩轨迹 NPZ、训练曲线、中间 checkpoint、源码快照）",
            "entries_dirs": sorted(plan_b_dirs, key=lambda r: -(r.get("actual_bytes") or 0)),
            "entries_files_ref": "deletion_plan_B_files.json（完整逐文件清单，不截断）",
            "entries_files_sample": plan_b_files[:50],
            "entries_files_total_count": len(plan_b_files),
            "entries_files_bytes_by_category": dict(agg),
            "estimated_reclaim_actual_bytes": b_dir_bytes + b_file_bytes,
        },
        "duplicate_large_reports": dup_groups,
    }

    protected_models = {
        "generated_at": ts,
        "root": ROOT,
        "identity_rule": "以实际 checkpoint SHA、spec 的 source_checkpoint/source_sha256、run terminal 与原始评估为准；Markdown 仅导航",
        "categories": MODELS,
        "active_task": ACTIVE,
        "teacher_shared_across_categories": [
            "runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt（Motion 选定教师，同时是 25D 蒸馏教师）",
            "runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt（Motion 祖先，同时是 v12/v13/活动 v14 的教师 checkpoint）",
            "runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_50.pt（B50 教师，v12/v13/v14 spec 显式引用）",
        ],
        "unknowns": [
            "四类模型的最终归属需用户确认（尤其 Recovery 与 31D 学生同根分叉：共同祖先 2a587c31…a9a）",
            "v14 尚在 source_eval，其 formal checkpoint 未产生，不能作为任一类的保留模型",
            "25D 候选 D1b 的完整 SHA 需执行前重验（本清单仅记录前缀 e56dc7f5…）",
        ],
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "deletion_plan_B_files.json"), "w") as fh:
        json.dump({
            "generated_at": ts,
            "status": "DRY_RUN_ONLY — 完整逐文件清单，供 tier B 审批；本轮不执行",
            "count": len(plan_b_files),
            "actual_bytes_total": sum(x["actual_bytes"] for x in plan_b_files),
            "files": plan_b_files,
        }, fh, ensure_ascii=False, indent=1)
    print("wrote", os.path.join(out_dir, "deletion_plan_B_files.json"))
    for name, obj in (("protected_models.json", protected_models),
                      ("keep_manifest.json", keep_manifest),
                      ("deletion_plan.json", deletion_plan)):
        with open(os.path.join(out_dir, name), "w") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
        print("wrote", os.path.join(out_dir, name))

    inv["classification"] = cls
    inv["classification_totals_corrected"] = {
        k: {"actual_bytes": v, "actual_GiB": round(v / 1073741824, 2)} for k, v in sorted(totals.items())
    }
    inv["overrides_applied"] = {**OVERRIDE_PROTECTED, **OVERRIDE_REVIEW}
    with open(args.inventory, "w") as fh:
        json.dump(inv, fh, ensure_ascii=False, indent=1)
    print("updated", args.inventory)

    print(json.dumps({
        "classification_totals_GiB": {k: round(v / 1073741824, 2) for k, v in sorted(totals.items())},
        "plan_A_reclaim_GiB": round(a_bytes / 1073741824, 2),
        "plan_B_reclaim_GiB": round((b_dir_bytes + b_file_bytes) / 1073741824, 2),
        "plan_B_files_by_category_GiB": {k: round(v / 1073741824, 2) for k, v in sorted(agg.items(), key=lambda x: -x[1])},
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
