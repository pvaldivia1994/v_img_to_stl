import json
import os
from pathlib import Path

import pytest

from app import persistence
from scripts.refine_ultrashape import Progress


def test_progress_survives_transient_windows_replace_lock(tmp_path, monkeypatch):
    path = tmp_path / 'project.json'
    path.write_text('{"status":"running"}')
    replace = Path.replace
    calls = []
    def locked_then_available(source, destination):
        calls.append(source)
        # Readers retain the previous complete snapshot until replacement succeeds.
        assert json.loads(path.read_text())['status'] == 'running'
        if len(calls) < 4:
            raise PermissionError(13, 'WinError 5: Access is denied')
        return replace(source, destination)
    monkeypatch.setattr(Path, 'replace', locked_then_available)
    monkeypatch.setattr(persistence.time, 'sleep', lambda _: None)
    Progress(tmp_path, {'status':'running'}).stage(4, 'Refinando', 62, 2100)
    assert json.loads(path.read_text())['progress']['value'] == 62
    assert len(calls) == 4
    assert not list(tmp_path.glob('*.tmp'))


def test_permanent_write_error_preserves_last_snapshot(tmp_path, monkeypatch):
    path = tmp_path / 'project.json'
    path.write_text('{"status":"running"}')
    def denied(*args):
        raise PermissionError('Locked')
    monkeypatch.setattr(Path, 'replace', denied)
    monkeypatch.setattr(persistence.time, 'sleep', lambda _: None)
    with pytest.raises(PermissionError):
        persistence.write_json(path, {'status':'ready'}, attempts=3)
    assert json.loads(path.read_text())['status'] == 'running'
    assert not list(tmp_path.glob('*.tmp'))


@pytest.mark.skipif(os.name != 'nt', reason='Windows file sharing semantics')
def test_retries_an_actual_windows_reader_lock(tmp_path):
    import ctypes
    from ctypes import wintypes
    import threading
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
                                  wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    path = tmp_path / 'project.json'
    path.write_text('{"status":"running"}')
    handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 128, None)
    assert handle != wintypes.HANDLE(-1).value
    timer = threading.Timer(.15, lambda: kernel.CloseHandle(handle))
    timer.start()
    try:
        persistence.write_json(path, {'status':'ready'})
    finally:
        timer.join()
    assert json.loads(path.read_text())['status'] == 'ready'
