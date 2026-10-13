"""Pure Torch recovery FSM, target handover and process reward.

No file, simulator or environment access. Height/contact gates are simulation
diagnostics, not a claimed deployable fall detector.
"""
from enum import IntEnum
import torch
from fnmatch import fnmatchcase


def support_indices(body_names,allowed_patterns):
    """Explicit task contact classification; unmatched modeled bodies stay restricted."""
    allowed=[i for i,name in enumerate(body_names) if any(fnmatchcase(name,p) for p in allowed_patterns)]
    return allowed,[i for i in range(len(body_names)) if i not in allowed]
from native_stand.command_v6.domain.contract import LEG_COLUMNS, WHEEL_COLUMNS


class Mode(IntEnum):
    STAND = 0
    FALLEN_CONFIRM = 1
    RECOVERY = 2
    HANDOVER = 3
    STAND_VERIFY = 4
    RECOVERY_FAILED = 5
    RUNTIME_FAULT = 6
    INITIALIZING = 7


class RecoveryFSM:
    def __init__(self, n, device, config):
        self.config = config
        self.mode = torch.full((n,), int(Mode.RECOVERY), device=device, dtype=torch.long)
        self.age = torch.zeros(n, device=device)
        self.dwell = torch.zeros_like(self.age)
        self.verify = torch.zeros_like(self.age)
        self.success_sent = torch.zeros(n, device=device, dtype=torch.bool)

    def reset(self, ids):
        self.mode[ids] = int(Mode.RECOVERY)
        self.age[ids] = 0.
        self.dwell[ids] = 0.
        self.verify[ids] = 0.
        self.success_sent[ids] = False

    def step(self, eligible, stable, fault, task_failed, *, dt, finish_on_success=True):
        active = (self.mode >= int(Mode.RECOVERY)) & (self.mode <= int(Mode.STAND_VERIFY))
        self.age.add_(active.float() * dt)
        recovering = self.mode == int(Mode.RECOVERY)
        if self.config.get('success_mode') == 'autonomous_hold':
            self.verify.copy_(torch.where(recovering & stable, self.verify + dt, 0.))
            successful = recovering & stable & (self.verify >= self.config['verify_s'] - 1e-5)
            failed = task_failed | (active & (self.age >= self.config['timeout_s']) & ~successful)
            pulse = successful & ~self.success_sent & ~failed & ~fault
            self.success_sent |= pulse
            if finish_on_success:
                self.mode[pulse] = int(Mode.STAND)  # Terminal success; never a teacher control step.
            self.mode[failed & ~fault] = int(Mode.RECOVERY_FAILED)
            self.mode[fault] = int(Mode.RUNTIME_FAULT)
            return pulse, failed, fault
        self.dwell.copy_(torch.where(recovering,
            torch.where(eligible,self.dwell+dt,0.),self.dwell))
        enter = recovering & (self.dwell >= self.config['gate_dwell_s'] - 1e-6)
        self.mode[enter] = int(Mode.HANDOVER)
        self.dwell[enter] = 0.
        blending = (self.mode == int(Mode.HANDOVER)) & ~enter
        self.dwell.add_(blending.float() * dt)
        blend_finished=blending & (self.dwell >= self.config['blend_s'] - 1e-6)
        self.mode[blend_finished] = int(Mode.STAND_VERIFY)
        # The last blend step still executed a partial blend. Count only steps
        # whose pre-physics mode was fully STAND_VERIFY, never that boundary.
        verifying = (self.mode == int(Mode.STAND_VERIFY)) & ~blend_finished
        # Instability during verification is a failed handover, not another try.
        handover_failed = verifying & ~stable
        self.verify.add_((verifying & stable).float() * dt)
        successful = verifying & stable & (self.verify >= self.config['verify_s'] - 1e-6)
        pulse = successful & ~self.success_sent
        self.success_sent |= successful
        self.mode[successful] = int(Mode.STAND)
        timed_out = active & (self.age >= self.config['timeout_s']) & ~successful
        failed = task_failed | handover_failed | timed_out
        self.mode[failed & ~fault] = int(Mode.RECOVERY_FAILED)
        self.mode[fault] = int(Mode.RUNTIME_FAULT)
        return pulse & ~failed & ~fault, failed, fault


class ReverseRecoveryCurriculum:
    """Per-stage gate for reverse recovery; no automatic difficulty jump mid-episode."""
    def __init__(self, levels, *, windows_required=2, success_rate_min=.9, episodes_per_window=128,
                 max_enabled_stage=None, full_confirmations_required=0):
        if not levels or windows_required < 1 or not (0 < success_rate_min <= 1):
            raise ValueError('Invalid reverse recovery curriculum')
        self.levels=tuple(levels); self.windows_required=int(windows_required)
        self.success_rate_min=float(success_rate_min); self.stage=0; self._passed=0
        self.episodes_per_window=int(episodes_per_window)
        if self.episodes_per_window < 1: raise ValueError('Invalid episode window')
        self.pending=[]
        self.windows=[]
        self.max_enabled_stage=len(levels)-1 if max_enabled_stage is None else int(max_enabled_stage)
        self.full_confirmations_required=int(full_confirmations_required)
        self.full_passed=0
        if not 0<=self.max_enabled_stage<len(levels) or self.full_confirmations_required<0:
            raise ValueError('Invalid curriculum stage cap or confirmations')

    def record_episodes(self, rows):
        for stage,success,fault in rows:
            if int(stage)!=self.stage: continue
            self.pending.append((bool(success),bool(fault)))
            if len(self.pending)==self.episodes_per_window:
                stage_before=self.stage
                episode_count=len(self.pending)
                successes=sum(s for s,_ in self.pending)
                faults=sum(f for _,f in self.pending)
                self.record_window(attempted=len(self.pending),successes=successes,runtime_faults=faults)
                self.windows.append({'stage':stage_before,'episodes':episode_count,
                    'successes':successes,'runtime_faults':faults,'next_stage':self.stage})
                self.pending.clear()

    def state(self):
        return {'stage':self.stage,'level':self.current_level(),'pending_episodes':len(self.pending),
            'consecutive_passed_windows':self._passed,'completed_windows':len(self.windows),
            'consecutive_full_confirmations':self.full_passed,
            'full_confirmations_required':self.full_confirmations_required,
            'max_enabled_stage':self.max_enabled_stage}

    def checkpoint_state(self):
        """Serialize curriculum progress, including the incomplete current window."""
        return {'version':1,'stage':self.stage,'passed_windows':self._passed,
            'pending':[[bool(success),bool(fault)] for success,fault in self.pending],
            'windows':[dict(window) for window in self.windows], 'full_passed':self.full_passed}

    def restore_checkpoint_state(self, state):
        if not isinstance(state,dict) or state.get('version') != 1:
            raise ValueError('unsupported Recovery curriculum checkpoint state')
        stage=int(state['stage'])
        passed=int(state['passed_windows'])
        pending=[(bool(row[0]),bool(row[1])) for row in state.get('pending',[])]
        if not 0 <= stage <= self.max_enabled_stage:
            raise ValueError('Recovery curriculum stage out of range')
        if not 0 <= passed <= self.windows_required:
            raise ValueError('Recovery curriculum passed-window count out of range')
        if len(pending) >= self.episodes_per_window:
            raise ValueError('Recovery curriculum pending window is complete')
        full_passed=int(state.get('full_passed',0))
        if not 0<=full_passed<=self.full_confirmations_required:
            raise ValueError('Recovery curriculum full-confirmation count out of range')
        self.stage=stage
        self._passed=passed
        self.full_passed=full_passed
        self.pending=pending
        self.windows=[dict(window) for window in state.get('windows',[])]
        return self.state()

    def record_window(self, *, attempted, successes, runtime_faults):
        if attempted < self.episodes_per_window or runtime_faults:
            self._passed=0; return self.stage
        passed=(successes/attempted) >= self.success_rate_min
        self._passed=min(self.windows_required,self._passed+1) if passed else 0
        self._promote()
        return self.stage

    def _promote(self):
        if (self._passed >= self.windows_required and self.stage < self.max_enabled_stage and
                self.full_passed>=self.full_confirmations_required):
            self.stage += 1; self._passed=0
            self.full_passed=0
            self.pending.clear()

    def confirm_evaluation(self, *, stage, accepted, continuous_s):
        if stage != self.stage or continuous_s < 10.:
            return self.state()
        self.full_passed=min(self.full_confirmations_required,self.full_passed+1) if accepted else 0
        self._promote()
        return self.state()

    def current_level(self):
        return self.levels[self.stage]


def blend_targets(recovery_leg, recovery_wheel, stand_leg, stand_wheel, fraction):
    """Blend physical targets, never normalized actions with different scales."""
    f = fraction.clamp(0., 1.)[:, None]
    return recovery_leg * (1-f) + stand_leg*f, recovery_wheel*(1-f) + stand_wheel*f


def capture_terminal(state,control,causes,active,done,terminal,terminal_control,terminal_causes):
    """Copy first-episode pre-reset tensors; later episodes cannot overwrite them."""
    new=active & done.bool()
    terminal[new]=state[new]
    terminal_control[new]=control[new]
    terminal_causes[new]=causes[new]
    return new


def executed_action(leg, wheel, reference, *, leg_scale, wheel_scale):
    """Explicit target-to-action adapter for each policy's history semantics."""
    result = reference.new_zeros(reference.shape)
    result[:, LEG_COLUMNS] = (leg-reference[:, LEG_COLUMNS])/leg_scale
    result[:, WHEEL_COLUMNS] = wheel/wheel_scale
    if bool((result.abs()>1.00001).any()):
        raise ValueError('executed target outside policy action encoding')
    return result.clamp(-1.,1.)


def reward_height_gate(height, low, high, mode='height'):
    """Explicit recipe gate; standing constraints can remain active at any height."""
    if mode == 'unconditional':
        return torch.ones_like(height)
    if mode != 'height' or high <= low:
        raise ValueError('Invalid reward height gate')
    return ((height-low)/(high-low)).clamp(0.,1.)


def process_reward(height, initial_height, target_height, up, effort, action_delta,
                   joint_margin, success, task_failed, *, weights, dt,
                   settling_config=None,linear_velocity=None,angular_velocity=None,pitch=None,roll=None,
                   contact=None,wheel_velocity=None,leg_symmetry=None,support_balance=None,
                   support_region=None,slip_proxy=None,wheel_longitudinal_offset=None,
                   standing_config=None,standing_diagnostics=None):
    # Broad linear progress is informative even at chassis-down height.
    minimum_height=weights.get('height_objective_version')=='autonomous_rise_min_height_v2'
    if minimum_height:
        from native_stand.recovery.min_height import height_terms
        progress=height_terms(height)['lift']
    else:
        progress = ((height-initial_height)/(target_height-initial_height).clamp_min(.05)).clamp(-1.,1.)
    raw = {'lift':progress, 'upright':up.clamp(0.,1.),
           'effort':(effort/effort.new_tensor([40,40,5.5,40,40,5.5])).square().mean(-1),
           'action_delta':action_delta.square().mean(-1), 'joint_margin':joint_margin}
    weighted = {key:value*weights[key]*dt for key,value in raw.items()}
    if 'height_overshoot' in weights:
        raw['height_overshoot']=((height-target_height).clamp_min(0.)/weights['height_overshoot_scale_m']).square()
        weighted['height_overshoot']=raw['height_overshoot']*weights['height_overshoot']*dt
    if 'pitch_level' in weights:
        if pitch is None:raise ValueError('Pitch cost requires explicit canonical pitch')
        gate=reward_height_gate(height,weights['pitch_level_start_m'],weights['pitch_level_full_m'],
                                weights.get('pitch_level_gate_mode','height'))
        raw['pitch_level']=gate*(pitch/weights['pitch_level_scale_rad']).square()
        weighted['pitch_level']=raw['pitch_level']*weights['pitch_level']*dt
    if 'roll_level' in weights:
        if roll is None:raise ValueError('Roll cost requires explicit canonical roll')
        gate=reward_height_gate(height,weights['roll_level_start_m'],weights['roll_level_full_m'],
                                weights.get('roll_level_gate_mode','height'))
        raw['roll_level']=gate*(roll/weights['roll_level_scale_rad']).square()
        weighted['roll_level']=raw['roll_level']*weights['roll_level']*dt
    if 'support' in weights:
        if contact is None: raise ValueError('Support reward needs explicit contact')
        raw['support']=(contact>weights.get('support_force_threshold_n',2.)).all(-1).float()
        weighted['support']=raw['support']*weights['support']*dt
    if 'low_height_wheel_spin' in weights:
        if wheel_velocity is None: raise ValueError('Wheel spin reward needs explicit wheel velocity')
        gate=(1.-((height-weights.get('wheel_gate_start_m',.20)) /
                  (weights.get('wheel_gate_full_m',.32)-weights.get('wheel_gate_start_m',.20))).clamp(0.,1.))
        scale=weights.get('wheel_spin_scale_rad_s',1.)
        if scale<=0: raise ValueError('Wheel spin normalization must be positive')
        raw['low_height_wheel_spin']=gate*((wheel_velocity/scale).square().mean(-1))
        weighted['low_height_wheel_spin']=raw['low_height_wheel_spin']*weights['low_height_wheel_spin']*dt
    for name,value in (('leg_symmetry',leg_symmetry),('support_balance',support_balance),
                       ('support_region',support_region),('slip_proxy',slip_proxy),
                       ('wheel_longitudinal_offset',wheel_longitudinal_offset)):
        if name in weights:
            if value is None: raise ValueError(f'{name} reward needs explicit diagnostic')
            if name == 'wheel_longitudinal_offset':
                deadband=weights.get('wheel_longitudinal_deadband_m',0.)
                scale=weights.get('wheel_longitudinal_scale_m',.1)
                if scale<=0 or deadband<0: raise ValueError('Invalid wheel longitudinal geometry scale')
                value=torch.relu(value-deadband).square()/scale**2
                if 'wheel_longitudinal_start_m' in weights:
                    value=value*reward_height_gate(height,weights['wheel_longitudinal_start_m'],
                                                  weights['wheel_longitudinal_full_m'],'height')
            if name == 'leg_symmetry' and 'leg_symmetry_start_m' in weights:
                start=weights['leg_symmetry_start_m']
                full=weights.get('leg_symmetry_full_m', start)
                if full <= start:
                    raise ValueError('leg symmetry gate must have positive height width')
                gate=((height-start)/(full-start)).clamp(0.,1.)
                value=value*gate
            raw[name]=value
            weighted[name]=value*weights[name]*dt
    if settling_config is not None:
        if settling_config.get('kind') == 'pseudo_huber':
            costs = huber_settling_costs(height, linear_velocity, angular_velocity, settling_config)
            for name, value in costs.items():
                raw[name] = value
                weighted[name] = value * settling_config[name + '_weight'] * dt
        else:
            raw['settling_motion']=settling_motion_cost(height,linear_velocity,angular_velocity,settling_config)
            weighted['settling_motion']=raw['settling_motion']*settling_config['weight']*dt
    if standing_config is not None:
        from native_stand.recovery.standing import standing_costs
        if standing_diagnostics is None or angular_velocity is None:
            raise ValueError('Standing reward requires pre-reset posture and body angular velocity')
        for name, value in standing_costs(height,target_height,standing_diagnostics,
                                         angular_velocity,standing_config).items():
            if minimum_height and name=='standing_height':
                value=height_terms(height)['standing_height']
            raw[name]=value
            weighted[name]=value*standing_config['weights'][name]*dt
    total = sum(weighted.values()) + success.float()*weights['success_once'] + task_failed.float()*weights['failure_once']
    return total, raw, weighted


def settling_motion_cost(height,linear_velocity,angular_velocity,config):
    """Height-gated bounded full-body velocity cost; no actor truth inputs."""
    low,high=config['height_start_m'],config['height_full_m']
    if high<=low or config['linear_scale_mps']<=0 or config['angular_scale_rad_s']<=0 or config['weight']>0:
        raise ValueError('Invalid settling reward parameters')
    if linear_velocity is None or angular_velocity is None:
        raise ValueError('Settling reward needs explicit current body velocities')
    gate=((height-low)/(high-low)).clamp(0.,1.)
    motion=((linear_velocity/config['linear_scale_mps']).square().sum(-1)+
            (angular_velocity/config['angular_scale_rad_s']).square().sum(-1)).clamp(0.,1.)
    return gate*motion


def huber_settling_costs(height, linear_velocity, angular_velocity, config):
    gate = reward_height_gate(height,config['height_start_m'],config['height_full_m'],
                              config.get('gate_mode','height'))
    costs = {'settling_linear': gate * (torch.sqrt(1.+(linear_velocity/config['linear_scale_mps']).square().sum(-1))-1.),
             'settling_angular': gate * (torch.sqrt(1.+(angular_velocity/config['angular_scale_rad_s']).square().sum(-1))-1.)}
    if 'settling_yaw_weight' in config:
        # Native canonical Y is vertical; X/Z are roll/pitch axes.
        costs['settling_yaw'] = gate * (torch.sqrt(
            1.+(angular_velocity[:, 1]/config['yaw_scale_rad_s']).square())-1.)
    return costs


def autonomous_stable(height, tilt, linear_velocity, angular_velocity, contact, chassis, config):
    """Simulation truth for success, not extra deployment actor inputs."""
    result = ((height >= config['height_m'][0]) & (height <= config['height_m'][1]) &
            (tilt <= config['tilt_max_rad']) &
            (contact > config['dual_contact_min_n']).all(-1) &
            (chassis >= config['chassis_clearance_min_m']))
    if config.get('objective', 'stationary') != 'survival_level':
        result &= ((torch.linalg.vector_norm(linear_velocity, dim=-1) <= config['linear_speed_max_mps']) &
                   (torch.linalg.vector_norm(angular_velocity, dim=-1) <= config['angular_speed_max_rad_s']))
    return result


def summarize_episodes(rows):
    """Retain invalid initial states and task failures in explicit denominators."""
    groups = {}
    for row in rows:
        key = f"{row['family']}:{row['seed']}"
        group = groups.setdefault(key, {'attempted':0,'rejected':0,'success':0,
            'handover_failed':0,'runtime_fault':0,'recovery_s':[]})
        group['attempted'] += 1
        group['rejected'] += int(not row['initial_valid'])
        group['success'] += int(row['success'])
        group['handover_failed'] += int(row.get('handover_failed',False))
        group['runtime_fault'] += int(row.get('runtime_fault',False))
        if row['success']:
            group['recovery_s'].append(row['recovery_s'])
    for group in groups.values():
        valid = group['attempted']-group['rejected']
        group['rejection_rate'] = group['rejected']/group['attempted']
        group['success_rate_valid'] = group['success']/valid if valid else None
        group['success_rate_all'] = group['success']/group['attempted']
    return groups
