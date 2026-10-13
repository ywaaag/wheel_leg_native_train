FROZEN_TEST_SCOPE='PORTABLE'
import numpy as np
import pytest
from native_stand.recovery.dynamic_diagnostic import smooth_clock,target,encode_native,validate_sample

def test_quintic_bounded_endpoints_overlap_and_no_outofrange_clamp():
    q=np.array([1.142,-1.41,-1.143,-1.409])
    assert np.array_equal(target(q,0,contraction_rad=.3,rotation_rad=.2,duration_s=.24,contraction_delay_s=.04),q)
    t=target(q,1,contraction_rad=.3,rotation_rad=.2,duration_s=.24,contraction_delay_s=.04)
    assert np.allclose(t-q,[.1,.5,-.1,.5]);encode_native(t,np.zeros(4))
    assert smooth_clock(-.1,.1)==0 and smooth_clock(1,.1)==1
    with pytest.raises(ValueError):encode_native(np.ones(4)*2,np.zeros(4))

def test_named_measurement_missing_contact_unknown_rate_rejected():
    sample={'time_s':0.,'episode_id':1,'initial_valid':True,'action_origin':'explicit_diagnostic',
        'override_mask':np.ones(6),'joint_q':np.zeros(4),'joint_dq':np.zeros(4),'root_state':np.zeros(13),
        'target6':np.zeros(6),'PD_requested6':np.zeros(6),'PD_clipped6':np.zeros(6),'PD_applied6':np.zeros(6)}
    assert validate_sample(sample,joint_names=list('abcd'),body_names=['wheel'],rate='PD')
    with pytest.raises(ValueError):validate_sample(sample,joint_names=list('abcd'),body_names=['wheel'],rate='physics')
    sample.update(contact_force_world_by_body=np.zeros((1,3)),contact_dt_s=.001)
    assert validate_sample(sample,joint_names=list('abcd'),body_names=['wheel'],rate='physics')
    sample['contact_dt_s']=.005
    with pytest.raises(ValueError):validate_sample(sample,joint_names=list('abcd'),body_names=['wheel'],rate='physics')
