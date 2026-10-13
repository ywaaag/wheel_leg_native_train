"""Explicit source-only CPU validation copy; no simulator, budget reservation or launch."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from .experiment_preparation import checked_input,publish


def validate(spec,output,tests=(),*,write=False,checkpoint_initialization=False,reuse=None,submission_package=False):
    root=Path(__file__).resolve().parents[4];spec=Path(spec).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
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
        raise ValueError('Source-only frozen validation requires declared PORTABLE tests; PROJECT_DATA/UNCLASSIFIED tests need separate project verification')
    report={'test_resource_scopes':test_scopes,'unclassified_tests':[k for k,v in test_scopes.items() if v=='UNCLASSIFIED'],
        'inputs':inputs,'source_root':str(source),'python':sys.executable,'tests':list(tests),
        'simulation':0,'optimizer_updates':0,'files_written':0,'validation_executed':False}
    if checkpoint_initialization:
        import torch,contextlib,io
        from .checkpoint_initialization import audit
        config=json.loads(spec.read_text());inputs.update([checked_input(config['source_checkpoint'],config['source_sha256'])])
        with contextlib.redirect_stdout(io.StringIO()):
            report['checkpoint_initialization']=audit(config,torch.load(config['source_checkpoint'],map_location='cpu',weights_only=False))
    if reuse is not None:
        prior_path=Path(reuse).resolve()/'validation_result.json'
        prior=json.loads(prior_path.read_text())
        if not prior.get('passed') or prior.get('python')!=sys.executable or prior.get('tests')!=list(tests):
            raise ValueError('Reusable frozen validation is not passed or test/interpreter contract differs')
        if prior.get('inputs')!=inputs:raise ValueError('Reusable frozen validation input identities differ')
        for path,digest in inputs.items():checked_input(path,digest)
        reused={'passed':True,'validation_executed':False,'reused_validation':checked_input(prior_path),
            'simulation':0,'optimizer_updates':0,'files_written':0,'inputs':inputs,'tests':list(tests),'python':sys.executable}
        if submission_package:raise ValueError('Build submission package from original complete validation, not a reuse-only summary')
        if write:
            publish(output,{'validation_result.json':reused},inputs,completion_marker=True)
            reused['files_written']=2
        return reused
    if not write:return report
    publish(output,{'validation_plan.json':report},inputs)
    snapshot=output/'source_snapshot';snapshot.mkdir()
    shutil.copytree(source,snapshot/'native_stand',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(spec,snapshot/'spec.json')
    config=json.loads(spec.read_text())
    (output/'manifest.json').write_text(json.dumps({'spec_sha256':inputs[str(spec)],
        'declared_execution_source_root':config.get('execution_source_root'),
        'execution_modules_sha256':{str(p.relative_to(snapshot/'native_stand')):checked_input(p)[1]
            for p in (snapshot/'native_stand').rglob('*.py')}},indent=2))
    (snapshot/'budget.json').write_text(json.dumps({'authorization':'UNAUTHORIZED',
        'limits':{p:0 for p in ('source_eval','smoke','formal','evaluate','play')},
        'used':{p:0 for p in ('source_eval','smoke','formal','evaluate','play')},'attempts':{},'source_eval_wall_used_s':0.}))
    environment={**os.environ,'PYTHONPATH':str(snapshot),'PYTHONDONTWRITEBYTECODE':'1'}
    # Config validation has no execution-root side effects; runtime preflight uses normal shared CLI.
    command=[sys.executable,'-c','import json; from native_stand.command_v6.config import validate; s=json.load(open("source_snapshot/spec.json")); e=validate(s); print(json.dumps(e)); raise SystemExit(bool(e))']
    result=subprocess.run(command,cwd=output,env=environment,capture_output=True,text=True,timeout=60)
    report['schema']={'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    command=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',str(snapshot/'spec.json'),
        '--output-dir',str(output/'PLAN_ONLY_RUN')]
    if config.get('evaluation_only'):command+=['--evaluation-only']
    result=subprocess.run(command,cwd=output,env=environment,capture_output=True,text=True,timeout=60)
    report['plan_only']={'command':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
        'run_created':(output/'PLAN_ONLY_RUN').exists()}
    if (output/'PLAN_ONLY_RUN').exists():raise RuntimeError('CPU plan created a run')
    if tests:
        (output/'tests').mkdir()
        for test in set(tests)|{'tests/conftest.py'}:
            destination=output/test;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/test,destination)
        args=[sys.executable,'-m','pytest','-q','--tb=short',*tests]
        result=subprocess.run(args,cwd=output,env=environment,capture_output=True,text=True,timeout=120)
        report['tests_result']={'command':args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    report.update(validation_executed=True,files_written='explicit CPU copy/report; no runs/checkpoint/environment copied')
    report['passed']=(report['schema']['returncode']==0 and report['plan_only']['returncode']==0
        and report.get('tests_result',{}).get('returncode',0)==0 and not report['plan_only']['run_created'])
    for path,digest in inputs.items():checked_input(path,digest)
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
