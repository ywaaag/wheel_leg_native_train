"""Explicit dual-interface probe; no simulator, no optimizer."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy,json,sys,types,importlib
from pathlib import Path
import torch,numpy as np,pytest
from native_stand.students.handoff_probe import owners,validate,KIND,VERSION,B250_SHA
from native_stand.recovery.handoff_protocol import declaration,duration
from native_stand.recovery.domain import Mode
from native_stand.recovery.motion_handoff import motion_frame

def test_case_scoped_reset_reproduces_and_fixes_unknown_family_without_training_mutation():
 from native_stand.students.requests import evaluation_recovery
 from native_stand.recovery.sampling import sample_poses
 config={'active_family':'swing','sampling':{'version':'fixed_environment_families_v1','family_weights':{'swing':1.},'environment_counts':{'swing':64}},'assessment':{'families':['swing'],'retained_families':[]}}
 original=copy.deepcopy(config)
 poses=[{'family':f,'split':'holdout','offline_valid':True} for f in ('swing','motion_native_normal')]
 with pytest.raises(ValueError,match='Unknown evaluation family'):
  sample_poses(poses,config,'motion_native_normal','holdout',training=False)
 for family in ('swing','motion_native_normal'):
  scoped=evaluation_recovery(config,poses,family)
  ids,weights=sample_poses(poses,scoped,family,'holdout',training=False)
  assert [poses[i]['family'] for i in ids]==[family] and weights==[1.]
  assert scoped['assessment']['retained_families']==[]
 assert config==original
 with pytest.raises(ValueError,match='Missing valid pose split'):
  evaluation_recovery(config,poses,'unknown')
 with pytest.raises(ValueError,match='Missing valid pose split'):
  evaluation_recovery(config,[{**p,'offline_valid':False} for p in poses],'swing')

def test_prefix_owners_exact_steps_and_invalid_initialization():
 initial=torch.tensor([False,False,True,False]);valid=torch.tensor([True,True,False,False])
 for k in [0,10,30,40,45,50,55,60,65]:
  count=torch.tensor([max(k-1,0),k,k+1,k+1]);owner,student,motion=owners(initial,valid,count,k)
  assert owner[1]==2 and owner[2]==0 and owner[3]==0
  if k:assert owner[0]==3
  else:assert owner[0]==2
  assert not (student&motion).any()

def spec():
 base={'case_id':'normal','kind':'teacher_normal','checkpoint':'cp','sha256':B250_SHA,'family':'motion_native_normal','seed':1,'yaw_rad':0.,'seconds':13.52,'role':'MotionZeroStudent'}
 case={**base,'case_id':'student','kind':KIND,'family':'swing_candidate_from_historical_r1','role':'RecoveryStudent','seconds':duration(.5,1.),'switch_s':.5}
 return {'evaluation_only':True,'evaluation':{'envs':64,'scored_envs':8},'budget':{'smoke_updates':0,'formal_updates':0},'recovery':{'initialization':{'settle_max_s':1.}},'student_evaluation':{'version':VERSION,'cases':[base,case],'max_output_bytes':1024,'handoff_protocol':declaration()},'student_teachers':[{'checkpoint':'rec','sha256':'a'*64,'spec':'spec','spec_sha256':'b'*64},{'checkpoint':'cp','sha256':B250_SHA,'spec':'spec','spec_sha256':'b'*64}]}

def test_protocol_schema_no_training_and_duration():
 s=spec();validate(s)
 for change in ['unknown','duration','training','normal']:
  d=copy.deepcopy(s)
  if change=='unknown':d['student_evaluation']['cases'][1]['hidden_blend']=True
  elif change=='duration':d['student_evaluation']['cases'][1]['seconds']+=.01
  elif change=='training':d['student_training']={'version':'other'}
  else:d['student_evaluation']['cases'].reverse()
  with pytest.raises(ValueError):validate(d)

class Scripted:
 def __init__(self,fail=False):
  self.device='cpu';self.num_envs=8;self.ids=list(range(6));self.robot=types.SimpleNamespace(joint_names=['LH','LA','LW','RH','RA','RW'],data=types.SimpleNamespace(root_state_w=types.SimpleNamespace(torch=torch.zeros(8,13)),joint_pos=types.SimpleNamespace(torch=torch.zeros(8,6)),joint_vel=types.SimpleNamespace(torch=torch.zeros(8,6))))
  self.robot.data.root_state_w.torch[:,6]=1;self.fsm=types.SimpleNamespace(mode=torch.full((8,),int(Mode.RECOVERY)));self.reference=torch.zeros(8,6);self.initialization_checked=torch.ones(8,dtype=torch.bool);self.executed_prefix=torch.zeros(8,dtype=torch.long);self.controller=torch.zeros(8,dtype=torch.long);self.executed_leg=torch.zeros(8,4);self.executed_wheel=torch.zeros(8,2);self.probe_student_obs=torch.zeros(8,31);self.hist=torch.zeros(8,125);self.fail=fail;self.steps=0;self.reset_calls=0;self.obs_refreshes=0;self.motion_age=torch.zeros(8)
 def configure_case(self,row):self.switch_steps=round(row['switch_s']/.01)
 def configure_protocol(self,p):pass
 def configure_randomization(self,p):pass
 def select_initial_family(self,*a):pass
 def obs(self,reset=False):
  self.obs_refreshes+=1;self.probe_student_obs[:,25:28]=torch.tensor([0.,1.,0.]);self.probe_student_obs[:,24]=.8
  self.motion_obs=motion_frame(torch.zeros(8,3),torch.tensor([[0.,-1.,0.]]*8),torch.zeros(8,6),torch.zeros(8,6),self.executed_leg,self.executed_wheel,self.reference,self.hist,torch.full((8,),reset));self.hist=self.motion_obs['history'];return {}
 def reset(self):self.reset_calls+=1;return self.obs(True),{}
 def control_owner_pre(self):return owners(self.fsm.mode==int(Mode.INITIALIZING),self.initialization_checked,self.executed_prefix,self.switch_steps)
 def step(self,action):
  owner,student,motion=self.control_owner_pre();self.executed_prefix+=student;self.controller=owner;self.steps+=1
  scale=torch.where(motion,.5,1.5)[:,None];self.executed_leg=action[:,[0,1,3,4]]*scale;self.executed_wheel=action[:,[2,5]]*100
  s=torch.zeros(8,39);s[:,0]=self.steps*.01;s[:,6]=.4;s[:,10:12]=10;s[:,13]=.01;s[:,29]=1;s[:,32]=int(Mode.RECOVERY)
  p=torch.zeros(8,10);control=torch.zeros(8,54);control[:,18:24]=action;control[:,28:32]=self.executed_leg
  self.recovery_snapshot=s;self.standing_snapshot=p;self.recovery_control_snapshot=control;self.wheel_geometry_snapshot=torch.zeros(8,13);self.handoff_root_post=self.robot.data.root_state_w.torch.clone();self.handoff_controller=owner;self.recovery_cause_snapshot=torch.zeros(8,6,dtype=torch.bool);self.motion_age+=motion*.01;self.handoff_motion_age=self.motion_age.clone();self.handoff_initial_age=torch.zeros(8);self.handoff_joint_q_post=self.robot.data.joint_pos.torch.clone();self.handoff_joint_dq_post=self.robot.data.joint_vel.torch.clone()
  done=torch.zeros(8,dtype=torch.bool)
  if self.fail and self.steps==2:done[4]=True;s[4,3]=1
  if self.steps>=1070:done[:]=True
  return self.obs(),torch.zeros(8),done,torch.zeros_like(done),{}

class Actor(torch.nn.Module):
 def __init__(self,motion=False):super().__init__();self.motion=motion;self.calls=[];self.weight=torch.nn.Parameter(torch.tensor(0.2))
 def forward(self,x,stochastic_output=False):
  if self.motion:
   assert x['policy'].shape[1]==25 and x['history'].shape[1]==125;assert torch.all(x['policy'][:,8]==2.) # .40 native height *5
   n=len(x['policy'])
  else:
   assert x.shape[1]==31 and torch.all(x[:,26]==1);n=len(x)
  self.calls.append(n);return torch.ones(n,6)*self.weight

def test_real_rollout_switch_no_reset_different_scales_failed_denominator_rng():
 from native_stand.students.evaluator import rollout
 env=Scripted(fail=True);a=Actor();m=Actor(True);a.train();m.train();rng=torch.get_rng_state().clone();row=spec()['student_evaluation']['cases'][1]
 payload,arrays=rollout(env,a,row,teacher=[Actor(),m])
 assert env.reset_calls==1 and env.obs_refreshes==env.steps+1
 assert len(a.calls)==50 and len(m.calls)==1020
 np.testing.assert_allclose(arrays['control'][:50,:,28:32],.3,atol=1e-7)
 np.testing.assert_allclose(arrays['control'][50:,:,28:32],.1,atol=1e-7)
 assert (arrays['controller'][:50]==3).all() and (arrays['controller'][50:]==2).all()
 assert arrays['motion_clock_s'][50,0,0]==pytest.approx(.01)
 assert not arrays['motion_previous_outside'][50].any()
 assert payload['scored_envs']==8 and payload['passed_envs']==7 and not payload['per_env'][4]['accepted']
 assert payload['per_env'][4]['actual_switched'] is False and payload['per_env'][4]['student_independent_accepted'] is False
 assert a.training and m.training and torch.equal(rng,torch.get_rng_state())
 assert payload['teacher_rescue_not_student_success'] and not hasattr(env,'student_trace_capture')

@pytest.mark.parametrize('runtime_fault',[False,True])
def test_public_evaluator_baseline_failure_stops_remaining_cases(tmp_path,monkeypatch,runtime_fault):
 from native_stand.students import evaluator
 from native_stand.command_v6 import train
 s=spec();s.update(interface_version='multiskill_mcu_v2',asset_module_root=str(tmp_path),asset_sha256='a'*64)
 s['student_evaluation']['max_output_bytes']=1024*1024
 s['student_evaluation']['cases'][0]['sha256']='a'*64
 config=tmp_path/'spec.json';config.write_text(json.dumps(s));out=tmp_path/'newrun';attempt='exact-fixture'
 (tmp_path/'budget.json').write_text(json.dumps({'attempts':{attempt:{'status':'RUNNING','output_dir':str(out.resolve()),'started_unix_s':__import__('time').time()}}}))
 args=types.SimpleNamespace(spec=config,output=out,run=True,attempt_id=attempt,wall_limit_s=1000)
 monkeypatch.setattr(evaluator,'plan',lambda *a:{'preflight':{'status':'PASS'},'requests':s['student_evaluation']['cases']})
 monkeypatch.setattr(train,'record_run_configuration',lambda *a:'fixture_sha')
 close_codes=[]
 def close_app(**kw):
  assert (out/'terminal_report.json').exists() and (out/'cleanup.json').exists()
  close_codes.append(kw['exit_code'])
 app=types.SimpleNamespace(close=close_app)
 monkeypatch.setitem(sys.modules,'isaaclab.app',types.SimpleNamespace(AppLauncher=lambda *a:types.SimpleNamespace(app=app)))
 env=Scripted();seen=[]
 def make(*a,**kw):
  seen.append(kw);env.reference=torch.zeros(8,6);env.close=lambda:None
  env.recovery_config={'active_family':kw['initial_family'],'sampling':{},'assessment':{}}
  return env
 monkeypatch.setattr(evaluator,'environment',make)
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.configure',types.SimpleNamespace(verify_asset_import=lambda *a:{}))
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.control_readback',types.SimpleNamespace(verify=lambda *a:{},verify_ground=lambda *a:{}))
 monkeypatch.setattr(evaluator,'teacher_models',lambda *a:[Actor(),Actor(True)])
 def evaluate(*a,**kw):
  if runtime_fault:raise ValueError('reset fixture fault')
  return {'passed_envs':0,'accepted':False}, {'state':np.zeros((1,8,39))}
 monkeypatch.setattr(evaluator,'rollout',evaluate)
 monkeypatch.setattr(evaluator,'sha',lambda p:'a'*64)
 monkeypatch.setattr(sys,'path',list(sys.path));rng=torch.get_rng_state().clone()
 assert evaluator.execute(args,s)==int(runtime_fault)
 terminal=json.loads((out/'terminal_report.json').read_text())
 assert terminal['conditions'][0]['status']==('INCOMPLETE' if runtime_fault else 'COMPLETED') and terminal['conditions'][1]['status']=='NOT_RUN'
 assert close_codes==[int(runtime_fault)]
 assert seen[0]['initial_family']==s['student_evaluation']['cases'][0]['family']
 assert len(seen)==1 and seen[0]['teacher'] and torch.equal(rng,torch.get_rng_state())

def test_probe_first_interval_failure_preserves_both_pre_action_inputs():
 from native_stand.students.evaluator import rollout
 env=Scripted();a=Actor();m=Actor(True);a.train();m.train();rng=torch.get_rng_state().clone()
 def failure(action):raise RuntimeError('first interval physical fixture failure')
 env.step=failure
 with pytest.raises(RuntimeError,match='first interval') as caught:rollout(env,a,spec()['student_evaluation']['cases'][1],teacher=[Actor(),m])
 arrays=caught.value.student_pre_action_arrays
 assert arrays['student_actor_input'].shape==(1,8,31)
 assert arrays['motion_policy_input'].shape==(1,8,25) and arrays['motion_history_input'].shape==(1,8,125)
 assert 'root_post' not in arrays and 'first_episode_valid' not in arrays
 assert a.training and m.training and torch.equal(rng,torch.get_rng_state())
