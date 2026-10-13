"""Publish independent frozen stochastic diagnostic; no runtime or authorization."""
import argparse,copy,json
from pathlib import Path
from native_stand.command_v6.domain.rollout_probe import declaration
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish,digest,differences
from native_stand.command_v6.config import validate


def prepare(parent,*,session,write=False,prior_failure=None,checkpoint=None):
    parent=Path(parent).resolve();s=json.loads(parent.read_text());inputs=dict([checked_input(parent)])
    if checkpoint is not None:
        import torch
        checkpoint=Path(checkpoint).resolve();saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
        if saved.get('spec_sha256')!=digest(parent) or saved.get('asset_sha256')!=s['asset_sha256']:
            raise ValueError('Candidate must match exact parent frozen spec and asset')
        s.update(source_checkpoint=str(checkpoint),source_sha256=digest(checkpoint),source_update=saved['update'],
            source_spec_sha256=digest(parent),source_asset_sha256=saved['asset_sha256'],
            recipe_parent_spec=str(parent),recipe_parent_spec_sha256=digest(parent))
    for k in ('source','asset','asset_module','colleague_config'):
        key='source_checkpoint' if k=='source' else k+'_path';inputs.update([checked_input(s[key],s[k+'_sha256'])])
    library=Path(s['recovery']['pose_library']);inputs.update([checked_input(library,s['recovery']['pose_library_sha256'])])
    spent=0.
    if prior_failure is not None:
        prior_failure=Path(prior_failure).resolve();inputs.update([checked_input(prior_failure)])
        prior=json.loads(prior_failure.read_text())
        if not prior['attempts'] or any(a['status']!='FAILED' or a['updates']!=0 for a in prior['attempts'].values()):
            raise ValueError('Only settled failed PPO0 diagnostic can prepare bounded retry')
        spent=sum(a['wall_s'] for a in prior['attempts'].values())
    ceiling=600-spent
    if ceiling<=90:raise ValueError('Insufficient cumulative diagnostic time')
    name=new_experiment_name('recovery_new25_leg_rollout_probe' if checkpoint else 'recovery_b25_frozen_rollout_guardfix' if prior_failure else 'recovery_b25_frozen_rollout_probe');out=Path(__file__).resolve().parents[1]/'configs/experiments'/name
    old=copy.deepcopy(s);s.update(experiment=name,evaluation_only=True,diagnostic_identity_only=True,rollout_probe=declaration(),execution_source_root=str(out.parents[2]/'src'),
        authorization={'status':'UNAUTHORIZED','hapi_session':session,'user_scope':'Prepare only; register current approval'})
    if checkpoint is not None:s['rollout_full_joint_capture']=True
    for k in ('evaluation_requests','input_capture','wiring_smoke','chain_submission','authorization_receipt','source_evidence_reference'):s.pop(k,None)
    s['recovery']['pose_library']=str(out/'poses.json');s['artifacts']['run_name']=name
    s['evaluation']['full_trace_updates']=[];s['evaluation']['unlock_full_updates']=[]
    s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,sample_limit=0,formal_samples=0,
        evaluation_wall_s=ceiling,chain_wall_s=ceiling,durability_wall_s=0)
    s['notifications']={'enabled':True,'target_session':session}
    s['resources']={'mode':'exclusive','sharing_authorized':False}
    errors=validate(s)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0,'play':0},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0,'play':0},'attempts':{},'sample_limit':0,'hapi_session':session}
    import hashlib
    js=lambda x:hashlib.sha256((json.dumps(x,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    approval={'approval_id':name+'__user_approved','user_scope':'REQUIRES_CURRENT_USER_SCOPE','session':session,
        'physical_gpu':0,'gpu_uuid':s['device']['uuid'],'max_online_updates':0,'max_phase_wall_s':ceiling,
        'arms':[{'spec':str(out/'spec.json'),'spec_sha256':js(s),'budget_sha256':js(book)}]}
    report={'output':str(out),'name':name,'inputs_sha256':inputs,'differences':differences(old,s),'simulation':0,'optimizer_updates':0,'approval_request':approval,
        'cumulative_wall_s':{'ceiling':600,'prior_used':spent,'remaining':ceiling}}
    if write:publish(out,{'spec.json':s,'budget.json':book,'preparation_manifest.json':report},inputs,
        raw_files={'poses.json':(library,s['recovery']['pose_library_sha256'])},completion_marker=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',type=Path,required=True);p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');p.add_argument('--prior-failure-ledger',type=Path);p.add_argument('--checkpoint',type=Path)
    a=p.parse_args();print(json.dumps(prepare(a.parent_spec,session=a.session,write=a.write,prior_failure=a.prior_failure_ledger,checkpoint=a.checkpoint),indent=2))
