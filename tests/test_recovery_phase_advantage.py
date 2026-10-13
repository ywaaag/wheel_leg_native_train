FROZEN_TEST_SCOPE='PROJECT_DATA' # repo-local script audit
import importlib.util
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parents[1]/'scripts/audit_recovery_phase_advantage.py'
spec=importlib.util.spec_from_file_location('phase_audit',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_matched_clock_removes_between_clock_negative_association():
    r=m.matching(np.array([1.,2.,3.,4.]),np.array([10.,11.,0.,1.]),np.array([1,1,2,2]))
    assert abs(r['within_clock_correlation']-1)<1e-12

def test_bonus_gae_stops_at_terminal_and_has_no_cross_rollout_leak():
    b=np.zeros((2,3,1));b[0,2,0]=1;done=np.zeros_like(b,dtype=bool);done[0,1,0]=True
    r=m.gae_bonus(b,done,.99,.95)
    assert r[0,0,0]==0 and r[0,1,0]==0 and r[0,2,0]==1 and (r[1]==0).all()
