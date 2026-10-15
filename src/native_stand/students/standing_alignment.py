"""Versioned normal-standing recipe: physical geometry, no action override."""
import torch
RECIPE='student_standing_alignment034_v12'
REWARD='student_standing_alignment_reward_v12'
SOURCE='bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d'


def configuration():
    from .recovery_task import configuration as base,SYMMETRY_VERSION
    c=base(SYMMETRY_VERSION);c['version']=REWARD
    c['standing_alignment']={'height_weight_per_s':4.,'height_width_m':.04,
        'mirror_scale_rad':.20,'mirror_weight_per_s':-.5,
        'wheel_deadband_m':.01,'wheel_scale_m':.05,'wheel_weight_per_s':-.5,
        'velocity_scale':[.5,.02,.03],'velocity_weight_per_s':-.5,
        'event_rewards':[0.,0.,0.],'scope':'all valid student control; no posture gate or action projection'}
    return c


def huber(x):
    x=x.abs();return torch.where(x<1.,.5*x.square(),x-.5)


def apply(result,height,q,offset,velocity,yaw,controlled,fault,*,alignment_configuration=None):
    if q is None or offset is None or q.shape!=(len(height),4) or offset.shape!=height.shape:
        raise ValueError('standing alignment requires actual physical q and wheel heading offset')
    if not torch.isfinite(q).all() or not torch.isfinite(offset).all():raise ValueError('invalid standing geometry')
    eligible=(controlled&~fault);c=configuration()['standing_alignment'] if alignment_configuration is None else alignment_configuration
    mirror=torch.stack((q[:,0]+q[:,2],q[:,1]-q[:,3]),-1)
    h=torch.exp(-((height-.34)/c['height_width_m']).square())
    m=huber(mirror/c['mirror_scale_rad']).mean(-1)
    w=huber(torch.relu(offset.abs()-c['wheel_deadband_m'])/c['wheel_scale_m'])
    v=huber(torch.cat((velocity[:,:2],yaw[:,None]),-1)/height.new_tensor(c['velocity_scale'])).sum(-1)
    # Replace inherited height, velocity and mirror; retain support/effort/target/angular terms.
    old=result['continuous_dt'][:,0]+result['motion_mirror_dt'].sum(-1)+result['events'].sum(-1)
    raw=torch.stack((h,m,w,v),-1)*eligible[:,None]
    density=raw*height.new_tensor([4.,-.5,-.5,-.5]);dt=density*.01
    result['total']=(result['total']-old+dt.sum(-1))*eligible
    result['events']=torch.zeros_like(result['events'])
    result['alignment_raw']=raw;result['alignment_density']=density;result['alignment_dt']=dt
    result['raw'][:,0]=raw[:,0];result['weighted_density'][:,0]=density[:,0];result['continuous_dt'][:,0]=dt[:,0]
    result['motion_mirror_raw'][:,0]=raw[:,3];result['motion_mirror_raw'][:,1]=raw[:,1]
    result['motion_mirror_weighted_density'][:,0]=density[:,3];result['motion_mirror_weighted_density'][:,1]=density[:,1]
    result['motion_mirror_dt'][:,0]=dt[:,3];result['motion_mirror_dt'][:,1]=dt[:,1]
    return result
