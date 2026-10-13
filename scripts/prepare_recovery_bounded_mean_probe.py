"""Publish explicit new-distribution threefamily PPO0; no training authorization."""
import argparse,copy,json
from pathlib import Path
from native_stand.command_v6.domain.action_distribution import declaration
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish,digest,differences
from native_stand.command_v6.config import validate


def prepare(parent,*,session,write=False):
    parent=Path(parent).resolve();s=json.loads(parent.read_text());old=copy.deepcopy(s);inputs=dict([checked_input(parent)])
    for key,sha in [('source_checkpoint','source_sha256'),('asset_path','asset_sha256'),('asset_module_path','asset_module_sha256'),('colleague_config_path','colleague_config_sha256')]:inputs.update([checked_input(s[key],s[sha])])
    library=Path(s['recovery']['pose_library']);inputs.update([checked_input(library,s['recovery']['pose_library_sha256'])])
    name=new_experiment_name('recovery_b25_bounded_mean_threegroup_ppo0');out=Path(__file__).resolve().parents[1]/'configs/experiments'/name
    s.update(experiment=name,action_distribution=declaration(),evaluation_only=True,effective_recipe_version=1,
        execution_source_root=str(out.parents[2]/'src'),authorization={'status':'UNAUTHORIZED','hapi_session':session,'user_scope':'Prepare only'})
    s['artifacts']['run_name']=name;s['recovery']['pose_library']=str(out/'poses.json')
    for key in ('rollout_probe','wiring_smoke','source_evidence_reference','chain_submission','authorization_receipt'):s.pop(key,None)
    s['evaluation']['full_trace_updates']=[];s['evaluation']['unlock_full_updates']=[]
    s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,sample_limit=0,formal_samples=0,
        evaluation_wall_s=900,chain_wall_s=900,durability_wall_s=0)
    s['evaluation_requests']=[{'checkpoint':s['source_checkpoint'],'sha256':s['source_sha256'],'target':[0,0],
        'family':f,'seconds':23,'seed':104,'role':'bounded_mean_migration','diagnostic_profile':'full_transition'}
        for f in ['swing_candidate_from_historical_r1','drawback_manual0001','R0']]
    s['notifications']={'enabled':True,'target_session':session};s['resources']={'mode':'exclusive','sharing_authorized':False}
    errors=validate(s)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0,'play':0},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0,'play':0},'attempts':{},'sample_limit':0,'hapi_session':session}
    import hashlib
    js=lambda x:hashlib.sha256((json.dumps(x,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    approval={'approval_id':name+'__approved','user_scope':'REQUIRES_EXPLICIT_SCOPE','session':session,'physical_gpu':0,
        'gpu_uuid':s['device']['uuid'],'max_online_updates':0,'max_phase_wall_s':900,
        'arms':[{'spec':str(out/'spec.json'),'spec_sha256':js(s),'budget_sha256':js(book)}]}
    report={'output':str(out),'name':name,'inputs_sha256':inputs,'differences':differences(old,s),'approval_request':approval,
        'simulation':0,'PPO':0,'scope':'Parameter identity preserved,behavior transformed; certification required'}
    if write:publish(out,{'spec.json':s,'budget.json':book,'preparation_manifest.json':report},inputs,
        raw_files={'poses.json':(library,s['recovery']['pose_library_sha256'])},completion_marker=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',type=Path,required=True);p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.parent_spec,session=a.session,write=a.write),indent=2))
