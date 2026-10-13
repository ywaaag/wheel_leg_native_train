FROZEN_TEST_SCOPE='PORTABLE'
import json,os
from types import SimpleNamespace
from native_stand.command_v6.completion import write

def test_actual_chain_continuation_runs_source_then_formal_and_retains_proof(tmp_path,monkeypatch):
 from native_stand.command_v6 import stand_chain
 spec=tmp_path/'spec.json';chain=tmp_path/'chain';chain.mkdir()
 write(spec,{'source_sha256':'e'*64,'recovery_course':{'resume':True},'ppo':{'envs':64,'steps_per_env':128}})
 write(tmp_path/'budget.json',{'limits':{'formal':300},'used':{'source_eval':1,'smoke':0,'formal':1}})
 write(chain/'manifest.json',{'attempt_id':'fixture','hapi_session':None})
 phases=[];proof=[]
 def run(path,phase,out,handshake_fd=None):
  phases.append(phase);out.mkdir()
  if phase=='formal':proof.append(json.loads((chain/'run_state.json').read_text())['continuation'])
  return {'phase':phase,'run':str(out),'exit_code':0,'status':'COMPLETED','terminal':{'actual_updates':1},'progress':{}}
 monkeypatch.setattr(stand_chain,'run_phase',run)
 monkeypatch.setattr('native_stand.students.course_requests.verify_continuation',lambda s:True)
 monkeypatch.setattr('native_stand.students.course_io.finish_block',lambda *a:None)
 monkeypatch.setattr(stand_chain,'notify',lambda *a:None)
 reader,writer=os.pipe()
 try:assert stand_chain.worker(SimpleNamespace(output_dir=chain,spec=spec,handshake_fd=writer))==0
 finally:os.close(reader)
 assert phases==['source_eval','formal'] and proof[0]['verified']
 assert json.loads((chain/'run_state.json').read_text())['state']=='COMPLETED'

def test_temporal_owner_B_not_submitted_after_A_fault(tmp_path,monkeypatch):
 from native_stand.students.temporal_ab_io import finish
 import native_stand.students.course_io as io
 m=tmp_path/'task_manifest.json';ledger=m.with_name('task_ledger.json');spec=tmp_path/'spec.json';chain=tmp_path/'run';chain.mkdir()
 write(m,{'temporal_ab':{'specs':{'B':'NEVER'}},'session':'owner'})
 write(spec,{'recovery_course':{'task_manifest':str(m)},'student_temporal_regularization':{'arm':'A'}})
 write(tmp_path/'budget.json',{'used':{'formal':1,'smoke':12},'attempts':{}})
 write(ledger,{'active_spec':str(spec.resolve()),'blocks':[],'totals':{'updates':0,'samples':0,'effective_actor_samples':0,'score_episodes':0,'wall_s':0.}})
 write(chain/'chain_terminal_report.json',{'phase_results':[],'event_id':'fixed','chain_wall_s':3.})
 monkeypatch.setattr(io,'authorize_block',lambda *a:(_ for _ in ()).throw(AssertionError('B submitted after fault')))
 d=finish(spec,chain,'FAILED','runtime failure')
 assert d['status']=='ENGINEERING_STOP' and d['totals']['updates']==13 and d['active_spec'] is None
