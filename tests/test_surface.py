import importlib.util
from pathlib import Path
import numpy as np
import trimesh

spec = importlib.util.spec_from_file_location('core', Path(__file__).parents[1] / 'comfy_nodes/forma_mesh/core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def test_sphere_is_closed():
    x, y, z = np.mgrid[-1:1:32j, -1:1:32j, -1:1:32j]
    vertices, faces = core.extract_surface(0.7 - np.sqrt(x*x+y*y+z*z), threshold=0)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    assert mesh.is_watertight
    assert mesh.is_winding_consistent
    assert len(mesh.split()) == 1

def test_volume_boundary_closed_and_components_preserved():
    field = np.zeros((32, 32, 32))
    field[:7, :7, :7] = 1
    field[20:25, 20:25, 20:25] = 1
    vertices, faces = core.extract_surface(field)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    assert mesh.is_watertight
    assert len(mesh.split()) == 2
