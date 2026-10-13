"""Pure deployment/trace encoder. No simulator, files or teacher identity."""
import torch
VERSION='multiskill_student_v1'
FRAME=22
FRAMES=51
ACTOR_DIM=1182
CRITIC_DIM=1191
LEGS=(0,1,3,4)
WHEELS=(2,5)
ORDER=('left_hip','left_active_link','left_wheel','right_hip','right_active_link','right_wheel')
SKILLS=('Motion','Recovery','Jump','Traverse')

def contract():
    return dict(version=VERSION,frame_dim=22,frames=51,frame_valid_dim=1,task_dim=9,
        actor_dim=1182,critic_dim=1191,dt=.01,history_order='oldest-to-newest',
        history_fill='zeros,valid=false; real initialization frames valid=true',
        frame_fields=['angular_body_rad_s:3*.25','gravity_body_unit:3','q_leg_minus_reference_rad:4/1.5',
                      'dq_active_rad_s:6*.05','previous_executed_leg_delta_rad:4/1.5','previous_executed_wheel_rad_s:2/100'],
        task_fields=['Motion','Recovery','Jump','Traverse','vx/4','yaw_rate/4','height/.5','jump_clearance_m','jump_distance_m'],
        body_axes='USD root-link body X/Y/Z; IMU angular and gravity in same axes',
        native_linear_axes='[-bodyZ,-bodyX,+bodyY],m/s,measured before action',
        critic_privileged=['height_m','vx_native_mps','vy_native_mps','vz_native_mps',
                           'left_contact_resultant_n/100','right_contact_resultant_n/100',
                           'controlled_s/2.5','entry_confirm_s/.2','hold_s/10'],
        action_order=list(ORDER),leg_scale_rad=1.5,wheel_scale_rad_s=100.,reference=[0.]*6,
        physics_pd_policy_s=[.001,.005,.01],effort_nm=[40.,40.,5.5,40.,40.,5.5])

def frame(angular_body,gravity_body,q,dq,previous_legs,previous_wheels,reference):
    if q.shape[-1]!=6 or dq.shape!=q.shape or reference.shape!=q.shape:raise ValueError('active left-first q/dq/reference required')
    out=torch.cat((angular_body*.25,gravity_body,(q[...,LEGS]-reference[...,LEGS])/1.5,
        dq*.05,(previous_legs-reference[...,LEGS])/1.5,previous_wheels/100.),-1)
    if out.shape[-1]!=FRAME or not torch.isfinite(out).all():raise ValueError('invalid student frame')
    if not torch.allclose(torch.linalg.vector_norm(gravity_body,dim=-1),torch.ones_like(gravity_body[...,0]),atol=2e-4):raise ValueError('gravity must be unit body vector')
    return out

def task(skill,command):
    if skill not in SKILLS or command.shape[-1]!=5:raise ValueError('explicit skill and five commands required')
    one=torch.zeros((*command.shape[:-1],4),device=command.device,dtype=command.dtype);one[...,SKILLS.index(skill)]=1
    scale=command.new_tensor([4.,4.,.5,1.,1.]);return torch.cat((one,command/scale),-1)

def actor_input(frames,valid,commands):
    if frames.shape[-2:]!=(51,22) or valid.shape!=frames.shape[:-1] or commands.shape!=(*frames.shape[:-2],9):raise ValueError('1182D history/task layout differs')
    return torch.cat((torch.cat((frames,valid.to(frames.dtype)[...,None]),-1).flatten(-2),commands),-1)

class History:
    """One append per policy time; only explicit episode reset clears a subset."""
    def __init__(self,n,device='cpu'):
        self.frames=torch.zeros(n,51,22,device=device);self.valid=torch.zeros(n,51,device=device,dtype=torch.bool)
        self.times=torch.full((n,51),float('nan'),device=device,dtype=torch.float64)
    def reset(self,ids):
        self.frames[ids]=0;self.valid[ids]=False;self.times[ids]=float('nan')
    def append(self,current,time_s,update=None):
        t=torch.as_tensor(time_s,device=self.frames.device,dtype=torch.float64).expand(len(current))
        existing=self.valid[:,-1]
        update=torch.ones_like(existing) if update is None else update.bool()
        if not torch.isfinite(t[update]).all():raise ValueError("nonfinite policy time")
        if (update&existing&((t-self.times[:,-1]-.01).abs()>2e-6)).any():raise ValueError('duplicate/missing/nonmonotonic policy time')
        self.frames[update]=torch.cat((self.frames[update,1:],current[update,None]),1)
        self.valid[update]=torch.cat((self.valid[update,1:],torch.ones_like(existing[update])[:,None]),1)
        self.times[update]=torch.cat((self.times[update,1:],t[update,None]),1)
    def encode(self,commands):return actor_input(self.frames,self.valid,commands)

def labels(legs,wheels,reference):
    result=reference.new_zeros((*legs.shape[:-1],6));result[...,LEGS]=(legs-reference[...,LEGS])/1.5;result[...,WHEELS]=wheels/100.
    if not torch.isfinite(result).all() or (result.abs()>1+1e-6).any():raise ValueError('teacher target not representable in student envelope')
    return result

def targets(raw,reference,limits=None):
    if raw.shape[-1]!=6:raise ValueError('6D action required')
    clipped=raw.clamp(-1,1);requested=reference[...,LEGS]+clipped[...,LEGS]*1.5
    legs=requested if limits is None else requested.clamp(limits[...,LEGS,0],limits[...,LEGS,1])
    return dict(raw_action=raw,clipped_action=clipped,leg_requested=requested,leg_executed=legs,
                wheel_executed=clipped[...,WHEELS]*100.,joint_limit_clipped=legs!=requested)

def critic_input(actor,height,velocity_native,contacts,controlled_s,entry_s,hold_s):
    extra=torch.cat((height[...,None],velocity_native,contacts/100.,controlled_s[...,None]/2.5,
                     entry_s[...,None]/.2,hold_s[...,None]/10.),-1)
    if actor.shape[-1]!=1182 or extra.shape[-1]!=9:raise ValueError('1191D critic layout differs')
    return torch.cat((actor,extra),-1)
