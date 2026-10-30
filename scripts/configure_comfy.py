"""Configure the portable installation without copying the model."""
import hashlib
import json
import subprocess
import shutil
from pathlib import Path

base = Path('C:/_IA/ComfyUI_windows_portable')
comfy = base / 'ComfyUI'
model = Path('C:/_IA/models/checkpoints/hunyuan3d-dit-v2.safetensors')
expected = '360bc281fc956d4acac0c3d36d5ec0ebf8cdddbf4b8892e894d12419388d479b'
if hashlib.file_digest(model.open('rb'), 'sha256').hexdigest() != expected:
    raise RuntimeError('Model checksum mismatch')
configuration = comfy / 'extra_model_paths.yaml'
content = 'local_ia:\n  base_path: C:/_IA/models\n  checkpoints: checkpoints\n'
if configuration.exists() and configuration.read_text() != content:
    raise RuntimeError('An existing model path configuration needs review')
configuration.write_text(content)
runtime = base / 'python_embeded/python.exe'
result = subprocess.run([str(runtime), '-s', '-c', 'import torch,json,sys; print(json.dumps({"python":sys.version,"torch":torch.__version__,"cuda":torch.version.cuda,"gpu":torch.cuda.get_device_name(0),"vram_bytes":torch.cuda.get_device_properties(0).total_memory}))'], capture_output=True, text=True, check=True)
root = Path(__file__).resolve().parents[1]
shutil.copytree(root / 'comfy_nodes/forma_mesh', comfy / 'custom_nodes/forma_mesh', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
(root / 'docs/runtime.json').write_text(result.stdout, encoding='utf-8')
print(result.stdout)
