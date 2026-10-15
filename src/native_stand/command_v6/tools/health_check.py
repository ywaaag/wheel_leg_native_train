"""Read-only project evidence/identity checks. Never imports Isaac or mutates a ledger."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess


def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()


def checkpoint_metadata(path):
    from .model_adapter import read
    try:return read(path).validate()
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        return {'status':'IDENTITY_ERROR','error':str(exc)}


def process_snapshot(pid):
    """Read one process, retaining only the GPU/session environment identity."""
    base=Path('/proc')/str(int(pid))
    argv=[value.decode() for value in base.joinpath('cmdline').read_bytes().split(b'\0') if value]
    stat=base.joinpath('stat').read_text().rsplit(')',1)[1].split()
    boot=float(next(line.split()[1] for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime ')))
    env={}
    try:
        for value in base.joinpath('environ').read_bytes().split(b'\0'):
            key,separator,item=value.partition(b'=')
            if separator and key in (b'CUDA_VISIBLE_DEVICES',b'HAPI_SESSION_ID'):
                env[key.decode()]=item.decode()
    except (OSError,UnicodeError):
        pass
    return {'pid':int(pid),'argv':argv,'command':' '.join(argv),
            'started_unix_s':boot+int(stat[19])/os.sysconf('SC_CLK_TCK'),'environment':env}


def argv_option(argv, name):
    """Reject ambiguous duplicate flags; support both standard CLI spellings."""
    values=[]
    for index,argument in enumerate(argv):
        if argument==name:
            values.append(argv[index+1] if index+1<len(argv) else None)
        elif argument.startswith(name+'='):
            values.append(argument[len(name)+1:])
    return values[0] if len(values)==1 else None


def process_identity(pid, *, output_dir, attempt_id, command_token=None, started_unix_s=None,
                     spec_path=None, physical_gpu=None, hapi_session=None):
    """A PID alone is never evidence of an active attempt (including PID reuse)."""
    try:
        snapshot=process_snapshot(pid)
    except (OSError,ValueError,TypeError,StopIteration,IndexError,UnicodeError):
        return {'status':'MISSING_EVIDENCE','reason':'process not present'}
    if not attempt_id or started_unix_s is None:
        return {**snapshot,'status':'MISSING_EVIDENCE','reason':'attempt/start identity not recorded'}
    argv=snapshot['argv']
    token_ok=(command_token is None or any(Path(value).name==command_token or
        value=='native_stand.command_v6.'+command_token.removesuffix('.py') for value in argv))
    checks={'output_dir':argv_option(argv,'--output-dir')==str(Path(output_dir).resolve()),
            'attempt_id':argv_option(argv,'--attempt-id')==str(attempt_id),
            'command_token':token_ok,
            'started_unix_s':abs(snapshot['started_unix_s']-float(started_unix_s))<2.}
    if spec_path is not None:checks['spec_path']=argv_option(argv,'--spec')==str(Path(spec_path).resolve())
    if physical_gpu is not None:
        checks['physical_gpu']=snapshot['environment'].get('CUDA_VISIBLE_DEVICES')==str(physical_gpu)
    if hapi_session is not None:
        checks['hapi_session']=argv_option(argv,'--hapi-session')==hapi_session
    return {**snapshot,'status':'OK' if all(checks.values()) else 'PROCESS_IDENTITY_MISMATCH',
            'checks':checks}


def own_process_start(pid):
    try:
        return process_snapshot(pid)['started_unix_s']
    except (OSError,ValueError,TypeError,IndexError,StopIteration,UnicodeError):return None


def submission_health(report, *, current_session, target_session,phase='source_eval',physical_gpu=None,resource_policy=None):
    from ..domain.resource_policy import resolve_resources,occupied_gpu_allowed
    policy=resource_policy or resolve_resources({})
    resolve_resources({'resources':{key:policy[key] for key in ('mode','sharing_authorized','authorization_note') if key in policy}})
    blocking=[row for row in report.get('findings',[]) if row['reason_code']!='BEHAVIOR_GATE_FAILED' and
              not (row['reason_code']=='BUDGET_EXHAUSTED' and row.get('detail')!=phase)]
    if not current_session or target_session!=current_session:
        blocking.append({'reason_code':'AUTHORIZATION_MISSING','detail':'HAPI target must match current HAPI_SESSION_ID'})
    if physical_gpu is not None:
        gpu=report.get('gpu') or {}
        if gpu.get('status')!='OK':
            blocking.append({'reason_code':'MISSING_EVIDENCE','detail':'physical GPU availability not verified'})
        else:
            devices=[row for row in gpu.get('devices',[]) if row['index']==physical_gpu]
            if len(devices)!=1:
                blocking.append({'reason_code':'CONFIG_ERROR','detail':'requested physical GPU missing'})
            elif any(row['gpu_uuid']==devices[0]['uuid'] for row in gpu.get('compute_processes',[])) and not occupied_gpu_allowed(policy):
                blocking.append({'reason_code':'RESOURCE_OCCUPIED','detail':'exclusive GPU occupied; explicit authorized shared mode required; no preemption'})
    if blocking:raise ValueError({'reason':'submission health prerequisite failed','findings':blocking})
    return {'resource_policy':policy,'physical_gpu':physical_gpu,'gpu_snapshot':report.get('gpu'),
            'sharing_used':occupied_gpu_allowed(policy),'preemption':False}


def gpu_snapshot():
    """One read-only inventory maps physical indices to GPU UUIDs and compute owners."""
    try:
        devices=subprocess.run(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],
            capture_output=True,text=True,timeout=10)
        processes=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,process_name,used_memory',
            '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
        if devices.returncode or processes.returncode:
            return {'status':'UNKNOWN','reason':devices.stderr or processes.stderr,
                    'exit_codes':[devices.returncode,processes.returncode]}
        return {'status':'OK','pressure_scope':'one instantaneous inventory; not a concurrency guarantee',
            'concurrency_advice':'Shared mode requires explicit approval; no automatic owner exemption or eviction. Compare available memory with the new task requirement.',
            'devices':[{'index':int(row[0]),'uuid':row[1].strip(),'name':row[2].strip(),
                'memory_total_mib':row[3].strip() if len(row)>3 else None,
                'memory_used_mib':row[4].strip() if len(row)>4 else None,
                'utilization_percent':row[5].strip() if len(row)>5 else None}
                for row in csv.reader(io.StringIO(devices.stdout)) if row],
            'compute_processes':[{'pid':int(row[0]),'gpu_uuid':row[1].strip(),
                'process_name':row[2].strip(),'used_memory_mib':row[3].strip()}
                for row in csv.reader(io.StringIO(processes.stdout)) if row]}
    except (OSError,subprocess.TimeoutExpired,ValueError,IndexError) as exc:
        return {'status':'UNKNOWN','reason':str(exc)}


def evaluation_task(result):
    return ('recovery' if result.get('task')=='recovery' else
        'capability' if 'capability_gate' in result else 'motion' if 'motion_gate' in result else 'standing')


def inspect_project(root, *, spec_path=None, run=None, include_processes=False, hapi_session=None):
    root=Path(root).resolve()
    findings=[]
    inputs={}
    checkpoint_info=None
    spec=None
    book=None
    evaluations={}
    process_checks=[]
    metadata_cache={}
    if spec_path is None and (root/'STATUS.md').is_file():
        links=re.findall(r'\]\((configs/experiments/[^)]+/spec\.json)\)',(root/'STATUS.md').read_text())
        if links:spec_path=root/links[0]
        else:findings.append({'reason_code':'MISSING_EVIDENCE','path':str(root/'STATUS.md'),'detail':'current spec link absent'})
    def issue(code,path,detail):findings.append({'reason_code':code,'path':str(path),'detail':detail})
    def read(path):
        path=Path(path)
        if not path.is_file():
            issue('MISSING_EVIDENCE',path,'file absent');return None
        inputs[str(path)]=digest(path)
        try:return json.loads(path.read_text())
        except (ValueError,OSError) as exc:issue('CONFIG_ERROR',path,str(exc));return None
    def local_path(path,base=root):
        path=Path(path)
        return path.resolve() if path.is_absolute() else (base/path).resolve()
    def metadata(path):
        key=str(path)
        if key not in metadata_cache:metadata_cache[key]=checkpoint_metadata(path)
        result=metadata_cache[key]
        if result.get('status')=='IDENTITY_ERROR':issue('IDENTITY_ERROR',path,result['error'])
        return result
    def check_metadata(path,*,update=None,spec_sha=None,asset_sha=None,input_dim=None,source_sha=None):
        info=metadata(path)
        for key,expected in (('update',update),('spec_sha256',spec_sha),
                             ('asset_sha256',asset_sha),('source_sha256',source_sha)):
            if expected is not None:
                if info.get(key) is None:issue('MISSING_EVIDENCE',path,'checkpoint internal '+key+' absent')
                elif info[key]!=expected:issue('IDENTITY_ERROR',path,'checkpoint internal '+key+' differs')
        if input_dim is not None:
            for key in ('actor_input_shape','critic_input_shape'):
                if not info.get(key) or info[key][-1]!=input_dim:
                    issue('IDENTITY_ERROR',path,'checkpoint internal '+key+' differs')
        return info
    for name in ('README.md','STATUS.md','TOOL_INDEX.md'):
        path=root/name
        if not path.exists():issue('MISSING_EVIDENCE',path,'entry document absent');continue
        inputs[str(path)]=digest(path)
        for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',path.read_text()):
            if '://' in target:continue
            destination=Path(target) if target.startswith('/') else root/target
            if not destination.exists():issue('MISSING_EVIDENCE',destination,f'broken link in {name}')
    if spec_path:
        spec_path=Path(spec_path).resolve()
        spec=read(spec_path)
        if spec:
            for field,sha_field in (('source_checkpoint','source_sha256'),('asset_path','asset_sha256')):
                if not spec.get(field) or not spec.get(sha_field):
                    issue('CONFIG_ERROR',spec_path,field+'/'+sha_field+' absent');continue
                path=local_path(spec[field])
                if not path.is_file():issue('MISSING_EVIDENCE',path,field)
                elif digest(path)!=spec[sha_field]:issue('IDENTITY_ERROR',path,sha_field)
            source=local_path(spec.get('source_checkpoint',''))
            if source.is_file():
                if spec.get('interface_version') in ('multiskill_student_v1','multiskill_mcu_v2'):
                    checkpoint_info=metadata(source)
                    if checkpoint_info.get('interface_version')!=spec['interface_version'] or checkpoint_info.get('actor_input_shape')!=([128,31] if spec['interface_version']=='multiskill_mcu_v2' else [256,1182]) or (checkpoint_info.get('critic_input_shape') is not None and checkpoint_info.get('critic_input_shape')!=([256,49 if checkpoint_info.get('critic_privileged_version') in ('standing_privileged49_v1','motion_privileged49_v1') else 40] if spec['interface_version']=='multiskill_mcu_v2' else [256,1191])):
                        issue('IDENTITY_ERROR',source,'student interface/network internal identity differs')
                    from native_stand.students.model import load
                    try:
                        motion_training=spec.get('student_training',{}).get('version')=='student_motion31_training_v1'
                        role='MotionZeroStudent' if spec.get('student_motion_validation') or motion_training else 'RecoveryStudent'
                        actor,student=load(source,role)
                        dataset_role=role
                        successor=spec.get('motion_training',{}).get('successor')
                        confirmation=spec.get('motion_confirmation')
                        if spec.get('student_motion_validation') or (motion_training and not spec['motion_training']['resume'] and not successor and not confirmation and not spec.get('motion_course')):
                            from native_stand.students.motion_transfer import transfer_actor
                            import torch
                            migration=student.get('migration',{})
                            if migration.get('version')!='recovery_to_motion_actor_column_transfer_v1' or not migration.get('initialization_only'):
                                raise ValueError('explicit migrated Motion initialization required')
                            origin=Path(migration['source_checkpoint']);parent=Path(migration['source_spec'])
                            if digest(origin)!=migration['source_sha256'] or digest(parent)!=migration['source_spec_sha256']:
                                raise ValueError('Motion transfer source identity differs')
                            teacher,origin_data=load(origin,'RecoveryStudent')
                            expected=transfer_actor(teacher)
                            if any(not torch.equal(v,expected.state_dict()[k]) for k,v in actor.state_dict().items()):
                                raise ValueError('Motion migrated Actor differs from exact declared transfer')
                            if student['dataset_sha256']!=origin_data['dataset_sha256'] or student['manifest_sha256']!=origin_data['manifest_sha256']:
                                raise ValueError('Motion inherited teacher provenance differs')
                            dataset_role='RecoveryStudent'
                        elif motion_training:
                            if spec.get('motion_advantage_probe'):
                                from native_stand.students.motion_advantage_probe import validate as validate_probe
                                validate_probe(spec)
                            elif spec.get('motion_course'):
                                from native_stand.students.motion_course_requests import verify
                                verify(spec)
                            elif confirmation:
                                from native_stand.students.motion_confirmation import verify
                                verify(spec)
                            elif successor:
                                from native_stand.students.motion_successor import verify
                                verify(spec)
                            else:
                                from native_stand.students.motion_training_requests import verify_continuation
                                verify_continuation(spec)
                            dataset_role='RecoveryStudent'
                        dependencies=spec['student_dependencies']
                        if successor:
                            # Parent spec SHA is verified above; inherit provenance by
                            # reference, without copying the legacy dependency graph.
                            parent=json.loads(Path(successor['parent_spec']).read_text())
                            dependencies={**parent['student_dependencies'],**dependencies}
                        manifests=[Path(p) for p,h in dependencies.items() if h==student['manifest_sha256']]
                        if len(manifests)!=1 or digest(manifests[0])!=student['manifest_sha256']:
                            raise ValueError('student teacher manifest binding differs')
                        manifest=json.loads(manifests[0].read_text())
                        datasets=[row for role,row in manifest.items() if role==dataset_role]
                        if len(datasets)!=1 or datasets[0]['sha256']!=student['dataset_sha256']:
                            raise ValueError('student dataset identity differs')
                        episodes=[e for e in manifest['episodes'] if e['role']==dataset_role]
                        if not episodes or any(e['asset_sha256']!=spec['asset_sha256'] for e in episodes):
                            raise ValueError('student teacher data asset provenance differs')
                    except (OSError,ValueError,KeyError,TypeError) as exc:issue('IDENTITY_ERROR',source,str(exc))
                else:
                    checkpoint_info=check_metadata(source,update=spec.get('source_update'),
                        spec_sha=spec.get('source_spec_sha256'),input_dim=spec.get('source_input_dim'),
                        asset_sha=spec.get('source_asset_sha256',spec.get('asset_sha256')))
            from native_stand.command_v6.domain.submission_contract import authorization
            try:
                configured_session=authorization(spec).get('hapi_session')
            except ValueError as exc:
                configured_session=None
                issue('CONFIG_ERROR',spec_path,str(exc))
            if hapi_session is not None and configured_session not in (None,hapi_session):
                issue('AUTHORIZATION_MISSING',spec_path,'configured HAPI target is not current session')
            book=read(spec_path.with_name('budget.json'))
            if book:
                if hapi_session is not None and book.get('hapi_session') not in (None,hapi_session):
                    issue('AUTHORIZATION_MISSING',spec_path.with_name('budget.json'),'ledger HAPI target is not current session')
                for attempt,row in book.get('attempts',{}).items():
                    if row.get('status') in ('RUNNING','UNKNOWN') or not row.get('status'):
                        issue('UNSETTLED_ATTEMPT',row.get('output_dir',''),str(row.get('status'))+' '+attempt)
                if book.get('authorization')!='AUTHORIZED':issue('AUTHORIZATION_MISSING',spec_path,'no explicit budget authorization')
                for phase,limit in book.get('limits',{}).items():
                    if limit>0 and book.get('used',{}).get(phase,0)>=limit:issue('BUDGET_EXHAUSTED',spec_path,phase)
                if run is None and book.get('attempts'):
                    directory_attempts=[row for row in book['attempts'].values()
                        if row.get('phase') not in ('evaluate','play')]
                    if directory_attempts:
                        latest=max(directory_attempts,key=lambda row:row.get('started_unix_s',0))
                        run=latest.get('output_dir')
                # Standalone evaluator output is a JSON file, not a trainer run directory.
                for attempt,row in book.get('attempts',{}).items():
                    if row.get('phase')!='evaluate':continue
                    path=local_path(row.get('output_dir',''))
                    result=read(path)
                    if not result:continue
                    from ..domain.evidence import resolve_gate
                    normalized=resolve_gate(result,evaluation_task(result),
                        expected_envs=spec.get('evaluation',{}).get('scored_envs'))
                    if normalized['status']=='FAILED':issue('BEHAVIOR_GATE_FAILED',path,'standalone evaluation did not pass')
                    elif normalized['status'] not in ('PASSED','NOT_RUN'):
                        issue('MISSING_EVIDENCE' if normalized['status']=='MISSING_EVIDENCE' else 'IDENTITY_ERROR',path,normalized['status'])
                    terminal_path=path.with_name(path.stem+'.terminal.json')
                    finished=read(terminal_path)
                    if finished and finished.get('attempt_id')!=attempt:
                        issue('IDENTITY_ERROR',terminal_path,'standalone evaluation attempt differs')
                    if finished and finished.get('status')!=row.get('status'):
                        issue('IDENTITY_ERROR',terminal_path,'standalone evaluation ledger/terminal conflict')
    if run:
        run=Path(run).resolve()
        manifest=read(run/'manifest.json')
        progress=read(run/'progress.json')
        is_running=(progress or {}).get('status')=='RUNNING'
        terminal=read(run/'terminal_report.json') if not is_running or (run/'terminal_report.json').is_file() else None
        if manifest and progress:
            if manifest.get('attempt_id')!=progress.get('attempt_id'):
                issue('IDENTITY_ERROR',run,'manifest/progress attempt mismatch')
            expected_spec_sha=digest(spec_path) if spec else None
            imported=(book or {}).get('attempts',{}).get(manifest.get('attempt_id'),{})
            if spec and imported.get('evidence_spec_path'):
                from .preflight import reusable_spec
                evidence_path=Path(imported['evidence_spec_path'])
                if (evidence_path.is_file() and
                        digest(evidence_path)==imported.get('evidence_spec_sha256') and
                        reusable_spec(evidence_path,spec)):
                    expected_spec_sha=digest(evidence_path)
            if spec and manifest.get('spec_sha256')!=expected_spec_sha:
                issue('IDENTITY_ERROR',run,'manifest/current spec SHA mismatch')
        if book and manifest:
            attempt=book.get('attempts',{}).get(manifest.get('attempt_id'))
            if attempt is None:issue('MISSING_EVIDENCE',run,'manifest attempt absent from ledger')
            else:
                if local_path(attempt.get('output_dir',''))!=run:issue('IDENTITY_ERROR',run,'ledger output differs')
                if progress and attempt.get('updates')!=progress.get('actual_updates'):
                    issue('IDENTITY_ERROR',run,'ledger/progress update mismatch')
                if terminal and attempt.get('status')!=terminal.get('status'):
                    issue('IDENTITY_ERROR',run,'ledger/terminal status mismatch')
        if manifest and progress and terminal:
            for key in ('actual_updates','samples','attempt_id','status'):
                if key in terminal and key in progress and terminal[key]!=progress[key]:
                    issue('IDENTITY_ERROR',run,'progress/terminal '+key+' mismatch')
            snapshot=run/'source_snapshot/spec.json'
            if snapshot.is_file() and digest(snapshot)!=manifest.get('spec_sha256'):
                issue('IDENTITY_ERROR',snapshot,'manifest spec SHA mismatch')
            if terminal.get('exit_code',0) and terminal.get('status')=='COMPLETED':
                issue('IDENTITY_ERROR',run,'terminal exit/status conflict')
        from ..domain.evidence import resolve_gate
        for path in sorted(run.glob('evaluation*.json')):
            evaluation=read(path)
            if evaluation is None:continue
            evaluations[str(path.resolve())]=evaluation
            task=evaluation_task(evaluation)
            expected_envs=(spec or {}).get('evaluation',{}).get('scored_envs')
            gate=resolve_gate(evaluation,task,expected_envs=expected_envs)
            if manifest and evaluation.get('spec_sha256') not in (None,manifest.get('spec_sha256')):
                issue('IDENTITY_ERROR',path,'evaluation/manifest spec SHA conflict')
            if gate['status']=='FAILED':issue('BEHAVIOR_GATE_FAILED',path,'completed evaluation did not pass')
            elif gate['status'] not in ('PASSED','NOT_RUN'):issue('MISSING_EVIDENCE' if gate['status']=='MISSING_EVIDENCE' else 'IDENTITY_ERROR',path,gate['status'])
        for milestone in (progress or {}).get('evaluations',[]):
            for case in milestone.get('cases',[milestone] if milestone.get('path') else []):
                if not case.get('path'):continue
                path=run/case['path'];raw=read(path)
                if raw and case.get('gate_evidence'):
                    task=evaluation_task(raw)
                    if case['gate_evidence'].get('raw_gate')!=raw.get(task+'_gate'):
                        issue('IDENTITY_ERROR',path,'progress/raw gate conflict')
                if raw:
                    for key in ('standing_gate','recovery_gate','capability_gate','motion_gate'):
                        if key in case and case[key]!=raw.get(key):issue('IDENTITY_ERROR',path,'progress/raw '+key+' conflict')
                    if case.get('effective_protocol') and case['effective_protocol']!=raw.get('effective_protocol'):
                        issue('IDENTITY_ERROR',path,'progress/raw protocol conflict')
        report_path=run/'analysis.json'
        if report_path.is_file():
            analysis=read(report_path)
            if analysis and terminal:
                for key in ('status','actual_updates','samples','exit_code'):
                    if key in analysis and key in terminal and analysis[key]!=terminal[key]:
                        issue('IDENTITY_ERROR',report_path,'analysis/terminal '+key+' conflict')
                if analysis.get('terminal_exit_conflict') or analysis.get('accounting_conflict'):
                    issue('IDENTITY_ERROR',report_path,'report declares accounting/exit conflict')
        completion_report=run/'completion_report.md'
        if not is_running:
            if not completion_report.is_file():issue('MISSING_EVIDENCE',completion_report,'completion report absent')
            elif terminal:
                inputs[str(completion_report)]=digest(completion_report)
                text=completion_report.read_text()
                declared=re.findall(r'(?:Terminal|Status):\s*([A-Z_]+)',text)
                if declared and any(value!=terminal.get('status') for value in declared):
                    issue('IDENTITY_ERROR',completion_report,'Markdown/terminal status conflict')
            ready=run/'report_ready.json'
            if ready.is_file():
                ready_data=read(ready)
                if ready_data and ready_data.get('report_sha256') and completion_report.is_file() and ready_data['report_sha256']!=digest(completion_report):
                    issue('IDENTITY_ERROR',ready,'report_ready/report SHA conflict')
        selection=read(run/'candidate_selection.json')
        if selection:
            if completion_report.is_file():
                verdicts=re.findall(r'^Best:.*; accepted=(True|False)\s*$',
                    completion_report.read_text(),flags=re.MULTILINE)
                if verdicts and any((value=='True')!=bool(selection.get('accepted_candidate')) for value in verdicts):
                    issue('IDENTITY_ERROR',completion_report,'Markdown/selection acceptance conflict')
            analysis=(read(report_path) if report_path.is_file() else None) or {}
            ref=analysis.get('candidate_selection_reference')
            if ref:
                selection_file=run/'candidate_selection.json'
                if (Path(ref.get('path','')).resolve()!=selection_file.resolve() or
                        not selection_file.is_file() or digest(selection_file)!=ref.get('sha256')):
                    issue('IDENTITY_ERROR',report_path,'analysis/selection reference conflict')
            elif analysis.get('candidate_selection') is not None and analysis['candidate_selection']!=selection:
                issue('IDENTITY_ERROR',report_path,'analysis/selection conflict')
            roles=[(role,selection.get(role)) for role in ('source_baseline','latest_checkpoint','accepted_candidate',
                'best_new_evaluated_candidate','best_observed_candidate','best_overall_candidate','fallback_checkpoint')]
            from ..domain.candidate_roles import ROLE_FIELDS
            for canonical,field in ROLE_FIELDS.items():
                if canonical in selection.get('model_roles',{}) and selection['model_roles'][canonical]!=selection.get(field):
                    issue('IDENTITY_ERROR',run,'canonical model role conflicts with '+field)
            progress_stages=(progress or {}).get('accepted_by_stage',{})
            selection_stages=selection.get('accepted_by_stage',{})
            for stage in set(progress_stages)&set(selection_stages):
                if progress_stages[stage]!=selection_stages[stage]:
                    issue('IDENTITY_ERROR',run,'selection/progress accepted_by_stage '+str(stage)+' conflict')
            stages={**progress_stages,**selection_stages}
            roles.extend(('accepted_by_stage.'+str(stage),candidate) for stage,candidate in stages.items())
            for role,candidate in roles:
                if candidate:
                    if not isinstance(candidate,dict):issue('CONFIG_ERROR',run,'candidate role '+role+' is not an object');continue
                    path=local_path(candidate.get('checkpoint',candidate.get('path','')),run)
                    if not path.is_file() or digest(path)!=candidate.get('checkpoint_sha256',candidate.get('sha256')):
                        issue('IDENTITY_ERROR',path,'candidate checkpoint SHA mismatch')
                    is_source=(role=='source_baseline' or candidate.get('role')=='source' or
                        bool(spec and str(path)==str(local_path(spec.get('source_checkpoint','')))))
                    if role=='best_new_evaluated_candidate' and is_source:
                        issue('IDENTITY_ERROR',path,'source registered as new candidate')
                    if path.is_file():
                        check_metadata(path,update=(spec or {}).get('source_update') if is_source else candidate.get('update'),
                            spec_sha=(spec or {}).get('source_spec_sha256') if is_source else (manifest or {}).get('spec_sha256'),
                            asset_sha=(spec or {}).get('source_asset_sha256',(spec or {}).get('asset_sha256')),
                            input_dim=(spec or {}).get('source_input_dim'))
                    if role=='latest_checkpoint':continue
                    candidate_sha=candidate.get('checkpoint_sha256',candidate.get('sha256'))
                    matching=[row for row in evaluations.values() if row.get('checkpoint_sha256')==candidate_sha]
                    external=candidate.get('evaluation')
                    if external:
                        evidence_base=run
                        if is_source and (manifest or {}).get('source_baseline_run'):
                            evidence_base=local_path(manifest['source_baseline_run'])
                        evidence_path=local_path(external,evidence_base)
                        if evidence_path.is_file() and str(evidence_path) not in evaluations:
                            evidence=read(evidence_path)
                            if evidence:
                                if evidence.get('checkpoint_sha256')!=candidate_sha:
                                    issue('IDENTITY_ERROR',evidence_path,'candidate/raw evaluation checkpoint differs')
                                else:matching.append(evidence)
                    if not matching:
                        issue('MISSING_EVIDENCE',path,role+' lacks same-checkpoint raw evaluation')
                    protocols=candidate.get('identity',{}).get('effective_protocols',{})
                    def candidate_gate(row):
                        target=tuple(row.get('target',row.get('command',[0,0]))[:2])
                        expected=protocols.get('zero' if target==(0,0) else 'motion')
                        return resolve_gate(row,evaluation_task(row),
                            expected_envs=(spec or {}).get('evaluation',{}).get('scored_envs'),
                            expected_protocol=expected)
                    for row in matching:
                        checked=candidate_gate(row)
                        if checked['status'] in ('MISSING_EVIDENCE','CONFLICTING_EVIDENCE'):
                            issue('MISSING_EVIDENCE' if checked['status']=='MISSING_EVIDENCE' else 'IDENTITY_ERROR',
                                path,{'role':role,'gate_status':checked['status'],
                                      'missing':checked['missing_fields'],'conflicts':checked['conflicts']})
                    if role=='accepted_candidate' or role.startswith('accepted_by_stage.'):
                        if not matching or any(candidate_gate(row)['status']!='PASSED' for row in matching):
                            issue('IDENTITY_ERROR',path,role+' lacks complete passed raw gates')
                        if candidate.get('accepted') is False or candidate.get('eligible') is False:
                            issue('IDENTITY_ERROR',path,role+' contradicts candidate acceptance/eligibility')
                        commands=candidate.get('identity',{}).get('capability_commands')
                        stage=candidate.get('stage')
                        stage_rows=(spec or {}).get('curriculum',{}).get('stages',[])
                        if commands is None and isinstance(stage,int) and 0<=stage<len(stage_rows):
                            commands=stage_rows[stage].get('commands')
                        if commands:
                            observed={tuple(row.get('target',row.get('command',[0,0]))[:2]) for row in matching}
                            missing={tuple(command[:2]) for command in commands}-observed
                            if missing:issue('MISSING_EVIDENCE',path,{'role':role,'missing_command_evaluations':sorted(missing)})
                    if matching and candidate.get('identity',{}).get('protocol_sha256') and manifest:
                        expected=candidate['identity']['protocol_sha256']
                        from ..completion import identity
                        if spec and expected!=identity(spec.get('evaluation',{})):
                            issue('IDENTITY_ERROR',path,'candidate protocol/spec identity conflict')
            if progress and selection.get('latest_checkpoint')!=progress.get('latest_checkpoint'):
                issue('IDENTITY_ERROR',run,'selection/progress latest checkpoint conflict')
        if include_processes and manifest and progress and progress.get('status')=='RUNNING':
            check=process_identity(manifest.get('pid'),output_dir=run,attempt_id=manifest.get('attempt_id'),
                command_token='train.py',started_unix_s=manifest.get('process_started_unix_s'),spec_path=spec_path)
            process_checks.append(check)
            if check['status']!='OK':issue(check['status'],run,check)
    processes=[]
    gpu=None
    if include_processes:
        for folder in Path('/proc').iterdir():
            if not folder.name.isdigit():continue
            try:
                snapshot=process_snapshot(int(folder.name))
                cwd=folder.joinpath('cwd').resolve()
            except (OSError,ValueError,IndexError,StopIteration,UnicodeError):continue
            command=snapshot['command']
            if (str(root) in command or cwd==root or root in cwd.parents) and any(token in command for token in (
                    'train.py','monitor.py','stand_chain','isaac','command_v6.train','command_v6.monitor')):
                match=next((row for row in process_checks if row.get('pid')==snapshot['pid']),None)
                processes.append({**snapshot,'identity':match['status'] if match else 'UNKNOWN',
                    'identity_reason':None if match else 'not matched to manifest/attempt/output/start time'})
        if run and (progress or {}).get('status')=='RUNNING':
            sidecars=[run.with_name(run.name+'.launcher.json'),run.with_name(run.name+'.monitor.json')]
            monitor_found=False
            for sidecar in sidecars:
                if not sidecar.is_file():continue
                row=read(sidecar)
                if not row:continue
                monitor_found=True
                check=process_identity(row.get('monitor_pid'),output_dir=run,
                    attempt_id=(manifest or {}).get('attempt_id'),command_token='monitor.py',
                    started_unix_s=row.get('process_started_unix_s'),spec_path=spec_path)
                process_checks.append(check)
                if check['status']!='OK':issue(check['status'],sidecar,check)
            if not monitor_found:issue('MISSING_EVIDENCE',run,'running monitor identity sidecar absent')
        gpu=gpu_snapshot()
    return {'status':'OK' if not findings else 'NEEDS_ATTENTION','findings':findings,'inputs':inputs,
            'processes':processes,'process_checks':process_checks,'gpu':gpu,'checkpoint':checkpoint_info,
            'hapi_target':{'requested':hapi_session,'current':os.environ.get('HAPI_SESSION_ID'),
                'matches_current':bool(hapi_session and hapi_session==os.environ.get('HAPI_SESSION_ID'))},
            'simulation':0,'ppo':0,'files_written':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--spec',type=Path)
    parser.add_argument('--run',type=Path)
    parser.add_argument('--processes',action='store_true')
    parser.add_argument('--hapi-session')
    args=parser.parse_args()
    print(json.dumps(inspect_project(args.project_root,spec_path=args.spec,run=args.run,
                                    include_processes=args.processes,hapi_session=args.hapi_session),indent=2))


if __name__=='__main__':main()
