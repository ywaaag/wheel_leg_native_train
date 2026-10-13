FROZEN_TEST_SCOPE='PORTABLE'
import copy,json,sys
from types import SimpleNamespace
import pytest
from native_stand.students import evaluator

def test_course_single_env_preview_never_loads_or_constructs_teachers(tmp_path,monkeypatch):
 class Env:
  def __init__(self,cfg,**kw):self.kw=kw;self.cfg=cfg
 class Course(Env):pass
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.env',SimpleNamespace(CommandEnvCfg=SimpleNamespace))
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.configure',SimpleNamespace(apply=lambda cfg,s,**kw:cfg))
 monkeypatch.setitem(sys.modules,'native_stand.recovery.handoff_runtime',SimpleNamespace(HandoffEnv=Env))
 monkeypatch.setitem(sys.modules,'native_stand.students.runtime',SimpleNamespace(StudentEnv=Env,TrainingStudentEnv=Env))
 monkeypatch.setitem(sys.modules,'native_stand.students.course_runtime',SimpleNamespace(CourseStudentEnv=Course))
 path=tmp_path/'poses.json';path.write_text(json.dumps({'poses':[]}))
 spec={'recovery':{'pose_library':str(path)},'recovery_course':{'state':{'stage':'B','prefix':180}},'student_training':{'version':'fixture'},'interface_version':'multiskill_mcu_v2','reward':{},'curriculum':{'stages':[{}],'schedule_s':[1,1,1,1]}}
 before=copy.deepcopy(spec)
 monkeypatch.setattr('native_stand.students.requests.evaluation_recovery',lambda config,poses,family:config)
 def forbidden(*a):raise AssertionError('autonomous preview loaded teachers')
 monkeypatch.setattr(evaluator,'teacher_models',forbidden)
 env=evaluator.environment(spec,'RecoveryStudent',envs=1,initial_family='Swing',autonomous_preview=True)
 assert type(env) is Env and not env.curriculum_training
 assert 'teacher_actors' not in env.kw and 'course_configuration' not in env.kw
 assert spec==before
 with pytest.raises(AssertionError,match='loaded teachers'):evaluator.environment(spec,'RecoveryStudent',envs=64)
 with pytest.raises(ValueError,match='one student'):evaluator.environment(spec,'RecoveryStudent',envs=64,autonomous_preview=True)

def test_explicit_family_does_not_select_another_source_family(tmp_path,monkeypatch,capsys):
 from native_stand.students import play
 cp=tmp_path/'candidate.pt';cp.write_bytes(b'fixture')
 from native_stand.students.data import sha
 row={'kind':'student','family':'normal','checkpoint':str(cp),'sha256':sha(cp),'role':'RecoveryStudent'}
 swing={**row,'family':'Swing'}
 spec={'interface_version':'multiskill_mcu_v2','recovery':{'active_family':'normal'},'student_evaluation':{'cases':[row,swing]}}
 monkeypatch.setattr(play,'validate',lambda s:[])
 monkeypatch.setattr('native_stand.command_v6.tools.experiment_preparation.verify_publication',lambda *a,**kw:{'status':'VERIFIED'})
 args=SimpleNamespace(checkpoint=cp,spec=tmp_path/'spec.json',preview_family='Swing',preview=True,handoff_condition=None,keyboard=False,run=False)
 play.execute(args,spec);result=json.loads(capsys.readouterr().out)
 assert result['initial_family']=='Swing' and result['teacher_prefix_intervals']==0 and not result['teacher_control']
