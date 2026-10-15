FROZEN_TEST_SCOPE='PORTABLE'
import ast,copy,json
from pathlib import Path
from types import SimpleNamespace
import pytest,torch
from native_stand.students.motion_quality import configuration,QualityTermination,CAUSES,apply_reward
from native_stand.students.motion_tracking_reward import QUALITY_VERSION,REFINEMENT_VERSION,reward,configuration as reward_cfg,reward_fields
from test_motion31_training import inputs

def quality_inputs(n=2):
 return dict(posture=torch.zeros(n,10),height=torch.ones(n)*.34,wheel_offset=torch.zeros(n),contacts=torch.ones(n,2)*20,
  target=torch.zeros(n,2),controlled=torch.ones(n,dtype=torch.bool),valid=torch.ones(n,dtype=torch.bool))

def test_correctible_bad_posture_uses_consecutive_timer_grace_and_reset():
 c=configuration();q=QualityTermination(2,'cpu',c);data=quality_inputs();data['posture'][:,2:4]=.3;data['posture'][0,1]=.3
 rng=torch.get_rng_state().clone()
 for _ in range(50):assert not q.observe(**data)['terminated'].any()
 for _ in range(24):assert not q.observe(**data)['terminated'].any()
 result=q.observe(**data);assert result['terminated'].tolist()==[True,False]
 assert result['causes'][0,CAUSES.index('roll')]
 assert not q.observe(**data)['terminated'].any() # emit failure once
 q.reset(torch.tensor([0]));assert q.age[0]==0 and not q.sent[0]
 data['posture'][0,1]=0
 for _ in range(100):assert not q.observe(**data)['terminated'].any()
 assert torch.equal(rng,torch.get_rng_state())

def test_quality_timer_inference_rollout_then_eager_reset_multiple_cases():
 q=QualityTermination(2,'cpu',configuration());data=quality_inputs();data['posture'][:,2:4]=.3;data['posture'][0,1]=.3
 buffer=q.ticks; rng=torch.get_rng_state().clone()
 for _ in range(3):
  with torch.inference_mode():
   for _ in range(75):q.observe(**data)
  assert q.ticks is buffer and not torch.is_inference(q.ticks)
  q.reset(torch.arange(2))
  assert not q.ticks.any() and not q.age.any() and not q.sent.any()
 assert torch.equal(rng,torch.get_rng_state())

def test_extreme_geometry_terminates_without_grace_but_initialization_never_does():
 q=QualityTermination(2,'cpu',configuration());data=quality_inputs();data['posture'][:,2]=.41;data['posture'][:,3]=.30;data['controlled'][0]=False
 result=q.observe(**data);assert result['terminated'].tolist()==[False,True]
 assert result['causes'][1,CAUSES.index('leg_length_difference')]

def test_pitch_allows_acceleration_lean_and_contact_short_transients():
 q=QualityTermination(2,'cpu',configuration());data=quality_inputs();data['posture'][:,2:4]=.3;data['posture'][:,0]=.4;data['target'][1,0]=1
 for _ in range(75):result=q.observe(**data)
 assert result['terminated'].tolist()==[True,False]
 data['posture'][:,0]=0;data['contacts'][1]=0
 for _ in range(19):assert not q.observe(**data)['terminated'].any()
 assert q.observe(**data)['terminated'].tolist()==[False,True]

def test_geometry_and_posture_tails_keep_state_error_discrimination_and_dt_once():
 cfg=reward_cfg(QUALITY_VERSION);cfg2=reward_cfg(REFINEMENT_VERSION)
 data=inputs();data['leg_lengths']=torch.tensor([[.435,.30]]).expand(3,-1).clone().requires_grad_()
 out=reward(**data,config=cfg);old=reward(**data,config=cfg2)
 assert out['raw'].shape==(3,16) and out['fields']==reward_fields(cfg)
 out['total'].sum().backward();assert data['leg_lengths'].grad[:,0].lt(-.07).all()
 assert (out['density'][:,11]<old['density'][:,11]).all()
 torch.testing.assert_close(out['total'],out['density'].sum(-1)*.01)
 data=inputs();data['angles']=torch.tensor([[.5,.3]]).expand(3,-1).clone().requires_grad_()
 out=reward(**data,config=cfg);out['total'].sum().backward();assert data['angles'].grad.lt(0).all()

def test_failure_event_once_preserves_sample_and_overrides_normal_timeout():
 data=inputs();base=reward(**data,config=reward_cfg(REFINEMENT_VERSION));posture=torch.zeros(3,10);posture[:,2:4]=.3
 quality=torch.tensor([True,False,False]);physical=torch.tensor([False,True,False]);fault=torch.tensor([False,False,True])
 out=apply_reward(base,posture=posture,wheel_offset=data['wheel_offset'],leg_q=data['leg_q'],controlled=data['controlled'],valid=data['valid'],quality_failed=quality,physical_failed=physical,fault=fault,config=configuration())
 assert out['total'].tolist()==[-1.,-1.,0.] and data['controlled'].all()
 from native_stand.students.standing_survival_task import bootstrap_reward
 terminated=quality|physical|fault;truncated=torch.ones(3,dtype=torch.bool)
 assert torch.equal(bootstrap_reward(out['total'],terminated,truncated,torch.ones(3)*100,gamma=.99),out['total'])

def test_actual_runtime_quality_wrapper_wires_pre_reset_failure_and_timeout_without_isaac():
 tree=ast.parse(Path('src/native_stand/students/motion_quality_runtime.py').read_text())
 method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_get_dones')
 class Base:
  def _get_dones(self):return torch.zeros(2,dtype=torch.bool),torch.ones(2,dtype=torch.bool)
 namespace={'Base':Base,'torch':torch,'apply_reward':apply_reward}
 clsnode=ast.ClassDef(name='Wrapper',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=[method],decorator_list=[])
 exec(compile(ast.fix_missing_locations(ast.Module(body=[clsnode],type_ignores=[])),'<actual quality wrapper>','exec'),namespace)
 obj=namespace['Wrapper']();obj.motion_quality_reward_config=reward_cfg(QUALITY_VERSION);obj.motion_quality_ready=True;obj.num_envs=2;obj.device='cpu';obj.quality_config=configuration();obj.quality_monitor=QualityTermination(2,'cpu',obj.quality_config)
 obj.recovery_snapshot=torch.zeros(2,39);obj.recovery_snapshot[:,6]=.34;obj.recovery_snapshot[:,10:12]=20;obj.recovery_snapshot[:,29]=1
 obj.standing_snapshot=torch.zeros(2,10);obj.standing_snapshot[:,2:4]=.30;obj.standing_snapshot[0,2]=.41
 obj.motion_quality_snapshot=torch.zeros(2,7,dtype=torch.bool);obj.recovery_snapshot_valid=torch.zeros(2,dtype=torch.bool)
 obj.rise_hold=SimpleNamespace(offset=torch.zeros(2),task_failure=torch.zeros(2,dtype=torch.bool),normal_timeout=torch.ones(2,dtype=torch.bool))
 obj.target_xy=torch.zeros(2,2);obj.student_actor_valid=torch.ones(2,dtype=torch.bool);obj.student_event_snapshot=torch.zeros(2,5,dtype=torch.bool);obj.episode_result_snapshot=torch.zeros(2,5,dtype=torch.bool)
 obj.fsm=SimpleNamespace(mode=torch.ones(2,dtype=torch.long));obj.ids=list(range(6));obj.robot=SimpleNamespace(data=SimpleNamespace(joint_pos=SimpleNamespace(torch=torch.zeros(2,6))))
 base=reward(**inputs(),config=reward_cfg(REFINEMENT_VERSION));obj.student_reward_result={k:v[:2] if isinstance(v,torch.Tensor) else v for k,v in base.items()}
 term,trunc=obj._get_dones();assert term.tolist()==[True,False] and trunc.tolist()==[False,True]
 assert obj.student_actor_valid.all() and obj.recovery_snapshot[0,3]==1 and obj.student_event_snapshot[0,3]
 assert obj.student_reward_result['total'][0]==-1 and obj.motion_quality_snapshot[0,2] and obj.recovery_snapshot_valid.all()

def test_quality_reward_actual_curve_snapshot_version_and_finite():
 from native_stand.students.motion_reward_audit import audit
 from native_stand.students.motion_training import declaration,protocol
 from native_stand.students.training_recipe import validate_instance
 cfg=reward_cfg(QUALITY_VERSION);recipe=declaration(reward_version=QUALITY_VERSION);validate_instance(recipe,recipe['source_actor_sha256'])
 result=audit(cfg);assert not result['warnings'] and result['named_weights']['roll_excess']==-.5
 assert all(torch.isfinite(torch.tensor(r['state_error_derivative'])) for r in result['curves'])
 assert protocol(quality=True)['version']=='motion31_quality_assessment_v2'

def test_true_failure_transition_remains_in_real_CPU_ppo_storage_and_return():
 from native_stand.students.ppo import assemble
 from native_stand.students.model import Student
 from native_stand.students.motion_training import declaration
 from native_stand.recovery.controlled_ppo import KEY
 from tensordict import TensorDict
 import tempfile
 torch.set_num_threads(1)
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'actor.pt';actor=Student(version='multiskill_mcu_v2')
  torch.save({'interface_version':'multiskill_mcu_v2','role':'MotionZeroStudent','actor':actor.state_dict()},path)
  obs=TensorDict({'student_actor':torch.zeros(8,31),'student_critic':torch.zeros(8,49),KEY:torch.ones(8,1,dtype=torch.bool)},batch_size=[8])
  ppo=assemble(path,obs,steps_per_env=1,recipe=declaration(reward_version=QUALITY_VERSION))
  failed=torch.tensor([True]*4+[False]*4);values=torch.tensor([-1.]*4+[.1]*4)
  with torch.inference_mode():
   ppo.act(obs);ppo.process_env_step(obs,values,failed,{})
   ppo.compute_returns(obs)
  assert ppo.storage.observations[KEY].all()
  torch.testing.assert_close(ppo.storage.rewards[0,:4,0],torch.full((4,),-1.))
  torch.testing.assert_close(ppo.storage.returns[0,:4,0],torch.full((4,),-1.))
  ppo.update();assert ppo.mask_summary['valid_actor_samples']==8 and ppo.mask_summary['actor_optimizer_steps']>0

def test_quality_consumption_budget_refuses_reset_and_duplicate(monkeypatch,tmp_path):
 from native_stand.students import motion_quality_budget as budget
 c={'version':budget.VERSION,'parent_spec':str(tmp_path/'configs/old/spec.json'),'parent_spec_sha256':'a'*64,
  'historical_online_updates':50,'historical_wall_s':1370.,'original_online_limit':2000,'original_chain_wall_s':64800.}
 monkeypatch.setattr(budget,'consumption',lambda parent:copy.deepcopy(c))
 spec={'experiment':'new','motion_training':{'prior_consumption':c},'budget':{'smoke_updates':50,'formal_updates':1900,'chain_wall_s':63430.}}
 assert budget.verify(spec)==c
 bad=copy.deepcopy(spec);bad['budget']['formal_updates']=1901
 with pytest.raises(ValueError,match='online budget'):budget.verify(bad)
 bad=copy.deepcopy(spec);bad['budget']['chain_wall_s']=64800
 with pytest.raises(ValueError,match='wall reset'):budget.verify(bad)
 claims=Path(c['parent_spec']).parent.parent/'.motion_quality_consumption_claims';claims.mkdir(parents=True)
 (claims/('a'*64+'.json')).write_text(json.dumps({'destination':'other'}))
 with pytest.raises(ValueError,match='claimed'):budget.verify(spec)

def test_tracking_refinement_cannot_ignore_new_posture_quality_gate():
 from native_stand.students.motion_refinement import initial,advance
 policy=reward_cfg(QUALITY_VERSION)['refinement'];state=initial([[.5,0.]])
 checks={k:True for k in policy['required_checks']};checks.update(quality_complete_window=True,roll_quality=False,leg_balance_quality=True,wheel_alignment_quality=True,joint_mirror_quality=True)
 record={'case':{'command':[.5,0.,.34]},'per_env':[{'checks':checks,'tracking':{'MAE':.1,'direction':1.,'gain':1.}} for _ in range(8)]}
 for _ in range(4):state,decisions=advance(state,[record],policy)
 assert state[0]['mix']==0 and not decisions[0]['eligible']

def test_quality_full_chain_uncompressed_estimate_fits_without_assuming_compression():
 from native_stand.command_v6.tools.storage_budget import estimate
 spec={'reward':{'version':QUALITY_VERSION},'student_training':{'version':'student_motion31_training_v1','milestones':list(range(100,1901,100))},
  'student_evaluation':{'cases':[{'seconds':31.52}]*5},'control':{'policy_dt_s':.01},'evaluation':{'scored_envs':8},
  'budget':{'formal_updates':1900,'smoke_updates':50},'ppo':{'envs':512},'artifacts':{'storage_max_bytes':2*2**30,'terminal_reserve_bytes':128*2**20}}
 rows=[estimate(spec,p) for p in ('source_eval','smoke','formal')]
 total=sum(r['estimated_artifact_bytes'] for r in rows)+max(r['atomic_temp_peak_bytes'] for r in rows)+rows[0]['terminal_reserve_bytes']
 assert total<2*2**30
