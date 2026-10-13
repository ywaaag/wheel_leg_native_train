"""Two explicit same-source course requests; no authorization or runtime."""
import argparse,json
from pathlib import Path
from native_stand.command_v6.tools.prepare_recovery_course import prepare as course
from native_stand.command_v6.tools.experiment_preparation import digest
from native_stand.command_v6.domain.action_distribution import declaration as distribution
from native_stand.recovery.support_record_proposal import declaration as reward
from native_stand.recovery.leg_center_auxiliary import declaration as auxiliary


def prepare(parent,checkpoint,library,*,session,write=False):
    f=reward()['family'];counts={f:26,'drawback_manual0001':25,'R0':13};results={}
    for arm in ('A','B'):
        request={'purpose':'recovery_leg_center_'+arm.lower()+'_from_new25','level_id':'Level3','current_family':f,
            'retained_families':['drawback_manual0001','R0'],'family_weights':{k:v/64 for k,v in counts.items()},
            'environment_counts':counts,'support_record_reward':reward(),'action_distribution':distribution(),
            'smoke_updates':10,'formal_updates':25,'evaluation_updates':[10,25],
            'wall_s':{'source_eval':900,'smoke':900,'formal':3600},
            'evaluation_schedule':{'full_every_updates':25,'checkpoint_every_updates':25},
            'notifications':{'enabled':True,'target_session':session,'authorization_note':'enable only on newexplicit training approval'}}
        if arm=='B':request['leg_center_auxiliary']=auxiliary()
        results[arm]=course(parent,checkpoint,library,request,checkpoint_sha256=digest(checkpoint),write=write)
    return {'arms':results,'authorization':'UNAUTHORIZED','simulation':0,'updates_total':70,'samples_total':573440,'phase_wall_total_s':10800,'chain_wall_total_s':10920}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent-spec','checkpoint','pose-library'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.parent_spec,a.checkpoint,a.pose_library,session=a.session,write=a.write),indent=2))
