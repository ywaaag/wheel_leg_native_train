FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.motion_validation import command_tensor,score,protocol
from native_stand.students.mcu_interface import actor_input,task

def test_motion_commands_reach_task_slots_without_changing_physical_fields():
 current=torch.randn(8,22);commands=command_tensor([-.5,0.,.34],current,'MotionZeroStudent')
 x=actor_input(current,task('Motion',commands))
 torch.testing.assert_close(x[:,:22],current);torch.testing.assert_close(x[:,22],torch.full((8,),-.125))
 torch.testing.assert_close(x[:,24],torch.full((8,),.68));assert x[:,25].eq(1).all() and x[:,26].eq(0).all()
 with pytest.raises(ValueError,match='role'):command_tensor([.5,0,.34],current,'RecoveryStudent')
 with pytest.raises(ValueError,match='invalid'):command_tensor([5,0,.34],current,'MotionZeroStudent')

def fixture(vx):
 s=torch.zeros(3000,39);s[:,6]=.34;s[:,7]=vx;s[:,10:12]=20;s[:,13]=.1;s[:,29]=1
 p=torch.zeros(3000,10);p[:,2:4]=.3;g=torch.zeros(3000,13);g[:,7]=-1;world=torch.zeros(3000,3);world[:,0]=vx
 return s,p,g,torch.ones(3000,dtype=torch.bool),world

def test_motion_tracking_and_zero_quality_are_separate():
 good=score(*fixture(.5),[.5,0,.34]);assert good['accepted'] and good['tracking']['samples']==2500
 assert 'horizontal_speed' not in good['checks'] and good['tracking']['MAE_mps']==0
 reverse=score(*fixture(-.5),[.5,0,.34]);assert not reverse['accepted'] and not reverse['checks']['direction']
 stop=score(*fixture(0),[.5,0,.34]);assert not stop['accepted'] and not stop['checks']['speed_gain']
 zero=score(*fixture(.5),[0,0,.34]);assert not zero['accepted'] and not zero['checks']['horizontal_speed']

def test_incomplete_cannot_pass_and_tracking_excludes_first5_seconds():
 values=list(fixture(.5));values[0][:500,7]=-2
 result=score(*values,[.5,0,.34]);assert result['tracking']['MAE_mps']==0
 shortened=[x[:-1] for x in fixture(.5)];assert not score(*shortened,[.5,0,.34])['accepted']

def test_motion_probe_validation_rejects_online_training_and_wrong_command_matrix():
 from native_stand.students.motion_validation import validate
 from native_stand.students.standing_survival_reward import configuration
 s={'interface_version':'multiskill_mcu_v2','evaluation_only':True,'student_motion_validation':protocol(),'reward':configuration(),
 'student_evaluation':{'cases':[{'role':'MotionZeroStudent','kind':'student','family':'motion_native_normal','seconds':31.52,'command':[v,0,.34]} for v in protocol()['commands_mps']]}}
 validate(s);s['student_training']={'version':'test'}
 with pytest.raises(ValueError,match='PPO0'):validate(s)

def test_monitor_report_does_not_accept_missing_cases(tmp_path):
 import json
 from native_stand.students.motion_validation import finalize
 spec={'source_checkpoint':'actor.pt','source_sha256':'a'*64,'student_evaluation':{'cases':[{'case_id':'zero'},{'case_id':'positive'}]}}
 (tmp_path/'evaluation_00.json').write_text(json.dumps({'passed_envs':8,'per_env':[]}))
 (tmp_path/'terminal_report.json').write_text(json.dumps({'attempt_id':'x','conditions':[{'condition':{'case_id':'zero'},'status':'COMPLETED','result':'evaluation_00.json'}]}))
 finalize(tmp_path,spec,'COMPLETED')
 assert json.loads((tmp_path/'analysis.json').read_text())['accepted'] is False
 assert json.loads((tmp_path/'candidate_selection.json').read_text())['accepted_candidate'] is None
 assert (tmp_path/'report_ready.json').is_file()
