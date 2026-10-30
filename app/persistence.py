"""Atomic JSON snapshots, including transient Windows reader/file scanner locks."""
import json
from pathlib import Path
import tempfile
import time


def write_json(path, record, attempts=25):
    path = Path(path)
    payload = json.dumps(record, ensure_ascii=False, indent=2)
    # Independent writers must never share an intermediate file.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.name+'.', suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
    try:
        for attempt in range(attempts):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                if attempt == attempts-1:
                    raise
                time.sleep(min(.01 * 2**attempt, .25))
    finally:
        temporary.unlink(missing_ok=True)
