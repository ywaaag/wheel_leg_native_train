"""Explicit single-reward course preparation, no simulation or authorization."""
import argparse,json
from pathlib import Path
from native_stand.command_v6.tools.prepare_recovery_course import prepare as course
from native_stand.command_v6.tools.experiment_preparation import digest
from native_stand.command_v6.domain.action_distribution import declaration as distribution
from native_stand.recovery.support_record_proposal import declaration as record
from native_stand.recovery.drawback_guidance_proposal import declaration as guidance


def prepare(parent,checkpoint,library,session,*,write=False,formal_updates=25):
    if type(formal_updates) is not int or formal_updates not in (25,90):raise ValueError('Supported formal budget is 25 or 90; smoke10 included separately')
    evaluations=[10,25] if formal_updates==25 else [10,25,50,90]
    f=guidance()['family'];counts={f:26,'drawback_manual0001':25,'R0':13}
    request={'purpose':('recovery_drawback_mirror_guidance_from_new25' if formal_updates==25 else 'recovery_drawback_mirror_guidance_total100'),'level_id':'Level3','current_family':f,
        'retained_families':['drawback_manual0001','R0'],'family_weights':{k:v/64 for k,v in counts.items()},
        'environment_counts':counts,'support_record_reward':record(),'action_distribution':distribution(),'drawback_guidance':guidance(),
        'smoke_updates':10,'formal_updates':formal_updates,'evaluation_updates':evaluations,
        'wall_s':{'source_eval':900,'smoke':900,'formal':(3600 if formal_updates==25 else 7200)},'evaluation_schedule':{'checkpoint_every_updates':25,'full_every_updates':25},
        'notifications':{'enabled':True,'target_session':session,'authorization_note':'Enable only after explicit new run approval; user permits currentowner terminal wake'}}
    return course(parent,checkpoint,library,request,checkpoint_sha256=digest(checkpoint),write=write)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('parent-spec','checkpoint','pose-library'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--formal-updates',type=int,choices=(25,90),default=25)
    p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.parent_spec,a.checkpoint,a.pose_library,a.session,write=a.write,formal_updates=a.formal_updates),indent=2))
