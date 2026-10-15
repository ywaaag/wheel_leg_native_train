FROZEN_TEST_SCOPE='PORTABLE'
import json
import numpy as np
import pytest
from native_stand.recovery.handoff_evaluator import atomic_result

def test_artifact_cap_is_not_phase_directory_cap(tmp_path):
 (tmp_path/'checkpoint.pt').write_bytes(b'x'*10000)
 for i in range(4):
  p=atomic_result(tmp_path,i,{'accepted':False},{'state':np.zeros((10,8,39))},20000,artifact_cap_bytes=3000)
  assert json.loads(p.read_text())['trace']['path']==f'trace_{i:02d}.npz'
 assert (tmp_path/'checkpoint.pt').stat().st_size==10000

def test_separate_caps_fail_without_partial_result(tmp_path):
 arrays={'state':np.zeros((10,8,39))}
 with pytest.raises(RuntimeError,match='artifact'):atomic_result(tmp_path,0,{},arrays,20000,artifact_cap_bytes=1)
 assert not list(tmp_path.iterdir())
 (tmp_path/'old.log').write_bytes(b'x'*10000)
 with pytest.raises(RuntimeError,match='cumulative'):atomic_result(tmp_path,1,{},arrays,10000,artifact_cap_bytes=3000)
 assert [p.name for p in tmp_path.iterdir()]==['old.log']

def test_resume_rejects_unbound_inputs():
 from native_stand.students.storage_resume import verify
 with pytest.raises(ValueError,match='schema'):verify({'student_storage_resume':{}})

def test_new_v14_checkpoints_capture_rng_and_resume_skips_warmup():
 import ast
 from pathlib import Path
 tree=ast.parse(Path('src/native_stand/students/training.py').read_text())
 save=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='save_checkpoint')
 text=ast.unparse(save)
 assert "data['training_rng'] = rng_state()" in text
 assert 'parent_formal_updates' in text

def test_recovery_verifies_consumption_fault_and_recipe(tmp_path,monkeypatch):
 import copy
 from native_stand.students.data import sha
 from native_stand.students.storage_resume import verify,VERSION
 import native_stand.command_v6.wiring as wiring
 monkeypatch.setattr(wiring,'validate_persisted_certificate',lambda *a:{'status':'PASSED'})
 parent=tmp_path/'old'/'spec.json';parent.parent.mkdir();formal=tmp_path/'formal';formal.mkdir();cp=formal/'model_update_300.pt';cp.write_bytes(b'checkpoint')
 old={'experiment':'old','source_checkpoint':'old.pt','source_sha256':'0'*64,'reward':{'weight':1},'student_training':{'version':'v14','source_actor_sha256':'0'*64,'milestones':[100]},'student_evaluation':{'cases':[{'checkpoint':'old.pt','sha256':'0'*64,'case_id':'normal'}]}}
 parent.write_text(json.dumps(old));book={'used':{'smoke':12,'formal':300},'limits':{'smoke':12,'formal':988},'attempts':{'f':{'phase':'formal','status':'FAILED','output_dir':str(formal),'updates':300},'s':{'phase':'smoke','status':'COMPLETED','output_dir':str(tmp_path/'smoke')}}}
 ledger=parent.with_name('budget.json');ledger.write_text(json.dumps(book));terminal=formal/'terminal_report.json';terminal.write_text(json.dumps({'actual_updates':300,'failure':{'exception':"RuntimeError('Handoff storage cap exceeded')"}}))
 s=copy.deepcopy(old);s.update(experiment='new',source_checkpoint=str(cp),source_sha256=sha(cp),budget={'smoke_updates':0,'formal_updates':688})
 s['student_storage_resume']={'version':VERSION,'parent_spec':str(parent),'inputs':{str(p):sha(p) for p in (parent,ledger,terminal,cp)},'parent_formal_updates':300,'historical_online_updates':312,'original_online_limit':1000,'rng_semantics':'restore_if_present_else_explicit_seed_reset'}
 assert verify(s)['remaining_online_updates']==688
 bad=copy.deepcopy(s);bad['budget']['formal_updates']=689
 with pytest.raises(ValueError,match='quota'):verify(bad)
 bad=copy.deepcopy(s);bad['reward']['weight']=2
 with pytest.raises(ValueError,match='behavior'):verify(bad)
 bad=copy.deepcopy(s);bad['student_storage_resume']['historical_online_updates']=0
 with pytest.raises(ValueError,match='accounting'):verify(bad)
 cp.write_bytes(b'tampered')
 with pytest.raises(ValueError,match='SHA'):verify(s)

def test_partial_json_publication_rolls_back_trace(tmp_path,monkeypatch):
 from pathlib import Path
 original=Path.rename
 def fail_json(self,target):
  if self.name.endswith('.tmp') and str(target).endswith('.json'):raise OSError('publication fault')
  return original(self,target)
 monkeypatch.setattr(Path,'rename',fail_json)
 with pytest.raises(OSError):atomic_result(tmp_path,0,{}, {'state':np.zeros(2)},10000,artifact_cap_bytes=10000)
 assert not list(tmp_path.iterdir())

@pytest.mark.parametrize('reuse',[False,True])
def test_real_worker_storage_resume_state_path(tmp_path,monkeypatch,reuse):
 from types import SimpleNamespace
 import native_stand.command_v6.stand_chain as chain
 import native_stand.students.storage_resume as resume
 from native_stand.command_v6.tools.run_state import transition
 source=tmp_path/'old_source';source.mkdir();(source/'terminal_report.json').write_text(json.dumps({'status':'COMPLETED'}));(source/'progress.json').write_text('{}')
 spec=tmp_path/'spec.json';decl={'student_training':{'version':'student_standing_survival_quality_v14'},'source_sha256':'a'*64,'student_storage_resume':{},'budget':{'smoke_updates':0}}
 decl['student_storage_resume']['version']='test'
 if reuse:decl['student_storage_resume']['source_eval_dir']=str(source)
 spec.write_text(json.dumps(decl));run=tmp_path/'run';run.mkdir();calls=[];reports=[];verification=[]
 monkeypatch.setattr(resume,'verify',lambda d:verification.append(d) or {'status':'VERIFIED'})
 def phase(path,name,output,handshake_fd=None):
  calls.append(name)
  return {'phase':name,'run':str(output),'exit_code':0,'status':'COMPLETED','terminal':{'status':'COMPLETED'},'progress':{'engineering_valid':True}}
 monkeypatch.setattr(chain,'run_phase',phase);monkeypatch.setattr(chain,'chain_event',lambda *a:None)
 monkeypatch.setattr(chain,'chain_report',lambda *a:reports.append(a))
 assert chain.worker(SimpleNamespace(output_dir=run,spec=spec,handshake_fd=-1))==0
 assert calls==(['formal'] if reuse else ['source_eval','formal'])
 assert json.loads((run/'run_state.json').read_text())['state']=='COMPLETED'
 assert reports[0][3]=='COMPLETED' and verification
 with pytest.raises(ValueError,match='transition'):transition('SOURCE_EVAL','FORMAL')
 with pytest.raises(ValueError,match='evidence'):transition('SOURCE_EVAL','FORMAL',continuation={'version':'verified_student_storage_continuation_v1','verified':False,'checkpoint_sha256':'a'*64})

def test_real_worker_blocks_bad_recovery_before_formal(tmp_path,monkeypatch):
 from types import SimpleNamespace
 import native_stand.command_v6.stand_chain as chain
 import native_stand.students.storage_resume as resume
 spec=tmp_path/'spec.json';spec.write_text(json.dumps({'student_storage_resume':{'version':'test'},'source_sha256':'a'*64,'student_training':{},'budget':{}}));run=tmp_path/'run';run.mkdir();calls=[]
 def reject(spec):raise ValueError('recovery SHA invalid')
 monkeypatch.setattr(resume,'verify',reject)
 monkeypatch.setattr(chain,'run_phase',lambda p,n,o,h=None:calls.append(n) or {'phase':n,'run':str(o),'status':'COMPLETED','exit_code':0,'terminal':{},'progress':{}})
 monkeypatch.setattr(chain,'chain_event',lambda *a:None);monkeypatch.setattr(chain,'chain_report',lambda *a:None)
 assert chain.worker(SimpleNamespace(output_dir=run,spec=spec,handshake_fd=-1))==1
 assert calls==['source_eval']
 assert json.loads((run/'run_state.json').read_text())['state']=='FAILED'
