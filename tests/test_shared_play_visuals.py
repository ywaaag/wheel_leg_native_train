"""Shared visual settings preserve legacy view and do not control physics."""
FROZEN_TEST_SCOPE='PORTABLE'
from types import SimpleNamespace
from native_stand.command_v6.tools import ground_visual

def test_floor_light_and_camera_share_settings(monkeypatch):
 calls=[];stage=object()
 def floor(s,**kw):assert s is stage;calls.append(('floor',kw));return {'collision':False,**kw}
 def light(s):assert s is stage;calls.append(('light',s));return {'intensity':1800.}
 monkeypatch.setattr(ground_visual,'apply',floor);monkeypatch.setattr(ground_visual,'add_lighting',light)
 sim=SimpleNamespace(set_camera_view=lambda **kw:calls.append(('camera',kw)))
 result=ground_visual.setup(stage,sim,style='solid',extent_m=64.,grid_spacing_m=.5)
 assert calls[0]==('floor',{'style':'solid','extent_m':64.,'grid_spacing_m':.5})
 assert result['ground_visual']['collision'] is False and result['lighting']['intensity']==1800.
 assert calls[-1]==('camera',{'eye':(1.3,1.3,.85),'target':(0.,0.,.35)})
 ground_visual.camera_view(sim,(2.,-3.))
 assert calls[-1]==('camera',{'eye':(3.3,-1.7,.85),'target':(2.,-3.,.35)})
