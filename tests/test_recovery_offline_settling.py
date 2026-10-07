import importlib.util
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('review',Path(__file__).parents[1]/'scripts/review_recovery_settling.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_alternating_speed_cannot_cancel_gate():
    a=np.zeros((300,39));a[:,0]=np.arange(1,301)*.01
    a[:,6]=.4;a[:,7]=np.where(np.arange(300)%2,.1,-.1)
    a[:,10:12]=3;a[:,13]=.3
    a[:,22]=np.sqrt(.5);a[:,25]=np.sqrt(.5)
    e={'env_id':0,'pose_id':'fixture','compact_trace_100hz':a.tolist(),
       'success':False,'termination_reason':['timeout'],'runtime_fault':False}
    c={'height_m':[.38,.42],'tilt_max_rad':.2,'linear_speed_max_mps':.05,
       'angular_speed_max_rad_s':.3,'dual_contact_min_n':2,'chassis_clearance_min_m':.25}
    r=module.review_episode(e,c)
    assert r['known_gate_pass_fraction']['horizontal_speed_necessary']==0
    assert r['all_known_longest_s']==0
    assert r['windows']['whole']['vx_abs_mean_mps']>.09
    assert 'UNKNOWN' in r['exact_all_gates']


def test_hold_requires_continuity():
    assert module.longest([True]*100+[False]+[True]*150)==1.5
