"""CPU-only plan: reject bad configuration before Isaac, ledger or output writes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from native_stand.command_v6.config import PHASES, SIM_PHASES, schedule, validate


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            sha.update(block)
    return sha.hexdigest()


def classify_errors(errors):
    """Stable reason codes; budget availability is never training authorization."""
    if not errors:
        return 'OK', 'no action required'
    if any('process identity' in e for e in errors):
        return 'PROCESS_IDENTITY_MISMATCH','verify command, start time and exact attempt/output'
    if any('behavior gate failed' in e for e in errors):
        return 'BEHAVIOR_GATE_FAILED','review behavioral evidence; do not change identity or budget'
    if any('SHA' in e or 'identity' in e or 'names or shapes' in e for e in errors):
        return 'IDENTITY_ERROR', 'verify frozen input identities; preserve previous evidence'
    if any('budget exhausted' in e for e in errors):
        return 'BUDGET_EXHAUSTED', 'create a new explicitly authorized spec and ledger'
    if any('not been authorized' in e for e in errors):
        return 'AUTHORIZATION_MISSING', 'obtain explicit authorization for a new attempt'
    if any('budget already occupied' in e for e in errors):
        return 'UNSETTLED_ATTEMPT', 'read terminal evidence and reconcile the exact attempt'
    if any('missing' in e or 'pending' in e or 'preceding phase' in e for e in errors):
        return 'MISSING_EVIDENCE', 'complete or locate the required frozen evidence'
    return 'CONFIG_ERROR', 'correct the reported configuration error before submission'


def reusable_spec(evidence_path, current):
    """Only submission metadata may differ when reusing completed wiring evidence."""
    ignored = {'experiment', 'budget', 'artifacts', 'authorization',
               'authorization_note', 'phase_initialization'}
    previous = json.loads(Path(evidence_path).read_text())
    return ({key: value for key, value in previous.items() if key not in ignored} ==
            {key: value for key, value in current.items() if key not in ignored})


def check(spec_path, output_dir, phase="formal", ledger_path=None, attempt_id=None):
    errors = []
    spec_path = Path(spec_path)
    output_dir = Path(output_dir)
    try:
        spec = json.loads(spec_path.read_text())
    except (OSError,ValueError) as exc:
        return {"status":"FAIL","reason_code":"CONFIG_ERROR","action":"correct spec JSON",
                "errors":[f"spec JSON: {exc}"],"simulation":0,"ppo":0,"files_written":0}
    if spec.get("interface_version") in ("multiskill_student_v1","multiskill_mcu_v2"):
        from native_stand.students.requests import preflight
        return preflight(spec_path,output_dir,phase,attempt_id)
    errors.extend(validate(spec))
    publication=None
    try:
        from .experiment_preparation import verify_publication
        publication=verify_publication(spec_path,authorized=True)
    except (OSError,ValueError,KeyError) as exc:errors.append('publication integrity: '+str(exc))
    engineering_certificate=None
    if spec.get('engineering_recovery'):
        try:
            from .motion_recovery_certificate import validate as validate_recovery
            engineering_certificate=validate_recovery(spec,json.loads(spec_path.with_name('budget.json').read_text()))
            if phase!='formal':errors.append('engineering recovery is formal-only; no source/smoke budget')
            claims=Path(__file__).resolve().parents[4]/'configs/experiments/.engineering_recovery_submissions'
            claim=claims/(spec['engineering_recovery']['single_use_id']+'.json')
            if claim.exists():
                row=json.loads(claim.read_text())
                if not (attempt_id and row.get('attempt_id')==attempt_id and
                        Path(row.get('output','')).resolve()==output_dir.resolve() and
                        Path(row.get('ledger','')).resolve()==spec_path.with_name('budget.json').resolve()):
                    errors.append('engineering recovery certificate already reserved; no duplicate submission')
        except (OSError,ValueError,KeyError,TypeError) as exc:errors.append('engineering recovery: '+str(exc))
    source_certificate=None
    if spec.get('source_evidence_reference') and not spec.get('engineering_recovery'):
        from .source_evidence import check as check_source
        source_certificate=check_source(spec,spec['source_evidence_reference'])
        if source_certificate['status']!='REUSABLE':errors.append('source evidence reuse '+source_certificate['status'])
    effective = execution = None
    try:
        from native_stand.command_v6.domain.recipe import resolve
        from native_stand.command_v6.tools.execution_identity import identity
        _, effective = resolve(spec)
        execution = identity(spec)
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    if spec.get('task')=='recovery':
        config=spec['recovery']
        dependencies=[('pose_library','pose_library_sha256')]
        from native_stand.command_v6.domain.episode_result import requires_stand
        if requires_stand(config):
            dependencies+=[('stand_checkpoint','stand_sha256'),('stand_spec','stand_spec_sha256')]
        for name,sha_name in dependencies:
            if name not in config or sha_name not in config:
                errors.append('recovery '+name+' identity missing');continue
            path=Path(config[name])
            if not path.is_file() or digest(path)!=config[sha_name]:
                errors.append(f'recovery {name} identity differs')
        if config.get('stand_checkpoint') and Path(config['stand_checkpoint']).is_file():
            import torch
            checkpoint=torch.load(config['stand_checkpoint'],map_location='cpu',weights_only=False)
            if checkpoint['actor']['mlp.0.weight'].shape!=(256,150) or checkpoint.get('update')!=500:
                errors.append('Frozen STAND must be native 150D update500')
        standing=config.get('standing_task')
        if phase=='source_eval' and not standing:
            errors.append('Recovery source-only uses dedicated R0 probe, not random Recovery actor')
        if phase in ('smoke','formal'):
            gates=('geometry_definition_confirmed',) if standing else (
                'geometry_definition_confirmed','runtime_initialization_validated','handover_domain_validated')
            for gate in gates:
                if not config.get(gate):errors.append(f'recovery physical prerequisite pending: {gate}')
            reverse=config.get('curriculum',{})
            if reverse.get('automatic_upgrade'):
                library=json.loads(Path(config['pose_library']).read_text())
                for level in reverse['levels']:
                    for split in ('train','holdout'):
                        if not any(p['family']==level['pose_family'] and p['split']==split and p['offline_valid']
                                   and 'initial_root_height_m' in p and 'initial_chassis_clearance_m' in p for p in library['poses']):
                            errors.append(f"Missing reverse initialization family: {level['pose_family']}/{split}")
    if phase not in PHASES+SIM_PHASES:
        errors.append("unknown phase")
    if output_dir.exists():
        errors.append("output path already exists")
    source_required=spec.get('initialization','warmstart')!='random'
    for key, identity in (("source_checkpoint","source_sha256"),("asset_path","asset_sha256"),
                          ("asset_module_path","asset_module_sha256"),
                          ("colleague_config_path","colleague_config_sha256")):
        if key not in spec or identity not in spec or (key=='source_checkpoint' and not source_required):
            continue
        source = Path(spec[key])
        if not source.is_file():
            errors.append(f"{key} missing")
        elif digest(source) != spec[identity]:
            errors.append(f"{key} SHA differs")
    if spec.get("interpreter") != sys.executable:
        errors.append("interpreter differs from frozen spec")
    path = Path(ledger_path) if ledger_path else spec_path.with_name("budget.json")
    try:
        book = json.loads(path.read_text())
        if book.get("authorization")!="AUTHORIZED":
            errors.append("new simulation/PPO budget has not been authorized")
        if phase in book["limits"]:
            if book["used"][phase] >= book["limits"][phase]:
                errors.append("phase budget exhausted")
        if phase=="source_eval" and book.get("source_eval_wall_used_s",0) >= spec["budget"]["source_eval_wall_s"]:
            errors.append("source evaluation wall budget exhausted")
        reserved=book['attempts'].get(attempt_id) if attempt_id else None
        own=bool(reserved and reserved['output_dir']==str(output_dir.resolve()) and
                 reserved['phase']==phase and reserved['status']=='RUNNING')
        if any(row["status"]=="RUNNING" and not (own and key==attempt_id)
               for key,row in book["attempts"].items()):
            errors.append("budget already occupied")
        completed = {name for name in book["limits"] if any(
            row["phase"]==name and row["status"]=="COMPLETED"
            for row in book["attempts"].values())}
        if source_certificate and source_certificate['status']=='REUSABLE':completed.add('source_eval')
        if engineering_certificate:completed.add('source_eval')
        if phase=='formal':
            from native_stand.command_v6.wiring import completed_smoke
            completed.discard('smoke')
            if completed_smoke(book,spec):completed.add('smoke')
        if spec.get('recovery',{}).get('standing_task') and phase in ('smoke','formal'):
            baselines=[row for row in book['attempts'].values() if row['phase']=='source_eval' and row['status']=='COMPLETED']
            valid=bool(source_certificate and source_certificate['status']=='REUSABLE')
            for row in baselines:
                folder=Path(row['output_dir'])
                result_path=folder/'evaluation_source.json'
                manifest_path=folder/'manifest.json'
                if not result_path.is_file() or not manifest_path.is_file():continue
                result=json.loads(result_path.read_text());manifest=json.loads(manifest_path.read_text())
                evidence_spec = row.get('evidence_spec_path')
                same_spec = manifest.get('spec_sha256') == digest(spec_path)
                if evidence_spec:
                    same_spec = (Path(evidence_spec).is_file() and
                        digest(Path(evidence_spec)) == manifest.get('spec_sha256') and
                        reusable_spec(evidence_spec, spec))
                valid_rising=(bool(spec['recovery'].get('rising_task')) and
                    result.get('effective_protocol',{}).get('protocol_identity')==spec['recovery']['rising_task']['version'] and
                    result.get('effective_protocol',{}).get('recovery_deadline_s')==11.5 and
                    result.get('effective_protocol',{}).get('post_rise_hold_s')==10. and
                    len(result.get('per_env',[]))==8 and all(
                        p.get('initial_valid') and not p.get('runtime_fault') and
                        p.get('outcome') in ('success','task_failure') for p in result['per_env']))
                if valid_rising:
                    from native_stand.command_v6.domain.evidence import resolve_gate
                    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
                    valid_rising=resolve_gate(result,'recovery',expected_envs=8,
                        expected_protocol=protocol_for_spec(spec,spec['evaluation']['seconds']))['candidate_eligible']
                if spec.get('receiver_training'):
                    from native_stand.command_v6.domain.evidence import resolve_gate
                    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
                    valid_rising=(len(result.get('per_env',[]))==8 and
                        result.get('receiver_protocol')==spec['receiver_training']['protocol'] and
                        all(p.get('initial_valid') and not p.get('runtime_fault') for p in result['per_env']) and
                        resolve_gate(result,'recovery',expected_envs=8,expected_protocol=protocol_for_spec(spec,spec['evaluation']['seconds']))['candidate_eligible'])
                valid |= (same_spec and result.get('checkpoint_sha256')==spec['source_sha256'] and valid_rising)
                valid |= (not spec['recovery'].get('rising_task') and same_spec and
                    result.get('checkpoint_sha256')==spec['source_sha256'] and
                    all(result.get('success_protocol',{}).get('standing_protocol',{}).get(key)==value
                        for key,value in spec['recovery']['standing_task']['protocol'].items()) and
                    result.get('success_protocol',{}).get('continuous_seconds',0.)>=10. and
                    len(result.get('per_env',[]))==8 and all(
                        p.get('initial_valid') and p.get('continuous_window_completed') and
                        p.get('continuous_s',0.)>=10.-1e-3 and
                        not p.get('runtime_fault') for p in result['per_env']))
            if not valid:errors.append('standing source continuous10s baseline pending or invalid')
        recovery_ready=bool(spec.get('recovery',{}).get('runtime_initialization_validated'))
        completed_for_prereq=set(completed)
        prerequisites={"smoke":set() if spec.get('initialization')=='random' or recovery_ready or spec.get('retention',{}).get('enabled') else {"source_eval"},"formal":{"smoke"},
                       "evaluate":set(),"play":{"source_eval"}}
        if not prerequisites.get(phase,set()) <= completed_for_prereq:
            errors.append("preceding phase has not completed")
        if any(row["output_dir"]==str(output_dir.resolve()) and not (own and key==attempt_id)
               for key,row in book["attempts"].items()):
            errors.append("output already in ledger")
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append(f"ledger invalid: {exc}")
    if source_required and "source_checkpoint" in spec and Path(spec["source_checkpoint"]).is_file():
        import torch
        try:
            checkpoint = torch.load(spec["source_checkpoint"],map_location="cpu",weights_only=False)
            if checkpoint.get("update") != spec.get('source_update',200) or checkpoint.get("asset_sha256") != spec.get("source_asset_sha256", spec.get("asset_sha256")):
                errors.append("source checkpoint internal identity differs")
            if spec.get('source_spec_sha256') and checkpoint.get('spec_sha256')!=spec['source_spec_sha256']:
                errors.append('native source prior experiment identity differs')
            for model, output in (("actor",6),("critic",1)):
                state = checkpoint[model]
                expected = {"mlp.0.weight":(256,spec.get('source_input_dim',132)),"mlp.0.bias":(256,),
                            "mlp.2.weight":(128,256),"mlp.2.bias":(128,),
                            "mlp.4.weight":(64,128),"mlp.4.bias":(64,),
                            "mlp.6.weight":(output,64),"mlp.6.bias":(output,)}
                if model == "actor":
                    expected["distribution.std_param"] = (6,)
                if set(state) != set(expected) or any(tuple(state[name].shape)!=shape
                        for name,shape in expected.items() if name in state):
                    errors.append(f"{model} names or shapes differ")
            optimizer = checkpoint["optimizer"]
            groups = optimizer["param_groups"]
            ids = groups[0]["params"] if len(groups)==1 else []
            if len(ids)!=17 or set(ids)!=set(optimizer["state"]):
                errors.append("optimizer parameter groups or state count differ")
            elif any(set(optimizer["state"][pid]) < {"step","exp_avg","exp_avg_sq"}
                     for pid in ids):
                errors.append("optimizer moments incomplete")
        except (KeyError,ValueError,RuntimeError,TypeError) as exc:
            errors.append(f"checkpoint unreadable: {exc}")
    evaluation = spec.get("evaluation",{})
    plan = ({str(update):schedule(update,phase,evaluation)
             for update in (10,50,100,200,500)}
            if all(key in evaluation for key in ("checkpoint_every_updates",
                "light_every_updates","full_every_updates")) else {})
    authorization_errors=("new simulation/PPO budget has not been authorized",
                          "phase budget exhausted","source evaluation wall budget exhausted")
    from native_stand.command_v6.domain.execution_plan import smoke_plan
    try:wiring_plan=smoke_plan(spec)
    except (KeyError,ValueError,TypeError) as exc:
        errors.append('wiring smoke plan invalid: '+str(exc))
        wiring_plan={'status':'INVALID','error':str(exc)}
    if phase=='smoke' and wiring_plan.get('budget_sufficient') is False:
        errors.append('declared smoke budget cannot reach required event')
    from .storage_budget import check as storage_check
    storage=storage_check(spec,output_dir,phase)
    if storage['status']!='PASS':errors.append('insufficient output storage capacity')
    auth_only=bool(errors) and all(error in authorization_errors for error in errors)
    reason_code,action=classify_errors(errors)
    return {"status":"READY_NEEDS_AUTH" if auth_only else "PASS" if not errors else "FAIL",
            "reason_code":reason_code,"action":action,
            "cpu_valid":not errors or auth_only,"errors":errors,
            "phase":phase,"output_dir":str(output_dir),"spec_sha256":digest(spec_path),
            "source_sha256":spec.get("source_sha256"),"asset_sha256":spec.get("asset_sha256"),
            "engineering_recovery_certificate":{'status':engineering_certificate['status'],'sha256':spec['engineering_recovery']['sha256']} if engineering_certificate else None,"publication_integrity":publication,"source_evidence_certificate":source_certificate,"storage_budget":storage,"evaluation_plan":plan,"wiring_smoke_plan":wiring_plan,"effective_recipe":effective,"execution_identity":execution,
            "simulation":0,"ppo":0,"files_written":0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--phase",choices=PHASES+SIM_PHASES,default="formal")
    args = parser.parse_args()
    result = check(args.spec,args.output_dir,args.phase)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["status"] in ("PASS","READY_NEEDS_AUTH") else 2)


if __name__ == "__main__":
    main()
