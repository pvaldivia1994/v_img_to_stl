"""Conservative reference handling; no unknown contact sheet is auto-cropped."""
import hashlib
import math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'Zorro Durmiente en Luna Creciente.png'
REGIONS = {'front': (2, 2, 916, 857), 'back': (920, 430, 1310, 856)}


def pixel_hash(image):
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def key_reference_background(image):
    """Specific neutral backdrop of the known sculpture reference, not any photo."""
    pixels = np.array(image.convert('RGB'))
    neutral = (np.ptp(pixels.astype(np.int16), axis=2) <= 8) & (pixels.mean(axis=2) < 128)
    components, _ = label(neutral)
    areas = np.bincount(components.ravel())
    selected = areas >= max(64, pixels.shape[0]*pixels.shape[1]*.0005)
    selected[0] = False
    pixels[selected[components]] = 255
    return Image.fromarray(pixels)


def split_known_sheet(image, model_family):
    if not REFERENCE.is_file():
        return None, None
    with Image.open(REFERENCE) as canonical:
        if image.size != canonical.size or pixel_hash(image) != pixel_hash(canonical):
            return None, None
    views = {view:key_reference_background(image.crop(region)) for view,region in REGIONS.items()
             if view == 'front' or model_family == 'hunyuan2'}
    return views, {'kind':'known-contact-sheet', 'source_pixel_sha256':pixel_hash(image),
                   'regions':{k:REGIONS[k] for k in views}, 'used_views':list(views),
                   'note':'La lámina se separó en vistas. 2.1 usa solamente el frente; 2.0 puede usar también el dorso.'}


def prepare_ai_cutout(image, occupancy=.85):
    """Clean isolated alpha speckles in this single-object AI reference.

    Preserve RGB, soft edge alpha, geometry and scale; no sharpening or repaint.
    Retain the raw AI output separately for audit.
    """
    rgba = np.array(image.convert('RGBA'))
    labels, count = label(rgba[...,3] >= 8)
    if not count:
        raise ValueError('La referencia no contiene un objeto opaco.')
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    main = labels == sizes.argmax()
    removed = int(np.count_nonzero((rgba[...,3] > 0) & ~main))
    rgba[...,3][~main] = 0
    ys,xs = np.where(main)
    bounds = (int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
    crop = Image.fromarray(rgba).crop(bounds)
    side = math.ceil(max(crop.size)/occupancy)
    canvas = Image.new('RGBA',(side,side),(255,255,255,0))
    canvas.alpha_composite(crop,((side-crop.width)//2,(side-crop.height)//2))
    white = Image.new('RGBA',canvas.size,'white')
    white.alpha_composite(canvas)
    return canvas,white.convert('RGB'),{'occupancy':occupancy,'alpha_speckle_pixels_removed':removed,
                                       'crop':bounds,'rgb_repainted':False}
