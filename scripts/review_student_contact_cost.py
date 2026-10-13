"""Offline named-schema replay of the v10 hold-contact addition. No simulator."""
import argparse,json
from pathlib import Path
import numpy as np
from native_stand.students.data import sha
from native_stand.command_v6.domain.trace_schema import STATE
from native_stand.students.recovery_task import configuration,CONTACT_SUFFIX_VERSION

def review(paths):
 rows=[]
 for path in paths:
  path=Path(path);result=json.loads(path.read_text());trace=path.parent/result['trace']['path']
  if sha(trace)!=result['trace']['sha256'] or result['field_schema'].get('state') is None:raise ValueError('trace identity/schema missing')
  a=np.load(trace);s=a['state'];valid=a['first_episode_valid'];owner=a['controller'].squeeze(-1)
  for env,r in enumerate(result['per_env']):
   entry=r['entry_index'];mask=valid[:,env]&(owner[:,env]==3)
   entered=np.arange(len(s))>=entry if entry is not None else np.zeros(len(s),bool)
   hold=mask&entered;contacts=s[:,env,[STATE['left_contact_n'],STATE['right_contact_n']]]
   raw=np.square(np.clip((2.-contacts)/2.,0.,1.)).mean(-1)*hold
   rows.append({'case':result['case']['case_id'],'env':env,'entry_index':entry,'student_samples':int(mask.sum()),'entered_samples':int(hold.sum()),'contact_deficit_samples':int((raw>0).sum()),'added_density_mean_per_s':float((-raw[hold]*.2).mean()) if hold.any() else 0.,'added_reward_sum':float((-raw*.2*.01).sum()),'accepted_before_change':r['accepted'],'source_evaluation':str(path),'evaluation_sha256':sha(path),'trace_sha256':sha(trace)})
 return {'version':'student_contact_cost_replay_v1','configuration':configuration(CONTACT_SUFFIX_VERSION)['hold_contact_deficit'],'rows':rows,'simulation':0,'optimizer_updates':0,'interpretation':'offline cost only; not evidence of learning improvement; force is sensor resultant, not certified normal load'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evaluation',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 result=review(a.evaluation);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'rows':len(result['rows']),'output':str(a.output),'simulation':0,'optimizer_updates':0}))
