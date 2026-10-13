"""Online clock shares frozen declaration with offline scorer; no simulator."""
import torch
from .handoff_protocol import declaration
from .min_height import protocol,entry_mask

class HandoffClock:
    def __init__(self,n,device,configuration=None):
        from .handoff_protocol import validate_protocol
        self.p=protocol();self.cfg=validate_protocol(configuration) if configuration else declaration();self.n=n;self.device=device
        self.age=torch.zeros(n,device=device);self.entry=torch.full_like(self.age,-1);self.count=torch.zeros(n,device=device,dtype=torch.long);self.motion=torch.zeros(n,device=device,dtype=torch.bool);self.motion_age=torch.zeros_like(self.age);self.dwell=torch.zeros_like(self.count);self.sent=torch.zeros_like(self.motion)
    def reset(self,ids):
        for t in (self.age,self.count,self.motion_age,self.dwell,self.sent,self.motion):t[ids]=0
        self.entry[ids]=-1
    def observe(self,h,a,t,c,g,cl,sat,*,active,valid,safety_failed,fault):
        self.age+=active*self.cfg['dt'];self.motion_age+=active*self.motion*self.cfg['dt']
        holding=active&self.motion&(self.entry>=0)&~self.sent
        self.count+=holding
        searching=active&self.motion&(self.entry<0)&~self.sent
        eligible=entry_mask(h,a,t,c,g,valid,self.p)
        self.dwell.copy_(torch.where(searching&eligible,self.dwell+1,torch.zeros_like(self.dwell)))
        confirm=searching&(self.dwell>=round(self.cfg['entry_dwell_s']/self.cfg['dt']))&(self.motion_age<=self.cfg['settle_s']+1e-5)
        self.entry[confirm]=self.age[confirm]
        expired=searching&~confirm&(self.motion_age>=self.cfg['settle_s']-1e-5)
        complete=holding&(self.count>=round(self.cfg['hold_s']/self.cfg['dt']))
        if getattr(self,'defer_completion',False):complete=torch.zeros_like(complete)
        end=(expired|complete|safety_failed|fault)&~self.sent
        # Complete is an end-of-window event, offline scorer owns certificate.
        pulse=complete&~safety_failed&~fault;failed=end&~pulse&~fault
        self.sent|=end
        return pulse,failed,end,fault
