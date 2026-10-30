"""Conservative mesh cleanup and explicit millimeter scaling; original is preserved."""
import argparse
import json
from pathlib import Path
import numpy as np
import trimesh

def export(source: Path, destination: Path, height: float, axis: str = 'y', keep_largest: bool = False):
    if not np.isfinite(height) or height <= 0:
        raise ValueError('Height must be a positive finite number.')
    scene = trimesh.load(source, force='scene')
    mesh = scene.to_mesh()
    if not len(mesh.vertices) or not len(mesh.faces):
        raise ValueError('The model is empty.')
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    removed_components = 0
    removed_faces = 0
    if keep_largest:
        groups = trimesh.graph.connected_components(mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1)
        if len(groups) > 1:
            largest = max(groups, key=len)
            removed_components = len(groups) - 1
            removed_faces = len(mesh.faces) - len(largest)
            mesh = mesh.submesh([largest], append=True)
    trimesh.repair.fix_normals(mesh)
    # GLB commonly uses Y up; STL is exported Z up for slicers.
    if axis == 'y':
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    if mesh.extents[2] <= 0:
        raise ValueError('The model has no height.')
    mesh.apply_scale(height / mesh.extents[2])
    mesh.apply_translation([-mesh.centroid[0], -mesh.centroid[1], -mesh.bounds[0, 2]])
    # Imported GLB normals can be stale after selecting a submesh. STL stores
    # face normals separately, so rebuild them from the final triangle winding.
    mesh.face_normals = trimesh.triangles.normals(mesh.triangles)[0]
    if destination.exists():
        raise FileExistsError(destination)
    mesh.export(destination)
    verified = trimesh.load(destination, force='mesh')
    components = trimesh.graph.connected_components(verified.face_adjacency, nodes=np.arange(len(verified.faces)), min_len=1)
    report = {'source': str(source), 'stl': str(destination), 'height_mm': height, 'source_up_axis': axis,
              'dimensions_mm': verified.extents.tolist(), 'vertices': len(verified.vertices),
              'faces': len(verified.faces), 'watertight': bool(verified.is_watertight),
              'winding_consistent': bool(verified.is_winding_consistent),
              'components': len(components),
              'largest_component_faces': max(map(len, components), default=0),
              'keep_largest': keep_largest, 'removed_components': removed_components, 'removed_faces': removed_faces,
              'note': 'No automatic thickness guarantee; no holes filled. Original GLB preserved.'}
    destination.with_suffix('.report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--height', type=float, required=True)
    parser.add_argument('--up', choices=['y', 'z'], default='y')
    parser.add_argument('--keep-largest', action='store_true')
    args = parser.parse_args()
    print(json.dumps(export(args.source, args.destination, args.height, args.up, args.keep_largest), indent=2))
