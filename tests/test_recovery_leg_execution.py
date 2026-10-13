FROZEN_TEST_SCOPE='PROJECT_DATA'
import importlib.util
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parents[1]/'scripts/audit_recovery_leg_execution.py'
s=importlib.util.spec_from_file_location('leg_audit',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_alignment_separates_action_jointlimit_PD_and_event_time():
    st=np.zeros((3,39));st[:,0]=[.01,.02,.03];st[:,29]=1;st[:,10:12]=5;st[2,10]=0;st[:,15]=[.01,.2,.3]
    c=np.zeros((3,54));c[:,12]=2;c[:,24:28]=.5;c[:,28:32]=.5;c[:,38]=40
    g=np.zeros((3,13));g[:,0]=.3;g[:,4]=.3
    r=m.summarize({'env_id':0,'family':'Swing','compact_trace_100hz':st.tolist(),'control_diagnostics_100hz':c.tolist(),'wheel_geometry_trace_100hz':g.tolist()},np.zeros((2,3)))
    assert r['raw_action_clip_fraction']==[1.,0.,0.,0.]
    assert r['joint_target_limit_clip_fraction']==[0.,0.,0.,0.]
    assert r['PD_limit_fraction']==[1.,0.,0.,0.]
    assert r['first_tilt_above018_clock_s']==.02 and r['first_contact_loss_clock_s']==.03

def test_mismatched_trace_lengths_rejected():
    import pytest
    with pytest.raises(ValueError,match='Aligned'):
        m.summarize({'compact_trace_100hz':[[0.]*39],'control_diagnostics_100hz':[],'wheel_geometry_trace_100hz':[]},np.zeros((2,3)))
