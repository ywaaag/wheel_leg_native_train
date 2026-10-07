#!/usr/bin/env python3
"""Run a bounded, resumable PPO=0 checkpoint sweep."""
import argparse, hashlib, json, os, subprocess, sys, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SWEEP=ROOT/'runs/recovery_checkpoint_sweep_20261004'
FORMAL=ROOT/'runs/recovery_level_from1000_20261003/formal'
UPDATES=list(range(100,500,100))+list(range(600,1000,100))+list(range(1100,1500,100))+list(range(1600,2000,100))

def notify(session, summary):
    event_id=uuid.uuid4().hex
    event={'event_id':event_id,'status':'pending','session_id':session,'time':time.time()}
    (SWEEP/'sweep_notification.json').write_text(json.dumps(event,indent=2)+'\n')
    if not session:
        event.update(status='notification_not_configured')
    else:
        message=(f'闭链 checkpoint sweep 已结束\n事件ID：{event_id}\n'
                 f'结果：{SWEEP}/sweep_summary.json\n'
                 f'可继续训练：请先读取 sweep_summary.json；本通知不自动续训。')
        try:
            p=subprocess.run(['hapi','ping-peer',session,'--message',message],capture_output=True,text=True,timeout=20)
            event.update(status='sent' if p.returncode==0 else 'failed',returncode=p.returncode,stderr=p.stderr[-500:])
        except Exception as exc:
            event.update(status='unknown_delivery',error=repr(exc))
    (SWEEP/'sweep_notification.json').write_text(json.dumps(event,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--hapi-session',default=os.environ.get('HAPI_SESSION_ID')); args=parser.parse_args()
    results=[]
    for u in UPDATES:
        out=SWEEP/'results'/f'update_{u}'
        result=out/'result.json'
        if result.is_file():
            try: results.append(json.loads(result.read_text())|{'update':u,'status':'COMPLETED'}); continue
            except Exception: pass
        spec=json.loads((SWEEP/'specs'/f'spec_{u}.json').read_text())
        ck=FORMAL/f'model_update_{u}.pt'; sha=hashlib.sha256(ck.read_bytes()).hexdigest()
        spec['source_checkpoint']=str(ck); spec['source_sha256']=sha; spec['source_input_dim']=150; spec['source_update']=u
        spec_path=SWEEP/'specs'/f'spec_{u}.json'; spec_path.write_text(json.dumps(spec,indent=2)+'\n')
        budget={'authorization':'AUTHORIZED','limits':{'source_eval':0,'smoke':0,'formal':0,'evaluate':1,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{}}
        (SWEEP/'specs'/'budget.json').write_text(json.dumps(budget,indent=2)+'\n')
        log=SWEEP/'results'/f'update_{u}.log'; out.parent.mkdir(parents=True,exist_ok=True)
        cmd=[sys.executable,'-m','native_stand.recovery.probe','--spec',str(spec_path),'--output-dir',str(out),'--mode','checkpoint','--checkpoint',str(ck),'--seconds','10','--run']
        with log.open('w') as stream:
            p=subprocess.run(cmd,cwd=ROOT,env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')},stdout=stream,stderr=subprocess.STDOUT,timeout=900)
        if result.is_file():
            try: results.append(json.loads(result.read_text())|{'update':u,'status': 'COMPLETED' if p.returncode==0 else 'FAILED'}); continue
            except Exception: pass
        results.append({'update':u,'status':'FAILED','returncode':p.returncode,'log':str(log)})
    summary={'updates':UPDATES,'results':results,'completed_at':time.time()}
    (SWEEP/'sweep_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (SWEEP/'READY_FOR_TRAINING').write_text('All checkpoint evaluations attempted. Review sweep_summary.json before training.\n')
    notify(args.hapi_session,summary)

if __name__=='__main__': main()
