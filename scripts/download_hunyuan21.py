"""Download and verify the Comfy-Org native Hunyuan3D 2.1 checkpoint."""
import hashlib
import json
from pathlib import Path
import time
import httpx

URL = 'https://huggingface.co/Comfy-Org/Hunyuan-3D-2.1/resolve/main/hunyuan_3d_v2.1.safetensors'
TARGET = Path('C:/_IA/models/checkpoints/hunyuan_3d_v2.1.safetensors')
TOTAL = 7365943290
SHA256 = '5f21e98a6cb99b13b5e224abaee33929570fff7af2b6a0060001559a04ba9d72'
STATUS = Path('C:/_IA/downloads/hunyuan21-download.json')


def report(state, downloaded):
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps({'state': state, 'bytes': downloaded, 'total': TOTAL,
                                 'percent': round(100 * downloaded / TOTAL, 1), 'time': time.time()}), encoding='utf-8')


def verify(path):
    with path.open('rb') as stream:
        return path.stat().st_size == TOTAL and hashlib.file_digest(stream, 'sha256').hexdigest() == SHA256


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        if not verify(TARGET):
            raise RuntimeError('An existing checkpoint failed verification; it was not overwritten.')
        report('verified', TOTAL)
        print('Already verified', flush=True)
        return
    part = TARGET.with_suffix(TARGET.suffix + '.part')
    for attempt in range(4):
        offset = part.stat().st_size if part.exists() else 0
        if offset == TOTAL:
            break
        try:
            headers = {'Range': f'bytes={offset}-'} if offset else {}
            with httpx.Client(follow_redirects=True, timeout=90) as client:
                with client.stream('GET', URL, headers=headers) as response:
                    response.raise_for_status()
                    if offset and (response.status_code != 206 or not response.headers.get('content-range', '').startswith(f'bytes {offset}-')):
                        raise RuntimeError('Server did not honor the resume range.')
                    last_percent = -1
                    with part.open('ab' if offset else 'wb') as output:
                        for block in response.iter_bytes(4 * 1024**2):
                            output.write(block)
                            offset += len(block)
                            if offset > TOTAL:
                                raise RuntimeError('Unexpected checkpoint length.')
                            percent = int(100 * offset / TOTAL)
                            if percent != last_percent:
                                report('downloading', offset)
                                print(f'Download {percent}%', flush=True)
                                last_percent = percent
            break
        except (httpx.HTTPError, OSError):
            if attempt == 3:
                raise
            time.sleep(2)
    report('verifying', part.stat().st_size)
    if not verify(part):
        raise RuntimeError('Checkpoint checksum or size mismatch. Partial file retained.')
    part.rename(TARGET)
    report('verified', TOTAL)
    print('Verified SHA256: ' + SHA256, flush=True)


if __name__ == '__main__':
    main()
