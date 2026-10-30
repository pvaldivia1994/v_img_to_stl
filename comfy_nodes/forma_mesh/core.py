"""Extract a closed isosurface, preserving separate components."""
import numpy as np
from skimage.measure import marching_cubes

def extract_surface(field, threshold=0.6):
    values = np.asarray(field, dtype=np.float32)
    if values.ndim != 3 or min(values.shape) < 2:
        raise ValueError('Expected a three-dimensional voxel field.')
    values = np.nan_to_num(values, nan=threshold - 1, posinf=threshold + 1, neginf=threshold - 1)
    if values.max() <= threshold:
        raise ValueError('No surface found in the generated volume.')
    # Close surfaces that touch a volume boundary by supplying an exterior border.
    padded = np.pad(values, 1, constant_values=threshold - 1)
    vertices, faces, _, _ = marching_cubes(padded, level=threshold, method='lewiner', allow_degenerate=False)
    vertices = vertices - 1
    extent = max(values.shape)
    vertices = (vertices - extent / 2) / (extent / 2)
    # Match ComfyUI's voxel-to-GLB coordinates; reflection reverses winding.
    return vertices[:, [2, 1, 0]].copy(), faces[:, [0, 2, 1]].astype(np.int64).copy()
