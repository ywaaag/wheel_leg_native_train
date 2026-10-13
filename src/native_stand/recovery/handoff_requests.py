"""Strict diagnostic request and single protocol duration authority."""
import math
from .handoff_protocol import declaration,duration,validate_protocol

def validate(spec):
    c=spec.get('motion_handoff')
    if c is None:return
    allowed={'version','protocol','motion_checkpoint','motion_sha256','motion_spec','motion_spec_sha256','max_storage_bytes','cases','normal_initialization_source'}
    modern=c.get('version')=='dual_frozen_handoff_v2'
    if modern:allowed|={'initialization_randomization'}
    if set(c)!=allowed or c['version'] not in ('dual_frozen_handoff_v1','dual_frozen_handoff_v2'):raise ValueError('Handoff schema differs')
    validate_protocol(c['protocol'])
    if not modern and (c['protocol']!=declaration() or c['max_storage_bytes']!=1073741824 or len(c['cases'])!=22):raise ValueError('Legacy bounded22 required')
    if not spec.get('evaluation_only') or isinstance(c['max_storage_bytes'],bool) or not 0<c['max_storage_bytes']<=1073741824 or not 1<=len(c['cases'])<=64:raise ValueError('PPO0 bounded cases required')
    ids=set()
    if modern:
        randomization=c['initialization_randomization']
        if set(randomization)!={'version','root_yaw_rad','distribution'} or randomization['version']!='reset_yaw_v1' or randomization['distribution']!='uniform' or not 0<=randomization['root_yaw_rad']<=.02:raise ValueError('Unknown initialization randomization')
    if spec['evaluation']['envs']!=64 or spec['evaluation']['scored_envs']!=8:raise ValueError('Explicit64 simulated/8 scored required')
    for i,row in enumerate(c['cases']):
        expected={'kind','recovery','switch_s','checkpoint','sha256','seconds','family','seed'}|({'case_id','recovery_spec','recovery_spec_sha256'} if modern else set())
        if set(row)!=expected:raise ValueError('Unknown handoff request fields')
        if modern:
            if not isinstance(row['case_id'],str) or not row['case_id'] or row['case_id'] in ids:raise ValueError('Unique case ID required')
            ids.add(row['case_id'])
        if row['kind'] not in ('normal_motion_baseline','direct_swing_motion','recovery_prefix_then_motion'):raise ValueError('Unknown condition')
        if not modern and row['switch_s'] not in (0.,.1,.25,.5,1.,2.):raise ValueError('Legacy prefix differs')
        if not math.isclose(row['seconds'],duration(row['switch_s'],spec['recovery']['initialization']['settle_max_s'],c['protocol']),abs_tol=1e-9,rel_tol=0):raise ValueError('Handoff duration mismatch')
        if not row['family'] or type(row['seed']) is not int or (not modern and row['seed']!=spec['seed']):raise ValueError('Condition initial identity differs')
    if c['cases'][0]['kind']!='normal_motion_baseline' or (not modern and c['cases'][1]['kind']!='direct_swing_motion'):raise ValueError('Baseline must run first')
