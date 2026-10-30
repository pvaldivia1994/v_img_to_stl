import importlib.util
from pathlib import Path

import numpy as np
import pytest
import trimesh

spec = importlib.util.spec_from_file_location('export_stl', Path(__file__).parents[1] / 'scripts/export_stl.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_scene_transform_height_and_original_preserved(tmp_path):
    scene = trimesh.Scene()
    transform = trimesh.transformations.translation_matrix([10, 20, 30])
    scene.add_geometry(trimesh.creation.box(extents=[2, 4, 3]), transform=transform)
    source = tmp_path / 'original.glb'
    source.write_bytes(scene.export(file_type='glb'))
    original = source.read_bytes()
    report = module.export(source, tmp_path / 'model.stl', 100)
    model = trimesh.load(tmp_path / 'model.stl')
    assert np.isclose(model.extents[2], 100)
    assert np.isclose(model.bounds[0, 2], 0)
    assert report['watertight']
    assert source.read_bytes() == original
    raw = (tmp_path / 'model.stl').read_bytes()
    dtype = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    records = np.frombuffer(raw, dtype=dtype, offset=84)
    edges_a = records['vertices'][:, 1] - records['vertices'][:, 0]
    edges_b = records['vertices'][:, 2] - records['vertices'][:, 0]
    cross = np.cross(edges_a, edges_b)
    assert np.all(np.einsum('ij,ij->i', cross, records['normal']) > 0)
    with pytest.raises(FileExistsError):
        module.export(source, tmp_path / 'model.stl', 100)

@pytest.mark.parametrize('height', [0, -1, float('nan'), float('inf')])
def test_invalid_height(tmp_path, height):
    with pytest.raises(ValueError):
        module.export(tmp_path / 'absent.glb', tmp_path / 'output.stl', height)

def test_disconnected_components_remain_in_export(tmp_path):
    first = trimesh.creation.box()
    second = trimesh.creation.box()
    second.apply_translation([4, 0, 0])
    scene = trimesh.Scene([first, second])
    source = tmp_path / 'separate.glb'
    source.write_bytes(scene.export(file_type='glb'))
    report = module.export(source, tmp_path / 'separate.stl', 100)
    assert report['components'] == 2

def test_optional_cleanup_keeps_main_piece_and_records_removals(tmp_path):
    main = trimesh.creation.icosphere(subdivisions=2)
    fragment = trimesh.creation.box(extents=[.1, .1, .1])
    fragment.apply_translation([4, 0, 0])
    scene = trimesh.Scene([main, fragment])
    source = tmp_path / 'original.glb'
    source.write_bytes(scene.export(file_type='glb'))
    original = source.read_bytes()
    report = module.export(source, tmp_path / 'clean.stl', 100, keep_largest=True)
    assert report['components'] == 1
    assert report['removed_components'] == 1
    assert report['removed_faces'] == 12
    assert report['watertight']
    assert source.read_bytes() == original
    raw = (tmp_path / 'clean.stl').read_bytes()
    dtype = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    records = np.frombuffer(raw, dtype=dtype, offset=84)
    cross = np.cross(records['vertices'][:, 1] - records['vertices'][:, 0], records['vertices'][:, 2] - records['vertices'][:, 0])
    assert np.all(np.einsum('ij,ij->i', cross, records['normal']) > 0)
