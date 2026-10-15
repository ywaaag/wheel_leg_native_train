"""Explicit terminal-only event subscription for an already running chain.

Systemd path activation, no polling loop; never alter the frozen training spec.
"""
import argparse,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())

def subscription(run,session,approval,unit):
 run=Path(run).resolve();manifest=read(run/'manifest.json')
 if not session or not approval or manifest.get('hapi_session')!=session:raise ValueError('explicit current owner approval required')
 route=manifest.get('notification_route',{})
 if route.get('owner_session')!=session or route.get('target_session')!=session:raise ValueError('owner route mismatch')
 if sha(manifest['spec_path'])!=manifest['spec_sha256']:raise ValueError('submitted spec identity differs')
 return {'version':'terminal_notification_subscription_v1','run':str(run),'session':session,
  'attempt_id':manifest['attempt_id'],'manifest_sha256':sha(run/'manifest.json'),
  'spec_sha256':manifest['spec_sha256'],'approval':approval,'systemd_unit':unit,'created_unix_s':time.time(),
  'scope':'terminal report delivery only; frozen notifications flag is superseded for this run by explicit new approval'}

def deliver(receipt,send=None):
 from native_stand.command_v6.completion import transport,write
 receipt=read(receipt) if isinstance(receipt,(str,Path)) else receipt
 run=Path(receipt['run']);manifest=read(run/'manifest.json')
 if (receipt.get('version')!='terminal_notification_subscription_v1' or not receipt.get('approval')
     or sha(run/'manifest.json')!=receipt['manifest_sha256'] or manifest['attempt_id']!=receipt['attempt_id']
     or manifest.get('hapi_session')!=receipt['session'] or manifest['spec_sha256']!=receipt['spec_sha256']):
  raise ValueError('terminal subscription identity mismatch')
 ready=read(run/'report_ready.json');report=run/'completion_report.md'
 if ready['report_sha256']!=sha(report):raise ValueError('terminal report SHA differs')
 with (run/'hapi_notification.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  path=run/'hapi_notification.json';prior=read(path) if path.exists() else None
  if prior and prior.get('status')!='notification_disabled':
   return prior  # Includes unknown delivery; never retry or duplicate.
  if prior and prior.get('event_id')!=ready['event_id']:raise ValueError('prior notification event differs')
  review=run/'completion_review.json'
  if review.exists() and read(review).get('event_id')==ready['event_id']:return {'status':'reviewed'}
  event={'event_id':ready['event_id'],'session_id':receipt['session'],'status':'sending',
   'subscription_attempt_id':receipt['attempt_id'],'approval':receipt['approval'],'time':time.time()}
  write(path,event)
  status=read(run/'analysis.json').get('status','UNKNOWN')
  message=f"事件ID：{ready['event_id']}\nrun：{run}\n终态：{status}\n报告：{report}\n请读取报告复盘，并按当前有效用户授权处理后续工作。"
  try:event.update((send or transport)(receipt['session'],message))
  except BaseException as exc:event.update(status='unknown_delivery',reason=repr(exc))
  write(path,event);return event

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path);p.add_argument('--receipt',type=Path,required=True)
 p.add_argument('--approval');p.add_argument('--deliver',action='store_true');a=p.parse_args()
 if a.deliver:
  receipt=read(a.receipt)
  try:print(json.dumps(deliver(receipt),ensure_ascii=False))
  finally:
   # Stop only this subscription's path trigger, never a trainer/monitor.
   subprocess.run(['systemctl','--user','stop',receipt['systemd_unit']+'.path'],check=False)
  return
 if not a.run or not a.run.resolve().is_relative_to(ROOT/'runs'):raise ValueError('explicit project run required')
 unit='native-terminal-'+hashlib.sha256(str(a.run.resolve()).encode()).hexdigest()[:12]
 receipt=subscription(a.run,os.environ.get('HAPI_SESSION_ID'),a.approval,unit)
 a.receipt.parent.mkdir(parents=True,exist_ok=True)
 with a.receipt.open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
 command=['systemd-run','--user','--unit='+unit,'--collect','--service-type=oneshot',
          '--path-property=PathExists='+str(a.run.resolve()/'report_ready.json')]
 for name in ('HAPI_SESSION_ID','HAPI_API_URL','HAPI_CLI_EXECUTABLE','PATH'):
  if name in os.environ:command+=['--setenv='+name+'='+os.environ[name]]
 command+=['--setenv=PYTHONPATH='+str(ROOT/'src'),sys.executable,str(Path(__file__).resolve()),
           '--receipt',str(a.receipt.resolve()),'--deliver']
 result=subprocess.run(command,capture_output=True,text=True)
 print(json.dumps({'unit':unit,'receipt':str(a.receipt),'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr},ensure_ascii=False))
 if result.returncode:raise SystemExit(result.returncode)

if __name__=='__main__':main()
