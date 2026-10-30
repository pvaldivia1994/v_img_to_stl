"""CPU background preparation; model cache stays in C:/_IA."""
import argparse
import os
from pathlib import Path
os.environ['U2NET_HOME'] = 'C:/_IA/models/background'
os.environ['NUMBA_CACHE_DIR'] = 'C:/_IA/cache/numba'
from PIL import Image
from rembg import new_session, remove

def prepare(source, destination, model_name='u2net'):
    session = new_session(model_name, providers=['CPUExecutionProvider'])
    with Image.open(source) as image:
        cutout = remove(image.convert('RGB'), session=session)
        background = Image.new('RGBA', cutout.size, 'white')
        background.alpha_composite(cutout)
        bounds = cutout.getchannel('A').getbbox()
        if bounds:
            background = background.crop(bounds)
        side = max(background.size)
        canvas = Image.new('RGB', (int(side * 1.15), int(side * 1.15)), 'white')
        canvas.paste(background.convert('RGB'), ((canvas.width-background.width)//2, (canvas.height-background.height)//2))
        canvas.save(destination)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--model', choices=['u2net', 'u2netp'], default='u2net')
    args = parser.parse_args()
    prepare(args.source, args.destination, args.model)
