import io
import json
import asyncio
import httpx

from fastapi.testclient import TestClient
from PIL import Image
import pytest
import trimesh

from app import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    monkeypatch.setattr(main, 'tasks', set())
    with TestClient(main.app) as client:
        yield client

def picture():
    buffer = io.BytesIO()
    Image.new('RGB', (20, 20), 'white').save(buffer, format='PNG')
    return buffer.getvalue()

def test_reject_invalid_image(client):
    result = client.post('/api/projects', files={'image': ('fake.png', b'not an image', 'image/png')})
    assert result.status_code == 422
    assert list(main.DATA.iterdir()) == []

def test_disconnected_does_not_create_project(client, monkeypatch):
    async def disconnected():
        return {'ready': False}
    monkeypatch.setattr(main, 'health', disconnected)
    result = client.post('/api/projects', files={'image': ('real.png', picture(), 'image/png')})
    assert result.status_code == 503
    assert list(main.DATA.iterdir()) == []

def test_external_comfy_job_blocks_upload(client, monkeypatch):
    async def occupied():
        return {'ready': True, 'busy': True}
    monkeypatch.setattr(main, 'health', occupied)
    result = client.post('/api/projects', files={'image': ('real.png', picture(), 'image/png')})
    assert result.status_code == 409

def test_upload_is_normalized_and_recorded(client, monkeypatch):
    async def ready():
        return {'ready': True, 'busy': False}
    monkeypatch.setattr(main, 'health', ready)
    monkeypatch.setattr(main, 'schedule', lambda coroutine: coroutine.close())
    result = client.post('/api/projects', files={'image': ('figure.png', picture(), 'image/png')}, data={'seed': '42', 'quality': 'detail'})
    assert result.status_code == 201
    identifier = result.json()['id']
    assert result.json()['seed'] == 42
    assert result.json()['quality'] == 'detail'
    assert client.get(f'/api/projects/{identifier}/files/input.png').status_code == 200
    assert client.get(f'/api/projects/{identifier}/files/project.json').status_code == 404
    assert client.get('/api/projects').json()[0]['name'] == 'figure'

def test_unknown_quality_rejected_before_creating_project(client):
    result = client.post('/api/projects', files={'image': ('figure.png', picture(), 'image/png')}, data={'quality': 'unknown'})
    assert result.status_code == 422
    assert list(main.DATA.iterdir()) == []

def test_export_and_download_preserve_original(client):
    path = main.DATA / 'test-model'
    path.mkdir()
    piece = trimesh.creation.box(extents=[1, 2, 1])
    fragment = trimesh.creation.icosphere(subdivisions=0, radius=.1)
    fragment.apply_translation([5, 0, 0])
    scene = trimesh.Scene([piece, fragment])
    original = scene.export(file_type='glb')
    (path / 'original.glb').write_bytes(original)
    record = dict(id='test-model', name='Test', status='ready', created_at=0, exports=[])
    (path / 'project.json').write_text(json.dumps(record))
    result = client.post('/api/projects/test-model/export', json={'height': 80, 'up': 'y', 'keep_largest': True})
    assert result.status_code == 200
    exported = result.json()['exports'][0]
    assert exported['report']['height_mm'] == 80
    assert exported['report']['removed_components'] == 1
    assert exported['report']['components'] == 1
    assert client.get('/api/projects/test-model/files/' + exported['filename']).status_code == 200
    assert (path / 'original.glb').read_bytes() == original
    assert client.post('/api/projects/test-model/export', json={'height': -5}).status_code == 422

def test_failed_generation_is_recorded(tmp_path, monkeypatch):
    original_client = httpx.AsyncClient
    def handler(request):
        if request.url.path == '/upload/image':
            return httpx.Response(200, json={'name': 'test.png', 'subfolder': ''})
        return httpx.Response(500, json={'error': 'generation unavailable'})
    monkeypatch.setattr(main.httpx, 'AsyncClient', lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(main, 'generation_lock', asyncio.Lock())
    (tmp_path / 'input.png').write_bytes(picture())
    record = dict(id='failed-test', status='queued', seed=42, remove_background=False)
    asyncio.run(main.generate(tmp_path, record))
    saved = json.loads((tmp_path / 'project.json').read_text(encoding='utf-8'))
    assert saved['status'] == 'error'
    assert saved['error']
    assert not (tmp_path / 'original.glb').exists()
