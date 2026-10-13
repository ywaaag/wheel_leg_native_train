"""NumPy deployment reference only. No hardware, simulator or model execution."""
import numpy as np
LEG=np.array([0,1,3,4]); WHEEL=np.array([2,5])
def vector(x,n,name):
    a=np.asarray(x,dtype=np.float32)
    if a.shape!=(n,) or not np.isfinite(a).all():raise ValueError(name+' shape/nonfinite')
    return a

def frame(angular_body,gravity_body,command,q,dq,executed_clipped_action,reference):
    angular=vector(angular_body,3,'angular');gravity=vector(gravity_body,3,'gravity')
    if not np.isclose(np.linalg.norm(gravity),1.,atol=1e-3):raise ValueError('gravity must be unit vector')
    command=vector(command,3,'command');q=vector(q,6,'q');dq=vector(dq,6,'dq');ref=vector(reference,6,'reference');prev=vector(executed_clipped_action,6,'previous clipped action')
    if np.max(np.abs(prev))>1.:raise ValueError('previous action is environment-clipped normalized action')
    return np.concatenate((angular*.25,gravity,command*np.array([2.,.25,5.],dtype=np.float32),(q[LEG]-ref[LEG])*2.,dq*.05,prev)).astype(np.float32)

class History:
    def __init__(self):self.value=None;self.last_step=None
    def update(self,current,policy_step,reset=False):
        f=vector(current,25,'frame')
        if not reset and self.last_step is not None and policy_step!=self.last_step+1:raise ValueError('duplicate/skipped policy step; explicit reset required')
        self.value=np.tile(f,(5,1)) if reset or self.value is None else np.vstack((self.value[1:],f))
        self.last_step=policy_step
        return np.concatenate((f,self.value.reshape(-1))).astype(np.float32)

def decode(deterministic_mean,reference):
    raw=vector(deterministic_mean,6,'post distribution mean');ref=vector(reference,6,'reference');clipped=np.clip(raw,-1.,1.)
    return {'raw_mean':raw,'previous_action_next':clipped,'leg_target_rad':ref[LEG]+.5*clipped[LEG],'wheel_target_rad_s':100.*clipped[WHEEL]}

def pd(q,dq,leg_target_rad,wheel_target_rad_s):
    q=vector(q,6,'q');dq=vector(dq,6,'dq');lt=vector(leg_target_rad,4,'leg target');wt=vector(wheel_target_rad_s,2,'wheel target')
    requested=np.zeros(6,dtype=np.float32);requested[LEG]=60.*(lt-q[LEG])-2.*dq[LEG];requested[WHEEL]=wt-dq[WHEEL]
    return requested,np.clip(requested,-np.array([40,40,5.5,40,40,5.5]),np.array([40,40,5.5,40,40,5.5]))
