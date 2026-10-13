"""Policy control ownership and deployment-observable interface declarations."""
import torch

INITIALIZATION=0
RECOVERY=1
RECEIVER=2

def ownership(initializing,checked,prefix_count,switch_steps):
    if initializing.shape!=checked.shape or prefix_count.shape!=checked.shape:
        raise ValueError('Ownership shapes differ')
    receiving=(~initializing.bool())&checked.bool()&(prefix_count>=switch_steps)
    controller=torch.where(initializing,0,torch.where(receiving,2,1))
    return controller,receiving

def yaw_randomize(q,uniform,amplitude):
    """World-Z quaternion multiplication, preserving passive q/dq and height."""
    if q.shape[-1]!=4 or uniform.shape!=q.shape[:-1]:raise ValueError('Quaternion sample shape differs')
    a=(uniform*2-1)*amplitude/2;c=torch.cos(a);s=torch.sin(a)
    # Installed IsaacLab3 math/articulation API uses xyzw (verified locally).
    x,y,z,w=q.unbind(-1)
    return torch.stack((c*x-s*y,c*y+s*x,c*z+s*w,c*w-s*z),-1)

def phase_metadata(controller,initial_age,prefix_count,motion_age,entry,hold_count):
    phase=torch.where((controller==2)&(entry>=0),3,controller)
    elapsed=torch.where(phase==0,initial_age,torch.where(phase==1,prefix_count*.01,
                      torch.where(phase==2,motion_age,hold_count*.01)))
    return phase,elapsed

def interface_contract():
    return {'version':'multi_skill_proprioception_v1_draft','status':'PLANNED',
        'observation_version':'proprioception_history_050_v1_draft',
        'command_version':'skill_command_v1_draft','action_version':'physical_joint_target_v1_draft',
        'deployment_sensors':['IMU','joint_position','joint_velocity'],
        'actor_history_s':.5,'resampling':'50prior frames at t-0.50..t-0.01 plus current frame; timestamped100Hz',
        'commands':{'Motion':['vx_mps','yaw_rad_s','height_m'],
                    'Recovery':['recover_swing'],'Jump':['amplitude'],'Traverse':['contact_obstacle']},
        'actions':'left-first physical joint position(rad)/wheel speed(rad/s)',
        'migration':'new interface ID/new models; legacy150D models retain native25+125 history',
        'runtime_required':False}
