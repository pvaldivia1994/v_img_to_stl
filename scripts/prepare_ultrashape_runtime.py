"""Small audited inference-only compatibility changes, with provenance."""
import hashlib
import json
from pathlib import Path
import subprocess
import httpx

ROOT = Path('C:/_IA/UltraShape-1.0')
CHANGES = [
    ('ultrashape/surface_loaders.py',
     'rng = np.random.default_rng()',
     'rng = np.random.default_rng(int(np.random.randint(0, 2**32, dtype=np.uint32)))  # Forma reproducible sampling'),
    ('ultrashape/__init__.py',
     'from .postprocessors import FaceReducer, FloaterRemover, DegenerateFaceRemover, MeshSimplifier',
     '# Forma inference-only: postprocessors are not imported or used.'),
    ('ultrashape/models/autoencoders/__init__.py',
     'from .vae_trainer import VAETrainer',
     '# Forma inference-only: training dependencies are not imported.'),
    ('ultrashape/models/autoencoders/surface_extractors.py',
     'import cubvh',
     'try:\n    import cubvh\nexcept ImportError:\n    cubvh = None  # Forma supplies a CPU Lewiner extractor explicitly.'),
    ('ultrashape/models/denoisers/dit_mask.py',
     'from flash_attn import flash_attn_varlen_func',
     'try:\n    from flash_attn import flash_attn_varlen_func\nexcept ImportError:\n    from scripts.ultrashape_compat import flash_attn_varlen_func'),
]


def main():
    previous = ROOT / 'forma-runtime.json'
    old = {p['path']:p for p in json.loads(previous.read_text()).get('patches',[])} if previous.exists() else {}
    manifest = {'revision': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(), 'patches': []}
    for relative, original, replacement in CHANGES:
        path = ROOT / relative
        text = path.read_text(encoding='utf-8')
        before = old.get(relative,{}).get('before',hashlib.sha256(text.encode()).hexdigest())
        if replacement not in text:
            if text.count(original) != 1:
                raise RuntimeError('Unexpected upstream source: ' + relative)
            path.write_text(text.replace(original, replacement), encoding='utf-8')
        manifest['patches'].append({'path': relative, 'before': before,
                                    'after': hashlib.sha256(path.read_bytes()).hexdigest()})
    target = Path('C:/_IA/models/ultrashape/dinov2-config.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        response = httpx.get('https://huggingface.co/facebook/dinov2-large/resolve/main/config.json', follow_redirects=True, timeout=60)
        response.raise_for_status()
        config = response.json()
        if config.get('hidden_size') != 1024 or config.get('num_hidden_layers') != 24:
            raise RuntimeError('Unexpected DINO architecture.')
        target.write_text(json.dumps(config, indent=2), encoding='utf-8')
    manifest['dino_config_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / 'forma-runtime.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
