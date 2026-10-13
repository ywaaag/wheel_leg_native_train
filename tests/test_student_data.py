"""PROJECT_DATA: saved first-episode teacher trajectories, never Isaac."""
from pathlib import Path
import json,torch,numpy as np
from native_stand.students.interface import VERSION,LEGS
ROOT=Path(__file__).resolve().parents[1]

def test_episode_splits_and_preaction_physical_targets():
 folder=ROOT/'isolated/student_teachers_20261011';manifest=json.loads((folder/'manifest.json').read_text())
 d=torch.load(folder/'RecoveryStudent.pt',map_location='cpu',weights_only=False)
 assert len([e for e in manifest['episodes'] if e['role']=='RecoveryStudent'])==31
 assert [len(d['episode'][d['split']==s].unique()) for s in (0,1,2)]==[15,8,8]
 for ep in d['episode'].unique():assert len(d['split'][d['episode']==ep].unique())==1
 assert (d['x'][:,-9:-5]==torch.tensor([0,1,0,0])).all()
 assert (d['y'].abs()<=1).all()
 # Real first training episode; last history frame is action-PRE q and executed-PREV target.
 ep=next(e for e in manifest['episodes'] if e['role']=='RecoveryStudent');run,case,env=ep['name'].split('/')
 r=ROOT/'runs'/run;raw=json.loads((r/f'evaluation_{int(case):02}.json').read_text());a=np.load(r/raw['trace']['path'])
 i=int(torch.where(d['episode']==ep['id'])[0][0]);sample=int(d['sample'][i]);ids=raw['field_schema']['active_indices']
 np.testing.assert_allclose(d['x'][i,:1173].reshape(51,23)[-1,6:10].numpy(),a['joint_q_pre'][sample,int(env),ids][list(LEGS)]/1.5,atol=1e-6)
 np.testing.assert_allclose(d['y'][i,list(LEGS)].numpy()*1.5,a['control'][sample,int(env),28:32],atol=1e-6)
 assert d['x'][i,50*23+22]==1

def test_student_checkpoint_identity_fresh_critic_optimizer_and_teacher_sha():
 from native_stand.students.model import load,ppo_initialization
 from native_stand.students.data import sha
 folder=ROOT/'isolated/recovery_student_bc_20261011';actor,d=load(folder/'best_validation.pt','RecoveryStudent')
 initial=torch.load(folder/'random_initialization.pt',weights_only=False,map_location='cpu')
 assert all(torch.equal(v,initial['critic'][k]) for k,v in d['critic'].items())
 actor,critic,optimizer=ppo_initialization(folder/'best_validation.pt')
 assert not optimizer.state
 assert not ({id(p) for p in actor.parameters()} & {id(p) for p in critic.parameters()})
 assert all(sha(path)==value for path,value in d['teacher_sha256'].items())
 assert not all(torch.equal(v,initial['actor'][k]) for k,v in actor.state_dict().items())
 torch.testing.assert_close(actor.log_std,initial['actor']['log_std'])

def test_real_ppo_assembly_new_storage_network_fields_and_no_bc_adam():
 from tensordict import TensorDict
 from native_stand.students.ppo import assemble
 from native_stand.recovery.controlled_ppo import KEY
 obs=TensorDict({'student_actor':torch.zeros(4,1182),'student_critic':torch.zeros(4,1191),KEY:torch.tensor([[True],[False],[True],[False]])},batch_size=[4])
 ppo=assemble(ROOT/'isolated/recovery_student_bc_20261011/best_validation.pt',obs,steps_per_env=4)
 assert not ppo.optimizer.state and ppo.storage.observations['student_critic'].shape[-1]==1191
 raw=ppo.act(obs);assert raw.shape==(4,6)
 torch.testing.assert_close(ppo.transition.actions,raw)
 torch.testing.assert_close(ppo.transition.actions_log_prob,ppo.actor.get_output_log_prob(raw))
 assert not ppo.optimizer.state


def test_loading_candidate_does_not_consume_sampling_rng():
 from native_stand.students.model import load
 before=torch.get_rng_state().clone()
 load(ROOT/'isolated/recovery_student_bc_20261011/best_validation.pt')
 assert torch.equal(before,torch.get_rng_state())
