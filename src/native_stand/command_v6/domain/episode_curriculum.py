"""Explicit episode deadlines and non-overlapping completed-episode windows."""
import math
import torch

FIELDS=('level','timeout','task_failure','duration_s','vx_abs','yaw_abs','excursion_m',
        'tilt_rad','contact_fraction','height_m','saturation_fraction','closure_m')


class EpisodeWindows:
    def __init__(self, config):
        self.config=config
        self.level=0
        self.pending={index:[] for index in range(len(config['lengths_s']))}
        self.streak={index:0 for index in self.pending}
        self.window_count={index:0 for index in self.pending}

    def consume(self, rows):
        events=[]
        for row in rows:
            level=int(row[0])
            self.pending[level].append(row)
            size=self.config['episodes_per_window']
            if len(self.pending[level])<size:
                continue
            window=self.pending[level][:size]
            del self.pending[level][:size]
            thresholds=self.config['gates']
            def episode_pass(entry):
                values=dict(zip(FIELDS,entry))
                return (all(math.isfinite(value) for value in entry) and
                    values['vx_abs']<=thresholds['vx_abs_max_mps'] and
                    values['yaw_abs']<=thresholds['yaw_abs_max_rad_s'] and
                    values['excursion_m']<=thresholds['excursion_max_m'] and
                    values['tilt_rad']<=thresholds['tilt_max_rad'] and
                    values['contact_fraction']>=thresholds['dual_contact_min'] and
                    thresholds['height_m'][0]<=values['height_m']<=thresholds['height_m'][1] and
                    values['saturation_fraction']<=thresholds['saturation_max'] and
                    values['closure_m']<=thresholds['closure_max_m'])
            normal=sum(entry[1]==1 and entry[2]==0 for entry in window)/size
            pass_fraction=sum(episode_pass(entry) for entry in window)/size
            passed=normal>=thresholds['normal_timeout_min'] and pass_fraction>=thresholds['metric_episode_pass_min']
            self.streak[level]=self.streak[level]+1 if passed else 0
            self.window_count[level]+=1
            event={'level':level,'length_s':self.config['lengths_s'][level],
                'window':self.window_count[level],'episodes':size,'normal_timeout_fraction':normal,
                'metric_episode_pass_fraction':pass_fraction,'passed':passed,'streak':self.streak[level],
                'means':{field:sum(entry[index] for entry in window)/size for index,field in enumerate(FIELDS)},
                'next_level':self.level}
            if (level==self.level and self.streak[level]>=self.config['consecutive_windows'] and
                    self.level<len(self.config['lengths_s'])-1):
                self.level+=1
                event['next_level']=self.level
                event['promoted']=True
            events.append(event)
        return events

    def state(self):
        return {'level':self.level,'length_s':self.config['lengths_s'][self.level],
            'pending_episodes':{str(key):len(value) for key,value in self.pending.items()},
            'consecutive_pass_windows':self.streak,'windows':self.window_count}


class EpisodeTracker:
    def __init__(self, num_envs, device, config, dt):
        self.config=config
        self.dt=dt
        self.assigned_level=torch.zeros(num_envs,dtype=torch.long,device=device)
        self.deadline_steps=torch.full((num_envs,),round(config['lengths_s'][0]/dt),device=device,dtype=torch.long)
        self.origin=torch.zeros(num_envs,2,device=device)
        self.sum=torch.zeros(num_envs,5,device=device,dtype=torch.float64)
        self.peaks=torch.zeros(num_envs,3,device=device)
        self.count=torch.zeros(num_envs,device=device,dtype=torch.long)
        self.records=[]
        self.masks=[]

    def reset(self, ids, root_xy, level):
        self.assigned_level[ids]=level
        self.deadline_steps[ids]=round(self.config['lengths_s'][level]/self.dt)
        self.origin[ids]=root_xy[ids]
        self.sum[ids]=0
        self.peaks[ids]=0
        self.count[ids]=0

    def observe(self, root_xy, height, vx, yaw, contact, tilt, closure, saturated, terminated, timeout):
        self.sum+=torch.stack((vx.abs(),yaw.abs(),contact.all(-1).float(),height,saturated.float()),-1).double()
        self.peaks.copy_(torch.maximum(self.peaks,torch.stack((torch.linalg.vector_norm(root_xy-self.origin,dim=-1),tilt,closure),-1)))
        self.count+=1
        mean=self.sum/self.count.clamp_min(1)[:,None]
        row=torch.stack((self.assigned_level.double(),timeout.double(),terminated.double(),
            self.count.double()*self.dt,mean[:,0],mean[:,1],self.peaks[:,0].double(),
            self.peaks[:,1].double(),mean[:,2],mean[:,3],mean[:,4],self.peaks[:,2].double()),-1)
        self.records.append(row)
        self.masks.append(terminated|timeout)

    def collect(self):
        if not self.records:
            return []
        packed=torch.cat((torch.stack(self.records),torch.stack(self.masks).unsqueeze(-1).double()),-1).cpu()
        self.records.clear()
        self.masks.clear()
        return packed[packed[:,:,-1].bool(),:-1].tolist()
