#!/usr/bin/env python3
"""生成修订版（rev2）审计清单：保守保护 + 可审核方案 A + 待裁定方案 B（不可执行）。

只读历史；只写新审计目录。方案 A 的执行由 scripts/prune_execute.py 在用户批准后完成。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

ROOT = "/home/kellen/wheel_leg_native_train"
SHA_TZ = timezone(timedelta(hours=8))
ORIG_AUDIT = "artifacts/2026_10_14-09_57__storage_prune_audit"
PREV_REVISION = "artifacts/2026_10_14-10_30__storage_prune_audit_rev2"
EXECUTOR_REL = "scripts/prune_execute.py"
SCHEMA_PLAN = "prune_plan_v1"
SCHEMA_ENTRIES = "prune_entries_v1"
SCHEMA_KEEP = "prune_keep_v1"

# 顶层永久保护（本轮不作为第一批删除对象）
TOPLEVEL_PROTECTED = [
    ".git", ".github", ".codebuddy", "src", "tests", "scripts", "configs", "docs",
    "assets", "deployment_protocol", "README.md", "AGENTS.md", "STATUS.md",
    "TOOL_INDEX.md", "TOOL_INDEX_HISTORY.md", "ARCHITECTURE.md", "WORKFLOW.md",
    "plan.md", "PROJECT_MASTER_PLAN.md", "TRAINING_EXPERIENCE_REUSE.md",
    "pyproject.toml", "requirements-cpu.txt", ".gitignore",
    "参考文献.md", "参考文献2.md", "开源文档.md",
]

# 方案 A 明确排除（即使原审计列为 SAFE）
A_EXCLUDE_PREFIXES = [
    ORIG_AUDIT,                                   # 原审计目录（原计划曾错误列入候选）
    "artifacts/2026_10_14-10_30__storage_prune_audit_rev2",   # rev2 审计目录（历史审计只读）
    "artifacts/prune_execution_receipts",         # 执行回执目录
    ".pytest_cache",                              # 易变缓存，避免身份抖动造成误拒
]

# 不消费 SHA 的大体量派生报告（体积过大，不纳入身份重验；其引用的原始证据已另行保护）
REFERENCE_DOC_MAX_BYTES = 5 * 1024 * 1024
EVIDENCE_FILE_MAX_BYTES = 20 * 1024 * 1024


def collect_evidence(protected_paths):
    """收集身份绑定的必要证据文件 + 需要检查引用的文档。

    - evidence_identity：声明完整 SHA256 的必要文件（模型/ONNX/祖先/规格/身份记录）
    - reference_documents：可解析的 JSON 引用文档（spec、manifest、startup handshake 等）
    """
    ev, docs, seen = [], [], set()

    def add(rel, reason, ref=False):
        full = os.path.join(ROOT, rel)
        if rel in seen or not os.path.isfile(full):
            return
        size = os.path.getsize(full)
        if size > EVIDENCE_FILE_MAX_BYTES:
            return
        seen.add(rel)
        digest = sha256_file(full)
        ev.append({"path": rel, "sha256": digest, "reason": reason})
        if ref and size <= REFERENCE_DOC_MAX_BYTES and rel.endswith(".json"):
            docs.append({"path": rel, "sha256": digest})

    for o in PROTECTED_ONNX:
        add(o["path"], "protected_onnx（部署模型身份）")
    for a in ANCESTOR_MINIMAL:
        p = a["path"].rstrip("/")
        if os.path.isfile(os.path.join(ROOT, p)):
            add(p, "ancestor_minimal_package（祖先 checkpoint）")
        else:
            for name in ("manifest.json", "chain_terminal_report.json",
                         "startup_handshake.json", "candidate_selection.json",
                         "dataset_manifest.json", "best_validation.json"):
                add(f"{p}/{name}", "ancestor_minimal_package（身份/终态记录）", ref=True)
    for item in protected_paths:
        p = item["path"].rstrip("/")
        if p.startswith("configs/experiments/"):
            add(f"{p}/spec.json", "受保护 spec（来源与配方身份）", ref=True)
        elif p.startswith("runs/") or p.startswith("isolated/"):
            for name in ("manifest.json", "chain_terminal_report.json",
                         "startup_handshake.json", "candidate_selection.json",
                         "dataset_manifest.json"):
                add(f"{p}/{name}", "受保护 run 的身份/终态/选择记录", ref=True)
    for name in ("manifest.json", "golden_vectors.json", "hardware_map.json",
                 "deployment_manifest.json"):
        add(f"deployment_protocol/motion_legacy150d_v1/{name}", "部署包身份与 golden vectors", ref=True)
    return ev, docs


def load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sha256_json(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--skip-hash", action="store_true", help="仅结构调试，不重算候选身份")
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, args.out_dir)
    if os.path.exists(out_dir):
        print("refuse: output exists")
        return 2
    os.makedirs(out_dir)
    ts = datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST")

    ex = load_module(os.path.join(ROOT, EXECUTOR_REL), "prune_execute")

    inv = json.load(open(os.path.join(ROOT, ORIG_AUDIT, "inventory.json")))
    cls = inv["classification"]

    # ---------------- 原审计目录引用与现场 SHA
    orig_files = {}
    for name in sorted(os.listdir(os.path.join(ROOT, ORIG_AUDIT))):
        p = os.path.join(ROOT, ORIG_AUDIT, name)
        if os.path.isfile(p):
            orig_files[name] = sha256_file(p)

    # ---------------- 保护集合（保守）
    protected_paths = []
    seen = set()

    def add_protected(rel, reason):
        rel = rel.rstrip("/")
        if rel in seen:
            return
        seen.add(rel)
        protected_paths.append({"path": rel, "reason": reason})

    for name in TOPLEVEL_PROTECTED:
        add_protected(name, "当前源码/测试/工具/配置/文档/资产/入口文档与 Git 历史")

    for path, e in cls.items():
        if e["classification"] == "PROTECTED":
            add_protected(path, e["reason"])

    add_protected(ORIG_AUDIT, "原审计目录（本轮引用的上游证据）")
    add_protected("artifacts/2026_10_14-10_30__storage_prune_audit_rev2", "rev2 修订审计目录（历史审计只读）")
    add_protected(args.out_dir, "本轮修订审计目录（自身保护）")
    add_protected("artifacts/prune_execution_receipts", "删除执行回执目录（执行器专属）")
    add_protected("scripts/prune_execute.py", "删除执行器本体（计划绑定其 SHA）")

    review_paths = sorted(p for p, e in cls.items() if e["classification"] == "REVIEW_REQUIRED")
    for p in review_paths:
        add_protected(p, f"REVIEW_REQUIRED（默认保护）: {cls[p]['reason']}")

    # ---------------- 身份绑定的必要证据（模型/ONNX/祖先/规格/终态与选择记录）
    evidence_identity, reference_documents = collect_evidence(protected_paths)

    # ---------------- 保护清单（先于候选筛选构建，使生成期与执行期共用同一套判定）
    keep_doc = {
        "schema": SCHEMA_KEEP,
        "keep_version": "2",
        "root": ROOT,
        "generated_at": ts,
        "protected_paths": protected_paths,
        "protected_checkpoints": PROTECTED_CHECKPOINTS,
        "protected_onnx": PROTECTED_ONNX,
        "ancestor_minimal_package": ANCESTOR_MINIMAL,
        "required_evidence": REQUIRED_EVIDENCE,
        "evidence_identity": evidence_identity,
        "reference_documents": reference_documents,
        "evidence_note": ("evidence_identity 为声明完整 SHA256 的必要身份文件，执行器逐条重验；"
                          "reference_documents 为可解析 JSON，其引用不得越出项目根、不得指向删除候选。"
                          f"大于 {EVIDENCE_FILE_MAX_BYTES // (1024 * 1024)} MiB 的派生报告不纳入身份重验。"),
        "never_delete": sorted(set(TOPLEVEL_PROTECTED + [
            ORIG_AUDIT, "artifacts/2026_10_14-10_30__storage_prune_audit_rev2",
            args.out_dir, "artifacts/prune_execution_receipts",
            "scripts/prune_execute.py"])),
        "active_task_dependencies": ACTIVE_DEPS,
        "active_task_snapshot": ACTIVE_SNAPSHOT,
        "active_task_exclusion": ACTIVE_TASK,
        "unresolved_identities": UNRESOLVED,
        "note": "执行器消费以上全部字段；任一字段缺失或 SHA 不一致即拒绝执行。",
    }
    pm_doc = {
        "schema": "prune_protected_models_v1",
        "root": ROOT,
        "generated_at": ts,
        "identity_rule": "以实际 checkpoint SHA、spec 的 source_checkpoint/source_sha256、run terminal 与原始评估为准",
        "categories": PROTECTED_MODELS,
        "active_task": ACTIVE_TASK,
        "unresolved": UNRESOLVED,
        "sha_verification": SHA_VERIFICATION,
    }

    # ---------------- 方案 A 候选
    a_candidates = []
    for path, e in cls.items():
        if e["classification"] != "SAFE_CANDIDATE":
            continue
        if any(path == p or path.startswith(p + "/") for p in A_EXCLUDE_PREFIXES):
            continue
        if path.split("/")[0] not in ("runs", "isolated", "artifacts"):
            continue
        a_candidates.append(path)
    a_candidates.sort()

    # 静态保护检查：与执行器 build_protected 完全同一套判定
    prot_parts, _prot_sources = ex.build_protected(keep_doc, pm_doc, review_paths)
    seen_entries = []
    a_ok, a_rejected = [], []
    for rel in a_candidates:
        try:
            parts = ex.check_entry_allowed(ROOT, rel, prot_parts, seen_entries)
            seen_entries.append({"rel": rel, "parts": parts})
            a_ok.append(rel)
        except ex.Refused as exc:
            a_rejected.append({"path": rel, "reason": str(exc)})

    # ---------------- 逐条身份清单
    entries = []
    total_actual = total_apparent = 0
    total_files = 0
    for i, rel in enumerate(a_ok, start=1):
        if args.skip_hash:
            info = inv["runs"].get(rel.split("/", 1)[1]) or inv["isolated"].get(rel.split("/", 1)[1]) or {}
            ident = {"kind": "dir", "manifest_sha256": "SKIPPED", "entries": [],
                     "actual_bytes": info.get("actual", 0), "file_count": info.get("files", 0)}
        else:
            ident = ex.build_manifest(ROOT, rel)
        total_actual += ident.get("actual_bytes") or 0
        total_files += ident.get("file_count") or 0
        entries.append({
            "id": f"A{i:04d}",
            "path": rel,
            "type": ident["kind"],
            "classification": "SAFE_CANDIDATE",
            "actual_bytes": ident.get("actual_bytes"),
            "file_count": ident.get("file_count"),
            "dependency_check": ("不在四类保留模型/未决候选的祖先链；未被保护集合引用；"
                                 "不含受保护 spec 引用的 checkpoint SHA；不与其它候选重叠"),
            "identity": ident,
        })

    # 保护路径中**文件**的祖先链说明（用于报告，不影响判定）
    ancestor_files = set()
    for p, e in cls.items():
        if e["classification"] == "PROTECTED":
            base = os.path.join(ROOT, p)
            if os.path.isfile(base):
                ancestor_files.add(p)

    # hardlink 与父子重叠核算（避免重复计算）
    # 回收量在**全部过滤之后**统一重算（见下方 recompute_reclaim），此处仅占位
    hl = {"file_blocks": 0, "dir_blocks": 0, "total_actual_bytes": 0, "hardlink_groups": 0,
          "hardlink_shared_bytes": 0, "hardlink_outside_bytes": 0, "net_reclaim_bytes": 0}
    ov = []
    net_actual = 0

    # ---------------- 待裁定 B（不可执行）
    review_entries = []
    b_pending_bytes = 0
    for p in review_paths:
        base = os.path.join(ROOT, p)
        if not os.path.isdir(base):
            continue
        size = sum(os.lstat(os.path.join(dp, f)).st_blocks * 512
                   for dp, _, fn in os.walk(base) for f in fn
                   if not os.path.islink(os.path.join(dp, f)))
        b_pending_bytes += size
        entry = {
            "path": p,
            "actual_bytes": size,
            "review_reason": cls[p]["reason"],
            "unresolved": "被保护集合内部文件引用或含被引用 checkpoint；整目录删除会破坏引用完整性",
            "action": "仅允许生成“最小保留包”逐文件清单，未经用户逐项裁定不得删除；不计入可立即回收量",
            "referenced_by": cls[p].get("referenced_by"),
        }
        review_entries.append(entry)

    # B25 目录专项：逐文件残差清单
    b25 = "runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50"
    b25_files = []
    if os.path.isdir(os.path.join(ROOT, b25)):
        keep_sub = "B/formal/model_update_25.pt"
        for dp, _, fn in os.walk(os.path.join(ROOT, b25)):
            for f in fn:
                fp = os.path.join(dp, f)
                r = os.path.relpath(fp, ROOT)
                st = os.lstat(fp)
                b25_files.append({
                    "path": r,
                    "actual_bytes": st.st_blocks * 512,
                    "protected": r.endswith(keep_sub),
                    "category": ex and _cat(r),
                })
        b25_files.sort(key=lambda x: -x["actual_bytes"])
    b25_residual_bytes = sum(x["actual_bytes"] for x in b25_files if not x["protected"])
    for e in review_entries:
        if e["path"] == b25:
            e["b25_detail"] = {
                "protected_file": "B/formal/model_update_25.pt（SHA 8c3f74f9…，被受保护 spec 引用）",
                "file_count": len(b25_files),
                "protected_count": sum(1 for x in b25_files if x["protected"]),
                "residual_bytes_if_minimal_package_kept": b25_residual_bytes,
                "residual_files": [x for x in b25_files if not x["protected"]][:800],
                "note": "整目录删除被明确禁止；本节仅列出若生成最小保留包后剩余的逐文件 REVIEW 候选，未经裁定不计入回收量。",
            }

    # ---------------- 本轮实时活动任务快照：命中候选的条目一律剔出 A（只减不加）
    LIVE_SNAPSHOT.update({"checked_at": datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST")})
    try:
        live = ex.scan_active_processes(ROOT)
        LIVE_SNAPSHOT.update({"process_count": live.get("count"),
                              "unresolved_cwd": live.get("unresolved_cwd"),
                              "unresolved_spec": live.get("unresolved_spec"),
                              "unresolved_cmdline": live.get("unresolved_cmdline"),
                              "tasks": [{"pid": p["pid"], "cwd": p["cwd"],
                                         "specs": p["specs"], "ref_count": len(p["refs"])}
                                        for p in live["processes"] if p["kind"] == "task"]})
        conflicting = ex.conflicting_entries(live, [e["path"] for e in entries], ROOT)
        # 实时快照解析出的真实依赖同样并入保护集合
        live_refs = sorted({r for p in live["processes"] for r in (p.get("refs") or [])})
        LIVE_SNAPSHOT["referenced_paths"] = live_refs
        for r in live_refs:
            if r and r != "src":
                ACTIVE_DEPS.append({"path": r,
                                    "reason": "实时进程快照：活动任务 argv/spec 实际引用的路径"})
    except Exception as exc:  # noqa: BLE001
        conflicting = {}
        LIVE_SNAPSHOT.update({"error": repr(exc)})
        CORRECTIONS.append({"id": "C13-LIVE-ACTIVITY",
                            "original": "生成期未检查活动任务实际依赖与候选的交集",
                            "finding": f"实时进程快照失败: {exc!r}",
                            "action": "fail closed：本计划不生成可执行范围，需人工复核"})
    if conflicting:
        for p in sorted(conflicting):
            a_rejected.append({"path": p,
                               "reason": "活动任务冲突（本轮实时快照）: "
                                         + "; ".join(conflicting[p][:3])})
            CORRECTIONS.append({"id": f"C13-{p}",
                                "original": "rev2 方案 A 将该路径列为可删除候选",
                                "finding": "; ".join(conflicting[p][:3]),
                                "action": "从本修订 A 中剔除（只减不加）；其所在目录已整体移出候选"})
        drop = set(conflicting)
        entries = [e for e in entries if e["path"] not in drop]
        total_actual = sum(e["actual_bytes"] for e in entries)
        total_files = sum(e.get("file_count") or 0 for e in entries)
    LIVE_SNAPSHOT["conflicting_candidates"] = {k: v for k, v in sorted(conflicting.items())}

    # ---------------- 保护证据引用检查：受保护文档引用到的候选一律剔出 A（只减不加）
    root_real = os.path.realpath(ROOT)
    ref_conflicts: dict = {}
    cand_parts = [(e["path"], ex.parse_parts(e["path"])) for e in entries]
    for doc in reference_documents:
        full = os.path.join(ROOT, doc["path"])
        try:
            refs = ex.collect_doc_refs(full, root_real)
        except Exception as exc:  # noqa: BLE001
            CORRECTIONS.append({"id": f"C14-DOC-{doc['path']}",
                                "original": "引用文档未被解析",
                                "finding": repr(exc),
                                "action": "该文档不参与引用检查（已在 keep_manifest 中保留身份）"})
            continue
        for ref in refs:
            if not ref or ref[0] in ex.HARD_FORBIDDEN_TOP:
                continue
            for rel, c in cand_parts:
                if ex.overlaps(ref, c):
                    ref_conflicts.setdefault(rel, set()).add(
                        f"{doc['path']} 引用 {'/'.join(ref)}")
    if ref_conflicts:
        for p in sorted(ref_conflicts):
            a_rejected.append({"path": p,
                               "reason": "被受保护证据文档引用（不得忽略）: "
                                         + "; ".join(sorted(ref_conflicts[p])[:2])})
            CORRECTIONS.append({"id": f"C14-{p}",
                                "original": "rev2 方案 A 将该路径列为可删除候选",
                                "finding": "; ".join(sorted(ref_conflicts[p])[:2]),
                                "action": "从本修订 A 中剔除（只减不加）"})
        drop_ref = set(ref_conflicts)
        entries = [e for e in entries if e["path"] not in drop_ref]
        total_actual = sum(e["actual_bytes"] for e in entries)
        total_files = sum(e.get("file_count") or 0 for e in entries)

    # ---------------- 与 rev2 的范围差异（只允许减少，不允许新增）
    try:
        prev_entries = json.load(open(os.path.join(ROOT, PREV_REVISION, "deletion_entries_A.json")))
        prev_a = {e["path"] for e in prev_entries["entries"]}
    except Exception as exc:  # noqa: BLE001
        prev_a = set()
        CORRECTIONS.append({"id": "SCOPE-READ", "original": "读取 rev2 候选清单失败",
                            "finding": repr(exc), "action": "无法对比范围，需人工核对"})
    cur_a = {e["path"] for e in entries}
    scope_changes = {
        "compared_with": PREV_REVISION,
        "prev_entry_count": len(prev_a),
        "cur_entry_count": len(cur_a),
        "added": sorted(cur_a - prev_a),
        "dropped": sorted(prev_a - cur_a),
        "carry_forward_protection": CARRY_FORWARD,
        "rule": "本修订只允许缩小候选范围；任何新增候选都必须人工复核后才能批准",
    }
    if scope_changes["added"]:
        for p in scope_changes["added"]:
            a_rejected.append({"path": p, "reason": "本轮新出现的候选，未经人工复核不纳入 A"})
        entries = [e for e in entries if e["path"] not in set(scope_changes["added"])]
        total_actual = sum(e["actual_bytes"] for e in entries)
        total_files = sum(e.get("file_count") or 0 for e in entries)
        hl = ex.hardlink_shared_bytes(ROOT, [e["path"] for e in entries])
        net_actual = hl["net_reclaim_bytes"]
        cur_a = {e["path"] for e in entries}
        scope_changes["enforced"] = "新增候选已剔除出 A（见 rejected_from_A）"

    # ---------------- 最终重算（过滤后唯一权威口径）
    total_actual = sum(e["actual_bytes"] for e in entries)
    total_files = sum(e.get("file_count") or 0 for e in entries)
    if args.skip_hash:
        hl = {"file_blocks": total_actual, "dir_blocks": 0, "total_actual_bytes": total_actual,
              "hardlink_groups": 0, "hardlink_shared_bytes": 0, "hardlink_outside_bytes": 0,
              "net_reclaim_bytes": total_actual, "note": "skip-hash 调试模式，未核算 hardlink"}
        ov = []
    else:
        hl = ex.hardlink_shared_bytes(ROOT, [e["path"] for e in entries])
        ov = ex.overlap_report(entries)
    net_actual = hl["net_reclaim_bytes"]
    scope_changes["cur_entry_count"] = len(entries)

    # ---------------- 输出
    def write(name, obj, indent=1):
        p = os.path.join(out_dir, name)
        with open(p, "w") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=indent)
        return sha256_file(p), len(json.dumps(obj, ensure_ascii=False))

    entries_doc = {
        "schema": SCHEMA_ENTRIES,
        "entries_version": "1",
        "root": ROOT,
        "generated_at": ts,
        "status": "DRY_RUN_ONLY",
        "entry_count": len(entries),
        "estimated_reclaim_actual_bytes": total_actual,
        "hardlink": hl,
        "estimated_reclaim_net_bytes": net_actual,
        "overlap_pairs": ov,
        "total_files": total_files,
        "excluded_from_A": A_EXCLUDE_PREFIXES,
        "rejected_from_A": a_rejected,
        "live_activity_snapshot": LIVE_SNAPSHOT,
        "entries": entries,
    }
    entries_sha, _ = write("deletion_entries_A.json", entries_doc)

    review_doc = {
        "schema": "prune_review_entries_v1",
        "root": ROOT,
        "generated_at": ts,
        "status": "REVIEW_ONLY_NOT_EXECUTABLE",
        "note": "方案 B 仅为建议，不允许直接执行；本清单不进入主计划的删除条目集合。",
        "entry_count": len(review_entries),
        "pending_actual_bytes": b_pending_bytes,
        "entries": review_entries,
    }
    review_sha, _ = write("review_entries_B.json", review_doc)

    keep_sha, _ = write("keep_manifest.json", keep_doc)
    pm_sha, _ = write("protected_models.json", pm_doc)

    executor_sha = sha256_file(os.path.join(ROOT, EXECUTOR_REL))
    plan_entries_sha = entries_sha
    plan = {
        "schema": SCHEMA_PLAN,
        "plan_version": "1",
        "root": ROOT,
        "generated_at": ts,
        "plan_scope": "A",
        "source_audit": {
            "dir": ORIG_AUDIT,
            "files": orig_files,
            "note": "上游审计现场 SHA（本轮现场重算，不引用旧报告中的值）",
        },
        "executor": {"path": EXECUTOR_REL, "version": ex.EXECUTOR_VERSION, "sha256": executor_sha},
        "inputs": {
            "keep_manifest": {"path": f"{args.out_dir}/keep_manifest.json", "sha256": keep_sha},
            "protected_models": {"path": f"{args.out_dir}/protected_models.json", "sha256": pm_sha},
            "entries": {"path": f"{args.out_dir}/deletion_entries_A.json", "sha256": entries_sha},
            "review_entries": {"path": f"{args.out_dir}/review_entries_B.json", "sha256": review_sha},
        },
        "active_task_snapshot": ACTIVE_SNAPSHOT,
        "live_activity_snapshot": LIVE_SNAPSHOT,
        "carry_forward_protection": CARRY_FORWARD,
        "scope_changes_vs_rev2": scope_changes,
        "previous_revision": PREV_REVISION,
        "previous_revision_plan_sha256": (
            "dcce196fdac04d88a9790f810130e95f0c659df10518e720c0253ba2935403ad"),
        "entry_count": len(entries),
        "estimated_reclaim_actual_bytes": total_actual,
        "estimated_reclaim_net_bytes": net_actual,
        "hardlink": hl,
        "overlap_pairs": ov,
        "estimated_reclaim_note": ("按实际磁盘块（st_blocks×512）累加；扣除批次内 hardlink 重复副本；"
                                   "再扣除“批次外仍持有链接、删除后不释放”的数据块（hardlink_outside_bytes）；"
                                   "候选之间父子重叠已校验"),
        "estimation_error_note": ("未计入 inode/块对齐、目录项历史碎片与文件系统预留；"
                                  "文件块(st_blocks)与目录块分别列出，便于核对"),
        "retained_scope": [
            "四类推荐模型及其全部未决候选的完整 checkpoint 与运行状态",
            "祖先最小保留包（含受保护 spec 中所有 source_checkpoint / teacher checkpoint / ONNX 来源）",
            "活动任务（v14）的 spec、run 及被引用教师与来源 checkpoint",
            "当前 src/tests/scripts/configs/docs/assets/deployment_protocol/.git 与入口文档",
            "全部 REVIEW_REQUIRED 与 UNKNOWN 对象（默认保护）",
            "原审计目录、本轮修订审计目录与执行回执目录",
        ],
        "lost_capabilities": [
            "被删 run 内的逐环境原始评估 JSON 与压缩轨迹 NPZ（无关实验的重放能力）",
            "被删 run 内的中间 checkpoint 与 optimizer 状态",
            "被删 run 的 TensorBoard events 与 metrics.jsonl 训练曲线",
            "被删 run 的 source_snapshot 源码快照（其历史执行树不可逐字节重建）",
            "依赖上述 run 作为输入的离线工具入口（audit_terminal / correct_evidence / review_recovery_events / compare_motion 等）",
        ],
        "approval_status": "UNAUTHORIZED",
        "execution_status": "NOT_EXECUTED",
        "approval_object": (f"方案A，plan SHA=<见 PLAN_SHA.txt 中 deletion_plan_A.json 的 SHA256>，"
                            f"批准此清单中的 {len(entries)} 个条目"),
        "note": "计划文件不等于用户授权；执行必须由后续明确用户指令批准本 plan 及其完整 SHA。",
    }
    plan_sha, _ = write("deletion_plan_A.json", plan)

    corrections = {
        "schema": "prune_corrections_v2",
        "generated_at": ts,
        "original_audit": ORIG_AUDIT,
        "original_file_sha256": orig_files,
        "previous_revision": "artifacts/2026_10_14-10_30__storage_prune_audit_rev2",
        "previous_revision_plan_sha256": (
            "dcce196fdac04d88a9790f810130e95f0c659df10518e720c0253ba2935403ad"),
        "executor": {"path": EXECUTOR_REL, "version": ex.EXECUTOR_VERSION,
                     "note": "执行器已升级为 v2（dry-run 完整核验 / spec 依赖解析 / 全局锁与 INTENT / 保护证据完整重验）；旧计划不得沿用"},
        "items": CORRECTIONS,
    }
    write("corrections_vs_rev2.json", corrections)

    print(json.dumps({
        "out_dir": args.out_dir,
        "A_entries": len(entries),
        "A_rejected": len(a_rejected),
        "A_reclaim_GiB": round(net_actual / 2**30, 2),
        "hardlink_groups": hl["hardlink_groups"],
        "hardlink_shared_GiB": round(hl["hardlink_shared_bytes"] / 2**30, 4),
        "hardlink_outside_GiB": round(hl["hardlink_outside_bytes"] / 2**30, 4),
        "file_blocks_GiB": round(hl["file_blocks"] / 2**30, 3),
        "dir_blocks_GiB": round(hl["dir_blocks"] / 2**30, 3),
        "live_conflicting_candidates": len(LIVE_SNAPSHOT.get("conflicting_candidates", {})),
        "evidence_identity_files": len(evidence_identity),
        "reference_documents": len(reference_documents),
        "overlap_pairs": len(ov),
        "A_files": total_files,
        "B_review_entries": len(review_entries),
        "B_pending_GiB": round(b_pending_bytes / 2**30, 2),
        "b25_residual_GiB": round(b25_residual_bytes / 2**30, 2),
        "protected_paths": len(protected_paths),
        "executor_sha256": executor_sha,
        "entries_sha256": entries_sha,
        "keep_sha256": keep_sha,
        "protected_models_sha256": pm_sha,
        "review_sha256": review_sha,
        "plan_sha256": plan_sha,
    }, ensure_ascii=False, indent=1))
    return 0


def _cat(rel: str) -> str:
    f = os.path.basename(rel)
    if f.endswith(".pt"):
        return "checkpoint"
    if f.endswith(".npz"):
        return "trace_npz"
    if f.endswith(".json"):
        return "json"
    if f.endswith(".jsonl"):
        return "metrics"
    if f.endswith(".log"):
        return "log"
    if f.endswith(".pyc") or "__pycache__" in rel:
        return "cache"
    if "/src/" in rel or "source_snapshot" in rel:
        return "source_copy"
    return "other"


# ------------------------------------------------------------------ 静态声明

PROTECTED_CHECKPOINTS = []   # 由 build() 前的数据填充（见下）
PROTECTED_ONNX = []
ANCESTOR_MINIMAL = []
REQUIRED_EVIDENCE = []
ACTIVE_DEPS = []
ACTIVE_SNAPSHOT = {}
LIVE_SNAPSHOT = {}
CARRY_FORWARD = []
ACTIVE_TASK = {}
UNRESOLVED = []
PROTECTED_MODELS = {}
SHA_VERIFICATION = {}
CORRECTIONS = []


def _init_static():
    global PROTECTED_CHECKPOINTS, PROTECTED_ONNX, ANCESTOR_MINIMAL, REQUIRED_EVIDENCE
    global ACTIVE_DEPS, ACTIVE_TASK, UNRESOLVED, PROTECTED_MODELS, SHA_VERIFICATION, CORRECTIONS
    global CARRY_FORWARD
    data = json.load(open(os.path.join(ROOT, "artifacts/2026_10_14-09_57__storage_prune_audit/protected_models.json")))
    PROTECTED_MODELS = data["categories"]
    ACTIVE_TASK = data["active_task"]

    verified = []
    for cat, v in PROTECTED_MODELS.items():
        for c in v["candidates"] + v["ancestors"]:
            p = c.get("path")
            if not p:
                continue
            full = os.path.join(ROOT, p)
            exists = os.path.exists(full)
            actual = sha256_file(full) if exists and os.path.isfile(full) else None
            match = (actual == c.get("sha256")) if (actual and c.get("sha256")) else None
            verified.append({"category": cat, "id": c.get("id"), "path": p, "exists": exists,
                             "recorded_sha256": c.get("sha256"), "actual_sha256": actual,
                             "match": match})
    SHA_VERIFICATION = {"checked_at": None, "items": verified}

    PROTECTED_CHECKPOINTS = [
        {"path": v["path"], "sha256": v["actual_sha256"] or v["recorded_sha256"],
         "reason": f'{v["category"]} / {v.get("id") or "ancestor"}',
         "match": v["match"]}
        for v in verified if v["exists"] and v["actual_sha256"]
    ]
    PROTECTED_ONNX = []
    for _rel in [
        "deployment_protocol/motion_legacy150d_v1/actor.onnx",
        "isolated/motion_frame25_actual034_bc_20261013/actor.onnx",
        "isolated/motion_frame25_zero_distilled_20261013/actor.onnx",
        "isolated/recovery_mcu_v2_deploy_20261011/actor.onnx",
        "isolated/motion_zero_mcu_v2_deploy_20261011/actor.onnx",
    ]:
        _full = os.path.join(ROOT, _rel)
        _exists = os.path.isfile(_full)   # 不跟随 symlink 到项目外
        PROTECTED_ONNX.append({
            "path": _rel,
            "exists": _exists,
            "sha256": sha256_file(_full) if _exists else None,
            "reason": "部署/推理 ONNX 及其来源模型身份",
        })
    ANCESTOR_MINIMAL = [
        {"path": "runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt",
         "reason": "B250：Motion 祖先 + v12/v13/活动 v14 教师 checkpoint"},
        {"path": "runs/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25",
         "reason": "B50 教师的直接父 run（整目录保留，本轮不裁剪）"},
        {"path": "isolated/recovery_swing_leg_initialization_qualified_20261010",
         "reason": "B50 初始化候选 initialization_candidate.pt"},
        {"path": "runs/recovery_pose_capture_20261002_145814",
         "reason": "姿态库（受保护课程/评估的运行时依赖）"},
        {"path": "isolated/recovery_mcu_v2_bc_20261011",
         "reason": "31D 两条链的共同 BC 根模型与 dataset"},
        {"path": "isolated/student_mcu_v2_teachers_20261011",
         "reason": "mcu_v2 BC 蒸馏数据集"},
        {"path": "isolated/recovery_standing_reset_distilled_20261011",
         "reason": "站立 reset-priority BC 学生"},
    ]
    REQUIRED_EVIDENCE = [
        {"path": "artifacts/2026_10_14-09_57__storage_prune_audit",
         "reason": "上游只读审计证据（inventory/protected_models/keep_manifest/deletion_plan）"},
        {"path": "configs/experiments", "reason": "全部冻结 spec（requested/effective 声明与来源身份）"},
        {"path": "deployment_protocol/motion_legacy150d_v1", "reason": "部署包：ONNX、manifest、golden vectors、硬件映射模板"},
    ]
    ACTIVE_DEPS = [
        {"path": "runs/2026_10_14-09_37__standing034_survival_quality_v14", "reason": "活动 run（source_eval）"},
        {"path": "runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt",
         "reason": "活动 v14 的 source_checkpoint（SHA 2af573b3…72cd）"},
        {"path": "runs/2026_10_10-14_23__recovery_swing_controlled_actor_b", "reason": "活动 spec 引用的 B50 教师"},
        {"path": "runs/motion_cohort_width_ab_20261006", "reason": "活动 spec 引用的 B250 教师"},
    ]
    # 只读进程快照：把活动任务实际引用的路径并入保护集合（生成期一次性）
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("pe_probe", os.path.join(ROOT, EXECUTOR_REL))
        _pe = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_pe)
        snap = _pe.scan_active_processes(ROOT)
        refs = set()
        for _p in snap.get("processes", []):
            if _p.get("cwd_parts"):
                refs.add("/".join(_p["cwd_parts"]))
            for _t in _p.get("path_tokens", []):
                refs.add(_t)
        ACTIVE_SNAPSHOT.update({
            "checked_at": datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST"),
            "process_count": snap.get("count"),
            "unresolved_cwd": snap.get("unresolved_cwd"),
            "referenced_paths": sorted(refs),
        })
        for r in sorted(refs):
            if r:
                ACTIVE_DEPS.append({"path": r,
                                    "reason": "只读进程快照：活动任务 argv/cwd 实际引用的路径"})
    except Exception as exc:  # noqa: BLE001
        ACTIVE_SNAPSHOT.update({"error": repr(exc)})

    # 单调保留：rev2 活动快照引用过的路径，不因本轮瞬时快照不再出现而解除保护
    try:
        prev_keep = json.load(open(os.path.join(ROOT, PREV_REVISION, "keep_manifest.json")))
        prev_refs = (prev_keep.get("active_task_snapshot") or {}).get("referenced_paths", [])
        prev_deps = [d["path"] for d in prev_keep.get("active_task_dependencies", [])]
        for r in sorted(set(prev_refs) | set(prev_deps)):
            if r and r != "src":
                ACTIVE_DEPS.append({"path": r,
                                    "reason": "rev2 活动任务依赖（单调保留）：瞬时快照消失不缩小保护"})
                CARRY_FORWARD.append(r)
    except Exception as exc:  # noqa: BLE001
        CARRY_FORWARD.append(f"ERROR: {exc!r}")
    UNRESOLVED = [
        {"id": "U1", "topic": "Recovery 与 31D 学生是否同类",
         "detail": "R1(10_39/u300) 与 S1(v13/u988) 同根于 00_12 v7 u300 (2a587c31…a9a)；两者均已保护，无需删除侧决策",
         "missing": "用户对“当前 Recovery 模型”的定义"},
        {"id": "U2", "topic": "31D 是否同时保留 v12 终态",
         "detail": "S1b(f1b3481b…) 与 S1c(73a7a09e…) 均已保护", "missing": "用户对 v12 终态的保留意愿"},
        {"id": "U3", "topic": "25D 更早 zero-only 版本 D1b",
         "detail": "路径存在且已保护；本轮需完整核验其 SHA（见 sha_verification）", "missing": "用户是否保留 D1b"},
        {"id": "U4", "topic": "Motion 最强运动候选 M1b",
         "detail": "df60f53c… 已保护", "missing": "用户是否与 M1 同时保留"},
    ]
    CORRECTIONS = [
        {"id": "C1", "original": "prune_dryrun.py 声称 --execute 但无删除实现",
         "finding": "确认：原脚本 run() 在 --execute 后仅打印 'EXECUTE 需要用户逐条批准' 并 return 6",
         "action": "新执行器 scripts/prune_execute.py 实现真实删除、回执、中断恢复"},
        {"id": "C2", "original": "load_keep_paths 只消费 checkpoint/ONNX/never_delete/写死活动 run",
         "finding": "确认：原脚本未读取 protected_paths、ancestor 最小包、REVIEW 对象",
         "action": "build_protected() 强制消费 protected_paths / protected_checkpoints / protected_onnx / ancestor_minimal_package / required_evidence / never_delete / active_task_dependencies / review_entries"},
        {"id": "C3", "original": "只绑定主 plan SHA",
         "finding": "确认：原脚本未绑定 keep_manifest、B 清单与执行器 SHA",
         "action": "主计划绑定 keep_manifest / protected_models / entries / review_entries / executor 五份 path+SHA，任一不符即拒绝"},
        {"id": "C4", "original": "无逐项 SHA 与目录内容变化核验",
         "finding": "确认：原脚本只判 exists()",
         "action": "文件级 size+SHA256；目录级完整子路径清单+类型+大小+SHA/symlink 文本，规范化 manifest 摘要 SHA 比对"},
        {"id": "C5", "original": "缺少统一绝对路径/越界/symlink/父子重叠校验",
         "finding": "确认：原脚本仅做字符串前缀与 FORBIDDEN 比较",
         "action": "normalize_parts/resolve_entry/within/overlaps 统一接口；按路径组件判定；拒绝绝对路径、..、通配符、symlink 父目录、项目根"},
        {"id": "C6", "original": "B 清单仍含内有受保护 B25 的 9.01GiB 目录作为整目录删除项",
         "finding": "确认：原 plan_B_minimal_archive.entries_dirs 含 runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50",
         "action": "移出任何整目录删除项；改为 review_entries_B.json 中的 b25_detail 逐文件残差清单（保护 B/formal/model_update_25.pt）"},
        {"id": "C7", "original": "A “保留原始评估”表述有歧义",
         "finding": "确认：A 实际会删除无关实验的全部原始评估 JSON/NPZ",
         "action": "改述为“仅保留受保护模型的必要证据”；并在 plan.lost_capabilities 明确列出失去的原始评估与轨迹"},
        {"id": "C8", "original": "不确定项统称 REVIEW",
         "finding": "确认：原报告 UNKNOWN=0 但未说明每个 REVIEW 缺什么",
         "action": "review_entries_B.json 每条记录 review_reason / unresolved / action；unresolved 单独列出 U1–U4 缺失信息"},
        {"id": "C9", "original": "原 A 清单把审计目录自身列为删除候选",
         "finding": "新发现：原 plan_A entries 含 artifacts/2026_10_14-09_57__storage_prune_audit（生成时该目录已存在，被误判为 SAFE_CANDIDATE），构成自删",
         "action": "A_EXCLUDE_PREFIXES 排除原审计目录、回执目录与易变 .pytest_cache；执行器额外硬保护 .git/src/tests/scripts/configs/docs/assets/deployment_protocol 顶层"},
        {"id": "C10", "original": "dry-run 不写回执，但执行器无回执概念",
         "finding": "确认：原脚本无 execution_id/回执/幂等/中断语义",
         "action": "新增 execution_id、独立回执目录、DELETED/ALREADY_DELETED_BY_THIS_EXECUTION/MISSING_UNEXPLAINED 状态与 --resume"},
    ]
    for v in verified:
        if v["exists"] and v["actual_sha256"] and v["match"] is False:
            CORRECTIONS.append({
                "id": f"C11-{v['category']}-{v.get('id')}",
                "original": "protected_models.json 记录的 SHA256 与实际不符",
                "finding": f"{v['path']} 记录值 {v['recorded_sha256']} ≠ 实际 {v['actual_sha256']}",
                "action": "以实际 SHA 为准写入本轮 keep_manifest.protected_checkpoints；原审计该字段不可用于执行前身份重验",
            })
        elif v["exists"] and v["actual_sha256"] and v["match"] is None:
            CORRECTIONS.append({
                "id": f"C12-{v['category']}-{v.get('id')}",
                "original": "protected_models.json 该条目 SHA256 为 null（未记录）",
                "finding": f"{v['path']} 实际 SHA {v['actual_sha256']}",
                "action": "本轮补全为实际 SHA",
            })

    SHA_VERIFICATION["checked_at"] = datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST")


_init_static()

if __name__ == "__main__":
    raise SystemExit(main())
