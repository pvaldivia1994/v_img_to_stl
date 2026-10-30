"""Resume the official archive in verified HTTP ranges, with bounded concurrency."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time
import httpx

URL = 'https://github.com/Comfy-Org/ComfyUI/releases/download/v0.43.0/ComfyUI_windows_portable_nvidia_cu126.7z'
TARGET = Path('C:/_IA/downloads/ComfyUI_windows_portable_nvidia_cu126.7z')
TOTAL = 1930972692
CHUNK = 64 * 1024 * 1024

def fetch(bounds):
    start, end = bounds
    part = TARGET.with_suffix(f'.part-{start}')
    expected = end - start + 1
    if part.exists() and part.stat().st_size == expected:
        return part
    for attempt in range(4):
        try:
            with httpx.Client(follow_redirects=True, timeout=90) as client:
                with client.stream('GET', URL, headers={'Range': f'bytes={start}-{end}'}) as response:
                    response.raise_for_status()
                    if response.status_code != 206 or not response.headers.get('content-range', '').startswith(f'bytes {start}-{end}/'):
                        raise RuntimeError('Server did not honor byte range')
                    with part.open('wb') as output:
                        for data in response.iter_bytes():
                            output.write(data)
            if part.stat().st_size != expected:
                raise RuntimeError('Incomplete range')
            print('Downloaded range', start, end, flush=True)
            return part
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2)

if __name__ == '__main__':
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    offset = TARGET.stat().st_size if TARGET.exists() else 0
    ranges = [(start, min(start + CHUNK, TOTAL) - 1) for start in range(offset, TOTAL, CHUNK)]
    with ThreadPoolExecutor(max_workers=6) as executor:
        parts = list(executor.map(fetch, ranges))
    with TARGET.open('ab') as output:
        for part in parts:
            with part.open('rb') as source:
                while data := source.read(1024 * 1024):
                    output.write(data)
            part.unlink()
    if TARGET.stat().st_size != TOTAL:
        raise RuntimeError('Archive size mismatch')
    print('Archive complete', flush=True)
