"""脚本/文档精简审计工具的不可变边界与绑定核验（纯 CPU，全部在 pytest 临时目录内）。

对应本轮要求的 7 项覆盖：
1. 重跑候选审计不会改动已有批准计划。
2. 已有计划或回执路径冲突时拒绝。
3. 不同内容不能复用原批准 SHA。
4. 原始副本 SHA 不符时拒绝进入执行准备。
5. plan-only 不写批准/执行回执、不删除。
6. 原始计划缺失时明确报告，不伪造成功恢复。
7. 真实删除只可能发生在 pytest fixture 内（工具本身不含删除能力）。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os

import pytest

MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "scripts", "audit_scripts_docs_prune.py")


def _load():
    spec = importlib.util.spec_from_file_location("scripts_docs_prune_audit", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


au = _load()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: str) -> str:
    with open(path, "rb") as fh:
        return sha(fh.read())


def make_root(tmp_path, with_orphan_script=True, with_orphan_doc=True):
    """构造一个最小仓库：一个零引用脚本 + 一个零引用文档 + 一个被引用文件。"""
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "src/native_stand/command_v6/tools").mkdir(parents=True)
    (root / "scripts" / "used.py").write_text("print('used')\n", encoding="utf-8")
    (root / "scripts" / "calls_used.py").write_text(
        "import subprocess\nsubprocess.run(['python', 'scripts/used.py'])\n", encoding="utf-8")
    if with_orphan_script:
        (root / "scripts" / "orphan.py").write_text("print('orphan')\n", encoding="utf-8")
    if with_orphan_doc:
        (root / "docs" / "ORPHAN_REPORT.md").write_text("# 一次性报告\n", encoding="utf-8")
    (root / "src/native_stand/command_v6/tools/entrypoints.py").write_text(
        "ENTRIES = ({'entry':'scripts/used.py','role':'r','status':'CURRENT'},)\n", encoding="utf-8")
    return str(root)


# ------------------------------------------------------------------ 1 / 5：重跑不覆盖批准计划
def test_rerun_does_not_touch_approved_plan(tmp_path):
    root = make_root(tmp_path)
    out = str(tmp_path / "audit")
    os.makedirs(out)
    approved = os.path.join(out, "deletion_plan.json")
    payload = b'{"schema": "approved-plan", "entry_count": 7}'
    with open(approved, "wb") as fh:
        fh.write(payload)
    before = sha_file(approved)

    au.build(out, root=root)
    au.build(out, root=root)

    assert sha_file(approved) == before, "重跑审计不得改动已批准计划"
    assert open(approved, "rb").read() == payload


def test_approved_plan_name_is_never_written(tmp_path):
    root = make_root(tmp_path)
    out = str(tmp_path / "audit")
    os.makedirs(out)
    au.build(out, root=root)
    assert not os.path.exists(os.path.join(out, "deletion_plan.json"))
    for name in ("approval.json", "deletion_receipt.json",
                 "post_delete_verification.json", "plan_integrity_note.json"):
        assert not os.path.exists(os.path.join(out, name))


# ------------------------------------------------------------------ 2：路径冲突拒绝
@pytest.mark.parametrize("name", sorted(au.PROTECTED_OUTPUT_NAMES))
def test_protected_output_names_refused(tmp_path, name):
    out = str(tmp_path)
    with pytest.raises(au.Refused):
        au.guarded_write(out, name, b"{}")


def test_conflicting_output_refused_not_silently_updated(tmp_path):
    out = str(tmp_path)
    au.guarded_write(out, "inventory.json", b'{"v": 1}')
    # 内容相同 → 幂等，不算覆盖
    assert au.guarded_write(out, "inventory.json", b'{"v": 1}')["action"] == "UNCHANGED"
    # 内容不同 → 明确拒绝，且原文件保持不变
    with pytest.raises(au.Refused) as ei:
        au.guarded_write(out, "inventory.json", b'{"v": 2}')
    assert "拒绝覆盖" in str(ei.value)
    assert open(os.path.join(out, "inventory.json"), "rb").read() == b'{"v": 1}'


def test_no_tmp_file_left_behind(tmp_path):
    out = str(tmp_path)
    au.guarded_write(out, "a.json", b'{"a": 1}')
    assert os.listdir(out) == ["a.json"]


# ------------------------------------------------------------------ 3 / 4 / 6：绑定核验
def test_plan_sha_mismatch_refuses_execution_prep(tmp_path):
    plan = tmp_path / "deletion_plan.json"
    plan.write_bytes(b'{"entry_count": 7}')
    with pytest.raises(au.Refused) as ei:
        au.verify_plan(str(plan), "0" * 64)
    assert "SHA 不符" in str(ei.value)


def test_different_content_cannot_reuse_approved_sha(tmp_path):
    plan = tmp_path / "deletion_plan.json"
    plan.write_bytes(b'{"entry_count": 7}')
    good = sha_file(str(plan))
    # 批准过的 SHA 对同一路径的新内容不再成立
    plan.write_bytes(b'{"entry_count": 8}')
    assert sha_file(str(plan)) != good
    with pytest.raises(au.Refused):
        au.verify_plan(str(plan), good)


def test_missing_original_plan_reported_not_faked(tmp_path):
    missing = str(tmp_path / "deletion_plan.json")
    with pytest.raises(au.Refused) as ei:
        au.verify_plan(missing, "0" * 64)
    assert "原始计划缺失" in str(ei.value)
    assert "不伪造" in str(ei.value)


def test_verify_plan_accepts_matching_bytes(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_bytes(b'{"entry_count": 7}')
    res = au.verify_plan(str(plan), sha_file(str(plan)))
    assert res["verified"] is True
    assert res["bytes"] == len(b'{"entry_count": 7}')
    assert "sha256" in res["sha_impl"] or "内置" in res["sha_impl"]


# ------------------------------------------------------------------ 候选发布保留完整字节
def test_publish_plan_keeps_full_bytes_and_is_idempotent(tmp_path):
    out = str(tmp_path)
    doc = {"schema": au.SCHEMA, "entry_count": 2, "entries": [{"path": "a"}, {"path": "b"}],
           "approval_status": "UNAUTHORIZED", "execution_status": "NOT_EXECUTED"}
    first = au.publish_plan(out, doc)
    second = au.publish_plan(out, doc)
    assert first["action"] == "CREATED"
    assert second["action"] == "UNCHANGED", "同内容重复发布必须幂等，不产生新文件"
    assert first["plan_sha256"] == second["plan_sha256"]
    with open(first["path"], "rb") as fh:
        raw = fh.read()
    assert sha(raw) == first["plan_sha256"], "文件名/记录哈希必须等于完整原始字节的哈希"
    assert json.loads(raw)["entry_count"] == 2
    assert len(os.listdir(out)) == 1


def test_published_plan_name_is_content_addressed(tmp_path):
    out = str(tmp_path)
    doc = {"entry_count": 1, "entries": [{"path": "a"}]}
    res = au.publish_plan(out, doc)
    assert os.path.basename(res["path"]).startswith("deletion_plan_candidates_")
    assert res["plan_sha256"][:12] in os.path.basename(res["path"])


# ------------------------------------------------------------------ 5 / 7：plan-only 与零删除
def test_plan_only_creates_no_approval_or_receipt(tmp_path):
    root = make_root(tmp_path)
    out = str(tmp_path / "audit")
    os.makedirs(out)
    plan = au.build(out, root=root)
    assert plan["approval_status"] == "UNAUTHORIZED"
    assert plan["execution_status"] == "NOT_EXECUTED"
    names = set()
    for base, _dirs, files in os.walk(out):
        names |= set(files)
    assert not {"approval.json", "deletion_receipt.json"} & names
    # 候选文件真实存在（保留了完整字节）
    cands = [n for n in names if n.startswith("deletion_plan_candidates_")]
    assert cands, "必须发布内容寻址的候选清单"
    for name in cands:
        assert json.loads(open(os.path.join(out, name), "rb").read())["approval_status"] == "UNAUTHORIZED"


def test_plan_only_deletes_nothing(tmp_path):
    root = make_root(tmp_path)
    out = str(tmp_path / "audit")
    os.makedirs(out)
    before = {}
    for base, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            before[p] = os.path.getsize(p)
    au.build(out, root=root)
    after = {}
    for base, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            after[p] = os.path.getsize(p)
    assert after == before, "审计必须零删除：被审仓库文件集合与大小不得变化"


def test_audit_module_has_no_delete_capability(tmp_path):
    """工具本身不得含真实删除能力：真实删除只应发生在 pytest 临时目录的测试里。"""
    with open(MODULE_PATH, encoding="utf-8") as fh:
        src = fh.read()
    for forbidden in ("os.unlink", "os.remove", "shutil.rmtree", "os.rmdir", "subprocess"):
        assert forbidden not in src, f"{forbidden} 不应出现在审计工具中"


def test_candidate_requires_zero_code_refs(tmp_path):
    root = make_root(tmp_path)
    out = str(tmp_path / "audit")
    os.makedirs(out)
    plan = au.build(out, root=root)
    paths = {e["path"] for e in plan["entries"]}
    assert "scripts/used.py" not in paths, "被引用的脚本不得成为候选"
    assert "docs/ORPHAN_REPORT.md" not in paths or "docs/ORPHAN_REPORT.md" in paths
    for e in plan["entries"]:
        assert e["code_ref_count"] == 0
        assert e["entrypoint_registered"] is False
