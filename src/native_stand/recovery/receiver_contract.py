"""Strict first receiver-training contract; legacy policy interfaces unchanged."""
from .handoff_protocol import declaration
from .controlled_ppo import declaration as mask_declaration

def validate(spec):
    c=spec.get('receiver_training')
    if c is None:return
    keys={'version','recovery_checkpoint','recovery_sha256','recovery_spec','recovery_spec_sha256',
          'motion_checkpoint','motion_sha256','motion_spec','motion_spec_sha256','protocol',
          'prefix_s','environment_counts','critic_context','reward_source','actor_mask',
          'evaluation_families','motion_return_commands'}
    if set(c)!=keys or c['version']!='motion_receiver_training_v1':raise ValueError('Unknown receiver fields')
    if c['prefix_s']!=.5 or c['environment_counts']!={'swing_candidate_from_historical_r1':32,'motion_native_normal':32}:raise ValueError('Receiver32/32 fixed prefix differs')
    if c['protocol']!=declaration() or c['actor_mask']!=mask_declaration():raise ValueError('Receiver protocol/mask differs')
    if c['critic_context']!={'version':'legacy150_phase_metadata_v1','network_input':'native_motion150','phase_time':'storage_metadata_not_network_input','alias_risk':'explicit_partial_observability','GAE':'original_all_intervals'}:raise ValueError('Critic context must be disclosed')
    if c['reward_source']!='motion_frozen_effective_recipe' or spec['source_sha256']!=c['motion_sha256'] or spec.get('restore_source_rng') or spec.get('restore_recovery_curriculum'):raise ValueError('Receiver source or RNG differs')
    if spec.get('action_distribution') or spec['action']['leg_scale_rad']!=.5 or spec['action']['wheel_scale_rad_s']!=100:raise ValueError('Receiver must keep ordinary Motion Gaussian/actions')
    if spec['reward']!=spec['receiver_reward']:raise ValueError('Only Motion reward may be used')
    if c['evaluation_families']!=['swing_candidate_from_historical_r1','motion_native_normal'] or c['motion_return_commands']!=[[.5,0],[-.5,0]]:raise ValueError('Receiver assessment differs')
    if spec['recovery'].get('support_record_reward') or spec['recovery'].get('drawback_guidance'):raise ValueError('Swing reward cannot enter receiver training')
