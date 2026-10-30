"""Extraction-only comparison with visible progress and preserved model family."""
import argparse
import asyncio
import json
import httpx
from app.main import COMFY, DATA
from scripts.run_fidelity_batch import extraction

async def main(args):
    source = DATA / args.source_project
    baseline = json.loads((source / 'project.json').read_text(encoding='utf-8'))
    if baseline.get('status') != 'ready':
        raise RuntimeError('La malla inicial todavia no esta lista.')
    async with httpx.AsyncClient(base_url=COMFY) as client:
        queue = (await client.get('/queue')).raise_for_status().json()
        if queue.get('queue_running') or queue.get('queue_pending'):
            raise RuntimeError('El motor ya esta ocupado.')
    if any(json.loads(p.read_text(encoding='utf-8')).get('status') in ('queued', 'running')
           for p in DATA.glob('*/project.json')):
        raise RuntimeError('Hay otro proyecto activo.')
    record = await extraction(source, baseline, args.threshold)
    print(json.dumps({'project': record['id'], 'status': record['status'],
                      'elapsed_seconds': record.get('elapsed_seconds')}, ensure_ascii=True))
    if record['status'] != 'ready':
        raise RuntimeError(record.get('error', 'Fallo la extraccion.'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_project')
    parser.add_argument('--threshold', type=float, default=.5)
    args = parser.parse_args()
    if not 0 < args.threshold < 1:
        parser.error('El nivel normalizado debe estar estrictamente entre 0 y 1.')
    asyncio.run(main(args))
