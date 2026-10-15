FROZEN_TEST_SCOPE='PORTABLE'
import copy,ast
from pathlib import Path
import pytest,torch
from native_stand.students.motion_course import configuration,stage_config,commands,advance,extend_mixture,choose,VERSION

def candidate(stage,update,passed=True):
 return {'stage':stage,'update':update,'complete_matrix':True,'checkpoint':f'model_{update}','sha256':str(update),
 'evaluations':[{'case':{'command':v+[.34]},'path':f'eval_{i}.json','sha256':'a'*64,'per_env':[{'env':i,'accepted':passed} for i in range(8)]} for i,v in enumerate(commands(stage))]}

def test_stages_no_unlocked_high_endpoints_and_exact_balanced512():
 for stage,total in enumerate((7,9,11,13)):
  s=stage_config(stage);assert len(s['commands'])==total and len(s['sampling_slots'])==512 and sum(s['slot_counts'])==512
  assert s['slot_counts'][0]==128 and s['slot_counts'][-2:]==[96,96] and sum(s['slot_counts'][1:-2])==192
  assert all(s['slot_counts'][i]==s['slot_counts'][i+1] for i in range(1,total,2))
  if stage<2:assert not any(v[1] for v in s['commands'])
 assert [0.,1.5] not in commands(2) and [0.,1.5] in commands(3)
 assert [2.,0.] not in commands(0)

def test_two_complete_actual_intervals_per_stage_unlock_without_budget_reset():
 state={'stage':0,'stage_started_update':0,'last_evaluation_update':-1,'consecutive_passes':0,'accepted_by_stage':{}}
 for i in range(4):
  u=500*i+250;state,d=advance(state,candidate(i,u));assert not d['advanced'] and not d['stage_passed']
  u=500*i+500;state,d=advance(state,candidate(i,u));assert d['stage_passed'] and d['advanced']==(i<3)
  assert state['accepted_by_stage'][str(i)]['update']==u
 assert d['all_stages_passed']

def test_failure_missing_env_old_endpoint_regression_prevents_unlock():
 base={'stage':0,'stage_started_update':0,'last_evaluation_update':-1,'consecutive_passes':0,'accepted_by_stage':{}}
 state,_=advance(base,candidate(0,250));c=candidate(0,500);c['evaluations'][0]['per_env'][0]['accepted']=False
 state,d=advance(state,c);assert not d['stage_passed'] and state['consecutive_passes']==0
 c=candidate(0,750);c['evaluations'][-1]['per_env'].pop();state,d=advance(state,c);assert not d['stage_passed']
 with pytest.raises(ValueError):advance(state,candidate(1,1000))

def test_mixture_retains_exact_old_targets_and_new_starts_wide():
 old=[{'target':[.5,0.],'mix':.75,'consecutive_eligible':1}];result=extend_mixture(old,[[.5,0.],[1.5,0.],[0.,1.]])
 assert result[0]==old[0] and result[1]['mix']==result[2]['mix']==0
 result[0]['mix']=0;assert old[0]['mix']==.75

def test_recipe_version_explicit_and_yaw_reward_direction_no_translation_coupling():
 from native_stand.students.motion_training import declaration,short_wiring
 from native_stand.students.motion_tracking_reward import QUALITY_VERSION,reward,configuration as reward_config
 from native_stand.students.training_recipe import validate_instance
 r=declaration('a'*64,reward_version=QUALITY_VERSION);r.update(course_version=VERSION,course_stage=0,smoke_wiring=short_wiring())
 assert validate_instance(r,'a'*64)==r
 n=3;z=torch.zeros(n);yes=torch.ones(n,dtype=torch.bool);targets=torch.tensor([[0.,1.],[0.,1.],[0.,1.]])
 data=dict(command=torch.cat((targets,torch.full((n,1),.34)),-1),target=targets,velocity=torch.zeros(n,3),yaw=torch.tensor([-1.,0.,1.]),height=z+.34,angles=torch.zeros(n,2),contacts=torch.ones(n,2)*20,leg_q=torch.zeros(n,4),wheel_offset=z,leg_lengths=torch.ones(n,2)*.3,applied_torque=torch.zeros(n,6),previous_targets=torch.zeros(n,6),executed_targets=torch.zeros(n,6),controlled=yes,valid=yes,physical_failure=~yes,fault=~yes,config=reward_config(QUALITY_VERSION))
 out=reward(**data);assert out['total'][0]<out['total'][1]<out['total'][2] and out['total'][2]>0
 assert out['density'][:,1].equal(torch.full((n,),4.)) # zero translation is rewarded while yaw learns

def test_runtime_course_branch_and_stop_do_not_bypass_shared_ppo():
 root=Path(__file__).resolve().parents[1]/'src/native_stand/students';runner=(root/'motion_runner.py').read_text();ast.parse(runner)
 for name in ('restore_course','advance_course','stage_budget_exhausted','retention_baseline','extend_mixture','selection_fn') :assert name in runner
 assert "source_records=candidates[0]['evaluations']" in runner
 assert 'ppo.update()' in runner and 'Ledger(args.spec.with_name' in runner

def test_actual_full_state_restore_cpu_no_optimizer_step():
 from native_stand.students.model import Student
 from native_stand.students.motion_course_requests import restore
 from native_stand.students.resume import rng_state
 from types import SimpleNamespace
 a=Student(True,version='multiskill_mcu_v2');v=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1');a.log_std.requires_grad_(False)
 opt=torch.optim.Adam([*a.parameters(),*v.parameters()],lr=3e-5)
 # Fabricate serialized Adam moments, without running an optimizer update.
 for p in [*a.parameters(),*v.parameters()]:
  if p.requires_grad:opt.state[p]={'step':torch.tensor(7.),'exp_avg':torch.ones_like(p)*.01,'exp_avg_sq':torch.ones_like(p)*.02}
 source={'actor':copy.deepcopy(a.state_dict()),'critic':copy.deepcopy(v.state_dict()),'optimizer':copy.deepcopy(opt.state_dict()),'training_rng':rng_state(),'reward_refinement_state':[{'target':c,'mix':.75 if c==[.5,0.] else 0.,'consecutive_eligible':0} for c in configuration()['source_capabilities']]}
 source['training_rng']['torch_cuda']=None
 actor=Student(True,version='multiskill_mcu_v2');critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1');actor.log_std.requires_grad_(False)
 ppo=SimpleNamespace(actor=actor,critic=critic,optimizer=torch.optim.Adam([*actor.parameters(),*critic.parameters()],lr=3e-5))
 restore(ppo,source,{},'formal')
 assert all(torch.equal(t,source['actor'][k]) for k,t in actor.state_dict().items())
 assert all(torch.equal(t,source['critic'][k]) for k,t in critic.state_dict().items())
 actual=ppo.optimizer.state_dict();assert actual['param_groups']==source['optimizer']['param_groups']
 assert all(torch.equal(t,actual['state'][index][name]) for index,state in source['optimizer']['state'].items() for name,t in state.items())
 assert ppo.reward_refinement_state[1]['mix']==.75 and len(ppo.reward_refinement_state)==7 and ppo.reward_refinement_state[-1]['mix']==0

def test_new_yaw_command_actor_and_critic_explicit_layout():
 from native_stand.students.motion_training import effective
 from native_stand.students.motion_privileged import critic_input
 target=torch.tensor([[0.,1.5],[0.,-1.5]])
 command=effective(target,torch.full((2,),15.))
 actor=torch.zeros(2,31);actor[:,22:25]=command/torch.tensor([4.,4.,.5]);actor[:,25]=1
 result=critic_input(actor,torch.ones(2)*.34,torch.zeros(2,3),torch.ones(2,2)*20,command,torch.tensor([1.,-1.]),torch.ones(2)*15,torch.ones(2,dtype=torch.bool),torch.zeros(2,6))
 assert torch.equal(result[:,22:25],actor[:,22:25]) and result.shape==(2,49)
 assert actor[0,23]==.375 and actor[1,23]==-.375
 assert torch.equal(result[:,37:39],command[:,:2]/4)

def test_course_best_is_stage_scoped_and_source_never_new_or_final_acceptance():
 source={'update':0,'stage':0,'per_env':[{'accepted':True,'survival_passed':True,'tracking':{'MAE':0}}],'complete_matrix':True,'checkpoint':'source','sha256':'source'}
 c={'update':500,'stage':0,'per_env':[{'accepted':True,'survival_passed':True,'tracking':{'MAE':.1}}],'complete_matrix':True,'checkpoint':'new0','sha256':'new0'}
 accepted={'0':{'checkpoint':'new0','sha256':'new0'}}
 result=choose([source,c],accepted);assert result['best_new']['checkpoint']=='new0' and result['accepted_candidate'] is None and '0' in result['accepted_by_stage']
 c2={**c,'stage':1,'update':750,'checkpoint':'new1','sha256':'new1','per_env':[{'accepted':False,'survival_passed':True,'tracking':{'MAE':.5}}]}
 result=choose([source,c,c2],accepted);assert result['best_new']['checkpoint']=='new1' and result['accepted_candidate'] is None

def test_effective_stage_view_preserves_frozen_spec_and_versioned_recipe():
 from native_stand.students.motion_course import effective_spec
 from native_stand.students.motion_training import declaration,short_wiring
 from native_stand.students.motion_tracking_reward import QUALITY_VERSION
 from native_stand.students.training_recipe import validate_instance
 recipe=declaration('a'*64,reward_version=QUALITY_VERSION);recipe.update(course_version=VERSION,course_stage=0,smoke_wiring=short_wiring())
 spec={'motion_training':{'stage':0},'student_training':recipe,'ppo':{'envs':512},'curriculum':{'stages':[stage_config(0)]},'student_evaluation':{'cases':[{'checkpoint':'frozen','sha256':'a'*64,'command':[0.,0.,.34]}]}}
 original=copy.deepcopy(spec)
 for stage in range(4):
  effective=effective_spec(spec,stage);assert spec==original
  assert effective['student_training']['stage']==effective['student_training']['course_stage']==stage
  assert validate_instance(effective['student_training'],'a'*64)==effective['student_training']
  assert [r['command'][:2] for r in effective['student_evaluation']['cases']]==commands(stage)
  assert sum(effective['curriculum']['stages'][0]['slot_counts'])==512
