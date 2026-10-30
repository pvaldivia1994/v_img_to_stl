"""Sequential comparisons visible in the app; originals and parameters retained."""
import asyncio
import copy
import json
from pathlib import Path
import shutil
import time
import uuid
import argparse
import httpx
from PIL import Image
from app.main import DATA, COMFY, generate, collect, save
from app.progress import set_stage, watch_progress
from app.fidelity import frame_reference


def make_record(source, baseline, name, settings=None, occupancy=None, seed=None):
    identifier = uuid.uuid4().hex
    path = DATA / identifier
    path.mkdir()
    for filename in set(baseline.get('views', {'front': 'input.png'}).values()) | {'source.png', 'input.png'}:
        if (source / filename).is_file():
            shutil.copyfile(source / filename, path / filename)
    if occupancy:
        with Image.open(source / 'input.png') as image:
            frame_reference(image, occupancy).save(path / 'input.png')
        shutil.copyfile(path / 'input.png', path / 'source.png')
    record = {key: copy.deepcopy(baseline[key]) for key in
              ('seed', 'quality', 'model_family', 'mode', 'views') if key in baseline}
    record.update(id=identifier, name=name, created_at=time.time(), status='queued',
                  remove_background=False, exports=[], worker='fidelity-batch',
                  comparison={'source_project': baseline['id'], 'occupancy': occupancy,
                              'focus': ['flores', 'patitas', 'espalda']})
    if seed is not None:
        record['seed'] = seed
    if settings:
        record['fidelity_settings'] = settings
    set_stage(record, 'preparing')
    save(path, record)
    return path, record


async def extraction(source, baseline, threshold=.5):
    path, record = make_record(source, baseline, f'Flores · superficie {threshold:.2f} · misma forma')
    record['fidelity_settings'] = {'threshold': threshold}
    prompt = copy.deepcopy(baseline['prompt'])
    prompt['62']['inputs']['threshold'] = threshold
    prompt['67']['inputs']['filename_prefix'] = 'mesh/' + record['id']
    record.update(prompt=prompt, status='running', started_at=time.time())
    connected = asyncio.Event()
    watcher = asyncio.create_task(watch_progress(COMFY, record, lambda: save(path, record), connected))
    try:
        await asyncio.wait_for(connected.wait(), 5)
        async with httpx.AsyncClient(base_url=COMFY, timeout=60) as client:
            response = await client.post('/prompt', json={'prompt': prompt, 'client_id': record['id']})
            response.raise_for_status()
            record['prompt_id'] = response.json()['prompt_id']
            save(path, record)
        await collect(path, record)
    except Exception as error:
        record.update(status='error', error=str(error))
        save(path, record)
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
    return record


async def main(args):
    source = DATA / args.source_project
    baseline = json.loads((source / 'project.json').read_text(encoding='utf-8'))
    if baseline.get('status') != 'ready' or baseline.get('model_family') != 'hunyuan21':
        raise ValueError('Se necesita una referencia 2.1 terminada.')
    async with httpx.AsyncClient(base_url=COMFY, timeout=30) as client:
        queue = (await client.get('/queue')).raise_for_status().json()
        if queue.get('queue_running') or queue.get('queue_pending'):
            raise RuntimeError('El motor ya está ocupado.')
    if any(json.loads(p.read_text(encoding='utf-8')).get('status') in ('running', 'queued')
           for p in DATA.glob('*/project.json')):
        raise RuntimeError('Hay otro trabajo activo en la aplicación.')
    manifest = {'source_project': baseline['id'], 'started_at': time.time(), 'jobs': []}
    target = DATA.parent / f'fidelity-fox/batch-{int(manifest["started_at"])}.json'
    def note(record):
        manifest['jobs'].append({'id': record['id'], 'name': record['name'], 'status': record['status']})
        target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        (target.parent / 'batch.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(manifest['jobs'][-1], ensure_ascii=True), flush=True)
    if not args.skip_extraction:
        note(await extraction(source, baseline))
    # Isolate framing first. Other seeds use exactly this same framing/steps.
    trials = [('Flores · encuadre 85% · 50 pasos', baseline['seed'], 50),
              ('Flores · encuadre 85% · semilla B', baseline['seed']+1, 50),
              ('Flores · encuadre 85% · semilla C', baseline['seed']+2, 50),
              ('Flores · encuadre 85% · 75 pasos', baseline['seed'], 75)]
    selected_trials = trials[args.start_trial:args.start_trial+args.trials]
    for index, (name, seed, steps) in enumerate(selected_trials, 1):
        path, record = make_record(source, baseline, name, {'steps': steps, 'threshold': .5}, .85, seed % 2**32)
        record['batch'] = {'index': index, 'total': len(selected_trials),
                           'refinement_after': args.refine_after,
                           'next': 'Después: UltraShape con 75 pasos, 16384 latentes y superficie 768.' if args.refine_after else None}
        await generate(path, record)
        note(record)
        if record['status'] != 'ready':
            raise RuntimeError(record.get('error', 'Falló la comparación'))
    manifest['finished_at'] = time.time()
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    if args.refine_after:
        import subprocess
        command = ['C:/_IA/envs/ultrashape/Scripts/python.exe', '-m', 'scripts.refine_ultrashape',
                   record['id'], '--steps', '75', '--latents', '16384', '--resolution', '768', '--chunks', '1024']
        result = await asyncio.to_thread(subprocess.run, command, cwd=DATA.parents[1])
        if result.returncode:
            raise RuntimeError('El refinador indicó un error; consulta el proyecto y el registro del lote.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_project')
    parser.add_argument('--trials', type=int, choices=range(1, 5), default=4)
    parser.add_argument('--start-trial', type=int, choices=range(4), default=0)
    parser.add_argument('--skip-extraction', action='store_true')
    parser.add_argument('--refine-after', action='store_true')
    asyncio.run(main(parser.parse_args()))
