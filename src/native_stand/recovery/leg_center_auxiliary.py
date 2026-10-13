"""Opt-in early-Swing train-only leg center regularizer; no action override."""
import torch
from .mean_auxiliary import MeanAuxiliary
from .leg_center_proposal import eligible_mask,terms


def declaration():
    return {'version':'swing_early_leg_center_v1','coefficient':.1,'band_rad':.15,
        'channels':[0,1,3,4],'family':'swing_candidate_from_historical_r1','pre_clock_window_s':[0.,.1],
        'batch':'all_eligible_current_rollout','denominator':'all_controlled_rollout_transitions',
        'application':'every_optimizer_step','gradient_order':'PPO_clipped_then_aux_then_actor_reclip',
        'apply_phases':['smoke','formal'],'failed_step':'excluded_after_step','runtime_action_override':False}


def validate(spec):
    c=spec.get('recovery',{}).get('leg_center_auxiliary')
    if c is None:return
    from native_stand.command_v6.domain.action_distribution import declaration as distribution
    if (c!=declaration() or spec.get('task')!='recovery' or spec.get('evaluation_only') or
        spec.get('initialization')!='warmstart' or spec.get('action_distribution')!=distribution() or
        spec['recovery'].get('active_family')!=c['family'] or
        any(spec['recovery'].get(k) for k in ('wheel_mean_auxiliary','exploration_initialization')) or
        spec.get('retention',{}).get('enabled') or spec['recovery'].get('standing_task',{}).get('retention',{}).get('enabled')):
        raise ValueError('Unknown/conflicting leg center auxiliary declaration')


class LegCenterAuxiliary(MeanAuxiliary):
    def capture_pre(self,observation,*,family,controlled,clock,entry):
        mask=eligible_mask(family,controlled,clock,entry,torch.zeros_like(controlled))
        self.capture(observation,mask,controlled)
        self.pending=True

    def finish_transition(self,failed):
        if not getattr(self,'pending',False):raise ValueError('Missing matching pre-action capture')
        self.masks[-1]&=~failed.bool();self.pending=False

    def finalize(self):
        if getattr(self,'pending',False):raise ValueError('Unfinished transition mask')
        super().finalize()

    def raw_terms(self,mean):
        return terms(mean,self.batch,torch.ones(len(mean),dtype=torch.bool,device=mean.device),band_rad=self.config['band_rad'])
