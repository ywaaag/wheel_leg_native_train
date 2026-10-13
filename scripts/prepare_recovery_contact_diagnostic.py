"""Same-reward bounded course with explicit contact-only diagnostic stop policy."""
import argparse,json
from pathlib import Path
from native_stand.command_v6.tools.prepare_recovery_course import prepare as course
from native_stand.command_v6.tools.experiment_preparation import digest
from native_stand.command_v6.domain.action_distribution import declaration as distribution
from native_stand.recovery.support_record_proposal import declaration as record
from native_stand.recovery.drawback_guidance_proposal import declaration as guidance
from native_stand.recovery.regression_policy import declaration as regression


def prepare(parent,checkpoint,library,session,*,total_updates=500,write=False):
    if type(total_updates) is not int or total_updates not in (100,500):raise ValueError('Supported total budget 100 or 500 includes smoke10')
    formal=total_updates-10;f=guidance()['family'];counts={f:26,'drawback_manual0001':25,'R0':13}
    evaluations=[10,25,50,90] if total_updates==100 else [10,25,50,100,200,300,400,490]
    request={'purpose':f'recovery_drawback_contact_diagnostic_total{total_updates}','level_id':'Level3','current_family':f,
        'retained_families':['drawback_manual0001','R0'],'family_weights':{k:v/64 for k,v in counts.items()},
        'environment_counts':counts,'support_record_reward':record(),'action_distribution':distribution(),
        'drawback_guidance':guidance(),'retention_regression_policy':regression(),
        'smoke_updates':10,'formal_updates':formal,'evaluation_updates':evaluations,
        'wall_s':{'source_eval':900,'smoke':900,'formal':7200 if total_updates==100 else 21600},
        'evaluation_schedule':{'checkpoint_every_updates':25,'full_every_updates':50},
        'notifications':{'enabled':True,'target_session':session,'authorization_note':'User approves bounded course and terminal wake currentowner; no retry/extension'}}
    return course(parent,checkpoint,library,request,checkpoint_sha256=digest(checkpoint),write=write)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent-spec','checkpoint','pose-library'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--total-updates',type=int,choices=(100,500),default=500);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.parent_spec,a.checkpoint,a.pose_library,a.session,total_updates=a.total_updates,write=a.write),indent=2))
