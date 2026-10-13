"""Owner's final frozen32 test through the existing bounded evaluation supervisor."""
import copy,json,os,subprocess,sys,time
from pathlib import Path
from .course import SWING
from .data import sha
from native_stand.command_v6.completion import write
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,checked_input

def run(parent_spec,chain,decision,task_ledger):
 s=copy.deepcopy(json.loads(Path(parent_spec).read_text()));c=s.pop('recovery_course');s.pop('student_training');checkpoint=decision['resume'];task=json.loads(Path(c['task_manifest']).read_text())
 manifest=json.loads((Path(chain)/'manifest.json').read_text());remaining=min(1800.,manifest['submitted_unix_s']+14400-time.time()-60)
 if remaining<180:return {'status':'NOT_RUN','accepted':False,'reason':'block wall time insufficient for independent certification','checkpoint':checkpoint,'score_episodes':0,'wall_s':0.}
 name=new_experiment_name('recovery_course_final32_'+str(len(task_ledger['blocks'])))
 root=Path(task['project_root']);folder=root/'configs/experiments'/name;output=root/'runs'/name
 s.update(experiment=name,source_checkpoint=checkpoint['checkpoint'],source_sha256=checkpoint['sha256'],reward={},restore_source_rng=False,evaluation_only=True)
 s['course_authorization_reference']={'task_manifest':c['task_manifest'],'task_manifest_sha256':c['task_manifest_sha256'],'kind':'independent_Swing32_certification'}
 s['authorization']={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'task-owned final certification'}
 s['budget'].update(smoke_updates=0,formal_updates=0,sample_limit=0,evaluation_wall_s=remaining)
 s['artifacts']['run_name']=name
 s['recovery'].update(active_family=SWING,sampling={'version':'family_weights_v1','family_weights':{SWING:1.}},assessment={'families':[SWING],'retained_families':[]})
 s['recovery']['fsm']['timeout_s']=13.52;s['curriculum']['episode_length_s']=13.52
 s['student_evaluation']={'version':'student_evaluation_v1','max_output_bytes':256*2**20,'cases':[dict(case_id=f'final_{seed}',kind='student',checkpoint=checkpoint['checkpoint'],sha256=checkpoint['sha256'],family=SWING,seed=seed,yaw_rad=0. if i==0 else .01,seconds=13.52,role='RecoveryStudent') for i,seed in enumerate([20261010,20261021,20261022,20261023])]}
 s['student_dependencies'][checkpoint['checkpoint']]=checkpoint['sha256']
 inputs={p:h for p,h in s['student_dependencies'].items()};inputs.update([checked_input(parent_spec)])
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'sample_limit':0,'source_eval_wall_used_s':0.,'hapi_session':None}
 publish(folder,{'spec.json':s,'budget.json':book},inputs,completion_marker=True)
 from native_stand.command_v6.tools.register_authorization import register
 request={'approval_id':Path(c['task_manifest']).parent.name+'_cert_'+name,'user_scope':task['user_scope'],'session':task['session'],'physical_gpu':0,'gpu_uuid':task['gpu_uuid'],'max_online_updates':0,'max_phase_wall_s':remaining,'arms':[{'spec':str(folder/'spec.json'),'spec_sha256':sha(folder/'spec.json'),'budget_sha256':sha(folder/'budget.json')}]}
 register(request,current_session=os.environ.get('HAPI_SESSION_ID'),write=True)
 command=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',str(folder/'spec.json'),'--output-dir',str(output),'--physical-gpu','0','--hapi-session',task['session'],'--resource-mode','shared','--sharing-authorization',task['user_scope'],'--evaluation-only','--wait','--launch']
 start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,env={**os.environ,'PYTHONPATH':s['execution_source_root']})
 write(Path(chain)/'certification_submission.json',{'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 terminal=json.loads((output/'terminal_report.json').read_text()) if (output/'terminal_report.json').exists() else {}
 evaluations=[json.loads(p.read_text()) for p in sorted(output.glob('evaluation_[0-9][0-9].json'))]
 if r.returncode or terminal.get('status')!='COMPLETED' or len(evaluations)!=4:raise RuntimeError('final certification runtime/incomplete evidence; no retry')
 accepted=all(e.get('accepted') and e.get('scored_envs')==8 for e in evaluations)
 result={'status':'COMPLETED','accepted':accepted,'checkpoint':checkpoint,'run':str(output),'spec_sha256':sha(folder/'spec.json'),'score_episodes':32,'wall_s':time.monotonic()-start,'results':[{k:e.get(k) for k in ('case','passed_envs','scored_envs','accepted')} for e in evaluations]}
 write(Path(chain)/'final_course_certification.json',result);return result
