"""Shared-source CPU validation; records identities without copying code or tests."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from .experiment_preparation import checked_input,publish


def validate(spec,output,tests=(),*,write=False,checkpoint_initialization=False,reuse=None,submission_package=False):
    root=Path(__file__).resolve().parents[4];spec=Path(spec).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    if submission_package:
        config=json.loads(spec.read_text())
        if not config.get('device',{}).get('uuid') or config['device'].get('physical_index') not in (0,1):
            raise ValueError('Submission package requires an explicit declared device identity before CPU execution')
    source=root/'src'/'native_stand';inputs=dict([checked_input(spec)])
    for path in source.rglob('*.py'):inputs.update([checked_input(path)])
    for test in tests:
        path=(root/test).resolve()
        if not path.is_relative_to(root/'tests') or path.suffix!='.py':raise ValueError('explicit project CPU test file required')
        inputs.update([checked_input(path)])
    if tests:inputs.update([checked_input(root/'tests/conftest.py')])
    from .test_resources import scope
    test_scopes={test:scope(root/test) for test in tests}
    if write and any(v!='PORTABLE' for v in test_scopes.values()):
        raise ValueError('Shared CPU validation requires declared PORTABLE tests; PROJECT_DATA/UNCLASSIFIED tests need separate project verification')
    from .submission_receipt import stable
    from .source_identity import dependencies
    dependency_versions=dependencies()
    import importlib.metadata
    try:
        distribution=importlib.metadata.distribution('rsl-rl-lib')
        algorithm=Path(distribution.locate_file('rsl_rl/algorithms/ppo.py')).resolve()
        inputs.update([checked_input(algorithm)])
    except importlib.metadata.PackageNotFoundError:pass
    source_inputs={p:h for p,h in inputs.items() if Path(p).is_relative_to(source)}
    critical_inputs={p:h for p,h in inputs.items() if p not in source_inputs}
    report={'test_resource_scopes':test_scopes,'unclassified_tests':[k for k,v in test_scopes.items() if v=='UNCLASSIFIED'],
        'dependency_versions':dependency_versions,'inputs':critical_inputs,'source_inputs_sha256':stable(source_inputs),'source_root':str(source),'python':sys.executable,'tests':list(tests),
        'simulation':0,'optimizer_updates':0,'files_written':0,'validation_executed':False}
    if checkpoint_initialization:
        import torch,contextlib,io
        from .checkpoint_initialization import audit
        config=json.loads(spec.read_text());inputs.update([checked_input(config['source_checkpoint'],config['source_sha256'])]);critical_inputs.update([checked_input(config['source_checkpoint'],config['source_sha256'])])
        with contextlib.redirect_stdout(io.StringIO()):
            report['checkpoint_initialization']=audit(config,torch.load(config['source_checkpoint'],map_location='cpu',weights_only=False))
    if reuse is not None:
        prior_path=Path(reuse).resolve()/'validation_result.json'
        prior=json.loads(prior_path.read_text())
        if not prior.get('passed') or prior.get('python')!=sys.executable or prior.get('tests')!=list(tests):
            raise ValueError('Reusable CPU validation is not passed or test/interpreter contract differs')
        if prior.get('inputs')!=critical_inputs or prior.get('source_inputs_sha256')!=stable(source_inputs) or prior.get('dependency_versions')!=dependency_versions:raise ValueError('Reusable CPU validation input identities differ')
        for path,digest in inputs.items():checked_input(path,digest)
        reused={'passed':True,'validation_executed':False,'reused_validation':checked_input(prior_path),
            'simulation':0,'optimizer_updates':0,'files_written':0,'dependency_versions':dependency_versions,'inputs':critical_inputs,'source_inputs_sha256':stable(source_inputs),'tests':list(tests),'python':sys.executable}
        if submission_package:raise ValueError('Build submission package from original complete validation, not a reuse-only summary')
        if write:
            publish(output,{'validation_result.json':reused},inputs,completion_marker=True)
            reused['files_written']=2
        return reused
    if not write:return report
    publish(output,{'validation_plan.json':report},inputs)
    config=json.loads(spec.read_text())
    from .source_identity import record_identity
    record_identity(config,output,spec_sha256=inputs[str(spec)])
    environment={**os.environ,'PYTHONPATH':str(root/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
    command=[sys.executable,'-c','import json; from native_stand.command_v6.config import validate; import sys; s=json.load(open(sys.argv[1])); e=validate(s); print(json.dumps(e)); raise SystemExit(bool(e))',str(spec)]
    result=subprocess.run(command,cwd=root,env=environment,capture_output=True,text=True,timeout=60)
    report['schema']={'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    command=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',str(spec),
        '--output-dir',str(output/'PLAN_ONLY_RUN')]
    if config.get('evaluation_only'):command+=['--evaluation-only']
    result=subprocess.run(command,cwd=root,env=environment,capture_output=True,text=True,timeout=60)
    try:plan=json.loads(result.stdout)
    except (ValueError,TypeError):plan={}
    preflight=plan.get('preflight',{})
    prerequisites={'new simulation/PPO budget has not been authorized','phase budget exhausted','preceding phase has not completed',
        'formal requires identity-matched student wiring certificate','student smoke requires engineering-valid source evaluation'}
    plan_cpu_valid=bool(preflight) and (preflight.get('cpu_valid') is True or (bool(preflight.get('errors')) and all(e in prerequisites for e in preflight['errors'])))
    def compact_identity(value):
        if isinstance(value,list):return [compact_identity(v) for v in value]
        if not isinstance(value,dict):return value
        return {k:({'source_identity_reference':str(output/'identity.json'),
                    **{name:field for name,field in v.items() if name in ('actual_execution_root','declared_source_root','declared_source_differs','location_independent_modules_sha256','PPO_path','PPO_sha256','python','dependencies')}}
                   if k=='execution_identity' and isinstance(v,dict) else compact_identity(v)) for k,v in value.items()}
    import hashlib
    recorded_stdout=json.dumps(compact_identity(plan)) if plan else result.stdout
    report['plan_only']={'config_valid':plan_cpu_valid,'submit_ready':False,'command':command,'returncode':result.returncode,'stdout':recorded_stdout,
        'original_stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'stderr':result.stderr,
        'run_created':(output/'PLAN_ONLY_RUN').exists()}
    if (output/'PLAN_ONLY_RUN').exists():raise RuntimeError('CPU plan created a run')
    if tests:
        args=[sys.executable,'-m','pytest','-q','--tb=short',*tests]
        result=subprocess.run(args,cwd=root,env=environment,capture_output=True,text=True,timeout=120)
        report['tests_result']={'command':args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    report.update(validation_executed=True,files_written='CPU identity/result only; no source/tests copied',source_code_copied_bytes=0,test_copied_bytes=0,validation_mode='shared_src_record_only')
    report['passed']=(report['schema']['returncode']==0 and report['plan_only']['returncode']==0 and plan_cpu_valid
        and report.get('tests_result',{}).get('returncode',0)==0 and not report['plan_only']['run_created'])
    for path,digest in inputs.items():checked_input(path,digest)
    after={str(p.resolve()):checked_input(p)[1] for p in source.rglob('*.py')}
    if after!=source_inputs:raise ValueError('Shared source file set changed during CPU validation')
    (output/'validation_result.json').write_text(json.dumps(report,indent=2))
    if submission_package:
        if not report['passed']:raise ValueError('Cannot prepare submission package from failed CPU validation')
        from .submission_preparation import package
        report['submission_package']=package(spec,output,report)
        (output/'validation_result.json').write_text(json.dumps(report,indent=2))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--test',action='append',default=[])
    p.add_argument('--checkpoint-initialization',action='store_true',help='strict CPU model/Adam/std intervention readback, no optimizer step')
    p.add_argument('--reuse-validation',type=Path,help='Reuse exact passed inputs/tests without another source copy')
    p.add_argument('--submission-package',action='store_true',help='Add review-only declaration/budget/identity/authorization template and supervisor command')
    p.add_argument('--write',action='store_true');a=p.parse_args()
    result=validate(a.spec,a.output_dir,a.test,write=a.write,checkpoint_initialization=getattr(a,'checkpoint_initialization',False),reuse=a.reuse_validation,submission_package=a.submission_package)
    print(json.dumps(result,indent=2))
    return 0 if not a.write or result['passed'] else 2


if __name__=='__main__':raise SystemExit(main())
