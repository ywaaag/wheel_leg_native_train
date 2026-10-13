import argparse,json
from native_stand.students.data import build
p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--output',required=True);p.add_argument('--interface-version',choices=['multiskill_student_v1','multiskill_mcu_v2'],default='multiskill_student_v1');a=p.parse_args()
r=build(a.root,a.output,version=a.interface_version);print(json.dumps({k:r[k] for k in ('RecoveryStudent','MotionZeroStudent' if a.interface_version=='multiskill_mcu_v2' else 'MotionStudent')},indent=2))
