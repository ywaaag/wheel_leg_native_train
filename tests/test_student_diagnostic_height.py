"""Explicit diagnostic height never changes a historical checkpoint contract."""
FROZEN_TEST_SCOPE='PROJECT_DATA'
import json,copy
from pathlib import Path
from native_stand.students.requests import validate


def test_explicit_mcu_diagnostic_height_validation():
    root=Path(__file__).resolve().parents[1]
    spec=json.loads((root/'configs/experiments/2026_10_11-11_36__mcu_v2_student_independent_ppo0/spec.json').read_text())
    spec['student_evaluation']['cases']=[next(r for r in spec['student_evaluation']['cases'] if r['kind']=='student')]
    row=spec['student_evaluation']['cases'][0];row['command_height_m']=.34
    assert not validate(spec)
    for value in (.29,.43,float('nan'),True):
        bad=copy.deepcopy(spec);bad['student_evaluation']['cases'][0]['command_height_m']=value
        assert any('diagnostic height' in e for e in validate(bad))
    bad=copy.deepcopy(spec);bad['student_evaluation']['cases'][0]['kind']='teacher_combination'
    assert any('diagnostic height' in e for e in validate(bad))


def test_runtime_sets_height_before_reset_and_restores_it():
    from native_stand.command_v6.tools.test_resources import source_file
    text=source_file('students/evaluator.py').read_text()
    assert "env.student_command_height=row['command_height_m']" in text
    assert text.index("env.student_command_height=row['command_height_m']")<text.index('obs,_=env.reset()')
    assert "'student_command_height','handoff_randomization'" in text
