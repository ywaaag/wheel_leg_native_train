"""Explicit CUDA visibility versus Kit physical renderer selection; no GPU queries."""

def resolve(physical_gpu,visible_devices=None):
    if type(physical_gpu) is not int or physical_gpu not in (0,1):raise ValueError('physical GPU must be 0 or 1')
    if visible_devices is not None and visible_devices!=str(physical_gpu):
        raise ValueError('GUI CUDA_VISIBLE_DEVICES must match the selected physical GPU')
    return {'physical_gpu':physical_gpu,'logical_cuda':'cuda:0','renderer_physical_gpu':physical_gpu,
        'environment':{'CUDA_VISIBLE_DEVICES':str(physical_gpu)},
        'app_options':{'device':'cuda:0','multi_gpu':False,
            'kit_args':f'--/renderer/activeGpu={physical_gpu} --/renderer/multiGpu/enabled=false'},
        'scope':'explicit index mapping; GPU UUID/resource/desktop rendering must be checked at runtime'}
