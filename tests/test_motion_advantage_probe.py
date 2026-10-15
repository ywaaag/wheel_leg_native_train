FROZEN_TEST_SCOPE='PORTABLE'
import importlib.util
from pathlib import Path
import numpy as np
import pytest


def reviewer():
    path=Path(__file__).resolve().parents[1]/'scripts/review_motion31_advantage_probe.py'
    s=importlib.util.spec_from_file_location('motion_advantage_review',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def test_reviewer_real_gae_and_centering_not_causal():
    t,n=3,2
    raw=np.array([[1,2],[3,4],[5,6]],dtype=np.float32)
    value=np.zeros((t,n,1),np.float32);returns=raw[...,None]
    rewards=raw.copy();rewards[:-1]-=.99*.95*raw[1:]
    a={'actor_valid':np.ones((t,n),bool),'advantage_raw':returns,'advantage_normalized':((raw-raw.mean())/raw.std(ddof=1))[...,None],
       'value':value,'returns':returns,'storage_reward':rewards[...,None],'terminated':np.zeros((t,n),bool),'truncated':np.zeros((t,n),bool),
       'bootstrap_last_value':np.zeros((n,1),np.float32),'actor_input':np.zeros((t,n,31),np.float32),'command':np.zeros((t,n,3),np.float32),
       'posture_pre_reset':np.zeros((t,n,6),np.float32),'action_raw':np.zeros((t,n,6),np.float32),'target':np.zeros((t,n,2),np.float32),'state_pre_reset':np.zeros((t,n,39),np.float32),'episode_age_s':np.ones((t,n),np.float32)*5,
       'command_index':np.zeros((t,n),np.int64),'reward_dt':np.zeros((t,n,1),np.float32)}
    spec={'ppo':{'gamma':.99,'lam':.95},'student_training':{'train_schedule_s':[.5,1,25.5,1]},'curriculum':{'stages':[{'commands':[[0,0]]}]}}
    result=reviewer().analyze(a,{'reward_names':['zero']},spec)
    assert result['checks_passed'] and result['groups'][0]['sign_flip_fraction']==.5
    a['actor_input'][...,22]=1
    assert not reviewer().analyze(a,{'reward_names':['zero']},spec)['checks_passed']


def test_probe_unknown_fields_and_contract_change_rejected(tmp_path,monkeypatch):
    import json
    from native_stand.students.motion_advantage_probe import declaration,validate
    from native_stand.students.data import sha
    import native_stand.students.requests as requests
    monkeypatch.setattr(requests,'validate',lambda s:[])
    cp=tmp_path/'source';cp.write_bytes(b'fake')
    original={'source_checkpoint':str(cp),'source_sha256':sha(cp),'action':{'scale':1.5},'ppo':{'envs':512,'steps_per_env':128},
        'motion_course':{'configuration':{'version':'motion31_straight_yaw_progression_v1'}},'artifacts':{},'budget':{}}
    p=tmp_path/'parent.json';p.write_text(json.dumps(original))
    s={**original,'experiment':'probe','evaluation_only':True,'notifications':{'enabled':False},'motion_advantage_probe':declaration(p,sha(p)),
       'budget':{'source_eval_updates':0,'smoke_updates':0,'formal_updates':0,'sample_limit':0,'formal_samples':0,'evaluation_wall_s':600,'chain_wall_s':600},'artifacts':{'run_name':'probe'}}
    assert validate(s)
    s['action']={'scale':.5}
    with pytest.raises(ValueError,match='preserve'):validate(s)
    s['action']=original['action'];s['motion_advantage_probe']['surprise']=True
    with pytest.raises(ValueError,match='declaration'):validate(s)


def test_collector_uses_actual_ppo_storage_without_any_optimizer_step(monkeypatch):
    import torch
    from tensordict import TensorDict
    from native_stand.students import motion_advantage_probe as module
    from native_stand.students.model import Student
    from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
    from rsl_rl.storage import RolloutStorage
    from native_stand.students.motion_tracking_reward import configuration,QUALITY_VERSION
    torch.set_num_threads(1)
    class Env:
        device='cpu';num_envs=512
        target_xy=torch.zeros(512,2);command=torch.zeros(512,3);command_index=torch.zeros(512,dtype=torch.long)
        motion_cohort_mix=torch.zeros(7);student_actor_valid=torch.ones(512,dtype=torch.bool)
        recovery_snapshot=torch.zeros(512,39);standing_snapshot=torch.zeros(512,6)
        wheel_geometry_snapshot=torch.zeros(512,9);recovery_control_snapshot=torch.zeros(512,50)
        def select_initial_family(self,*args):pass
        def obs(self):
            return {'student_actor':torch.zeros(512,31),'student_critic':torch.zeros(512,49)}
        def actor_valid_pre(self):return self.student_actor_valid
        def reset(self):
            from types import SimpleNamespace
            self.rise_hold=SimpleNamespace(episode=SimpleNamespace(steps=torch.zeros(512,dtype=torch.long)))
            return self.obs(),{}
        def step(self,action):
            self.rise_hold.episode.steps+=1
            self.student_reward_result={'raw':torch.ones(512,16),'dt':torch.ones(512,16)*.01,'events':torch.zeros(512,3)}
            return self.obs(),torch.ones(512),torch.zeros(512,dtype=torch.bool),torch.zeros(512,dtype=torch.bool),{}
    saved={}
    def assemble(path,obs,recipe):
        actor=Student(True,version='multiskill_mcu_v2');actor.log_std.requires_grad_(False)
        critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1')
        storage=RolloutStorage('rl',512,128,obs,[6],device='cpu')
        p=ControlledPPO(actor,critic,storage,device='cpu',schedule='fixed')
        def forbidden(*args,**kwargs):raise AssertionError('optimizer must never step')
        monkeypatch.setattr(p.optimizer,'step',forbidden)
        return p
    def restore(ppo,source,spec,phase):
        ppo.reward_refinement_state=[{'mix':0.}]*7
        return {'test_fixture':True}
    monkeypatch.setattr('native_stand.students.ppo.assemble',assemble)
    monkeypatch.setattr('native_stand.students.model.load',lambda *a:(None,saved))
    monkeypatch.setattr('native_stand.students.motion_course_requests.restore',restore)
    spec={'source_checkpoint':'fake','seed':1,'student_training':{},'reward':configuration(QUALITY_VERSION),
          'motion_advantage_probe':module.declaration('/fake','a'*64)}
    arrays,report=module.collect(Env(),spec,stopped=lambda:False)
    assert report['optimizer_updates']==0 and report['frozen_state_unchanged']
    assert arrays['value'].shape==(128,512,1) and arrays['actor_input'].shape==(128,512,31)
    assert report['captured_transitions']==65536 and arrays['actor_valid'].all()


def test_local_gradient_is_offline_and_does_not_modify_parameters():
    import torch
    from native_stand.students.model import Student
    actor=Student(True,version='multiskill_mcu_v2')
    commands=[[0,0],[.5,0],[-.5,0],[1,0],[-1,0],[1.5,0],[-1.5,0]]
    a={'actor_valid':np.ones((2,7),bool),'command_index':np.tile(np.arange(7),(2,1)),
       'advantage_raw':np.arange(14,dtype=np.float32).reshape(2,7,1),
       'advantage_normalized':np.ones((2,7,1),np.float32),'actor_input':np.zeros((2,7,31),np.float32),
       'action_raw':np.ones((2,7,6),np.float32)*.01,'terminated':np.zeros((2,7),bool)}
    rng=torch.get_rng_state().clone();r=reviewer().local_gradients(actor,a,commands)
    assert r['parameters_unchanged'] and r['optimizer_updates']==0 and len(r['groups'])==7
    assert torch.equal(rng,torch.get_rng_state()) and all(p.grad is None for p in actor.parameters())
