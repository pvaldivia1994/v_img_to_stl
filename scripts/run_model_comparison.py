"""Run a reproducible comparison on the existing engine, without restarting services.

Creates a normal project record so the running app displays inputs, progress,
errors and the saved GLB. This worker does not listen on a network port.
"""
import argparse
import asyncio
import json
from pathlib import Path
import subprocess
import time
import uuid

import httpx
from PIL import Image

from app.main import COMFY, DATA, generate, save
from app.progress import set_stage
from app.workflows import HUNYUAN21_MODEL


async def run(args):
    async with httpx.AsyncClient(base_url=COMFY, timeout=30) as client:
        queue = (await client.get('/queue')).raise_for_status().json()
        if queue.get('queue_running') or queue.get('queue_pending'):
            raise RuntimeError('The engine already has an active job. No comparison was submitted.')
        nodes = (await client.get('/object_info')).raise_for_status().json()
        models = nodes.get('ImageOnlyCheckpointLoader', {}).get('input', {}).get('required', {}).get('ckpt_name', [[]])[0]
        if HUNYUAN21_MODEL not in models or 'FormaVAEDecodeHunyuan3D' not in nodes:
            raise RuntimeError('The verified 2.1 checkpoint or streaming decoder is not available.')
    if any(json.loads(p.read_text(encoding='utf-8')).get('status') in ('queued', 'running')
           for p in DATA.glob('*/project.json')):
        raise RuntimeError('The application has an active project. No comparison was submitted.')
    identifier = uuid.uuid4().hex
    path = DATA / identifier
    with Image.open(args.image) as image:
        image.load()
        normalized = image.convert('RGB')
    path.mkdir()
    normalized.save(path / 'input.png')
    (path / 'source.png').write_bytes((path / 'input.png').read_bytes())
    record = {'id': identifier, 'name': args.name, 'created_at': time.time(), 'seed': args.seed,
              'status': 'queued', 'remove_background': False, 'background_model': None,
              'quality': args.quality, 'model_family': 'hunyuan21', 'mode': 'single',
              'views': {'front': 'input.png'}, 'exports': [],
              'comparison': {'source_image': str(args.image.resolve()),
                             'focus': ['flowers', 'front paws'], 'runner': 'standalone'}}
    set_stage(record, 'preparing')
    save(path, record)
    pointer = DATA.parent / 'fidelity-fox/latest-hunyuan21-project-id.txt'
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(identifier, encoding='utf-8')
    print('Project: ' + identifier, flush=True)
    task = asyncio.create_task(generate(path, record))
    while not task.done():
        try:
            gpu = await asyncio.to_thread(subprocess.run,
                ['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5)
            with (path / 'gpu-samples.csv').open('a', encoding='utf-8') as output:
                output.write(f'{time.time()},{gpu.stdout.strip()}\n')
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=5)
        except TimeoutError:
            pass
    await task
    print(json.dumps({'id': identifier, 'status': record['status'], 'error': record.get('error'),
                      'elapsed_seconds': record.get('elapsed_seconds')}, ensure_ascii=True), flush=True)
    if record['status'] != 'ready':
        raise RuntimeError(record.get('error', 'Generation failed'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image', type=Path)
    parser.add_argument('--quality', choices=['standard', 'detail', 'maximum'], default='maximum')
    parser.add_argument('--seed', type=int, default=4007959359)
    parser.add_argument('--name', default='Zorro - Hunyuan 2.1 - flores y patitas')
    asyncio.run(run(parser.parse_args()))
