import asyncio
import io
import json

import httpx
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app import main
from app.profiles import apply_profile
from app.workflows import build_workflow, MULTIVIEW_MODEL, SINGLE_MODEL

def png(color='white'):
    output = io.BytesIO()
    Image.new('RGB', (20, 20), color).save(output, format='PNG')
    return output.getvalue()

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    monkeypatch.setattr(main, 'tasks', set())
    monkeypatch.setattr(main, 'schedule', lambda coroutine: coroutine.close())
    async def ready():
        return {'ready': True, 'single_ready': True, 'multiview_ready': True, 'busy': False}
    monkeypatch.setattr(main, 'health', ready)
    with TestClient(main.app) as client:
        yield client

def test_views_survive_storage_download_and_repeat(client):
    uploads = {'image': ('front.png', png(), 'image/png'), 'back_image': ('back.png', png('gray'), 'image/png'), 'left_image': ('left.png', png('red'), 'image/png')}
    result = client.post('/api/projects', files=uploads, data={'remove_background': 'false', 'quality': 'detail'})
    assert result.status_code == 201
    record = result.json()
    assert record['mode'] == 'multiview'
    assert set(record['views']) == {'front', 'back', 'left'}
    assert client.get(f"/api/projects/{record['id']}/files/input-back.png").status_code == 200
    assert client.get(f"/api/projects/{record['id']}/files/source-back.png").status_code == 404
    # Storage/repetition is checked after the simulated generation finishes.
    from app.persistence import write_json
    write_json(main.DATA / record['id'] / 'project.json', {**record, 'status':'ready'})
    repeated = client.post(f"/api/projects/{record['id']}/repeat")
    assert repeated.status_code == 201
    assert set(repeated.json()['views']) == set(record['views'])
    first = main.DATA / record['id']
    second = main.DATA / repeated.json()['id']
    assert (first / 'input-back.png').read_bytes() == (second / 'input-back.png').read_bytes()

def test_bad_secondary_view_rejected_without_creating_project(client):
    result = client.post('/api/projects', files={'image': ('front.png', png(), 'image/png'), 'back_image': ('back.png', b'invalid', 'image/png')})
    assert result.status_code == 422
    assert not list(main.DATA.iterdir())

def test_missing_multiview_model_blocks_submission(client, monkeypatch):
    async def single_only():
        return {'ready': True, 'single_ready': True, 'multiview_ready': False}
    monkeypatch.setattr(main, 'health', single_only)
    result = client.post('/api/projects', files={'image': ('front.png', png(), 'image/png'), 'back_image': ('back.png', png(), 'image/png')})
    assert result.status_code == 503
    assert not list(main.DATA.iterdir())


def test_known_contact_sheet_is_separated_before_generation(client):
    from app.reference_preparation import REFERENCE
    with REFERENCE.open('rb') as image:
        response=client.post('/api/projects',files={'image':('sheet.png',image,'image/png')},
                             data={'remove_background':'false'})
    record=response.raise_for_status().json()
    assert record['mode'] == 'multiview'
    assert set(record['views']) == {'front','back'}
    assert record['input_preparation']['kind'] == 'known-contact-sheet'
    path=main.DATA/record['id']
    assert (path/'source-sheet.png').is_file()
    from PIL import Image
    with Image.open(path/'input.png') as front:
        assert front.size == (914,855)

@pytest.mark.parametrize('views', [{'front':'front.png'}, {'front':'front.png','back':'back.png'}, {'front':'front.png','left':'left.png','back':'back.png','right':'right.png'}])
def test_workflow_selects_model_and_keeps_view_labels(views):
    prompt = build_workflow(views, 42, 'mesh/test')
    apply_profile(prompt, 'detail')
    assert prompt['54']['inputs']['ckpt_name'] == (MULTIVIEW_MODEL if len(views)>1 else SINGLE_MODEL)
    assert prompt['3']['inputs']['seed'] == 42
    for node in prompt.values():
        for value in node['inputs'].values():
            if isinstance(value, list) and len(value)==2 and isinstance(value[1], int):
                assert value[0] in prompt
    if len(views)>1:
        assert set(prompt['80']['inputs']) == set(views)
        assert prompt['3']['inputs']['cfg'] == 7.5
        for view, link in prompt['80']['inputs'].items():
            encoder = prompt[link[0]]
            loader = prompt[encoder['inputs']['image'][0]]
            assert loader['inputs']['image'] == views[view]

def test_generation_uploads_each_view_to_comfy(tmp_path, monkeypatch):
    original_client = httpx.AsyncClient
    submitted = {}
    def handler(request):
        if request.url.path == '/upload/image':
            name = 'front-upload.png' if not submitted else 'back-upload.png'
            submitted[name] = True
            return httpx.Response(200, json={'name': name, 'subfolder': ''})
        submitted['prompt'] = json.loads(request.content)['prompt']
        return httpx.Response(200, json={'prompt_id': 'test'})
    monkeypatch.setattr(main.httpx, 'AsyncClient', lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(main, 'generation_lock', asyncio.Lock())
    async def collect(path, record):
        record['status'] = 'ready'
        main.save(path, record)
    monkeypatch.setattr(main, 'collect', collect)
    for name in ('input.png','input-back.png'):
        (tmp_path / name).write_bytes(png())
    record = {'id':'test','seed':42,'quality':'standard','remove_background':False,'views':{'front':'input.png','back':'input-back.png'}}
    asyncio.run(main.generate(tmp_path, record))
    prompt = submitted['prompt']
    assert prompt['54']['inputs']['ckpt_name'] == MULTIVIEW_MODEL
    assert set(prompt['80']['inputs']) == {'front','back'}
    assert record['status'] == 'ready'
