"""Single-variable support-record short course; CPU preparation only."""
import argparse
import json
from pathlib import Path
from native_stand.command_v6.tools.prepare_recovery_course import prepare as course
from native_stand.command_v6.tools.experiment_preparation import digest
from native_stand.recovery.support_record_proposal import declaration


def prepare(parent,checkpoint,library,*,session,write=False,formal_updates=25):
    if formal_updates not in (25,100):raise ValueError('Only declared25/100 update blocks supported')
    f=declaration()['family'];counts={f:26,'drawback_manual0001':25,'R0':13}
    request={'purpose':'recovery_swing_support_record100_from_b25' if formal_updates==100 else 'recovery_swing_support_record_from_b25','level_id':'Level3','current_family':f,
        'retained_families':['drawback_manual0001','R0'],'family_weights':{k:v/64 for k,v in counts.items()},
        'environment_counts':counts,'support_record_reward':declaration(),
        'smoke_updates':10,'formal_updates':formal_updates,'evaluation_updates':[10,25,50,100] if formal_updates==100 else [10,25],
        'wall_s':{'source_eval':900,'smoke':900,'formal':7200 if formal_updates==100 else 3600}}
    request['notifications']={'enabled':True,'target_session':session,
        'authorization_note':'User permits terminal notification to current owner'}
    request['evaluation_schedule']={'full_every_updates':formal_updates,'checkpoint_every_updates':25}
    return course(parent,checkpoint,library,request,checkpoint_sha256=digest(checkpoint),write=write)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent-spec','checkpoint','pose-library'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--formal-updates',type=int,choices=(25,100),default=25);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.parent_spec,a.checkpoint,a.pose_library,session=a.session,write=a.write,formal_updates=a.formal_updates),indent=2))
