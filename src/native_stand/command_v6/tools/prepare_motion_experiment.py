"""Prepare explicit Motion evaluation/course declarations. Default zero-write plan."""
import argparse
import contextlib
import copy
import io
import json
import math
from pathlib import Path

from ..config import validate
from ..domain.experiment_naming import validate_new_experiment_name
from ..domain.recipe import resolve
from ..domain.submission_contract import authorization
from .experiment_preparation import checked_input, differences, publish


def commands(values):
    if not isinstance(values,list) or not values:raise ValueError('commands must be a nonempty list')
    result=[]
    for value in values:
        if (not isinstance(value,list) or len(value)!=2 or any(type(v) not in (int,float)
                or not math.isfinite(v) for v in value)):
            raise ValueError('invalid command')
        if value[0] and value[1]:raise ValueError('combined straight/yaw command is outside this preparer')
        if value in result:raise ValueError('duplicate command')
        result.append(value)
    return result


def full_checkpoint(saved,spec):
    """CPU strict network/Adam-name audit, no optimizer constructed or stepped."""
    import torch
    from tensordict import TensorDict
    from .model_factory import model
    obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
    names=[];parameters=[]
    with contextlib.redirect_stdout(io.StringIO()):
        for role in ('actor','critic'):
            network=model(obs,actor=role=='actor',spec=spec)
            network.load_state_dict(saved[role],strict=True)
            named=list(network.named_parameters())
            if saved.get('parameter_names',{}).get(role)!=[n for n,_ in named]:
                raise ValueError('checkpoint parameter-name mapping missing or mismatched: '+role)
            if not all(torch.isfinite(v).all() for v in saved[role].values()):
                raise ValueError('checkpoint nonfinite: '+role)
            names.extend(role+'.'+n for n,_ in named);parameters.extend(v for _,v in named)
    optimizer=saved['optimizer'];ids=[v for group in optimizer['param_groups'] for v in group['params']]
    if len(ids)!=len(parameters) or len(set(ids))!=len(ids):raise ValueError('Adam parameter count/order differs')
    steps=[]
    for index,param in zip(ids,parameters):
        state=optimizer['state'].get(index)
        if not state:raise ValueError('Adam moment state missing')
        for field in ('exp_avg','exp_avg_sq'):
            if state[field].shape!=param.shape or not torch.isfinite(state[field]).all():
                raise ValueError('Adam shape/finite check failed: '+field)
        if (state['exp_avg_sq']<0).any():raise ValueError('Adam second moment negative')
        step=float(state['step'])
        if not math.isfinite(step) or step<0:raise ValueError('Adam step invalid')
        steps.append(step)
    if (not isinstance(saved.get('cpu_rng'),torch.Tensor) or saved['cpu_rng'].dtype!=torch.uint8
            or not isinstance(saved.get('cuda_rng'),list)):
        raise ValueError('checkpoint CPU/CUDA RNG state missing')
    return {'parameter_names':names,'Adam_states':len(ids),'Adam_steps':sorted(set(steps)),
            'source_learning_rates':[group['lr'] for group in optimizer['param_groups']],
            'RNG_fields':['cpu_rng','cuda_rng'],'strict_network_load':True}


def prepare(parent,checkpoint,request,output,*,checkpoint_sha256,session,physical_gpu,gpu_uuid,
            write=False,audit=None,audit_sha256=None):
    parent,checkpoint,request,output=map(lambda p:Path(p).resolve(),(parent,checkpoint,request,output))
    validate_new_experiment_name(output.name)
    if output.exists():raise FileExistsError(output)
    if not session or not isinstance(session,str) or not session.strip():raise ValueError('explicit current session required')
    if type(physical_gpu) is not int or physical_gpu not in (0,1) or not gpu_uuid or not gpu_uuid.startswith('GPU-'):
        raise ValueError('explicit GPU index/UUID required')
    inputs=dict([checked_input(parent),checked_input(request),checked_input(checkpoint,checkpoint_sha256)])
    if audit is not None:
        if audit_sha256 is None:raise ValueError('audit requires expected SHA')
        inputs.update([checked_input(audit,audit_sha256)])
    original=json.loads(parent.read_text());spec=copy.deepcopy(original)
    if spec.get('task')=='recovery':raise ValueError('Motion preparer cannot consume Recovery')
    if spec.get('effective_recipe_version')!=1:raise ValueError('explicit effective parent recipe required; migrate legacy declarations separately')
    if spec.get('initialization','warmstart')!='warmstart':
        raise ValueError('checkpoint preparation requires a warmstart parent')
    parent_errors=validate(spec)
    if parent_errors:raise ValueError('invalid parent recipe: '+str(parent_errors))
    resolve(spec)
    for field,sha_field in (('asset_path','asset_sha256'),('asset_module_path','asset_module_sha256'),
                            ('colleague_config_path','colleague_config_sha256')):
        inputs.update([checked_input(spec[field],spec[sha_field])])
    data=json.loads(request.read_text())
    if not isinstance(data,dict):raise ValueError('request must be an object')
    common={'mode','commands','wall_s','seed'}
    course={'retained_commands','current_commands','weights','online_updates','smoke_updates','full_every_updates'}
    mode=data.get('mode')
    if mode not in ('evaluation','course'):raise ValueError('mode must be evaluation or course')
    required=common-{'seed'} if mode=='evaluation' else course|{'mode','wall_s'}
    missing=required-set(data)
    if missing:raise ValueError('missing request fields: '+','.join(sorted(missing)))
    unknown=set(data)-(common if mode=='evaluation' else course|{'mode','wall_s'})
    if unknown:raise ValueError('unsupported request fields: '+','.join(sorted(unknown)))
    import torch
    saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if saved.get('asset_sha256')!=spec['asset_sha256']:raise ValueError('checkpoint asset identity differs')
    spec.update(source_checkpoint=str(checkpoint),source_sha256=inputs[str(checkpoint)],
        source_input_dim=150,source_update=saved['update'],source_spec_sha256=saved['spec_sha256'])
    audit_model=full_checkpoint(saved,spec)
    spec.update(experiment=output.name,authorization={'status':'UNAUTHORIZED','hapi_session':session,
        'user_scope':'Preparation only; this declaration grants no runtime budget'},
        execution_source_root=str(Path(__file__).resolve().parents[3]),evaluation_only=mode=='evaluation',
        diagnostic_identity_only=mode=='evaluation')
    spec['artifacts']['run_name']=output.name
    spec['device']={'physical_index':physical_gpu,'uuid':gpu_uuid,'logical':'cuda:0','headless':True}
    spec['resources']={'mode':'exclusive','sharing_authorized':False}
    for key in ('external_prerequisites','evaluation_requests','next_phase_authorization',
                'endpoint_baseline','cumulative_quota_reference','authorization_note'):
        spec.pop(key,None)
    limits={'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0}
    if mode=='evaluation':
        targets=commands(data['commands']);wall=data['wall_s'];seed=data.get('seed',spec['evaluation']['seed'])
        if type(wall) not in (int,float) or not math.isfinite(wall) or wall<=120:raise ValueError('evaluation wall bound invalid')
        if type(seed) is not int or seed<0:raise ValueError('evaluation seed invalid')
        spec['evaluation_requests']=[{'checkpoint':str(checkpoint),'sha256':inputs[str(checkpoint)],
            'role':'source','target':target,'seconds':spec['evaluation']['seconds'],'seed':seed} for target in targets]
        spec['budget'].update(smoke_updates=0,formal_updates=0,sample_limit=0,formal_samples=0,evaluation_wall_s=wall)
        limits['evaluate']=1
    else:
        retained=commands(data['retained_commands']);current=commands(data['current_commands'])
        if retained[0]!=[0,0] or len(current)!=2 or current[0]!=[-v for v in current[1]] or [0,0] in current:
            raise ValueError('course requires zero retained and one symmetric current pair')
        if any(c in retained for c in current):raise ValueError('current pair already retained')
        if any(c!=[0,0] and [-v for v in c] not in retained for c in retained):
            raise ValueError('retained endpoints must include both directions')
        axis=0 if current[0][0] else 1
        previous=max(abs(c[axis]) for c in retained)
        if any(abs(v)>4 for c in retained+current for v in c):
            raise ValueError('course endpoints exceed the declared +/-4 goal')
        if axis==1 and ([4,0] not in retained or [-4,0] not in retained):
            raise ValueError('yaw course requires retained straight +/-4 endpoints')
        if not math.isclose(abs(current[0][axis]),previous+.5,abs_tol=1e-9):
            raise ValueError('current pair must be the next 0.5 step on its axis')
        targets=retained+current;weights=data['weights']
        if (not isinstance(weights,list) or len(weights)!=len(targets)
                or any(type(w) not in (int,float) or not math.isfinite(w) or w<=0 for w in weights)
                or not math.isclose(sum(weights),1.,abs_tol=1e-6)):
            raise ValueError('weights must match commands and sum to one')
        total=data['online_updates'];smoke=data['smoke_updates'];frequency=data['full_every_updates']
        if type(total) is not int or type(smoke) is not int or not 1<=smoke<total:raise ValueError('inclusive online budget invalid')
        if type(frequency) is not int or frequency<1:raise ValueError('full evaluation frequency invalid')
        wall=data['wall_s']
        if not isinstance(wall,dict) or set(wall)!=set(('source_eval','smoke','formal')):
            raise ValueError('explicit source_eval/smoke/formal wall bounds required')
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<=120 for v in wall.values()):
            raise ValueError('invalid phase wall bound')
        _,effective=resolve(spec)
        spec['curriculum']['stages']=[{'id':0,'name':'L0','commands':[[0,0]],'weights':[1.],
            'command_mode':'ramp','sampling_mode':'categorical_weights','enforce_whitelist':True}, {'id':1,'name':'CURRENT',
            'commands':targets,'weights':weights,'boundary':current,'command_mode':'ramp','sampling_mode':'categorical_weights','enforce_whitelist':True}]
        spec['curriculum']['active_stage']=1
        task=spec['curriculum'].get('task_progression')
        if not task:raise ValueError('parent must define explicit task progression/retention')
        task.update(initial_stage=1,max_enabled_stage=1,consecutive_confirmations=max(2,task['consecutive_confirmations']),
            max_updates_per_stage=total-smoke,confirmation_spacing_updates=frequency,required_commands=targets,
            blocked_reason=f'Single-stage course; formal limit {total-smoke} updates; no higher commands unlocked')
        for axis in ('linear','yaw'):
            d=effective['reward'][axis+'_error_denominator']
            spec['reward']['stage_'+axis+'_denominators']={'0':d,'1':d}
        spec['evaluation'].update(full_every_updates=frequency,checkpoint_every_updates=frequency,
            zero_every_updates=frequency,light_every_updates=0,unlock_full_updates=[],motion_commands=targets,
            run_final_durability=False)
        # Explicitly freeze this preparer's single-stage scope using existing legacy behavior.
        spec.update(cohort_width_ab=True,straight_high_speed_course=False,
            source_evaluation_commands=retained[1:],source_required_commands=retained[1:],restore_source_rng=True)
        spec['budget'].update(smoke_updates=smoke,formal_updates=total-smoke,
            sample_limit=total*spec['ppo']['envs']*spec['ppo']['steps_per_env'],
            formal_samples=(total-smoke)*spec['ppo']['envs']*spec['ppo']['steps_per_env'])
        for phase,value in wall.items():spec['budget'][phase+'_wall_s']=value
        spec['budget'].pop('evaluation_wall_s',None)
        limits.update(source_eval=1,smoke=smoke,formal=total-smoke)
    errors=validate(spec)
    if errors:raise ValueError(errors)
    # Recipe preservation is enforced, not just declared in the report.
    for field in ('action','control','ground','observation','history','termination','ppo'):
        if spec[field]!=original[field]:raise ValueError('unapproved recipe change: '+field)
    if spec['evaluation']['protocol_identity']!=original['evaluation']['protocol_identity']:
        raise ValueError('unapproved protocol migration')
    changes=differences(original,spec)
    allowed_roots={'experiment','authorization','authorization_note','execution_source_root','evaluation_only',
        'diagnostic_identity_only','source_checkpoint','source_sha256','source_input_dim','source_update',
        'source_spec_sha256','artifacts','device','resources','external_prerequisites','evaluation_requests',
        'next_phase_authorization','endpoint_baseline','cumulative_quota_reference','budget','curriculum',
        'evaluation','reward','cohort_width_ab','straight_high_speed_course','source_evaluation_commands',
        'source_required_commands','restore_source_rng'}
    for change in changes:
        field=change['field']
        if field.split('.')[0] not in allowed_roots:raise ValueError('unapproved change: '+field)
        if field.startswith('reward.') and not field.startswith(('reward.stage_linear_denominators','reward.stage_yaw_denominators')):
            raise ValueError('unapproved reward change: '+field)
        if field.startswith('evaluation.') and field.split('.')[1] not in {
                'full_every_updates','checkpoint_every_updates','zero_every_updates','light_every_updates',
                'unlock_full_updates','motion_commands','run_final_durability'}:
            raise ValueError('unapproved evaluation change: '+field)
    _,effective=resolve(spec)
    book={'authorization':'UNAUTHORIZED','experiment':output.name,'limits':limits,
        'used':{key:0 for key in limits},'attempts':{},'source_eval_wall_used_s':0.,
        'total_online_PPO_limit':limits['smoke']+limits['formal'],'inherited_usage':0,
        'quota_note':'Proposal only; authorize against cumulative scope before submission'}
    from ..domain.command_sampling import resolve as sampling_plan
    from ..domain.evaluation_config import identities
    manifest={'parent_spec':str(parent),'checkpoint':str(checkpoint),'inputs':inputs,
        'checkpoint_audit':audit_model,'requested':data,'effective':effective,
        'effective_authorization':authorization(spec),'differences':changes,
        'sampling_plan':[sampling_plan(row,spec['ppo']['envs']) for row in spec['curriculum']['stages']],
        'evaluation_identity_components':identities(spec['evaluation']),
        'allowed_change_roots':sorted(allowed_roots),
        'audit_scope':'Referenced audit identity only; no automatic capability certificate or quota import',
        'runtime_authorized':False,'simulation':0,'optimizer_updates':0,'files_written':3 if write else 0}
    from .execution_identity import identity
    manifest['execution_identity']=identity(spec)
    if write:
        publish(output,{'spec.json':spec,'budget.json':book,'preparation_manifest.json':manifest},inputs)
    return {'spec':spec,'budget':book,'preparation_manifest':manifest,'output':str(output),
            'files_written':3 if write else 0,'runtime_authorized':False,'simulation':0,'ppo':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent-spec','checkpoint','request','output-dir'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('checkpoint-sha256','hapi-session','gpu-uuid'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--physical-gpu',type=int,choices=(0,1),required=True)
    parser.add_argument('--audit',type=Path);parser.add_argument('--audit-sha256')
    parser.add_argument('--write',action='store_true',help='publish UNAUTHORIZED declarations; never launch')
    args=parser.parse_args()
    config_root=Path(__file__).resolve().parents[3].parent/'configs'/'experiments'
    if args.write and args.output_dir.resolve().parent!=config_root.resolve():
        parser.error('--write output must be a fresh directory under this project configs/experiments')
    result=prepare(args.parent_spec,args.checkpoint,args.request,args.output_dir,
        checkpoint_sha256=args.checkpoint_sha256,session=args.hapi_session,physical_gpu=args.physical_gpu,
        gpu_uuid=args.gpu_uuid,write=args.write,audit=args.audit,audit_sha256=args.audit_sha256)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
