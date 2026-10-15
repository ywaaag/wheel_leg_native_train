"""Shared smoke evidence validation; no fixed update number or evaluation filename."""
import hashlib
import json
import math
from pathlib import Path
from .domain.execution_plan import smoke_plan
from .domain.episode_summary import normalize as episode_summary


def smoke_certificate(folder, spec):
    if spec.get('student_training'):
        from native_stand.students.training_evidence import smoke_certificate as student_certificate
        return student_certificate(folder,spec)
    folder=Path(folder)
    errors=[]
    inputs={}
    def read(name):
        path=folder/name
        if not path.is_file():errors.append('missing '+name);return {}
        inputs[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        try:return json.loads(path.read_text())
        except (OSError,ValueError):errors.append('invalid '+name);return {}
    progress=read('progress.json')
    terminal=read('terminal_report.json')
    manifest=read('manifest.json')
    if spec.get('receiver_training'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            owners=[row.get('receiver_ownership',{}) for row in rows]
            masks=[row.get('actor_update_scope',{}) for row in rows]
            if not any(o.get('frozen_recovery',0)>0 and o.get('receiver',0)>0 and o.get('real_handoffs',0)>0 for o in owners):errors.append('receiver smoke real control handoff missing')
            if not any(o.get('receiver_episode_ends',0)>0 for o in owners):errors.append('receiver smoke episode end missing')
            if not masks or any(m.get('valid_actor_samples')!=o.get('receiver') for m,o in zip(masks,owners)) or not any(m.get('actor_optimizer_steps',0)>0 for m in masks):errors.append('receiver smoke masked optimizer missing/misaligned')
            inputs['receiver_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError,ValueError,TypeError):errors.append('receiver smoke ownership evidence missing')
    frozen_spec=read('source_snapshot/spec.json')
    if frozen_spec!=spec:errors.append('smoke frozen spec differs')
    if inputs.get('source_snapshot/spec.json')!=manifest.get('spec_sha256'):
        errors.append('smoke spec SHA differs')
    if progress.get('actual_updates')!=spec['budget']['smoke_updates']:
        errors.append('actual smoke update count differs')
    if terminal.get('actual_updates')!=progress.get('actual_updates'):
        errors.append('terminal/progress update conflict')
    if not progress.get('actor_parameters_changed'):errors.append('actor update unproven')
    if spec.get('recovery',{}).get('actor_update_scope'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            inputs['controlled_actor_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            audits=[r.get('actor_update_scope') for r in rows]
            if not audits or any(a is None for a in audits):errors.append('Controlled actor optimizer readback missing')
            elif not any(a['valid_actor_samples']>0 and a['actor_optimizer_steps']>0 for a in audits):errors.append('Controlled actor optimizer events missing')
            elif any(a['valid_actor_samples']+a['invalid_actor_samples']!=a['total_transitions'] for a in audits):errors.append('Actor mask accounting conflict')
        except (OSError,ValueError,KeyError,TypeError):errors.append('Controlled actor evidence missing')
    if spec.get('recovery',{}).get('drawback_guidance'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            inputs['drawback_guidance_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            audits=[r.get('task_metrics',{}).get('drawback_guidance_audit') for r in rows]
            if not audits or any(a is None for a in audits):errors.append('DrawBack guidance runtime readback missing')
            elif (not any(a['positive_samples']>0 for a in audits) or
                  any(a['failed_reward_violations'] or a['ineligible_reward_violations'] for a in audits)):
                errors.append('DrawBack guidance positive-event/mask certificate failed')
        except (OSError,ValueError,KeyError,TypeError):errors.append('DrawBack guidance evidence missing')
    if spec.get('recovery',{}).get('leg_center_auxiliary'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            inputs['leg_center_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            if not any(r.get('leg_center_auxiliary',{}).get('eligible_count',0)>0 and
                r.get('leg_center_auxiliary',{}).get('nonempty_applications',0)>0 and
                (r.get('leg_center_auxiliary',{}).get('first_step') or {}).get('weighted_aux_actor_norm',0)>0 for r in rows):
                errors.append('leg center smoke eligible nonzero gradient missing')
        except (OSError,ValueError,TypeError):errors.append('leg center smoke evidence missing')
    if spec.get('action_distribution'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            inputs['bounded_mean_policy_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            policies=[r.get('support_record_policy',{}) for r in rows if r.get('support_record_policy',{}).get('eligible_count',0)>0]
            proven=bool(policies) and all(len(p.get('abs_mean_normalized',[]))==2 and
                all(math.isfinite(v) and 0<=v<=1+1e-6 for v in p['abs_mean_normalized']) for p in policies)
            for channel in (0,1):
                proven=proven and any(len(p.get('sample_clip_fraction',[]))==2 and
                    math.isfinite(p['sample_clip_fraction'][channel]) and 0<=p['sample_clip_fraction'][channel]<1 for p in policies)
            if not proven:errors.append('bounded mean smoke actual eligible policy/exploration unproven')
        except (OSError,ValueError,KeyError,TypeError):errors.append('bounded mean smoke policy evidence missing')
    if spec.get('recovery',{}).get('support_record_reward'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            inputs['support_record_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            audits=[row.get('task_metrics',{}).get('support_record_audit') for row in rows]
            if not audits or any(a is None for a in audits):errors.append('support record baseline/reset audit missing')
            elif any(a.get(k,1)!=0 for a in audits for k in ('failed_step_reward_violations','ineligible_reward_violations','episode_budget_violations')):
                errors.append('support record reward budget/scope violations')
            elif not any(a.get('baseline_established_count',0)>0 and a.get('reset_count',0)>0 for a in audits):errors.append('support record baseline/reset events unproven')
            observed=[row.get('rollout',{}).get('weighted_mean',{}).get('support_record_progress') for row in rows]
            if not observed or any(value is None or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 for value in observed):
                errors.append('smoke support record reward readback missing or invalid')
            elif not any(value>0 for value in observed):
                errors.append('smoke support record positive progress event unproven')
        except (OSError,ValueError,KeyError):errors.append('smoke support record evidence missing')
    if spec.get('recovery',{}).get('wheel_mean_auxiliary'):
        path=folder/'metrics.jsonl'
        try:
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            inputs['mean_auxiliary_metrics_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            proven=any(row.get('wheel_mean_auxiliary',{}).get('eligible_count',0)>0 and
                row.get('wheel_mean_auxiliary',{}).get('nonempty_applications',0)>0 and
                (row.get('wheel_mean_auxiliary',{}).get('first_step') or {}).get('weighted_aux_actor_norm',0)>0
                for row in rows)
            if not proven:errors.append('smoke mean auxiliary eligible gradient unproven')
        except (OSError,ValueError,KeyError):errors.append('smoke mean auxiliary evidence missing')
    if terminal.get('failure') or terminal.get('status') not in ('COMPLETED','STOPPED_BOUNDED'):
        errors.append('smoke terminal failure')
    if manifest.get('source_sha256')!=spec.get('source_sha256'):
        errors.append('source identity differs')
    try:
        requirements=smoke_plan(spec)
    except (KeyError,ValueError,TypeError) as exc:
        errors.append('wiring smoke plan invalid: '+str(exc))
        requirements={}
    if requirements.get('budget_sufficient') is False:
        errors.append('smoke sampling budget cannot cover the required event')
    if requirements.get('required_event') is not None or requirements.get('required_groups'):
        metrics_path=folder/'metrics.jsonl'
        try:
            inputs['metrics.jsonl']=hashlib.sha256(metrics_path.read_bytes()).hexdigest()
            metrics=[json.loads(line) for line in metrics_path.read_text().splitlines()]
            if requirements['required_event']=='normal_timeout':
                count=sum(row.get('task_metrics',{}).get('training_episode',{}).get('normal_timeouts',0)
                          for row in metrics)
            elif requirements['required_event'] is not None:
                count=sum(episode_summary(row.get('rollout',{}).get('episodes',{}))['completed']
                          for row in metrics)
            else:count=0
            if requirements['required_event'] is not None and count<requirements['minimum_event_count']:
                errors.append('smoke did not observe the required '+requirements['required_event'])
            if requirements['required_event'] is not None and not any((row.get('rollout',{}).get('episodes',{}).get('max_duration_s') or 0)>=requirements['required_event_duration_s']-1e-4
                       for row in metrics):
                errors.append('smoke did not record a complete required-duration training episode')
            for group in requirements.get('required_groups',[]):
                observed=[episode_summary(item) for row in metrics
                          for item in (row.get('task_metrics') or {}).get('episodes_by_pose',[])
                          if item.get('family')==group['family'] and
                          ('pose_id' not in group or item.get('pose_id')==group['pose_id'])]
                eligible=[item for item in observed if (item.get('max_duration_s') or 0)>=group.get('minimum_duration_s',0.)]
                count=sum(item['completed'] for item in eligible)
                if group.get('require_runtime_initial_valid'):
                    # Max duration and validity must refer to the same episode set.
                    count=sum(item['completed'] for item in eligible
                              if item.get('runtime_initial_valid_episodes')==item['completed'])
                if count<group.get('minimum_completed',1):
                    errors.append('smoke task group evidence missing: '+group['family']+'/'+str(group.get('pose_id','*')))
        except (OSError,ValueError,TypeError):
            errors.append('required smoke event metrics missing or invalid')
    evaluations=[case.get('path') for row in progress.get('evaluations',[]) for case in row.get('cases',[]) if case.get('path')]
    if not evaluations:errors.append('no recorded smoke evaluation')
    for name in evaluations:
        if Path(name).name!=name:errors.append('invalid evaluation path');continue
        result=read(name)
        if result.get('outcome_counts',{}).get('runtime_fault',0):errors.append('evaluation runtime fault')
        if not result.get('per_env'):errors.append('evaluation evidence absent')
        if spec.get('evaluation',{}).get('scored_envs') and len(result.get('per_env',[]))!=spec['evaluation']['scored_envs']:
            errors.append('evaluation scored environment count differs')
        if spec.get('source_sha256') and spec.get('asset_sha256'):
            for field,expected in (('source_sha256',spec['source_sha256']),('asset_sha256',spec['asset_sha256']),
                                   ('spec_sha256',manifest.get('spec_sha256'))):
                if result.get(field)!=expected:errors.append('evaluation '+field+' differs')
            checkpoint=Path(result.get('checkpoint',''))
            if not checkpoint.is_file() or checkpoint.resolve().parent!=folder.resolve():
                errors.append('evaluation checkpoint missing or outside smoke run')
            else:
                inputs[str(checkpoint.name)]=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
                if result.get('checkpoint_sha256')!=inputs[str(checkpoint.name)]:errors.append('evaluation checkpoint SHA differs')
            from .domain.evidence import validate_effective_protocol
            try:validate_effective_protocol(result.get('effective_protocol',{}))
            except (KeyError,ValueError,TypeError):errors.append('evaluation effective protocol missing or invalid')
            rows=result.get('per_env',[])
            if any(row.get('outcome') not in ('completed','success','task_failure') or
                   not isinstance(row.get('continuous_s'),(int,float)) or row['continuous_s']<=0
                   for row in rows):errors.append('evaluation incomplete or malformed episode evidence')
            if len({row.get('env_id') for row in rows})!=len(rows):errors.append('evaluation duplicate environment identity')
    return {'schema_version':1,'status':'PASSED' if not errors else 'FAILED',
            'spec_sha256':manifest.get('spec_sha256'),
            'actual_updates':progress.get('actual_updates'),'source_sha256':spec.get('source_sha256'),
            'inputs':inputs,'errors':errors,'run':str(folder.resolve()),'smoke_plan':requirements}


def validate_persisted_certificate(folder, spec, *, certificate_path=None):
    folder=Path(folder)
    try:
        record=json.loads((Path(certificate_path) if certificate_path else folder/'wiring_certificate.json').read_text())
    except (OSError,ValueError):
        return {'status':'FAILED','errors':['persisted wiring certificate missing or invalid']}
    current=smoke_certificate(folder,spec)
    # Version-one records predate smoke_plan; their other identities remain strict.
    comparable=current if 'smoke_plan' in record else {key:value for key,value in current.items() if key!='smoke_plan'}
    if record!=comparable:
        return {**current,'status':'FAILED','errors':current['errors']+['persisted wiring certificate differs from evidence']}
    return current


def completed_smoke(book,spec):
    if spec.get('motion_training',{}).get('wiring_reuse'):
        try:
            from native_stand.students.motion_wiring_recovery import verify
            return verify(spec)['status']=='VERIFIED'
        except (OSError,ValueError,KeyError,TypeError):return False
    if spec.get('motion_training',{}).get('resume'):
        try:
            from native_stand.students.motion_training_requests import verify_continuation
            return verify_continuation(spec)
        except (OSError,ValueError,KeyError,TypeError):return False
    if spec.get('student_storage_resume'):
        try:
            from native_stand.students.storage_resume import verify
            verify(spec)
            return True
        except (OSError,ValueError,KeyError,TypeError):return False
    if spec.get('recovery_course',{}).get('resume'):
        try:
            from native_stand.students.course_requests import verify_continuation
            return verify_continuation(spec)
        except (OSError,ValueError,KeyError,TypeError):return False
    if spec.get('engineering_recovery'):
        try:
            from .tools.motion_recovery_certificate import validate
            validate(spec,book)
            return True  # Explicit recovered wiring, not an edited historical smoke certificate.
        except (OSError,ValueError,KeyError,TypeError):return False
    for row in book.get('attempts',{}).values():
        if row.get('phase')!='smoke' or row.get('status') not in ('COMPLETED','STOPPED_BOUNDED'):continue
        folder=Path(row['output_dir'])
        evidence_spec=spec
        if row.get('evidence_spec_path'):
            from .tools.preflight import reusable_spec,digest
            path=Path(row['evidence_spec_path'])
            if (not path.is_file() or digest(path)!=row.get('evidence_spec_sha256') or
                    not reusable_spec(path,spec)):
                continue
            evidence_spec=json.loads(path.read_text())
        certificate=row.get('evidence_certificate_path')
        if certificate:
            p=Path(certificate)
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row.get('evidence_certificate_sha256'):
                continue
        if validate_persisted_certificate(folder,evidence_spec,certificate_path=certificate)['status']=='PASSED':return True
    return False
