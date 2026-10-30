"""Validated, recorded experimental settings; never silently alter a profile."""
import math
from PIL import Image
import numpy as np


def frame_reference(image, occupancy=.85):
    if not .5 <= occupancy <= .98:
        raise ValueError('La ocupación debe estar entre 50% y 98%.')
    rgba = image.convert('RGBA')
    white = Image.new('RGBA', rgba.size, 'white')
    white.alpha_composite(rgba)
    rgb = white.convert('RGB')
    # Existing reference was already segmented. Do not run segmentation again.
    mask = np.any(np.asarray(rgb) < 245, axis=2)
    rows, cols = np.where(mask)
    if not len(rows):
        raise ValueError('La imagen no contiene una figura visible.')
    crop = rgb.crop((int(cols.min()), int(rows.min()), int(cols.max())+1, int(rows.max())+1))
    side = math.ceil(max(crop.size) / occupancy)
    canvas = Image.new('RGB', (side, side), 'white')
    canvas.paste(crop, ((side-crop.width)//2, (side-crop.height)//2))
    return canvas


def apply_fidelity(prompt, settings):
    allowed = {'steps', 'threshold', 'num_chunks', 'octree_resolution'}
    if settings.keys() - allowed:
        raise ValueError('Parámetro de comparación desconocido.')
    steps = settings.get('steps', prompt['3']['inputs']['steps'])
    threshold = settings.get('threshold', prompt['62']['inputs']['threshold'])
    chunks = settings.get('num_chunks', prompt['61']['inputs']['num_chunks'])
    resolution = settings.get('octree_resolution', prompt['61']['inputs']['octree_resolution'])
    if not isinstance(steps, int) or not 1 <= steps <= 100:
        raise ValueError('Pasos fuera del rango probado.')
    if not math.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError('El nivel normalizado debe estar entre 0 y 1.')
    if not isinstance(chunks, int) or not 256 <= chunks <= 20000:
        raise ValueError('Lote fuera del rango admitido.')
    if not isinstance(resolution, int) or not 16 <= resolution <= 512:
        raise ValueError('El decodificador activo admite hasta 512; no se fuerza otro método silenciosamente.')
    prompt['3']['inputs']['steps'] = steps
    prompt['62']['inputs']['threshold'] = threshold
    prompt['61']['inputs'].update(num_chunks=chunks, octree_resolution=resolution)
    return prompt
