"""Explain execution/compatibility fields without changing Recovery behavior."""
from .task_protocol import resolve


def disclose(spec):
    config=spec['recovery'];task=resolve(config);rising=config.get('rising_task')
    from .sampling import effective,allocation_plan,LEGACY_KEYS
    sampling=effective(config)
    sampling['allocation_plan']=allocation_plan(config,spec['ppo']['envs']) if 'ppo' in spec else {'status':'MISSING_EVIDENCE:ppo.envs'}
    rows=[]
    def add(field,status,consumer,reason):rows.append({'field':field,'status':status,'consumer':consumer,'reason':reason})
    add('recovery.rising_task','ACTIVE' if rising else 'NOT_CONFIGURED','recovery.task_protocol/min_height/rising','owns deadline and hold scoring')
    add('recovery.sampling','ACTIVE' if 'sampling' in config else 'LEGACY_READ_ONLY_ADAPTER','recovery.sampling/sample_poses','reset family weights; not scoring')
    add('recovery.assessment','ACTIVE' if 'assessment' in config else 'LEGACY_READ_ONLY_ADAPTER','recovery.sampling/retained_families','evaluation and old-skill protection scope; not reset weights')
    add('control.height_command_m','ACTIVE_COMPATIBILITY','CommandEnv observation/reset','actor command slot; not minimum-height certificate upper bound')
    add('recovery.standing_task.protocol','ADAPTED' if rising else 'ACTIVE','rise_protocol/standing scorer','minimum-height v2 replaces old narrow band with its own protocol' if rising else 'standing thresholds')
    add('recovery.fsm','ACTIVE_COMPATIBILITY','RecoveryEnv/FSM','initialization and legacy transition settings; rising success/deadline owned by task, not standalone handover certificate')
    add('reward','ACTIVE','recovery.domain/process_reward','weights consumed by task reward; gate thresholds remain separately owned')
    fields=[]
    minimum=bool(rising and rising.get('version')=='autonomous_rise_min_height_v2')
    def leaves(value,path):
        if isinstance(value,dict):
            for key,item in value.items():leaves(item,path+'.'+key)
        else:
            status='DECLARED_REQUIRES_CONSUMER_REVIEW';consumer='schema/task assembly';effective=value
            if path.startswith('recovery.standing_task.protocol.') and minimum:
                from .min_height import protocol
                key=path.rsplit('.',1)[-1];resolved=protocol()
                status='TASK_PROTOCOL_OVERRIDE';consumer='min_height.protocol';effective=resolved.get(key)
            elif path.startswith('recovery.fsm.') and minimum:
                status='LEGACY_COMPATIBILITY_NOT_TASK_CERTIFICATE';consumer='runtime FSM construction; RiseHold owns task ending'
            elif path.startswith('recovery.rising_task.') and path.rsplit('.',1)[-1] in LEGACY_KEYS:
                status='LEGACY_SAMPLING_ADAPTER';consumer='recovery.sampling only; excluded from scoring protocol'
            elif path.startswith('recovery.sampling.'):
                status='ACTIVE_SAMPLING';consumer='recovery.sampling/sample_poses'
            elif path.startswith('recovery.assessment.'):
                status='ACTIVE_ASSESSMENT';consumer='recovery.recipe/retained_families'
            elif path.startswith('recovery.rising_task.'):
                status='ACTIVE_TASK_DECLARATION';consumer='task_protocol/validate_rise/runtime'
            elif path.startswith(('recovery.initialization.','recovery.contacts.')) or path in ('recovery.active_family','recovery.pose_library','recovery.pose_library_sha256'):
                status='ACTIVE_INITIALIZATION';consumer='RecoveryEnv reset/readback'
            elif path.startswith('reward.'):
                status='REWARD_DECLARATION';consumer='process_reward validation/conditional branches; actual activation needs raw metrics'
            fields.append({'field':path,'requested':value,'effective':effective,'status':status,'consumer':consumer})
    leaves(config,'recovery');leaves(spec.get('reward',{}),'reward')
    fields.append({'field':'control.height_command_m','requested':spec['control']['height_command_m'],
        'effective':spec['control']['height_command_m'],'status':'ACTIVE_COMPATIBILITY',
        'consumer':'actor command slot/reset; not certificate upper bound'})
    return {'sampling_and_assessment':sampling,'task':task,'field_effectiveness':rows,'complete_field_inventory':fields,'requested_recovery':config,
        'scope':'all declared Recovery/reward leaves enumerated; unreviewed consumers explicitly identified, not claimed active',
        'changes_to_recipe':False}
