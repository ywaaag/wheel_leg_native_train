FROZEN_TEST_SCOPE='PORTABLE'
import copy,json
from pathlib import Path
import pytest
from native_stand.students.data import sha
from native_stand.students.motion_wiring_recovery import verify_partial,PARTIAL_VERSION

def fixture(tmp_path):
 cfg=tmp_path/'configs/parent';cfg.mkdir(parents=True);parent=cfg/'spec.json';run=tmp_path/'run';source=run/'source_eval';smoke=run/'smoke';source.mkdir(parents=True);smoke.mkdir()
 def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v))
 keys=('source_checkpoint','source_sha256','asset_path','asset_sha256','student_interface','observation','history','action','control','ground','termination','ppo','reward','curriculum','motion_assessment','student_training','student_evaluation','recovery','seed','performance','device')
 old={k:{} for k in keys};old.update(source_sha256='a'*64,asset_sha256='b'*64,motion_training={},budget={'smoke_updates':50,'formal_updates':1950,'chain_wall_s':64800},student_evaluation={'cases':[{'command':[v,0,.34]} for v in (0,.5,-.5,1,-1)]})
 write(parent,old);write(parent.with_name('budget.json'),{'used':{'smoke':1,'formal':0},'attempts':{'source':{'phase':'source_eval','status':'COMPLETED'},'smoke':{'phase':'smoke','status':'FAILED'}}})
 write(run/'chain_terminal_report.json',{'status':'FAILED','chain_wall_s':900})
 write(smoke/'terminal_report.json',{'status':'FAILED','actual_updates':0,'failure':{'exception':"AttributeError(\"'function' object has no attribute 'items'\")"}})
 (smoke/'metrics.jsonl').write_text(json.dumps({'update':1,'actor_changed_this_update':False,'critic_changed_this_update':True,'actor_update_scope':{'critic_warmup':True}})+'\n')
 write(source/'source_snapshot/spec.json',old);specsha=sha(source/'source_snapshot/spec.json')
 write(source/'manifest.json',{'spec_sha256':specsha,'source_sha256':'a'*64,'asset_sha256':'b'*64});write(source/'candidate_registry.json',[])
 evaluations=[]
 for i,case in enumerate(old['student_evaluation']['cases']):
  trace=source/f'trace_{i}.npz';trace.write_bytes(b'CPU evidence fixture')
  raw={'trace':{'path':trace.name,'sha256':sha(trace)},'protocol':old['motion_assessment'],'checkpoint_sha256':'a'*64,'asset_sha256':'b'*64,'spec_sha256':specsha,'case':case,'per_env':[{'env':e,'survival_passed':True,'controlled_seconds':30} for e in range(8)]}
  p=source/f'evaluation_{i:02}.json';write(p,raw);evaluations.append({'path':p.name,'sha256':sha(p)})
 write(source/'terminal_report.json',{'status':'COMPLETED','actual_updates':0,'failure':None,'evaluations':evaluations})
 inputs={str(p):sha(p) for p in [parent,parent.with_name('budget.json'),*run.rglob('*')] if p.is_file()}
 new=copy.deepcopy(old);new.update(experiment='recovered',budget={'smoke_updates':49,'formal_updates':1950,'chain_wall_s':63900},motion_training={'partial_smoke_recovery':{'version':PARTIAL_VERSION,'parent_spec':str(parent),'parent_run':str(run),'inputs':inputs,'historical_smoke_updates':1,'historical_wall_s':900,'original_online_limit':2000}})
 return new,parent,run

def test_partial_recovery_reuses_only_source_and_preserves_historical_bytes(tmp_path):
 spec,parent,run=fixture(tmp_path);before={p:p.read_bytes() for p in [parent,parent.with_name('budget.json'),*run.rglob('*')] if p.is_file()}
 result=verify_partial(spec);assert result['status']=='VERIFIED_SOURCE_ONLY' and result['remaining_smoke_updates']==49
 assert not result['wiring_passed'] and not result['capability_accepted']
 assert all(p.read_bytes()==data for p,data in before.items())
 from native_stand.command_v6.wiring import completed_smoke
 assert completed_smoke({'attempts':{}},spec) is False

@pytest.mark.parametrize('field,value',[(('budget','smoke_updates'),50),(('budget','formal_updates'),1951),(('budget','chain_wall_s'),64800),(('reward',),{'changed':True})])
def test_partial_recovery_rejects_reset_budget_or_behavior(tmp_path,field,value):
 spec,_,_=fixture(tmp_path)
 if len(field)==2:spec[field[0]][field[1]]=value
 else:spec[field[0]]=value
 with pytest.raises(ValueError):verify_partial(spec)

def test_partial_recovery_rejects_changed_raw_and_duplicate_claim(tmp_path):
 spec,parent,run=fixture(tmp_path);raw=run/'source_eval/evaluation_00.json';raw.write_text('{}')
 with pytest.raises(ValueError,match='SHA'):verify_partial(spec)
 spec,parent,run=fixture(tmp_path/'again');claims=parent.parent.parent/'.motion_wiring_recovery_claims';claims.mkdir()
 (claims/(sha(parent)+'.json')).write_text(json.dumps({'destination':'another'}))
 with pytest.raises(ValueError,match='claimed'):verify_partial(spec)
