import asyncio
from contextlib import asynccontextmanager
import io
import json
import os
from pathlib import Path
import time
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from scripts.export_stl import export
from app.profiles import PROFILES, apply_profile
from app.workflows import build_workflow, SINGLE_MODEL, MULTIVIEW_MODEL, HUNYUAN21_MODEL
from app.progress import set_stage, watch_progress
from app.fidelity import apply_fidelity
from app.refinement import ready as refinement_ready, create_refinement, launch_refinement
from app.reference_preparation import split_known_sheet
from app.persistence import write_json
from app import job_control
from app.regeneration import clone as clone_generation

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/projects'
DATA.mkdir(parents=True, exist_ok=True)
COMFY = os.environ.get('COMFY_URL', 'http://127.0.0.1:8188').rstrip('/')
tasks = set()
generation_lock = asyncio.Lock()
control_lock = asyncio.Lock()

def folder(identifier):
    if not identifier or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in identifier):
        raise HTTPException(404, 'Proyecto inexistente')
    path = DATA / identifier
    if not (path / 'project.json').exists():
        raise HTTPException(404, 'Proyecto inexistente')
    return path

def read(path):
    return json.loads((path / 'project.json').read_text(encoding='utf-8'))

def save(path, record):
    if (path/'cancel.request.json').is_file():
        return
    write_json(path / 'project.json', record)

async def collect(path, record):
    async with httpx.AsyncClient(base_url=COMFY, timeout=60) as client:
        missing_count = 0
        while True:
            job_control.check_cancelled(path)
            response = await client.get('/history/' + record['prompt_id'])
            response.raise_for_status()
            history = response.json().get(record['prompt_id'])
            if history:
                (path / 'history.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
                if history.get('status', {}).get('status_str') == 'error':
                    messages = history.get('status', {}).get('messages', [])
                    error = next((data.get('exception_message', '') for kind, data in messages if kind == 'execution_error'), '')
                    raise RuntimeError('ComfyUI no pudo generar la malla. ' + error)
                for node in history.get('outputs', {}).values():
                    for item in node.get('3d', []):
                        if str(item.get('filename', '')).endswith('.glb'):
                            result = await client.get('/view', params={key: item[key] for key in ('filename', 'subfolder', 'type') if key in item})
                            result.raise_for_status()
                            (path / 'original.glb').write_bytes(result.content)
                            record.update(status='ready', elapsed_seconds=round(time.time() - record['started_at'], 1))
                            set_stage(record, 'complete', 1, 1)
                            save(path, record)
                            return
                raise RuntimeError('El trabajo terminó sin un archivo GLB.')
            queue_response = await client.get('/queue')
            queue_response.raise_for_status()
            queue = queue_response.json()
            queued_ids = {item[1] for key in ('queue_running', 'queue_pending') for item in queue.get(key, [])}
            missing_count = missing_count + 1 if record['prompt_id'] not in queued_ids else 0
            if missing_count >= 3:
                raise RuntimeError('El trabajo ya no aparece en ComfyUI. Puede haberse reiniciado el motor; genera una nueva variante.')
            await asyncio.sleep(3)

async def generate(path, record):
    async with generation_lock:
        watcher = None
        job_control.RUNNING_TASKS[record['id']] = asyncio.current_task()
        try:
            job_control.check_cancelled(path)
            if record.get('worker'):
                job_control.register_worker(path)
            record.update(status='running', started_at=time.time(), error=None)
            set_stage(record, 'preparing')
            save(path, record)
            if record.get('remove_background'):
                from scripts.remove_background import prepare
                for view, filename in record.get('views', {'front': 'input.png'}).items():
                    job_control.check_cancelled(path)
                    source = 'source.png' if view == 'front' else f'source-{view}.png'
                    prepared = path / f'prepared-{view}.png'
                    await asyncio.to_thread(prepare, path / source, prepared)
                    prepared.replace(path / filename)
            async with httpx.AsyncClient(base_url=COMFY, timeout=60) as client:
                uploaded_views = {}
                for view, filename in record.get('views', {'front': 'input.png'}).items():
                    with (path / filename).open('rb') as image:
                        response = await client.post('/upload/image', files={'image': (f"{record['id']}-{view}.png", image, 'image/png')})
                    response.raise_for_status()
                    uploaded = response.json()
                    uploaded_views[view] = '/'.join(filter(None, [uploaded.get('subfolder'), uploaded['name']]))
                prompt = build_workflow(uploaded_views, record['seed'], 'mesh/' + record['id'], record.get('model_family', 'hunyuan2'))
                apply_profile(prompt, record.get('quality', 'standard'))
                if record.get('fidelity_settings'):
                    apply_fidelity(prompt, record['fidelity_settings'])
                record['prompt'] = prompt
                set_stage(record, 'loading')
                connected = asyncio.Event()
                watcher = asyncio.create_task(watch_progress(COMFY, record, lambda: save(path, record), connected))
                try:
                    await asyncio.wait_for(connected.wait(), timeout=3)
                except TimeoutError:
                    pass
                job_control.check_cancelled(path)
                response = await client.post('/prompt', json={'prompt': prompt, 'client_id': record['id']})
                if response.is_error:
                    raise RuntimeError('ComfyUI rechazó el flujo: ' + response.text[:1500])
                record['prompt_id'] = response.json()['prompt_id']
                save(path, record)
            await collect(path, record)
        except job_control.JobCancelled:
            record.update(job_control.finish_cancelled(path))
        except asyncio.CancelledError:
            raise
        except Exception as error:
            record.update(status='error', error=str(error))
            save(path, record)
        finally:
            job_control.RUNNING_TASKS.pop(record['id'],None)
            if watcher:
                watcher.cancel()
                await asyncio.gather(watcher, return_exceptions=True)

def schedule(coroutine):
    task = asyncio.create_task(coroutine)
    tasks.add(task)
    task.add_done_callback(tasks.discard)

async def resume(path, record):
    async with generation_lock:
        job_control.RUNNING_TASKS[record['id']] = asyncio.current_task()
        watcher = asyncio.create_task(watch_progress(COMFY, record, lambda: save(path, record)))
        try:
            await collect(path, record)
        except Exception as error:
            record.update(status='error', error='No se pudo recuperar el resultado: ' + str(error))
            save(path, record)
        finally:
            job_control.RUNNING_TASKS.pop(record['id'],None)
            watcher.cancel()
            await asyncio.gather(watcher, return_exceptions=True)

@asynccontextmanager
async def lifespan(app):
    for path in DATA.iterdir():
        if (path / 'project.json').exists():
            record = read(path)
            if record['status'] in ('running', 'queued'):
                if record.get('worker'):
                    # Independent refinement/batch workers own their recovery and records.
                    continue
                if record.get('prompt_id'):
                    schedule(resume(path, record))
                else:
                    record.update(status='error', error='La aplicación se cerró antes de confirmar el envío. Revisa la cola de ComfyUI antes de repetir.')
                    save(path, record)
    yield
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

app = FastAPI(title='Imagen a STL', lifespan=lifespan)

@app.post('/api/projects/{identifier}/stop')
async def stop_model(identifier: str):
    path = folder(identifier)
    async with control_lock:
        record = read(path)
        if record['status'] == 'cancelled':
            return record
        if record['status'] not in job_control.ACTIVE:
            raise HTTPException(409,'Esta generación ya terminó. Puedes regenerarla.')
        try:
            return await job_control.stop(ROOT,DATA,COMFY,identifier)
        except (OSError,RuntimeError,httpx.HTTPError) as error:
            raise HTTPException(503,'No se confirmó la detención. '+str(error)) from error

@app.post('/api/projects/{identifier}/regenerate',status_code=201)
async def regenerate_model(identifier: str):
    source = folder(identifier)
    async with control_lock:
        baseline = read(source)
        if baseline['status'] in job_control.ACTIVE:
            raise HTTPException(409,'Detén esta generación antes de regenerarla.')
        state = await health()
        if state.get('busy') or any(not task.done() for task in tasks) or any(
                read(p).get('status') in job_control.ACTIVE for p in DATA.iterdir() if (p/'project.json').exists()):
            raise HTTPException(409,'Hay otro trabajo en curso. Deténlo o espera a que termine.')
        refinement = baseline.get('model_family') == 'ultrashape'
        if not state.get('connected') or (not refinement and not state.get('ready')):
            raise HTTPException(503,'Inicia ComfyUI antes de regenerar.')
        if refinement and not refinement_ready():
            raise HTTPException(503,'El refinador todavía no está disponible.')
        if not refinement:
            family = baseline.get('model_family','hunyuan2')
            model_ready = state.get('hunyuan21_ready') if family=='hunyuan21' else state.get(
                'multiview_ready' if len(baseline.get('views',{}))>1 else 'single_ready',state.get('ready'))
            if not model_ready or (baseline.get('quality')=='maximum' and not state.get('maximum_ready')):
                raise HTTPException(503,'El modelo o el modo de detalle usados todavía no están disponibles.')
        try:
            path,record = clone_generation(source,DATA)
        except ValueError as error:
            raise HTTPException(422,str(error)) from error
        schedule(launch_refinement(path) if refinement else generate(path,record))
        return record

@app.get('/api/health')
async def health():
    try:
        async with httpx.AsyncClient(base_url=COMFY, timeout=8) as client:
            result = await client.get('/object_info')
            result.raise_for_status()
            nodes = result.json()
            workflow = json.loads((ROOT / 'workflows/hunyuan3d-2-api.json').read_text())
            missing = sorted({n['class_type'] for n in workflow.values()} - nodes.keys())
            models = nodes.get('ImageOnlyCheckpointLoader', {}).get('input', {}).get('required', {}).get('ckpt_name', [[]])[0]
            model_found = SINGLE_MODEL in models
            single_ready = not missing and model_found
            multiview_ready = not missing and 'Hunyuan3Dv2ConditioningMultiView' in nodes and MULTIVIEW_MODEL in models
            hunyuan21_ready = not missing and 'FormaVAEDecodeHunyuan3D' in nodes and HUNYUAN21_MODEL in models
            queue_response = await client.get('/queue')
            queue_response.raise_for_status()
            queue = queue_response.json()
            return {'connected': True, 'ready': single_ready or multiview_ready or hunyuan21_ready, 'single_ready': single_ready, 'multiview_ready': multiview_ready, 'hunyuan21_ready': hunyuan21_ready, 'maximum_ready': 'FormaVAEDecodeHunyuan3D' in nodes, 'refinement_ready': refinement_ready(), 'busy': bool(queue.get('queue_running') or queue.get('queue_pending')), 'missing_nodes': missing, 'model_found': model_found}
    except Exception:
        return {'connected': False, 'ready': False}

@app.get('/api/projects')
def projects():
    records = [read(path) for path in DATA.iterdir() if (path / 'project.json').exists()]
    return sorted(records, key=lambda row: row['created_at'], reverse=True)

@app.post('/api/projects/{identifier}/refine', status_code=201)
async def refine_model(identifier: str):
    source = folder(identifier)
    if read(source)['status'] != 'ready':
        raise HTTPException(409, 'Primero espera a que termine la malla inicial.')
    if not refinement_ready():
        raise HTTPException(503, 'El refinador todavía no está instalado y verificado.')
    state = await health()
    if not state.get('connected'):
        raise HTTPException(503, 'Inicia ComfyUI antes de refinar.')
    if state.get('busy') or tasks or any(read(p).get('status') in job_control.ACTIVE for p in DATA.iterdir() if (p / 'project.json').exists()):
        raise HTTPException(409, 'Ya hay un trabajo en curso. Espera a que termine.')
    path, record = create_refinement(source, DATA)
    schedule(launch_refinement(path))
    return record

@app.get('/api/projects/{identifier}')
def project(identifier: str):
    return read(folder(identifier))

async def normalize_image(image):
    data = await image.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, 'La imagen supera los 20 MB.')
    try:
        with Image.open(io.BytesIO(data)) as loaded:
            if loaded.format not in ('PNG', 'JPEG') or loaded.width * loaded.height > 40_000_000:
                raise ValueError('Usa una imagen PNG/JPG de hasta 40 megapíxeles.')
            loaded.load()
            converted = loaded.convert('RGBA')
            background = Image.new('RGBA', converted.size, 'white')
            background.alpha_composite(converted)
            normalized = background.convert('RGB')
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise HTTPException(422, 'Imagen inválida. ' + str(error))
    return normalized

@app.post('/api/projects', status_code=201)
async def create(image: UploadFile = File(...), remove_background: bool = Form(True), seed: int | None = Form(default=None, ge=0, le=4294967295), quality: str = Form('standard'), back_image: UploadFile | None = File(None), left_image: UploadFile | None = File(None), right_image: UploadFile | None = File(None), model_family: str = Form('hunyuan2')):
    if quality not in PROFILES:
        raise HTTPException(422, 'Elige una calidad disponible.')
    if model_family not in ('hunyuan2', 'hunyuan21'):
        raise HTTPException(422, 'Elige un modelo disponible.')
    if model_family == 'hunyuan21' and any(view is not None for view in (back_image, left_image, right_image)):
        raise HTTPException(422, 'Hunyuan3D 2.1 utiliza una sola imagen frontal. Desactiva las vistas adicionales.')
    if tasks:
        raise HTTPException(409, 'Ya hay una generación en curso. Espera a que termine.')
    images = {'front': await normalize_image(image)}
    for view, uploaded in (('back', back_image), ('left', left_image), ('right', right_image)):
        if uploaded is not None:
            images[view] = await normalize_image(uploaded)
    sheet_image = None
    extracted, input_preparation = split_known_sheet(images['front'], model_family)
    if extracted:
        sheet_image = images['front']
        images['front'] = extracted.pop('front')
        for view, prepared in extracted.items():
            images.setdefault(view, prepared)
    state = await health()
    if not state['ready']:
        raise HTTPException(503, 'ComfyUI no está listo. Comprueba que está iniciado y que el modelo está instalado.')
    if quality == 'maximum' and not state.get('maximum_ready'):
        raise HTTPException(503, 'El modo de máximo detalle necesita actualizar y reiniciar ComfyUI.')
    if model_family == 'hunyuan21' and not state.get('hunyuan21_ready'):
        raise HTTPException(503, 'El modelo Hunyuan3D 2.1 todavía no está disponible.')
    if model_family == 'hunyuan2' and len(images) > 1 and not state.get('multiview_ready'):
        raise HTTPException(503, 'El modelo para varias vistas todavía no está disponible.')
    if model_family == 'hunyuan2' and len(images) == 1 and not state.get('single_ready', state['ready']):
        raise HTTPException(503, 'El modelo para una imagen todavía no está disponible.')
    if state.get('busy') or any(read(p).get('status') in job_control.ACTIVE for p in DATA.iterdir() if (p/'project.json').exists()):
        raise HTTPException(409, 'ComfyUI ya tiene un trabajo en curso. Espera a que termine.')
    # Recheck after awaited health call: a concurrent upload may have started.
    if tasks:
        raise HTTPException(409, 'Ya hay una generación en curso.')
    identifier = uuid.uuid4().hex
    path = DATA / identifier
    path.mkdir()
    if sheet_image:
        sheet_image.save(path / 'source-sheet.png')
    views = {}
    for view, normalized in images.items():
        filename = 'input.png' if view == 'front' else f'input-{view}.png'
        source = 'source.png' if view == 'front' else f'source-{view}.png'
        normalized.save(path / filename)
        (path / source).write_bytes((path / filename).read_bytes())
        views[view] = filename
    record = {'id': identifier, 'name': Path(image.filename or 'Figura').stem[:100], 'created_at': time.time(), 'seed': seed if seed is not None else int.from_bytes(os.urandom(4), 'little'), 'status': 'queued', 'remove_background': remove_background, 'quality': quality, 'mode': 'multiview' if len(views) > 1 else 'single', 'views': views, 'background_model': 'u2net' if remove_background else None, 'exports': []}
    record['model_family'] = model_family
    if input_preparation:
        record['input_preparation'] = input_preparation
    set_stage(record, 'preparing')
    save(path, record)
    schedule(generate(path, record))
    return record

class ExportRequest(BaseModel):
    height: float = Field(gt=0, le=2000, allow_inf_nan=False)
    up: str = Field(default='y', pattern='^(y|z)$')
    keep_largest: bool = False

@app.post('/api/projects/{identifier}/export')
async def export_model(identifier: str, request: ExportRequest):
    path = folder(identifier)
    record = read(path)
    if record['status'] != 'ready':
        raise HTTPException(409, 'La malla todavía no está lista.')
    name = 'model-' + uuid.uuid4().hex[:10] + '.stl'
    try:
        report = await asyncio.to_thread(export, path / 'original.glb', path / name, request.height, request.up, request.keep_largest)
    except Exception as error:
        raise HTTPException(422, 'No se pudo exportar: ' + str(error))
    # Reload so independent completed exports remain in the history.
    record = read(path)
    record.setdefault('exports', []).append({'filename': name, 'report': report, 'created_at': time.time()})
    save(path, record)
    return record

@app.post('/api/projects/{identifier}/repeat', status_code=201)
async def repeat(identifier: str):
    path = folder(identifier)
    record = read(path)
    source = path / 'source.png' if (path / 'source.png').exists() else path / 'input.png'
    image = UploadFile(filename=record['name'] + '.png', file=source.open('rb'))
    extras = {}
    for view in ('back', 'left', 'right'):
        if view in record.get('views', {}):
            source = path / f'source-{view}.png'
            if not source.exists():
                source = path / record['views'][view]
            extras[view] = UploadFile(filename=f'{view}.png', file=source.open('rb'))
    try:
        return await create(image, record.get('remove_background', False), None, record.get('quality', 'standard'), extras.get('back'), extras.get('left'), extras.get('right'), record.get('model_family', 'hunyuan2'))
    finally:
        await image.close()
        for uploaded in extras.values():
            await uploaded.close()

@app.get('/api/projects/{identifier}/files/{filename}')
def files(identifier: str, filename: str):
    path = folder(identifier)
    record = read(path)
    allowed = {'input.png', 'original.glb'} | set(record.get('views', {}).values()) | {item['filename'] for item in record.get('exports', [])}
    if filename not in allowed or not (path / filename).is_file():
        raise HTTPException(404, 'Archivo inexistente')
    return FileResponse(path / filename)

if (ROOT / 'frontend/dist').exists():
    app.mount('/', StaticFiles(directory=ROOT / 'frontend/dist', html=True), name='frontend')
