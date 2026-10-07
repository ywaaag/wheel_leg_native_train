"""CPU-only manual pose controls; no policy or implicit file/environment input."""
import math
import torch

LEG_NAMES=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')


class Controls:
    def __init__(self,limits,initial,step=.02):
        if len(limits)!=4 or len(initial)!=4 or not 0.<step<=.1:
            raise ValueError('Expected four leg limits/targets and step in (0,.1] rad')
        self.limits=limits;self.step=step;self.selected=0
        self.targets=[0.]*4;self.mode='PASSIVE';self.paused=False
        self.save_requested=False;self.reset_requested=False;self.stop=False
        for i,value in enumerate(initial):self.set(i,value)

    def set(self,index,value):
        if not math.isfinite(value):raise ValueError('Nonfinite joint target')
        self.targets[index]=min(self.limits[index][1],max(self.limits[index][0],value))

    def key(self,name):
        if name in ('KEY_1','KEY_2','KEY_3','KEY_4','1','2','3','4'):
            self.selected=int(name[-1])-1
        elif name in ('UP','DOWN'):
            self.set(self.selected,self.targets[self.selected]+self.step*(1 if name=='UP' else -1))
        elif name=='SPACE':self.mode='ADJUST' if self.mode=='PASSIVE' else 'PASSIVE'
        elif name=='P':self.paused=not self.paused
        elif name=='S':self.save_requested=True
        elif name=='R':self.reset_requested=True
        elif name=='ESCAPE':self.stop=True


def clearance(body_pos,body_quat,shapes,ground_height):
    """Ideal primitive minima from actual rigid-body poses, not PhysX contact distance."""
    # Local import is pure Torch math, deliberately no Isaac dependency.
    ids=torch.tensor([s['body_index'] for s in shapes],device=body_pos.device)
    matrices=body_pos.new_tensor([s['matrix'] for s in shapes])
    q=body_quat[ids];v=body_pos.new_tensor([0.,0.,1.]).expand(len(shapes),3)
    xyz=q[:,:3];w=q[:,3:4]
    # Inverse xyzw rotation of world up into body frame.
    t=2*torch.cross(-xyz,v,dim=-1)
    normal=v+w*t+torch.cross(-xyz,t,dim=-1)
    center=body_pos[ids,2]+(normal*matrices[:,:3,3]).sum(-1)
    n=torch.einsum('bi,bij->bj',normal,matrices[:,:3,:3])
    ext=[]
    for i,s in enumerate(shapes):
        if s['type']=='Cube':value=n[i].abs().sum()*s['size']/2
        elif s['type']=='Sphere':value=n[i].norm()*s['radius']
        elif s['type'] in ('Cylinder','Capsule'):
            axis='XYZ'.index(s['axis'])
            radial=n[i].norm() if s['type']=='Capsule' else n[i,[j for j in range(3) if j!=axis]].norm()
            value=n[i,axis].abs()*s['height']/2+radial*s['radius']
        else:raise ValueError(f"Unsupported collider {s['type']}")
        ext.append(value)
    return center-torch.stack(ext)-ground_height
