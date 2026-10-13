"""PORTABLE explicit student interface, distribution and real tensor boundaries."""
import pytest,torch
from native_stand.students import interface as I
from native_stand.students.model import Student
FROZEN_TEST_SCOPE='PORTABLE'

def test_history_timestamp_partial_reset_and_padding():
 h=I.History(2);f=torch.ones(2,22);h.append(f,0.);assert h.valid.sum()==2
 assert h.encode(I.task('Recovery',torch.zeros(2,5))).shape==(2,1182)
 assert (h.frames[:,:50]==0).all()
 with pytest.raises(ValueError):h.append(f,0.)
 h.append(f*2,.01);h.reset([0]);h.append(f*3,torch.tensor([0.,.02],dtype=torch.float64))
 assert h.valid.sum(1).tolist()==[1,3];assert h.frames[1,-3:,0].tolist()==[1,2,3]

def test_physical_label_roundtrip_and_no_silent_clipping():
 ref=torch.zeros(1,6);leg=torch.tensor([[.3,-.2,.4,-.1]]);wheel=torch.tensor([[20.,-30.]])
 y=I.labels(leg,wheel,ref);assert y[0,0]==pytest.approx(.2)
 t=I.targets(y,ref);torch.testing.assert_close(t['leg_executed'],leg);torch.testing.assert_close(t['wheel_executed'],wheel)
 with pytest.raises(ValueError):I.labels(leg*10,wheel,ref)
 limit=torch.tensor([[-.1,.1]]*6)[None];assert I.targets(y,ref,limit)['joint_limit_clipped'].all()

def test_encoder_and_privilege_isolation():
 q=torch.zeros(2,6);g=torch.tensor([[0.,-1.,0.]]).repeat(2,1)
 f=I.frame(torch.ones(2,3),g,q,q,torch.zeros(2,4),torch.zeros(2,2),q)
 assert f.shape==(2,22);assert torch.equal(f[:,:3],torch.ones(2,3)*.25)
 h=I.History(2);h.append(f,.0);x=h.encode(I.task('Recovery',torch.tensor([[0.,0.,.36,0.,0.]]).repeat(2,1)))
 z=I.critic_input(x,torch.ones(2),torch.ones(2,3),torch.ones(2,2),torch.ones(2),torch.ones(2),torch.ones(2))
 assert z.shape==(2,1191);torch.testing.assert_close(z[:,:1182],x);assert x[:,-9:-5].tolist()==[[0,1,0,0]]*2

def test_bounded_mean_unsquashed_gaussian_coordinates():
 torch.manual_seed(5);actor=Student();critic=Student(False);x=torch.randn(4,1182)
 raw=actor(x,True);torch.testing.assert_close(actor.log_prob(x,raw),actor.distribution(x).log_prob(raw).sum(-1))
 assert (actor(x).abs()<=1).all();assert not ({id(p) for p in actor.parameters()}&{id(p) for p in critic.parameters()})
 torch.testing.assert_close(actor.log_std.exp()*torch.tensor([1.5,1.5,100,1.5,1.5,100]),torch.tensor([.05,.05,2,.05,.05,2]))

def test_legacy_frame_and_factory_shape_remain_strict():
 from native_stand.command_v6.domain import contract as legacy
 q=torch.zeros(2,6);f=legacy.frame(torch.zeros(2,3),torch.tensor([[0.,-1.,0.]]).repeat(2,1),torch.zeros(2,3),q,q,q,q)
 assert f.shape==(2,25)
 with pytest.raises(ValueError):legacy.history(torch.zeros(2,1173),f,torch.zeros(2,dtype=torch.bool))
