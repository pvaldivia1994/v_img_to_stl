import json
import pytest
from fastapi.testclient import TestClient
from app import main, refinement


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    monkeypatch.setattr(main, 'tasks', set())
    monkeypatch.setattr(main, 'refinement_ready', lambda: True)
    monkeypatch.setattr(main, 'schedule', lambda coroutine: coroutine.close())
    async def available():
        return {'connected': True, 'ready': True, 'busy': False}
    monkeypatch.setattr(main, 'health', available)
    manifest = tmp_path / 'runtime.json'
    manifest.write_text(json.dumps({'revision':'verified-upstream'}))
    monkeypatch.setattr(refinement, 'MANIFEST', manifest)
    path = tmp_path / 'baseline'
    path.mkdir()
    (path / 'project.json').write_text(json.dumps({'id':'baseline', 'status':'ready', 'created_at':0}))
    (path / 'input.png').write_bytes(b'reference-preserved')
    (path / 'original.glb').write_bytes(b'coarse-preserved')
    return path


def test_refinement_is_separate_and_blocks_concurrent_gpu_jobs(source):
    with TestClient(main.app) as client:
        record = client.post('/api/projects/baseline/refine').raise_for_status().json()
        assert record['model_family'] == 'ultrashape'
        assert record['refinement']['source_project'] == 'baseline'
        assert record['refinement']['latents'] == 16384
        assert record['progress']['percent'] is None
        target = source.parent / record['id']
        assert (target / 'coarse.glb').read_bytes() == (source / 'original.glb').read_bytes()
        assert (target / 'input.png').read_bytes() == (source / 'input.png').read_bytes()
        assert client.post('/api/projects/baseline/refine').status_code == 409


def test_missing_refiner_does_not_create_incomplete_project(source, monkeypatch):
    monkeypatch.setattr(main, 'refinement_ready', lambda: False)
    with TestClient(main.app) as client:
        assert client.post('/api/projects/baseline/refine').status_code == 503
    assert [p.name for p in source.parent.iterdir() if p.is_dir()] == ['baseline']


def test_refinement_preserves_rear_reference_and_declares_indirect_use(source):
    baseline = json.loads((source / 'project.json').read_text())
    baseline.update(mode='multiview',views={'front':'input.png','back':'input-back.png'})
    (source / 'input-back.png').write_bytes(b'rear-reference')
    (source / 'project.json').write_text(json.dumps(baseline))
    path,record = refinement.create_refinement(source,source.parent,{'sequential_cfg':True,'latents':32768})
    assert (path / 'input-back.png').read_bytes() == b'rear-reference'
    assert record['refinement']['base_geometry_views'] == ['front','back']
    assert record['refinement']['direct_image_views'] == ['front']
    assert record['refinement']['sequential_cfg'] is True
