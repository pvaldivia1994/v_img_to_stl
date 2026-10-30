import pytest
from fastapi.testclient import TestClient

from app import main
from app.profiles import apply_profile
from app.workflows import build_workflow, HUNYUAN21_MODEL
from tests.test_multiview import png


def test_21_uses_native_capacity_guidance_and_streaming_decode():
    graph = build_workflow({'front': 'front.png'}, 42, 'mesh/test21', 'hunyuan21')
    apply_profile(graph, 'maximum')
    assert graph['54']['inputs']['ckpt_name'] == HUNYUAN21_MODEL
    assert graph['66']['inputs']['resolution'] == 4096
    assert graph['70']['inputs']['sampling'] == 'flow'
    assert graph['3']['inputs']['cfg'] == 5
    assert graph['3']['inputs']['steps'] == 50
    assert graph['61']['class_type'] == 'FormaVAEDecodeHunyuan3D'
    assert graph['61']['inputs']['octree_resolution'] == 512
    assert graph['61']['inputs']['num_chunks'] == 2048
    assert graph['80']['class_type'] == 'Hunyuan3Dv2Conditioning'
    with pytest.raises(ValueError):
        build_workflow({'front': 'front.png', 'back': 'back.png'}, 42, 'test', 'hunyuan21')


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    monkeypatch.setattr(main, 'tasks', set())
    monkeypatch.setattr(main, 'schedule', lambda coroutine: coroutine.close())
    async def available():
        return {'ready': True, 'single_ready': False, 'multiview_ready': False,
                'hunyuan21_ready': True, 'maximum_ready': True, 'busy': False}
    monkeypatch.setattr(main, 'health', available)
    with TestClient(main.app) as client:
        yield client


def test_21_upload_and_repeat_preserve_family_without_requiring_v2(client):
    record = client.post('/api/projects', files={'image': ('fox.png', png(), 'image/png')},
                         data={'model_family': 'hunyuan21', 'quality': 'maximum'}).raise_for_status().json()
    assert record['model_family'] == 'hunyuan21'
    # Storage/repetition is checked after the simulated generation finishes.
    from app.persistence import write_json
    write_json(main.DATA / record['id'] / 'project.json', {**record, 'status':'ready'})
    repeated = client.post('/api/projects/' + record['id'] + '/repeat').raise_for_status().json()
    assert repeated['model_family'] == 'hunyuan21'
    assert repeated['quality'] == 'maximum'
    assert repeated['views'] == {'front': 'input.png'}


def test_21_extra_views_are_rejected_without_losing_them_silently(client):
    response = client.post('/api/projects', files={'image': ('front.png', png(), 'image/png'),
                                                 'back_image': ('back.png', png(), 'image/png')},
                           data={'model_family': 'hunyuan21'})
    assert response.status_code == 422
    assert not list(main.DATA.iterdir())


def test_21_known_sheet_uses_front_without_claiming_back_conditioning(client):
    from app.reference_preparation import REFERENCE
    with REFERENCE.open('rb') as image:
        record=client.post('/api/projects',files={'image':('sheet.png',image,'image/png')},
                           data={'model_family':'hunyuan21'}).raise_for_status().json()
    assert record['mode'] == 'single'
    assert set(record['views']) == {'front'}
    assert record['input_preparation']['used_views'] == ['front']


def test_missing_21_checkpoint_blocks_submission(client, monkeypatch):
    async def missing():
        return {'ready': True, 'hunyuan21_ready': False}
    monkeypatch.setattr(main, 'health', missing)
    response = client.post('/api/projects', files={'image': ('fox.png', png(), 'image/png')},
                           data={'model_family': 'hunyuan21'})
    assert response.status_code == 503
    assert not list(main.DATA.iterdir())
