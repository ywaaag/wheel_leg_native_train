"""Recipe-specific Swing declaration; generic CPU preparer owns publication/audit."""
import argparse
import json
from pathlib import Path
from native_stand.command_v6.tools.prepare_recovery_course import prepare as prepare_course
from native_stand.command_v6.tools.experiment_preparation import digest

SWING='swing_candidate_from_historical_r1'
DRAWBACK='drawback_manual0001'


def prepare(parent,checkpoint,library,*,write=False,output=None):
    request={'purpose':'recovery_level3_swing_from_b25','level_id':'Level3','current_family':SWING,
        'retained_families':[DRAWBACK,'R0'],'family_weights':{SWING:.4,DRAWBACK:.4,'R0':.2},
        'smoke_updates':10,'formal_updates':100,'evaluation_updates':[25,50,100],
        'wall_s':{'source_eval':900,'smoke':900,'formal':7200}}
    # This wrapper intentionally retains the B25 recipe identity, not arbitrary checkpoints.
    import torch
    if torch.load(checkpoint,map_location='cpu',weights_only=False).get('update')!=25:
        raise ValueError('Swing historical recipe requires update25; use generic preparer otherwise')
    return prepare_course(parent,checkpoint,library,request,checkpoint_sha256=digest(checkpoint),write=write,output=output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent-spec',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--pose-library',type=Path,required=True);p.add_argument('--output-dir',type=Path)
    p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.parent_spec,a.checkpoint,a.pose_library,write=a.write,output=a.output_dir),indent=2))
