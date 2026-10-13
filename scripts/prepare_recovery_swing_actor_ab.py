"""Swing-only controlled-actor A/B, same frozen recipe, distinct source identity."""
import argparse,json
from pathlib import Path
from native_stand.command_v6.tools.prepare_recovery_course import prepare as course
from native_stand.command_v6.tools.experiment_preparation import digest
from native_stand.recovery.controlled_ppo import declaration


def prepare(parent,source,candidate,recipe,library,session,*,write=False):
    effective=json.loads(Path(recipe).read_text());f='swing_candidate_from_historical_r1';results={}
    for arm,cp in (('A',source),('B',candidate)):
        request={'purpose':'recovery_swing_controlled_actor_'+arm.lower(),'level_id':'Level3','current_family':f,'retained_families':[],
            'family_weights':{f:1.},'environment_counts':{f:64},'swing_only':True,'actor_update_scope':declaration(),
            'seed':20261010,'restore_source_rng':False,'cleanup_wall_s':100,
            'support_record_reward':effective['recovery']['support_record_reward'],'drawback_guidance':effective['recovery']['drawback_guidance'],
            'action_distribution':effective['action_distribution'],'smoke_updates':10,'formal_updates':100,'evaluation_updates':[25,50,100],
            'wall_s':{'source_eval':900,'smoke':900,'formal':3500},'evaluation_schedule':{'checkpoint_every_updates':25,'full_every_updates':50},
            'notifications':{'enabled':True,'target_session':session,'authorization_note':'User explicitly approves A/B at-most-once terminal wake; sequential B only after A terminal'}}
        results[arm]=course(parent,cp,library,request,checkpoint_sha256=digest(cp),reward_recipe=recipe,write=write)
    return {'arms':results,'authorization':'UNAUTHORIZED','total_updates':220,'total_raw_samples':1802240,'total_chain_wall_s':10800,'independent_training_seeds':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent-spec','source','candidate','reward-recipe','pose-library'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.parent_spec,a.source,a.candidate,a.reward_recipe,a.pose_library,a.session,write=a.write),indent=2))
