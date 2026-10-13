"""Device choice is explicit and CPU path must not touch CUDA/RNG."""
FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.distill import select_device
from native_stand.students.model import Student

def test_explicit_cpu_selection_preserves_rng_and_parameters(monkeypatch):
 actor=Student(version='multiskill_mcu_v2');rng=torch.get_rng_state().clone();before={k:v.clone() for k,v in actor.state_dict().items()}
 monkeypatch.setattr(torch.cuda,'is_available',lambda:(_ for _ in ()).throw(AssertionError('CPU must not query CUDA')))
 device,report=select_device(actor,torch.zeros(512,31),torch.zeros(512,6),'cpu')
 assert device=='cpu' and report['optimizer_steps']==0 and torch.equal(rng,torch.get_rng_state())
 assert all(torch.equal(v,actor.state_dict()[k]) for k,v in before.items())

def test_unknown_device_or_unmapped_GPU_rejected_before_resource_use(monkeypatch):
 actor=Student(version='multiskill_mcu_v2');x=torch.zeros(512,31);y=torch.zeros(512,6)
 with pytest.raises(ValueError,match='device must'):select_device(actor,x,y,'cuda:1')
 monkeypatch.delenv('CUDA_VISIBLE_DEVICES',raising=False)
 with pytest.raises(ValueError,match='explicit physical GPU0'):select_device(actor,x,y,'auto')
