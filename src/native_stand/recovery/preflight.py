"""Recovery CPU plan; no Isaac/GPU/run/ledger mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from native_stand.command_v6.config import validate


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(spec_path,output_dir):
    spec=json.loads(Path(spec_path).read_text());errors=validate(spec)
    config=spec['recovery']
    for path,sha in ((spec['asset_path'],spec['asset_sha256']),
                     (spec['asset_module_path'],spec['asset_module_sha256']),
                     (spec['colleague_config_path'],spec['colleague_config_sha256']),
                     (config['stand_checkpoint'],config['stand_sha256']),
                     (config['stand_spec'],config['stand_spec_sha256']),
                     (config['pose_library'],config['pose_library_sha256'])):
        if not Path(path).is_file() or digest(path)!=sha:errors.append(f'Identity differs: {path}')
    if Path(output_dir).exists():errors.append('Output already exists')
    library=json.loads(Path(config['pose_library']).read_text())
    if not library.get('collision_geometry') or not library.get('joint_limits_rad'):
        errors.append('Pose library lacks runtime collision geometry or joint limits')
    curriculum=config.get('curriculum',{})
    if curriculum.get('automatic_upgrade'):
        for level in curriculum['levels']:
            for split in ('train','holdout'):
                poses=[p for p in library['poses'] if p['family']==level['pose_family'] and p['split']==split and p['offline_valid']]
                if not poses: errors.append(f"Missing curriculum pose family: {level['pose_family']}/{split}")
                elif any('initial_root_height_m' not in p or 'initial_chassis_clearance_m' not in p for p in poses):
                    errors.append(f"Missing stage initialization bounds: {level['pose_family']}/{split}")
    if not errors:
        state=torch.load(config['stand_checkpoint'],map_location='cpu',weights_only=False)
        if state['actor']['mlp.0.weight'].shape!=(256,150) or state['critic']['mlp.0.weight'].shape!=(256,150):
            errors.append('STAND is not the frozen 150D network')
        if state.get('update')!=500:errors.append('STAND checkpoint update differs')
        expected={'mlp.0.weight':(256,150),'mlp.0.bias':(256,),
            'mlp.2.weight':(128,256),'mlp.2.bias':(128,),
            'mlp.4.weight':(64,128),'mlp.4.bias':(64,),
            'mlp.6.weight':(6,64),'mlp.6.bias':(6,), 'distribution.std_param':(6,)}
        if set(state['actor'])!=set(expected) or any(tuple(state['actor'][key].shape)!=shape for key,shape in expected.items()):
            errors.append('STAND state dict names/shape differ')
    book=json.loads(Path(spec_path).with_name('budget.json').read_text())
    if any(row['status']=='RUNNING' for row in book['attempts'].values()):errors.append('Budget occupied')
    prerequisites=('geometry_definition_confirmed',) if config.get('standing_task') else (
        'geometry_definition_confirmed','runtime_initialization_validated','handover_domain_validated')
    blockers=[key for key in prerequisites if not config.get(key)]
    if config.get('standing_task'):blockers.append('new_pose_continuous10s_source_baseline_pending')
    return {'cpu_valid':not errors,'errors':errors,'runtime_blockers':blockers,
        'budget_authorization':book.get('authorization','UNAUTHORIZED'),
        'stand_sha256':config['stand_sha256'],'simulation':0,'ppo':0,'files_written':0,
        'proposed_samples_smoke':spec['budget']['smoke_updates']*spec['ppo']['envs']*spec['ppo']['steps_per_env'],
        'proposed_samples_formal':spec['budget']['formal_updates']*spec['ppo']['envs']*spec['ppo']['steps_per_env']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();result=check(args.spec,args.output_dir)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['cpu_valid'] else 2)


if __name__=='__main__':main()
