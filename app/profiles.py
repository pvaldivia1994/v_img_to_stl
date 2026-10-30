"""Profiles keep UI choices simple and preserve the exact workflow per project."""
from app.workflows import HUNYUAN21_MODEL
PROFILES = {
    'standard': {'steps': 20, 'cfg': 8.0, 'octree_resolution': 256, 'num_chunks': 8000},
    'detail': {'steps': 40, 'cfg': 6.0, 'octree_resolution': 384, 'num_chunks': 8000},
    'maximum': {'steps': 50, 'cfg': 7.5, 'octree_resolution': 512, 'num_chunks': 4000},
}

def apply_profile(prompt, quality):
    profile = PROFILES[quality]
    cfg = 7.5 if prompt['80']['class_type'] == 'Hunyuan3Dv2ConditioningMultiView' else profile['cfg']
    prompt['3']['inputs'].update(steps=profile['steps'], cfg=cfg)
    prompt['61']['inputs']['octree_resolution'] = profile['octree_resolution']
    prompt['61']['inputs']['num_chunks'] = profile['num_chunks']
    if quality == 'maximum':
        prompt['61']['class_type'] = 'FormaVAEDecodeHunyuan3D'
    if prompt['54']['inputs']['ckpt_name'] == HUNYUAN21_MODEL:
        # Follow the official 2.1 template's CFG and native latent capacity.
        # Stream the volume at every quality to leave more GPU memory available.
        prompt['3']['inputs']['cfg'] = 5.0
        prompt['61']['class_type'] = 'FormaVAEDecodeHunyuan3D'
        prompt['61']['inputs']['num_chunks'] = 2048
    return prompt
