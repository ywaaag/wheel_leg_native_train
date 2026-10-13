"""Offline evidence probe only, not an implemented student runtime interface."""
import torch

def history_rows(data):
    if not {'x','episode','sample'}<=set(data):raise ValueError('named current input/episode/sample required')
    x,episode,sample=data['x'],data['episode'],data['sample']
    if x.ndim!=2 or x.shape[1]!=31 or episode.shape!=(len(x),) or sample.shape!=(len(x),) or not torch.isfinite(x).all():raise ValueError('31D diagnostic dataset schema differs')
    histories=x.new_zeros(len(x),5,22);valid=torch.zeros(len(x),dtype=torch.bool,device=x.device)
    for ep in episode.unique():
        ids=torch.where(episode==ep)[0]
        for k in range(4,len(ids)):
            window=ids[k-4:k+1]
            if torch.equal(sample[window],torch.arange(int(sample[window[0]]),int(sample[window[0]])+5,device=sample.device)):
                histories[ids[k]]=x[window,:22];valid[ids[k]]=True
    return histories,valid
