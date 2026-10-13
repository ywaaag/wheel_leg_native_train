import argparse,json
from pathlib import Path
from native_stand.students.export import export
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--dataset',required=True);p.add_argument('--output',required=True);a=p.parse_args()
r=export(a.checkpoint,a.dataset,a.output,Path(__file__).resolve().parents[1]);print(json.dumps(r,indent=2))
