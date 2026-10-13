import importlib.util
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
def module():
 p=ROOT/'scripts/review_recovery_temporal_terminal.py';s=importlib.util.spec_from_file_location('terminal_review',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_truncated_smooth_window_is_not_included_in_full_window_mean():
 m=module();base={'accepted':False,'entry_index':2,'hold_complete':False,'valid_hold_prefix_s':.5,'failed_checks':['incomplete_hold'],'observed_termination_causes':{},'entry_first200':None,'full_hold':None}
 a={**base,'first200':{'intervals':50,'wheel_delta_rms_rad_s':[0.,0.]}}
 b={**base,'first200':{'intervals':200,'wheel_delta_rms_rad_s':[3.,4.],'wheel_applied_torque_rms_nm':[1.,1.],'wheel_torque_sign_changes':[2,2],'policy_limit_fraction':.1,'mean_abs_vx_mps':.2,'pitch_roll_peak_rad':[.1,.1],'dual_contact_fraction':1.}}
 r=m.aggregate([{'rows':[a,b]}]);assert r['first200']['complete_n']==1 and r['first200']['incomplete_n']==1
 assert r['first200']['wheel_delta_rms_rad_s']==[3.,4.] and r['complete_windows']==0

def test_named_left_first_wheel_targets_are_decoded_in_physical_units():
 m=module();schema={'STATE':{'saturated':0,'vx_mps':1,'left_contact_n':2,'right_contact_n':3,'height_m':4},'CONTROL':{'clipped_action':slice(0,6),'applied_torque':slice(6,12)},'POSTURE':{'pitch_rad':0,'roll_rad':1}}
 control=np.zeros((2,1,12));control[1,0,[2,5]]=[.1,.2];state=np.zeros((2,1,5));state[:,:,2:4]=10;state[:,:,4]=.4
 r=m.window({'control':control,'state':state,'posture':np.zeros((2,1,2))},np.array([0,1]),0,schema)
 assert r['wheel_delta_rms_rad_s']==[10.,20.] and r['dual_contact_fraction']==1.
