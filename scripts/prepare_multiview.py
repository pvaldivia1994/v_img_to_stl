"""Prepare independent views from the user's original contact sheet."""
import json
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import label
from remove_background import prepare

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'data/multiview-fox'
TARGET.mkdir(parents=True, exist_ok=True)
regions = {
    'front': (2, 2, 916, 857),
    'back': (920, 430, 1310, 856),
    'left': (445, 862, 618, 1124),
    'right': (856, 862, 1072, 1124),
}
with Image.open(ROOT / 'Zorro Durmiente en Luna Creciente.png') as sheet:
    for view, region in regions.items():
        crop = TARGET / f'{view}-source.png'
        original = sheet.crop(region).convert('RGB')
        original.save(crop)
        # This reference sheet has a dark neutral background, including enclosed
        # gaps that U2Net mistakenly keeps. Only key out large neutral dark areas;
        # small facial marks are retained. This is reference-specific preparation.
        pixels = np.array(original)
        neutral_dark = (np.ptp(pixels.astype(np.int16), axis=2) <= 8) & (pixels.mean(axis=2) < 128)
        labels, count = label(neutral_dark)
        areas = np.bincount(labels.ravel())
        selected = areas >= max(64, pixels.shape[0]*pixels.shape[1]*0.0005)
        selected[0] = False
        pixels[selected[labels]] = 255
        keyed = TARGET / f'{view}-keyed.png'
        Image.fromarray(pixels).save(keyed)
        prepare(keyed, TARGET / f'{view}.png')
        print('Prepared', view, flush=True)
(TARGET / 'preparation.json').write_text(json.dumps({
    'source': 'Zorro Durmiente en Luna Creciente.png', 'regions': regions,
    'background_model': 'u2net', 'reference_specific_neutral_background_cleanup': True,
    'notes': 'Front is the large near-frontal perspective; back is the large rear panel. Side views are low resolution and reserved for a later comparison. Views are AI reference art, not calibrated photographs.',
}, indent=2), encoding='utf-8')
