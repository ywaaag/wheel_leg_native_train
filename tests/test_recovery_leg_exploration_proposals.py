FROZEN_TEST_SCOPE='PROJECT_DATA'
import importlib.util
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parents[1]/'scripts/audit_recovery_leg_exploration.py'
s=importlib.util.spec_from_file_location('leg_exploration',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_centered_independent_sign_probability_and_finite_tail():
    q=np.zeros((1,4));r=m.coverage(q,np.ones_like(q)*.1,q,q)
    assert abs(r['joint_sign_probability_mean']-1/16)<1e-12
    r=m.coverage(np.array([[-2.,0.,2.,0.]]),np.ones_like(q)*.1,q,q)
    assert np.isfinite(r['joint_sign_log10_probability_mean']) and r['joint_sign_probability_mean']<1e-50
    assert r['local_box_prob_max']>0
