"""Publish a frozen checkpoint diagnostic spec/ledger; never authorize or launch."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ..config import validate
from ..domain.experiment_naming import validate_new_experiment_name
from .checkpoint_input import inspect
from .recovery_batch import validate_request
from ..domain.diagnostic_profiles import resolve as profile
from native_stand.recovery.task_protocol import batch_seconds


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(parent, checkpoint, output, *, family, protocol, session, physical_gpu, gpu_uuid,
            diagnostic_profile='full_transition', wall_s=1800, seed=104,commands=None,evaluation_mode='full',write=True):
    parent,checkpoint,output=map(lambda p:Path(p).resolve(),(parent,checkpoint,output))
    validate_new_experiment_name(output.name)
    if output.exists():raise FileExistsError(output)
    import math
    if not session or not gpu_uuid or physical_gpu not in (0,1) or not math.isfinite(wall_s) or wall_s<=0:
        raise ValueError('explicit session/GPU identity and positive wall bound required')
    original=json.loads(parent.read_text());spec=copy.deepcopy(original)
    recovery=spec.get('task')=='recovery'
    if not recovery and family is not None:raise ValueError('Motion diagnostic has no Recovery family')
    expected=spec['evaluation'].get('protocol_identity')
    if protocol!=expected:raise ValueError('protocol must match frozen parent; do not change scoring recipe here')
    identities={str(parent):sha(parent),str(checkpoint):sha(checkpoint)}
    for key,digest in (('asset_path','asset_sha256'),('asset_module_path','asset_module_sha256'),
                       ('colleague_config_path','colleague_config_sha256')):
        if sha(spec[key])!=spec[digest]:raise ValueError(key+' SHA differs')
        identities[str(Path(spec[key]).resolve())]=spec[digest]
    info=inspect(checkpoint,spec,parent)
    if recovery:
        library=Path(spec['recovery']['pose_library'])
        if sha(library)!=spec['recovery']['pose_library_sha256']:raise ValueError('pose library SHA differs')
        if family not in {row['family'] for row in json.loads(library.read_text())['poses']}:raise ValueError('family missing')
        identities[str(library.resolve())]=sha(library)
        requests=[validate_request(spec,{'checkpoint':str(checkpoint),'sha256':sha(checkpoint),'target':[0,0],
            'family':family,'seconds':batch_seconds(spec),'seed':seed,'diagnostic_profile':diagnostic_profile})]
    else:
        from ..domain.evaluation_requests import motion_request as validate_motion
        if not commands:raise ValueError('Explicit Motion commands required')
        seconds=spec['evaluation'].get('light_seconds',4.) if evaluation_mode=='light' else spec['evaluation']['seconds']
        requests=[validate_motion({'checkpoint':str(checkpoint),'sha256':sha(checkpoint),'target':c,
            'seconds':seconds,'seed':seed,'diagnostic_profile':diagnostic_profile,'evaluation_mode':evaluation_mode}) for c in commands]
    storage=profile(diagnostic_profile,task='recovery' if recovery else 'motion',dt=spec['control']['policy_dt_s'])
    spec.update(experiment=output.name,effective_recipe_version=1,evaluation_only=True,
        diagnostic_identity_only=True,
        evaluation_requests=requests,execution_source_root=str(Path(__file__).resolve().parents[3]),
        authorization={'hapi_session':session,'user_scope':'diagnostic preparation only; runtime not authorized'})
    spec['resources']={'mode':'exclusive','sharing_authorized':False}
    spec['device']={'physical_index':physical_gpu,'uuid':gpu_uuid}
    spec['artifacts']['run_name']=output.name
    spec['budget'].update(smoke_updates=0,formal_updates=0,sample_limit=0,formal_samples=0,evaluation_wall_s=wall_s)
    # PPO0 storage is owned by each request, not inherited training milestones.
    spec['evaluation']['full_trace_updates']=[]
    errors=validate(spec)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','experiment':output.name,
          'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0,'play':0},
          'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0,'play':0},'attempts':{},
          'source_eval_wall_used_s':0.,'sample_limit':0}
    manifest={'parent_spec':str(parent),'inputs':identities,'checkpoint_identity':info,
              'diagnostic_storage':storage,'runtime_authorized':False,'simulation':0,'ppo':0}
    if any(sha(path)!=digest for path,digest in identities.items()):raise ValueError('input changed before publication')
    if write:
        from .experiment_preparation import publish
        publish(output,{'spec.json':spec,'budget.json':book,'preparation_manifest.json':manifest},identities,completion_marker=True)
    manifest['files_written']=4 if write else 0
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent-spec','checkpoint','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--family')
    for name in ('protocol','hapi-session','gpu-uuid'):p.add_argument('--'+name,required=True)
    p.add_argument('--physical-gpu',type=int,choices=(0,1),required=True)
    p.add_argument('--diagnostic-profile',choices=('summary','failure_tail','full_transition'),default='full_transition')
    p.add_argument('--wall-s',type=float,default=1800)
    p.add_argument('--commands',type=Path,help='Motion JSON list of [vx,yaw]')
    p.add_argument('--evaluation-mode',choices=('full','light'),default='full')
    p.add_argument('--write',action='store_true',help='publish UNAUTHORIZED declaration; default zero-write CLI')
    a=p.parse_args()
    result=prepare(a.parent_spec,a.checkpoint,a.output_dir,family=a.family,protocol=a.protocol,
        session=a.hapi_session,physical_gpu=a.physical_gpu,gpu_uuid=a.gpu_uuid,
        diagnostic_profile=a.diagnostic_profile,wall_s=a.wall_s,commands=json.loads(a.commands.read_text()) if a.commands else None,
        evaluation_mode=a.evaluation_mode,write=a.write)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
