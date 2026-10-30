"""Run a reproducible quality comparison through the application API."""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', type=Path)
    parser.add_argument('--quality', choices=['standard', 'detail'], default='detail')
    parser.add_argument('--seed', type=int, default=4007959359)
    parser.add_argument('--name', default='Zorro-detalle')
    for view in ('back', 'left', 'right'):
        parser.add_argument('--' + view, type=Path)
    args = parser.parse_args()
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=180) as client:
        with ExitStack() as stack:
            files = {'image': (args.name+'.png', stack.enter_context(args.image.open('rb')), 'image/png')}
            for view in ('back', 'left', 'right'):
                path = getattr(args, view)
                if path:
                    files[view+'_image'] = (view+'.png', stack.enter_context(path.open('rb')), 'image/png')
            response = client.post('/api/projects', files=files, data={'remove_background': 'false', 'quality': args.quality, 'seed': str(args.seed)})
        response.raise_for_status()
        record = response.json()
        identifier = record['id']
        (ROOT / 'data/quality').mkdir(parents=True, exist_ok=True)
        (ROOT / 'data/quality/latest-project-id.txt').write_text(identifier)
        project = ROOT / 'data/projects' / identifier
        print('Project:', identifier, flush=True)
        while True:
            record = client.get('/api/projects/' + identifier).raise_for_status().json()
            print('Status:', record['status'], flush=True)
            if record['status'] == 'error':
                raise RuntimeError(record['error'])
            if record['status'] == 'ready':
                break
            gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
            with (project / 'gpu-samples.csv').open('a') as output:
                output.write(f'{time.time()},{gpu.stdout.strip()}\n')
            time.sleep(10)
        exported = client.post('/api/projects/' + identifier + '/export', json={'height': 100, 'up': 'y'}).raise_for_status().json()
        print(json.dumps({'id': identifier, 'elapsed_seconds': record['elapsed_seconds'], 'export': exported['exports'][-1]}, indent=2), flush=True)

if __name__ == '__main__':
    main()
