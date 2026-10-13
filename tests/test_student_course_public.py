FROZEN_TEST_SCOPE='PROJECT_DATA'
import copy,json
from pathlib import Path
import pytest
from native_stand.students.course import *
from native_stand.students.course_io import prepare_block
ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'isolated/recovery_continuous_course_20261012/task/task_manifest.json'

def test_public_preparer_dynamic_and_current_contract_zero_write(tmp_path):
 from native_stand.command_v6.config import validate
 state=initial_state();state.update(stage='B',prefix=65,previous_prefix=80)
 out=tmp_path/'2026_10_12-10_00__dynamic_fixture'
 r=prepare_block(TASK,state=state,write_files=False,output=out)
 assert not out.exists() and r['total_update_limit'] is None
 r=prepare_block(TASK,state=state,write_files=True,output=out);s=json.loads((out/'spec.json').read_text())
 assert validate(s)==[] and s['budget']['chain_wall_s']==14400
 assert s['student_training']['version']==SUFFIX_RECIPE
 assert [x['prefix_s'] for x in s['student_evaluation']['cases'][:3]]==[.65]*3
 assert s['reward']['motion_zero_tracking']['gate']=='height_progress_times_first_entry_confirmed'
 assert s['student_training']['critic']=='student_control_only'
 assert json.loads((out/'budget.json').read_text())['used']['formal']==0

@pytest.mark.parametrize('mutation',['network','resource','reward','case','budget','source_rng','teacher_metadata_actor'])
def test_public_decl_rejects_unallowed_changes(tmp_path,mutation):
 from native_stand.command_v6.config import validate
 out=tmp_path/'2026_10_12-10_01__course_fixture';prepare_block(TASK,write_files=True,output=out)
 s=json.loads((out/'spec.json').read_text())
 if mutation=='network':s['ppo']['hidden_dims']=[256,128,64]
 if mutation=='resource':s['control']['effort_limits_nm'][2]=10.
 if mutation=='reward':s['reward']['hold_wheel_smooth']['weight_per_s']=-1.
 if mutation=='case':s['student_evaluation']['cases'][0]['hidden_teacher_id']=1
 if mutation=='budget':s['budget']['formal_updates']=999999
 if mutation=='source_rng':s['restore_source_rng']=True
 if mutation=='teacher_metadata_actor':s['student_interface']['actor_dim']=32
 assert validate(s)

def test_teacher_and_original_source_files_unchanged_by_prepare(tmp_path):
 from native_stand.students.data import sha
 task=json.loads(TASK.read_text());inputs={task['source_checkpoint']:task['source_sha256'],task['source_parent']:task['source_parent_sha256']}
 for t in task['teachers']:inputs[t['checkpoint']]=t['sha256'];inputs[t['spec']]=t['spec_sha256']
 prepare_block(TASK,output=tmp_path/'2026_10_12-10_02__identity_fixture',write_files=True)
 assert all(sha(path)==h for path,h in inputs.items())


def test_task_authorization_identity_stop_and_no_duplicate_block(tmp_path,monkeypatch):
 from native_stand.students.course_requests import verify_task,project_root_for
 from native_stand.students.course_io import authorize_block
 from native_stand.students.data import sha
 from native_stand.command_v6.completion import write
 task=json.loads(TASK.read_text());folder=tmp_path/'task';folder.mkdir();manifest=folder/'task_manifest.json';write(manifest,task)
 name='2026_10_12-10_03__authorized_fixture';out=tmp_path/name;prepare_block(manifest,write_files=True,output=out)
 spec=json.loads((out/'spec.json').read_text());spec['authorization'].update(status='AUTHORIZED',hapi_session=task['session']);spec['device'].update(physical_index=0,uuid=task['gpu_uuid'])
 write(folder/'task_ledger.json',{'status':'RUNNING','active_spec':str(ROOT/'configs/experiments'/name/'spec.json')})
 assert verify_task(spec)['source_sha256']==SOURCE_SHA
 assert project_root_for(spec,tmp_path)==ROOT
 (folder/'STOP').write_text('user stop')
 with pytest.raises(ValueError,match='stopped'):verify_task(spec)
 spec['recovery_course']['task_manifest_sha256']='0'*64
 with pytest.raises(ValueError,match='identity'):project_root_for(spec,tmp_path)
