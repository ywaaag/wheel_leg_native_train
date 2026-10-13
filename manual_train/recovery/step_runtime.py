"""单步CLI的公共准备/登记适配；调用者必须选择正确的独立PYTHONPATH。"""
import argparse,copy,json,os,shlex,sys,uuid
from pathlib import Path
from native_stand.command_v6.completion import write
from native_stand.students.data import sha
from native_stand.students.course import VERSION,initial_state,plan
from native_stand.students.course_io import prepare_block
ROOT=Path('/home/kellen/wheel_leg_native_train')

def read(p):return json.loads(Path(p).read_text())
def publish(draft_path):
 draft=read(draft_path);folder=Path(draft['folder']);d=draft['settings'];source=Path(draft['checkpoint']) if draft['resume'] else (ROOT/d['source_checkpoint']).resolve();parent=Path(draft['parent_spec']) if draft['resume'] else (ROOT/d['source_parent_spec']).resolve();base=read(parent)
 from native_stand.students.manual_parameters import SETTINGS,REWARD_SHA
 if SETTINGS!=d or REWARD_SHA!=draft['reward_sha256']:raise ValueError('draft/config/reward differs from executed bundle')
 if sha(source)!=draft['source_sha256']:raise ValueError('source checkpoint changed')
 state=draft.get('state') or initial_state()
 if not draft['resume']:state.update(stage='A' if d['mode']=='standing' else 'B',prefix=round(d['teacher_prefix_s']*100) if d['mode']=='bridge' else 0,previous_prefix=round(d['teacher_prefix_s']*100) if d['mode']=='bridge' else 0)
 task={'version':VERSION,'plan':plan(),'authorization':'UNAUTHORIZED','session':draft['session'],'physical_gpu':0,'gpu_uuid':base['device']['uuid'],'resource_mode':'shared','project_root':str(ROOT),'source_checkpoint':str(source),'source_sha256':sha(source),'source_parent':str(parent),'source_parent_sha256':sha(parent),'teachers':base['student_teachers'],'stop_file':str(folder/'STOP'),'notification_enabled':False,'user_scope':'人工分步实验尚未授权','manual_experiment':{'version':'manual_experiment_v1','settings':d,'reward_sha256':REWARD_SHA}}
 write(folder/'task_manifest.json',task);write(folder/'task_ledger.json',{'version':VERSION,'status':'READY','state':state,'active_spec':None,'blocks':[],'totals':dict(updates=0,samples=0,effective_actor_samples=0,wall_s=0.,score_episodes=0),'smoke_evidence':{},'next_decision':None,'previous_experiment':draft.get('previous_experiment')})
 # The module parameters remain fixed on full resume; only source checkpoint/spec
 # differ from SETTINGS. All hyperparameters and reward remain identical.
 if draft['resume']:
  task['source_checkpoint']=draft['checkpoint'];task['source_sha256']=draft['source_sha256'];task['source_parent']=draft['parent_spec'];task['source_parent_sha256']=sha(draft['parent_spec']);write(folder/'task_manifest.json',task)
 r=prepare_block(folder/'task_manifest.json',state=state,resume=draft['resume'],smoke_evidence=draft.get('smoke_evidence'),write_files=True,output=ROOT/'configs/experiments'/folder.name)
 smoke=0 if draft['resume'] else 12
 r.update(session=task['session'],bundle=draft['bundle'],task_manifest=str(folder/'task_manifest.json'),run=str(ROOT/'runs'/folder.name),block_wall_s=d['chain_wall_s'],total_update_limit=d['formal_updates']+smoke)
 write(folder/'experiment.json',r);print(json.dumps(r,ensure_ascii=False))

def authorize(path,approval,do_write):
 from native_stand.command_v6.tools.register_authorization import register
 i=read(path);s=Path(i['spec']);spec=read(s);b=s.with_name('budget.json')
 req=dict(approval_id=s.parent.name+'_human',user_scope=approval,session=i['session'],physical_gpu=0,gpu_uuid=spec['device']['uuid'],max_online_updates=spec['budget']['smoke_updates']+spec['budget']['formal_updates'],max_phase_wall_s=spec['budget']['chain_wall_s'],arms=[dict(spec=str(s),spec_sha256=sha(s),budget_sha256=sha(b))])
 r=register(req,current_session=i['session'],write=do_write)
 if do_write:
  write(Path(path).with_name('authorization.json'),r);p=Path(i['task_manifest']).with_name('task_ledger.json');book=read(p);book.update(status='RUNNING',active_spec=str(s.resolve()));write(p,book)
 print(json.dumps(r,ensure_ascii=False,indent=2))

def resume(parent_path,checkpoint):
 import hashlib,torch
 from native_stand.students.manual_steps_contract import verify_resume
 from native_stand.students.manual_parameters import SETTINGS,REWARD_SHA
 from native_stand.command_v6.domain.experiment_naming import new_experiment_name
 p=read(parent_path);spec=read(p['spec']);cp=torch.load(checkpoint,map_location='cpu',weights_only=False)
 evidence=verify_resume(p,spec,cp,Path(checkpoint))
 name=new_experiment_name(SETTINGS['purpose']+'_resume');folder=ROOT/'manual_train/recovery/experiments'/name
 if folder.exists():raise FileExistsError(folder)
 folder.mkdir();shutil=__import__('shutil');shutil.copytree(Path(parent_path).parent/'tests',folder/'tests')
 state=copy.deepcopy(cp['course_state']);state['cumulative_updates']=cp['cumulative_update']
 bundle=Path(p['bundle']);mods={str(f.relative_to(bundle/'native_stand')):sha(f) for f in sorted((bundle/'native_stand').rglob('*.py'))}
 draft=dict(version='manual_step_draft_v1',folder=str(folder),bundle=str(bundle),settings=SETTINGS,reward_sha256=REWARD_SHA,source_sha256=sha(checkpoint),session='manual-'+uuid.uuid4().hex,resume=True,modules=mods,checkpoint=str(checkpoint),parent_spec=str(Path(checkpoint).parent/'source_snapshot/spec.json'),state=state,smoke_evidence=evidence,previous_experiment=str(Path(parent_path).resolve()))
 write(folder/'draft.json',draft);print(json.dumps({'draft':str(folder/'draft.json'),'restored_on_run':['Actor','Critic','Adam','RNG','recipe_updates','course_state'],'physical_state_restored':False,'smoke_updates':0,'automatic_submission':False},ensure_ascii=False,indent=2))

p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
a=sub.add_parser('publish');a.add_argument('draft')
a=sub.add_parser('authorize');a.add_argument('experiment');a.add_argument('--approve',required=True);a.add_argument('--write',action='store_true')
a=sub.add_parser('resume');a.add_argument('experiment');a.add_argument('checkpoint')
if __name__=='__main__':
 a=p.parse_args()
 if a.command=='publish':publish(a.draft)
 elif a.command=='authorize':authorize(a.experiment,a.approve,a.write)
 else:resume(a.experiment,a.checkpoint)
