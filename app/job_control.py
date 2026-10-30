"""Cancellation shared by the web app and independent calculation workers."""
import asyncio
import json
import os
from pathlib import Path
import time

from app.persistence import write_json

ACTIVE = ('queued', 'running', 'stopping')
RUNNING_TASKS = {}


class JobCancelled(Exception):
    pass


def check_cancelled(path):
    if (path / 'cancel.request.json').is_file():
        raise JobCancelled('Detenido por el usuario.')


def register_worker(path):
    write_json(path / 'worker.json', {'pid':os.getpid(), 'registered_at':time.time()})


def finish_cancelled(path):
    record = json.loads((path/'project.json').read_text(encoding='utf-8'))
    if record.get('status') == 'ready':
        return record
    now = time.time()
    record.update(status='cancelled', cancelled_at=now, error=None,
                  cancellation_reason='Detenido por el usuario. Los archivos se conservan.')
    record['progress'] = dict(record.get('progress',{}), stage='cancelled',
                              label='Generación detenida', percent=None, updated_at=now)
    write_json(path/'project.json', record)
    return record


def scope(data, identifier):
    """A comparison stops as a unit, including its not-yet-created stages."""
    records = {p.parent.name:json.loads(p.read_text(encoding='utf-8')) for p in data.glob('*/project.json')}
    groups = []
    identifiers = {identifier}
    for manifest in (data.parent/'experiments').glob('*/experiment.json'):
        state = json.loads(manifest.read_text(encoding='utf-8'))
        members = {item['id'] for item in state.get('projects',[])}
        if identifier in members and state.get('state') not in ('ready','cancelled'):
            groups.append(manifest.parent)
            identifiers.update(members)
    return {key:records[key] for key in identifiers if key in records and records[key].get('status') in ACTIVE}, groups


def stop_processes(root, data, records, groups):
    """Terminate only verified project calculation processes, never the services."""
    import psutil
    modules = ('scripts.refine_ultrashape','scripts.run_hybrid_fidelity','scripts.run_fidelity_batch')
    snapshots = {}
    for process in psutil.process_iter(['pid','name','cmdline','cwd','create_time']):
        try:
            info = process.info
            command = info['cmdline'] or []
            module = next((m for m in modules if '-m' in command and command[command.index('-m')+1:command.index('-m')+2] == [m]), None)
            if module and Path(info['cwd']).resolve() == root.resolve() and process.pid != os.getpid():
                snapshots[process.pid] = (process, module, command, info['create_time'])
        except (psutil.Error, OSError, TypeError):
            continue
    selected = set()
    # Registry timestamps prevent an old PID from selecting a later process.
    for directory in [data/key for key in records] + groups:
        registration = directory/'worker.json'
        if registration.is_file():
            owner = json.loads(registration.read_text(encoding='utf-8'))
            candidate = snapshots.get(owner['pid'])
            if candidate and owner['registered_at']-120 <= candidate[3] <= owner['registered_at']+1:
                selected.add(owner['pid'])
    # Compatibility with calculations already launched before the controls existed.
    for pid, (process, module, command, _) in snapshots.items():
        argument = command[command.index(module)+1:command.index(module)+2]
        if module == 'scripts.refine_ultrashape':
            if argument and (argument[0] in records if '--prepared' in command else any(
                    r.get('refinement',{}).get('source_project') == argument[0] for r in records.values())):
                selected.add(pid)
        elif module == 'scripts.run_hybrid_fidelity' and '--resume' in command:
            if command[command.index('--resume')+1:command.index('--resume')+2] in [[p.name] for p in groups]:
                selected.add(pid)
    # Stop the batch driver before its children so it cannot launch the next job.
    for pid in list(selected):
        try:
            for parent in snapshots[pid][0].parents():
                if parent.pid in snapshots and snapshots[parent.pid][1] != 'scripts.refine_ultrashape':
                    selected.add(parent.pid)
        except psutil.Error:
            pass
    for pid in list(selected):
        try:
            selected.update(child.pid for child in snapshots[pid][0].children(recursive=True) if child.pid in snapshots)
        except psutil.Error:
            pass
    processes = [snapshots[pid][0] for pid in sorted(selected,key=lambda p:snapshots[p][1]=='scripts.refine_ultrashape')]
    for process in processes:
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass
        except psutil.Error as error:
            raise RuntimeError('Windows no permitió detener el proceso del cálculo.') from error
    _, alive = psutil.wait_procs(processes, timeout=5)
    for process in alive:
        try:
            process.kill()
        except psutil.NoSuchProcess:
            pass
        except psutil.Error as error:
            raise RuntimeError('Windows no permitió cerrar el proceso del cálculo.') from error
    _, alive = psutil.wait_procs(alive, timeout=3)
    if alive:
        raise RuntimeError('El cálculo todavía no se ha detenido. Vuelve a pulsar Detener.')
    return [p.pid for p in processes]


async def stop_comfy(comfy, records):
    import httpx
    identifiers = set(records)
    prompts = {r.get('prompt_id') for r in records.values()} - {None}
    def owned(entry):
        return entry[1] in prompts or (len(entry)>3 and entry[3].get('client_id') in identifiers)
    async with httpx.AsyncClient(base_url=comfy,timeout=15) as client:
        try:
            queue = (await client.get('/queue')).raise_for_status().json()
        except httpx.HTTPError:
            if any(r.get('model_family') != 'ultrashape' for r in records.values()):
                raise RuntimeError('No se pudo comprobar ComfyUI. Vuelve a pulsar Detener cuando esté disponible.')
            return
        jobs = [e[1] for key in ('queue_running','queue_pending') for e in queue.get(key,[]) if owned(e)]
        for prompt in jobs:
            # This installed ComfyUI endpoint atomically targets one prompt.
            (await client.post(f'/api/jobs/{prompt}/cancel')).raise_for_status()
        for _ in range(30):
            queue = (await client.get('/queue')).raise_for_status().json()
            if not any(owned(e) for key in ('queue_running','queue_pending') for e in queue.get(key,[])):
                if not queue.get('queue_running') and not queue.get('queue_pending'):
                    (await client.post('/free',json={'unload_models':True,'free_memory':True})).raise_for_status()
                return
            await asyncio.sleep(.5)
    raise RuntimeError('El motor está terminando de detenerse. Vuelve a pulsar Detener en unos segundos.')


async def stop(root, data, comfy, identifier):
    records, groups = scope(data,identifier)
    now = time.time()
    for path in [data/key for key in records] + groups:
        write_json(path/'cancel.request.json',{'requested_at':now})
    for key, record in records.items():
        record.update(status='stopping')
        write_json(data/key/'project.json',record)
    local = [RUNNING_TASKS[key] for key in records if key in RUNNING_TASKS]
    for task in local:
        task.cancel()
    if local:
        await asyncio.gather(*local,return_exceptions=True)
    await asyncio.to_thread(stop_processes, root, data, records, groups)
    # A driver could have created its next record while the stop request arrived.
    # Once the driver is gone, capture and stop any such child before confirming.
    latest, _ = scope(data,identifier)
    for directory in groups:
        manifest = json.loads((directory/'experiment.json').read_text(encoding='utf-8'))
        for item in manifest.get('projects',[]):
            path = data/item['id']/'project.json'
            if path.is_file():
                record = json.loads(path.read_text(encoding='utf-8'))
                if record.get('status') in ACTIVE:
                    latest[item['id']] = record
    additions = {key:value for key,value in latest.items() if key not in records}
    if additions:
        for key,record in additions.items():
            write_json(data/key/'cancel.request.json',{'requested_at':now})
            record['status'] = 'stopping'
            write_json(data/key/'project.json',record)
        records.update(additions)
    await asyncio.to_thread(stop_processes, root, data, records, groups)
    await stop_comfy(comfy,records)
    for key in records:
        finish_cancelled(data/key)
    for directory in groups:
        path = directory/'experiment.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        manifest.update(state='cancelled',finished_at=time.time(),cancellation_reason='Detenido por el usuario.')
        for item in manifest.get('projects',[]):
            if item['id'] in records:
                item['status'] = 'cancelled'
        write_json(path,manifest)
    return json.loads((data/identifier/'project.json').read_text(encoding='utf-8'))
