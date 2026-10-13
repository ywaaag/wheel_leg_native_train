"""人工工作台CLI：冻结独立源码，复用公共prepare/授权/supervisor/play。"""
import argparse,copy,hashlib,json,os,re,shutil,subprocess,sys,tomllib,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
PYTHON=Path('/home/kellen/anaconda3/envs/issaclab/bin/python')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def project_path(value):
    p=(ROOT/value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    if not p.is_relative_to(ROOT):raise ValueError('只允许本项目内路径：'+str(p))
    return p

def settings(path):
    d=tomllib.loads(Path(path).read_text())
    required={'purpose','mode','teacher_prefix_s','formal_updates','learning_rate','seed','chain_wall_s','source_checkpoint','source_parent_spec','physical_gpu','resource_mode'}
    if set(d)!=required:raise ValueError('settings.toml字段缺失/未知：'+str(set(d)^required))
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,55}',d['purpose']):raise ValueError('purpose只用小写英文、数字、下划线')
    if d['mode'] not in ('swing','standing','bridge'):raise ValueError('mode必须swing/standing/bridge')
    if type(d['formal_updates']) is not int or not 6<=d['formal_updates']<=300:raise ValueError('formal_updates必须6..300')
    if type(d['seed']) is not int or not 0<=d['seed']<2**31:raise ValueError('seed必须有效整数')
    if type(d['chain_wall_s']) is not int or not 2400<=d['chain_wall_s']<=14400:raise ValueError('chain_wall_s必须2400..14400')
    if not isinstance(d['learning_rate'],(float,int)) or not 1e-6<=d['learning_rate']<=1e-3:raise ValueError('learning_rate必须1e-6..1e-3')
    if not 0<=d['teacher_prefix_s']<=1.8 or abs(d['teacher_prefix_s']*100-round(d['teacher_prefix_s']*100))>1e-8:raise ValueError('前缀必须0..1.8秒且10ms对齐')
    if d['physical_gpu']!=0 or d['resource_mode']!='shared':raise ValueError('人工入口只支持GPU0共享，不抢占或换卡')
    for k in ('source_checkpoint','source_parent_spec'):
        p=project_path(d[k])
        if not p.is_file():raise FileNotFoundError(k+': '+str(p))
    return d

def patch(path,old,new):
    text=Path(path).read_text()
    if text.count(old)!=1:raise ValueError('公共接口变化，请更新人工适配，不静默绕过：'+str(path)+' / '+old[:70])
    Path(path).write_text(text.replace(old,new,1))

def make_bundle(folder,d):
    source=folder/'src/native_stand';shutil.copytree(ROOT/'src/native_stand',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    st=source/'students';shutil.copy2(WORK/'reward.py',st/'manual_reward.py');shutil.copy2(WORK/'runtime_support.py',st/'manual_support.py')
    shutil.copy2(WORK/'continuation_contract.py',st/'manual_steps_contract.py')
    import torch
    cp=torch.load(project_path(d['source_checkpoint']),map_location='cpu',weights_only=False)
    parent=json.loads(project_path(d['source_parent_spec']).read_text())
    if cp.get('interface_version')!='multiskill_mcu_v2' or cp.get('role')!='RecoveryStudent' or cp.get('spec_sha256')!=digest(project_path(d['source_parent_spec'])) or cp.get('asset_sha256')!=parent.get('asset_sha256'):raise ValueError('来源必须31D Recovery训练checkpoint及其自己的冻结spec；不要猜谱系')
    if cp.get('training_recipe')!=parent.get('student_training'):raise ValueError('来源checkpoint与冻结recipe不同')
    (st/'manual_parameters.py').write_text('SETTINGS = '+repr(d)+'\nREWARD_SHA = '+repr(digest(WORK/'reward.py'))+'\nSOURCE_TRAINING_RECIPE = '+repr(cp.get('training_recipe'))+'\n')
    patch(st/'course.py','def recipe_for(state,task):','def recipe_for(state,task):\n if task.get("manual_experiment"):\n  from .manual_support import RECIPE\n  return RECIPE')
    patch(st/'training_recipe.py','def declaration(version=VERSION,source_actor_sha256=None):','def declaration(version=VERSION,source_actor_sha256=None):\n if version=="manual_recovery_ppo_v1":\n  from .manual_support import recipe\n  return recipe(source_actor_sha256)')
    patch(st/'recovery_task.py','def configuration(version=VERSION):','def configuration(version=VERSION):\n if version=="manual_recovery_reward_v1":\n  from .manual_support import configuration as manual_configuration\n  return manual_configuration(configuration(CONTACT_SUFFIX_VERSION))')
    marker=' if cfg!=configuration(cfg.get(\'version\')):raise ValueError(\'student reward configuration differs\')'
    body=''' if cfg.get('version')=='manual_recovery_reward_v1':
  if cfg!=configuration(cfg['version']):raise ValueError('manual reward config differs')
  context=locals().copy()
  base=reward(height,h0,angles,contacts,clearance,torque,previous_targets,executed_targets,angular_body,velocity_native,yaw,entered,controlled,fault,entry_event,success_event,failure_event,reward_configuration=configuration(CONTACT_SUFFIX_VERSION),active_leg_q=active_leg_q)
  from .manual_support import evaluate
  return evaluate(context,base,cfg)
'''
    patch(st/'recovery_task.py',marker,body+marker)
    patch(st/'ppo.py','learning_rate=3e-5,schedule=',f'learning_rate={d["learning_rate"]!r} if recipe.get("version")=="manual_recovery_ppo_v1" else 3e-5,schedule=')
    p=st/'course_io.py'
    marker=" ab=task.get('temporal_ab')"
    patch(p,marker," if task.get('manual_experiment'):\n  from .manual_parameters import SETTINGS\n  formal=SETTINGS['formal_updates']\n"+marker)
    marker=" s['student_evaluation']={'version':'student_course_evaluation_v1'"
    text=p.read_text();position=text.index(marker)
    text=text[:position]+" if task.get('manual_experiment'):\n  from .manual_support import budget as manual_budget\n  s['budget'].update(manual_budget(resume));s['ppo']['learning_rate']=task['manual_experiment']['settings']['learning_rate'];s['seed']=task['manual_experiment']['settings']['seed']\n"+text[position:];p.write_text(text)
    marker=" if task.get('temporal_ab'):\n  from .temporal_ab_io import finish"
    patch(p,marker," if task.get('manual_experiment'):\n  from .manual_support import finish\n  return finish(spec_path,chain,chain_status,failure)\n"+marker)
    p=st/'course_requests.py'
    patch(p,"task.get('authorization')!='AUTHORIZED' or task.get('project_root')", "(task.get('authorization')!='AUTHORIZED' and not task.get('manual_experiment')) or task.get('project_root')")
    marker="  if any(spec['ppo'].get(k)!=v for k,v in expected_ppo.items())"
    text=p.read_text();position=text.index(marker);text=text[:position]+"  if task.get('manual_experiment'):expected_ppo['learning_rate']=task['manual_experiment']['settings']['learning_rate']\n"+text[position:];p.write_text(text)
    marker="  formal=100 if ab else min(300,600-state['stage_A_updates']) if state['stage']=='A' else 300"
    patch(p,marker,marker+"\n  if task.get('manual_experiment'):formal=task['manual_experiment']['settings']['formal_updates']")
    marker="  expected_budget=dict(source_eval_updates=0,smoke_updates=smoke,formal_updates=formal,sample_limit=(formal+smoke)*8192,source_eval_wall_s=900,smoke_wall_s=900 if smoke else 0,formal_wall_s=12600 if smoke else 13500,chain_wall_s=14400)"
    replacement="  expected_budget=dict(source_eval_updates=0,smoke_updates=smoke,formal_updates=formal,sample_limit=(formal+smoke)*8192,source_eval_wall_s=900,smoke_wall_s=900 if smoke else 0,formal_wall_s=12600 if smoke else 13500,chain_wall_s=14400)\n  if task.get('manual_experiment'):\n   from .manual_support import budget as manual_budget\n   expected_budget=manual_budget(c['resume'])"
    patch(p,marker,replacement)
    marker=" if task.get('authorization')!='AUTHORIZED' or task.get('session')!=spec['authorization']['hapi_session']"
    text=p.read_text();position=text.index(marker);text=text[:position]+" if task.get('manual_experiment'):\n  from .manual_support import verify_task as verify_manual_task\n  return verify_manual_task(spec,task,path)\n"+text[position:];p.write_text(text)
    patch(st/'training_evidence.py',
          "if spec['recovery_course']['state']['stage']=='B':",
          "if spec['recovery_course']['state']['stage']=='B' and (spec['recovery_course']['state']['prefix']>0 or spec['recovery_course']['state']['previous_prefix']>0):")
    patch(st/'course_io.py',
          "'early_end_allowed':True}", "'early_end_allowed':False}")
    # Ancestor pyproject.toml injects shared src; test the actual frozen snapshot.
    # This change stays inside the manual bundle, preserving active shared code.
    patch(source/'command_v6/tools/validate_frozen_cpu.py',
          "args=[sys.executable,'-m','pytest','-q','--tb=short',*tests]",
          "args=[sys.executable,'-m','pytest','-q','--tb=short','-o','pythonpath='+str(snapshot),*tests]")
    # Tests are part of a normal public frozen-CPU package, not a private trainer.
    tests=folder/'tests';tests.mkdir();shutil.copy2(ROOT/'tests/conftest.py',tests/'conftest.py')
    for name in ('test_manual_recovery_runtime.py','test_student_recovery_runtime_parent.py','test_recovery_controlled_ppo.py','test_student_course_runtime.py'):shutil.copy2(ROOT/'tests'/name,tests/name)
    return source.parent

def invoke(command,env,*,stdout=None):
    result=subprocess.run([str(PYTHON),*command],env=env,cwd=ROOT,stdout=stdout,stderr=None)
    if result.returncode:raise RuntimeError('命令失败('+str(result.returncode)+')：'+' '.join(command))
    return result

def prepare(config,write_files):
    d=settings(config);count=d['formal_updates']+12
    proposal={'settings':d,'reward_file':str(WORK/'reward.py'),'reward_sha256':digest(WORK/'reward.py'),'source_sha256':digest(project_path(d['source_checkpoint'])),'online_updates_max':count,'samples_max':count*8192,'wall_s':d['chain_wall_s'],'storage_max_bytes':2*2**30,'simulation':0,'ledger_authorization':'UNAUTHORIZED','write_files':write_files}
    if not write_files:return proposal
    from native_stand.command_v6.domain.experiment_naming import new_experiment_name
    name=new_experiment_name(d['purpose']);folder=WORK/'experiments'/name
    if folder.exists():raise FileExistsError(folder)
    folder.mkdir();shutil.copy2(config,folder/'settings.toml');shutil.copy2(WORK/'reward.py',folder/'reward.py')
    bundle=make_bundle(folder,d);env={**os.environ,'PYTHONPATH':str(bundle),'PYTHONDONTWRITEBYTECODE':'1','HAPI_SESSION_ID':'manual-'+uuid.uuid4().hex}
    save(folder/'inputs.json',proposal)
    code='''import json,sys
from pathlib import Path
from native_stand.students.course import initial_state,plan,VERSION
from native_stand.students.course_io import prepare_block
from native_stand.students.data import sha
from native_stand.command_v6.completion import write
from native_stand.students.manual_parameters import SETTINGS,REWARD_SHA
folder=Path(sys.argv[1]);root=Path('/home/kellen/wheel_leg_native_train');d=SETTINGS
source=(root/d['source_checkpoint']).resolve();parent=(root/d['source_parent_spec']).resolve();base=json.load(open(parent))
state=initial_state();state.update(stage='A' if d['mode']=='standing' else 'B',prefix=round(d['teacher_prefix_s']*100) if d['mode']=='bridge' else 0,previous_prefix=round(d['teacher_prefix_s']*100) if d['mode']=='bridge' else 0)
task={'version':VERSION,'plan':plan(),'authorization':'UNAUTHORIZED','session':__import__('os').environ['HAPI_SESSION_ID'],'physical_gpu':0,'gpu_uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72','resource_mode':'shared','project_root':str(root),'source_checkpoint':str(source),'source_sha256':sha(source),'source_parent':str(parent),'source_parent_sha256':sha(parent),'teachers':base['student_teachers'],'stop_file':str(folder/'STOP'),'notification_enabled':False,'user_scope':'人工独立实验尚未登记运行授权','manual_experiment':{'version':'manual_experiment_v1','settings':d,'reward_sha256':REWARD_SHA}}
write(folder/'task_manifest.json',task);write(folder/'task_ledger.json',{'version':VERSION,'status':'READY','state':state,'active_spec':None,'blocks':[],'totals':{'updates':0,'samples':0,'effective_actor_samples':0,'wall_s':0.,'score_episodes':0},'smoke_evidence':{},'next_decision':None})
r=prepare_block(folder/'task_manifest.json',state=state,write_files=True,output=root/'configs/experiments'/folder.name)
r.update(session=task['session'],bundle=str(folder/'src'),task_manifest=str(folder/'task_manifest.json'),run=str(root/'runs'/folder.name),block_wall_s=d['chain_wall_s'],total_update_limit=d['formal_updates']+12)
write(folder/'experiment.json',r);print(json.dumps(r,ensure_ascii=False))
'''
    invoke(['-c',code,str(folder)],env)
    # Run real public schema/planner and PORTABLE regression over the generated bundle.
    info=json.load(open(folder/'experiment.json'))
    validate_cmd=['-m','native_stand.command_v6.tools.validate_frozen_cpu','--spec',info['spec'],'--output-dir',str(folder/'cpu_validation'),'--test','tests/test_manual_recovery_runtime.py','--test','tests/test_student_recovery_runtime_parent.py','--test','tests/test_recovery_controlled_ppo.py','--test','tests/test_student_course_runtime.py','--write']
    with (folder/'cpu_validation_output.json').open('w') as stream:invoke(validate_cmd,{**env,'MANUAL_BUNDLE_TEST_REQUIRED':'1'},stdout=stream)
    save(WORK/'last_experiment.json',{'experiment':str(folder/'experiment.json')})
    return {**proposal,**info,'CPU_validated':True,'next':'train.sh --run --approve 本人批准本实验GPU0共享及所列预算'}

def selected_experiment(path):
    if path:return project_path(path)
    ref=WORK/'last_experiment.json'
    if not ref.exists():raise ValueError('先执行prepare.sh --write，或--experiment指定experiment.json')
    return project_path(json.load(open(ref))['experiment'])

def train(path,run,approval):
    receipt=selected_experiment(path);info=json.load(open(receipt));env={**os.environ,'PYTHONPATH':info['bundle'],'PYTHONDONTWRITEBYTECODE':'1','HAPI_SESSION_ID':info['session'],'CUDA_VISIBLE_DEVICES':'0'}
    common=['-m','native_stand.command_v6.supervisor','--spec',info['spec'],'--output-dir',info['run'],'--hapi-session',info['session'],'--physical-gpu','0','--resource-mode','shared','--sharing-authorization',approval or '仅规划人工GPU0共享实验，未启动']
    if not run:return invoke(common,env)
    if not approval or not approval.strip():raise ValueError('--run必须同时提供--approve明确人工批准说明')
    validation=json.load(open(receipt.parent/'cpu_validation/validation_result.json'))
    if not validation['passed']:raise ValueError('冻结CPU验证未通过')
    authorized=Path(info['spec']).with_name('authorization_receipt.json').exists()
    # Recheck bundle/test/config inputs exactly as the validated report recorded.
    for file,h in validation['inputs'].items():
        if authorized and Path(file).resolve()==Path(info['spec']).resolve():continue # public receipt verifies registered spec below
        if digest(file)!=h:raise ValueError('prepare后文件变化，请prepare新实验：'+file)
    code='''import json,sys
from pathlib import Path
from native_stand.students.data import sha
from native_stand.command_v6.tools.register_authorization import register
from native_stand.command_v6.completion import write
p=Path(sys.argv[1]);info=json.load(open(p));s=Path(info['spec']);spec=json.load(open(s));budget=s.with_name('budget.json')
request={'approval_id':p.parent.name+'_human','user_scope':sys.argv[2],'session':info['session'],'physical_gpu':0,'gpu_uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72','max_online_updates':spec['budget']['smoke_updates']+spec['budget']['formal_updates'],'max_phase_wall_s':spec['budget']['chain_wall_s'],'arms':[{'spec':str(s),'spec_sha256':sha(s),'budget_sha256':sha(budget)}]}
r=register(request,current_session=info['session'],write=True);write(p.parent/'authorization.json',r)
l=p.parent/'task_ledger.json';b=json.load(open(l));b.update(status='RUNNING',active_spec=str(s.resolve()));write(l,b)
'''
    if authorized:
        b=json.load(open(Path(info['spec']).with_name('budget.json')))
        if b['attempts'] or any(b['used'].values()) or Path(info['spec']).with_name('chain_submission.json').exists():raise ValueError('本实验已提交/消耗，不能重复启动；新实验需prepare新目录')
        invoke(['-c','from native_stand.command_v6.tools.experiment_preparation import verify_publication; import sys; verify_publication(sys.argv[1],authorized=True)',info['spec']],env)
    else:invoke(['-c',code,str(receipt),approval],env)
    with (receipt.parent/'submission_check.json').open('w') as stream:invoke(common+['--check-submission'],env,stdout=stream)
    check=json.load(open(receipt.parent/'submission_check.json'))
    if check['submission_contract']['status']!='READY':raise RuntimeError('资源/身份未就绪，未启动；查看submission_check.json；不循环等待或换卡')
    with (receipt.parent/'submission.json').open('w') as stream:invoke(common+['--launch','--handshake-wait-s','30'],env,stdout=stream)
    print('已提交；查看本实验submission.json。后台owner只运行本块，不自动新开实验。')

def play(pose,run,experiment,checkpoint):
    if experiment:
        info=json.load(open(selected_experiment(experiment)));spec=info['spec'];bundle=info['bundle'];family='swing_candidate_from_historical_r1' if pose=='swing' else 'motion_native_normal'
        if not checkpoint:
            result=Path(info['run'])/'formal/candidate_selection.json'
            if not result.exists():raise ValueError('formal尚无候选，请--checkpoint明确指定')
            checkpoint=json.load(open(result))['best_overall']['checkpoint']
    else:
        row=json.load(open(WORK/'models/catalog.json'))[pose];checkpoint=checkpoint or str(WORK/'models'/row['local_file']);spec=row['spec'];bundle=str(ROOT/'src');family=row['family']
        if Path(checkpoint).resolve()==(WORK/'models'/row['local_file']).resolve() and digest(checkpoint)!=row['sha256']:raise ValueError('参考模型副本已变化，请另存并明确指定来源，不能仍称原候选')
    cp=project_path(checkpoint);env={**os.environ,'PYTHONPATH':bundle,'PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':'0'}
    cmd=['-m','native_stand.command_v6.tools.play','--spec',spec,'--checkpoint',str(cp),'--preview','--strict-identities','--physical-gpu','0','--preview-family',family,'--ground-style','grid','--max-policy-steps','3000','--max-wall-seconds','300']
    return invoke(cmd+(['--run'] if run else []),env)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare');q.add_argument('--config',default=str(WORK/'settings.toml'));q.add_argument('--write',action='store_true')
    q=sub.add_parser('train');q.add_argument('--experiment');q.add_argument('--run',action='store_true');q.add_argument('--approve')
    q=sub.add_parser('play');q.add_argument('--pose',choices=('swing','standing'),default='swing');q.add_argument('--run',action='store_true');q.add_argument('--experiment');q.add_argument('--checkpoint')
    q=sub.add_parser('status');q.add_argument('--experiment')
    q=sub.add_parser('stop');q.add_argument('--experiment');q.add_argument('--confirm',action='store_true')
    a=p.parse_args()
    if a.command=='prepare':print(json.dumps(prepare(a.config,a.write),indent=2,ensure_ascii=False))
    elif a.command=='train':train(a.experiment,a.run,a.approve)
    elif a.command=='play':play(a.pose,a.run,a.experiment,a.checkpoint)
    elif a.command=='stop':
        receipt=selected_experiment(a.experiment)
        if not a.confirm:print('只会停止这个人工实验：'+str(receipt.parent)+'；加--confirm写STOP，不终止其他进程')
        else:(receipt.parent/'STOP').write_text('human requested stop\n');print('已请求本人工任务停止；不删除模型/账本，不kill其他进程')
    else:
        catalog=json.load(open(WORK/'models/catalog.json'));print(json.dumps({'models':catalog,'latest_manual_experiment':json.load(open(WORK/'last_experiment.json')) if (WORK/'last_experiment.json').exists() else None},indent=2,ensure_ascii=False))
        if a.experiment:
            info=json.load(open(selected_experiment(a.experiment)));path=Path(info['run'])/'chain_terminal_report.json'
            print('终态：'+json.load(open(path))['status'] if path.exists() else '没有终态证据；不能仅据此判断进程存活')
if __name__=='__main__':
    try:main()
    except Exception as error:print('人工工作台错误：'+str(error),file=sys.stderr);raise SystemExit(2)
