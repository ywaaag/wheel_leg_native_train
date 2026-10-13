FROZEN_TEST_SCOPE='PROJECT_DATA' # repo-local scripts are not copied by frozen CPU validator
import importlib.util
from pathlib import Path
import numpy as np

p=Path(__file__).resolve().parents[1]/'scripts/audit_recovery_record_learnability.py'
spec=importlib.util.spec_from_file_location('record_audit',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_attribution_closes_with_length_direction_rotation_interactions():
    a=(np.array([.375,.375]),np.array([[0.,1.,0.],[0.,1.,0.]]),np.array([0.,0.,-1.]))
    b=(np.array([.3,.25]),np.array([[0.,.6,-.8],[0.,.8,-.6]]),np.array([0.,-.6,-.8]))
    parts=module.attribution(a,b)
    assert abs(parts.sum()-(module.score(b)-module.score(a)))<1e-12
    assert np.allclose(module.attribution(a,a),0)

def test_body_rotation_only_does_not_get_counted_as_contraction():
    a=(np.array([.375,.375]),np.array([[0.,1.,0.],[0.,1.,0.]]),np.array([0.,0.,-1.]))
    b=(a[0],a[1],np.array([0.,1.,0.]))
    parts=module.attribution(a,b)
    assert np.allclose(parts[:2],0) and parts[2]>0
