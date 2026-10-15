"""View frozen reward curves; exclusive output, no run/ledger mutation."""
import argparse,hashlib,json
from pathlib import Path
from native_stand.students.motion_reward_audit import audit

def snapshot(spec):
 result=audit(spec['reward'])
 from native_stand.students import motion_tracking_reward
 path=Path(motion_tracking_reward.__file__)
 result.update(experiment=spec['experiment'],source_sha256=spec['source_sha256'],reward_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),runtime_implementation=str(path),
  scoring_protocol=spec['motion_assessment'],sample_time_s=spec['control']['policy_dt_s'])
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
 spec=json.loads(a.spec.read_text());result=snapshot(spec);result['spec_sha256']=hashlib.sha256(a.spec.read_bytes()).hexdigest()
 if a.output:
  with a.output.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False)
  print(a.output)
 else:print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
