"""Versioned raw policy-trace layout shared by offline consumers."""
VERSION='recovery_policy_trace_v1'
STATE={'recovery_clock_s':0,'height_m':6,'vx_mps':7,'vy_mps':8,'yaw_rad_s':9,
       'left_contact_n':10,'right_contact_n':11,'closure_m':12,'clearance_m':13,'tilt_rad':15,'saturated':17}
WIDTHS={'state':39,'posture':10,'control':54,'geometry':13}
CONTROL={'raw_action':slice(12,18),'clipped_action':slice(18,24),
         'requested_torque':slice(32,38),'physical_clipped_torque':slice(38,44),'applied_torque':slice(44,50)}


def validate_rows(rows,kind):
    if kind not in WIDTHS:raise ValueError('unknown trace kind')
    if any(len(row)!=WIDTHS[kind] for row in rows):raise ValueError('trace layout differs: '+kind)
    return rows

# Additional named fields authored by RecoveryEnv.recovery_snapshot; never infer
# a different trace version from matching widths alone.
STATE.update(hold_clock_s=1,success=2,task_failed=3,runtime_fault=4,pose_index=5,
             excursion_m=16,mode=18,initial_valid=29,initial_rejected=30,
             episode_id=31,previous_mode=32)
POSTURE={'pitch_rad':0,'roll_rad':1}
CONTROL.update(joint_q=slice(0,6),joint_dq=slice(6,12),
               leg_target_before_limit=slice(24,28),leg_target_after_limit=slice(28,32))
PHASE_CODES={'initializing':7}
