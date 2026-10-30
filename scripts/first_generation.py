"""Run and record the first real ComfyUI generation; safe to resume monitoring."""
import json
import time
import uuid
import subprocess
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'data/projects/first-fox'
BASE = 'http://127.0.0.1:8188'

def main():
    record_path = PROJECT / 'generation.json'
    with httpx.Client(base_url=BASE, timeout=60) as client:
        if record_path.exists():
            record = json.loads(record_path.read_text())
        else:
            with (PROJECT / 'input-cropped.png').open('rb') as image:
                result = client.post('/upload/image', files={'image': ('fox-first.png', image, 'image/png')}, data={'overwrite': 'false'})
            result.raise_for_status()
            uploaded = result.json()
            prompt = json.loads((ROOT / 'workflows/hunyuan3d-2-api.json').read_text())
            prompt['56']['inputs']['image'] = '/'.join(filter(None, [uploaded.get('subfolder'), uploaded['name']]))
            response = client.post('/prompt', json={'prompt': prompt, 'client_id': str(uuid.uuid4())})
            if response.is_error:
                raise RuntimeError(response.text)
            record = {'prompt_id': response.json()['prompt_id'], 'started_at': time.time(), 'prompt': prompt}
            record_path.write_text(json.dumps(record, indent=2))
        print('Monitoring', record['prompt_id'], flush=True)
        while True:
            response = client.get('/history/' + record['prompt_id'])
            response.raise_for_status()
            history = response.json().get(record['prompt_id'])
            if history:
                (PROJECT / 'history.json').write_text(json.dumps(history, indent=2))
                if history.get('status', {}).get('status_str') == 'error':
                    raise RuntimeError(json.dumps(history['status']))
                for output in history.get('outputs', {}).values():
                    for values in output.values():
                        if not isinstance(values, list):
                            continue
                        for file in values:
                            if isinstance(file, dict) and str(file.get('filename', '')).endswith('.glb'):
                                params = {k: file[k] for k in ('filename', 'subfolder', 'type') if k in file}
                                model = client.get('/view', params=params)
                                model.raise_for_status()
                                (PROJECT / 'original.glb').write_bytes(model.content)
                                record['elapsed_seconds'] = round(time.time() - record['started_at'], 2)
                                record_path.write_text(json.dumps(record, indent=2))
                                print('Saved original.glb; elapsed:', record['elapsed_seconds'], flush=True)
                                return
                raise RuntimeError('Execution ended without a GLB. Inspect history.json.')
            print('Generation in progress; elapsed seconds:', round(time.time() - record['started_at']), flush=True)
            try:
                gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
                with (PROJECT / 'gpu-samples.csv').open('a') as samples:
                    samples.write(f'{time.time()},{gpu.stdout.strip()}\n')
            except (OSError, subprocess.TimeoutExpired):
                pass
            time.sleep(15)

if __name__ == '__main__':
    main()
