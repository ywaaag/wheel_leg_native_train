FROZEN_TEST_SCOPE='PROJECT_DATA'
import json,copy,os,subprocess,sys
from pathlib import Path
import pytest
from native_stand.students.temporal_ab_io import verify_source
ROOT=Path(__file__).resolve().parents[1]

def test_actual_temporal_source_phase_receipt_and_full_state_are_verified(monkeypatch):
 # A completed historical experiment binds its own frozen execution code. New
 # unrelated recipes must not be required to retain the old full-repo SHA.
 folder=ROOT/'isolated/recovery_temporal_ab_20261012'
 preparation=json.load(open(folder/'final_preparation.json'));s=json.load(open(preparation['specs']['A']))
 task=json.load(open(preparation['manifest']))
 frozen=ROOT/'runs'/s['experiment']/'source_snapshot'
 code='''import json,sys
from native_stand.students.temporal_ab_io import verify_source
from native_stand.students import course_requests
s=json.load(open(sys.argv[1]));t=json.load(open(sys.argv[2]));course_requests.verify_task=lambda spec:t
r=verify_source(s);assert r['Actor_Critic_Adam_RNG_restored'] and r['new_smoke_required'];print(json.dumps(r))
'''
 result=subprocess.run([sys.executable,'-c',code,preparation['specs']['A'],preparation['manifest']],cwd=folder,env={**os.environ,'PYTHONPATH':str(frozen),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=60)
 assert result.returncode==0,result.stderr
 assert json.loads(result.stdout)['Actor_Critic_Adam_RNG_restored']
 monkeypatch.setattr('native_stand.students.course_requests.verify_task',lambda spec:task)
 from native_stand.command_v6.tools.execution_identity import identity
 if identity(s)['location_independent_modules_sha256']!=task['temporal_ab']['execution_sha256']:
  with pytest.raises(ValueError,match='execution bundle changed'):verify_source(s)
 else:
  wrong=copy.deepcopy(s);wrong['reward']['success_once']=123
  with pytest.raises(ValueError,match='reward/control/PPO'):verify_source(wrong)
