FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.model import Student,load
from native_stand.students.motion_transfer import transfer_actor,compare
from native_stand.students.mcu_interface import task,actor_input

def test_transfer_preserves_output_and_source_and_std(tmp_path):
 with torch.random.fork_rng(devices=[]):
  torch.manual_seed(7);source=Student(version='multiskill_mcu_v2');before={k:v.clone() for k,v in source.state_dict().items()}
  command=torch.randn(128,3);command[:,2]=.34
  x=actor_input(torch.randn(128,22),task('Recovery',command));new=transfer_actor(source);proof=compare(source,new,x)
 assert proof['mapped_action_max']<1e-6 and proof['std_equal']
 assert all(torch.equal(v,before[k]) for k,v in source.state_dict().items())
 assert all(torch.equal(v,before[k]) for k,v in new.state_dict().items() if k!='mlp.0.weight')
 p=tmp_path/'actor.pt';torch.save({'role':'MotionZeroStudent','interface_version':'multiskill_mcu_v2','actor':new.state_dict()},p)
 reloaded,_=load(p,'MotionZeroStudent');assert compare(source,reloaded,x)['mapped_action_max']<1e-6
 with pytest.raises(ValueError,match='role'):load(p,'RecoveryStudent')

def test_transfer_rejects_wrong_interface_or_mode():
 with pytest.raises(ValueError,match='MCU'):transfer_actor(Student())
 source=Student(version='multiskill_mcu_v2');new=transfer_actor(source)
 with pytest.raises(ValueError,match='Recovery'):compare(source,new,torch.zeros(3,31))
 with pytest.raises(ValueError,match='finite'):compare(source,new,torch.ones(2,25))
