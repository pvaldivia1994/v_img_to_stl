"""Refinement project creation and isolated execution; no torch in the app."""
import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid
from app.persistence import write_json

RUNTIME = Path('C:/_IA/envs/ultrashape/Scripts/python.exe')
WEIGHTS = Path('C:/_IA/models/ultrashape/ultrashape_v1.pt')
MANIFEST = Path('C:/_IA/UltraShape-1.0/forma-runtime.json')
VALIDATED = Path('C:/_IA/UltraShape-1.0/forma-validated.json')
DEFAULTS = {'steps': 75, 'latents': 16384, 'resolution': 768, 'chunks': 1024, 'seed': 42, 'sequential_cfg':False}


def ready():
    return RUNTIME.is_file() and WEIGHTS.is_file() and MANIFEST.is_file() and VALIDATED.is_file()


def create_refinement(source, data, settings=None, name='Flores · UltraShape · relieve fino'):
    settings = DEFAULTS | (settings or {})
    baseline = json.loads((source / 'project.json').read_text(encoding='utf-8'))
    if baseline.get('status') != 'ready' or not (source / 'original.glb').is_file():
        raise ValueError('Se necesita una malla inicial terminada.')
    path = data / uuid.uuid4().hex
    path.mkdir()
    for original, target in [('input.png', 'input.png'), ('input.png', 'source.png'), ('original.glb', 'coarse.glb')]:
        shutil.copyfile(source / original, path / target)
    views = {'front':'input.png'}
    for view, filename in baseline.get('views', {}).items():
        if view != 'front':
            target = f'input-{view}.png'
            shutil.copyfile(source / filename, path / target)
            views[view] = target
    if (source / 'conditioning-front.png').is_file():
        shutil.copyfile(source / 'conditioning-front.png', path / 'conditioning-front.png')
    now = time.time()
    record = {'id': path.name, 'name': name, 'status': 'queued', 'model_family': 'ultrashape',
        'quality': 'maximum', 'mode': 'single', 'views': views, 'exports': [],
        'created_at': now, 'seed': settings['seed'], 'worker': 'ultrashape',
        'refinement': {'source_project': baseline['id'], **{k:v for k,v in settings.items() if k != 'seed'},
            'cfg': 5., 'mc_level_raw': 0., 'offload': 'CPU initialization + sequential DiT blocks',
            'base_geometry_views':baseline.get('refinement',{}).get('base_geometry_views',list(baseline.get('views',{'front':'input.png'}))),
            'direct_image_views':['front'],
            'decoder': 'dense full attention streamed to RAM',
            'source_revision': json.loads(MANIFEST.read_text())['revision']},
        'progress': {'stage': 'refine-1', 'stage_index': 1, 'stage_count': 7,
            'label': 'Esperando el refinamiento de geometría', 'percent': None, 'updated_at': now}}
    write_json(path / 'project.json', record)
    return path, record


async def launch_refinement(path):
    root = Path(__file__).resolve().parents[1]
    log = root / 'data/logs' / (path.name+'-ultrashape.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if hasattr(subprocess, 'CREATE_NO_WINDOW') else {}
    try:
        with log.open('ab') as output:
            process = await asyncio.create_subprocess_exec(str(RUNTIME), '-m', 'scripts.refine_ultrashape',
                path.name, '--prepared', cwd=root, stdout=output, stderr=output, **options)
            code = await process.wait()
        record = json.loads((path / 'project.json').read_text(encoding='utf-8'))
        if code and record.get('status') in ('queued', 'running'):
            raise RuntimeError(f'El refinador se detuvo (código {code}). Revisa {log.name}.')
    except asyncio.CancelledError:
        # An independent worker survives an ordinary web app restart.
        raise
    except Exception as error:
        record = json.loads((path / 'project.json').read_text(encoding='utf-8'))
        if record.get('status') in ('queued', 'running'):
            record.update(status='error', error=str(error))
            write_json(path / 'project.json', record)
