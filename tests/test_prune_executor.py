"""prune_execute 的 CPU 安全契约测试。

全部删除只发生在 pytest 的 tmp_path fixture 目录内；不触碰真实 run/checkpoint/spec/ledger。
不降低断言、不吞异常。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXECUTOR_PATH = os.path.join(PROJECT_ROOT, "scripts", "prune_execute.py")


def _load_executor():
    spec = importlib.util.spec_from_file_location("prune_execute", EXECUTOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ex = _load_executor()
REAL_SCAN = ex.scan_active_processes  # autouse fixture 会打补丁，这里保留真实函数


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    return sha256_file(path)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    return sha256_file(path)


class Fixture:
    """构造 plan 目录 + 受控项目根，并产出各输入文件及其 SHA。"""

    def __init__(self, tmp_path, candidate_specs=None, protected=None, approval="UNAUTHORIZED"):
        self.tmp = tmp_path
        self.root = os.path.join(tmp_path, "root")
        # plan 与各输入都放在项目根内的 audit/ 下：执行器只接受“项目根相对路径”绑定
        self.audit = os.path.join(self.root, "audit")
        os.makedirs(self.audit)

        # 受保护对象
        self.protected_file = "keep_model/model.pt"
        self.protected_dir = "keep_dir"
        write_text(os.path.join(self.root, self.protected_file), "PROTECTED-MODEL")
        write_text(os.path.join(self.root, self.protected_dir, "sub", "evidence.json"), "{}")

        # 候选
        self.candidates = candidate_specs or [
            ("runs/cand_a", {"f.bin": "A" * 2048, "sub/g.txt": "gg"}),
            ("runs/cand_b", {"h.bin": "B" * 1024}),
        ]
        for rel, files in self.candidates:
            for f, content in files.items():
                write_text(os.path.join(self.root, rel, f), content)

        protected = protected or {}
        self.keep = {
            "schema": "prune_keep_v1",
            "keep_version": "1",
            "root": self.root,
            "protected_paths": protected.get("protected_paths", [
                {"path": self.protected_dir, "reason": "protected dir"},
            ]),
            "protected_checkpoints": protected.get("protected_checkpoints", [
                {"path": self.protected_file, "sha256": sha256_file(os.path.join(self.root, self.protected_file)),
                 "reason": "protected model"},
            ]),
            "protected_onnx": protected.get("protected_onnx", []),
            "ancestor_minimal_package": protected.get("ancestor_minimal_package", []),
            "required_evidence": protected.get("required_evidence", []),
            "never_delete": protected.get("never_delete", []),
            "active_task_dependencies": protected.get("active_task_dependencies", []),
            "active_task_snapshot": {"checked_at": "TEST", "process_count": 0,
                                     "unresolved_cwd": 0, "referenced_paths": []},
            "evidence_identity": protected.get("evidence_identity", []),
            "reference_documents": protected.get("reference_documents", []),
        }
        self.protected_models = {"schema": "prune_protected_models_v1", "categories": {}}

        self.review = {"schema": "prune_review_entries_v1", "entries": []}
        self.entries = []
        for i, (rel, _files) in enumerate(self.candidates, start=1):
            ident = ex.build_manifest(self.root, rel)
            self.entries.append({"id": f"A{i:04d}", "path": rel, "type": ident["kind"],
                                 "actual_bytes": ident["actual_bytes"], "identity": ident})
        self.approval = approval

    def bind(self, executor_sha=None, entries_sha=None, keep_sha=None, plan_sha=None):
        self.keep_path = os.path.join(self.audit, "keep_manifest.json")
        self.pm_path = os.path.join(self.audit, "protected_models.json")
        self.entries_path = os.path.join(self.audit, "deletion_entries_A.json")
        self.review_path = os.path.join(self.audit, "review_entries_B.json")
        self.stub_path = os.path.join(self.audit, "executor_stub.py")

        keep_sha = write(self.keep_path, self.keep) if keep_sha is None else keep_sha
        pm_sha = write(self.pm_path, self.protected_models)
        entries_doc = {"schema": "prune_entries_v1", "root": self.root, "entries": self.entries}
        real_entries_sha = write(self.entries_path, entries_doc)
        review_sha = write(self.review_path, self.review)
        real_exec_sha = write_text(self.stub_path, "# executor stub\n")

        self.plan = {
            "schema": "prune_plan_v1",
            "plan_version": "1",
            "root": self.root,
            "generated_at": "TEST",
            "executor": {"path": "audit/executor_stub.py", "version": ex.EXECUTOR_VERSION,
                         "sha256": executor_sha or real_exec_sha},
            "inputs": {
                "keep_manifest": {"path": "audit/keep_manifest.json", "sha256": keep_sha},
                "protected_models": {"path": "audit/protected_models.json", "sha256": pm_sha},
                "entries": {"path": "audit/deletion_entries_A.json",
                            "sha256": entries_sha or real_entries_sha},
                "review_entries": {"path": "audit/review_entries_B.json", "sha256": review_sha},
            },
            "entry_count": len(self.entries),
            "plan_scope": "A",
            "approval_status": self.approval,
            "execution_status": "NOT_EXECUTED",
        }
        self.plan_path = os.path.join(self.audit, "deletion_plan_A.json")
        real_plan_sha = write(self.plan_path, self.plan)
        self.plan_sha = real_plan_sha if plan_sha is None else plan_sha

        # 独立批准回执（fixture 内的虚拟批准；真实计划不生成）
        self.approval_path = os.path.join(self.audit, "approval.json")
        self.approval_doc = {
            "schema": "prune_approval_v1",
            "approval_id": "fixture-approval",
            "approved_plan_sha256": self.plan_sha,
            "entries_sha256": self.plan["inputs"]["entries"]["sha256"],
            "keep_manifest_sha256": self.plan["inputs"]["keep_manifest"]["sha256"],
            "protected_models_sha256": self.plan["inputs"]["protected_models"]["sha256"],
            "executor_sha256": self.plan["executor"]["sha256"],
            "scope": "A",
            "entry_count": len(self.entries),
            "explicit_user_approval_text": "fixture approval for CPU tests only",
            "approved_at": "TEST",
        }
        self.approval_sha = write(self.approval_path, self.approval_doc)
        return self

    def args(self, execute=True, resume=False, receipt=None, approval="valid",
             approval_sha=None):
        if not execute or approval == "none":
            ap_path, ap_sha = None, None
        else:
            ap_path, ap_sha = self.approval_path, (approval_sha or self.approval_sha)
        return SimpleNamespace(plan=self.plan_path, plan_sha256=self.plan_sha,
                               execute=execute, resume=resume, receipt=receipt,
                               receipt_sha256=None,
                               approval=ap_path, approval_sha256=ap_sha)

    def exists(self, rel):
        return os.path.lexists(os.path.join(self.root, rel))


@pytest.fixture(autouse=True)
def idle_processes(monkeypatch):
    """默认：没有与本项目相关的活动进程。"""
    monkeypatch.setattr(ex, "scan_active_processes",
                        lambda root: {"count": 0, "processes": [], "unresolved_cwd": 0})


# ----------------------------------------------------------------- 基础：dry-run / 批准


def test_default_dryrun_deletes_nothing(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=False)) == 0
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")
    assert not os.path.exists(os.path.join(f.root, "artifacts", "prune_execution_receipts"))


def test_unapproved_plan_refused(tmp_path):
    """计划自身声明 UNAUTHORIZED 时不构成授权：没有批准回执即拒绝。"""
    f = Fixture(tmp_path, approval="UNAUTHORIZED").bind()
    assert ex.run(f.args(execute=True, approval="none")) == 3
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")


def test_approved_execute_deletes_only_listed(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=True)) == 0
    assert not f.exists("runs/cand_a")
    assert not f.exists("runs/cand_b")
    # 保护对象与必要记录仍在
    assert f.exists(f.protected_file)
    assert f.exists(os.path.join(f.protected_dir, "sub", "evidence.json"))


def test_receipt_written_outside_audit_dir(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    ex.run(f.args(execute=True))
    receipts = os.path.join(f.root, "artifacts", "prune_execution_receipts")
    files = [x for x in os.listdir(receipts) if x.endswith(".json")]
    assert len(files) == 1, files
    assert not os.path.exists(os.path.join(f.audit, "prune_execution_receipts"))
    doc = json.load(open(os.path.join(receipts, files[0])))
    assert doc["status"] == "COMPLETED"
    assert all(i["status"] == "DELETED" for i in doc["items"])


# ----------------------------------------------------------------- 契约绑定


def test_plan_sha_mismatch_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.plan_sha = "0" * 64
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_keep_manifest_sha_mismatch_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.plan["inputs"]["keep_manifest"]["sha256"] = "0" * 64
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_entries_sha_mismatch_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.plan["inputs"]["entries"]["sha256"] = "0" * 64
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_executor_sha_mismatch_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.plan["executor"]["sha256"] = "0" * 64
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_missing_keep_manifest_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    os.unlink(f.keep_path)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_executor_version_mismatch_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.plan["executor"]["version"] = "prune_execute_v0"
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3


# ----------------------------------------------------------------- 路径语义


@pytest.mark.parametrize("bad", [
    "/etc/passwd", "/", "~/.ssh", "../outside", "runs/../..", "runs/cand_a/../cand_b",
    "runs/*", "runs/cand?", "runs/[ab]", "", "  runs/cand_a  ", "runs//cand_a",
])
def test_bad_paths_refused(tmp_path, bad):
    with pytest.raises(ex.Refused):
        ex.normalize_parts(bad)


def test_root_and_hard_forbidden_refused():
    for rel in ["src", "src/native_stand", ".git", "tests", "assets", "configs", "docs",
                "scripts", "deployment_protocol"]:
        with pytest.raises(ex.Refused):
            ex.normalize_parts(rel)


def test_entry_with_dotdot_refused_end_to_end(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.entries.append({"id": "AX", "path": "runs/../keep_dir", "identity": {"kind": "dir"}})
    f.plan["entry_count"] = len(f.entries)
    write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
    f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_symlink_parent_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    outside = os.path.join(tmp_path, "outside")
    os.makedirs(outside)
    link = os.path.join(f.root, "runs", "linkdir")
    os.symlink(outside, link)
    with pytest.raises(ex.Refused) as ei:
        ex.resolve_entry(f.root, "runs/linkdir/victim")
    assert "symlink" in str(ei.value)


def test_symlink_body_deleted_without_following_target(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    outside = os.path.join(tmp_path, "outside")
    os.makedirs(outside)
    write_text(os.path.join(outside, "keepme.txt"), "outside-data")
    os.makedirs(os.path.join(f.root, "runs", "cand_link"))
    os.symlink(outside, os.path.join(f.root, "runs", "cand_link", "ptr"))
    f.candidates = [("runs/cand_link", {})]
    f.entries = []
    ident = ex.build_manifest(f.root, "runs/cand_link")
    f.entries = [{"id": "A0001", "path": "runs/cand_link", "type": "dir",
                  "actual_bytes": ident["actual_bytes"], "identity": ident}]
    f.bind()
    assert ex.run(f.args(execute=True)) == 0
    assert not os.path.lexists(os.path.join(f.root, "runs", "cand_link"))
    assert os.path.isfile(os.path.join(outside, "keepme.txt"))


# ----------------------------------------------------------------- 保护集合


def test_protected_file_entry_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.entries.append({"id": "AX", "path": f.protected_file,
                      "identity": ex.build_manifest(f.root, f.protected_file)})
    f.plan["entry_count"] = len(f.entries)
    write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
    f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists(f.protected_file)


def test_protected_dir_child_refused(tmp_path):
    for i, rel in enumerate(["keep_dir", "keep_dir/sub", "keep_dir/sub/evidence.json"]):
        f = Fixture(tmp_path / f"case{i}", approval="APPROVED").bind()
        f.entries.append({"id": "AX", "path": rel,
                          "identity": ex.build_manifest(f.root, rel)})
        f.plan["entry_count"] = len(f.entries)
        write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
        f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
        f.plan_sha = write(f.plan_path, f.plan)
        assert ex.run(f.args()) == 3, rel


def test_protected_path_ancestor_refused(tmp_path):
    """保护 keep_dir/sub/... 时，其祖先 runs 型目录不得整体删除。"""
    f = Fixture(tmp_path, approval="APPROVED", protected={
        "protected_paths": [{"path": "keep_dir/sub", "reason": "protected subtree"}],
    }).bind()
    f.entries.append({"id": "AX", "path": "keep_dir", "identity": {"kind": "dir"}})
    f.plan["entry_count"] = len(f.entries)
    write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
    f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists(os.path.join("keep_dir", "sub", "evidence.json"))


def test_b25_ancestor_checkpoint_in_candidate_refused(tmp_path):
    """A 目录含受保护 B25 checkpoint 时，该目录不得作为删除条目。"""
    f = Fixture(tmp_path, approval="APPROVED").bind()
    b25 = "runs/b25run/B/formal/model_update_25.pt"
    write_text(os.path.join(f.root, b25), "B25-WEIGHTS")
    f.keep["protected_checkpoints"].append(
        {"path": b25, "sha256": sha256_file(os.path.join(f.root, b25)), "reason": "B25 ancestor"})
    write(f.keep_path, f.keep)
    f.plan["inputs"]["keep_manifest"]["sha256"] = sha256_file(f.keep_path)
    f.plan_sha = write(f.plan_path, f.plan)
    # 覆盖该目录作为候选
    f.entries.append({"id": "AX", "path": "runs/b25run",
                      "identity": ex.build_manifest(f.root, "runs/b25run")})
    f.plan["entry_count"] = len(f.entries)
    write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
    f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists(b25)


def test_review_entries_are_protected(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.review["entries"] = [{"path": "runs/cand_b"}]
    write(f.review_path, f.review)
    f.plan["inputs"]["review_entries"]["sha256"] = sha256_file(f.review_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_b") and f.exists("runs/cand_a")


def test_duplicate_entries_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.entries.append(dict(f.entries[0]))
    f.plan["entry_count"] = len(f.entries)
    write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
    f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3


def test_parent_child_overlap_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    f.entries.append({"id": "AX", "path": "runs/cand_a/sub",
                      "identity": ex.build_manifest(f.root, "runs/cand_a/sub")})
    f.plan["entry_count"] = len(f.entries)
    write(f.entries_path, {"schema": "prune_entries_v1", "root": f.root, "entries": f.entries})
    f.plan["inputs"]["entries"]["sha256"] = sha256_file(f.entries_path)
    f.plan_sha = write(f.plan_path, f.plan)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


# ----------------------------------------------------------------- 身份变化


def test_dir_added_file_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    write_text(os.path.join(f.root, "runs/cand_a", "new_file.txt"), "NEW")
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_dir_removed_file_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    os.unlink(os.path.join(f.root, "runs/cand_a", "f.bin"))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_same_size_content_change_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    p = os.path.join(f.root, "runs/cand_b", "h.bin")
    before = os.path.getsize(p)
    write_text(p, "C" * before)
    assert os.path.getsize(p) == before
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_b")


def test_type_change_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    d = os.path.join(f.root, "runs/cand_b", "h.bin")
    os.unlink(d)
    os.makedirs(d)
    assert ex.run(f.args()) == 3


def test_symlink_change_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    os.makedirs(os.path.join(f.root, "runs", "cand_link"))
    os.symlink("/tmp/aaa", os.path.join(f.root, "runs", "cand_link", "ptr"))
    ident = ex.build_manifest(f.root, "runs/cand_link")
    f.entries = [{"id": "A0001", "path": "runs/cand_link", "type": "dir",
                  "actual_bytes": ident["actual_bytes"], "identity": ident}]
    f.bind()
    os.unlink(os.path.join(f.root, "runs", "cand_link", "ptr"))
    os.symlink("/tmp/bbb", os.path.join(f.root, "runs", "cand_link", "ptr"))
    assert ex.run(f.args()) == 3


def test_whole_batch_verified_before_any_delete(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    # 只破坏第二个条目
    os.unlink(os.path.join(f.root, "runs/cand_b", "h.bin"))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a"), "整批核验失败时不得删除任何条目"


# ----------------------------------------------------------------- 活动任务


def mkproc(root, pid, **kw):
    """构造与 scan_active_processes v2 同构的进程记录。"""
    root_real = os.path.realpath(root)
    cwd = kw.get("cwd")
    argv = kw.get("argv", [])
    cwd_parts = None
    if cwd:
        real = os.path.realpath(cwd)
        if real == root_real:
            cwd_parts = ()
        elif real.startswith(root_real + os.sep):
            try:
                cwd_parts = ex.parse_parts(os.path.relpath(real, root_real))
            except ex.Refused:
                cwd_parts = None
    refs = set(kw.get("refs", ()))
    for tok in argv:
        for parts in ex._looks_like_project_path(tok, root_real, [cwd or "."]):
            refs.add("/".join(parts))
    if cwd_parts:
        refs.add("/".join(cwd_parts))
    return {"pid": pid, "argv": argv, "cwd": cwd, "cwd_parts": cwd_parts,
            "kind": kw.get("kind", "task"), "specs": kw.get("specs", []),
            "refs": sorted(refs)}


def _scan(procs, **kw):
    return {"count": len(procs), "processes": procs,
            "unresolved_cwd": kw.get("unresolved_cwd", 0),
            "unresolved_spec": kw.get("unresolved_spec", 0),
            "unresolved_cmdline": kw.get("unresolved_cmdline", 0)}


def test_active_process_conflict_refused(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    monkeypatch.setattr(ex, "scan_active_processes", lambda root: _scan(
        [mkproc(f.root, "4242", argv=["python", "train.py", "--output-dir", "runs/cand_a"])]))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")


def test_active_process_cwd_inside_candidate_refused(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    inside = os.path.join(f.root, "runs/cand_a")
    monkeypatch.setattr(ex, "scan_active_processes", lambda root: _scan(
        [mkproc(f.root, "4243", argv=["python", "train.py"], cwd=inside)]))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_active_task_spec_referencing_candidate_refused(tmp_path, monkeypatch):
    """活动任务通过 spec 引用候选 checkpoint 时必须拒绝（v2 新增）。"""
    f = Fixture(tmp_path, approval="APPROVED").bind()
    cand_ckpt = os.path.join(f.root, "runs/cand_a", "f.bin")
    spec = os.path.join(f.root, "other_area", "spec.json")
    write(spec, {"source_checkpoint": os.path.relpath(cand_ckpt, f.root)})
    monkeypatch.setattr(ex, "scan_active_processes", lambda root: _scan(
        [mkproc(f.root, "4246", argv=["python", "-m", "native_stand.command_v6.train",
                                      "--spec", "other_area/spec.json"],
                cwd=os.path.join(f.root, "other_area"),
                refs=["runs/cand_a/f.bin"])]))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_conflicting_entries_end_to_end_from_spec_on_disk(tmp_path):
    """活动任务 spec 真实引用候选 checkpoint 时，conflicting_entries 必须命中该候选。"""
    root = os.path.join(tmp_path, "root")
    os.makedirs(os.path.join(root, "runs", "cand_a", "formal"))
    os.makedirs(os.path.join(root, "configs", "experiments", "live"))
    write_text(os.path.join(root, "runs", "cand_a", "formal", "model_update_50.pt"), "W")
    write_text(os.path.join(root, "configs", "experiments", "live", "spec.json"),
               json.dumps({"source_checkpoint": "runs/cand_a/formal/model_update_50.pt"}))
    root_real = os.path.realpath(root)
    spec = os.path.join(root_real, "configs", "experiments", "live", "spec.json")
    refs = ex.collect_spec_refs(spec, root_real, [root_real])
    proc = {"pid": "1", "argv": ["python", "stand_chain.py", "--spec",
                                 "configs/experiments/live/spec.json"],
            "cwd": root_real, "cwd_parts": (), "kind": "task",
            "specs": ["configs/experiments/live/spec.json"],
            "refs": sorted("/".join(r) for r in refs)}
    conf = ex.conflicting_entries({"processes": [proc]}, ["runs/cand_a"])
    assert "runs/cand_a" in conf
    assert any("model_update_50.pt" in r for r in conf["runs/cand_a"])
    # 与候选无交集时不得报冲突
    assert ex.conflicting_entries({"processes": [proc]}, ["runs/other"]) == {}


def test_spec_refs_parsed_from_real_spec_file(tmp_path):
    """spec 递归解析：相对路径按 spec 目录与项目根解析，只在配方 spec 白名单内递归。"""
    root = os.path.join(tmp_path, "root")
    os.makedirs(os.path.join(root, "runs", "cand_a"))
    os.makedirs(os.path.join(root, "configs", "experiments", "exp1"))
    write_text(os.path.join(root, "runs", "cand_a", "f.bin"), "X")
    write_text(os.path.join(root, "configs", "experiments", "exp1", "parent.json"),
               json.dumps({"source_checkpoint": "../../../runs/cand_a/f.bin"}))
    spec = os.path.join(root, "configs", "experiments", "exp1", "spec.json")
    write_text(spec, json.dumps({"source_parent_spec": "parent.json",
                                 "output_dir": "../../../runs/cand_a/"}))
    refs = ex.collect_spec_refs(spec, os.path.realpath(root), [os.path.realpath(root)])
    joined = {"/".join(r) for r in refs}
    assert "runs/cand_a" in joined
    assert "runs/cand_a/f.bin" in joined


def test_source_snapshot_is_not_followed(tmp_path):
    """不进入 run 内的 source_snapshot 历史副本，避免把历史祖先链误判为实时依赖。"""
    root = os.path.join(tmp_path, "root")
    os.makedirs(os.path.join(root, "runs", "oldrun", "formal", "source_snapshot"))
    os.makedirs(os.path.join(root, "configs", "experiments", "exp1"))
    write_text(os.path.join(root, "runs", "oldrun", "formal", "source_snapshot", "spec.json"),
               json.dumps({"source_checkpoint": "runs/historic_candidate/m.pt"}))
    os.makedirs(os.path.join(root, "runs", "historic_candidate"))
    write_text(os.path.join(root, "runs", "historic_candidate", "m.pt"), "W")
    spec = os.path.join(root, "configs", "experiments", "exp1", "spec.json")
    write_text(spec, json.dumps(
        {"source_parent_spec": "runs/oldrun/formal/source_snapshot/spec.json"}))
    refs = ex.collect_spec_refs(spec, os.path.realpath(root), [os.path.realpath(root)])
    joined = {"/".join(r) for r in refs}
    assert "runs/oldrun/formal/source_snapshot/spec.json" in joined
    assert "runs/historic_candidate/m.pt" not in joined, "不得递归进入 source_snapshot"


def test_labels_and_shas_are_not_treated_as_paths(tmp_path):
    """姿态标签、SHA 字符串等不得被误判为项目路径。"""
    root = os.path.join(tmp_path, "root")
    os.makedirs(os.path.join(root, "configs", "experiments", "exp1"))
    root_real = os.path.realpath(root)
    base = os.path.join(root_real, "configs", "experiments", "exp1")
    for value in ["guide_wheel_lower_left_01", "Capsule", "Cube", "a" * 64, "0.0.0.0", "6006"]:
        assert ex._looks_like_project_path(value, root_real, [base]) == [], value
    # 真实存在的路径仍必须被识别
    os.makedirs(os.path.join(root_real, "runs", "cand_a"))
    write_text(os.path.join(root_real, "runs", "cand_a", "m.pt"), "W")
    got = {"/".join(p) for p in ex._looks_like_project_path(
        "runs/cand_a/m.pt", root_real, [base])}
    assert got == {"runs/cand_a/m.pt"}


def test_spec_form_variants_and_spaces(tmp_path):
    """--spec=、python -m、位置参数、带空格路径都要正确提取。"""
    root = os.path.join(tmp_path, "root")
    root_real = os.path.realpath(root)
    for name in ("s.json", "sp ace.json", "pos.json"):
        write_text(os.path.join(root, "runs", "cand_a", name), "{}")
    a = ex._extract_spec_paths(["python", "train.py", "--spec=runs/cand_a/s.json"],
                               root_real, root_real)
    assert a == [os.path.join(root_real, "runs/cand_a/s.json")]
    b = ex._extract_spec_paths(["python", "-m", "native_stand.command_v6.train",
                                "--spec", "runs/cand_a/sp ace.json"], root_real, root_real)
    assert b == [os.path.join(root_real, "runs/cand_a/sp ace.json")]
    c = ex._extract_spec_paths(["python", "train.py", "runs/cand_a/pos.json"],
                               root_real, root_real)
    assert c == [os.path.join(root_real, "runs/cand_a/pos.json")]


def test_unreadable_spec_fails_closed(tmp_path):
    root = os.path.join(tmp_path, "root")
    os.makedirs(os.path.join(root, "runs", "cand_a"))
    bad = os.path.join(root, "runs", "cand_a", "spec.json")
    write_text(bad, "{not json")
    with pytest.raises(ex.Refused):
        ex.collect_spec_refs(bad, os.path.realpath(root), [os.path.realpath(root)])


def test_unresolved_spec_refused(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    monkeypatch.setattr(ex, "scan_active_processes",
                        lambda root: _scan([], unresolved_spec=1))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_unresolved_cwd_refused(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    monkeypatch.setattr(ex, "scan_active_processes", lambda root: _scan(
        [mkproc(f.root, "4244", argv=["python", "train.py"])], unresolved_cwd=1))
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a")


def test_process_scan_failure_fails_closed(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()

    def boom(root):
        raise ex.Refused("活动进程检查失败，fail closed: 无法列出 /proc")

    monkeypatch.setattr(ex, "scan_active_processes", boom)
    assert ex.run(f.args()) == 3
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")


def test_unrelated_active_task_allowed(tmp_path, monkeypatch):
    """项目根内运行的、与候选无交集的任务不阻塞；且不得被停止或修改。"""
    f = Fixture(tmp_path, approval="APPROVED").bind()
    other = os.path.join(f.root, "other_area")
    os.makedirs(other)
    with open(os.path.join(f.root, "other_area", "spec.json"), "w") as fh:
        json.dump({"output_dir": "other_area/out"}, fh)
    monkeypatch.setattr(ex, "scan_active_processes", lambda root: _scan(
        [mkproc(f.root, "4245", argv=["python", "-m", "native_stand.command_v6.train",
                                      "--spec", "other_area/spec.json"], cwd=other)]))
    assert ex.run(f.args(execute=True)) == 0
    assert not f.exists("runs/cand_a")
    assert os.path.isdir(other), "无关活动任务的工作目录不得被改动"


def test_real_scan_smoke_is_read_only(tmp_path):
    """真实 scan_active_processes 在真实项目根上可运行且不抛异常（只读 /proc）。"""
    res = REAL_SCAN(PROJECT_ROOT)
    assert set(res) == {"count", "processes", "unresolved_cwd", "unresolved_spec",
                        "unresolved_cmdline"}
    for p in res["processes"]:
        assert set(p) >= {"pid", "argv", "cwd", "cwd_parts", "kind", "refs", "specs"}


# ----------------------------------------------------------------- 中断与恢复


def test_partial_failure_recorded_and_stops(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    real_rmdir = ex.os.rmdir
    state = {"fail": True}

    def flaky(path):
        if path.endswith("cand_b") and state["fail"]:
            raise OSError("simulated rmdir failure")
        return real_rmdir(path)

    monkeypatch.setattr(ex.os, "rmdir", flaky)
    assert ex.run(f.args(execute=True)) == 3
    assert not f.exists("runs/cand_a")
    assert f.exists("runs/cand_b"), "失败的目录不得被部分遗留为不可恢复状态"
    rpath = _receipt_path(f)
    doc = json.load(open(rpath))
    assert doc["status"] == "FAILED"
    statuses = {i["path"]: i["status"] for i in doc["items"]}
    assert statuses["runs/cand_a"] == "DELETED"
    assert statuses["runs/cand_b"] == "FAILED"

    # 恢复：目录被部分删除（文件已删、目录未删）→ 必须能明确恢复并完成
    state["fail"] = False
    assert ex.run(f.args(execute=True, resume=True, receipt=rpath)) == 0
    assert not f.exists("runs/cand_b")
    doc = json.load(open(rpath))
    assert doc["status"] == "COMPLETED"
    assert {i["path"]: i["status"] for i in doc["items"]}["runs/cand_b"] == "DELETED"
    assert len({i["path"] for i in doc["items"]}) == 2, "恢复不得重复记账"


def test_resume_does_not_redelete_and_completes(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    real_rmdir = ex.os.rmdir
    state = {"fail": True}

    def flaky(path):
        if path.endswith("cand_b") and state["fail"]:
            raise OSError("simulated rmdir failure")
        return real_rmdir(path)

    monkeypatch.setattr(ex.os, "rmdir", flaky)
    assert ex.run(f.args(execute=True)) == 3
    rpath = _receipt_path(f)

    state["fail"] = False
    # 未使用 --resume：同一 execution_id 已有回执，必须拒绝
    assert ex.run(f.args(execute=True)) == 3
    # 使用原回执恢复
    assert ex.run(f.args(execute=True, resume=True, receipt=rpath)) == 0
    assert not f.exists("runs/cand_a") and not f.exists("runs/cand_b")
    doc = json.load(open(rpath))
    assert doc["status"] == "COMPLETED"
    statuses = [i["status"] for i in doc["items"]]
    assert statuses.count("DELETED") == 2
    assert f.exists(f.protected_file)


def test_resume_with_wrong_receipt_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    bogus = os.path.join(f.audit, "bogus_receipt.json")
    write(bogus, {"execution_id": "deadbeef"})
    assert ex.run(f.args(execute=True, resume=True, receipt=bogus)) == 3
    assert f.exists("runs/cand_a")


def test_missing_unexplained_stops_without_claiming_success(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    # 核验阶段放宽，模拟“核验后、删除前”外部删除
    monkeypatch.setattr(ex, "verify_entry_identity", lambda root, e: None)
    import shutil as _sh
    _sh.rmtree(os.path.join(f.root, "runs/cand_b"))
    assert ex.run(f.args(execute=True)) == 3
    assert not f.exists("runs/cand_a"), "在缺失条目之前已处理完成的条目应保持已删除"
    doc = json.load(open(_receipt_path(f)))
    assert doc["status"] == "RUNNING"
    statuses = {i["path"]: i["status"] for i in doc["items"]}
    assert statuses.get("runs/cand_b") == "MISSING_UNEXPLAINED"


# ----------------------------------------------------------------- 回收量核算


def test_reclaim_does_not_double_count_hardlinks(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    a = os.path.join(f.root, "runs/cand_a", "shared.bin")
    b = os.path.join(f.root, "runs/cand_b", "shared.bin")
    write_text(a, "X" * 4096)
    os.link(a, b)
    hl = ex.hardlink_shared_bytes(f.root, ["runs/cand_a", "runs/cand_b"])
    assert hl["hardlink_groups"] == 1
    assert hl["hardlink_shared_bytes"] > 0
    assert hl["net_reclaim_bytes"] == hl["total_actual_bytes"] - hl["hardlink_shared_bytes"]


def test_overlap_report_detects_nesting():
    entries = [{"path": "runs/a"}, {"path": "runs/a/sub"}, {"path": "runs/b"}]
    assert ex.overlap_report(entries) == [("runs/a", "runs/a/sub")]


def test_within_is_component_wise():
    assert ex.within(("runs", "ab"), ("runs", "a")) is False
    assert ex.within(("runs", "a", "x"), ("runs", "a")) is True
    assert ex.within(("runs", "a"), ("runs", "a")) is True


# ----------------------------------------------------------------- 保护的完整消费


def test_build_protected_consumes_every_section(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    keep = {
        "schema": "prune_keep_v1",
        "protected_paths": [{"path": "p1", "reason": "r"}],
        "protected_checkpoints": [{"path": "p2/m.pt", "reason": "r"}],
        "protected_onnx": [{"path": "p3/a.onnx"}],
        "ancestor_minimal_package": [{"path": "p4", "reason": "r"}],
        "required_evidence": [{"path": "p5/spec.json", "reason": "r"}],
        "never_delete": ["p6"],
        "active_task_dependencies": [{"path": "p7", "reason": "r"}],
    }
    protected, sources = ex.build_protected(keep, {"categories": {}}, ["p8/review"])
    for rel in ["p1", "p2/m.pt", "p3/a.onnx", "p4", "p5/spec.json", "p6", "p7", "p8/review"]:
        assert ex.parse_parts(rel) in protected, rel


def test_build_protected_rejects_partial_manifest(tmp_path):
    with pytest.raises(ex.Refused):
        ex.build_protected({"schema": "nope"}, {"categories": {}}, [])


# ----------------------------------------------------------------- dry-run 完整性（缺口1）


def test_dryrun_verifies_candidate_identity_and_fails(tmp_path, capsys):
    """dry-run 也必须拒绝同大小内容变化（v1 在核验前就返回了）。"""
    f = Fixture(tmp_path, approval="APPROVED").bind()
    p = os.path.join(f.root, "runs/cand_b", "h.bin")
    size = os.path.getsize(p)
    write_text(p, "Z" * size)
    assert os.path.getsize(p) == size
    assert ex.run(f.args(execute=False)) == 3
    err = capsys.readouterr().err
    assert "身份核验" in err and "runs/cand_b" in err
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")


def test_dryrun_reports_all_flags_when_clean(tmp_path, capsys):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=False)) == 0
    out = capsys.readouterr().out
    for flag in ("inputs_verified", "candidate_identity_verified",
                 "protected_evidence_verified", "activity_verified",
                 "deletions_performed"):
        assert flag in out, flag
    assert "deletions_performed       : 0" in out


def test_dryrun_does_not_create_receipt_dir(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=False)) == 0
    assert not os.path.exists(os.path.join(f.root, "artifacts", "prune_execution_receipts"))


def test_dryrun_rejects_tampered_protected_evidence(tmp_path):
    """保护证据（NPZ/ONNX/spec 等身份文件）SHA 变化必须让 dry-run 失败。"""
    for name, kind in (("evidence.traces.npz", "npz"), ("actor.onnx", "onnx"),
                       ("spec.json", "spec")):
        d = tmp_path / kind
        f = Fixture(d, approval="APPROVED")
        rel = f"keep_evidence/{name}"
        write_text(os.path.join(f.root, rel), "ORIGINAL")
        f.keep["evidence_identity"] = [{"path": rel,
                                        "sha256": sha256_file(os.path.join(f.root, rel))}]
        f.bind()
        # 篡改保护证据（同大小，避免仅靠 size 发现）
        write_text(os.path.join(f.root, rel), "TAMPERED")
        assert ex.run(f.args(execute=False)) == 3, name


def test_dryrun_rejects_missing_reference_document(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    f.keep["reference_documents"] = [{"path": "keep_dir/sub/evidence.json",
                                      "sha256": None}]
    f.bind()
    os.unlink(os.path.join(f.root, "keep_dir", "sub", "evidence.json"))
    assert ex.run(f.args(execute=False)) == 3


def test_reference_document_pointing_into_candidate_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    doc_rel = "keep_dir/sub/evidence.json"
    doc_abs = os.path.join(f.root, doc_rel)
    write_text(doc_abs, json.dumps({"raw_trace": "runs/cand_a/f.bin"}))
    f.keep["reference_documents"] = [{"path": doc_rel,
                                      "sha256": sha256_file(doc_abs)}]
    f.bind()
    assert ex.run(f.args(execute=False)) == 3
    assert f.exists("runs/cand_a")


# ----------------------------------------------------------------- 锁 / INTENT / 恢复（缺口3）


def _receipt_path(f):
    d = os.path.join(f.root, "artifacts", "prune_execution_receipts")
    files = [x for x in os.listdir(d) if x.endswith(".json")]
    assert len(files) == 1, files
    return os.path.join(d, files[0])


def test_global_lock_excludes_second_executor(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    fd = ex.acquire_lock(f.root)
    try:
        with pytest.raises(ex.Refused) as ei:
            ex.acquire_lock(f.root)
        assert "锁" in str(ei.value)
        # 第二个执行器必须拒绝，且不得删除任何东西
        assert ex.run(f.args(execute=True)) == 3
    finally:
        os.close(fd)
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")
    lock_path = os.path.join(f.root, "artifacts", "prune_execution_receipts", ".prune.lock")
    assert os.path.isfile(lock_path)


def test_intent_persist_failure_deletes_nothing(tmp_path, monkeypatch):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    calls = {"n": 0}
    real_save = ex.save_receipt

    def flaky(path, payload):
        calls["n"] += 1
        if calls["n"] >= 2:  # 第1次=RUNNING；第2次=第一个条目的 INTENT
            raise OSError("simulated receipt write failure")
        return real_save(path, payload)

    monkeypatch.setattr(ex, "save_receipt", flaky)
    assert ex.run(f.args(execute=True)) == 3
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b"), "INTENT 未落盘时不得删除"


def test_crash_after_delete_before_deleted_recorded(tmp_path, monkeypatch):
    """删除完成、DELETED 落盘前崩溃：INTENT 已记录，归属可判定，可明确恢复。"""
    f = Fixture(tmp_path, approval="APPROVED").bind()
    calls = {"n": 0}
    real_save = ex.save_receipt

    def flaky(path, payload):
        calls["n"] += 1
        if calls["n"] == 3:  # RUNNING=1, INTENT=2, DELETED=3
            raise OSError("simulated crash before DELETED persisted")
        return real_save(path, payload)

    monkeypatch.setattr(ex, "save_receipt", flaky)
    assert ex.run(f.args(execute=True)) == 3
    monkeypatch.setattr(ex, "save_receipt", real_save)

    rpath = _receipt_path(f)
    doc = json.load(open(rpath))
    statuses = {i["path"]: i["status"] for i in doc["items"]}
    assert statuses["runs/cand_a"] in ("INTENT", "FAILED")
    assert not f.exists("runs/cand_a")

    assert ex.run(f.args(execute=True, resume=True, receipt=rpath)) == 0
    doc = json.load(open(rpath))
    assert doc["status"] == "COMPLETED"
    assert not f.exists("runs/cand_a") and not f.exists("runs/cand_b")
    assert len({i["path"] for i in doc["items"]}) == 2


def test_deleted_target_reappearing_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=True)) == 0
    rpath = _receipt_path(f)
    # 把回执改回 RUNNING，模拟“已删除条目被外部重建后继续恢复”
    doc = json.load(open(rpath))
    doc["status"] = "RUNNING"
    ex.save_receipt(rpath, doc)
    write_text(os.path.join(f.root, "runs/cand_a", "f.bin"), "REAPPEARED")
    assert ex.run(f.args(execute=True, resume=True, receipt=rpath)) == 3
    assert f.exists("runs/cand_a"), "重新出现的目标不得被再次删除"


def test_completed_receipt_refuses_reexecution(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=True)) == 0
    rpath = _receipt_path(f)
    assert ex.run(f.args(execute=True, resume=True, receipt=rpath)) == 3
    assert ex.run(f.args(execute=True)) == 3


def test_receipt_must_live_in_receipt_dir(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    elsewhere = os.path.join(f.audit, "fake.json")
    write(elsewhere, {"schema": ex.SCHEMA_RECEIPT, "execution_id": "x"})
    assert ex.run(f.args(execute=True, resume=True, receipt=elsewhere)) == 3
    assert f.exists("runs/cand_a")


def test_tampered_receipt_digest_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=True)) == 0
    rpath = _receipt_path(f)
    doc = json.load(open(rpath))
    doc["items"] = []
    with open(rpath, "w") as fh:
        json.dump(doc, fh)
    assert ex.run(f.args(execute=True, resume=True, receipt=rpath)) == 3


# ----------------------------------------------------------------- 批准契约（三）


def test_execute_without_approval_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=True, approval="none")) == 3
    assert f.exists("runs/cand_a")


def test_unauthorized_real_plan_cannot_execute(tmp_path):
    """真实计划保持 UNAUTHORIZED / NOT_EXECUTED：批准必须来自独立回执。"""
    f = Fixture(tmp_path, approval="UNAUTHORIZED").bind()
    assert f.plan["approval_status"] == "UNAUTHORIZED"
    assert ex.run(f.args(execute=True, approval="none")) == 3
    assert f.exists("runs/cand_a") and f.exists("runs/cand_b")


@pytest.mark.parametrize("field", [
    "approved_plan_sha256", "entries_sha256", "keep_manifest_sha256",
    "protected_models_sha256", "executor_sha256", "scope", "entry_count",
])
def test_approval_binding_tamper_refused(tmp_path, field):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    doc = json.load(open(f.approval_path))
    doc[field] = "TAMPERED" if isinstance(doc[field], str) else 999
    f.approval_sha = write(f.approval_path, doc)
    assert ex.run(f.args(execute=True)) == 3
    assert f.exists("runs/cand_a")


def test_approval_sha_mismatch_refused(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED").bind()
    assert ex.run(f.args(execute=True, approval_sha="0" * 64)) == 3
    assert f.exists("runs/cand_a")


# ----------------------------------------------------------------- 执行完整性


def test_protected_models_and_evidence_intact_after_execute(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    ev_rel = "keep_evidence/model.sha"
    write_text(os.path.join(f.root, ev_rel), "EVIDENCE")
    f.keep["evidence_identity"] = [{"path": ev_rel,
                                    "sha256": sha256_file(os.path.join(f.root, ev_rel))}]
    f.bind()
    before = sha256_file(os.path.join(f.root, ev_rel))
    assert ex.run(f.args(execute=True)) == 0
    assert not f.exists("runs/cand_a") and not f.exists("runs/cand_b")
    assert os.path.isfile(os.path.join(f.root, f.protected_file))
    assert os.path.isfile(os.path.join(f.root, "keep_dir/sub/evidence.json"))
    assert sha256_file(os.path.join(f.root, ev_rel)) == before


def test_new_file_appearing_between_preflight_and_delete_refused(tmp_path, monkeypatch):
    """核验与删除之间的竞态：删除前出现冻结清单之外的文件必须中止。"""
    f = Fixture(tmp_path, approval="APPROVED").bind()
    real = ex.verify_entry_identity

    def add_then_verify(root, entry):
        real(root, entry)
        if entry["path"] == "runs/cand_a":
            write_text(os.path.join(root, "runs/cand_a", "intruder.txt"), "X")

    monkeypatch.setattr(ex, "verify_entry_identity", add_then_verify)
    assert ex.run(f.args(execute=True)) == 3
    doc = json.load(open(_receipt_path(f)))
    assert doc["status"] != "COMPLETED"


def test_hardlink_outside_batch_not_counted_as_reclaimable(tmp_path):
    f = Fixture(tmp_path, approval="APPROVED")
    a = os.path.join(f.root, "runs/cand_a", "shared.bin")
    outside = os.path.join(f.root, "keep_dir", "shared.bin")
    write_text(a, "X" * 4096)
    os.link(a, outside)
    hl = ex.hardlink_shared_bytes(f.root, ["runs/cand_a", "runs/cand_b"])
    assert hl["hardlink_outside_bytes"] > 0
    assert hl["net_reclaim_bytes"] == (hl["file_blocks"] + hl["dir_blocks"]
                                       - hl["hardlink_shared_bytes"]
                                       - hl["hardlink_outside_bytes"])
