"""Publish explicitly authorized forward-only course; no launch on preparation."""
import argparse,copy,json,os
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students import motion_forward_course as course
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]

def prepare(parent,source_run,*,write=False):
 parent=Path(parent).resolve();source_run=Path(source_run).resolve();s=copy.deepcopy(json.loads(parent.read_text()))
 name=new_experiment_name('motion31_forward512_course');folder=ROOT/'configs/experiments'/name
 s['experiment']=name;s['motion_course']['configuration']=course.configuration()
 s['motion_course'].update(source_parent_spec=str(parent),source_parent_spec_sha256=sha(parent))
 # Forward verification binds the previous exact course, not a rewritten historical declaration.
 s['student_training'].update(course_version=course.VERSION,course_stage=0,stage=0)
 from native_stand.students.motion_startup import smoke_profile,build
 s['student_training']['smoke_wiring']=smoke_profile()
 s['motion_training'].update(stage=0,spec_path=str(folder/'spec.json'))
 s['motion_assessment']=course.protocol();s['student_evaluation']['version']=course.ASSESSMENT
 s['student_evaluation']['cases']=course.cases(s,0)
 s['curriculum']['stages']=[course.stage_config(0)]
 s['evaluation']['protocol_identity']=course.ASSESSMENT
 s['artifacts']['run_name']=name
 s['authorization']={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'User authorizes2000 inclusive updates forward-only progressive course; no precision stopping; original1600'}
 s['notifications']={'enabled':True}
 s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':'Current user authorizes forward training on inherited GPU0 shared; no preemption'}
 s['student_dependencies'].update({str(parent):sha(parent)})
 s['motion_startup']=build(s,[source_run])
 from native_stand.students.requests import validate
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'hapi_session':os.environ['HAPI_SESSION_ID'],
 'limits':{'source_eval':1,'smoke':5,'formal':1995,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':2000}
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'source':s['source_checkpoint'],'source_sha256':s['source_sha256'],
 'stages':[course.stage_config(i) for i in range(3)],'source_reuse':s['motion_startup'],'simulation':0,'online_limit_inclusive':2000,
 'budget':s['budget'],'files_written':0}
 if write:
  from native_stand.students.motion_reward_audit import audit
  from native_stand.students import motion_tracking_reward
  snapshot=audit(s['reward']);snapshot.update(source_sha256=s['source_sha256'],reward_source_sha256=sha(motion_tracking_reward.__file__))
  publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report,'reward_snapshot.json':snapshot},s['student_dependencies'],completion_marker=True)
  report['files_written']=5
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',required=True);p.add_argument('--source-run',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
 print(json.dumps(prepare(a.parent_spec,a.source_run,write=a.write),indent=2))
