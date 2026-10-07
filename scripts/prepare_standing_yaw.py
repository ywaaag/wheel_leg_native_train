"""Fresh diagnostic or yaw-only recipe; never rewrite old run evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from native_stand.command_v6.ledger import transfer_unused_updates


def write(path, data):
    with path.open('x') as stream:
        json.dump(data,stream,indent=2);stream.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old-run',type=Path,required=True)
    p.add_argument('--old-ledger',type=Path,required=True)
    p.add_argument('--config-dir',type=Path,required=True)
    p.add_argument('--mode',choices=('diagnostic','yaw','scissor'),required=True)
    a=p.parse_args()
    if a.config_dir.exists():raise FileExistsError(a.config_dir)
    terminal=json.loads((a.old_run/'terminal_report.json').read_text())
    book=json.loads(a.old_ledger.read_text())
    if terminal['exit_code']!=0 or any(row['status']=='RUNNING' for row in book['attempts'].values()):
        raise ValueError('Old exact attempt must finish before preparing intervention')
    parent=a.old_run/'source_snapshot/spec.json';spec=json.loads(parent.read_text())
    a.config_dir.mkdir(parents=True)
    if a.mode=='diagnostic':
        # Preserve exact candidate spec identity; only a new independent read-only ledger.
        with (a.config_dir/'spec.json').open('xb') as f:f.write(parent.read_bytes())
        attempts={key:copy.deepcopy(row) for key,row in book['attempts'].items()
                  if row['phase']=='source_eval' and row['status']=='COMPLETED'}
        write(a.config_dir/'budget.json',{'authorization':'AUTHORIZED',
            'authorization_evidence':'2026-10-06 user agreed saturation-channel PPO0 diagnostic, at most300s',
            'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},
            'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},
            'attempts':attempts,'source_eval_wall_used_s':0})
        return
    spec['experiment']=a.config_dir.name
    spec['artifacts']['run_name']=a.config_dir.name
    if a.mode=='yaw':
        spec['recovery']['settling_reward'].update(settling_yaw_weight=-.8,yaw_scale_rad_s=.35)
    spec['recovery']['authorization_note']='Only one-variable R0 controlled continuation; no new difficulty.'
    spec['authorization_note']='2026-10-06 user agreed one-variable R0 continuation; no automatic extension.'
    spec['authorization']['user_scope']=spec['authorization_note']
    spec['budget'].update(source_eval_wall_s=300,smoke_updates=3,smoke_wall_s=300,
        formal_updates=100,formal_wall_s=None,sample_limit=103*8192,chain_wall_s=None)
    spec['evaluation'].update(light_every_updates=100,full_every_updates=50,
        checkpoint_every_updates=100,full_at_final=True,run_final_durability=False)
    spec['experiment_variable']='One-variable controlled continuation; source1500 and Adam retained. No action/physics/symmetry/height/termination change.'
    spec['comparison_evidence']={'source1500':'runs/standing_level_v2_check_20261006_151025/source_eval/evaluation_source.json',
        'old_update250':str((a.old_run/'evaluation_250_0_0.json').resolve()),
        'old_run_terminal':str((a.old_run/'terminal_report.json').resolve())}
    if a.mode=='scissor':
        spec['reward'].update(wheel_longitudinal_offset=-.1875,
            wheel_longitudinal_deadband_m=.03,wheel_longitudinal_scale_m=.03)
        spec['budget'].update(source_eval_wall_s=120,formal_updates=50,sample_limit=53*8192)
        spec['diagnostics']['wheel_geometry_readback_gate']={'tolerance_m':.002,'samples_per_env':8}
        spec['authorization_note']='2026-10-06 user agreed geometry readback PPO0/120s,3smoke/300s and50formal;53unused updates transferred, no extension.'
        spec['authorization']['user_scope']=spec['authorization_note']
        spec['recovery']['authorization_note']=spec['authorization_note']
        spec['experiment_variable']='Only added wheel-center horizontal native-forward alignment cost: -.1875*(relu(offset-.03)/.03)^2*.01. Source1500, same Adam/LR3e-5 and fixedBC0.02, all other yaw recipe/physics/protocol unchanged.'
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    write(a.config_dir/'spec.json',spec)
    newbook={'authorization':'AUTHORIZED','authorization_evidence':spec['authorization_note'],
        'experiment':spec['experiment'],'limits':{'source_eval':1,'evaluate':1,'smoke':3,'formal':spec['budget']['formal_updates']},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0,'sample_limit':spec['budget']['sample_limit'],'chain_wall_limit_s':None,
        'hapi_session':spec['authorization']['hapi_session']}
    transfer_unused_updates(a.old_ledger,a.config_dir/'budget.json',newbook,
        transfer_id=a.config_dir.name,requested=spec['budget']['formal_updates']+3,smoke_updates=3)
    write(a.config_dir/'yaw_reward_probe.json',{'formula':'-0.8*(sqrt(1+(canonical_yaw/0.35)^2)-1)*0.01',
        'dt_s':.01,'canonical_yaw_axis':1,'gate':'unconditional',
        'values':[{'yaw_rad_s':x,'additional_reward_per_step':-.8*((1+(x/.35)**2)**.5-1)*.01}
                  for x in [0.,.03,.1,.15,.3,.36,1.,2.45]]})


if __name__=='__main__':main()
