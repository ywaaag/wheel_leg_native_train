import importlib.util
from pathlib import Path
import torch
sp=importlib.util.spec_from_file_location('frame25',Path(__file__).with_name('distill.py'));d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)

def test_exact_network_and_no_history_input():
 net=d.actor();assert sum(p.numel() for p in net.parameters())==13862;assert net(torch.zeros(2,25)).shape==(2,6)
 try:net(torch.zeros(2,150))
 except RuntimeError:pass
 else:raise AssertionError('150D must not be silently accepted')

def test_physical_scale_and_loss():
 p=torch.zeros(2,6);y=p.clone();p[:,0]=.2;p[:,2]=.1;e=d.physical_error(p,y);assert torch.allclose(e[:,0],torch.full((2,),.1));assert torch.allclose(e[:,2],torch.full((2,),10.));assert torch.isclose(d.loss(p,y),torch.tensor(.75))

def test_episode_split_and_finite_actual_dataset():
 data=torch.load(d.ROOT/'isolated/motion_frame25_zero_distilled_20261013/dataset.pt',weights_only=False);assert data['x'].shape[1]==25 and data['y'].shape[1]==6;assert torch.isfinite(data['x']).all() and torch.isfinite(data['y']).all();assert torch.allclose(data['x'][:,8],torch.full_like(data['x'][:,8],1.7))
 for ep in data['episode'].unique():assert len(data['split'][data['episode']==ep].unique())==1

def test_saved_checkpoint_and_script_actual_outputs():
 root=d.ROOT/'isolated/motion_frame25_zero_distilled_20261013';cp=torch.load(root/'best_validation.pt',weights_only=False);assert cp['interface_version']==d.VERSION;net=d.actor();net.load_state_dict(cp['actor']);data=torch.load(root/'dataset.pt',weights_only=False);script=torch.jit.load(str(root/'actor_torchscript.pt'));assert torch.equal(script(data['x'][:32]),net(data['x'][:32]));assert d.sha(d.TEACHER)==d.SHA
