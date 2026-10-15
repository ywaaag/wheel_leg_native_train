#!/usr/bin/env python3
"""只读磁盘/身份审计：生成精简方案（report/inventory/protected_models/keep_manifest/deletion_plan）。

本脚本只读取文件并写入一个新的带时间戳审计目录，不删除、移动、压缩或改写任何历史产物。
用法：
  PYTHONDONTWRITEBYTECODE=1 /home/kellen/anaconda3/envs/issaclab/bin/python \
      scripts/audit_storage_prune_plan.py --output-dir artifacts/<时间戳>__storage_prune_audit
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta

ROOT = "/home/kellen/wheel_leg_native_train"
SHA_TZ = timezone(timedelta(hours=8))

# ---------------------------------------------------------------- 分类规则

CATEGORY_RULES = [
    ("checkpoint_optimizer", lambda p, f: f.endswith(".pt")),
    ("onnx_deploy", lambda p, f: f.endswith(".onnx")),
    ("tensorboard_events", lambda p, f: "tfevents" in f),
    ("cache_temp", lambda p, f: f.endswith(".tmp") or f.endswith(".pyc") or "__pycache__" in p or ".pytest_cache" in p),
    ("source_copy", lambda p, f: "source_snapshot" in p or p.endswith("/src") or "/src/" in p or "frozen" in os.path.basename(os.path.dirname(p))),
    ("log_metrics", lambda p, f: f.endswith(".log") or f.endswith(".jsonl")),
    ("raw_evaluation_json", lambda p, f: f.startswith("evaluation") and f.endswith(".json")),
    ("derived_analysis_report", lambda p, f: f in {
        "analysis.json", "chain_terminal_report.json", "candidate_selection.json",
        "candidate_registry.json", "completion_report.md", "audit.json", "review.json",
        "result.json", "validation_result.json", "preparation_manifest.json",
    } or f.endswith("_review.json") or f.endswith("_audit.json")),
    ("compressed_traces_npz", lambda p, f: f.endswith(".npz")),
    ("spec_config_manifest", lambda p, f: f in {
        "spec.json", "budget.json", "manifest.json", "configuration.json",
        "publication_complete.json", "authorization_receipt.json", "task_manifest.json",
        "chain_progress.json", "run_state.json", "supervisor_terminal.json",
        "startup_handshake.json", "report_ready.json", "cleanup.json",
    } or f.startswith("actor_update_proof")),
]

GENERIC = "other_json_text"


def categorize(path: str) -> str:
    f = os.path.basename(path)
    for name, rule in CATEGORY_RULES:
        try:
            if rule(path, f):
                return name
        except Exception:
            pass
    return GENERIC


# ---------------------------------------------------------------- 保护集合

# 活动任务（进程快照确认，绝不可删）
ACTIVE_RUNS = ["2026_10_14-09_37__standing034_survival_quality_v14"]
ACTIVE_SPECS = ["2026_10_14-09_37__standing034_survival_quality_v14"]

# Motion（legacy150D 教师）链：B250 -> pm2 block0000..0004
MOTION_RUNS = [
    "motion_cohort_width_ab_20261006",
    "2026_10_13-00_16__motion_standing034_pm2_block0000",
    "2026_10_13-02_16__motion_standing034_pm2_block0001",
    "2026_10_13-03_58__motion_standing034_pm2_block0002",
    "2026_10_13-05_39__motion_standing034_pm2_block0003",
    "2026_10_13-07_21__motion_standing034_pm2_block0004",
]
MOTION_SPECS = MOTION_RUNS + [
    "2026_10_13-08_29__motion_standing034_symmetry_block0000",
    "2026_10_13-09_07__motion_standing034_symmetry_block0000",
    "2026_10_13-10_22__motion_standing034_symmetry_block0001",
    "2026_10_13-11_19__motion_standing034_alignment_block0000",
    "2026_10_13-15_12__motion034_selected_movement_recheck_ppo0",
    "2026_10_13-13_35__motion_alignment_update_diagnostic_block0000",
]

# 31D 学生 / Recovery 站立共同主干与其两条分支
STUDENT_TRUNK_RUNS = [
    "2026_10_11-17_12__recovery_mcu_v2_standing_rehearsal_from_bc",
    "2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled",
    "2026_10_11-22_43__recovery_standing_motion_mirror_from50",
    "2026_10_12-00_12__recovery_standing_velocity_huber_from200",
    "2026_10_12-09_56__recovery_course_a_prefix0_block0000",
    "2026_10_12-11_42__recovery_course_b_prefix180_block0001",
    "2026_10_12-13_29__recovery_course_b_prefix180_block0002",
]
RECOVERY_V11_RUNS = [
    "2026_10_13-00_20__recovery_standing034_smoke_fix_block0001",
    "2026_10_13-02_19__recovery_standing034_mirror_huber_block0002",
    "2026_10_13-04_09__recovery_standing034_mirror_huber_block0003",
    "2026_10_13-06_00__recovery_standing034_mirror_huber_block0004",
    "2026_10_13-07_50__recovery_standing034_mirror_huber_block0005",
    "2026_10_13-09_00__recovery_standing034_mirror_huber_block0006",
    "2026_10_13-10_39__recovery_standing034_mirror_huber_block0007",
    "2026_10_13-12_15__recovery_standing034_mirror_huber_block0008",
]
STUDENT_V12V13_RUNS = [
    "2026_10_13-17_16__student_standing034_alignment_v12",
    "2026_10_13-22_14__standing034_zero_privileged49_v13",
    "2026_10_14-09_07__v13_u988_survival30_ppo0",
]
STUDENT_EXTRA_RUNS = [
    "2026_10_11-13_35__recovery_mcu_v2_task_ppo_from_bc",
    "2026_10_11-14_32__recovery_mcu_v2_failure_zero_from_bc",
    "2026_10_11-15_25__recovery_mcu_v2_lift_rate_from_bc",
]
# 活动 v14 spec 显式引用的教师 checkpoint 所在 run
TEACHER_RUNS = [
    "2026_10_10-14_23__recovery_swing_controlled_actor_b",
    "motion_cohort_width_ab_20261006",
]

D25_RUNS = ["2026_10_13-17_09__motion_frame25_asymmetric_ppo_closurefix_from_bc"]

PROTECTED_ISOLATED = [
    "recovery_mcu_v2_bc_20261011",
    "recovery_standing_reset_distilled_20261011",
    "recovery_standing_distilled_20261011",
    "student_mcu_v2_teachers_20261011",
    "recovery_standing_teacher_data_20261011",
    "recovery_standing_reset_teacher_data_20261011",
    "motion_frame25_actual034_bc_20261013",
    "motion_frame25_zero_distilled_20261013",
    "motion_frame25_ppo_review_20261013",
    "recovery_standing034_smoke_fix_resume_20261013",
    "recovery_standing034_symmetry_20261012",
    "recovery_continuous_course_20261012",
]

PROTECTED_MANUAL = [
    "manual_train/motion/frame25_actual034_distillation_20261013",
    "manual_train/motion/teacher_deployment_export_20261013",
]

PROTECTED_RUNS = list(dict.fromkeys(
    ACTIVE_RUNS + MOTION_RUNS + STUDENT_TRUNK_RUNS + RECOVERY_V11_RUNS
    + STUDENT_V12V13_RUNS + STUDENT_EXTRA_RUNS + TEACHER_RUNS + D25_RUNS
))
PROTECTED_SPECS = list(dict.fromkeys(ACTIVE_SPECS + MOTION_SPECS + PROTECTED_RUNS))

# 顶层不可作为删除对象
TOPLEVEL_NEVER_DELETE = {".git", "src", "tests", "configs", "docs", "assets", "README.md"}

REF_RE = re.compile(r"(?:runs|isolated|sim2sim|manual_train|artifacts)/([A-Za-z0-9_.\-]+)")


# ---------------------------------------------------------------- 工具


def sha256_file(path: str, limit: int | None = None) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        read = 0
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            if limit is not None and read >= limit:
                break
            h.update(chunk)
            read += len(chunk)
    return h.hexdigest()


def stat_pair(path: str) -> tuple[int, int]:
    st = os.lstat(path)
    apparent = st.st_size
    actual = st.st_blocks * 512
    return apparent, actual


def dir_stats(path: str):
    """返回 (apparent, actual, count, by_category)"""
    apparent = actual = count = 0
    by_cat: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for dp, dn, fn in os.walk(path, followlinks=False):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                a, b = stat_pair(p)
            except OSError:
                continue
            if os.path.islink(p):
                continue
            apparent += a
            actual += b
            count += 1
            c = categorize(p)
            by_cat[c][0] += a
            by_cat[c][1] += b
            by_cat[c][2] += 1
    return apparent, actual, count, {k: {"apparent": v[0], "actual": v[1], "files": v[2]} for k, v in by_cat.items()}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT)


def collect_reference_closure(protected_dirs, protected_files):
    """从保护集合内部（排除 source_snapshot）扫描对其他目录的路径引用。"""
    hits: dict[str, set[str]] = defaultdict(set)
    files = list(protected_files)
    for d in protected_dirs:
        if not os.path.isdir(d):
            continue
        for dp, dn, fn in os.walk(d):
            if "source_snapshot" in dp or "/src" in dp or dp.endswith("/src"):
                continue
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    if os.path.getsize(p) > 20 * 1024 * 1024:
                        continue
                    if os.path.splitext(f)[1] not in (".json", ".md", ".txt", ".log", ".env", ".sh", ".py"):
                        continue
                except OSError:
                    continue
                files.append(p)
    for p in files:
        try:
            text = open(p, "rb").read().decode("utf-8", "ignore")
        except Exception:
            continue
        for m in REF_RE.finditer(text):
            hits[m.group(1)].add(rel(p))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()
    out_dir = os.path.abspath(args.output_dir)
    if os.path.exists(out_dir):
        print(f"refuse: output exists {out_dir}", file=sys.stderr)
        return 2

    ts = datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST")
    os.makedirs(out_dir, exist_ok=True)

    # ---- 1. 顶层统计
    toplevel = {}
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if os.path.islink(p):
            toplevel[name] = {"symlink": True, "target": os.readlink(p)}
            continue
        if os.path.isfile(p):
            a, b = stat_pair(p)
            toplevel[name] = {"type": "file", "apparent": a, "actual": b}
            continue
        a, b, c, cats = dir_stats(p)
        toplevel[name] = {"type": "dir", "apparent": a, "actual": b, "files": c, "by_category": cats}

    # ---- 2. runs / isolated 逐目录
    def scan_child_dirs(parent):
        res = {}
        base = os.path.join(ROOT, parent)
        if not os.path.isdir(base):
            return res
        for name in sorted(os.listdir(base)):
            p = os.path.join(base, name)
            if os.path.islink(p):
                res[name] = {"path": rel(p), "symlink": True, "target": os.readlink(p)}
                continue
            if not os.path.isdir(p):
                a, b = stat_pair(p)
                res[name] = {"path": rel(p), "type": "file", "apparent": a, "actual": b}
                continue
            a, b, c, cats = dir_stats(p)
            res[name] = {"path": rel(p), "type": "dir", "apparent": a, "actual": b,
                         "files": c, "by_category": cats}
        return res

    runs_map = scan_child_dirs("runs")
    isolated_map = scan_child_dirs("isolated")
    artifacts_map = scan_child_dirs("artifacts")
    sim2sim_map = scan_child_dirs("sim2sim")
    manual_map = scan_child_dirs("manual_train")

    # ---- 3. 引用闭包
    prot_dirs = [os.path.join(ROOT, "runs", r) for r in PROTECTED_RUNS]
    prot_dirs += [os.path.join(ROOT, "isolated", i) for i in PROTECTED_ISOLATED]
    prot_dirs += [os.path.join(ROOT, m) for m in PROTECTED_MANUAL]
    prot_dirs += [os.path.join(ROOT, "deployment_protocol")]
    prot_files = []
    for s in PROTECTED_SPECS:
        sp = os.path.join(ROOT, "configs", "experiments", s, "spec.json")
        if os.path.exists(sp):
            prot_files.append(sp)
    hits = collect_reference_closure(prot_dirs, prot_files)

    # ---- 4. 分类
    classification = {}

    def mark(path_key, cls, reason, extra=None):
        e = {"path": path_key, "classification": cls, "reason": reason}
        if extra:
            e.update(extra)
        classification[path_key] = e

    for name, info in runs_map.items():
        key = info["path"]
        if name in ACTIVE_RUNS:
            mark(key, "PROTECTED", "活动任务（进程快照确认：stand_chain/monitor/train 正在运行 source_eval）")
        elif name in TEACHER_RUNS:
            mark(key, "PROTECTED", "活动 v14 spec 与 v12/v13 spec 显式引用的教师 checkpoint 来源")
        elif name in PROTECTED_RUNS:
            mark(key, "PROTECTED", "四类保留模型或其祖先链 run")
        elif name in hits:
            mark(key, "REVIEW_REQUIRED",
                 "被保护集合内部文件引用，需用户确认是否为真实依赖",
                 {"referenced_by": sorted(hits[name])[:8], "reference_count": len(hits[name])})
        else:
            mark(key, "SAFE_CANDIDATE", "不在四类模型祖先链中，且未被保护集合引用")

    for name, info in isolated_map.items():
        key = info["path"]
        if name in PROTECTED_ISOLATED:
            mark(key, "PROTECTED", "四类保留模型 / 祖先 / 蒸馏数据集 / 任务状态")
        elif name in hits:
            mark(key, "REVIEW_REQUIRED", "被保护集合内部文件引用",
                 {"referenced_by": sorted(hits[name])[:8], "reference_count": len(hits[name])})
        else:
            mark(key, "SAFE_CANDIDATE", "与四类保留模型无身份/依赖关系的独立产物")

    for name, info in artifacts_map.items():
        key = info["path"]
        if name in hits:
            mark(key, "REVIEW_REQUIRED", "被保护集合引用", {"referenced_by": sorted(hits[name])[:5]})
        else:
            mark(key, "SAFE_CANDIDATE", "历史工程/CPU 审计产物，不参与模型身份或能力证明")

    for name, info in sim2sim_map.items():
        key = info["path"]
        if "2026_10_13" in name:
            mark(key, "PROTECTED", "当前选定 Motion 教师（05_39/u300）的 MuJoCo 迁移诊断证据")
        else:
            mark(key, "REVIEW_REQUIRED", "旧 B250 sim2sim 诊断，与当前选定教师不同源")

    for name, info in manual_map.items():
        key = info["path"]
        mark(key, "PROTECTED", "当前人工工作台/源码与配置（本轮不作为第一批删除对象）")

    for name, info in toplevel.items():
        key = name
        if name in ("src", "tests", "scripts", "configs", "docs", "assets", ".git"):
            mark(key, "PROTECTED", "当前共享源码/测试/工具/配置/资产/入口文档与 Git 历史，本轮不删")
        elif name == "deployment_protocol":
            mark(key, "PROTECTED", "电控部署协议与已选定 Motion 教师的 ONNX/golden vectors")
        elif name in ("README.md", "AGENTS.md", "STATUS.md", "TOOL_INDEX.md",
                      "ARCHITECTURE.md", "WORKFLOW.md", "plan.md", "PROJECT_MASTER_PLAN.md",
                      "TRAINING_EXPERIENCE_REUSE.md"):
            mark(key, "PROTECTED", "项目入口文档")
        elif name == ".pytest_cache":
            mark(key, "REGENERABLE", "pytest 缓存，可由测试重跑生成")
        elif name == ".codebuddy":
            mark(key, "PROTECTED", "IDE 项目数据，按规则不得删除")
        elif name == ".github":
            mark(key, "PROTECTED", "CI 配置")

    # ---- 5. 大文件分组（已由外部 sha 统计提供则复用）
    big = []
    for parent in ("runs", "isolated", "artifacts", "sim2sim", "manual_train"):
        base = os.path.join(ROOT, parent)
        for dp, dn, fn in os.walk(base):
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    a, b = stat_pair(p)
                except OSError:
                    continue
                if a >= 100 * 1024 * 1024:
                    big.append({"path": rel(p), "apparent": a, "actual": b,
                                "category": categorize(p)})
    big.sort(key=lambda x: -x["actual"])

    # ---- 6. 输出
    total_apparent = sum(v.get("apparent", 0) for v in toplevel.values() if isinstance(v.get("apparent"), int))
    total_actual = sum(v.get("actual", 0) for v in toplevel.values() if isinstance(v.get("actual"), int))
    total_files = sum(v.get("files", 0) for v in toplevel.values() if isinstance(v.get("files"), int))

    def sum_cat(mapping):
        agg = defaultdict(lambda: [0, 0, 0])
        for name, info in mapping.items():
            for c, v in (info.get("by_category") or {}).items():
                agg[c][0] += v["apparent"]
                agg[c][1] += v["actual"]
                agg[c][2] += v["files"]
        return {k: {"apparent": v[0], "actual": v[1], "files": v[2]} for k, v in sorted(agg.items())}

    by_class_bytes = defaultdict(int)
    by_class_files = defaultdict(int)
    for key, e in classification.items():
        info = None
        if "/" in key:
            parent, name = key.split("/", 1)
            mapping = {"runs": runs_map, "isolated": isolated_map, "artifacts": artifacts_map,
                       "sim2sim": sim2sim_map, "manual_train": manual_map}.get(parent)
            if mapping and name in mapping:
                info = mapping[name]
        else:
            info = toplevel.get(key)
        if not info:
            continue
        by_class_bytes[e["classification"]] += info.get("actual", 0)
        by_class_files[e["classification"]] += info.get("files", 0)

    payload = {
        "audit_version": "1.0",
        "generated_at": ts,
        "root": ROOT,
        "mode": "READ_ONLY_INVESTIGATION",
        "disk": {
            "project_apparent_bytes": total_apparent,
            "project_actual_bytes": total_actual,
            "project_file_count": total_files,
        },
        "toplevel": toplevel,
        "runs": runs_map,
        "isolated": isolated_map,
        "artifacts": artifacts_map,
        "sim2sim": sim2sim_map,
        "manual_train": manual_map,
        "classification": classification,
        "classification_totals": {
            k: {"actual_bytes": v, "files": by_class_files[k]} for k, v in sorted(by_class_bytes.items())
        },
        "category_totals": {
            "runs": sum_cat(runs_map), "isolated": sum_cat(isolated_map),
            "artifacts": sum_cat(artifacts_map), "sim2sim": sum_cat(sim2sim_map),
            "manual_train": sum_cat(manual_map),
        },
        "big_files_over_100MiB": big,
        "reference_closure_from_protected": {k: sorted(v)[:10] for k, v in sorted(hits.items())},
    }
    with open(os.path.join(out_dir, "inventory.json"), "w") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    print(f"wrote {out_dir}/inventory.json")
    print(json.dumps(payload["classification_totals"], ensure_ascii=False, indent=1))
    print(f"project actual = {total_actual/1073741824:.2f} GiB, apparent = {total_apparent/1073741824:.2f} GiB, files={total_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
