#!/usr/bin/env python3
"""prune_execute v2 —— 受清单驱动的不可逆删除执行器（默认 dry-run）。

v2 相对 v1 的收口（对应已确认的 4 个缺口）：
 1. dry-run 与 execute **共享同一套完整前置核验**（输入绑定 / 候选身份 / 保护证据 / 活动任务）；
    dry-run 任一项失败即返回非零，且不写回执、不改状态、不删除。
 2. 活动任务检查改读 `/proc/<pid>/cmdline`（完整 argv），并按进程 cwd 解析相对路径，
    递归读取实际 spec 中的本地依赖引用；无法识别即 fail closed。
 3. 全局 fcntl 排他锁 + 两阶段 INTENT/DELETED 持久化 + 冻结清单逐文件删除（可选 A 语义）。
 4. 保护证据完整重验：模型/候选/祖先/ONNX/证据文件/引用文档（spec、manifest、terminal）。

安全边界：根目录来自主计划 `root`；无 `--root` / `--force` / `--yes` / 通配符能力。
删除不可逆，且**不是**可回滚的原子事务。
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone, timedelta

EXECUTOR_VERSION = "prune_execute_v2"
SCHEMA_PLAN = "prune_plan_v1"
SCHEMA_ENTRIES = "prune_entries_v1"
SCHEMA_KEEP = "prune_keep_v1"
SCHEMA_APPROVAL = "prune_approval_v1"
SCHEMA_RECEIPT = "prune_receipt_v2"

RECEIPT_DIR_REL = "artifacts/prune_execution_receipts"
LOCK_NAME = ".prune.lock"
RECEIPT_MAX_BYTES = 512 * 1024 * 1024

SHA_TZ = timezone(timedelta(hours=8))

HARD_FORBIDDEN_TOP = {
    ".git", "src", "tests", "scripts", "configs", "docs", "assets",
    "deployment_protocol", ".github", ".codebuddy",
}

STATUS_PLANNED = "PLANNED"
STATUS_INTENT = "INTENT"
STATUS_DELETED = "DELETED"
STATUS_FAILED = "FAILED"
STATUS_MISSING = "MISSING_UNEXPLAINED"
STATUS_ALREADY = "ALREADY_DELETED_BY_THIS_EXECUTION"
DONE_STATUSES = (STATUS_DELETED, STATUS_ALREADY)

STRICT_TASK_MARKERS = ("stand_chain", "monitor.py", "supervisor", "launcher.py",
                       "command_v6", "train.py", "--spec", "-m native_stand", "source_eval")
LOOSE_MARKERS = ("wheel_leg_native_train", "native_stand")

# 只递归“配方 spec”白名单；不进入 run 内的 source_snapshot 历史副本
# （历史副本的祖先链由受保护模型的祖先图覆盖，不构成活动任务的实时依赖）
SPEC_FOLLOW_PREFIXES = ("configs/experiments/",)
NEVER_FOLLOW_SUBSTR = ("source_snapshot",)
MAX_SPEC_DEPTH = 2
MAX_SPEC_FILES = 64
SPEC_FOLLOW_KEYS = ("spec", "spec_path", "parent_spec", "recipe_parent_spec")


class Refused(Exception):
    """任何安全条件不满足；调用方必须 fail closed。"""


# ---------------------------------------------------------------- 基础工具


def now() -> str:
    return datetime.now(SHA_TZ).strftime("%Y-%m-%d %H:%M:%S CST")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def load_and_verify(path: str, expected_sha: str, what: str) -> dict:
    if not path or not os.path.isfile(path):
        raise Refused(f"{what}: 文件不存在 {path}")
    actual = sha256_file(path)
    if actual != expected_sha:
        raise Refused(f"{what}: SHA256 不匹配\n  期望 {expected_sha}\n  实际 {actual}")
    try:
        with open(path) as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise Refused(f"{what}: JSON 解析失败 {exc}") from exc


# ---------------------------------------------------------------- 路径


def _parse(rel: str) -> tuple:
    if not isinstance(rel, str) or rel == "":
        raise Refused("路径拒绝: 空路径")
    if rel != rel.strip():
        raise Refused(f"路径拒绝: 前后含空白 {rel!r}")
    if rel.startswith("/") or os.path.isabs(rel) or rel.startswith("~"):
        raise Refused(f"路径拒绝: 绝对路径 {rel!r}")
    if any(ch in rel for ch in "*?[]{}"):
        raise Refused(f"路径拒绝: 通配符 {rel!r}")
    if "\\" in rel:
        raise Refused(f"路径拒绝: 反斜杠 {rel!r}")
    parts = tuple(rel.split("/"))
    if any(p in ("", ".", "..") for p in parts):
        raise Refused(f"路径拒绝: 含空/./.. 组件 {rel!r}")
    if parts == ("",):
        raise Refused("路径拒绝: 项目根")
    return parts


def parse_parts(rel: str) -> tuple:
    """仅语法解析（保护集合路径允许 assets/src 等顶层）。"""
    return _parse(rel)


def normalize_parts(rel: str) -> tuple:
    """删除条目专用：语法解析 + 硬保护顶层拒绝。"""
    parts = _parse(rel)
    if parts[0] in HARD_FORBIDDEN_TOP:
        raise Refused(f"路径拒绝: 硬保护顶层目录 {parts[0]}")
    return parts


def resolve_entry(root: str, rel: str) -> str:
    parts = normalize_parts(rel)
    root_real = os.path.realpath(root)
    cur = root_real
    for comp in parts[:-1]:
        cur = os.path.join(cur, comp)
        if os.path.islink(cur):
            raise Refused(f"路径拒绝: 父路径含 symlink {os.path.relpath(cur, root_real)}")
    target = os.path.join(root_real, *parts)
    parent_real = os.path.realpath(os.path.dirname(target))
    if parent_real != root_real and not parent_real.startswith(root_real + os.sep):
        raise Refused(f"路径拒绝: 越出项目根 {rel!r}")
    return target


def within(child_parts: tuple, parent_parts: tuple) -> bool:
    return child_parts[: len(parent_parts)] == parent_parts and len(child_parts) >= len(parent_parts)


def overlaps(a: tuple, b: tuple) -> bool:
    return within(a, b) or within(b, a)


# ---------------------------------------------------------------- 保护集合


def build_protected(keep: dict, protected_models: dict, review_paths) -> tuple:
    """消费 keep_manifest 的**全部**字段；返回 (保护路径组件集合, 来源映射)。"""
    if keep.get("schema") != SCHEMA_KEEP:
        raise Refused(f"keep_manifest schema 不支持: {keep.get('schema')}")
    sources: dict = {}

    def add(rel, reason):
        if rel in (".", "./", ""):
            raise Refused("保护集合不允许为项目根")
        sources.setdefault(parse_parts(rel), reason)

    for item in keep.get("protected_paths", []):
        add(item["path"], f"protected_paths: {item.get('reason', '')}")
    for item in keep.get("protected_checkpoints", []):
        add(item["path"], "protected_checkpoints")
    for item in keep.get("protected_onnx", []):
        add(item["path"], "protected_onnx")
    for item in keep.get("ancestor_minimal_package", []):
        add(item["path"], f"ancestor_minimal_package: {item.get('reason', '')}")
    for item in keep.get("required_evidence", []):
        add(item["path"], f"required_evidence: {item.get('reason', '')}")
    for item in keep.get("evidence_identity", []):
        add(item["path"], "evidence_identity")
    for item in keep.get("reference_documents", []):
        add(item["path"], "reference_documents")
    for item in keep.get("never_delete", []):
        add(item, "never_delete")
    for item in keep.get("active_task_dependencies", []):
        add(item["path"], f"active_task_dependencies: {item.get('reason', '')}")
    for rel in review_paths:
        add(rel, "REVIEW_REQUIRED / UNKNOWN（默认保护）")

    for _k, v in (protected_models.get("categories") or {}).items():
        for c in v.get("candidates", []):
            if c.get("path"):
                add(c["path"], f"protected_models.{_k}.candidates")
        for a in v.get("ancestors", []):
            if a.get("path"):
                add(a["path"], f"protected_models.{_k}.ancestors")
    return set(sources.keys()), sources


def identity_bound_files(keep: dict, protected_models: dict) -> list:
    """收集所有声明了 SHA256 的必要身份文件（用于执行前完整重验）。"""
    out, seen = [], set()

    def add(path, sha, reason):
        if not path or path in seen:
            return
        seen.add(path)
        out.append({"path": path, "sha256": sha, "reason": reason})

    for item in keep.get("protected_checkpoints", []):
        add(item["path"], item.get("sha256"), "protected_checkpoints")
    for item in keep.get("protected_onnx", []):
        add(item["path"], item.get("sha256"), "protected_onnx")
    for item in keep.get("evidence_identity", []):
        add(item["path"], item.get("sha256"), "evidence_identity")
    for item in keep.get("required_evidence", []):
        add(item["path"], item.get("sha256"), "required_evidence")
    for item in keep.get("ancestor_minimal_package", []):
        add(item["path"], item.get("sha256"), "ancestor_minimal_package")
    for _k, v in (protected_models.get("categories") or {}).items():
        for c in list(v.get("candidates", [])) + list(v.get("ancestors", [])):
            add(c.get("path"), c.get("sha256"), f"protected_models.{_k}")
    return out


def check_entry_allowed(root: str, rel: str, protected: set, seen: list) -> tuple:
    parts = normalize_parts(rel)
    for s in seen:
        if parts == s["parts"]:
            raise Refused(f"重复条目: {rel}")
        if overlaps(parts, s["parts"]):
            raise Refused(f"父子重叠条目: {rel} 与 {s['rel']}")
    for p in protected:
        if overlaps(parts, p):
            raise Refused(f"命中保护集合: {rel} 与 {'/'.join(p)}")
    resolve_entry(root, rel)
    return parts


# ---------------------------------------------------------------- 身份清单


def build_manifest(root: str, rel: str) -> dict:
    """构建身份清单：文件 size+sha256；symlink 文本；目录条目。不跟随 symlink。"""
    target = resolve_entry(root, rel)
    if os.path.islink(target):
        return {"kind": "symlink", "link_target": os.readlink(target), "entries": []}
    if os.path.isfile(target):
        st = os.lstat(target)
        return {"kind": "file", "size": st.st_size, "sha256": sha256_file(target),
                "actual_bytes": st.st_blocks * 512, "entries": []}
    if not os.path.isdir(target):
        raise Refused(f"身份核验: 目标既不是文件也不是目录 {rel}")

    entries = []
    for dp, dn, fn in os.walk(target, followlinks=False):
        for name in sorted(dn):
            p = os.path.join(dp, name)
            r = os.path.relpath(p, root)
            if os.path.islink(p):
                entries.append({"path": r, "kind": "symlink", "link_target": os.readlink(p)})
            else:
                entries.append({"path": r, "kind": "dir"})
        for name in sorted(fn):
            p = os.path.join(dp, name)
            r = os.path.relpath(p, root)
            if os.path.islink(p):
                entries.append({"path": r, "kind": "symlink", "link_target": os.readlink(p)})
            else:
                st = os.lstat(p)
                entries.append({"path": r, "kind": "file", "size": st.st_size,
                                "sha256": sha256_file(p), "actual_bytes": st.st_blocks * 512})
    entries.sort(key=lambda e: e["path"])
    digest = sha256_bytes(canonical(entries))
    return {"kind": "dir", "actual_bytes": sum(e.get("actual_bytes", 0) for e in entries),
            "file_count": sum(1 for e in entries if e["kind"] == "file"),
            "manifest_sha256": digest, "entries": entries}


def verify_entry_resumable(root: str, entry: dict) -> None:
    """中断恢复用：剩余内容必须是冻结清单的子集，且每项身份仍一致。"""
    rel = entry["path"]
    identity = entry["identity"]
    target = os.path.join(root, rel)
    if not os.path.lexists(target):
        raise Refused(f"恢复核验: {rel} 已不存在（无本次删除记录）")
    if identity["kind"] == "symlink":
        if os.readlink(target) != identity["link_target"]:
            raise Refused(f"恢复核验: {rel} symlink 目标变化")
        return
    if identity["kind"] == "file":
        st = os.lstat(target)
        if st.st_size != identity["size"] or sha256_file(target) != identity["sha256"]:
            raise Refused(f"恢复核验: {rel} 文件内容变化")
        return
    frozen = {e["path"]: e for e in identity["entries"]}
    cur = _current_paths(target, root)
    extra = sorted(set(cur) - set(frozen))
    if extra:
        raise Refused(f"恢复核验: {rel} 出现冻结清单之外的新条目 {extra[:5]}")
    for path, kind in cur.items():
        rec = frozen.get(path)
        if rec is None:
            raise Refused(f"恢复核验: {rel} 出现未记录条目 {path}")
        if rec["kind"] != kind:
            raise Refused(f"恢复核验: {rel} 条目 {path} 类型由 {rec['kind']} 变为 {kind}")
        if kind == "file":
            st = os.lstat(os.path.join(root, path))
            if st.st_size != rec["size"] or sha256_file(os.path.join(root, path)) != rec["sha256"]:
                raise Refused(f"恢复核验: {rel} 条目 {path} 内容变化")
        elif kind == "symlink":
            if os.readlink(os.path.join(root, path)) != rec["link_target"]:
                raise Refused(f"恢复核验: {rel} 条目 {path} symlink 目标变化")


def verify_entry_identity(root: str, entry: dict) -> None:
    rel = entry["path"]
    recorded = entry["identity"]
    cur = build_manifest(root, rel)
    if cur["kind"] != recorded["kind"]:
        raise Refused(f"身份核验: {rel} 类型由 {recorded['kind']} 变为 {cur['kind']}")
    if recorded["kind"] == "symlink":
        if cur["link_target"] != recorded["link_target"]:
            raise Refused(f"身份核验: {rel} symlink 目标变化")
        return
    if recorded["kind"] == "file":
        if cur["size"] != recorded["size"] or cur["sha256"] != recorded["sha256"]:
            raise Refused(f"身份核验: {rel} 文件内容变化")
        return
    if cur["manifest_sha256"] != recorded["manifest_sha256"]:
        old = {e["path"]: e for e in recorded["entries"]}
        new = {e["path"]: e for e in cur["entries"]}
        added = sorted(set(new) - set(old))[:5]
        removed = sorted(set(old) - set(new))[:5]
        changed = sorted(k for k in set(old) & set(new) if old[k] != new[k])[:5]
        raise Refused(f"身份核验: {rel} 目录内容变化 (新增={added} 缺失={removed} 变化={changed})")


# ---------------------------------------------------------------- 活动任务


def _self_and_ancestors() -> set:
    pids = {str(os.getpid()), str(os.getppid())}
    cur = os.getppid()
    for _ in range(32):
        try:
            with open(f"/proc/{cur}/stat") as fh:
                rest = fh.read().rsplit(")", 1)[1].split()
            ppid = int(rest[1])
        except Exception:  # noqa: BLE001
            break
        if ppid <= 1 or str(ppid) in pids:
            break
        pids.add(str(ppid))
        cur = ppid
    return pids


def _looks_like_project_path(value: str, root_real: str, base_dirs) -> list:
    """把字符串解析为**确实存在**的项目内相对路径。

    只接受磁盘上真实存在的路径：这样既不会漏掉 spec 里真实引用的 checkpoint/输出目录，
    也不会把姿态标签、SHA 字符串、超参名等普通取值误判成路径。
    """
    if not isinstance(value, str) or not value:
        return []
    v = value.strip()
    if not v or v.startswith("-"):
        return []
    if "=" in v and len(v.split("=", 1)[0]) <= 32:
        rhs = v.split("=", 1)[1]
        if rhs.startswith(("/", "runs/", "isolated/", "artifacts/", "configs/")):
            v = rhs
    cands = []
    if v.startswith("/"):
        if v == root_real or v.startswith(root_real + os.sep):
            cands.append(v[len(root_real):].lstrip("/"))
        else:
            return []
    else:
        cands.append(v)
        for b in base_dirs:
            if b:
                cands.append(os.path.normpath(os.path.join(b, v)))
    out, seen = [], set()
    for c in cands:
        try:
            parts = parse_parts(c)
        except Refused:
            continue
        if not parts or parts in seen:
            continue
        if not os.path.exists(os.path.join(root_real, *parts)):
            continue
        if not os.path.isdir(os.path.join(root_real, parts[0])):
            continue
        seen.add(parts)
        out.append(parts)
    return out


def _iter_strings(obj, key_path=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(v, key_path + (str(k),))
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_strings(v, key_path)
    elif isinstance(obj, str):
        yield key_path, obj


def collect_spec_refs(spec_abs: str, root_real: str, base_dirs, depth: int = 0,
                      seen=None, out=None) -> set:
    """从实际 spec 递归收集本地路径引用（只读配置，不读训练 log/progress/metrics）。"""
    seen = set() if seen is None else seen
    out = set() if out is None else out
    if depth > MAX_SPEC_DEPTH or len(seen) >= MAX_SPEC_FILES:
        return out
    real = os.path.realpath(spec_abs)
    if real in seen or not os.path.isfile(real):
        return out
    seen.add(real)
    try:
        with open(real) as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        raise Refused(f"活动 spec 无法解析，fail closed: {spec_abs} :: {exc}") from exc

    follow = []
    spec_dir = os.path.dirname(os.path.relpath(real, root_real))
    bases = [root_real, spec_dir or "."] + list(base_dirs)
    key_ends = tuple(SPEC_FOLLOW_KEYS)
    for key_path, value in _iter_strings(doc):
        resolved = _looks_like_project_path(value, root_real, bases)
        for parts in resolved:
            out.add(parts)
        key = str(key_path[-1]) if key_path else ""
        if not key.endswith(key_ends):
            continue
        for parts in resolved:
            rel = "/".join(parts)
            if not rel.startswith(SPEC_FOLLOW_PREFIXES):
                continue
            if any(s in rel for s in NEVER_FOLLOW_SUBSTR):
                continue
            if rel.endswith(".json"):
                follow.append(os.path.join(root_real, *parts))
    for f in sorted(set(follow)):
        collect_spec_refs(f, root_real, bases, depth + 1, seen, out)
    return out


def _extract_spec_paths(argv, root_real: str, cwd: str | None) -> list:
    """支持 --spec PATH / --spec=PATH / 位置参数指向 *.json。"""
    specs, i = [], 0
    while i < len(argv):
        tok = argv[i]
        val = None
        if tok == "--spec" and i + 1 < len(argv):
            val = argv[i + 1]
            i += 2
        elif tok.startswith("--spec="):
            val = tok.split("=", 1)[1]
            i += 1
        elif tok.endswith(".json") and not tok.startswith("-"):
            val = tok
            i += 1
        else:
            i += 1
        if not val:
            continue
        for parts in _looks_like_project_path(val, root_real, [cwd or "."]):
            specs.append(os.path.join(root_real, *parts))
    return sorted(set(specs))


def scan_active_processes(project_root: str) -> dict:
    """一次只读进程快照：完整 argv（/proc/<pid>/cmdline）+ cwd + spec 递归依赖。"""
    root_real = os.path.realpath(project_root)
    self_tree = _self_and_ancestors()
    procs, unresolved_cwd, unresolved_spec, unresolved_cmdline = [], 0, 0, 0

    try:
        entries = sorted(d for d in os.listdir("/proc") if d.isdigit())
    except OSError as exc:
        raise Refused(f"活动进程检查失败，fail closed: 无法列出 /proc :: {exc}") from exc
    if not entries:
        raise Refused("活动进程检查失败，fail closed: /proc 为空")

    for pid in entries:
        if pid in self_tree:
            continue
        raw = None
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                raw = fh.read()
        except OSError:
            raw = None
        argv = [t for t in raw.decode("utf-8", "ignore").split("\0") if t] if raw else []
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError:
            cwd = None

        cwd_parts = None
        if cwd:
            real = os.path.realpath(cwd)
            if real == root_real:
                cwd_parts = ()
            elif real.startswith(root_real + os.sep):
                try:
                    cwd_parts = parse_parts(os.path.relpath(real, root_real))
                except Refused:
                    cwd_parts = None
                    cwd = None

        argv_abs = []
        for tok in argv:
            argv_abs += _looks_like_project_path(tok, root_real, [cwd or "."])

        related = bool(cwd_parts is not None) or bool(argv_abs)
        if not related:
            continue

        kind = "task" if any(m in " ".join(argv) for m in STRICT_TASK_MARKERS) else "other"
        if raw is None and kind == "task":
            unresolved_cmdline += 1
        if cwd is None and kind == "task":
            unresolved_cwd += 1

        refs = {tuple(p) for p in argv_abs}
        if cwd_parts:
            refs.add(tuple(cwd_parts))
        specs = _extract_spec_paths(argv, root_real, cwd)
        for s in specs:
            try:
                refs |= collect_spec_refs(s, root_real, [cwd or "."])
            except Refused:
                unresolved_spec += 1

        procs.append({
            "pid": pid, "argv": argv[:64], "cwd": cwd, "cwd_parts": cwd_parts,
            "kind": kind, "specs": [os.path.relpath(s, root_real) for s in specs],
            "refs": sorted("/".join(r) for r in refs if r),
        })

    return {"count": len(procs), "processes": procs,
            "unresolved_cwd": unresolved_cwd,
            "unresolved_spec": unresolved_spec,
            "unresolved_cmdline": unresolved_cmdline}


def conflicting_entries(active: dict, entry_paths, root: str = None) -> dict:
    """返回 {候选路径: [冲突原因...]}，供执行器与清单生成器共用同一套判定。"""
    out: dict = {}
    cand = [(p, parse_parts(p)) for p in entry_paths]
    for p in active.get("processes", []):
        cwd_parts = p.get("cwd_parts")
        refs = [parse_parts(r) for r in (p.get("refs") or []) if r]
        for rel, c in cand:
            if cwd_parts and len(cwd_parts) > 0 and within(cwd_parts, c):
                out.setdefault(rel, set()).add(f"pid {p['pid']} ({p['kind']}) cwd 位于 {rel} 内")
            for r in refs:
                if overlaps(c, r):
                    out.setdefault(rel, set()).add(
                        f"pid {p['pid']} ({p['kind']}) 引用 {'/'.join(r)}")
    return {k: sorted(v) for k, v in out.items()}


def active_task_conflicts(active: dict, entry_paths, root: str = None) -> list:
    conflicts = []
    if active.get("unresolved_cwd"):
        conflicts.append("UNRESOLVED_CWD: 有本项目任务进程读不到 cwd，按未知范围处理")
    if active.get("unresolved_spec"):
        conflicts.append("UNRESOLVED_SPEC: 有本项目任务的 spec 无法解析，按未知范围处理")
    if active.get("unresolved_cmdline"):
        conflicts.append("UNRESOLVED_CMDLINE: 有本项目任务进程读不到 cmdline")
    for rel, reasons in conflicting_entries(active, entry_paths, root).items():
        for r in reasons:
            conflicts.append(f"{r} → 冲突候选 {rel}")
    return sorted(set(conflicts))


# ---------------------------------------------------------------- 保护证据


def collect_doc_refs(doc_path: str, root_real: str) -> set:
    """仅检查该文档自身声明的引用（不递归），保证保护证据核验可控且快速。"""
    out = set()
    real = os.path.realpath(doc_path)
    if not os.path.isfile(real):
        return out
    try:
        with open(real) as fh:
            doc = json.load(fh)
    except Exception:  # noqa: BLE001
        return out
    bases = [root_real, os.path.dirname(os.path.relpath(real, root_real)) or "."]
    for _kp, value in _iter_strings(doc):
        for parts in _looks_like_project_path(value, root_real, bases):
            out.add(parts)
    return out


def verify_protected_evidence(root: str, keep: dict, protected_models: dict,
                              candidate_parts) -> dict:
    """完整重验所有声明了 SHA 的身份文件，并检查引用文档不越界、不指向候选。

    引用目标不存在的历史引用只记录（不掩盖、不放行），因为删除不会使其更糟；
    但引用**指向删除候选**或**越出项目根**一律拒绝。
    """
    root_real = os.path.realpath(root)
    checked, refs_checked = 0, 0
    missing_targets, escaped = [], []

    for item in identity_bound_files(keep, protected_models):
        rel = item["path"]
        parse_parts(rel)
        full = os.path.join(root_real, rel)
        if not os.path.exists(full):
            raise Refused(f"保护证据核验: 必需文件缺失 {rel}")
        if os.path.isfile(full) and item.get("sha256"):
            actual = sha256_file(full)
            if actual != item["sha256"]:
                raise Refused(f"保护证据核验: {rel} SHA256 不匹配（{item['reason']}）")
            checked += 1
        elif os.path.isfile(full):
            raise Refused(f"保护证据核验: {rel} 未声明 SHA256，无法身份绑定（{item['reason']}）")

    for doc in keep.get("reference_documents", []):
        rel = doc["path"]
        full = os.path.join(root_real, rel)
        if not os.path.isfile(full):
            raise Refused(f"引用文档缺失 {rel}")
        if doc.get("sha256") and sha256_file(full) != doc["sha256"]:
            raise Refused(f"引用文档 SHA256 不匹配 {rel}")
        for ref in collect_doc_refs(full, root_real):
            if not ref:
                continue
            if ref[0] in HARD_FORBIDDEN_TOP:
                continue  # 源码/资产等顶层引用属于受保护范围，非删除候选
            refs_checked += 1
            target = os.path.join(root_real, *ref)
            if not os.path.realpath(target).startswith(root_real + os.sep):
                escaped.append(f"{rel} → {'/'.join(ref)}")
                continue
            if not os.path.exists(target):
                missing_targets.append(f"{rel} → {'/'.join(ref)}")
                continue
            for c in candidate_parts:
                if overlaps(ref, c):
                    raise Refused(
                        f"引用文档 {rel} 指向删除候选 {'/'.join(ref)}；"
                        "该候选必须从清单中剔除（不得忽略引用）")
    if escaped:
        raise Refused("引用文档越出项目根，拒绝执行: " + "; ".join(sorted(set(escaped))[:5]))
    return {"identity_files_checked": checked,
            "documents": len(keep.get("reference_documents", [])),
            "references_checked": refs_checked,
            "missing_reference_targets": sorted(set(missing_targets))[:50],
            "missing_reference_target_count": len(set(missing_targets))}


# ---------------------------------------------------------------- 回收量


def hardlink_shared_bytes(root: str, rels) -> dict:
    """统计批次内 hardlink 重复；并区分“批次外仍有链接”导致无法释放的数据块。"""
    groups: dict = {}
    total = 0
    dir_blocks = 0
    for rel in rels:
        target = os.path.join(root, rel)
        for dp, dn, fn in os.walk(target, followlinks=False):
            for name in dn:
                p = os.path.join(dp, name)
                if not os.path.islink(p):
                    dir_blocks += os.lstat(p).st_blocks * 512
            for f in fn:
                p = os.path.join(dp, f)
                if os.path.islink(p):
                    continue
                st = os.lstat(p)
                total += st.st_blocks * 512
                groups.setdefault((st.st_dev, st.st_ino), []).append(st.st_blocks * 512)
    shared_in_batch = 0
    unreclaimable = 0
    nlink_groups = 0
    for inode, blocks_list in groups.items():
        if len(blocks_list) > 1:
            nlink_groups += 1
            shared_in_batch += sum(blocks_list[1:])
    # 批次外仍有链接：该 inode 的数据块在本批删除后不会释放
    for rel in rels:
        target = os.path.join(root, rel)
        for dp, _, fn in os.walk(target, followlinks=False):
            for f in fn:
                p = os.path.join(dp, f)
                if os.path.islink(p):
                    continue
                st = os.lstat(p)
                if st.st_nlink > len(groups.get((st.st_dev, st.st_ino), [])):
                    unreclaimable += st.st_blocks * 512
    file_blocks = total
    return {"file_blocks": file_blocks, "dir_blocks": dir_blocks,
            "total_actual_bytes": file_blocks + dir_blocks,
            "hardlink_groups": nlink_groups,
            "hardlink_shared_bytes": shared_in_batch,
            "hardlink_outside_bytes": unreclaimable,
            "net_reclaim_bytes": file_blocks + dir_blocks - shared_in_batch - unreclaimable,
            "note": ("file_blocks/dir_blocks 为 st_blocks×512 之和；"
                     "hardlink_shared_bytes 为批次内重复副本；"
                     "hardlink_outside_bytes 为批次外仍持有链接、删除后不释放的数据块；"
                     "未计入 inode/块对齐与历史碎片误差")}


def overlap_report(entries) -> list:
    parts = [normalize_parts(e["path"]) for e in entries]
    out = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if overlaps(parts[i], parts[j]):
                out.append((entries[i]["path"], entries[j]["path"]))
    return out


# ---------------------------------------------------------------- 锁与回执


def receipt_dir(root: str) -> str:
    return os.path.join(root, RECEIPT_DIR_REL)


def acquire_lock(root: str):
    d = receipt_dir(root)
    os.makedirs(d, exist_ok=True)
    lock_path = os.path.join(d, LOCK_NAME)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        os.close(fd)
        raise Refused(f"另一个清理执行器正在运行（全局清理锁被持有）: {lock_path}") from exc
    os.ftruncate(fd, 0)
    os.write(fd, f"pid={os.getpid()} at={now()}\n".encode())
    return fd


def receipt_file(root: str, execution_id: str) -> str:
    return os.path.join(receipt_dir(root), f"{execution_id}.json")


def _digest_receipt(payload: dict) -> str:
    body = {k: v for k, v in payload.items() if k != "digest"}
    return sha256_bytes(canonical(body))


def save_receipt(path: str, payload: dict) -> None:
    payload["digest"] = _digest_receipt(payload)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    dfd = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def load_receipt(path: str) -> dict:
    if not os.path.isfile(path):
        raise Refused(f"回执不存在 {path}")
    if os.path.getsize(path) > RECEIPT_MAX_BYTES:
        raise Refused("回执过大，拒绝解析")
    payload = json.load(open(path))
    if payload.get("schema") != SCHEMA_RECEIPT:
        raise Refused(f"回执 schema 不支持: {payload.get('schema')}")
    if payload.get("digest") != _digest_receipt(payload):
        raise Refused("回执自校验失败（digest 不匹配），拒绝恢复")
    return payload


# ---------------------------------------------------------------- 契约装载


def load_contract(plan_path: str, plan_sha: str) -> dict:
    plan = load_and_verify(plan_path, plan_sha, "主计划")
    if plan.get("schema") != SCHEMA_PLAN:
        raise Refused(f"主计划 schema 不支持: {plan.get('schema')}")
    if plan.get("executor", {}).get("version") != EXECUTOR_VERSION:
        raise Refused("执行器版本与计划不一致（旧计划不适配新执行器）")
    return plan


def bind_inputs(plan: dict, root: str) -> dict:
    out = {}
    for key in ("keep_manifest", "protected_models", "entries", "review_entries"):
        spec = (plan.get("inputs") or {}).get(key)
        if not spec:
            raise Refused(f"主计划缺少 inputs.{key} 绑定")
        parse_parts(spec["path"])
        p = os.path.join(root, spec["path"])
        if not os.path.isfile(p):
            raise Refused(f"inputs.{key}: 绑定文件不存在 {spec['path']}")
        out[key] = load_and_verify(p, spec["sha256"], f"inputs.{key}")
        out[key + "__path"] = p
    ex = (plan.get("executor") or {})
    parse_parts(ex.get("path", ""))
    ex_path = os.path.join(root, ex["path"])
    if not os.path.isfile(ex_path):
        raise Refused(f"执行器自身路径不存在 {ex.get('path')}")
    actual = sha256_file(ex_path)
    if actual != ex.get("sha256"):
        raise Refused(f"执行器 SHA256 不匹配\n  期望 {ex.get('sha256')}\n  实际 {actual}")
    return out


def verify_approval(approval_path: str, approval_sha: str, plan_sha: str, plan: dict,
                    inputs: dict) -> dict:
    """独立批准回执：只绑定不可变候选清单，不能扩大范围。"""
    ap = load_and_verify(approval_path, approval_sha, "批准回执")
    if ap.get("schema") != SCHEMA_APPROVAL:
        raise Refused(f"批准回执 schema 不支持: {ap.get('schema')}")
    exp = {
        "approved_plan_sha256": plan_sha,
        "entries_sha256": plan["inputs"]["entries"]["sha256"],
        "keep_manifest_sha256": plan["inputs"]["keep_manifest"]["sha256"],
        "protected_models_sha256": plan["inputs"]["protected_models"]["sha256"],
        "executor_sha256": plan["executor"]["sha256"],
        "scope": plan.get("plan_scope"),
        "entry_count": plan.get("entry_count"),
    }
    for k, v in exp.items():
        if ap.get(k) != v:
            raise Refused(f"批准回执绑定不符: {k} 期望 {v!r} 实际 {ap.get(k)!r}")
    if not ap.get("explicit_user_approval_text"):
        raise Refused("批准回执缺少 explicit_user_approval_text")
    return ap


# ---------------------------------------------------------------- 删除


def _frozen_sorted(identity: dict) -> tuple:
    ents = identity.get("entries", [])
    files = [e for e in ents if e["kind"] in ("file", "symlink")]
    dirs = [e for e in ents if e["kind"] == "dir"]
    key = lambda e: (e["path"].count("/"), e["path"])
    files.sort(key=key, reverse=True)
    dirs.sort(key=key, reverse=True)
    return files, dirs


def _current_paths(target: str, root: str) -> dict:
    cur = {}
    for dp, dn, fn in os.walk(target, followlinks=False):
        for name in dn + fn:
            p = os.path.join(dp, name)
            cur[os.path.relpath(p, root)] = "symlink" if os.path.islink(p) else \
                ("dir" if os.path.isdir(p) and not os.path.islink(p) else "file")
    return cur


def delete_entry(root: str, entry: dict, on_intent, on_deleted) -> None:
    """按冻结清单逐项删除；symlink 只删本体；目录最后自深到浅 rmdir。"""
    rel = entry["path"]
    target = resolve_entry(root, rel)
    identity = entry["identity"]

    if identity["kind"] == "symlink":
        on_intent()
        if os.readlink(target) != identity["link_target"]:
            raise Refused(f"删除前身份变化: {rel} symlink 目标变化")
        os.unlink(target)
        on_deleted()
        return

    if identity["kind"] == "file":
        on_intent()
        st = os.lstat(target)
        if st.st_size != identity["size"] or sha256_file(target) != identity["sha256"]:
            raise Refused(f"删除前身份变化: {rel} 文件内容变化")
        os.unlink(target)
        on_deleted()
        return

    on_intent()
    frozen_files, frozen_dirs = _frozen_sorted(identity)
    frozen_map = {e["path"]: e for e in frozen_files}
    frozen_dir_set = {e["path"] for e in frozen_dirs}

    current = _current_paths(target, root)
    extra = sorted(set(current) - frozen_dir_set - set(frozen_map))
    if extra:
        raise Refused(f"删除中止: {rel} 出现冻结清单之外的条目 {extra[:5]}")

    for e in frozen_files:
        p = os.path.join(root, e["path"])
        if not os.path.lexists(p):
            continue
        if e["kind"] == "symlink":
            if os.readlink(p) != e["link_target"]:
                raise Refused(f"删除中止: {e['path']} symlink 目标变化")
            os.unlink(p)
        else:
            st = os.lstat(p)
            if st.st_size != e["size"] or sha256_file(p) != e["sha256"]:
                raise Refused(f"删除中止: {e['path']} 内容变化")
            os.unlink(p)

    for e in frozen_dirs:
        p = os.path.join(root, e["path"])
        if os.path.isdir(p) and not os.path.islink(p):
            try:
                os.rmdir(p)
            except OSError as exc:
                raise Refused(f"删除中止: 目录 {e['path']} 非空或不可删 {exc}") from exc
    try:
        os.rmdir(target)
    except OSError as exc:
        raise Refused(f"删除中止: 根目录 {rel} 非空或不可删 {exc}") from exc
    on_deleted()


# ---------------------------------------------------------------- 前置核验


def preflight(args, plan, root, inputs, entries, status_map=None):
    """dry-run 与 execute 共用的完整前置核验。任一项失败抛 Refused。"""
    status_map = dict(status_map or {})
    flags = {}
    review_paths = [e["path"] for e in inputs["review_entries"].get("entries", [])]
    protected, _src = build_protected(inputs["keep_manifest"], inputs["protected_models"],
                                      review_paths)
    flags["inputs_verified"] = True

    seen = []
    for e in entries:
        parts = check_entry_allowed(root, e["path"], protected, seen)
        seen.append({"rel": e["path"], "parts": parts})
    cand_parts = [s["parts"] for s in seen]
    flags["overlap_pairs"] = len(overlap_report(entries))

    st = inputs["keep_manifest"].get("active_task_snapshot") or {}
    if not st or st.get("error"):
        raise Refused(f"keep_manifest 缺少可用活动任务快照: {st.get('error')}")
    active = scan_active_processes(root)
    conflicts = active_task_conflicts(active, [e["path"] for e in entries], root)
    if conflicts:
        raise Refused("活动任务与候选冲突，拒绝执行: " + "; ".join(conflicts[:5]))
    flags["activity_verified"] = True

    ev = verify_protected_evidence(root, inputs["keep_manifest"], inputs["protected_models"],
                                   cand_parts)
    flags["protected_evidence"] = ev

    verified = 0
    resumed = 0
    for e in entries:
        st = status_map.get(e["path"], STATUS_PLANNED)
        if st in DONE_STATUSES:
            if os.path.lexists(os.path.join(root, e["path"])):
                raise Refused(f"状态变化: {e['path']} 已记录删除但重新出现，拒绝继续")
            continue
        if st in (STATUS_INTENT, STATUS_FAILED):
            if os.path.lexists(os.path.join(root, e["path"])):
                verify_entry_resumable(root, e)
            resumed += 1
        else:
            verify_entry_identity(root, e)
        verified += 1
    flags["candidate_identity_verified"] = verified
    flags["resumed_entries"] = resumed
    flags["protected_path_count"] = len(protected)
    return flags, cand_parts


# ---------------------------------------------------------------- 主流程


def run(args) -> int:
    try:
        plan = load_contract(args.plan, args.plan_sha256)
        root = plan["root"]
        if not os.path.isdir(root):
            raise Refused(f"项目根不存在 {root}")
        inputs = bind_inputs(plan, root)

        ef = inputs["entries"]
        if ef.get("schema") != SCHEMA_ENTRIES:
            raise Refused(f"entries schema 不支持: {ef.get('schema')}")
        entries = ef["entries"]
        if len(entries) != plan.get("entry_count"):
            raise Refused(f"条目数不一致: 计划 {plan.get('entry_count')} vs 清单 {len(entries)}")

        print(f"plan        : {args.plan}")
        print(f"plan sha256 : {args.plan_sha256}")
        print(f"root        : {root}")
        print(f"entries     : {len(entries)}")
        print(f"approval    : {plan.get('approval_status')}   execution: {plan.get('execution_status')}")

        # execution_id 只绑定**不可变**的计划 SHA 与条目清单 SHA，不含任何批准字段
        execution_id = sha256_bytes(
            (root + args.plan_sha256 + plan["inputs"]["entries"]["sha256"]).encode())[:16]
        rpath = receipt_file(root, execution_id)
        print(f"execution_id: {execution_id}")
        print(f"receipt     : {rpath}")

        status_map = {}
        approval = None
        if args.execute:
            if not args.approval or not args.approval_sha256:
                raise Refused("缺少 --approval/--approval-sha256：计划文件不等于用户授权")
            approval = verify_approval(args.approval, args.approval_sha256, args.plan_sha256,
                                       plan, inputs)
            print(f"approval_id : {approval.get('approval_id')}")
            if args.resume:
                if not args.receipt or os.path.realpath(args.receipt) != os.path.realpath(rpath):
                    raise Refused(f"恢复只接受受保护回执目录中的 {rpath}")
                if args.receipt_sha256 and sha256_file(args.receipt) != args.receipt_sha256:
                    raise Refused("回执 SHA256 不匹配")
                rec = load_receipt(rpath)
                if rec.get("execution_id") != execution_id:
                    raise Refused("回执 execution_id 不匹配")
                if rec.get("plan_sha256") != args.plan_sha256:
                    raise Refused("回执 plan_sha256 不匹配")
                if rec.get("entries_sha256") != plan["inputs"]["entries"]["sha256"]:
                    raise Refused("回执 entries_sha256 不匹配")
                if rec.get("status") == "COMPLETED":
                    raise Refused("该清单已完成，拒绝重复执行")
                status_map = {i["path"]: i.get("status") for i in rec.get("items", [])}
            elif os.path.exists(rpath):
                raise Refused(f"同一 execution_id 回执已存在，拒绝重复执行: {rpath}")

        flags, cand_parts = preflight(args, plan, root, inputs, entries, status_map)
        print(f"inputs_verified            : {flags.get('inputs_verified')}")
        print(f"candidate_identity_verified: {flags.get('candidate_identity_verified')}")
        print(f"protected_evidence_verified: {flags.get('protected_evidence')}")
        print(f"activity_verified          : {flags.get('activity_verified')}")
        print(f"protected_paths            : {flags.get('protected_path_count')}")
        print(f"overlap_pairs              : {flags.get('overlap_pairs')}")

        hl = hardlink_shared_bytes(root, [e["path"] for e in entries])
        print(f"file_blocks     : {hl['file_blocks']/2**30:.3f} GiB")
        print(f"dir_blocks      : {hl['dir_blocks']/2**30:.3f} GiB")
        print(f"hardlink in-batch shared  : {hl['hardlink_shared_bytes']/2**30:.3f} GiB (groups={hl['hardlink_groups']})")
        print(f"hardlink outside-links    : {hl['hardlink_outside_bytes']/2**30:.3f} GiB")
        print(f"NET reclaim               : {hl['net_reclaim_bytes']/2**30:.2f} GiB")
        print("deletions_performed       : 0")

        if not args.execute:
            print("\nDRY-RUN OK：未删除任何文件；未写执行回执；未改批准状态。")
            return 0

        # ---------------- execute：持锁后二次确认回执状态 ----------------
        lock_fd = acquire_lock(root)
        try:
            if args.resume:
                receipt = load_receipt(rpath)
            else:
                if os.path.exists(rpath):
                    raise Refused(f"同一 execution_id 回执已存在，拒绝重复执行: {rpath}")
                receipt = {
                    "schema": SCHEMA_RECEIPT,
                    "execution_id": execution_id,
                    "plan_path": args.plan,
                    "plan_sha256": args.plan_sha256,
                    "entries_sha256": plan["inputs"]["entries"]["sha256"],
                    "approval_id": approval.get("approval_id"),
                    "executor_version": EXECUTOR_VERSION,
                    "started_at": now(),
                    "status": "RUNNING",
                    "items": [],
                    "note": "删除不可逆，且不是可回滚的原子事务；INTENT 先于删除，DELETED 后于删除。",
                }
                save_receipt(rpath, receipt)

            results = {i["path"]: i for i in receipt.get("items", [])}
            for e in entries:
                results.setdefault(e["path"], {"path": e["path"], "status": STATUS_PLANNED})

            def flush():
                receipt["items"] = [results[e["path"]] for e in entries]
                save_receipt(rpath, receipt)

            def flush_best_effort():
                """失败路径上的尽力记录；写盘失败不得掩盖原始错误。"""
                try:
                    flush()
                except Exception:  # noqa: BLE001
                    pass

            for e in entries:
                rel = e["path"]
                rec = results[rel]
                target = os.path.join(root, rel)
                if rec["status"] in DONE_STATUSES:
                    if os.path.lexists(target):
                        rec.update({"status": STATUS_FAILED, "at": now(),
                                    "error": "已删除目标重新出现，状态变化"})
                        flush_best_effort()
                        raise Refused(f"状态变化: {rel} 已记录删除但重新出现，拒绝继续")
                    continue
                if not os.path.lexists(target):
                    if rec["status"] in (STATUS_INTENT, STATUS_FAILED):
                        rec.update({"status": STATUS_ALREADY, "at": now(),
                                    "error": "本次执行已删除该目标（中断前完成）"})
                        flush()
                        continue
                    rec.update({"status": STATUS_MISSING, "at": now()})
                    flush_best_effort()
                    raise Refused(f"状态变化: {rel} 不存在且无本次删除记录，立即停止")

                def on_intent(r=rec):
                    r.update({"status": STATUS_INTENT, "at": now()})
                    flush()

                def on_deleted(r=rec):
                    r.update({"status": STATUS_DELETED, "at": now()})
                    flush()

                try:
                    delete_entry(root, e, on_intent, on_deleted)
                except Refused as exc:
                    # 删除中途被自身安全判定中止：条目状态必须显式记为 FAILED
                    rec.update({"status": STATUS_FAILED, "at": now(), "error": str(exc)[:300]})
                    receipt["status"] = "FAILED"
                    flush_best_effort()
                    raise
                except Exception as exc:  # noqa: BLE001
                    rec.update({"status": STATUS_FAILED, "at": now(), "error": repr(exc)[:300]})
                    receipt["status"] = "FAILED"
                    flush_best_effort()
                    raise Refused(f"删除失败，已停止且不自动重试: {rel} :: {exc}") from exc

            receipt["status"] = "COMPLETED"
            receipt["finished_at"] = now()
            receipt["deleted_count"] = sum(1 for v in results.values()
                                           if v["status"] == STATUS_DELETED)
            flush()
            print(f"\nEXECUTED execution_id={execution_id} receipt={rpath}")
            print(f"deleted={receipt['deleted_count']} status={receipt['status']}")
            return 0
        finally:
            os.close(lock_fd)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR(fail closed): {exc!r}", file=sys.stderr)
        return 4


def main() -> int:
    ap = argparse.ArgumentParser(description=f"prune_execute ({EXECUTOR_VERSION})")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--plan-sha256", required=True, help="主计划完整 SHA256（64 hex）")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--approval", default=None, help="独立批准回执路径（--execute 必填）")
    ap.add_argument("--approval-sha256", default=None, help="批准回执完整 SHA256")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--receipt", default=None)
    ap.add_argument("--receipt-sha256", default=None)
    args = ap.parse_args()
    if len(args.plan_sha256) != 64:
        print("REFUSED: --plan-sha256 必须是完整 64 位十六进制", file=sys.stderr)
        return 3
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
