"""Stable CLI entry to the frozen native motion GUI runtime."""
import argparse
import os
from pathlib import Path
import sys

PROJECT=Path(__file__).resolve().parents[1]
RUNTIME=PROJECT/'isolated/motion_gpu1_20261002'
PYTHON='/home/kellen/anaconda3/envs/issaclab/bin/python'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,default=PROJECT/'runs/motion_gpu1_20261002/smoke/model_update_5.pt',help='Native150D checkpoint; use its matching spec')
    parser.add_argument('--spec',type=Path,default=RUNTIME/'configs/experiments/motion_gpu1_20261002/spec.json',help='Matching experiment spec, including source/asset identity')
    parser.add_argument('--speed',type=float,default=.1,help='Initial linear speed setting in m/s')
    parser.add_argument('--yaw-speed',type=float,default=.1,help='Initial yaw setting in rad/s')
    parser.add_argument('--max-speed',type=float,default=4.,help='Keyboard linear limit, <=4m/s')
    parser.add_argument('--max-yaw-speed',type=float,default=4.,help='Keyboard yaw limit, <=4rad/s')
    parser.add_argument('--max-wall-seconds',type=float,default=1800.,help='Bounded GUI wall time, <=7200s')
    parser.add_argument('--run',action='store_true',help='Open GUI; omitted means CPU-only identity plan')
    args=parser.parse_args()
    command=[PYTHON,'-m','native_stand.command_v6.tools.keyboard_play',
        '--checkpoint',str(args.checkpoint.resolve()),'--spec',str(args.spec.resolve()),
        '--speed',str(args.speed),'--yaw-speed',str(args.yaw_speed),
        '--max-speed',str(args.max_speed),'--max-yaw-speed',str(args.max_yaw_speed),
        '--max-wall-seconds',str(args.max_wall_seconds)]
    if args.run: command.append('--run')
    environment={**os.environ,'PYTHONPATH':str(RUNTIME/'src'),'CUDA_VISIBLE_DEVICES':'0,1'}
    os.chdir(RUNTIME)
    os.execve(PYTHON,command,environment)


if __name__=='__main__': main()
