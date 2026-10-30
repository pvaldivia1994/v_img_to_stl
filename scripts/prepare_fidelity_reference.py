"""Tighten white margins without inventing or repainting reference details."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
target = root / 'data/fidelity-fox'
target.mkdir(parents=True, exist_ok=True)
manifest = {}
for view in ('front', 'back'):
    source = root / 'data/multiview-fox' / (view + '.png')
    with Image.open(source) as opened:
        image = opened.convert('RGB')
        foreground = np.any(np.array(image) < 245, axis=2)
        rows, columns = np.where(foreground)
        if not len(rows):
            raise ValueError('No foreground in ' + view)
        bounds = (int(columns.min()), int(rows.min()), int(columns.max()) + 1, int(rows.max()) + 1)
        cropped = image.crop(bounds)
        side = max(cropped.size)
        padding = max(2, round(side * .03))
        canvas = Image.new('RGB', (side + 2 * padding, side + 2 * padding), 'white')
        canvas.paste(cropped, ((canvas.width - cropped.width) // 2, (canvas.height - cropped.height) // 2))
        canvas.save(target / (view + '.png'))
        manifest[view] = {'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                          'crop': bounds, 'size': canvas.size, 'margin_fraction_per_side': .03}
(target / 'preparation.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(target)
