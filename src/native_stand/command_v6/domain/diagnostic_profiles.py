"""Explicit storage scope; sampling rate is policy-rate, never physics-rate."""
PROFILES = {
    'paired_state': {'full_trace':True,'diagnostics':True,
        'fields':['summary','terminal_pre_reset','state','control','actor_input','geometry'],
        'scope':'explicit bounded Motion actor input plus pre/post root/wheel state at policy rate'},
    'summary': {'full_trace':False,'diagnostics':False,'fields':['summary','terminal_pre_reset'],
                'scope':'aggregated first episode'},
    'failure_tail': {'full_trace':False,'diagnostics':True,
        'fields':['summary','terminal_pre_reset','state','posture','control','geometry'],
        'scope':'last up to one second of failed first episode; no successful full timeline'},
    'full_transition': {'full_trace':True,'diagnostics':True,
        'fields':['summary','terminal_pre_reset','state','posture','control','geometry'],
        'scope':'complete valid first episode, pre-reset, up to requested duration'},
}


def resolve(name, *, required=(), task='recovery', dt=.01):
    if name is None:
        if required:raise ValueError('required fields need an explicit diagnostic profile')
        return None  # No request: preserve historical flag behavior.
    if name not in PROFILES:raise ValueError('unknown diagnostic profile')
    if not isinstance(required,(list,tuple)) or any(not isinstance(v,str) for v in required):
        raise ValueError('required diagnostic fields must be strings')
    record={**PROFILES[name],'fields':list(PROFILES[name]['fields']),'profile':name,'sample_rate_hz':1/dt}
    if name=='paired_state' and task=='recovery':raise ValueError('paired_state is Motion only')
    if task!='recovery' and name!='paired_state':record['fields']=[v for v in record['fields'] if v not in ('posture','geometry')]
    missing=set(required)-set(record['fields'])
    if missing:raise ValueError('diagnostic profile lacks required fields: '+','.join(sorted(missing)))
    record['required_fields']=list(required)
    record['limitation']='policy samples; latest held PD torque, not every physics/PD substep'
    return record


def storage_plan(spec,*,update=None,full=False,final=False,request=None,legacy_full_trace=False,legacy_diagnostics=False):
    """One explicit storage decision; omitted profiles preserve previous collection behavior."""
    request=request or {};evaluation=spec.get('evaluation',{})
    name=request.get('diagnostic_profile',evaluation.get('diagnostic_profile'))
    required=request.get('required_diagnostic_fields',evaluation.get('required_diagnostic_fields',[]))
    selected=full and update in evaluation.get('full_trace_updates',[])
    minimum=spec.get('recovery',{}).get('rising_task',{}).get('version')=='autonomous_rise_min_height_v2'
    origin='explicit request' if request.get('diagnostic_profile') else 'evaluation profile' if name else 'legacy adapter'
    if name is None and minimum and full:name='full_transition';origin='minimum-height required diagnostics'
    record=resolve(name,required=required,task=spec.get('task','motion'),dt=spec['control']['policy_dt_s'])
    if record is None:
        record={'profile':None,'full_trace':bool(legacy_full_trace or selected),'diagnostics':bool(legacy_diagnostics),
            'fields':None,'required_fields':[],'sample_rate_hz':1/spec['control']['policy_dt_s'],
            'scope':'legacy collection flags; field availability checked from raw evidence'}
    if selected and not record['full_trace']:raise ValueError('full_trace_updates conflicts with explicit profile')
    return {**record,'origin':origin,'update':update,'final':final,
        'runtime_kwargs':{'full_trace':record['full_trace'],'diagnostics':record['diagnostics'],
                         **({'paired_state':True} if record['profile']=='paired_state' else {}),
                         **({'diagnostic_profile':record['profile']} if spec.get('task')=='recovery' and record['profile'] else {})}}
