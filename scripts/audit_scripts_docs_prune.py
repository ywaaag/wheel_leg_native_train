#!/usr/bin/env python3
"""脚本/文档精简审计（只读调查 + 精确删除清单；本脚本不删除任何文件）。

设计原则：
1. 所有结论都现场重算（SHA256、入向引用、入口注册），不照抄人工判断。
2. 候选只有"零入向引用 + 已核验无当前用途"才进入 deletion_plan；
   任何被引用或被注册的条目自动降级为 UNKNOWN/保护（fail closed）。
3. deletion_plan 只含文件级精确相对路径，禁止通配符、目录、runs/isolated/资产。
4. approval_status 恒为 UNAUTHORIZED：计划文件不等于用户授权。

用法：
    python scripts/audit_scripts_docs_prune.py --out-dir <新审计目录>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CST = timezone(timedelta(hours=8))
SCHEMA = "scripts_docs_prune_plan_v1"

# 只读扫描语料：排除大体量实验数据（本轮范围不含它们）
CORPUS_SKIP_DIRS = ("runs", "isolated", "artifacts", "sim2sim", "manual_train",
                    ".git", "__pycache__", ".pytest_cache", "node_modules")
CORPUS_EXT = (".py", ".md", ".json", ".toml", ".sh", ".cfg", ".txt", ".yaml", ".yml")

# 绝不进入删除候选的前缀（保护 + 本轮范围外）
NEVER_CANDIDATE = ("runs/", "isolated/", "artifacts/", ".git/", "sim2sim/",
                   "manual_train/", "src/", "tests/", "configs/",
                   "deployment_protocol/", "assets/")

# ---------------------------------------------------------------- 人工判定（附证据要求）

# 第一轮已按批准删除（回执：deletion_receipt.json）；不再作为候选重复列出
DELETED_ROUND1 = ("scripts/audit_motion_capability_recipe.py", "scripts/build_prune_rev2.py",
                  "scripts/prepare_motion_forward_cohort.py",
                  "scripts/prepare_motion_forward_diagnostic.py",
                  "scripts/run_checkpoint_sweep.py",
                  "scripts/summarize_motion_forward_cohort.py")
DELETED_ROUND1_DOCS = ("docs/EXPERIMENT_PLAN.md",)

# 删除候选：必须零入向引用且无当前用途；构建期会逐条重验，不满足即自动剔除
SCRIPT_CANDIDATES = {
    "scripts/build_prune_rev2.py": (
        "DELETE_CANDIDATE",
        "被 build_prune_rev3.py 取代；rev2 审计产物已按只读证据保留，无需再生成",
        "scripts/build_prune_rev3.py（同族最新；rev2/rev3 产物本身不在删除范围）"),
    "scripts/audit_motion_capability_recipe.py": (
        "DELETE_CANDIDATE",
        "一次性 Gaussian 核比较脚本；零入向引用，能力审计已有注册入口 audit_motion_response.py",
        "scripts/audit_motion_response.py"),
    "scripts/run_checkpoint_sweep.py": (
        "DELETE_CANDIDATE",
        "硬编码 runs/recovery_checkpoint_sweep_20261003/20261004 历史目录；零入向引用，不服务当前模型或祖先",
        None),
    "scripts/prepare_motion_forward_cohort.py": (
        "DELETE_CANDIDATE",
        "冻结单变量 forward cohort 一次性声明器；零入向引用，历史 cohort 已结束",
        None),
    "scripts/prepare_motion_forward_diagnostic.py": (
        "DELETE_CANDIDATE",
        "硬编码 runs/motion_retention_ab_20261006 与 isolated/root_cause_audit_20261006；零入向引用",
        None),
    "scripts/summarize_motion_forward_cohort.py": (
        "DELETE_CANDIDATE",
        "仅为上述 forward cohort 服务的汇总器；零入向引用",
        None),
    "scripts/prepare_motion_capability_course.py": (
        "DELETE_CANDIDATE",
        "capability-first motion 课程声明器，已被注册入口 prepare_motion_experiment 覆盖；"
        "第一轮其唯一引用者 audit_motion_capability_recipe.py 已删除，故本轮零代码引用",
        "src/native_stand/command_v6/tools/prepare_motion_experiment.py"),
}

# 需先迁移调用再删（本轮只登记，不进入 deletion_plan）
SCRIPT_MIGRATE_FIRST = {
    "scripts/run_motion_high_speed_preparation.py": (
        "MIGRATE_THEN_DELETE",
        "entrypoints.py 登记为 RETIRED 且运行即自拒；但删除前必须先从 ENTRIES 元组移除该条目",
        "移除 ENTRIES 中 RETIRED 条目"),
    "scripts/watch_recovery_submission.py": (
        "MIGRATE_THEN_DELETE",
        "entrypoints.py 登记为 RETIRED 且直接 parser.error；被 test_student_engineering_boundary 用于校验守卫语义",
        "先把守卫语义迁移到 ENTRIES 断言，再删除脚本与注册条目"),
}

# 证据不足 → 默认保护
SCRIPT_UNKNOWN = {
    "scripts/capture_motion_reference.py": "docstring 表明需 Isaac rollout 采集 SHA 绑定参考；零入向引用但无法排除人工外部调用",
    "scripts/review_student_recovery_dynamics.py": "CPU-only 离线探针，docstring 完整；未在 docs/tests/configs 命中，可能被未索引的历史命令使用",
}

DOC_CANDIDATES = {
    "docs/MULTI_SKILL_ROADMAP.md": (
        "DELETE_OBSOLETE",
        "第二轮：独有正文（接口版本/第一阶段交付/后续次序）已迁入 PROJECT_MASTER_PLAN，"
        "文件已收敛为纯指针，零代码引用",
        "PROJECT_MASTER_PLAN.md「多技能路线图细节」"),
    "docs/EXPERIMENT_PLAN.md": (
        "DELETE_OBSOLETE",
        "2026-10-01 站立条件计划，零入向链接；其条件已由 PROJECT_MASTER_PLAN 目标段与 STATUS 当前正文覆盖，且引用旧 budget.json",
        "PROJECT_MASTER_PLAN.md（目标）、STATUS.md（当前状态）"),
}

DOC_MIGRATED_THEN_DELETE = {}  # 路线图独有正文已于第二轮迁入 PROJECT_MASTER_PLAN

DOC_UNKNOWN = {
    "参考文献.md": "零入向链接的前期资料摘录；是否仍有独立证据价值未确认",
    "参考文献2.md": "零入向链接的 3 行摘录；归属与价值未确认",
    "docs/CHANGED_FILES.md": "零入向链接但疑似变更台账证据",
    "docs/REUSE_DECISIONS.md": "零入向链接但疑似复用来源台账证据",
    "docs/COLLEAGUE_ALIGNMENT.md": "零入向链接的流程对齐说明，未证明可并入他文",
}

DOC_AUTHORITY = (
    "AGENTS.md", "README.md", "STATUS.md", "TOOL_INDEX.md", "WORKFLOW.md",
    "ARCHITECTURE.md", "PROJECT_MASTER_PLAN.md", "TRAINING_EXPERIENCE_REUSE.md",
    "TOOL_INDEX_HISTORY.md", "scripts/README.md", "docs/README.md",
    "docs/PUBLIC_RELEASE.md", "docs/RECOVERY_STANDING_PLAN.md",
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Refused(Exception):
    """拒绝：输出冲突、绑定不符、原始计划缺失。调用方应据此报错而不是继续。"""


# 只属于“已批准计划 / 批准回执 / 执行回执 / 完整性记录”的文件名。
# 本工具绝不生成、绝不覆盖它们；批准计划由批准流程归档并视为不可变。
PROTECTED_OUTPUT_NAMES = frozenset({
    "deletion_plan.json", "approval.json", "deletion_receipt.json",
    "post_delete_verification.json", "plan_integrity_note.json",
    "cleaned_evidence_annotations.json", "integrity_review.json",
})


def guarded_write(out_dir: str, name: str, payload: bytes) -> dict:
    """写入审计产物。

    - 受保护文件名 → 直接拒绝；
    - 目标已存在且字节完全相同 → 幂等（UNCHANGED），不算覆盖；
    - 目标已存在但内容不同 → 明确拒绝，绝不静默更新。
    """
    if os.path.basename(name) in PROTECTED_OUTPUT_NAMES:
        raise Refused(f"拒绝写入受保护产物名（只属于已批准计划/回执）: {name}")
    path = os.path.join(out_dir, name)
    digest = sha256_bytes(payload)
    if os.path.exists(path):
        if sha256_file(path) == digest:
            return {"path": path, "sha256": digest, "action": "UNCHANGED"}
        raise Refused(f"输出路径冲突，拒绝覆盖已有文件: {name}")
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as fh:
        fh.write(payload)
    os.replace(tmp, path)
    return {"path": path, "sha256": digest, "action": "CREATED"}


def publish_plan(out_dir: str, plan_doc: dict) -> dict:
    """发布“待批准候选计划”：内容寻址命名 + 保留完整原始字节。

    只保存 SHA 不足以在原始文件丢失后恢复计划，因此这里保存完整字节；
    文件名携带内容哈希，因此重复生成是幂等的，永不覆盖其它内容。
    """
    payload = json.dumps(plan_doc, ensure_ascii=False, indent=1).encode("utf-8")
    digest = sha256_bytes(payload)
    name = f"deletion_plan_candidates_{digest[:12]}.json"
    result = guarded_write(out_dir, name, payload)
    result.update({"plan_sha256": digest, "plan_bytes": len(payload),
                   "approval_status": plan_doc.get("approval_status"),
                   "execution_status": plan_doc.get("execution_status"),
                   "note": ("候选清单按内容寻址命名并保留完整字节；已批准计划文件名 deletion_plan.json "
                            "只由批准流程归档，本工具不再生成或覆盖")})
    return result


def _executor_sha256_file():
    """复用已绑定执行器 scripts/prune_execute.py 的 SHA 实现，避免第二套实现。"""
    import importlib.util
    path = os.path.join(ROOT, "scripts", "prune_execute.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("_prune_execute_for_sha", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "sha256_file", None)


def verify_plan(plan_path: str, expected_sha256: str) -> dict:
    """执行准备前的绑定核验：字节必须与批准的 SHA 完全一致。

    原始计划缺失时明确拒绝，不伪造“恢复成功”。
    """
    if not os.path.isfile(plan_path):
        raise Refused(f"原始计划缺失，无法核验：{plan_path}（不伪造成功恢复）")
    with open(plan_path, "rb") as fh:
        raw = fh.read()
    actual = sha256_bytes(raw)
    if actual != expected_sha256:
        raise Refused(f"计划 SHA 不符，拒绝进入执行准备：期望 {expected_sha256}，实际 {actual}")
    shared = _executor_sha256_file()
    if shared is not None and shared(plan_path) != actual:
        raise Refused("与执行器 SHA 实现结果不一致，拒绝进入执行准备")
    return {"path": plan_path, "sha256": actual, "bytes": len(raw), "verified": True,
            "sha_impl": "scripts/prune_execute.py:sha256_file" if shared else "内置实现"}


def load_corpus(root: str = None):
    """把只读语料读进内存，用于一次扫描多次匹配。"""
    root = root or ROOT
    corpus = {}
    for base, dirs, files in os.walk(root):
        rel_base = os.path.relpath(base, root)
        if rel_base == ".":
            rel_base = ""
        parts = rel_base.split(os.sep) if rel_base else []
        if any(p in CORPUS_SKIP_DIRS for p in parts):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in CORPUS_SKIP_DIRS]
        for name in files:
            if not name.endswith(CORPUS_EXT):
                continue
            rel = os.path.join(rel_base, name) if rel_base else name
            if rel in ("artifacts",) or rel.startswith("artifacts/"):
                continue
            try:
                with open(os.path.join(base, name), encoding="utf-8", errors="ignore") as fh:
                    corpus[rel] = fh.read()
            except OSError:
                continue
    return corpus



# 第二轮候选的证据化注解：引用核查 / 替代入口 / 历史用途 / 删除损失
ENTRY_NOTES = {
    "scripts/prepare_motion_capability_course.py": {
        "purpose": "为已完成实验 motion_capability_course_20261006 生成 capability-first spec 与独立 ledger（一次性配方脚本）",
        "current_refs": "零代码引用（唯一引用者 scripts/audit_motion_capability_recipe.py 已在第一轮删除）；entrypoints.py 未注册",
        "replacement": "src/native_stand/command_v6/tools/prepare_motion_experiment.py（已在 ENTRIES 注册的通用准备器）",
        "dependencies_intact": "其输入 configs/experiments/motion_forward_cohort_20261006/spec.json 与 runs/motion_forward_cohort_20261006/formal/model_update_25.pt 仍存在，脚本仍可运行",
        "historical_use": "2026-10-06 capability course 声明的原始生成器；产物 configs/experiments/motion_capability_course_20261006 已存在",
        "deletion_loss": "失去「逐字节重生成该历史 spec/ledger」的能力；不能再用它发布新的 UNAUTHORIZED 声明（须改用注册的通用准备器）",
        "verification": "现场重算 SHA + 零代码引用 + 未注册 + 非保护前缀 + 依赖存在性已核验",
    },
    "docs/MULTI_SKILL_ROADMAP.md": {
        "purpose": "多技能路线图历史导航文件（独有正文已迁入 PROJECT_MASTER_PLAN）",
        "current_refs": "ARCHITECTURE.md 的导航引用已在本轮迁往 PROJECT_MASTER_PLAN「多技能路线图细节」；其余提及均为历史报告列表",
        "replacement": "PROJECT_MASTER_PLAN.md「多技能路线图细节（自 docs/MULTI_SKILL_ROADMAP.md 迁入，2026-10-14）」",
        "migration_fidelity": "迁移前快照的 15 行非指针正文已逐行断言全部存在于 PROJECT_MASTER_PLAN",
        "historical_use": "旧路线与 1182D 接口记录的历史导航；原文另存 docs/history/ENTRY_DOCS_BEFORE_CONSOLIDATION_20261008.md 与 git 历史",
        "deletion_loss": "失去该文件路径本身（导航价值已由权威正文与历史归档覆盖）",
        "verification": "零代码引用 + 迁移保真逐行断言 + 入向导航已迁移，删除后不留死链",
    },
}

# 只报告“谁可能删除谁”的审计工具：它们提到候选名只是审计台账，不构成调用依赖
AUDIT_TOOLING = ("scripts/audit_scripts_docs_prune.py",)


def inbound_refs(corpus: dict, rel: str) -> dict:
    """返回 {"code": [...], "doc": [...]}：引用该文件的 (文件, 行号)。

    code = .py/.sh/.json/.toml/.cfg 等可执行或注册载体；doc = .md 文档提及。
    两者证据强度不同：删除候选要求 code 引用为 0，文档提及逐条登记后判断。
    """
    base = os.path.basename(rel)
    stem = base.rsplit(".", 1)[0]
    out = {"code": [], "doc": []}
    for other, text in corpus.items():
        if other == rel or other in AUDIT_TOOLING:
            continue
        if base not in text and stem not in text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if base in line or (len(stem) > 6 and stem in line):
                out["doc" if other.endswith(".md") else "code"].append(f"{other}:{i}")
                break
    return out


def parse_entrypoints(root: str = None) -> dict:
    """解析 entrypoints.py 的 ENTRIES：脚本相对路径 -> status。

    支持两种登记形式：dict（含显式 status）与星号展开的 (entry, role) 元组（默认 CURRENT）。
    """
    p = os.path.join(root or ROOT, "src/native_stand/command_v6/tools/entrypoints.py")
    reg = {}
    if not os.path.isfile(p):
        return reg
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    for m in re.finditer(r"['\"]entry['\"]\s*:\s*['\"]([^'\"]+)['\"]", text):
        entry = m.group(1)
        window = text[m.end():m.end() + 240]
        st = re.search(r"['\"]status['\"]\s*:\s*['\"]([A-Z_]+)['\"]", window)
        reg[entry] = st.group(1) if st else "CURRENT"
    gen = re.search(r"\*\(\s*\{[^}]*\}\s*for\s+entry\s*,\s*role\s+in\s*\((.*?)\)\s*\)", text, re.S)
    if gen:
        for m in re.finditer(r"\(\s*'([^']+)'\s*,\s*'", gen.group(1)):
            reg.setdefault(m.group(1), "CURRENT")
    return {k: v for k, v in reg.items() if k.startswith("scripts/")}


def build(out_dir: str, root: str = None, publish_as: str = None) -> dict:
    root = root or ROOT
    ts = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")
    corpus = load_corpus(root)
    reg = parse_entrypoints(root)
    try:
        audit_prefix = os.path.relpath(out_dir, root) + "/"
    except ValueError:
        audit_prefix = ""

    # ---------------- 脚本清单
    scripts = sorted(r for r in corpus
                     if r.startswith("scripts/") and r.endswith(".py"))
    script_inventory = {"schema": "script_inventory_v1", "generated_at": ts,
                        "corpus_files": len(corpus), "entrypoint_registered": len(reg),
                        "scripts": []}
    for rel in scripts:
        refs = inbound_refs(corpus, rel)
        full = os.path.join(ROOT, rel)
        if rel in DELETED_ROUND1 or not os.path.isfile(full):
            script_inventory["scripts"].append({
                "path": rel, "sha256": None, "size": None, "classification": "DELETED",
                "reason": "第一轮已按批准删除（见 deletion_receipt.json）", "replacement": None,
                "entrypoint_status": None, "code_ref_count": 0, "doc_ref_count": 0,
                "code_refs_sample": [], "doc_refs_sample": []})
            continue
        if rel in SCRIPT_CANDIDATES:
            cls, reason, repl = SCRIPT_CANDIDATES[rel]
        elif rel in SCRIPT_MIGRATE_FIRST:
            cls, reason, repl = SCRIPT_MIGRATE_FIRST[rel]
        elif rel in SCRIPT_UNKNOWN:
            cls, reason, repl = "UNKNOWN", SCRIPT_UNKNOWN[rel], None
        elif rel in reg:
            cls, reason, repl = "KEEP_CURRENT", f"entrypoints.py 登记为 {reg[rel]}", None
        elif refs["code"] or refs["doc"]:
            cls, reason, repl = ("KEEP_CURRENT",
                                 f"存在入向引用（code={len(refs['code'])}, doc={len(refs['doc'])}）", None)
        else:
            cls, reason, repl = "UNKNOWN", "零入向引用但未证明无当前用途，默认保护", None
        script_inventory["scripts"].append({
            "path": rel, "sha256": sha256_file(full) if os.path.isfile(full) else None,
            "size": os.path.getsize(full) if os.path.isfile(full) else None,
            "classification": cls, "reason": reason, "replacement": repl,
            "entrypoint_status": reg.get(rel),
            "code_ref_count": len(refs["code"]), "doc_ref_count": len(refs["doc"]),
            "code_refs_sample": refs["code"][:5], "doc_refs_sample": refs["doc"][:5],
        })

    # ---------------- 文档清单
    docs = sorted(r for r in corpus
                  if r.endswith(".md") and (os.sep not in r or r.startswith("docs/")))
    document_inventory = {"schema": "document_inventory_v1", "generated_at": ts,
                          "documents": []}
    for rel in docs:
        text = corpus[rel]
        refs = inbound_refs(corpus, rel)
        full = os.path.join(root, rel)
        if rel in DELETED_ROUND1_DOCS or not os.path.isfile(full):
            document_inventory["documents"].append({
                "path": rel, "sha256": None, "lines": 0, "classification": "DELETED",
                "reason": "第一轮已按批准删除（见 deletion_receipt.json）", "authority_for": None,
                "code_ref_count": 0, "doc_ref_count": 0, "code_refs_sample": [],
                "doc_refs_sample": [], "claims_current_status": False})
            continue
        if rel in DOC_CANDIDATES:
            cls, reason, repl = DOC_CANDIDATES[rel]
        elif rel in DOC_MIGRATED_THEN_DELETE:
            cls, reason, repl = DOC_MIGRATED_THEN_DELETE[rel]
        elif rel in DOC_UNKNOWN:
            cls, reason, repl = "UNKNOWN", DOC_UNKNOWN[rel], None
        elif rel in DOC_AUTHORITY:
            cls, reason, repl = "KEEP_AUTHORITY", "权威正文（职责见 report.md）", None
        elif rel.startswith("docs/history/"):
            cls, reason, repl = "KEEP_EVIDENCE", "历史导航/正文归档证据，禁止删除", None
        elif rel.startswith("docs/") and re.search(r"20\d{6}", rel):
            cls, reason, repl = "KEEP_EVIDENCE", "按日期追溯的实验/工程证据", None
        else:
            cls, reason, repl = "UNKNOWN", "归属未确认，默认保护", None
        claims_status = bool(re.search(r"当前状态|当前是|下一步|未授权|待授权", text))
        document_inventory["documents"].append({
            "path": rel, "sha256": sha256_file(full) if os.path.isfile(full) else None,
            "lines": len(text.splitlines()), "classification": cls, "reason": reason,
            "authority_for": repl,
            "code_ref_count": len(refs["code"]), "doc_ref_count": len(refs["doc"]),
            "code_refs_sample": refs["code"][:5], "doc_refs_sample": refs["doc"][:5],
            "claims_current_status": claims_status,
        })

    # ---------------- 删除计划（只接受零引用、非保护、非注册的精确文件）
    entries, rejected = [], []
    for item in script_inventory["scripts"] + document_inventory["documents"]:
        rel = item["path"]
        cls = item["classification"]
        if cls not in ("DELETE_CANDIDATE", "DELETE_OBSOLETE"):
            continue
        problems = []
        if rel.startswith(NEVER_CANDIDATE) or rel.startswith(audit_prefix):
            problems.append("命中保护前缀")
        if item["code_ref_count"] != 0:
            problems.append(f"存在 {item['code_ref_count']} 处代码引用 {item['code_refs_sample'][:2]}")
        if item.get("entrypoint_status"):
            problems.append(f"entrypoints.py 登记为 {item['entrypoint_status']}")
        if not os.path.isfile(os.path.join(root, rel)):
            problems.append("文件不存在")
        if problems:
            rejected.append({"path": rel, "reason": "; ".join(problems),
                             "action": "降级为 UNKNOWN，本轮不进入删除清单"})
            item["classification"] = "UNKNOWN"
            item["reason"] = item["reason"] + "（自动降级：" + "; ".join(problems) + "）"
            continue
        entries.append({
            "path": rel, "type": "file",
            "size": item.get("size") or os.path.getsize(os.path.join(root, rel)),
            "sha256": item["sha256"], "classification": cls,
            "reason": item["reason"], "replacement": item.get("replacement") or item.get("authority_for"),
            "notes": ENTRY_NOTES.get(rel, {}),
            "code_ref_count": 0, "doc_ref_count": item["doc_ref_count"],
            "doc_mentions": item["doc_refs_sample"],
            "doc_mention_note": ("文档提及均为历史台账/归档列举，不构成调用依赖；"
                                 "如批准删除，需同步在对应台账追加一条“已退役”记录"
                                 if item["doc_ref_count"] else "无文档提及"),
            "entrypoint_registered": False,
            "verification": "构建期重算 SHA + 零代码引用 + 未注册 + 非保护前缀",
            "requires": "用户明确批准本清单及完整 SHA256 后才可删除",
        })
    entries.sort(key=lambda e: e["path"])

    deletion_plan = {
        "schema": SCHEMA, "plan_version": "1",
        "root": root, "generated_at": ts,
        "scope": "scripts_and_docs_only",
        "approval_status": "UNAUTHORIZED",
        "execution_status": "NOT_EXECUTED",
        "note": ("本计划只准备删除，不执行删除；计划文件不等于用户授权。"
                 "候选均为文件级精确相对路径，不含通配符、目录或 runs/isolated/资产。"),
        "entry_count": len(entries),
        "total_bytes": sum(e["size"] for e in entries),
        "inputs": {
            "script_inventory": "script_inventory.json",
            "document_inventory": "document_inventory.json",
            "migration_map": "migration_map.json",
            "protected_paths": "protected_paths.json",
            "validation_results": "validation_results.json",
        },
        "excluded_by_rule": ["runs/", "isolated/", "artifacts/", ".git/", "src/",
                             "tests/", "configs/", "deployment_protocol/", "sim2sim/",
                             "manual_train/", "assets/", audit_prefix],
        "rejected_during_build": rejected,
        "entries": entries,
        "approval_object": ("方案「脚本与文档精简」：批准 deletion_plan.json 中的 %d 个文件条目"
                            "（SHA256 见清单），执行前须重新核验入向引用与 SHA。" % len(entries)),
    }

    # ---------------- 保护范围
    protected = {
        "schema": "scripts_docs_protected_paths_v1", "generated_at": ts, "root": root,
        "authority_docs": list(DOC_AUTHORITY),
        "reading_chain": ["AGENTS.md", "STATUS.md", "WORKFLOW.md", "TOOL_INDEX.md",
                          "ARCHITECTURE.md", "README.md"],
        "protected_globs_or_dirs": [
            "AGENTS.md", "README.md", "STATUS.md", "TOOL_INDEX.md", "WORKFLOW.md",
            "ARCHITECTURE.md", "PROJECT_MASTER_PLAN.md", "TRAINING_EXPERIENCE_REUSE.md",
            "docs/**", "src/**", "tests/**", "configs/**", "scripts/**（除批准删除项）",
            "deployment_protocol/**", "assets/**", ".git/**",
            "artifacts/2026_10_14-09_57__storage_prune_audit/**",
            "artifacts/2026_10_14-10_30__storage_prune_audit_rev2/**",
            "artifacts/2026_10_14-11_05__storage_prune_audit_rev3/**",
            "artifacts/prune_execution_receipts/**", audit_prefix + "**",
            "runs/**", "isolated/**（本轮不调查的工具与数据）",
        ],
        "protected_reasons": {
            "AGENTS.md": "Codex 授权与不可变边界（唯一正文）",
            "STATUS.md": "当前任务状态、授权与未决事项（唯一正文）",
            "TOOL_INDEX.md": "工具命令、参数与副作用（唯一正文）",
            "WORKFLOW.md": "固定执行流程（唯一正文）",
            "ARCHITECTURE.md": "模块职责、调用链与数据契约（唯一正文）",
            "README.md": "项目介绍与最短阅读链入口",
            "PROJECT_MASTER_PLAN.md": "长期目标与路线图正文",
            "TRAINING_EXPERIENCE_REUSE.md": "可复用训练经验与证据边界",
            "docs/**": "按日期追溯的实验/工程证据与历史归档",
            "src/**": "当前模型加载/训练/评估/导出/部署实现",
            "tests/**": "CPU 契约与回归",
            "deployment_protocol/**": "部署输入/动作协议与 golden vectors",
            "artifacts/**（审计与回执）": "审计、批准、执行回执与保护清单",
        },
        "unknown_default": "protect",
    }

    # ---------------- 迁移映射
    migration = {
        "schema": "scripts_docs_migration_map_v1", "generated_at": ts,
        "doc_text_moves": [
            {"from": "TOOL_INDEX.md 第 3–13 行（时间性通知条目）",
             "to": "STATUS.md「工具手册迁出的通知条目（原文迁移，2026-10-14）」",
             "method": "脚本逐字搬迁，未改写正文；TOOL_INDEX 头部改为稳定前言 + 状态权威指针",
             "verification": "搬迁前后原文快照见 pre_edit_snapshots/"},
            {"from": "plan.md「## 实施状态（2026-10-14）」表的状态语义",
             "to": "STATUS.md（当前状态唯一正文）",
             "method": "在表前插入状态归属指针，不搬迁正文",
             "verification": "plan.md 只保留设计实施快照与验证入口"},
            {"from": "docs/MULTI_SKILL_ROADMAP.md 目标段与「当前状态」表",
             "to": "PROJECT_MASTER_PLAN.md（路线图正文）+ STATUS.md（状态）",
             "method": "文件头加收敛指针；正文暂留，列入待删候选",
             "verification": "指针已在文件头，正文可由权威文档覆盖"},
        ],
        "script_entry_moves": [],
        "still_required_before_delete": [
            "docs/MULTI_SKILL_ROADMAP.md：确认 PROJECT_MASTER_PLAN 覆盖其独有内容后批准",
            "scripts/run_motion_high_speed_preparation.py：先从 ENTRIES 移除 RETIRED 条目",
            "scripts/watch_recovery_submission.py：先把守卫语义迁移到注册表断言",
        ],
    }

    # ---------------- 输出
    os.makedirs(out_dir, exist_ok=True)

    snapshot_dir = os.path.join(out_dir, "snapshots", datetime.now(CST).strftime("%Y%m%d_%H%M%S"))
    os.makedirs(snapshot_dir, exist_ok=True)

    def write(name, obj):
        """可再生的清单/验证输出：写入本次运行的独立快照目录，永不覆盖历史快照。"""
        payload = json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8")
        path = os.path.join(snapshot_dir, name)
        tmp = f"{path}.tmp"
        with open(tmp, "wb") as fh:
            fh.write(payload)
        os.replace(tmp, path)
        return {"path": path, "sha256": sha256_bytes(payload), "action": "SNAPSHOT"}

    def write_stable(name, obj):
        """需要稳定文件名的待审清单：内容变化即拒绝覆盖，不静默更新。"""
        return guarded_write(out_dir, name,
                             json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8"))

    write("script_inventory.json", script_inventory)
    write("document_inventory.json", document_inventory)
    write("migration_map.json", migration)
    write("protected_paths.json", protected)
    write("validation_results.json", {
        "schema": "scripts_docs_prune_validation_v1", "generated_at": ts,
        "plan_only_zero_write": True,
        "deletions_performed": 0,
        "note": "本脚本只读调查，不删除、不移动、不改写任何被审对象；不启动仿真/PPO/Isaac。",
    })
    # 审计器只产出“候选清单”，按内容寻址命名并保留完整原始字节。
    # 已批准计划（deletion_plan.json）、批准回执与执行回执均由批准/执行流程归档，本工具绝不生成或覆盖。
    while True:
        try:
            pub = publish_plan(out_dir, deletion_plan)
            break
        except Refused as exc:
            print(f"发布候选清单被拒绝: {exc}", file=sys.stderr)
            return exc
    print(f"candidate plan: {os.path.basename(pub['path'])}  sha256={pub['plan_sha256']}  "
          f"action={pub['action']}（候选清单，未执行）")
    if publish_as:
        try:
            stable = guarded_write(out_dir, publish_as,
                                   json.dumps(deletion_plan, ensure_ascii=False, indent=1).encode("utf-8"))
            print(f"stable name  : {publish_as}  action={stable['action']}")
        except Refused as exc:
            print(f"稳定文件名发布被拒绝（已存在且内容不同）: {exc}", file=sys.stderr)

    print("corpus files :", len(corpus))
    print("scripts      :", len(scripts), " (registered:", len(reg), ")")
    print("docs         :", len(docs))
    print("delete entries:", len(entries), " rejected:", len(rejected))
    for e in entries:
        print("   DEL", e["path"], e["size"])
    for r in rejected:
        print("   REJ", r["path"], "|", r["reason"])
    return deletion_plan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", help="审计产物目录（只生成候选清单；不写批准/回执）")
    ap.add_argument("--publish-as", help="把候选清单同时发布为该稳定文件名（已存在且内容不同则拒绝）")
    ap.add_argument("--verify-plan", help="执行准备前核验：计划文件路径")
    ap.add_argument("--plan-sha256", help="与 --verify-plan 配对：批准计划声明的完整 SHA256")
    args = ap.parse_args()
    if args.verify_plan:
        if not args.plan_sha256:
            print("--verify-plan 必须同时给出 --plan-sha256", file=sys.stderr)
            return 2
        try:
            res = verify_plan(args.verify_plan, args.plan_sha256)
        except Refused as exc:
            print(f"绑定核验失败: {exc}", file=sys.stderr)
            return 3
        print(json.dumps(res, ensure_ascii=False))
        return 0
    if not args.out_dir:
        print("需要 --out-dir，或使用 --verify-plan/--plan-sha256", file=sys.stderr)
        return 2
    out = args.out_dir if os.path.isabs(args.out_dir) else os.path.join(ROOT, args.out_dir)
    return 0 if not isinstance(build(out, publish_as=args.publish_as), Exception) else 2


if __name__ == "__main__":
    sys.exit(main())
