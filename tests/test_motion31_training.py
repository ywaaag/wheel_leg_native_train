FROZEN_TEST_SCOPE='PORTABLE'
import copy,json
import pytest,torch
from native_stand.students.motion_training import commands,stage_config,effective,score,choose,compare_source,declaration
from native_stand.students.motion_tracking_reward import reward,configuration,FIELDS
from native_stand.students.motion_privileged import critic_input,contract

def inputs(v=0.,command=0.,yaw=0.,yaw_command=0.):
 n=3;z=torch.zeros(n);yes=torch.ones(n,dtype=torch.bool)
 return dict(command=torch.tensor([[command,yaw_command,.34]]).expand(n,-1).float(),target=torch.tensor([[command,yaw_command]]).expand(n,-1).float(),
  velocity=torch.tensor([[v,0.,0.]]).expand(n,-1).float(),yaw=z+yaw,height=z+.34,angles=torch.zeros(n,2),contacts=torch.ones(n,2)*20,
  leg_q=torch.zeros(n,4),wheel_offset=z,leg_lengths=torch.ones(n,2)*.3,applied_torque=torch.zeros(n,6),previous_targets=torch.zeros(n,6),executed_targets=torch.zeros(n,6),controlled=yes,valid=yes,physical_failure=~yes,fault=~yes)

@pytest.mark.parametrize('command',[-4.,-2.,-1.,-.5,0.,.5,1.,2.,4.])
def test_reward_target_is_best_both_signs_and_dt_once(command):
 ideal=reward(**inputs(command,command));wrong=reward(**inputs(command-1,command))
 assert ideal['total'].min()>wrong['total'].max()
 torch.testing.assert_close(ideal['total'],ideal['density'].sum(-1)*.01)
 assert tuple(ideal['fields'])==FIELDS and ideal['events'].eq(0).all()

def test_far_field_huber_has_nonzero_state_derivative_and_no_yaw_speed_coupling():
 data=inputs(-.9,1.);data['velocity']=data['velocity'].clone().requires_grad_();out=reward(**data);out['total'].sum().backward()
 assert data['velocity'].grad[:,0].gt(0).all()
 ideal=reward(**inputs(0.,0.,4.,4.));bad=reward(**inputs(0.,0.,3.,4.))
 assert ideal['total'].min()>bad['total'].max() and ideal['raw'][:,2].eq(1).all()
 assert torch.exp(torch.tensor(-1./.04))<1e-10

def test_modes_penalize_cross_axis_without_multiplying_tracking():
 straight=inputs(.5,.5,yaw=.3);spin=inputs(.3,0.,yaw=1.,yaw_command=1.)
 assert reward(**straight)['raw'][0,2]<.4
 assert reward(**spin)['raw'][0,1]<.4
 assert reward(**spin)['raw'][0,2]==1

def test_episode_target_not_ramp_controls_zero_normalization_and_masks():
 zero=inputs(.3);nonzero=inputs(.3,.5);nonzero['command']=nonzero['command'].clone();nonzero['command'][:,0]=0
 assert reward(**zero)['raw'][0,1]<reward(**nonzero)['raw'][0,1]
 zero['controlled'][0]=False;zero['fault'][1]=True;zero['physical_failure'][2]=True
 assert reward(**zero)['total'].eq(0).all()

@pytest.mark.parametrize('stage',range(7))
def test_fixed_64_slots_whitelist_and_balanced_signs(stage):
 cfg=stage_config(stage);assert len(cfg['sampling_slots'])==64 and cfg['slot_counts'][0]==16
 assert sum(cfg['slot_counts'])==64 and cfg['slot_counts'][1::2]==cfg['slot_counts'][2::2]
 assert cfg['commands']==commands(stage)
 from native_stand.command_v6.domain.command_sampling import resolve
 assert resolve(cfg,64)['fixed_slots']==cfg['sampling_slots']
 if stage<4:assert all(yaw==0 for vx,yaw in cfg['commands'])
 assert max(abs(v) for row in cfg['commands'] for v in row)<=4

def test_parallel512_preserves_cohort_proportions_and_separate_evaluation_slots():
 cfg=stage_config(0,512);assert cfg['slot_counts']==[128,96,96,96,96]
 assert len(cfg['sampling_slots'])==512
 assert cfg['weights']==stage_config(0,64)['weights']
 from native_stand.command_v6.domain.command_sampling import resolve
 resolve(cfg,512)
 with pytest.raises(ValueError):resolve(cfg,64)
 from native_stand.command_v6.domain.execution_plan import samples_per_update
 assert samples_per_update({'ppo':{'envs':512,'steps_per_env':128}})==65536

def test_parallel512_CPU_ppo_storage_mask_is_not_8192(tmp_path):
 from native_stand.students.model import Student
 from native_stand.students.ppo import assemble
 from native_stand.recovery.controlled_ppo import KEY
 from tensordict import TensorDict
 torch.set_num_threads(1);path=tmp_path/'actor.pt';actor=Student(version='multiskill_mcu_v2')
 torch.save({'interface_version':'multiskill_mcu_v2','role':'MotionZeroStudent','actor':actor.state_dict()},path)
 obs=TensorDict({'student_actor':torch.randn(512,31),'student_critic':torch.randn(512,49),KEY:torch.ones(512,1,dtype=torch.bool)},batch_size=[512])
 ppo=assemble(path,obs,steps_per_env=2,recipe=declaration());std=ppo.actor.log_std.clone()
 with torch.inference_mode():
  for _ in range(2):
   action=ppo.act(obs);ppo.process_env_step(obs,action[:,0]+1,torch.zeros(512,dtype=torch.bool),{})
  ppo.compute_returns(obs)
 ppo.update();assert ppo.mask_summary['total_transitions']==1024 and ppo.mask_summary['valid_actor_samples']==1024
 assert torch.equal(std,ppo.actor.log_std)

def test_motion_storage_estimate_uses_npz_and_five_cases(tmp_path):
 from native_stand.command_v6.tools.storage_budget import estimate,check
 spec={'student_training':{'version':'student_motion31_training_v1','milestones':list(range(100,2001,100))},'student_evaluation':{'cases':[{'seconds':31.52}]*5},'control':{'policy_dt_s':.01},'evaluation':{'scored_envs':8},'budget':{'formal_updates':2000},'ppo':{'envs':512},'artifacts':{'storage_max_bytes':2*2**30,'terminal_reserve_bytes':128*2**20}}
 p=estimate(spec,'formal');assert p['schema_version']=='motion_student_npz_budget_v1' and p['estimated_artifact_bytes']<2*2**30
 assert check(spec,tmp_path,'formal')['status']=='PASS'

def test_runner_charges_exact_ledger_after_actual_optimizer_step():
 # AST structural contract complements real Ledger fixtures without Isaac.
 import ast
 from pathlib import Path
 tree=ast.parse(Path('src/native_stand/students/motion_runner.py').read_text())
 charges=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='charge']
 assert len(charges)==1 and isinstance(charges[0].args[0],ast.Attribute) and charges[0].args[0].attr=='attempt_id'

def test_recovery_lifecycle_requires_explicit_bound_evidence():
 from native_stand.command_v6.tools.run_state import transition
 assert transition('SOURCE_EVAL','FORMAL',continuation={'version':'verified_motion_wiring_recovery_v1','verified':True,'checkpoint_sha256':'a'*64})=='FORMAL'

def test_recovery_consumes_real_smoke_without_changing_old_ledger(tmp_path,monkeypatch):
 from native_stand.students.motion_wiring_recovery import verify,VERSION
 from native_stand.students.data import sha
 from native_stand.command_v6 import wiring
 monkeypatch.setattr(wiring,'validate_persisted_certificate',lambda *a:{'status':'PASSED'})
 folder=tmp_path/'config';folder.mkdir();parent=folder/'spec.json';run=tmp_path/'old_run';run.mkdir()
 old={k:{} for k in ('asset_path','asset_sha256','student_interface','observation','history','action','control','ground','termination','ppo','reward','curriculum','motion_assessment','student_training','recovery','performance','device')}
 old.update(source_checkpoint='source.pt',source_sha256='a'*64,seed=1,budget={'chain_wall_s':64800},student_evaluation={'cases':[{'command':[0,0,.34]}]})
 parent.write_text(json.dumps(old));ledger=folder/'budget.json';ledger.write_text(json.dumps({'used':{'smoke':0},'attempts':{'s':{'phase':'smoke','status':'COMPLETED'}}}))
 (run/'chain_terminal_report.json').write_text(json.dumps({'status':'FAILED','failure':"ValueError('insufficient output storage before reserve')",'chain_wall_s':2000}))
 for phase in ('source_eval','smoke'):
  p=run/phase;p.mkdir();trace=p/'trace.npz';trace.write_bytes(b'identity-bound trace')
  raw={'trace':{'path':'trace.npz','sha256':sha(trace)},'protocol':{},'per_env':[{}]*8,'case':{'command':[0,0,.34]}}
  result=p/'evaluation_00.json';result.write_text(json.dumps(raw));records=[{'path':result.name,'sha256':sha(result)}]
  terminal={'status':'COMPLETED','evaluations':records,'actual_updates':50 if phase=='smoke' else 0}
  (p/'terminal_report.json').write_text(json.dumps(terminal));(p/'candidate_registry.json').write_text('[]')
 smoke=run/'smoke';(smoke/'progress.json').write_text(json.dumps({'actual_updates':50}));(smoke/'wiring_certificate.json').write_text('{}');(smoke/'metrics.jsonl').write_text(''.join(json.dumps({'update':i})+'\n' for i in range(1,51)))
 before=ledger.read_bytes();inputs={str(p):sha(p) for p in [parent,ledger,*run.rglob('*')] if p.is_file()}
 spec=copy.deepcopy(old);spec['budget']={'smoke_updates':0,'formal_updates':2000,'chain_wall_s':62800}
 spec['experiment']='recovery';spec['motion_training']={'wiring_reuse':{'version':VERSION,'parent_spec':str(parent),'parent_run':str(run),'inputs':inputs,'historical_smoke_updates':50,'historical_wall_s':2000,'original_online_limit':2050}}
 assert verify(spec)['historical_ledger_discrepancy'] and ledger.read_bytes()==before
 bad=copy.deepcopy(spec);bad['budget']['smoke_updates']=1
 with pytest.raises(ValueError,match='budget'):verify(bad)
 bad=copy.deepcopy(spec);bad['reward']={'changed':True}
 with pytest.raises(ValueError,match='behavior'):verify(bad)
 bad=copy.deepcopy(spec);bad['budget']['chain_wall_s']=64800
 with pytest.raises(ValueError,match='wall'):verify(bad)

def test_training_hold_majority_schedule_and_actor_command_slots():
 age=torch.arange(3000)*.01;target=torch.tensor([[1.,0.]]).expand(3000,-1);cmd=effective(target,age,True)
 assert cmd[150:2700,0].eq(1).all() and cmd[:,2].eq(.34).all()
 assert ((age>=1.5)&(age<27.)).float().mean()>.8
 from native_stand.students.mcu_interface import actor_input,task
 x=actor_input(torch.zeros(3000,22),task('Motion',cmd))
 torch.testing.assert_close(x[:,22:25],cmd/cmd.new_tensor([4,4,.5]));assert x[:,25].eq(1).all() and x[:,26].eq(0).all()

def test_named49_critic_preserves_actor_and_distinguishes_standing_layout():
 x=torch.zeros(2,31);z=torch.zeros(2);v=torch.tensor([[1.,2.,3.]]).expand(2,-1);c=torch.tensor([[.5,0,.34]]).expand(2,-1)
 result=critic_input(x,z+.34,v,torch.ones(2,2)*100,c,z,z+30,z.bool(),torch.tensor([[40,40,5.5,40,40,5.5]]).expand(2,-1))
 assert result.shape==(2,49);torch.testing.assert_close(result[:,:31],x);torch.testing.assert_close(result[:,32:35],v)
 assert result[:,35:37].eq(1).all() and result[:,-6:].eq(1).all()
 from native_stand.students.mcu_interface import contract as default
 from native_stand.students.standing_zero_privileged import contract as standing
 assert default()['critic_dim']==40 and contract()!=standing()

def trajectory(command):
 s=torch.zeros(3000,39);s[:,6]=.34;s[:,10:12]=20;s[:,13]=.1;s[:,29]=1
 p=torch.zeros(3000,10);p[:,2:4]=.3;g=torch.zeros(3000,13);g[:,7]=-1;world=torch.zeros(3000,3)
 axis=9 if command[1] else 7;s[1000:1800,axis]=command[1] or command[0]
 return s,p,g,torch.ones(3000,dtype=torch.bool),world

@pytest.mark.parametrize('command',[[0.,0.],[.5,0.],[-1.,0.],[4.,0.],[0.,-4.]])
def test_complete_hold_and_parking_are_separate(command):
 args=trajectory(command);r=score(*args,command);assert r['accepted'] and r['standing_quality_certified'] is False
 assert r['tracking']['parking_horizontal_mean_mps']==0
 args[4][2600:,0]=.5;bad=score(*args,command);assert not bad['accepted'] and 'parking' in bad['failed_checks']
 short=score(*(a[:-1] for a in args),command);assert not short['accepted']

def candidate(update,good=True):
 r=score(*trajectory([1.,0.]),[1.,0.]);r['env_id']=0;r['accepted']=good
 return {'update':update,'per_env':[r]*40,'complete_matrix':True}

def test_source_guard_unknown_and_repeat_confirmation_cannot_stitch():
 source=candidate(0);a=candidate(100);b=candidate(200)
 a['per_env']=copy.deepcopy(a['per_env']);a['per_env'][0]['tracking']['pitch_hold_abs_mean_rad']=.01
 compare_source(a,source);assert not a['per_env'][0]['accepted']
 assert choose([source,candidate(100)])['accepted_candidate'] is None
 assert choose([source,candidate(100),candidate(200)])['accepted_candidate'] is not None
 assert choose([source,candidate(100),candidate(200,False),candidate(300)])['accepted_candidate'] is None
 incomplete=candidate(200);incomplete['complete_matrix']=False
 assert choose([source,candidate(100),incomplete])['accepted_candidate'] is None

def test_real_cpu_PPO_update_actor_critic_and_fixed_std(tmp_path):
 from native_stand.students.model import Student
 from native_stand.students.ppo import assemble
 from native_stand.recovery.controlled_ppo import KEY
 from tensordict import TensorDict
 torch.manual_seed(7);torch.set_num_threads(1)
 actor=Student(version='multiskill_mcu_v2');path=tmp_path/'actor.pt'
 torch.save({'interface_version':'multiskill_mcu_v2','role':'MotionZeroStudent','actor':actor.state_dict()},path)
 obs=TensorDict({'student_actor':torch.randn(4,31),'student_critic':torch.randn(4,49),KEY:torch.ones(4,1,dtype=torch.bool)},batch_size=[4])
 ppo=assemble(path,obs,steps_per_env=4,recipe=declaration());a=[p.clone() for p in ppo.actor.parameters()];c=[p.clone() for p in ppo.critic.parameters()];std=ppo.actor.log_std.clone()
 for _ in range(4):
  with torch.inference_mode():
   action=ppo.act(obs);ppo.process_env_step(obs,action[:,0].detach()+1,torch.zeros(4,dtype=torch.bool),{})
 with torch.inference_mode():ppo.compute_returns(obs)
 ppo.update()
 assert any(not torch.equal(x,y) for x,y in zip(a,ppo.actor.parameters()))
 assert any(not torch.equal(x,y) for x,y in zip(c,ppo.critic.parameters()))
 assert torch.equal(std,ppo.actor.log_std) and ppo.optimizer.param_groups[0]['lr']==3e-5

def test_task_budget_no_duplicates_or_overrun(tmp_path):
 from native_stand.students.motion_training_requests import audit_task
 path=tmp_path/'spec.json';path.write_text(json.dumps({'experiment':'test','motion_training':{'task_manifest_sha256':'a'*64}}));(tmp_path/'budget.json').write_text(json.dumps({'experiment':'test','used':{'formal':1950},'limits':{'formal':2000},'attempts':{}}))
 task={'formal_limit':2000,'blocks':[{'index':1,'spec':str(path)}]};current={'block_index':1,'task_manifest_sha256':'a'*64}
 assert audit_task(task,tmp_path,current)['remaining_formal_updates']==50
 task['blocks']*=2
 with pytest.raises(ValueError,match='duplicate'):audit_task(task,tmp_path,current)

def test_new_block_plan_counts_budget_before_files_exist(tmp_path):
 from native_stand.students.motion_training_requests import audit_task
 task={'formal_limit':2000,'blocks':[{'index':1,'spec':str(tmp_path/'missing/spec.json')}]}
 with pytest.raises(ValueError,match='cumulative'):audit_task(task,tmp_path,{'block_index':1},planned_formal=2001)

def test_append_only_registry_missing_or_wrong_task_is_not_budget(tmp_path):
 from native_stand.students.motion_training_requests import audit_task
 registry=tmp_path/'registry';registry.mkdir();task={'formal_limit':2000,'registry_dir':str(registry)}
 cfg={'block_index':1,'spec_path':str(tmp_path/'spec.json'),'task_manifest_sha256':'a'*64}
 with pytest.raises(ValueError,match='not registered'):audit_task(task,tmp_path,cfg)
 assert audit_task(task,tmp_path,cfg,planned_formal=300,allow_planned=True)['remaining_formal_updates']==2000
 (registry/'block_0001.json').write_text(json.dumps({'index':1,'spec':cfg['spec_path']}))
 (tmp_path/'spec.json').write_text(json.dumps({'experiment':'x','motion_training':{'task_manifest_sha256':'b'*64}}))
 (tmp_path/'budget.json').write_text(json.dumps({'experiment':'x','used':{'formal':100},'limits':{'formal':300},'attempts':{}}))
 with pytest.raises(ValueError,match='identity'):audit_task(task,tmp_path,cfg)

def test_motion_no_smoke_continuation_requires_bound_49_state(tmp_path):
 from native_stand.command_v6.tools.run_state import transition
 assert transition('SOURCE_EVAL','FORMAL',continuation={'version':'verified_motion_continuation_v1','verified':True,'checkpoint_sha256':'a'*64})=='FORMAL'
 with pytest.raises(ValueError):transition('SOURCE_EVAL','FORMAL')
 from native_stand.command_v6.wiring import completed_smoke
 assert not completed_smoke({}, {'motion_training':{'resume':{'parent_spec':str(tmp_path/'missing')}}})

def test_chain_wall_larger_than_phase_does_not_reject_before_reserve(tmp_path,monkeypatch):
 from native_stand.command_v6 import stand_chain
 import time
 class Ready(dict):pass
 ready=Ready(status='PASS');spec=tmp_path/'spec.json';spec.write_text(json.dumps({'ppo':{'envs':64,'steps_per_env':128},'budget':{'source_eval_wall_s':3600,'chain_wall_s':14400}}))
 (tmp_path/'manifest.json').write_text(json.dumps({'submitted_unix_s':time.time()}))
 monkeypatch.setattr(stand_chain,'check',lambda *a:ready)
 class ReachedReserve(Exception):pass
 class Ledger:
  def __init__(self,*a):pass
  def reserve(self,*a,**k):raise ReachedReserve('owned CPU boundary; no actual reservation')
 monkeypatch.setattr(stand_chain,'Ledger',Ledger)
 with pytest.raises(ReachedReserve):stand_chain.run_phase(spec,'source_eval',tmp_path/'source_eval')

def test_explicit_recipe_and_legacy_default_unchanged():
 from native_stand.students.training_recipe import validate_instance,declaration as base
 r=declaration();assert validate_instance(r,r['source_actor_sha256'])==r
 assert base()['version']!='student_motion31_training_v1'
 r['reward']['linear_denominator']=.04
 with pytest.raises(ValueError):validate_instance(r,r['source_actor_sha256'])

def test_runtime_actor_command_survives_legacy_clock_and_cached_terminal(monkeypatch):
 """Execute the actual observation methods with a deliberately hostile legacy getter."""
 import importlib,sys,types
 from native_stand.students.interface import History
 from native_stand.students.mcu_interface import PolicyClock
 class Base:
  def _get_observations(self):self.command.fill_(99.);return {}
 monkeypatch.setitem(sys.modules,'native_stand.recovery.runtime',types.SimpleNamespace(RecoveryEnv=Base))
 monkeypatch.setitem(sys.modules,'isaaclab.utils.math',types.SimpleNamespace(quat_apply_inverse=lambda q,v:v))
 saved={name:sys.modules.pop(name,None) for name in ('native_stand.students.runtime','native_stand.students.motion_runtime')}
 try:
  Env=importlib.import_module('native_stand.students.motion_runtime').MotionStudentEnv;e=Env.__new__(Env);n=2;z=torch.zeros(n)
  wrap=lambda x:types.SimpleNamespace(torch=x)
  data=types.SimpleNamespace(root_quat_w=wrap(torch.zeros(n,4)),root_lin_vel_w=wrap(torch.zeros(n,3)),joint_pos=wrap(torch.zeros(n,6)),joint_vel=wrap(torch.zeros(n,6)),applied_torque=wrap(torch.zeros(n,6)))
  e.robot=types.SimpleNamespace(data=data);e.num_envs=n;e.ids=list(range(6));e.reference=torch.zeros(n,6);e.device='cpu'
  e.motion_training_enabled=True;e.motion_manual_command=None;e.motion_config=declaration();e.curriculum_training=True;e.target_xy=torch.tensor([[1.,0.],[-1.,0.]])
  e.command=torch.zeros(n,3);e.student_ready=True;e.student_role='MotionZeroStudent';e.interface_version='multiskill_mcu_v2';e.student_command_height=.34
  e.fsm=types.SimpleNamespace(mode=torch.zeros(n,dtype=torch.long));e.student_history=History(n,'cpu');e.mcu_clock=PolicyClock(n)
  e.executed_leg=torch.zeros(n,4);e.executed_wheel=torch.zeros(n,2);e.episode_length_buf=torch.full((n,),200);e.step_dt=.01
  e.rise_hold=types.SimpleNamespace(episode=types.SimpleNamespace(steps=torch.full((n,),200)),dwell=z,age=z,count=z)
  e.root_height=z+.34;e.contact_force=torch.ones(n,2)*20;e.yaw=z;e.critic_privileged_version='motion_privileged49_v1';e.student_obs=None
  e._motion_state=lambda:(torch.zeros(n,3),torch.tensor([[0.,-1.,0.]]).expand(n,-1))
  obs=e._get_observations();torch.testing.assert_close(obs['student_actor'][:,22],torch.tensor([.25,-.25]));assert obs['student_critic'].shape==(n,49)
  # Same policy timestamp is legal for a terminal-value getter; new command
  # must still replace cached Actor task fields.
  e.rise_hold.episode.steps.fill_(2750)
  obs=e._get_observations();torch.testing.assert_close(obs['student_actor'][:,22],torch.tensor([.125,-.125]))
 finally:
  for name,value in saved.items():
   sys.modules.pop(name,None)
   if value is not None:sys.modules[name]=value
