"""Create two equal-budget BC schedules and debit only unused authorized updates."""
import argparse
import copy
import json
from pathlib import Path

from native_stand.command_v6.config import validate
from native_stand.command_v6.ledger import transfer_unused_updates


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-spec',type=Path,required=True)
    p.add_argument('--quota-ledger',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    if a.output_dir.exists():raise FileExistsError(a.output_dir)
    old=json.loads(a.quota_ledger.read_text())
    if any(r['status']=='RUNNING' for r in old['attempts'].values()):raise ValueError('quota occupied')
    if old['limits']['formal']-old['used']['formal']<206:raise ValueError('insufficient equal-budget pair')
    source=json.loads(a.source_spec.read_text())
    specs={}
    for arm,kind in [('A_fixed','constant'),('B_annealed','cosine_to_zero')]:
        spec=copy.deepcopy(source)
        spec['experiment']=a.output_dir.name+'_'+arm
        spec['artifacts']['run_name']=spec['experiment']
        retention=spec['recovery']['standing_task']['retention']
        retention.update(channels='all',gradient_diagnostics=True,save_gradient_updates=[1,3,10,50,51,100],
            schedule={'kind':kind,**({'zero_after_updates':50} if kind!='constant' else {})})
        spec['budget'].update(smoke_updates=3,formal_updates=100,formal_wall_s=None,
            chain_wall_s=None,sample_limit=103*8192,source_eval_wall_s=300,smoke_wall_s=300)
        spec['authorization_note']='2026-10-06 user agreed gradient check then same-source full-channel BC fixed/annealed A/B;103unused updates transferred per arm, no automatic extra training.'
        spec['authorization']['user_scope']=spec['authorization_note']
        spec['recovery']['authorization_note']=spec['authorization_note']
        spec['experiment_variable']='Same source1500/Adam/seed/yaw recipe/physics/acceptance. A constantBC0.02; B cosineBC0.02 at first formal update,0.01 at26,exact0 from51. No wheel-only or mirror BC in this pair.'
        errors=validate(spec)
        if errors:raise ValueError(errors)
        specs[arm]=spec
    for arm,spec in specs.items():
        folder=a.output_dir/arm;folder.mkdir(parents=True)
        with (folder/'spec.json').open('x') as f:json.dump(spec,f,indent=2);f.write('\n')
        book={'authorization':'AUTHORIZED','authorization_evidence':spec['authorization_note'],
            'experiment':spec['experiment'],'limits':{'source_eval':1,'evaluate':0,'smoke':3,'formal':100},
            'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
            'source_eval_wall_used_s':0,'sample_limit':103*8192,'chain_wall_limit_s':None,
            'hapi_session':spec['authorization']['hapi_session']}
        transfer_unused_updates(a.quota_ledger,folder/'budget.json',book,
            transfer_id=a.output_dir.name+'_'+arm,requested=103,smoke_updates=3)
    print(json.dumps({'config_dir':str(a.output_dir.resolve()),'total_updates':206,'total_samples':206*8192}))


if __name__=='__main__':main()
