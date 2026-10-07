"""Prepare frozen-source Recovery capability checks and BC coverage A/B."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import validate_new_experiment_name


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(parent, output, session, authorize=False):
    output=Path(output).resolve();parent=Path(parent).resolve()
    if output.exists():raise FileExistsError(output)
    validate_new_experiment_name(output.name)
    base=json.loads(parent.read_text())
    for key,digest in [('source_checkpoint','source_sha256'),('asset_path','asset_sha256'),
                       ('asset_module_path','asset_module_sha256'),('colleague_config_path','colleague_config_sha256')]:
        if sha(base[key])!=base[digest]:raise ValueError(key+' identity differs')
    library=Path(base['recovery']['pose_library'])
    if sha(library)!=base['recovery']['pose_library_sha256']:raise ValueError('pose identity differs')
    scope=('Current user approved source50 R0/R1 frozen10s capability check (2seeds each), '
           'and BC sampling-only A/B: each arm smoke10+formal<=100, eval25/50/100, '
           'coefficient.02 and all reward/PPO/physics unchanged. No coefficient escalation or R1 PPO.')
    resources={'mode':'shared','sharing_authorized':True,
               'authorization_note':'User explicitly permitted shared GPU0; do not stop any other process.'}
    cases={}
    for label,selection in [('A_first','first'),('B_uniform','uniform_rollout'),('source_capability',None)]:
        folder=output/label
        s=copy.deepcopy(base)
        s.update(experiment=output.name+'_'+label,recipe_parent_spec_sha256=sha(parent),
                 effective_recipe_version=1,resources=resources)
        s['authorization']={'hapi_session':session,'user_scope':scope if authorize else 'Preparation only'}
        s['recovery']['authorization_note']=s['authorization']['user_scope']
        s['recovery']['pose_library']=str(folder/'poses.json')
        s['artifacts']['run_name']=s['experiment']
        if selection:
            s['recovery']['standing_task']['retention']['sample_selection']=selection
            s['experiment_variable']='Only retention sample_selection='+selection+';256 valid inputs,.02 all-channel coefficient.'
            limits={'source_eval':1,'evaluate':0,'smoke':10,'formal':100}
            sample_limit=110*s['ppo']['envs']*s['ppo']['steps_per_env']
        else:
            s['execution_source_root']=str(parent.parents[3]/'src')
            s['device']={'physical_index':0,'uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72'}
            s['recovery']['holdout_sampling']='balanced_pose_cycle'
            s['evaluation_requests']=[{'checkpoint':s['source_checkpoint'],'sha256':s['source_sha256'],
                'target':[0,0],'family':family,'seconds':10.,'seed':seed}
                for family in ('R0','R0_perturbed') for seed in (104,205)]
            s['budget']['evaluation_wall_s']=1200
            limits={'source_eval':0,'evaluate':1,'smoke':0,'formal':0};sample_limit=0
        errors=validate(s)
        if errors:raise ValueError(errors)
        book={'authorization':'AUTHORIZED' if authorize else 'UNAUTHORIZED',
              'authorization_evidence':s['authorization']['user_scope'],'experiment':s['experiment'],
              'limits':limits,'used':dict.fromkeys(limits,0),'attempts':{},
              'source_eval_wall_used_s':0.,'sample_limit':sample_limit,'hapi_session':session}
        cases[label]=(s,book)
    output.mkdir(parents=True)
    for label,(s,book) in cases.items():
        folder=output/label;folder.mkdir()
        for name,value in [('spec.json',s),('budget.json',book)]:
            with (folder/name).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
        with (folder/'poses.json').open('xb') as stream:stream.write(library.read_bytes())
    return cases


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session',required=True)
    parser.add_argument('--authorize',action='store_true')
    args=parser.parse_args()
    validate_new_experiment_name(args.output_dir.name)
    prepare(args.parent,args.output_dir,args.hapi_session,args.authorize)
    print(json.dumps({'configs':str(args.output_dir),'simulation':0,'ppo':0,
                      'maximum_PPO_updates':220,'maximum_PPO_samples':1802240,'capability_cases':4}))
