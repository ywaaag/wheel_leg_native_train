import copy
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from native_stand.command_v6.config import schedule,validate
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.tools.preflight import check
from native_stand.command_v6.tools.validate_ledger import validate as validate_ledger
from native_stand.command_v6.train import send_handshake
from native_stand.command_v6.domain.protocol import standing_gate
from native_stand.command_v6.monitor import reconcile

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def setup(tmp_path):
    spec=json.loads((ROOT.parents[2]/"configs/experiments/stand_plane.json").read_text())
    # This is a fresh CPU fixture, not a mutation of the historical experiment.
    import hashlib
    spec['colleague_config_sha256']=hashlib.sha256(Path(spec['colleague_config_path']).read_bytes()).hexdigest()
    path=tmp_path/"spec.json"
    path.write_text(json.dumps(spec))
    book=json.loads((ROOT.parents[2]/"configs/experiments/budget.json").read_text())
    book["authorization"]="AUTHORIZED"
    book["limits"]={"source_eval":2,"smoke":5,"formal":200,"evaluate":2,"play":2}
    book["used"]={name:0 for name in book["limits"]}
    book["attempts"]={}
    book["source_eval_wall_used_s"]=0.
    (tmp_path/"budget.json").write_text(json.dumps(book))
    return spec,path,tmp_path/"run"


def test_plan_only_pass_and_no_side_effect(setup):
    _,spec_path,run=setup
    before=spec_path.with_name("budget.json").read_bytes()
    result=check(spec_path,run,"source_eval")
    assert result["status"]=="PASS"
    assert result["simulation"]==result["ppo"]==result["files_written"]==0
    assert not run.exists()
    assert spec_path.with_name("budget.json").read_bytes()==before


def test_reserved_attempt_preflight_is_exact(setup):
    _,path,run=setup
    Ledger(path.with_name('budget.json')).reserve('owned','source_eval',run)
    assert check(path,run,'source_eval',attempt_id='owned')['status']=='PASS'
    assert check(path,run,'source_eval',attempt_id='other')['status']=='FAIL'


@pytest.mark.parametrize("mutation,expected",[
    (lambda s:s.pop("reward"),"missing reward"),
    (lambda s:s.__setitem__("source_sha256","0"*64),"source_checkpoint SHA differs"),
    (lambda s:s["evaluation"].__setitem__("light_every_updates",10),"too frequent"),
])
def test_preflight_rejects_bad_inputs(setup,mutation,expected):
    spec,path,run=setup
    mutation(spec)
    path.write_text(json.dumps(spec))
    assert expected in " ".join(check(path,run,"source_eval")["errors"])


def test_existing_output_and_occupied_budget(setup):
    _,path,run=setup
    run.mkdir()
    assert "output path already exists" in check(path,run,"source_eval")["errors"]
    run.rmdir()
    book=json.loads(path.with_name("budget.json").read_text())
    book["attempts"]["busy"]={"phase":"source_eval","output_dir":"/other","status":"RUNNING","updates":0}
    path.with_name("budget.json").write_text(json.dumps(book))
    assert "budget already occupied" in check(path,run,"source_eval")["errors"]


def test_phase_prerequisite_and_schedule(setup):
    spec,path,run=setup
    assert "preceding phase" in " ".join(check(path,run,"formal")["errors"])
    ev=spec["evaluation"]
    assert schedule(10,"formal",ev)=={"checkpoint":False,"light":False,"full":False}
    assert schedule(100,"formal",ev)=={"checkpoint":True,"light":True,"full":False}
    assert schedule(200,"formal",ev)=={"checkpoint":True,"light":True,"full":True}
    assert schedule(500,"formal",ev)=={"checkpoint":True,"light":True,"full":False}
    assert schedule(100,"source_eval",ev)=={"checkpoint":False,"light":False,"full":False}


def test_ledger_exact_attempt_charging_and_source_only(setup,tmp_path):
    _,path,run=setup
    ledger=Ledger(path.with_name("budget.json"))
    ledger.reserve("source","source_eval",run)
    with pytest.raises(ValueError,match="no PPO"):
        ledger.charge("source",run)
    ledger.finalize("source",run,"COMPLETED",exit_code=0)
    with pytest.raises(ValueError,match="already ended"):
        ledger.finalize("source",run,"COMPLETED")
    benchmark=tmp_path/"smoke"
    ledger.reserve("b1","smoke",benchmark)
    with pytest.raises(ValueError,match="identity"):
        ledger.charge("b1",tmp_path/"wrong")
    assert ledger.charge("b1",benchmark)==1
    ledger.finalize("b1",benchmark,"FAILED",exit_code=3)
    book=json.loads(path.with_name("budget.json").read_text())
    assert book["used"]["source_eval"]==1
    assert book["used"]["smoke"]==1
    assert book["attempts"]["source"]["updates"]==0
    assert book["attempts"]["b1"]["updates"]==1
    assert validate_ledger(book)["status"]=="PASS"


def test_source_only_completion_gate_and_exact_attempt_finalization(setup):
    spec,path,run=setup
    ledger=Ledger(path.with_name("budget.json"))
    ledger.reserve("source","source_eval",run)
    rows=[{"outcome":"completed","continuous_s":10.,"net_drift_m":.1,
           "max_excursion_m":.12,"closure_max_m":1e-4,
           "height_steady_mean_m":.363,"dual_contact_fraction":.95,
           "peak_tilt_rad":.05,"saturation_fraction":0.,
           "mean_abs_vx_error_mps":.01,"mean_abs_yaw_error_rad_s":.01} for _ in range(8)]
    assert standing_gate({"per_env":rows},spec["evaluation"])["accepted"]
    rows[0]["outcome"]="task_failure"
    failed=standing_gate({"per_env":rows},spec["evaluation"])
    assert not failed["accepted"] and "continuous" in failed["per_env"][0]["failed_checks"]
    rows[0]["outcome"]="completed"
    rows[0]["dual_contact_fraction"]=None
    failed=standing_gate({"per_env":rows},spec["evaluation"])
    assert not failed["accepted"] and "dual_contact_fraction" in failed["per_env"][0]["failed_checks"]
    ledger.finalize("source",run,"COMPLETED",exit_code=0)
    book=json.loads(path.with_name("budget.json").read_text())
    assert book["used"]["source_eval"]==1
    assert book["attempts"]["source"]["updates"]==0


def test_monitor_recovers_only_matching_orphan_attempt(setup,tmp_path):
    _,path,run=setup
    ledger=Ledger(path.with_name("budget.json"))
    ledger.reserve("source","source_eval",run)
    ledger.finalize("source",run,"COMPLETED",exit_code=0)
    orphan=tmp_path/"orphan"
    orphan.mkdir()
    ledger.reserve("b1","smoke",orphan)
    ledger.charge("b1",orphan)
    with pytest.raises(ValueError,match="identity"):
        reconcile(path.with_name("budget.json"),"b1",tmp_path/"other",124)
    result=reconcile(path.with_name("budget.json"),"b1",orphan,124)
    assert result["status"]=="TERMINATED"
    assert json.loads((orphan/"terminal_report.json").read_text())["actual_updates"]==1
    book=json.loads(path.with_name("budget.json").read_text())
    assert book["attempts"]["source"]["status"]=="COMPLETED"
    assert book["attempts"]["b1"]["status"]=="TERMINATED"
    assert validate_ledger(book)["status"]=="PASS"


def test_evaluation_and_play_charge_attempts_without_ppo(setup,tmp_path):
    _,path,run=setup
    ledger=Ledger(path.with_name("budget.json"))
    ledger.reserve("source","source_eval",run)
    ledger.finalize("source",run,"COMPLETED")
    for phase in ("evaluate","play"):
        output=tmp_path/f"{phase}.json"
        ledger.reserve(phase,phase,output)
        with pytest.raises(ValueError,match="no PPO"):
            ledger.charge(phase,output)
        ledger.finalize(phase,output,"COMPLETED")
    book=json.loads(path.with_name("budget.json").read_text())
    assert book["used"]["evaluate"]==book["used"]["play"]==1
    assert validate_ledger(book)["status"]=="PASS"


def test_closed_handshake_reader_does_not_fail_trainer():
    reader,writer=os.pipe()
    os.close(reader)
    try:
        assert send_handshake(writer,{"status":"RUNNING"}) is False
    finally:
        os.close(writer)
