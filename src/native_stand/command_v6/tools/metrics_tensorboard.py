"""Read-only JSONL-to-TensorBoard viewer; does not import Isaac or alter training."""
import argparse
import json
import math
from pathlib import Path
import time
import signal


def scalars(value, prefix=''):
    if isinstance(value,dict):
        for name,item in value.items():
            yield from scalars(item,f'{prefix}/{name}' if prefix else name)
    elif isinstance(value,list):
        for index,item in enumerate(value):
            yield from scalars(item,f'{prefix}/{index}')
    elif isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):
        yield prefix,float(value)


def row_scalars(row):
    """Keep legacy tags; add named reward tags only from present valid evidence."""
    yield from scalars(row)
    names=row.get('reward_fields',[])
    if not names or any(not isinstance(n,str) for n in names) or len(set(names))!=len(names):
        return
    for key,tag in (('reward_raw_mean','raw'),('reward_raw_std','raw_std'),('reward_dt_mean','dt_contribution')):
        values=row.get(key)
        if not isinstance(values,list) or len(values)!=len(names) or any(
            not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in values):
            continue
        for name,value in zip(names,values):
            yield f'reward/{tag}/{name}',float(value)
        if key=='reward_dt_mean':
            yield 'reward/continuous_per_step',float(sum(values))
            total=row.get('reward_total_per_step',sum(values))
            if isinstance(total,(int,float)) and not isinstance(total,bool) and math.isfinite(total):yield 'reward/total_per_step',float(total)
            dt=row.get('reward_dt_s')
            if isinstance(dt,(int,float)) and not isinstance(dt,bool) and math.isfinite(dt) and dt>0:
                for name,value in zip(names,values):
                    yield f'reward/weighted_density/{name}',float(value/dt)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics',type=Path,required=True)
    parser.add_argument('--log-dir',type=Path,required=True)
    parser.add_argument('--follow',action='store_true')
    parser.add_argument('--wait-for-metrics',action='store_true',
                        help='Background viewer waits for a newly submitted run to write its first update.')
    args=parser.parse_args()
    if not args.metrics.is_file() and not args.wait_for_metrics:
        parser.error('metrics file does not exist')
    def stopped(signum,frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stopped)
    try:
        while not args.metrics.is_file():
            time.sleep(5)
    except KeyboardInterrupt:
        return
    from torch.utils.tensorboard import SummaryWriter
    writer=SummaryWriter(str(args.log_dir))
    try:
        with args.metrics.open() as stream:
            while True:
                position=stream.tell()
                line=stream.readline()
                if not line or not line.endswith('\n'):
                    stream.seek(position)
                    writer.flush()
                    if not args.follow:
                        break
                    time.sleep(5)
                    continue
                try:
                    row=json.loads(line)
                except ValueError:
                    print(f'skipped invalid complete JSONL line at byte {position}',flush=True)
                    continue
                step=row.get('actual_update',row.get('update'))
                if not isinstance(step,int):
                    continue
                for name,value in row_scalars(row):
                    writer.add_scalar(name,value,step)
    except KeyboardInterrupt:
        pass
    finally:
        writer.close()


if __name__=='__main__':
    main()
