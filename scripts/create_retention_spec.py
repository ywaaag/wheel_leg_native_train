import copy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'configs/experiments/motion_overnight_20261005/spec.json'
OUT=ROOT/'configs/experiments/motion_retention_20261005'
def sha(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def main():
 from native_stand.command_v6.tools.entrypoints import historical_cli_guard
 historical_cli_guard('scripts/create_retention_spec.py')
 if OUT.exists(): raise FileExistsError(OUT)
 s=json.loads(BASE.read_text()); s['experiment']='motion_retention_20261005'
 s['source_checkpoint']=str(ROOT/'runs/motion_overnight_20261005_retry2/formal/model_update_50.pt')
 s['source_sha256']=sha(s['source_checkpoint']); s['source_update']=50
 s['colleague_config_sha256']=sha(s['colleague_config_path'])
 s['retention']={'enabled':True,'lambda':0.01,'reference_path':str(ROOT/'runs/motion_retention_reference_20261005/reference.pt'),'reference_sha256':'PENDING'}
 s['budget']={'source_eval_wall_s':0,'smoke_wall_s':1800,'formal_wall_s':14400,'source_eval_updates':0,'smoke_updates':1,'formal_updates':50,'sample_limit':409600,'formal_samples':409600,'wall_limit_enabled':True,'terminal_reserve_s':180}
 s['evaluation']={**s['evaluation'],'full_every_updates':25,'checkpoint_every_updates':25,'motion_commands':[[0,0],[.5,0],[-.5,0]],'command_mode':'fixed','motion_protocol':'fixed'}
 OUT.mkdir(); (OUT/'spec.json').write_text(json.dumps(s,indent=2)+'\n'); (OUT/'budget.json').write_text(json.dumps({'authorization':'AUTHORIZED','limits':{'source_eval':0,'smoke':1,'formal':50,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.},indent=2)+'\n')
 print(json.dumps({'spec':str(OUT/'spec.json'),'ledger':str(OUT/'budget.json'),'source_sha256':s['source_sha256']},indent=2))
if __name__=='__main__': main()
