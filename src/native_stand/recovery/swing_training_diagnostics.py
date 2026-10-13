"""Passive counters of existing on-policy transitions; no actor forward or RNG."""
import torch
class SwingDiagnostics:
    def __init__(self,n,device):
        self.dwell=torch.zeros(n,device=device,dtype=torch.long);self.reset()
    def reset(self):self.counts=torch.zeros(8,device=self.dwell.device);self.clip=torch.zeros(6,device=self.dwell.device);self.direction=torch.zeros(4,device=self.dwell.device);self.length=torch.zeros(2,device=self.dwell.device);self.effort=torch.zeros(6,device=self.dwell.device);self.support=torch.zeros(2,device=self.dwell.device);self.contact=torch.zeros(2,device=self.dwell.device);self.tilt=torch.zeros((),device=self.dwell.device);self.hold_peak=torch.zeros((),device=self.dwell.device);self.all_direction=torch.zeros((),device=self.dwell.device)
    def pre(self,valid,q,sample,reference):
        self.valid=valid.clone();self.counts[0]+=valid.numel();self.counts[1]+=valid.sum();self.counts[2]+=(~valid).sum()
        self.clip+=((sample.abs()>1)*valid[:,None]).sum(0)
        delta=reference[:,[0,1,3,4]]+sample[:,[0,1,3,4]].clamp(-1,1)*1.6-q[:,[0,1,3,4]]
        direction=delta*delta.new_tensor([1,1,-1,1])>0
        self.direction+=(direction*valid[:,None]).sum(0);self.all_direction+=(direction.all(1)&valid).sum()
    def post(self,state,posture,effort,done,geometry,anchors):
        v=self.valid
        vec=geometry[:,:6].reshape(-1,2,3)-anchors;gravity=geometry[:,6:9];down=gravity/gravity.norm(dim=-1,keepdim=True).clamp_min(1e-8)
        cosine=(vec*down[:,None,:]).sum(-1)/vec.norm(dim=-1).clamp_min(1e-8)
        self.support+=(cosine*v[:,None]).sum(0);self.contact+=((state[:,10:12]>2)*v[:,None]).sum(0);self.tilt+=(state[:,15]*v).sum();self.hold_peak=torch.maximum(self.hold_peak,state[:,1].max())
        short=(posture[:,2:4]<=.34).all(1)&v
        self.dwell=torch.where(short,self.dwell+1,torch.zeros_like(self.dwell));self.counts[3]+=(self.dwell==5).sum()
        self.counts[4]+=((state[:,1]>0)&v).sum();self.counts[5]+=(state[:,2].bool()&v).sum();self.counts[6]+=((state[:,1]==0)&v).sum();self.counts[7]+=done.sum()
        self.length+=(posture[:,2:4]*v[:,None]).sum(0);self.effort+=((effort.abs()>=effort.new_tensor([40,40,5.5,40,40,5.5])-1e-4)*v[:,None]).sum(0);self.dwell[done]=0
    def summary(self):
        c=self.counts.cpu().tolist();n=max(c[1],1)
        return {'total_transitions':int(c[0]),'controlled_Swing':int(c[1]),'initialization':int(c[2]),'bilateral_short_034_50ms_events':int(c[3]),'hold_samples':int(c[4]),'success_pulses':int(c[5]),'pre_entry_samples':int(c[6]),'done_count':int(c[7]),'mean_leg_lengths_m':(self.length/n).cpu().tolist(),'sample_clip_fraction':(self.clip/n).cpu().tolist(),'local_direction_fraction':(self.direction/n).cpu().tolist(),'torque_limit_fraction':(self.effort/n).cpu().tolist(),'support_cosine_mean':(self.support/n).cpu().tolist(),'wheel_contact_fraction':(self.contact/n).cpu().tolist(),'tilt_mean_rad':float(self.tilt/n),'hold_prefix_peak_s':float(self.hold_peak),'all_four_local_direction_fraction':float(self.all_direction/n),'milestone_is_not_accepted':True}
