"""Portable tests consumed by the generated manual source bundle."""
FROZEN_TEST_SCOPE='PORTABLE'
import importlib.util,os,torch,pytest
available=importlib.util.find_spec('native_stand.students.manual_support') is not None
if os.environ.get('MANUAL_BUNDLE_TEST_REQUIRED')=='1' and not available:
 raise RuntimeError('Manual bundle tests imported shared source instead of the frozen manual runtime')
pytestmark=pytest.mark.skipif(not available,reason='runs against the generated manual bundle')

def values():
 return dict(height=torch.tensor([.4,.168]),h0=torch.tensor([.168,.168]),angles=torch.zeros(2,2),contacts=torch.ones(2,2)*10,clearance=torch.ones(2)*.1,torque=torch.zeros(2,6),previous_targets=torch.zeros(2,6),executed_targets=torch.zeros(2,6),angular_body=torch.zeros(2,3),velocity_native=torch.zeros(2,3),yaw=torch.zeros(2),entered=torch.tensor([True,False]),controlled=torch.tensor([True,True]),fault=torch.zeros(2,dtype=torch.bool),entry_event=torch.zeros(2,dtype=torch.bool),success_event=torch.zeros(2,dtype=torch.bool),failure_event=torch.zeros(2,dtype=torch.bool),active_leg_q=torch.zeros(2,4))

def test_manual_declaration_and_actual_reward_consumption():
 from native_stand.students.manual_parameters import SETTINGS
 from native_stand.students.recovery_task import configuration,reward,FIELDS
 from native_stand.students.manual_support import REWARD,RECIPE
 from native_stand.students.training_recipe import declaration
 cfg=configuration(REWARD);r=reward(**values(),reward_configuration=cfg)
 torch.testing.assert_close(r['weighted_density'],r['raw']*torch.tensor([cfg['weights'][f] for f in FIELDS]))
 assert torch.isfinite(r['total']).all() and r['total'][0]>0
 assert cfg['manual_implementation_sha256']
 d=declaration(RECIPE,source_actor_sha256='a'*64)
 assert d['reward']==cfg and d['milestones'][-1]==SETTINGS['formal_updates']


def test_initialization_and_fault_reward_stay_zero():
 from native_stand.students.recovery_task import configuration,reward
 from native_stand.students.manual_support import REWARD
 v=values();v['controlled'][0]=False;v['fault'][1]=True;v['success_event'][:]=True
 assert reward(**v,reward_configuration=configuration(REWARD))['total'].tolist()==[0.,0.]


def test_manual_ppo_uses_declared_learning_rate_and_31_40_dims(tmp_path):
 from native_stand.students.manual_parameters import SETTINGS
 from native_stand.students.ppo import assemble
 from native_stand.students.manual_support import RECIPE
 from native_stand.students.training_recipe import declaration
 from native_stand.recovery.controlled_ppo import KEY
 from tensordict import TensorDict
 from native_stand.students.model import Student
 cp=tmp_path/'student.pt';torch.save({'interface_version':'multiskill_mcu_v2','role':'RecoveryStudent','actor':Student(version='multiskill_mcu_v2').state_dict()},cp)
 from native_stand.students.data import sha
 obs=TensorDict({'student_actor':torch.zeros(2,31),'student_critic':torch.zeros(2,40),KEY:torch.ones(2,1,dtype=torch.bool)},batch_size=[2])
 ppo=assemble(cp,obs,recipe=declaration(RECIPE,source_actor_sha256=sha(cp)))
 assert ppo.learning_rate==SETTINGS['learning_rate'] and not ppo.optimizer.state
 assert ppo.actor(obs).shape==(2,6) and ppo.critic(obs).shape==(2,1)
 assert not ppo.actor.log_std.requires_grad

def test_zero_prefix_smoke_does_not_require_teacher_handoff(tmp_path):
 import json
 from native_stand.students.training_evidence import smoke_certificate
 spec={'source_sha256':'a'*64,'recovery_course':{'state':{'stage':'B','prefix':0,'previous_prefix':0}}}
 for name,value in {'progress.json':{},'terminal_report.json':{},'manifest.json':{},'source_snapshot/spec.json':spec}.items():
  p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
 errors=smoke_certificate(tmp_path,spec)['errors']
 assert 'real teacher-to-student handoff missing' not in errors
 spec['recovery_course']['state']['prefix']=50
 assert 'real teacher-to-student handoff missing' in smoke_certificate(tmp_path,spec)['errors']

def test_finite_finish_never_launches_another_block(tmp_path):
 import json
 from native_stand.students.manual_support import finish
 spec=tmp_path/'spec.json';manifest=tmp_path/'task_manifest.json';chain=tmp_path/'chain';chain.mkdir()
 spec.write_text(json.dumps({'recovery_course':{'task_manifest':str(manifest)}}))
 (tmp_path/'task_ledger.json').write_text(json.dumps({'active_spec':str(spec.resolve()),'blocks':[],'totals':dict(updates=0,samples=0,effective_actor_samples=0,wall_s=0.,score_episodes=0)}))
 (tmp_path/'budget.json').write_text(json.dumps({'used':{'smoke':12,'formal':100}}))
 (chain/'chain_terminal_report.json').write_text(json.dumps({'chain_wall_s':42.,'phase_results':[]}))
 finish(spec,chain,'COMPLETED',None)
 result=json.loads((tmp_path/'task_ledger.json').read_text())
 assert result['totals']['updates']==112 and result['totals']['samples']==917504
 assert result['active_spec'] is None and result['next_decision']['action']=='STOP'
 with pytest.raises(ValueError,match='already settled'):finish(spec,chain,'COMPLETED',None)

def test_resume_budget_has_no_repeated_smoke_or_extra_samples():
 from native_stand.students.manual_support import budget
 a,b=budget(),budget(True)
 assert a['smoke_updates']==12 and b['smoke_updates']==0 and b['smoke_wall_s']==0
 assert b['sample_limit']==b['formal_updates']*8192
 assert b['formal_wall_s']+b['source_eval_wall_s']==b['chain_wall_s']

def test_full_resume_restores_actual_CPU_Adam_and_rng():
 from native_stand.students.model import Student
 from native_stand.students.resume import restore,rng_state
 from types import SimpleNamespace
 import copy
 def pair():
  a,c=Student(version='multiskill_mcu_v2'),Student(False,version='multiskill_mcu_v2');a.log_std.requires_grad_(False)
  return SimpleNamespace(actor=a,critic=c,optimizer=torch.optim.Adam([*a.parameters(),*c.parameters()],lr=3e-5))
 p=pair();p.optimizer.zero_grad();(p.actor(torch.ones(2,31)).square().sum()+p.critic(torch.ones(2,40)).square().sum()).backward();p.optimizer.step()
 state=rng_state();data=dict(course_resume_version='student_full_training_resume_v1',recipe_version='manual_recovery_ppo_v1',interface_version='multiskill_mcu_v2',fixed_std=True,actor=copy.deepcopy(p.actor.state_dict()),critic=copy.deepcopy(p.critic.state_dict()),optimizer=copy.deepcopy(p.optimizer.state_dict()),training_rng=state,cumulative_update=112,recipe_updates=100)
 q=pair();result=restore(q,data,{'version':'manual_recovery_ppo_v1'})
 assert result['warmup_repeated'] is False and result['cumulative_update']==112
 for x,y in zip(p.actor.parameters(),q.actor.parameters()):torch.testing.assert_close(x,y,rtol=0,atol=0)
 for x,y in zip(p.critic.parameters(),q.critic.parameters()):torch.testing.assert_close(x,y,rtol=0,atol=0)
 assert q.optimizer.state_dict()['param_groups']==p.optimizer.state_dict()['param_groups']
 for k,v in p.optimizer.state_dict()['state'].items():
  for n,x in v.items():torch.testing.assert_close(x,q.optimizer.state_dict()['state'][k][n],rtol=0,atol=0)
 assert torch.equal(torch.get_rng_state(),state['torch_cpu'])

def test_manual_resume_rejects_failed_run_and_changed_code(tmp_path,monkeypatch):
 import json
 from native_stand.students.manual_steps_contract import verify_resume
 from native_stand.students.manual_parameters import SETTINGS,REWARD_SHA
 from native_stand.students.data import sha
 from native_stand.command_v6.tools import execution_identity
 from native_stand.command_v6 import wiring
 run=tmp_path/'run';phase=run/'formal';phase.mkdir(parents=True);checkpoint=phase/'model_update_100.pt';checkpoint.write_bytes(b'CPU metadata fixture; not a runnable model')
 parent=phase/'source_snapshot/spec.json';parent.parent.mkdir();parent.write_text('{}')
 smoke=run/'smoke';smoke.mkdir();(smoke/'wiring_certificate.json').write_text('{}');(smoke/'source_snapshot').mkdir();(smoke/'source_snapshot/spec.json').write_text('{}')
 task=tmp_path/'task.json';task.write_text(json.dumps({'manual_experiment':{'settings':SETTINGS}}))
 spec={'student_training':{'reward':{'manual_implementation_sha256':REWARD_SHA}},'asset_sha256':'a'*64,'recovery_course':{'resume':False}}
 cp=dict(course_resume_version='student_full_training_resume_v1',recipe_version='manual_recovery_ppo_v1',interface_version='multiskill_mcu_v2',fixed_std=True,training_recipe=spec['student_training'],asset_sha256='a'*64,spec_sha256=sha(parent),source_code_sha256='b'*64,critic={},optimizer={},training_rng={},cumulative_update=112,recipe_updates=100,course_state={},certified_capabilities=[])
 info={'run':str(run),'task_manifest':str(task)}
 for p in (phase/'terminal_report.json',run/'chain_terminal_report.json'):p.write_text(json.dumps({'status':'COMPLETED','failure':None}))
 monkeypatch.setattr(execution_identity,'identity',lambda s:{'location_independent_modules_sha256':'b'*64})
 monkeypatch.setattr(wiring,'validate_persisted_certificate',lambda f,s:{'status':'PASSED'})
 assert verify_resume(info,spec,cp,checkpoint)['folder']==str(smoke)
 cp['source_code_sha256']='c'*64
 with pytest.raises(ValueError,match='code changed'):verify_resume(info,spec,cp,checkpoint)
 cp['source_code_sha256']='b'*64
 (phase/'terminal_report.json').write_text(json.dumps({'status':'FAILED','failure':'CPU fixture fault'}))
 with pytest.raises(ValueError,match='unsettled'):verify_resume(info,spec,cp,checkpoint)
