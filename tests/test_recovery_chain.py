from native_stand.recovery.chain import gate_ok,baseline_ok


def test_probes_require_true_gate_and_complete_exit():
    r0={'standing_gate':{'accepted':True},'per_env':[{}]*8}
    assert gate_ok('r0',r0,{'status':'COMPLETED'},0)
    assert not gate_ok('r0',r0,{'status':'FAILED'},0)
    assert not gate_ok('r0',r0,{'status':'COMPLETED'},124)
    assert not gate_ok('r0',{'standing_gate':{'accepted':False},'per_env':[{}]*8},{'status':'COMPLETED'},0)


def test_initialization_requires_all64_not_only_scored8():
    assert not gate_ok('initial',{'passed':True,'validated_envs':8},{'status':'COMPLETED'},0)
    assert gate_ok('initial',{'passed':True,'validated_envs':64},{'status':'COMPLETED'},0)
    assert not gate_ok('initial',{'passed':False,'validated_envs':64},{'status':'COMPLETED'},0)


def test_autonomous_baseline_task_failure_allows_learning_but_fault_does_not():
    import copy
    result={'checkpoint_sha256':'fixed','per_env':[{'initial_valid':True,
        'outcome':'task_failure','runtime_fault':False} for _ in range(8)],
        'success_protocol':{'mode':'autonomous_hold','required_stable_s':2.,'teacher_control':False},
        'initialization':[{'rejected':0}]}
    terminal={'status':'COMPLETED','exit_code':0}
    assert baseline_ok(result,terminal,'fixed')
    assert not baseline_ok(result,terminal,'other')
    bad=copy.deepcopy(result);bad['per_env'][0]['runtime_fault']=True
    assert not baseline_ok(bad,terminal,'fixed')
    bad=copy.deepcopy(result);bad['initialization'][0]['rejected']=1
    assert not baseline_ok(bad,terminal,'fixed')
    assert not baseline_ok(result,{'status':'STOPPED_BOUNDED','exit_code':0},'fixed')
