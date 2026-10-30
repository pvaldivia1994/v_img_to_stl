"""Persist actual ComfyUI node/step events; percentages belong to a stage."""
import asyncio
import json
import time
from urllib.parse import urlencode, urlsplit, urlunsplit

from websockets.asyncio.client import connect

STAGES = {
    'preparing': (1, 'Preparando las imágenes'),
    'loading': (2, 'Leyendo las vistas y cargando el modelo'),
    'shape': (3, 'Generando la forma'),
    'details': (4, 'Calculando los detalles de la superficie'),
    'surface': (5, 'Construyendo la malla'),
    'saving': (6, 'Guardando el modelo'),
    'complete': (6, 'Modelo disponible'),
}


def set_stage(record, stage, value=None, total=None):
    previous = record.get('progress', {})
    index, label = STAGES[stage]
    if index < previous.get('stage_index', 0):
        return False
    progress = {'stage': stage, 'stage_index': index, 'stage_count': 6,
                'label': label, 'updated_at': time.time(), 'percent': None}
    if total is not None and total > 0 and value is not None:
        progress.update(value=value, total=total, percent=round(100 * max(0, min(value / total, 1)), 1))
    elif previous.get('stage') == stage:
        for key in ('value', 'total', 'percent'):
            if key in previous:
                progress[key] = previous[key]
    if previous.get('stage') == stage:
        progress['started_at'] = previous.get('started_at', time.time())
    else:
        progress['started_at'] = time.time()
    record['progress'] = progress
    return True


def node_stage(record, node):
    kind = record.get('prompt', {}).get(str(node), {}).get('class_type', '')
    if kind == 'KSampler':
        return 'shape'
    if kind in ('VAEDecodeHunyuan3D', 'FormaVAEDecodeHunyuan3D'):
        return 'details'
    if kind == 'FormaVoxelToMesh':
        return 'surface'
    if kind == 'SaveGLB':
        return 'saving'
    return 'loading'


def apply_event(record, event):
    if record.get('status') not in ('queued', 'running'):
        return False
    data = event.get('data', {})
    if data.get('prompt_id') and data['prompt_id'] != record.get('prompt_id'):
        return False
    kind = event.get('type')
    if kind == 'executing':
        node = data.get('node')
        if node is None:
            return set_stage(record, 'saving')
        record['active_node'] = str(node)
        return set_stage(record, node_stage(record, node))
    if kind == 'progress':
        node = data.get('node', record.get('active_node'))
        return set_stage(record, node_stage(record, node), data.get('value'), data.get('max'))
    if kind == 'progress_state':
        running = [n for n in data.get('nodes', {}).values() if n.get('state') == 'running']
        if running:
            node = max(running, key=lambda n: STAGES[node_stage(record, n['node_id'])][0])
            return set_stage(record, node_stage(record, node['node_id']), node.get('value'), node.get('max'))
    return False


async def watch_progress(comfy_url, record, publish, connected=None):
    parts = urlsplit(comfy_url)
    url = urlunsplit(('wss' if parts.scheme == 'https' else 'ws', parts.netloc,
                     parts.path.rstrip('/') + '/ws', urlencode({'clientId': record['id']}), ''))
    last_write = 0
    while record.get('status') in ('queued', 'running'):
        try:
            async with connect(url, proxy=None, open_timeout=5, close_timeout=2, max_size=2**20) as socket:
                if connected:
                    connected.set()
                record['progress_connection'] = 'connected'
                publish()
                async for message in socket:
                    if not isinstance(message, str):
                        continue
                    old_stage = record.get('progress', {}).get('stage')
                    if apply_event(record, json.loads(message)):
                        now = time.monotonic()
                        if now - last_write >= 1 or old_stage != record['progress']['stage']:
                            publish()
                            last_write = now
        except Exception:
            # Progress transport must never fail an otherwise valid generation.
            record['progress_connection'] = 'reconnecting'
            if record.get('status') not in ('queued', 'running'):
                return
            publish()
            await asyncio.sleep(2)
