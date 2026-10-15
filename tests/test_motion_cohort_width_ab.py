import copy
import importlib.util
from pathlib import Path

import torch
import json
import os
from types import SimpleNamespace

from native_stand.command_v6.domain.command_schedule import effective
from native_stand.command_v6.domain.tracking_width import linear_width
from native_stand.command_v6.domain.reward import compute
from native_stand.command_v6.completion import choose

ROOT=Path(__file__).resolve().parents[1]


def test_episode_target_selection_never_narrows_new_ramp():
    target=torch.tensor([[0.,0.],[.5,0.],[-.5,0.],[1.,0.],[-1.,0.],[0.,1.]])
    config={'linear_error_denominator':1.,'linear_cohort_width':{
        'retained_commands':[[0,0],[.5,0],[-.5,0]],'retained_denominator':.04}}
    before=target.clone()
    for time in (0.,2.,10.,28.,30.):
        command=effective(target,torch.full((6,),time),entry=1,ramp=2,hold=24,exit=2)
        width=linear_width(target,config)
        torch.testing.assert_close(width,torch.tensor([.04,.04,.04,1.,1.,1.]))
        if time==2:
            assert command[3,0]==.5 and width[3]==1.
    torch.testing.assert_close(target,before)
    assert linear_width(target,{'linear_error_denominator':1.})==1.


def test_reward_only_linear_kernel_changes_per_cohort():
    n=5
    target=torch.tensor([[0.,0.],[.5,0.],[-.5,0.],[1.,0.],[-1.,0.]])
    width=linear_width(target,{'linear_error_denominator':1.,'linear_cohort_width':{
        'retained_commands':[[0,0],[.5,0],[-.5,0]],'retained_denominator':.04}})
    command=torch.cat((target,torch.full((n,1),.4)),dim=-1)
    args=(torch.full((n,),.4),torch.ones(n),target[:,0]+.2,torch.zeros(n),torch.zeros(n),
          command,torch.ones(n,2,dtype=torch.bool),torch.zeros(n,6),torch.zeros(n,6),
          torch.zeros(n,6),torch.zeros(n,4),torch.zeros(n,dtype=torch.bool))
    kwargs=dict(weights={'upright':2.,'height':2.,'velocity_tracking':8.,'two_wheel_contact':.5,
        'effort':-.02,'action_delta':-.01,'joint_margin':-.05},height_width=.06,
        yaw_denominator=.09,terminal_penalty=-1.,dt=.01)
    total_a,raw_a,_=compute(*args,linear_denominator=1.,**kwargs)
    total_b,raw_b,_=compute(*args,linear_denominator=width,**kwargs)
    for key in raw_a:
        if key!='velocity_tracking':
            torch.testing.assert_close(raw_a[key],raw_b[key])
    torch.testing.assert_close(raw_b['velocity_tracking'][:3],torch.full((3,),torch.exp(torch.tensor(-1.)).item()))
    torch.testing.assert_close(total_a[3:],total_b[3:])
    torch.testing.assert_close(total_a-total_b,.08*(raw_a['velocity_tracking']-raw_b['velocity_tracking']))


def fixture_entry(command,accepted=True):
    fields=('continuous_s','net_drift_m','max_excursion_m','dual_contact_fraction',
        'mean_abs_vx_error_mps','mean_abs_yaw_error_rad_s','height_steady_mean_m',
        'peak_tilt_rad','closure_max_m','saturation_fraction')
    row={key:0. for key in fields}
    row.update(env_id=0,outcome='completed',continuous_s=30.,dual_contact_fraction=1.)
    return dict(role='candidate',kind='full',checkpoint='/model.pt',checkpoint_sha256='same',update=125,
        identity={'scored_envs':1,'capability_commands':[[0,0],[1,0],[-1,0]]},
        result={'target':command,'per_env':[row],'capability_gate':{'accepted':accepted,
            'passed_envs':int(accepted),'per_env':[{'env_id':0,'accepted':accepted,'failed_checks':[] if accepted else ['hold_speed']}]}})


def test_selection_requires_same_checkpoint_all_commands():
    expected=fixture_entry([0,0])['identity']
    assert choose([fixture_entry([0,0])],None,expected)['accepted_candidate'] is None
    entries=[fixture_entry(command) for command in expected['capability_commands']]
    result=choose(entries,None,expected)
    assert result['accepted_candidate'] and result['full_eligible_count']==1
    entries[-1]=fixture_entry([-1,0],False)
    assert choose(entries,None,expected)['accepted_candidate'] is None
    entries[-1]['checkpoint_sha256']='other'
    assert choose(entries,None,expected)['full_eligible_count']==0


def test_specs_have_only_authorized_variable():
    import json
    module_spec=importlib.util.spec_from_file_location('prepare_ab',ROOT/'scripts/prepare_motion_cohort_width_ab.py')
    module=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    base=json.loads((ROOT/'configs/experiments/motion_capability_course_20261006/spec.json').read_text())
    before=copy.deepcopy(base)
    a,b=module.arm_specs(base)
    assert base==before
    b['experiment']=a['experiment']
    cohort=b['reward'].pop('linear_cohort_width')
    assert cohort['retained_denominator']==.04
    assert a==b
    assert a['source_sha256']=='bacd31f34a1e3917afa8e5dd9648bb5985c023dd0bc9ffd6a96ad1e1eed6fbad'
    assert a['budget']['formal_updates']==250 and a['budget']['smoke_updates']==1
    assert a['curriculum']['task_progression']['max_enabled_stage']==1


def test_current_ab_plan_is_read_only_and_exact(tmp_path):
    from native_stand.command_v6.tools.preflight import check
    from native_stand.command_v6.ledger import Ledger
    for arm in ('A','B'):
        path=ROOT/f'configs/experiments/motion_cohort_width_ab_20261006/{arm}/spec.json'
        before=path.with_name('budget.json').read_bytes()
        result=check(path,tmp_path/arm,'source_eval')
        assert result['status'] in ('PASS','READY_NEEDS_AUTH'),result['errors']
        if result['status']=='READY_NEEDS_AUTH':assert result['reason_code']=='BUDGET_EXHAUSTED'
        assert result['files_written']==result['simulation']==result['ppo']==0
        assert path.with_name('budget.json').read_bytes()==before
    local=tmp_path/'spec.json'
    local.write_bytes(path.read_bytes())
    ledger=tmp_path/'budget.json'
    book=json.loads(before)
    book['used']={name:0 for name in book['limits']}
    book['attempts']={};book['source_eval_wall_used_s']=0
    ledger.write_text(json.dumps(book))
    approval=check(local,tmp_path/'out','source_eval')
    assert approval['status']=='PASS',approval['errors']
    Ledger(ledger).reserve('exact','source_eval',tmp_path/'out',approval=approval)
    assert check(local,tmp_path/'out','source_eval',attempt_id='exact')['status']=='PASS'
    assert check(local,tmp_path/'out','source_eval',attempt_id='other')['status']=='FAIL'


def fake_chain(tmp_path,monkeypatch,source_pass=True,formal_status='COMPLETED',spawn_error=False):
    from native_stand.command_v6 import motion_width_ab as ab
    from native_stand.command_v6.completion import write,sha
    from native_stand.command_v6.ledger import Ledger
    chain=tmp_path/'run'
    chain.mkdir()
    arms={}
    for label in ('A','B'):
        folder=tmp_path/label
        folder.mkdir()
        spec=folder/'spec.json'
        write(spec,{'budget':{'source_eval_wall_s':1500,'smoke_wall_s':180,'formal_wall_s':6000,'smoke_updates':1}})
        write(folder/'budget.json',dict(authorization='AUTHORIZED',
            limits={'source_eval':1,'smoke':1,'formal':250},
            used={'source_eval':0,'smoke':0,'formal':0},attempts={},source_eval_wall_used_s=0.))
        arms[label]={'spec':str(spec),'sha256':sha(spec)}
    config=tmp_path/'ab.json'
    write(config,{'arms':arms,'wall_limit_s':14400})
    from native_stand.command_v6.tools.submission_receipt import approve
    monkeypatch.setattr(ab,'check',lambda spec,output,phase:approve({'status':'PASS','spec_sha256':sha(spec)},spec,output,phase))
    calls=[]
    def popen(command,**kwargs):
        if spawn_error:
            raise OSError('fixture spawn failure')
        spec=Path(command[command.index('--spec')+1])
        output=Path(command[command.index('--output-dir')+1])
        phase=command[command.index('--phase')+1]
        attempt=command[command.index('--attempt-id')+1]
        output.mkdir()
        used=0 if phase=='source_eval' else 1
        if used:
            Ledger(spec.with_name('budget.json')).charge(attempt,output)
        status=formal_status if phase=='formal' else 'COMPLETED'
        Ledger(spec.with_name('budget.json')).finalize(attempt,output,status,exit_code=0,wall_s=1.)
        write(output/'terminal_report.json',{'status':status,'actual_updates':used})
        write(output/'progress.json',{'source_pass':source_pass,'actor_parameters_changed':True,'actual_updates':used,
            'evaluations':[{'cases':[{'path':'evaluation_fixture.json'}]}] if phase=='smoke' else []})
        if phase=='smoke':
            (output/'source_snapshot').mkdir()
            (output/'source_snapshot/spec.json').write_bytes(spec.read_bytes())
            write(output/'manifest.json',{'source_sha256':None,'spec_sha256':sha(spec)})
            write(output/'evaluation_fixture.json',{'per_env':[{}]*8,'outcome_counts':{}})
            from native_stand.command_v6.wiring import smoke_certificate
            write(output/'wiring_certificate.json',smoke_certificate(output,json.loads(spec.read_text())))
        calls.append((spec.parent.name,phase))
        return SimpleNamespace(pid=100,wait=lambda:0)
    monkeypatch.setattr(ab.subprocess,'Popen',popen)
    reports=[]
    monkeypatch.setattr(ab,'finish',lambda chain,config,phases,status,failure,started:reports.append((status,failure)))
    reader,writer=os.pipe()
    result=ab.worker(SimpleNamespace(config=config,output_dir=chain,handshake_fd=writer))
    os.close(reader)
    return result,calls,reports,arms


def test_chain_runs_both_arms_even_if_a_has_bounded_task_failure(tmp_path,monkeypatch):
    code,calls,reports,_=fake_chain(tmp_path,monkeypatch,formal_status='STOPPED_BOUNDED')
    assert code==0 and reports[-1][0]=='COMPLETED'
    assert calls==[(arm,phase) for arm in ('A','B') for phase in ('source_eval','smoke','formal')]


def test_source_missing_old_capability_blocks_online_updates(tmp_path,monkeypatch):
    code,calls,reports,_=fake_chain(tmp_path,monkeypatch,source_pass=False)
    assert code==0 and reports[-1][0]=='STOPPED_BOUNDED'
    assert calls==[('A','source_eval')]


def test_spawn_failure_settles_only_reserved_attempt(tmp_path,monkeypatch):
    code,calls,reports,arms=fake_chain(tmp_path,monkeypatch,spawn_error=True)
    assert code==1 and reports[-1][0]=='FAILED'
    book=json.loads(Path(arms['A']['spec']).with_name('budget.json').read_text())
    assert [row['status'] for row in book['attempts'].values()]==['FAILED']
    assert book['used']['formal']==0


def test_two_retained_failures_stop_without_unlock():
    from native_stand.command_v6.domain.task_curriculum import TaskProgression
    progression=TaskProgression(dict(initial_stage=1,max_enabled_stage=1,
        consecutive_confirmations=99,standing_regression_confirmations=2,
        learned_regression_confirmations=2,blocked_reason='A/B no promotion'))
    cases=[{'command':command,'gate':{'accepted':command!=[-.5,0]}}
           for command in ([0,0],[.5,0],[-.5,0],[1,0],[-1,0])]
    assert not progression.confirm(125,cases,new_commands=([1,0],[-1,0]),episode_length_s=31)['stop']
    event=progression.confirm(250,cases,new_commands=([1,0],[-1,0]),episode_length_s=31)
    assert event['stop'] and event['next_stage']==1 and not event.get('promoted')


def test_chain_wall_budget_blocks_any_phase(tmp_path,monkeypatch):
    from native_stand.command_v6 import motion_width_ab as ab
    monkeypatch.setattr(ab.time,'monotonic',iter((0.,20000.)).__next__)
    code,calls,reports,_=fake_chain(tmp_path,monkeypatch)
    assert code==0 and calls==[] and reports[-1][0]=='STOPPED_BOUNDED'


def test_real_source_actor_critic_adam_std_and_cpu_rng_restore():
    from tensordict import TensorDict
    from native_stand.command_v6.learning import model
    from native_stand.command_v6.domain.warmstart import initialize_state,initialize_adam
    spec=json.loads((ROOT/'configs/experiments/motion_cohort_width_ab_20261006/A/spec.json').read_text())
    source=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
    obs=TensorDict({'policy':torch.zeros(2,25),'history':torch.zeros(2,125)},batch_size=[2])
    actor=model(obs,actor=True,spec=spec)
    critic=model(obs,actor=False,spec=spec)
    for name,network in (('actor',actor),('critic',critic)):
        network.load_state_dict(initialize_state(source[name],network.state_dict(),input_dim=150))
        for key,value in network.state_dict().items():
            torch.testing.assert_close(value,source[name][key],rtol=0,atol=0)
    optimizer=torch.optim.Adam(list(actor.parameters())+list(critic.parameters()),lr=3e-5)
    old_named=[(name+'.'+key,value) for name in ('actor','critic') for key,value in source[name].items()]
    new_named=[('actor.'+key,value) for key,value in actor.named_parameters()]+[('critic.'+key,value) for key,value in critic.named_parameters()]
    initialize_adam(source['optimizer'],optimizer,old_named,new_named,input_dim=150,learning_rate=3e-5)
    restored=optimizer.state_dict()
    for old_id,new_id in zip(source['optimizer']['param_groups'][0]['params'],restored['param_groups'][0]['params']):
        for key in ('step','exp_avg','exp_avg_sq'):
            torch.testing.assert_close(restored['state'][new_id][key],source['optimizer']['state'][old_id][key],rtol=0,atol=0)
    assert len(restored['state'])==17 and optimizer.param_groups[0]['lr']==3e-5
    with torch.random.fork_rng(devices=[]):
        torch.set_rng_state(source['cpu_rng'])
        first=torch.rand(8)
        torch.set_rng_state(source['cpu_rng'])
        torch.testing.assert_close(first,torch.rand(8),rtol=0,atol=0)
