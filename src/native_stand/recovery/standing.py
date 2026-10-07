"""Explicit standing geometry, acceptance and frozen-source retention. CPU safe."""
import math
import torch
from native_stand.recovery.domain import reward_height_gate


POSTURE_FIELDS = ('pitch_rad', 'roll_rad', 'left_leg_length_m', 'right_leg_length_m',
                  'hip_mirror_error_rad', 'active_mirror_error_rad',
                  'wheel_speed_difference_rad_s', 'vertical_velocity_mps',
                  'linear_speed_mps', 'angular_speed_rad_s')
REWARD_FIELDS = ('standing_height', 'vertical_motion', 'level_angular_motion',
                 'mirror_posture', 'leg_length_balance', 'wheel_difference')


def survival_level(protocol):
    return protocol.get('objective', 'stationary') == 'survival_level'


def standing_success_mask(diagnostics, protocol):
    mask = diagnostics[:, :2].abs().amax(-1) <= protocol['level_peak_max_rad']
    if not survival_level(protocol):
        mask &= ((diagnostics[:, 4:6].abs().amax(-1) <= protocol['mirror_error_max_rad']) &
                 ((diagnostics[:, 2]-diagnostics[:, 3]).abs() <= protocol['leg_length_difference_max_m']))
    return mask


def pose_sampling(poses, family, split, *, retained_families=(), retained_fraction=0.):
    """Metadata-only weighted rehearsal; physics states are never altered."""
    current = [i for i, p in enumerate(poses)
               if p['family'] == family and p['split'] == split and p['offline_valid']]
    old = [i for i, p in enumerate(poses) if p['family'] in retained_families and
           p['family'] != family and p['split'] == split and p['offline_valid']]
    if not current or not 0. <= retained_fraction < 1. or (retained_fraction and not old):
        raise ValueError('Invalid standing pose sampling or missing rehearsal poses')
    indices, weights = [], []
    groups = [(current, 1.-retained_fraction), (old, retained_fraction)] if retained_fraction else [(current, 1.)]
    for group, mass in groups:
        total = sum(poses[i].get('sample_weight', 1.) for i in group)
        if total <= 0:
            raise ValueError('Pose sampling weights must have positive mass')
        indices.extend(group)
        weights.extend(mass*poses[i].get('sample_weight', 1.)/total for i in group)
    return indices, weights

def longitudinal_geometry(wheels_root, gravity):
    """Wheel-center offset projected on horizontal native forward=-root Z."""
    up=-gravity/gravity.norm(dim=-1,keepdim=True).clamp_min(1e-8)
    axis=torch.zeros_like(up); axis[:,2]=-1.
    axis=axis-(axis*up).sum(-1,keepdim=True)*up
    norm=axis.norm(dim=-1,keepdim=True)
    signed=((wheels_root[:,0]-wheels_root[:,1])*axis/norm.clamp_min(1e-8)).sum(-1)
    return torch.where((norm[:,0]>1e-6)&(gravity.norm(dim=-1)>1e-8),signed,
                       torch.full_like(signed,float('nan')))


def posture(gravity, active_q, wheel_velocity, hip_positions, wheel_positions,
            linear_velocity, angular_velocity):
    """Hip-anchor to main-wheel-center distance; not a virtual-leg controller."""
    lengths = torch.linalg.vector_norm(wheel_positions - hip_positions, dim=-1)
    return torch.stack((torch.atan2(gravity[:, 2], -gravity[:, 1]),
        torch.atan2(gravity[:, 0], -gravity[:, 1]), lengths[:, 0], lengths[:, 1],
        active_q[:, 0] + active_q[:, 3], active_q[:, 1] - active_q[:, 4],
        wheel_velocity[:, 0] - wheel_velocity[:, 1], linear_velocity[:, 2],
        torch.linalg.vector_norm(linear_velocity, dim=-1),
        torch.linalg.vector_norm(angular_velocity, dim=-1)), dim=-1)


def standing_costs(height, target, diagnostics, angular_velocity, config):
    gate = reward_height_gate(height,config['gate_start_m'],config['gate_full_m'],
                              config.get('gate_mode','height'))
    deadband = config['mirror_deadband_rad']
    mirror = torch.relu(diagnostics[:, 4:6].abs()-deadband)
    return {
        'standing_height': torch.exp(-((height-target)/config['height_width_m']).square()),
        'vertical_motion': gate*(diagnostics[:, 7]/config['vertical_scale_mps']).square(),
        'level_angular_motion': gate*(angular_velocity[:, (0, 2)]/
                                    config['level_angular_scale_rad_s']).square().mean(-1),
        'mirror_posture': gate*(mirror/config['mirror_scale_rad']).square().mean(-1),
        'leg_length_balance': gate*((diagnostics[:, 2]-diagnostics[:, 3])/
                                   config['leg_length_scale_m']).square(),
        'wheel_difference': gate*(diagnostics[:, 6]/config['wheel_difference_scale_rad_s']).square(),
    }


def score_standing(series, diagnostics, *, dt, requested_s, protocol, runtime_fault,
                   initial_valid, terminated):
    """Score one continuous pre-reset episode. Missing data cannot pass."""
    checks = {}
    metrics = {}
    if not len(series) or diagnostics.shape != (len(series), len(POSTURE_FIELDS)):
        return {'accepted': False, 'failed_checks': ['missing_metrics'],
                'checks': {'missing_metrics': False}, 'metrics': {}}
    times = torch.arange(1, len(series)+1, dtype=series.dtype)*dt
    start, end = protocol['steady_window_s']
    window = (times >= start-1e-5) & (times <= min(end, requested_s)+1e-5)
    checks['continuous'] = len(series)*dt >= requested_s-1e-5 and not terminated
    checks['protocol_duration'] = requested_s >= protocol['seconds']
    checks['runtime_fault'] = not runtime_fault
    checks['initial_valid'] = bool(initial_valid)
    checks['finite'] = bool(torch.isfinite(series).all() and torch.isfinite(diagnostics).all())
    if not checks['finite']:
        return {'accepted': False, 'failed_checks': [k for k,v in checks.items() if not v],
                'checks': checks, 'metrics': {}}
    # The episode's origin is saved before physics, including reset geometry.
    origin = protocol.get('initial_xy')
    if origin is None:
        checks['initial_position_missing'] = False
        excursion = None
    else:
        distance = torch.linalg.vector_norm(series[:, 19:21]-series.new_tensor(origin), dim=-1)
        excursion = float(distance.max())
        metrics['net_drift_m'] = float(distance[-1])
    metrics['max_excursion_m'] = excursion
    if not survival_level(protocol):
        checks['excursion'] = excursion is not None and excursion <= protocol['excursion_max_m']
    metrics['height_min_m'] = float(series[:, 6].min())
    metrics['peak_tilt_rad'] = float(series[:, 15].max())
    metrics['closure_max_m'] = float(series[:, 12].max())
    metrics['saturation_fraction_policy'] = float(series[:, 17].mean())
    checks['tilt'] = metrics['peak_tilt_rad'] <= protocol['peak_tilt_max_rad']
    checks['closure'] = metrics['closure_max_m'] <= protocol['closure_max_m']
    checks['saturation'] = metrics['saturation_fraction_policy'] <= protocol['saturation_max']
    if not bool(window.any()):
        checks['steady_window_missing'] = False
    else:
        selected, p = series[window], diagnostics[window]
        low, high = protocol['height_m']
        metrics.update(height_steady_mean_m=float(selected[:, 6].mean()),
            height_in_range_fraction=float(((selected[:, 6]>=low)&(selected[:, 6]<=high)).float().mean()),
            mean_abs_vx_mps=float(selected[:, 7].abs().mean()),
            abs_mean_vx_mps=float(selected[:, 7].mean().abs()),
            mean_abs_vy_mps=float(selected[:, 8].abs().mean()),
            mean_abs_yaw_rad_s=float(selected[:, 9].abs().mean()),
            dual_contact_fraction=float((selected[:, 10:12]>2.).all(-1).float().mean()),
            mean_abs_pitch_rad=float(p[:, 0].abs().mean()),
            mean_abs_roll_rad=float(p[:, 1].abs().mean()),
            peak_abs_pitch_rad=float(diagnostics[:, 0].abs().max()),
            peak_abs_roll_rad=float(diagnostics[:, 1].abs().max()),
            mean_mirror_error_rad=float(p[:, 4:6].abs().mean()),
            mean_leg_length_difference_m=float((p[:, 2]-p[:, 3]).abs().mean()),
            mean_support_difference=float(((selected[:, 10]-selected[:, 11]).abs()/
                                           selected[:, 10:12].sum(-1).clamp_min(1.)).mean()))
        checks.update(height_mean=low <= metrics['height_steady_mean_m'] <= high,
            height_fraction=metrics['height_in_range_fraction'] >= protocol['height_fraction_min'],
            contact=metrics['dual_contact_fraction'] >= protocol['dual_contact_min'],
            pitch=metrics['mean_abs_pitch_rad'] <= protocol['level_mean_max_rad'] and
                  metrics['peak_abs_pitch_rad'] <= protocol['level_peak_max_rad'],
            roll=metrics['mean_abs_roll_rad'] <= protocol['level_mean_max_rad'] and
                 metrics['peak_abs_roll_rad'] <= protocol['level_peak_max_rad'])
        if not survival_level(protocol):
            checks.update(vx=metrics['mean_abs_vx_mps'] <= protocol['vx_abs_max_mps'],
                vy=metrics['mean_abs_vy_mps'] <= protocol['vy_abs_max_mps'],
                yaw=metrics['mean_abs_yaw_rad_s'] <= protocol['yaw_abs_max_rad_s'],
                mirror=metrics['mean_mirror_error_rad'] <= protocol['mirror_error_max_rad'],
                leg_length=metrics['mean_leg_length_difference_m'] <= protocol['leg_length_difference_max_m'],
                support_balance=metrics['mean_support_difference'] <= protocol['support_difference_max'])
    return {'accepted': all(checks.values()), 'failed_checks': [k for k,v in checks.items() if not v],
            'checks': checks, 'metrics': metrics}


class StandingRegression:
    """Only completed full evaluations can regress an already accepted model."""
    def __init__(self, *, failures_required=2, confirmed=False):
        self.failures_required=failures_required
        self.confirmed=bool(confirmed)
        self.failures=0

    def observe(self, *, accepted, full, continuous_s):
        if not full or continuous_s<10.:
            return False
        if accepted:
            self.confirmed=True
            self.failures=0
        elif self.confirmed:
            self.failures+=1
        return self.confirmed and self.failures>=self.failures_required


class StandingRetention:
    """Public Adam pre-step hook; frozen source means on actual near-standing inputs.

    The trainer captures the observations/mask before their action is executed.
    No actor/optimizer method is replaced. This is a new auxiliary loss, not reward.
    """
    def __init__(self, actor, teacher, *, coefficient, max_samples, max_grad_norm,
                 schedule=None, channels='all', gradient_diagnostics=False, save_gradient_updates=()):
        if not math.isfinite(coefficient) or coefficient <= 0 or max_samples < 1:
            raise ValueError('invalid standing retention parameters')
        self.actor, self.teacher = actor, teacher.eval()
        for p in teacher.parameters():
            p.requires_grad_(False)
        self.coefficient, self.max_samples = coefficient, max_samples
        if channels not in ('all','wheels'):
            raise ValueError('Unknown standing BC channels')
        self.schedule = schedule or {'kind':'constant'}
        retention_coefficient(coefficient,self.schedule,0)
        self.channels = channels
        self.gradient_diagnostics = gradient_diagnostics
        self.save_gradient_updates = tuple(save_gradient_updates)
        self.effective_coefficient = coefficient
        self.update = 0
        self.max_grad_norm = max_grad_norm
        self.observations = None
        self.reset()

    def reset(self):
        self.observations = None
        self.batches = []
        self.masks = []
        self.prepared = False
        self.samples = 0
        self.selected = 0
        self.eligible_count = None
        self.sample_metadata = []
        self.selected_metadata = None
        self.channel_error = None
        self.raw_sum = None
        self.calls = 0
        self.gradient_probe = None
        self.gradient_components = None
        self.gradient_payload = None

    def begin_rollout(self, update, *, phase):
        self.reset()
        self.update = update
        # Smoke is wiring only. Formal starts independently from the same source.
        self.effective_coefficient = retention_coefficient(
            self.coefficient,self.schedule,update-1 if phase=='formal' else 0)

    def capture(self, obs, eligible, metadata=None):
        self.samples += eligible.numel()
        # Fixed-shape copies avoid CUDA's dynamic boolean-index allocation per step.
        self.batches.append(obs.detach().clone())
        self.masks.append(eligible.detach().clone())
        if metadata is not None:self.sample_metadata.append(metadata.detach().clone())

    def before_step(self, optimizer, args, kwargs):
        if not self.prepared:
            if self.batches:
                batch=torch.cat(self.batches,dim=0)
                mask=torch.cat(self.masks)
                self.eligible_count=mask.sum()
                self.observations=batch[mask][:self.max_samples]
                if self.sample_metadata:
                    self.selected_metadata=torch.cat(self.sample_metadata)[mask][:self.max_samples]
                self.sample_metadata.clear()
                self.selected=len(self.observations)
                if not self.selected:self.observations=None
            self.batches.clear()
            self.masks.clear()
            self.prepared=True
        if self.observations is None:
            return
        from tensordict import TensorDict
        # Copy out of inference_mode so autograd can save its inputs.
        observations = TensorDict({k:v.detach().clone() for k,v in self.observations.items()},
                                  batch_size=self.observations.batch_size)
        current = self.actor(observations, stochastic_output=False)
        with torch.no_grad():
            target = self.teacher(observations, stochastic_output=False)
        error = current-target
        if self.selected_metadata is not None:self.channel_error=error.detach().square().mean(0)
        chosen = error if self.channels=='all' else error[:,(2,5)]
        raw = chosen.square().mean()
        if self.gradient_diagnostics and self.calls == 0:
            named=[(n,p) for n,p in self.actor.named_parameters() if p.requires_grad]
            params=[p for _,p in named]
            ppo_grad=[p.grad.detach().clone() if p.grad is not None else torch.zeros_like(p)
                      for p in params]
            bc_grad=torch.autograd.grad(raw,params,retain_graph=True,allow_unused=True)
            bc_grad=[g.detach() if g is not None else torch.zeros_like(p)
                     for p,g in zip(params,bc_grad)]
            self.gradient_probe=gradient_comparison(ppo_grad,bc_grad,
                self.effective_coefficient,self.coefficient)
            components={}
            for label,indices in (('legs',(0,1,3,4)),('wheels',(2,5))):
                # Contributions use the full six-channel denominator so they sum
                # to the original BC loss/gradient, unlike two separately averaged losses.
                loss=error[:,indices].square().sum()/error.numel()
                gs=torch.autograd.grad(loss,params,retain_graph=True,allow_unused=True)
                components[label]=[g.detach() if g is not None else torch.zeros_like(p)
                                   for p,g in zip(params,gs)]
            self.gradient_components=torch.stack([gradient_comparison(ppo_grad,components[label],
                self.effective_coefficient,self.coefficient) for label in ('legs','wheels')])
            if self.update in self.save_gradient_updates:
                self.gradient_payload={'parameter_names':[n for n,_ in named],
                'ppo_actor_gradients':[g.cpu() for g in ppo_grad],
                'bc_raw_gradients':[g.cpu() for g in bc_grad],
                'bc_component_gradients':{label:[g.cpu() for g in gs] for label,gs in components.items()},
                'observations':{k:v.detach().cpu() for k,v in observations.items()},
                'teacher_actions':target.detach().cpu(),'student_actions':current.detach().cpu(),
                'channel_mse':error.detach().square().mean(0).cpu(),
                'effective_coefficient':self.effective_coefficient,
                'scope':'First optimizer step of rollout. PPO actor composite includes entropy, clipped before BC; BC uses captured real inputs, not the PPO minibatch. No reward-specific causal decomposition.'}
        if self.effective_coefficient > 0:
            (raw*self.effective_coefficient).backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
        self.raw_sum = raw.detach() if self.raw_sum is None else self.raw_sum+raw.detach()
        self.calls += 1

    def summary(self):
        raw = float(self.raw_sum/self.calls) if self.calls else None
        probe=None
        if self.gradient_probe is not None:
            packed=torch.cat((self.gradient_probe[None],self.gradient_components)).cpu().tolist()
            values=packed[0]
            names=('ppo_actor_norm','bc_raw_norm','bc_weighted_norm','cosine',
                   'weighted_norm_ratio','reference_weighted_norm','reference_norm_ratio')
            probe={k:v if math.isfinite(v) else None for k,v in zip(names,values)}
            for label,component in zip(('legs','wheels'),packed[1:]):
                probe[label]={k:v if math.isfinite(v) else None for k,v in zip(names,component)}
            probe['scope']='First optimizer step, actor PPO+entropy after clipping versus BC on captured rollout states; null cosine when a norm is zero.'
        return {'samples':self.samples, 'retained_samples':self.selected,
                'raw':raw, 'weighted':None if raw is None else raw*self.effective_coefficient,
                'coefficient':self.effective_coefficient,'base_coefficient':self.coefficient,
                'channels':self.channels,'optimizer_steps':self.calls,'gradient_comparison':probe}


def retention_coefficient(base, schedule, update):
    if not math.isfinite(base) or base<=0 or update<0:
        raise ValueError('Invalid retention base or update')
    kind=schedule.get('kind','constant')
    if kind=='constant':return base
    end=schedule.get('zero_after_updates')
    if kind!='cosine_to_zero' or not isinstance(end,int) or end<1:
        raise ValueError('Invalid retention schedule')
    return 0. if update>=end else base*.5*(1.+math.cos(math.pi*update/end))


def gradient_comparison(ppo, bc, coefficient, reference):
    """Tensor-only directional probe; never mutates optimizer gradients."""
    p2=sum(g.double().square().sum() for g in ppo)
    b2=sum(g.double().square().sum() for g in bc)
    dot=sum(p.double().mul(b.double()).sum() for p,b in zip(ppo,bc))
    pn,bn=p2.sqrt(),b2.sqrt()
    nan=pn.new_tensor(float('nan'))
    cosine=torch.where((pn>0)&(bn>0),dot/(pn*bn).clamp_min(1e-30),nan)
    ratio=torch.where(pn>0,bn*coefficient/pn.clamp_min(1e-30),nan)
    reference_ratio=torch.where(pn>0,bn*reference/pn.clamp_min(1e-30),nan)
    return torch.stack((pn,bn,bn*coefficient,cosine,ratio,bn*reference,reference_ratio))
