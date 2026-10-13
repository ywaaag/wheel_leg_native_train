"""人工分步工具。每次仅执行所选步骤；从不自动提交训练。"""
import argparse,json,os,shlex,shutil,subprocess,sys,uuid
from pathlib import Path
import workbench as w

def read(path):return json.loads(Path(path).read_text())
def modules(root):return {str(p.relative_to(root)):w.digest(p) for p in sorted(Path(root).rglob('*.py'))}
def source_identity(settings):
 import torch
 cp=torch.load(w.project_path(settings['source_checkpoint']),map_location='cpu',weights_only=False)
 parent=read(w.project_path(settings['source_parent_spec']))
 if cp.get('interface_version')!='multiskill_mcu_v2' or cp.get('role')!='RecoveryStudent' or cp.get('spec_sha256')!=w.digest(w.project_path(settings['source_parent_spec'])) or cp.get('asset_sha256')!=parent.get('asset_sha256') or cp.get('training_recipe')!=parent.get('student_training'):
  raise ValueError('来源checkpoint、自己的冻结spec、31D角色或recipe身份不同')
 return cp

def init_source(config,write):
 d=w.settings(config);folder=w.WORK/'editable'
 if not write:return {'action':'init-source','destination':str(folder),'write':False,'simulation':0}
 if folder.exists():raise FileExistsError('可编辑源码已存在，不覆盖：'+str(folder))
 folder.mkdir();bundle=w.make_bundle(folder,d)
 w.save(folder/'origin.json',{'version':'manual_editable_source_v1','original_shared_modules':modules(w.ROOT/'src/native_stand'),'note':'mutable human workspace; experiments use separate immutable copies'})
 return {'editable_src':str(bundle),'reward_file':str(bundle/'native_stand/students/manual_reward.py'),'simulation':0}

def freeze(config,write):
 d=w.settings(config);source=w.WORK/'editable/src'
 if not source.exists():raise ValueError('先单独init-source --write，再编辑源码')
 cp=source_identity(d)
 from native_stand.command_v6.domain.experiment_naming import new_experiment_name
 name=new_experiment_name(d['purpose']);folder=w.WORK/'experiments'/name
 proposal={'action':'freeze','folder':str(folder),'settings':d,'source_dir':str(source),'simulation':0,'write':write}
 if not write:return proposal
 if folder.exists():raise FileExistsError(folder)
 folder.mkdir();shutil.copytree(source,folder/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'));shutil.copytree(w.WORK/'editable/tests',folder/'tests')
 shutil.copy2(config,folder/'settings.toml')
 st=folder/'src/native_stand/students';h=w.digest(st/'manual_reward.py')
 (st/'manual_parameters.py').write_text('SETTINGS = '+repr(d)+'\nREWARD_SHA = '+repr(h)+'\nSOURCE_TRAINING_RECIPE = '+repr(cp['training_recipe'])+'\n')
 draft={'version':'manual_step_draft_v1','folder':str(folder),'bundle':str(folder/'src'),'settings':d,'reward_sha256':h,'source_sha256':w.digest(w.project_path(d['source_checkpoint'])),'session':'manual-'+uuid.uuid4().hex,'resume':False,'modules':modules(folder/'src/native_stand')}
 w.save(folder/'draft.json',draft)
 return {**proposal,'draft':str(folder/'draft.json'),'next_step':'publish; not validated or authorized'}

def environment(info):
 values={'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':info['bundle'],'HAPI_SESSION_ID':info['session'],'CUDA_VISIBLE_DEVICES':'0','MANUAL_PYTHON':str(w.PYTHON),'MANUAL_SPEC':info['spec'],'MANUAL_RUN':info['run'],'MANUAL_EXPERIMENT':str(Path(info['task_manifest']).with_name('experiment.json')),'MANUAL_EXPECTED_GPU_UUID':read(info['task_manifest'])['gpu_uuid']}
 return ''.join('export '+k+'='+shlex.quote(str(v))+'\n' for k,v in values.items())

def invoke(info,args,**kwargs):
 return w.invoke(args,{**os.environ,'PYTHONPATH':info['bundle'],'PYTHONDONTWRITEBYTECODE':'1','HAPI_SESSION_ID':info['session'],'MANUAL_BUNDLE_TEST_REQUIRED':'1'},**kwargs)

def publish(draft_path,write):
 draft=read(w.project_path(draft_path));folder=Path(draft['folder'])
 if modules(Path(draft['bundle'])/'native_stand')!=draft['modules']:raise ValueError('冻结源码改变，请从editable重新freeze，不编辑冻结副本')
 if not write:return {'draft':str(draft_path),'action':'publish','write':False,'simulation':0}
 if (folder/'experiment.json').exists():raise FileExistsError('此草稿已经发布')
 invoke(draft,[str(w.WORK/'step_runtime.py'),'publish',str(Path(draft_path).resolve())],stdout=subprocess.PIPE)
 info=read(folder/'experiment.json');(folder/'session.env').write_text(environment(info))
 return {'experiment':str(folder/'experiment.json'),'session_env':str(folder/'session.env'),'next_step':'validate; ledger UNAUTHORIZED','simulation':0}

def validate(path,write):
 info=read(w.project_path(path));folder=Path(path).resolve().parent
 if not write:return {'action':'validate','write':False,'simulation':0}
 command=['-m','native_stand.command_v6.tools.validate_frozen_cpu','--spec',info['spec'],'--output-dir',str(folder/'cpu_validation')]
 for name in ('test_manual_recovery_runtime.py','test_student_recovery_runtime_parent.py','test_recovery_controlled_ppo.py','test_student_course_runtime.py'):command+=['--test','tests/'+name]
 with (folder/'cpu_validation_output.json').open('x') as stream:invoke(info,command+['--write'],stdout=stream)
 report=read(folder/'cpu_validation/validation_result.json')
 return {'passed':report['passed'],'tests':report['tests_result']['stdout'],'next_step':'plan, then explicit authorization; nothing submitted','simulation':0}

def authorize(path,approval,write):
 if not approval or not approval.strip():raise ValueError('请明确--approve批准说明')
 info=read(w.project_path(path));folder=Path(path).resolve().parent;report=read(folder/'cpu_validation/validation_result.json')
 if not report['passed']:raise ValueError('CPU验证未通过')
 for p,h in report['inputs'].items():
  if w.digest(p)!=h:raise ValueError('CPU验证后文件改变：'+p)
 args=[str(w.WORK/'step_runtime.py'),'authorize',str(Path(path).resolve()),'--approve',approval]+(['--write'] if write else [])
 result=invoke(info,args,stdout=subprocess.PIPE)
 return {'action':'authorize','registration':json.loads(result.stdout),'write':write,'submitted':False,'next_step':'resource check, then separate supervisor launch','simulation':0}

def resume(parent_path,checkpoint,write):
 parent=read(w.project_path(parent_path));spec=read(parent['spec']);folder=Path(parent_path).resolve().parent
 if not (Path(parent['bundle'])/'native_stand/students/manual_steps_contract.py').exists():raise ValueError('这是旧版工作台，缺少完整续训契约；只能Actor迁移到新版新实验')
 if not write:return {'action':'resume-draft','parent':str(parent_path),'checkpoint':checkpoint,'write':False,'simulation':0}
 # Verification runs under the identical source bundle; no optimizer or simulation.
 args=[str(w.WORK/'step_runtime.py'),'resume',str(Path(parent_path).resolve()),str(w.project_path(checkpoint))]
 result=invoke(parent,args,stdout=subprocess.PIPE)
 return {'action':'resume-draft',**json.loads(result.stdout),'note':'之后手动publish/validate/authorize/launch','simulation':0}

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='step',required=True)
 for name in ('init-source','freeze'):
  a=sub.add_parser(name);a.add_argument('--config',default=str(w.WORK/'settings.toml'));a.add_argument('--write',action='store_true')
 a=sub.add_parser('publish');a.add_argument('--draft',required=True);a.add_argument('--write',action='store_true')
 for name in ('validate','authorize','env','inspect'):
  a=sub.add_parser(name);a.add_argument('--experiment',required=True)
  if name in ('validate','authorize'):a.add_argument('--write',action='store_true')
  if name=='authorize':a.add_argument('--approve',required=True)
 a=sub.add_parser('resume');a.add_argument('--experiment',required=True);a.add_argument('--checkpoint',required=True);a.add_argument('--write',action='store_true')
 a=p.parse_args()
 if a.step=='init-source':r=init_source(a.config,a.write)
 elif a.step=='freeze':r=freeze(a.config,a.write)
 elif a.step=='publish':r=publish(a.draft,a.write)
 elif a.step=='validate':r=validate(a.experiment,a.write)
 elif a.step=='authorize':r=authorize(a.experiment,a.approve,a.write)
 elif a.step=='resume':r=resume(a.experiment,a.checkpoint,a.write)
 elif a.step=='env':print(environment(read(w.project_path(a.experiment))),end='');return
 else:
  i=read(w.project_path(a.experiment));s=read(i['spec']);b=read(i['ledger']);selection=Path(i['run'])/'formal/candidate_selection.json';terminal=Path(i['run'])/'chain_terminal_report.json'
  r={'experiment':i,'budget':b,'recipe':s['student_training'],'source_checkpoint':s['source_checkpoint'],'terminal':read(terminal) if terminal.exists() else 'NO_TERMINAL_EVIDENCE','selection':read(selection) if selection.exists() else None}
 print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as exc:print('人工步骤失败：'+str(exc),file=sys.stderr);raise SystemExit(2)
