FROZEN_TEST_SCOPE='PORTABLE'
import copy
import torch
import pytest
from native_stand.recovery.drawback_guidance_proposal import declaration,quality,guided_reward,validate
from native_stand.command_v6.domain.recovery_course import parse_request
from native_stand.recovery.reward_fields import resolve


def test_guidance_shape_mirror_gradient_and_failure_masks():
    c=declaration();target=torch.tensor(c['target_root_m']);w=target.clone();w[1,2]+=.15
    q=torch.tensor([-.02,1.43,.02,1.43]);assert quality(target,q,target)['quality']==1
    bad=q.clone();bad[0]+=.7;assert 0<quality(w,bad,target)['quality']<quality(w,q,target)['quality']
    mirrored=w.flip(0).clone();mirrored[:,0]*=-1;qm=bad[[2,3,0,1]]*torch.tensor([-1,1,-1,1])
    assert torch.allclose(quality(w,bad,target)['quality'],quality(mirrored,qm,target)['quality'])
    w=w[None].repeat(3,1,1);q=bad[None].repeat(3,1).requires_grad_()
    r,t=guided_reward(w,q,torch.tensor([.18]*3),torch.tensor([1,1,0],dtype=torch.bool),torch.tensor([0,1,0],dtype=torch.bool),config=c,dt=.01)
    assert 0<r[0]<=.01 and r[1]==r[2]==0;r.sum().backward();assert q.grad[0,0]<0 and (q.grad[1:]==0).all()


def test_height_exit_no_memory_no_terminal_release():
    c=declaration();target=torch.tensor(c['target_root_m'])[None].repeat(4,1,1);q=torch.tensor([-.02,1.43,.02,1.43])[None].repeat(4,1)
    r,_=guided_reward(target,q,torch.tensor([.18,.22,.26,.30]),torch.ones(4,dtype=torch.bool),torch.zeros(4,dtype=torch.bool),config=c,dt=.01)
    assert torch.allclose(r,torch.tensor([.01,.01,.005,0.]),atol=1e-6)
    # Climbing beyond fade cannot release a negative cost or produce a bonus spike.
    assert bool((r[:-1]>=r[1:]).all())


def test_version_conflicts_and_optional_fields():
    c=declaration();s={'task':'recovery','recovery':{'drawback_guidance':c,'rising_task':{'version':'autonomous_rise_min_height_v2'}}};validate(s)
    b=copy.deepcopy(s);b['recovery']['leg_center_auxiliary']={'enabled':True}
    with pytest.raises(ValueError):validate(b)
    b=copy.deepcopy(s);b['recovery']['drawback_guidance']['strict_symmetry']=True
    with pytest.raises(ValueError):validate(b)
    assert 'drawback_mirror_guidance' in resolve({},s['recovery'])
    assert 'drawback_mirror_guidance' not in resolve({}, {})
