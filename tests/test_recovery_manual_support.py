import copy
import json
from pathlib import Path
from native_stand.recovery.domain import support_indices
from native_stand.recovery.validation import validate_recovery

ROOT=Path(__file__).resolve().parents[1]


def test_linkage_support_leaves_weak_parts_restricted():
    names=['robot','left_wheel','guide_wheel_lower_left_01','left_parallel_link','right_lower_leg','camera']
    allowed,restricted=support_indices(names,['robot','left_wheel','guide_wheel_lower_*','*_parallel_link','*_lower_leg'])
    assert allowed==[0,1,2,3,4] and restricted==[5]
    assert support_indices(names[:3],['*'])==([0,1,2],[])


def test_linkage_support_requires_explicit_user_confirmation():
    spec=json.loads((ROOT/'configs/experiments/recovery_r1_20261002/spec.json').read_text())
    spec['recovery']['contacts']['allowed_candidate']+=['*_active_link','*_long_link','*_node_link','*_parallel_link','*_upper_leg','*_lower_leg']
    assert 'Unvalidated support-body classification change' in validate_recovery(spec)
    spec['recovery']['contacts']['linkage_support_user_confirmed']=True
    assert not validate_recovery(spec)
    spec['recovery']['contacts']['allowed_candidate'].append('camera')
    assert 'Unvalidated support-body classification change' in validate_recovery(spec)
