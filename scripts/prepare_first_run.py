"""Prepare a single-view input and an API workflow from the official example."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
project = ROOT / 'data/projects/first-fox'
project.mkdir(parents=True, exist_ok=True)
with Image.open(ROOT / 'Zorro Durmiente en Luna Creciente.png') as image:
    # Main panel only: exclude the contact sheet and its divider lines.
    image.crop((0, 0, 917, 858)).convert('RGB').save(project / 'input-cropped.png')
with Image.open(ROOT / 'workflows/official-hunyuan3d-2.webp') as image:
    raw = image.getexif()[33432]
    workflow = json.loads(raw.removeprefix('workflow:').rstrip('\x00'))
(ROOT / 'workflows/official-hunyuan3d-2.json').write_text(json.dumps(workflow, indent=2), encoding='utf-8')
prompt = {
    '54': {'class_type': 'ImageOnlyCheckpointLoader', 'inputs': {'ckpt_name': 'hunyuan3d-dit-v2.safetensors'}},
    '56': {'class_type': 'LoadImage', 'inputs': {'image': 'fox-first.png'}},
    '51': {'class_type': 'CLIPVisionEncode', 'inputs': {'clip_vision': ['54', 1], 'image': ['56', 0], 'crop': 'none'}},
    '70': {'class_type': 'ModelSamplingAuraFlow', 'inputs': {'model': ['54', 0], 'shift': 1.0}},
    '66': {'class_type': 'EmptyLatentHunyuan3Dv2', 'inputs': {'resolution': 3072, 'batch_size': 1}},
    '80': {'class_type': 'Hunyuan3Dv2Conditioning', 'inputs': {'clip_vision_output': ['51', 0]}},
    '3': {'class_type': 'KSampler', 'inputs': {'model': ['70', 0], 'positive': ['80', 0], 'negative': ['80', 1], 'latent_image': ['66', 0], 'seed': 42, 'steps': 20, 'cfg': 8.0, 'sampler_name': 'euler', 'scheduler': 'normal', 'denoise': 1.0}},
    '61': {'class_type': 'VAEDecodeHunyuan3D', 'inputs': {'samples': ['3', 0], 'vae': ['54', 2], 'num_chunks': 8000, 'octree_resolution': 256}},
    '62': {'class_type': 'FormaVoxelToMesh', 'inputs': {'voxel': ['61', 0], 'threshold': 0.6}},
    '67': {'class_type': 'SaveGLB', 'inputs': {'mesh': ['62', 0], 'filename_prefix': 'mesh/fox-first'}},
}
(ROOT / 'workflows/hunyuan3d-2-api.json').write_text(json.dumps(prompt, indent=2), encoding='utf-8')
print(project)
