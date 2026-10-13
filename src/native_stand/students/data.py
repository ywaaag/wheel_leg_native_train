"""Audited first-episode teacher transitions; filesystem IO at this adapter only."""
import hashlib,json
from pathlib import Path
import numpy as np
import torch
from .interface import History,frame,task,labels,VERSION
from native_stand.command_v6.domain.trace_schema import VERSION as TRACE,CONTROL,STATE
from native_stand.recovery.motion_handoff import score
B50='46add82fa9d32c04fcc0a8b79c6339a27df3b9ca6c95050b8e13f52b644b7f75'
B250='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'
ASSET='32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7'
RUNS=('2026_10_10-16_44__recovery_motion_b250_handoff_ppo0','2026_10_10-22_24__receiver_window_ppo0')
STAGES=('preparation','turn_lift','dynamic_settle','stable_hold')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def build(root,output,*,version=VERSION):
    if version not in (VERSION,"multiskill_mcu_v2"):raise ValueError("unknown dataset interface")
    mcu=version=="multiskill_mcu_v2"
    from . import mcu_interface
    torch.set_num_threads(4)
    root=Path(root);output=Path(output)
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    packs={r:{k:[] for k in ('x','y','stage','split','episode','sample')} for r in ('RecoveryStudent','MotionZeroStudent' if mcu else 'MotionStudent')}
    manifest={'interface_version':version,'interface_contract':mcu_interface.contract() if mcu else __import__('native_stand.students.interface',fromlist=['contract']).contract(),'teachers':{},'files':{},'episodes':[],'excluded':[],
              'limitations':'31 adjacent-condition successful episodes, not independent recovery configurations or training seeds; Motion zero-command only'}
    for name,key,expected in [('runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_50.pt','B50',B50),('runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt','B250',B250)]:
        assert sha(root/name)==expected;manifest['teachers'][key]={'path':str(root/name),'sha256':expected}
    for ri,runname in enumerate(RUNS):
        run=root/'runs'/runname;readback=json.loads((run/'runtime_readback.json').read_text());spec=json.loads((run/'source_snapshot/spec.json').read_text())
        assert spec['asset_sha256']==ASSET and sha(root/spec['asset_path'])==ASSET
        assert [spec['control'][k] for k in ('physics_dt_s','pd_dt_s','policy_dt_s','leg_kp','leg_kd','wheel_kv')]==[.001,.005,.01,60.,2.,1.]
        assert spec['control']['effort_limits_nm']==[40,40,5.5,40,40,5.5]
        terminal=json.loads((run/'terminal_report.json').read_text());ids=readback['active_indices']
        manifest['files'][str(run/'runtime_readback.json')]=sha(run/'runtime_readback.json');manifest['files'][str(run/'source_snapshot/spec.json')]=sha(run/'source_snapshot/spec.json')
        for condition in terminal['conditions']:
            row=condition['condition'];normal=row['kind']=='normal_motion_baseline'
            wanted=normal or (row.get('recovery')=='B50' and row['switch_s']==.5)
            if not wanted:continue
            path=run/condition['result'];saved=json.loads(path.read_text());trace=run/saved['trace']['path']
            assert saved['field_schema']['state']==TRACE and saved['field_schema']['control']==TRACE
            assert saved['field_schema']['active_indices']==ids and saved['field_schema']['joint_names']==readback['joint_names']
            assert saved['motion_sha256']==B250 and (normal or saved['checkpoint_sha256']==B50)
            assert sha(trace)==saved['trace']['sha256'];manifest['files'][str(path)]=sha(path);manifest['files'][str(trace)]=sha(trace)
            with np.load(trace) as compressed:
                a={key:compressed[key] for key in compressed.files}
            for eid,result in enumerate(saved['per_env']):
                name=f'{runname}/{condition["index"]}/{eid}'
                if not result['accepted']:
                    manifest['excluded'].append({'episode':name,'reason':result['failed_checks'],'diagnostic_only':True});continue
                valid=a['first_episode_valid'][:,eid];indices=np.flatnonzero(valid);s=torch.tensor(a['state'][valid,eid]);p=torch.tensor(a['posture'][valid,eid]);ctrl=a['controller'][valid,eid,0]
                res=score(s,p,torch.tensor(ctrl==2),policy_time_s=torch.tensor(a['policy_time_s'][valid],dtype=s.dtype),configuration=saved['protocol'])
                assert res['accepted'] and res['hold_complete'];stop=res['hold_index_half_open'][1];entry=res['entry_index']
                ref=torch.tensor(readback['reference'][eid:eid+1],dtype=torch.float32);history=History(1)
                role=('MotionZeroStudent' if mcu else 'MotionStudent') if normal else 'RecoveryStudent'
                split=(0 if ri==0 else {20261010:0,20261011:1,20261012:2}[row['seed']]) if not normal else (0 if ri==0 and eid<6 else 1 if ri==0 else 2)
                ep=len(manifest['episodes']);counts=[0]*4;switch=int(np.flatnonzero(ctrl==2)[0])
                for local,absolute in enumerate(indices[:stop]):
                    q=torch.tensor(a['joint_q_pre'][absolute,eid,ids])[None];dq=torch.tensor(a['joint_dq_pre'][absolute,eid,ids])[None]
                    old=torch.tensor(a['recovery_frame'][absolute,eid])[None]
                    previous=torch.tensor(a['target_pre'][absolute,eid])[None]
                    if ctrl[local]==0 and not mcu:previous=torch.cat((ref[:,(0,1,3,4)],torch.zeros(1,2)),-1)
                    f=frame(old[:,:3]/.25,old[:,3:6],q,dq,previous[:,:4],previous[:,4:],ref)
                    history.append(f,torch.tensor([a['policy_time_s'][absolute]],dtype=torch.float64))
                    if mcu:
                        cmd=mcu_interface.task('Motion' if normal else 'Recovery',torch.tensor([[0.,0.,.40]]))
                        x=mcu_interface.actor_input(f,cmd)[0]
                    else:
                        cmd=task('Motion' if normal else 'Recovery',torch.tensor([[0.,0.,.40 if normal else .36,0.,0.]]));x=history.encode(cmd)[0]
                    if ctrl[local]==0:continue
                    ct=torch.tensor(a['control'][absolute,eid]);leg=ct[CONTROL['leg_target_after_limit']][None];wheel=ct[CONTROL['clipped_action']][[2,5]][None]*100.
                    y=labels(leg,wheel,ref)[0]
                    stage=3 if local>entry else 0 if ctrl[local]==1 else 1 if local-switch<25 else 2
                    for k,v in [('x',x),('y',y),('stage',stage),('split',split),('episode',ep),('sample',int(absolute))]:packs[role][k].append(v)
                    counts[stage]+=1
                manifest['episodes'].append({'id':ep,'name':name,'role':role,'split':['train','validation','test'][split],'stage_unique_counts':counts,'source_case_seed':row['seed'],'asset_sha256':ASSET,'command':[0,0,.40 if mcu or normal else .36],'teacher_original_height_command_m':.40 if normal else .36,'student_height_reencoding_only':mcu,'first_episode':True,'score_protocol':saved['protocol']})
    for role,pack in packs.items():
        data={k:torch.stack(v) if k in ('x','y') else torch.tensor(v) for k,v in pack.items()};torch.save(data,output/(role+'.pt'))
        manifest[role]={'file':role+'.pt','sha256':sha(output/(role+'.pt')),'unique_samples':len(data['x']),
            'split_stage_counts':{split:{stage:int(((data['split']==si)&(data['stage']==st)).sum()) for st,stage in enumerate(STAGES)} for si,split in enumerate(('train','validation','test'))}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
