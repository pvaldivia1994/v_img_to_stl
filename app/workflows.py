import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SINGLE_MODEL = 'hunyuan3d-dit-v2.safetensors'
MULTIVIEW_MODEL = 'hunyuan3d-dit-v2-mv.safetensors'
HUNYUAN21_MODEL = 'hunyuan_3d_v2.1.safetensors'

def build_workflow(images, seed, prefix, model_family='hunyuan2'):
    if 'front' not in images:
        raise ValueError('A front view is required.')
    unknown = set(images) - {'front', 'back', 'left', 'right'}
    if unknown:
        raise ValueError('Unknown view names: ' + ', '.join(sorted(unknown)))
    if model_family not in ('hunyuan2', 'hunyuan21'):
        raise ValueError('Unknown model family.')
    if model_family == 'hunyuan21' and len(images) != 1:
        raise ValueError('Hunyuan3D 2.1 accepts a single front image in this workflow.')
    prompt = copy.deepcopy(json.loads((ROOT / 'workflows/hunyuan3d-2-api.json').read_text()))
    prompt['56']['inputs']['image'] = images['front']
    prompt['3']['inputs']['seed'] = seed
    prompt['67']['inputs']['filename_prefix'] = prefix
    if model_family == 'hunyuan21':
        prompt['54']['inputs']['ckpt_name'] = HUNYUAN21_MODEL
        prompt['66']['inputs']['resolution'] = 4096
        prompt['70']['inputs']['sampling'] = 'flow'
    if len(images) > 1:
        prompt['54']['inputs']['ckpt_name'] = MULTIVIEW_MODEL
        conditioning = {'front': ['51', 0]}
        for index, view in enumerate(('left', 'back', 'right')):
            if view not in images:
                continue
            loader, encoder = str(100 + index), str(110 + index)
            prompt[loader] = {'class_type': 'LoadImage', 'inputs': {'image': images[view]}}
            prompt[encoder] = {'class_type': 'CLIPVisionEncode', 'inputs': {'clip_vision': ['54', 1], 'image': [loader, 0], 'crop': 'none'}}
            conditioning[view] = [encoder, 0]
        prompt['80'] = {'class_type': 'Hunyuan3Dv2ConditioningMultiView', 'inputs': conditioning}
    return prompt
